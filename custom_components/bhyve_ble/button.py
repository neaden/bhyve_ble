from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import BhyveBleEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

    from .coordinator import BhyveBleCoordinator
    from .hub import BhyveBleHub


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    hub: BhyveBleHub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        BhyveBleRefreshStatusButton(coordinator) for coordinator in hub.coordinators.values()
    )


class BhyveBleRefreshStatusButton(BhyveBleEntity, ButtonEntity):
    """Runs the same BLE poll as the coordinator interval (device info + device status)."""

    _attr_has_entity_name = True
    _attr_translation_key = "refresh_status"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator: BhyveBleCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{coordinator.address}_refresh_status"

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()
