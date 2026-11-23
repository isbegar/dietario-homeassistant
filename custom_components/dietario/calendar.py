"""Calendario con las comidas y cenas de la semana."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN, SLOT_NAMES, SLOT_TIMES
from .coordinator import DietarioCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([DietarioCalendar(hass.data[DOMAIN][entry.entry_id], entry)])


def _to_event(meal: dict) -> CalendarEvent:
    day = date.fromisoformat(meal["date"])
    (sh, sm), (eh, em) = SLOT_TIMES[meal["slot"]]
    tz = dt_util.DEFAULT_TIME_ZONE
    description = meal.get("summary") or ""
    if meal.get("prepAhead"):
        description += f"\nPreparar antes: {meal['prepAhead']}"
    return CalendarEvent(
        start=datetime.combine(day, time(sh, sm), tzinfo=tz),
        end=datetime.combine(day, time(eh, em), tzinfo=tz),
        summary=f"{SLOT_NAMES.get(meal['slot'], '')}: {meal['title']}",
        description=description.strip() or None,
    )


class DietarioCalendar(CalendarEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "meals"
    _attr_icon = "mdi:silverware-fork-knife"

    def __init__(self, coordinator: DietarioCoordinator, entry: ConfigEntry) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)}, name=entry.title, manufacturer="Dietario", entry_type=DeviceEntryType.SERVICE
        )
        self._event: CalendarEvent | None = None

    @property
    def event(self) -> CalendarEvent | None:
        return self._event

    async def async_update(self) -> None:
        """Próxima comida (o la que está en curso)."""
        now = dt_util.now()
        today = now.date()
        meals = await self._coordinator.api.meals(today.isoformat(), (today + timedelta(days=7)).isoformat())
        upcoming = [e for e in map(_to_event, meals) if e.end > now]
        self._event = min(upcoming, key=lambda e: e.start) if upcoming else None

    async def async_get_events(self, hass: HomeAssistant, start_date: datetime, end_date: datetime) -> list[CalendarEvent]:
        start = dt_util.as_local(start_date).date()
        end = dt_util.as_local(end_date).date()
        meals = await self._coordinator.api.meals(start.isoformat(), end.isoformat())
        return [e for e in map(_to_event, meals) if e.end > start_date and e.start < end_date]
