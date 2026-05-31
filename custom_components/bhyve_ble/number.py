from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTime
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import BhyveBleEntity
from .orbit_codec import MANUAL_WATER_RUN_SEC_MAX, MANUAL_WATER_RUN_SEC_MIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

    from .coordinator import BhyveBleCoordinator
    from .hub import BhyveBleHub


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    hub: BhyveBleHub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        BhyveBleManualRunTimeNumber(coordinator) for coordinator in hub.coordinators.values()
    )


class BhyveBleManualRunTimeNumber(BhyveBleEntity, NumberEntity):
    """Run duration (seconds) sent to the timer when a station switch is turned on.

    Lets automations request an exact watering time and let the valve self-time and
    self-stop, instead of the old hardcoded 600 s. Default 600 preserves prior behavior.
    """

    _attr_has_entity_name = True
    _attr_name = "Run Duration"
    _attr_icon = "mdi:timer-cog-outline"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = float(MANUAL_WATER_RUN_SEC_MIN)
    _attr_native_max_value = float(MANUAL_WATER_RUN_SEC_MAX)
    _attr_native_step = 15.0
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS

    def __init__(self, coordinator: BhyveBleCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = (
            f"{coordinator.entry.entry_id}_{coordinator.address}_manual_run_time"
        )

    @property
    def native_value(self) -> float:
        return float(self.coordinator.manual_run_time_sec)

    async def async_set_native_value(self, value: float) -> None:
        self.coordinator.manual_run_time_sec = int(value)
        self.async_write_ha_state()
