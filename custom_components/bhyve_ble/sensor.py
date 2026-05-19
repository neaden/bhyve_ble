from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import PERCENTAGE
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import BhyveBleEntity
from .orbit_codec import (
    parse_battery_percent_mv_from_decoded,
    resolve_battery_percent_display,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

    from .coordinator import BhyveBleCoordinator
    from .hub import BhyveBleHub


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    hub: BhyveBleHub = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []
    for coordinator in hub.coordinators.values():
        entities.extend(
            [
                BhyveBleLastOneofSensor(coordinator),
                BhyveBleBatterySensor(coordinator),
                BhyveBleBatteryMvSensor(coordinator),
                BhyveBleNumStationsSensor(coordinator),
            ]
        )
    async_add_entities(entities)


class BhyveBleLastOneofSensor(BhyveBleEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: BhyveBleCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{coordinator.address}_last_oneof"
        self._attr_name = "Last message type"

    @property
    def native_value(self) -> str:
        msg = (self.coordinator.data or {}).get("last_message") or {}
        framing = msg.get("_framing") or {}
        return framing.get("oneof") or "unknown"


class BhyveBleNumStationsSensor(BhyveBleEntity, SensorEntity):
    """Reports ``deviceInfo.numStations`` (number of valve ports)."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: BhyveBleCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{coordinator.address}_num_stations"
        self._attr_name = "Output Ports"

    @property
    def native_value(self) -> int:
        return self.coordinator.num_stations


class BhyveBleBatterySensor(BhyveBleEntity, SensorEntity):
    """``batteryLevelPercent`` when sent; otherwise estimated from ``batteryLevelMV``."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator: BhyveBleCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{coordinator.address}_battery"
        self._attr_name = "Battery"

    def _battery_fields(self) -> tuple[int | None, int | None, str | None]:
        last = (self.coordinator.data or {}).get("last_message")
        pct, mv = parse_battery_percent_mv_from_decoded(last)
        display_pct, source = resolve_battery_percent_display(pct, mv)
        return display_pct, mv, source

    @property
    def native_value(self) -> int | None:
        display_pct, _mv, _source = self._battery_fields()
        return display_pct

    @property
    def extra_state_attributes(self) -> dict[str, int | str]:
        display_pct, mv, source = self._battery_fields()
        attrs: dict[str, int | str] = {}
        if mv is not None:
            attrs["voltage_mv"] = mv
        if source is not None:
            attrs["battery_percent_source"] = source
        if source == "estimated_mv" and display_pct is not None:
            attrs["battery_percent_note"] = (
                "Device sent mV only; percent estimated from voltage (2400-3000 mV)."
            )
        return attrs


class BhyveBleBatteryMvSensor(BhyveBleEntity, SensorEntity):
    """Millivolts from ``deviceStatusInfo`` payload."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = "mV"

    def __init__(self, coordinator: BhyveBleCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{coordinator.address}_battery_mv"
        self._attr_name = "Battery (mV)"

    @property
    def native_value(self) -> int | None:
        last = (self.coordinator.data or {}).get("last_message")
        _pct, mv = parse_battery_percent_mv_from_decoded(last)
        return mv
