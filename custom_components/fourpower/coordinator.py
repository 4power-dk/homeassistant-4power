"""Single poll for the whole account, shared by every entity."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    FourPowerApi,
    FourPowerAuthError,
    FourPowerRateLimited,
)
from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_SECONDS,
    POST_COMMAND_REFRESH,
)

_LOGGER = logging.getLogger(__name__)


class FourPowerCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Polls /ha/devices once and indexes the result by device id.

    One coordinator per config entry, NOT per spa — the cloud returns every
    device in a single call and rate-limits per token, so a coordinator per
    device would multiply the request count by the number of spas and get the
    account throttled.
    """

    def __init__(self, hass: HomeAssistant, api: FourPowerApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.api = api
        # Spas the account can see but has no subscription for. Reported as a
        # count by the cloud, never named — so this is all we can honestly
        # tell the user, and it is worth telling them: otherwise a customer
        # installs the integration, sees nothing, and assumes it is broken.
        self.unlicensed_count = 0

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            payload = await self.api.async_get_devices()
        except FourPowerAuthError as err:
            # Triggers Home Assistant's re-authentication flow rather than
            # retrying a token that will never work again.
            raise ConfigEntryAuthFailed(str(err)) from err
        except FourPowerRateLimited as err:
            if err.retry_after:
                self.update_interval = timedelta(seconds=max(err.retry_after, MIN_SCAN_SECONDS))
                _LOGGER.warning(
                    "4Power asked us to slow down; next poll in %ss", self.update_interval.seconds
                )
            raise UpdateFailed("rate limited by the 4Power cloud") from err
        except Exception as err:  # noqa: BLE001 — coordinator contract
            raise UpdateFailed(str(err)) from err

        # Honour the floor the cloud publishes rather than hardcoding one, so a
        # change there does not need an integration release.
        published = payload.get("minPollSeconds")
        if isinstance(published, int) and published > 0:
            wanted = timedelta(seconds=max(published, MIN_SCAN_SECONDS))
            if self.update_interval != wanted:
                _LOGGER.debug("adopting the cloud's poll floor: %ss", wanted.seconds)
                self.update_interval = wanted

        self.unlicensed_count = int(payload.get("unlicensedCount") or 0)
        devices = payload.get("devices") or []
        return {d["deviceId"]: d for d in devices if d.get("deviceId")}

    async def async_request_refresh_soon(self) -> None:
        """Re-poll shortly after a command.

        The cloud reports a just-commanded value at its target for about ten
        seconds while the spa echoes it back. Refreshing inside that window
        makes the UI settle immediately; waiting for the scheduled poll would
        show the old state and look like the command failed.
        """
        self.hass.loop.call_later(
            POST_COMMAND_REFRESH.total_seconds(),
            lambda: self.hass.async_create_task(self.async_request_refresh()),
        )
