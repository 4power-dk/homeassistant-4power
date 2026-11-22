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
from .entity import FourPowerEntity, async_remove_stale, spa_has


@dataclass(frozen=True, kw_only=True)
class FourPowerBinaryDescription(BinarySensorEntityDescription):
    """A boolean the spa reports."""

    state_key: str
    # Set when the sensor belongs to a control the spa may not have: filling
    # sensors exist only on a spa that can fill (controls.fill).
    control: str | None = None


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
        key="aqua_filling", state_key="aquaFilling", translation_key="filling",
        device_class=BinarySensorDeviceClass.RUNNING, control="fill",
    ),
    FourPowerBinaryDescription(
        key="auto_refill", state_key="autoRefill", translation_key="auto_refill",
        control="fill",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: FourPowerConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create a binary sensor for each boolean the spa actually reports."""
    coordinator = entry.runtime_data
    entities = [
        FourPowerBinarySensor(coordinator, device_id, description)
        for device_id, device in coordinator.data.items()
        for description in DESCRIPTIONS
        if description.state_key in (device.get("state") or {})
        and (description.control is None or spa_has(device, description.control, description.state_key))
    ]
    async_remove_stale(
        hass, entry, "binary_sensor",
        {d.key for d in DESCRIPTIONS if d.control},
        {e.unique_id for e in entities},
    )
    async_add_entities(entities)


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
