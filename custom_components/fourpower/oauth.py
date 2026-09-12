"""Our own OAuth2 implementation, registered so the user is never asked for one.

WHY NOT the application_credentials platform: that platform exists so a user
can supply a client id and secret, and Home Assistant will DEMAND them through
the "Add credentials" dialog before the flow starts — which is exactly the
friction this integration is meant to avoid. `async_import_client_credential`
does not help: Home Assistant loads config_flow.py to run a flow without
calling the component's async_setup first, so there is nothing to import from
yet.

Registering an implementation directly works because the 4Power client is
PUBLIC: PKCE authenticates the exchange, so there is no secret in this
repository to leak, and the cloud refuses to issue a code to this client
without a challenge.
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_entry_oauth2_flow

from .const import CLIENT_ID, DOMAIN, OAUTH2_AUTHORIZE, OAUTH2_TOKEN


@callback
def async_register_our_implementation(hass: HomeAssistant) -> None:
    """Register the 4Power public client.

    Called from BOTH the config flow (so a new setup goes straight to the
    login) and async_setup_entry (so an existing entry can still resolve its
    implementation after a restart — the flow does not run then).

    Registering twice is harmless: it replaces the entry for this domain.
    """
    config_entry_oauth2_flow.async_register_implementation(
        hass,
        DOMAIN,
        config_entry_oauth2_flow.LocalOAuth2ImplementationWithPkce(
            hass,
            DOMAIN,
            CLIENT_ID,
            OAUTH2_AUTHORIZE,
            OAUTH2_TOKEN,
        ),
    )
