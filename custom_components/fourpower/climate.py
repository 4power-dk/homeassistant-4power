"""The spa as a thermostat, with rest mode as a preset."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import FourPowerConfigEntry
from .const import MAX_TEMP, MIN_TEMP
from .entity import FourPowerEntity
from .switch import async_send

# Rest mode is the spa's own energy-saving state: it holds a lower setpoint
# until the next ready time. Modelled as a preset rather than an HVAC mode
# because the spa is always heating towards SOMETHING — it never turns off.
PRESET_READY = "ready"
PRESET_REST = "rest"


async def async_setup_entry(
    hass: HomeAssistant, entry: FourPowerConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """One climate entity per controllable spa that reports a setpoint."""
    coordinator = entry.runtime_data
    async_add_entities(
        FourPowerClimate(coordinator, device_id)
        for device_id, device in coordinator.data.items()
        if (device.get("capabilities") or {}).get("outputControl")
        and "targetTemp" in (device.get("state") or {})
    )


class FourPowerClimate(FourPowerEntity, ClimateEntity):
    """Target temperature, current temperature, and rest/ready."""

    _attr_name = None  # the spa's own name is the entity name
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.HEAT]
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP
    _attr_target_temperature_step = 0.5
    _attr_preset_modes = [PRESET_READY, PRESET_REST]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
    )

    def __init__(self, coordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id, "climate")

    @property
    def hvac_mode(self) -> HVACMode:
        # A spa heats and nothing else; there is no cooling and no off.
        return HVACMode.HEAT

    @property
    def hvac_action(self) -> HVACAction:
        if self._state.get("heating"):
            return HVACAction.HEATING
        return HVACAction.IDLE

    @property
    def current_temperature(self) -> float | None:
        value = self._state.get("actualTemp")
        # Never substituted from the setpoint — the cloud refuses to fake it,
        # and a wrong "current" reading is worse than none.
        return None if value is None else round(float(value), 1)

    @property
    def target_temperature(self) -> float | None:
        value = self._state.get("targetTemp")
        return None if value is None else float(value)

    @property
    def preset_mode(self) -> str:
        return PRESET_REST if self._state.get("restMode") else PRESET_READY

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        # The cloud clamps to 10-40 °C; min/max above keep the UI honest so a
        # user is not offered a value that will be silently altered.
        await async_send(
            self.coordinator, self._device_id, "targetTemp", float(temperature)
        )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        # Note the case: the state reads back as `restMode`, but the command
        # whitelist accepts `restmode`. They genuinely differ.
        await async_send(
            self.coordinator, self._device_id, "restmode", preset_mode == PRESET_REST
        )
