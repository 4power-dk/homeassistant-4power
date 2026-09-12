"""The 4Power integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client, config_entry_oauth2_flow

from .api import FourPowerApi
from .coordinator import FourPowerCoordinator
from .oauth import async_register_our_implementation

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.SWITCH,
]

type FourPowerConfigEntry = ConfigEntry[FourPowerCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: FourPowerConfigEntry) -> bool:
    """Set up 4Power from a config entry."""
    # After a restart the config flow does not run, so nothing else would have
    # registered our implementation and resolving it would fail.
    async_register_our_implementation(hass)
    implementation = (
        await config_entry_oauth2_flow.async_get_config_entry_implementation(hass, entry)
    )
    oauth_session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
    api = FourPowerApi(aiohttp_client.async_get_clientsession(hass), oauth_session)

    coordinator = FourPowerCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    if not coordinator.data and coordinator.unlicensed_count:
        # Not an error: the account has spas, none of them are paid for. Say so
        # once at setup, because otherwise the integration loads with zero
        # entities and looks broken.
        _LOGGER.warning(
            "4Power: no spa has an active subscription (%s visible without one). "
            "Home Assistant control is a paid feature — entities will appear once "
            "a spa is covered",
            coordinator.unlicensed_count,
        )

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: FourPowerConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
