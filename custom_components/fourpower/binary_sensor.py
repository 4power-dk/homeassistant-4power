"""Read-only spa state."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import FourPowerConfigEntry
from .entity import FourPowerEntity


@dataclass(frozen=True, kw_only=True)
class FourPowerBinaryDescription(BinarySensorEntityDescription):
    """A boolean the spa reports."""

    state_key: str


DESCRIPTIONS: tuple[FourPowerBinaryDescription, ...] = (
    FourPowerBinaryDescription(
        key="heating", state_key="heating", translation_key="heating",
        device_class=BinarySensorDeviceClass.HEAT,
    ),
    FourPowerBinaryDescription(
        key="circulation", state_key="circulation", translation_key="circulation",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    FourPowerBinaryDescription(
        key="flow", state_key="flow", translation_key="flow",
    ),
    FourPowerBinaryDescription(
        key="level", state_key="level", translation_key="level",
    ),
    FourPowerBinaryDescription(
        key="thermo", state_key="thermo", translation_key="thermo",
    ),
    FourPowerBinaryDescription(
        key="emergency_shutdown", state_key="emergencyShutdown",
        translation_key="emergency_shutdown",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    FourPowerBinaryDescription(
        key="no_flow_shutdown", state_key="noFlowShutdown",
        translation_key="no_flow_shutdown",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    FourPowerBinaryDescription(
        key="aqua_filling", state_key="aquaFilling", translation_key="aqua_filling",
    ),
    FourPowerBinaryDescription(
        key="auto_refill", state_key="autoRefill", translation_key="auto_refill",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: FourPowerConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create a binary sensor for each boolean the spa actually reports."""
    coordinator = entry.runtime_data
    async_add_entities(
        FourPowerBinarySensor(coordinator, device_id, description)
        for device_id, device in coordinator.data.items()
        for description in DESCRIPTIONS
        if description.state_key in (device.get("state") or {})
    )


class FourPowerBinarySensor(FourPowerEntity, BinarySensorEntity):
    """A boolean the spa reports."""

    entity_description: FourPowerBinaryDescription

    def __init__(self, coordinator, device_id: str, description) -> None:
        super().__init__(coordinator, device_id, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        value = self._state.get(self.entity_description.state_key)
        return None if value is None else bool(value)
