"""The spa light."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import FourPowerConfigEntry
from .entity import FourPowerEntity
from .switch import async_send


async def async_setup_entry(
    hass: HomeAssistant, entry: FourPowerConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """One light per spa that has one and can be controlled."""
    coordinator = entry.runtime_data
    async_add_entities(
        FourPowerLight(coordinator, device_id)
        for device_id, device in coordinator.data.items()
        if (device.get("capabilities") or {}).get("outputControl")
        and "light" in (device.get("state") or {})
    )


class FourPowerLight(FourPowerEntity, LightEntity):
    """On/off only — the spa exposes no brightness or colour."""

    _attr_translation_key = "light"
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(self, coordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id, "light")

    @property
    def is_on(self) -> bool | None:
        value = self._state.get("light")
        return None if value is None else bool(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await async_send(self.coordinator, self._device_id, "light", True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await async_send(self.coordinator, self._device_id, "light", False)
