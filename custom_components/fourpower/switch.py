"""Jets, filling, and rest mode."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import FourPowerConfigEntry
from .api import FourPowerOffline, FourPowerSubscriptionRequired
from .entity import FourPowerEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class FourPowerSwitchDescription(SwitchEntityDescription):
    """A switchable output."""

    state_key: str
    # The whitelist key the cloud accepts, which is NOT always the state key:
    # rest mode reads back as `restMode` but is commanded as `restmode`.
    command_key: str


DESCRIPTIONS: tuple[FourPowerSwitchDescription, ...] = (
    FourPowerSwitchDescription(
        key="jet1", state_key="jet1", command_key="jet1",
        translation_key="jet1", device_class=SwitchDeviceClass.SWITCH,
    ),
    FourPowerSwitchDescription(
        key="jet2", state_key="jet2", command_key="jet2",
        translation_key="jet2", device_class=SwitchDeviceClass.SWITCH,
    ),
    FourPowerSwitchDescription(
        key="aqua_filling", state_key="aquaFilling", command_key="aquaFilling",
        translation_key="aqua_filling", device_class=SwitchDeviceClass.SWITCH,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: FourPowerConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create a switch per output the spa reports — if it can be controlled.

    A spa without `outputControl` (an analyzer-only HydroSense, say) reports
    state but has nothing to switch; the cloud would refuse the command as an
    unsupported model, so no switch is offered.
    """
    coordinator = entry.runtime_data
    async_add_entities(
        FourPowerSwitch(coordinator, device_id, description)
        for device_id, device in coordinator.data.items()
        if (device.get("capabilities") or {}).get("outputControl")
        for description in DESCRIPTIONS
        if description.state_key in (device.get("state") or {})
    )


class FourPowerSwitch(FourPowerEntity, SwitchEntity):
    """A switchable spa output."""

    entity_description: FourPowerSwitchDescription

    def __init__(self, coordinator, device_id: str, description) -> None:
        super().__init__(coordinator, device_id, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        value = self._state.get(self.entity_description.state_key)
        return None if value is None else bool(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._async_set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._async_set(False)

    async def _async_set(self, value: bool) -> None:
        await async_send(
            self.coordinator, self._device_id, self.entity_description.command_key, value
        )


async def async_send(coordinator, device_id: str, output: str, value: Any) -> None:
    """Send one output and turn the cloud's verdict into an HA error.

    The cloud answers with a real outcome, so a refusal surfaces as a message
    the owner can act on rather than a switch that silently springs back.
    """
    try:
        await coordinator.api.async_command(device_id, output, value)
    except FourPowerSubscriptionRequired as err:
        raise HomeAssistantError(
            "This spa has no active 4Power subscription, so it cannot be controlled "
            "from Home Assistant"
        ) from err
    except FourPowerOffline as err:
        raise HomeAssistantError(
            "The spa is not reachable right now, so the command was not sent"
        ) from err
    except Exception as err:  # noqa: BLE001 — surfaced to the user
        raise HomeAssistantError(f"4Power refused the command: {err}") from err
    await coordinator.async_request_refresh_soon()
