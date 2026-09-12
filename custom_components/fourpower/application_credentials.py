"""OAuth2 details for the 4Power cloud.

PKCE, no client secret. The cloud registers this client as `is_public = true`
and REFUSES to issue a code without a `code_challenge`, so the flow cannot
silently degrade to an unprotected authorization code — which is the whole
reason the integration can ship its client id in a public repository.
"""

from __future__ import annotations

from homeassistant.components.application_credentials import (
    AuthorizationServer,
    ClientCredential,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow

from .const import OAUTH2_AUTHORIZE, OAUTH2_TOKEN


async def async_get_authorization_server(hass: HomeAssistant) -> AuthorizationServer:
    """Return the 4Power authorization server."""
    return AuthorizationServer(authorize_url=OAUTH2_AUTHORIZE, token_url=OAUTH2_TOKEN)


async def async_get_auth_implementation(
    hass: HomeAssistant, auth_domain: str, credential: ClientCredential
) -> config_entry_oauth2_flow.AbstractOAuth2Implementation:
    """Return a PKCE implementation.

    `client_secret` is passed through as whatever the credential holds — empty
    for our public client. The verifier is what authenticates the exchange.
    """
    return config_entry_oauth2_flow.LocalOAuth2ImplementationWithPkce(
        hass,
        auth_domain,
        credential.client_id,
        authorize_url=OAUTH2_AUTHORIZE,
        token_url=OAUTH2_TOKEN,
        client_secret=credential.client_secret or "",
    )
