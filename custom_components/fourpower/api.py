"""Thin async client for the 4Power cloud /ha endpoints."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientResponseError, ClientSession
from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session

from .const import API_COMMAND, API_DEVICES

_LOGGER = logging.getLogger(__name__)


class FourPowerAuthError(Exception):
    """The token was rejected — re-authentication is required."""


class FourPowerRateLimited(Exception):
    """The cloud asked us to slow down."""

    def __init__(self, retry_after: int | None) -> None:
        super().__init__("rate limited")
        self.retry_after = retry_after


class FourPowerSubscriptionRequired(Exception):
    """This spa has no active subscription, so the cloud will not command it."""


class FourPowerOffline(Exception):
    """The spa is not reachable, so the command was refused rather than lost."""


class FourPowerApiError(Exception):
    """Anything else the cloud said no to."""


class FourPowerApi:
    """Calls the cloud as the config entry's user.

    One request returns EVERY spa (`/ha/devices`). That is deliberate on the
    cloud side: a per-device endpoint would multiply Lambda invocations and IoT
    shadow reads by the customer's spa count on every poll. So this client has
    no "fetch one device" method, and the coordinator must not add one.
    """

    def __init__(self, session: ClientSession, oauth_session: OAuth2Session) -> None:
        self._session = session
        self._oauth = oauth_session

    async def _headers(self) -> dict[str, str]:
        # Refreshes the token when it has expired. The 4Power token endpoint
        # returns a new access_token WITHOUT a refresh_token; Home Assistant
        # merges the response over the stored token, so the original refresh
        # token is preserved. Do not "fix" this by expecting rotation.
        await self._oauth.async_ensure_token_valid()
        token = self._oauth.token["access_token"]
        return {"Authorization": f"Bearer {token}"}

    async def async_get_devices(self) -> dict[str, Any]:
        """Every spa this account may see, with current state."""
        try:
            resp = await self._session.get(API_DEVICES, headers=await self._headers())
            if resp.status == 401:
                raise FourPowerAuthError("token rejected")
            if resp.status == 429:
                retry = resp.headers.get("Retry-After")
                raise FourPowerRateLimited(int(retry) if retry and retry.isdigit() else None)
            resp.raise_for_status()
            return await resp.json()
        except ClientResponseError as err:
            raise FourPowerApiError(f"/ha/devices failed: {err.status}") from err

    async def async_command(self, device_id: str, output: str, value: Any) -> dict[str, Any]:
        """Set one output on one spa, and report what the cloud actually did.

        The cloud answers with a real outcome rather than accepting blindly:
        402 when the spa has no subscription, 503 when it is offline (a desired
        write to an idle spa would "succeed" and never apply), 400 when the
        value is outside what the device accepts.
        """
        payload = {"deviceId": device_id, "output": output, "value": value}
        resp = await self._session.post(
            API_COMMAND, headers=await self._headers(), json=payload
        )
        if resp.status == 401:
            raise FourPowerAuthError("token rejected")
        if resp.status == 402:
            raise FourPowerSubscriptionRequired(device_id)
        if resp.status == 503:
            raise FourPowerOffline(device_id)
        if resp.status == 429:
            retry = resp.headers.get("Retry-After")
            raise FourPowerRateLimited(int(retry) if retry and retry.isdigit() else None)
        if resp.status >= 400:
            body = await resp.text()
            raise FourPowerApiError(f"{output}={value!r} on {device_id}: {resp.status} {body[:200]}")
        return await resp.json()
