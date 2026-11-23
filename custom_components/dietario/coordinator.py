"""Coordinador de datos de Dietario."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DietarioApi, DietarioAuthError, DietarioError
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class DietarioCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Descarga el resumen y la lista de la compra cada pocos minutos."""

    def __init__(self, hass: HomeAssistant, api: DietarioApi, name: str) -> None:
        super().__init__(hass, _LOGGER, name=f"{DOMAIN} {name}", update_interval=SCAN_INTERVAL)
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            summary = await self.api.summary()
            items = await self.api.shopping()
        except DietarioAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except DietarioError as err:
            raise UpdateFailed(str(err)) from err
        return {"summary": summary, "items": items}
