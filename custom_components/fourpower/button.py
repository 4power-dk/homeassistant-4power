"""One-shot spa commands."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import FourPowerConfigEntry
from .entity import FourPowerEntity
from .switch import async_send


@dataclass(frozen=True, kw_only=True)
class FourPowerButtonDescription(ButtonEntityDescription):
    """A command that runs to completion on its own."""

    # The key that must be present in reported state for the spa to have this
    # function at all — the command key is not always readable back.
    state_key: str
    command_key: str


DESCRIPTIONS: tuple[FourPowerButtonDescription, ...] = (
    # Filling is a ONE-SHOT: the spa starts filling and stops when it decides
    # to, and there is no way to cancel it. A switch would be a lie — it would
    # offer an "off" that does nothing, and would flip back by itself when the
    # firmware finished. A button says exactly what is on offer: start it.
    # Whether it is currently filling is the `Filling` binary sensor's job.
    FourPowerButtonDescription(
        key="fill_spa",
        state_key="aquaFilling",
        command_key="aquaFilling",
        translation_key="fill_spa",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: FourPowerConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create a button per one-shot command the spa supports."""
    coordinator = entry.runtime_data
    async_add_entities(
        FourPowerButton(coordinator, device_id, description)
        for device_id, device in coordinator.data.items()
        if (device.get("capabilities") or {}).get("outputControl")
        for description in DESCRIPTIONS
        if description.state_key in (device.get("state") or {})
    )


class FourPowerButton(FourPowerEntity, ButtonEntity):
    """A command the spa carries out once."""

    entity_description: FourPowerButtonDescription

    def __init__(self, coordinator, device_id: str, description) -> None:
        super().__init__(coordinator, device_id, description.key)
        self.entity_description = description

    async def async_press(self) -> None:
        await async_send(
            self.coordinator, self._device_id, self.entity_description.command_key, True
        )
