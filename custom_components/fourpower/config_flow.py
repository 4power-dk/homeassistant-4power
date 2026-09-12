"""Config flow: OAuth2 with PKCE, plus re-auth."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from homeassistant.config_entries import ConfigFlowResult
from homeassistant.helpers import config_entry_oauth2_flow

from .const import DOMAIN, OAUTH2_SCOPE
from .oauth import async_register_our_implementation

_LOGGER = logging.getLogger(__name__)


class FourPowerOAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Handle the 4Power OAuth2 flow."""

    DOMAIN = DOMAIN
    VERSION = 1

    @property
    def logger(self) -> logging.Logger:
        return _LOGGER

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        # Without this scope the cloud answers /ha/* with 403
        # insufficient_scope — it is what separates this integration's tokens
        # from Google Home account-linking tokens in the same table.
        return {"scope": OAUTH2_SCOPE}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Register our public client, then go straight to the 4Power login.

        With exactly one implementation registered, Home Assistant skips the
        implementation picker — so the user sees the login page and nothing
        else. No client id, no secret, no API key.
        """
        async_register_our_implementation(self.hass)
        return await super().async_step_user(user_input)

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """A rejected token sends the user back through the login."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is None:
            return self.async_show_form(step_id="reauth_confirm")
        return await self.async_step_user()

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> ConfigFlowResult:
        """One entry per 4Power account.

        Keyed on the account rather than on a spa: the cloud returns every spa
        the account can see in one call, so a second entry for the same account
        would double the polling for no gain.
        """
        if self.source == "reauth":
            entry = self._get_reauth_entry()
            return self.async_update_reload_and_abort(entry, data=data)
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title="4Power", data=data)
