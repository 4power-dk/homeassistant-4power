"""Shared base for every 4Power entity."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FourPowerCoordinator


def spa_has(device: dict[str, Any], control: str, state_key: str) -> bool:
    """Whether a spa has a jet, the blower or filling.

    The cloud answers this in `controls` — the same rule its device page uses:
    the installation's profile, and on a Balboa spa its known pumps and blower.
    A cloud too old to send `controls` falls back to "the spa reports the key",
    which is how every entity here was created before.
    """
    controls = device.get("controls")
    if isinstance(controls, dict):
        return bool(controls.get(control))
    return state_key in (device.get("state") or {})


def controls_signature(data: dict[str, dict[str, Any]] | None) -> tuple:
    """What decides which spas and controls exist — a change means a reload."""
    return tuple(
        sorted(
            (device_id, tuple(sorted((device.get("controls") or {}).items())))
            for device_id, device in (data or {}).items()
        )
    )


def async_remove_stale(
    hass: HomeAssistant,
    entry: ConfigEntry,
    domain: str,
    governed_keys: set[str],
    created_unique_ids: set[str],
) -> None:
    """Drop registry entries for controls a spa no longer has.

    Only the keys `controls` governs are touched. A sensor whose reading is
    briefly missing must keep its registry entry (and the owner's name, area
    and dashboards with it); a jet the spa does not have must not linger as a
    permanently unavailable switch.
    """
    registry = er.async_get(hass)
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if entity.domain != domain or entity.unique_id in created_unique_ids:
            continue
        if any(entity.unique_id.endswith(f"_{key}") for key in governed_keys):
            registry.async_remove(entity.entity_id)


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
