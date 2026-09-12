"""Measured values and diagnostics."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfElectricPotential, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import FourPowerConfigEntry
from .entity import FourPowerEntity


@dataclass(frozen=True, kw_only=True)
class FourPowerSensorDescription(SensorEntityDescription):
    """A number the spa reports."""

    state_key: str
    precision: int | None = None


DESCRIPTIONS: tuple[FourPowerSensorDescription, ...] = (
    FourPowerSensorDescription(
        key="water_temperature", state_key="actualTemp",
        translation_key="water_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        precision=1,
    ),
    FourPowerSensorDescription(
        key="ph", state_key="ph", translation_key="ph",
        device_class=SensorDeviceClass.PH,
        state_class=SensorStateClass.MEASUREMENT,
        precision=2,
    ),
    FourPowerSensorDescription(
        key="orp", state_key="orp", translation_key="orp",
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        state_class=SensorStateClass.MEASUREMENT,
        precision=0,
    ),
    FourPowerSensorDescription(
        key="wifi_rssi", state_key="wifiRssi", translation_key="wifi_rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement="dBm",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: FourPowerConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create a sensor for each value the spa actually reports.

    pH and ORP only exist on a spa with an analyzer or a BlueConnect meter, and
    only once it has taken a reading — the BLE meter reads on a slow cadence to
    spare its battery. A spa without them gets no chemistry entities rather
    than entities stuck at unknown.
    """
    coordinator = entry.runtime_data
    async_add_entities(
        FourPowerSensor(coordinator, device_id, description)
        for device_id, device in coordinator.data.items()
        for description in DESCRIPTIONS
        if description.state_key in (device.get("state") or {})
    )


class FourPowerSensor(FourPowerEntity, SensorEntity):
    """A number the spa reports."""

    entity_description: FourPowerSensorDescription

    def __init__(self, coordinator, device_id: str, description) -> None:
        super().__init__(coordinator, device_id, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        # Chemistry and temperature keep their meaning while the spa is
        # unreachable: the last reading is still the last known truth, and an
        # offline spa is exactly when an owner wants to see it. So these stay
        # available as long as the spa is in the payload at all.
        return (
            super(FourPowerEntity, self).available
            and self._device_id in self.coordinator.data
        )

    @property
    def native_value(self) -> float | None:
        value = self._state.get(self.entity_description.state_key)
        if value is None:
            return None
        if self.entity_description.precision is not None:
            return round(float(value), self.entity_description.precision)
        return float(value)
