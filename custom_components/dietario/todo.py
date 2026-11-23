"""Lista de la compra como lista de tareas de Home Assistant (se sincroniza con la web)."""
from __future__ import annotations

from homeassistant.components.todo import TodoItem, TodoItemStatus, TodoListEntity, TodoListEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import DietarioError
from .const import DOMAIN
from .coordinator import DietarioCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([DietarioShoppingList(hass.data[DOMAIN][entry.entry_id], entry)])


class DietarioShoppingList(CoordinatorEntity[DietarioCoordinator], TodoListEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "shopping"
    _attr_icon = "mdi:cart"
    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
    )

    def __init__(self, coordinator: DietarioCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_shopping"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)}, name=entry.title, manufacturer="Dietario", entry_type=DeviceEntryType.SERVICE
        )

    @property
    def todo_items(self) -> list[TodoItem]:
        return [
            TodoItem(
                uid=i["id"],
                summary=f"{i['name']} ({i['qty']})" if i.get("qty") else i["name"],
                status=TodoItemStatus.COMPLETED if i["checked"] else TodoItemStatus.NEEDS_ACTION,
                description=i.get("section") or None,
            )
            for i in self.coordinator.data["items"]
        ]

    async def _run(self, coro) -> None:
        try:
            await coro
        except DietarioError as err:
            raise HomeAssistantError(f"Dietario: {err}") from err
        await self.coordinator.async_request_refresh()

    async def async_create_todo_item(self, item: TodoItem) -> None:
        await self._run(self.coordinator.api.add_item((item.summary or "").strip()))

    async def async_update_todo_item(self, item: TodoItem) -> None:
        if item.status is not None:
            await self._run(self.coordinator.api.set_checked(item.uid, item.status == TodoItemStatus.COMPLETED))

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        for uid in uids:
            try:
                await self.coordinator.api.remove_item(uid)
            except DietarioError as err:
                raise HomeAssistantError(f"Dietario: {err}") from err
        await self.coordinator.async_request_refresh()
