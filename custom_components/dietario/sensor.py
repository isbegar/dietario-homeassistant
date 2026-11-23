"""Sensores: menú de hoy y mañana, preparación para mañana y artículos pendientes de la compra."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SLOT_DINNER, SLOT_LUNCH
from .coordinator import DietarioCoordinator


def _meal(day: str, slot: str) -> Callable[[dict[str, Any]], dict[str, Any] | None]:
    return lambda s: (s.get(day) or {}).get(slot)


@dataclass(frozen=True, kw_only=True)
class DietarioSensorDescription(SensorEntityDescription):
    meal: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None


MEAL_SENSORS = (
    DietarioSensorDescription(key="today_lunch", translation_key="today_lunch", icon="mdi:food", meal=_meal("today", SLOT_LUNCH)),
    DietarioSensorDescription(key="today_dinner", translation_key="today_dinner", icon="mdi:food-variant", meal=_meal("today", SLOT_DINNER)),
    DietarioSensorDescription(key="tomorrow_lunch", translation_key="tomorrow_lunch", icon="mdi:food", meal=_meal("tomorrow", SLOT_LUNCH)),
    DietarioSensorDescription(key="tomorrow_dinner", translation_key="tomorrow_dinner", icon="mdi:food-variant", meal=_meal("tomorrow", SLOT_DINNER)),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: DietarioCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [DietarioMealSensor(coordinator, entry, d) for d in MEAL_SENSORS]
    entities.append(DietarioPrepSensor(coordinator, entry))
    entities.append(DietarioShoppingSensor(coordinator, entry))
    async_add_entities(entities)


class _Base(CoordinatorEntity[DietarioCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: DietarioCoordinator, entry: ConfigEntry, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)}, name=entry.title, manufacturer="Dietario", entry_type=DeviceEntryType.SERVICE
        )

    @property
    def _summary(self) -> dict[str, Any]:
        return self.coordinator.data["summary"]


class DietarioMealSensor(_Base):
    entity_description: DietarioSensorDescription

    def __init__(self, coordinator: DietarioCoordinator, entry: ConfigEntry, description: DietarioSensorDescription) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def _current(self) -> dict[str, Any] | None:
        return self.entity_description.meal(self._summary)

    @property
    def native_value(self) -> str | None:
        return self._current["title"] if self._current else "Sin planificar"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        m = self._current or {}
        return {
            "resumen": m.get("summary", ""),
            "preparar_antes": m.get("prepAhead", ""),
            "etiquetas": m.get("tags", []),
            "puntuacion": m.get("rating"),
            "fecha": self._summary.get("date"),
        }


class DietarioPrepSensor(_Base):
    _attr_translation_key = "prep_tomorrow"
    _attr_icon = "mdi:clock-check-outline"

    def __init__(self, coordinator: DietarioCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "prep_tomorrow")

    @property
    def native_value(self) -> int:
        return len(self._summary.get("prep_for_tomorrow", []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        items = self._summary.get("prep_for_tomorrow", [])
        return {
            "tareas": items,
            "texto": "\n".join(f"{i['title']}: {i['prepAhead']}" for i in items),
        }


class DietarioShoppingSensor(_Base):
    _attr_translation_key = "shopping_pending"
    _attr_icon = "mdi:cart"
    _attr_native_unit_of_measurement = "artículos"

    def __init__(self, coordinator: DietarioCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "shopping_pending")

    @property
    def native_value(self) -> int:
        return sum(1 for i in self.coordinator.data["items"] if not i["checked"])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"total": len(self.coordinator.data["items"])}
