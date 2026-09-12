"""Diagnostics, with the account's secrets left out."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import FourPowerConfigEntry

# Device ids identify a customer's hardware, and the token is a live
# credential — neither belongs in a diagnostics file people paste into issues.
TO_REDACT = {"access_token", "refresh_token", "deviceId", "serial_number"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: FourPowerConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return {
        "poll_interval_seconds": (
            coordinator.update_interval.total_seconds() if coordinator.update_interval else None
        ),
        "licensed_device_count": len(coordinator.data or {}),
        "unlicensed_device_count": coordinator.unlicensed_count,
        "devices": async_redact_data(list((coordinator.data or {}).values()), TO_REDACT),
    }
