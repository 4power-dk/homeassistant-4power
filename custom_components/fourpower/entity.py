"""Shared base for every 4Power entity."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FourPowerCoordinator


class FourPowerEntity(CoordinatorEntity[FourPowerCoordinator]):
    """One physical spa, many entities.

    Entities are created from the state keys the spa ACTUALLY reports, not from
    the `capabilities` map. The capability flags describe platform features
    (outputControl, blueConnect, namedEnergyShadow…) and do not enumerate a
    model's outputs — a HydroBrain reports `jet1` and no `jet2`, while a
    SpaControl reports both, and nothing in `capabilities` distinguishes them.
    The reported state does. `outputControl` still gates whether anything is
    writable at all.
    """

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: FourPowerCoordinator, device_id: str, key: str
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_{key}"

    @property
    def _device(self) -> dict[str, Any]:
        return self.coordinator.data.get(self._device_id) or {}

    @property
    def _state(self) -> dict[str, Any]:
        return self._device.get("state") or {}

    @property
    def available(self) -> bool:
        # A spa that dropped out of the payload entirely (unsubscribed, or
        # access removed) is unavailable, not merely offline. `online: false`
        # also makes it unavailable — the cloud refuses commands to an idle spa
        # rather than writing a desired value nothing will apply.
        return (
            super().available
            and self._device_id in self.coordinator.data
            and bool(self._device.get("online"))
        )

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            manufacturer="4Power",
            name=self._device.get("name") or self._device_id,
            model=self._device.get("model"),
            sw_version=self._device.get("firmwareVersion"),
            hw_version=self._device.get("hwVersion"),
            serial_number=self._device_id,
        )
