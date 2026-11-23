"""Cliente de la API de Dietario (/ha-api/v1)."""
from __future__ import annotations

from typing import Any

import aiohttp


class DietarioError(Exception):
    """Error genérico de la API."""


class DietarioAuthError(DietarioError):
    """Token rechazado."""


class DietarioConnectionError(DietarioError):
    """No se pudo conectar."""


class DietarioApi:
    def __init__(self, session: aiohttp.ClientSession, url: str, token: str) -> None:
        self._session = session
        self._base = url.rstrip("/") + "/ha-api/v1"
        self._headers = {"Authorization": f"Bearer {token}"}

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            async with self._session.request(
                method,
                self._base + path,
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=15),
                **kwargs,
            ) as resp:
                if resp.status in (401, 403):
                    raise DietarioAuthError("Token no válido")
                if resp.status >= 400:
                    try:
                        data = await resp.json()
                        msg = data.get("error", resp.reason)
                    except Exception:  # noqa: BLE001
                        msg = resp.reason
                    raise DietarioError(f"{resp.status}: {msg}")
                return await resp.json()
        except aiohttp.ClientError as err:
            raise DietarioConnectionError(str(err)) from err
        except TimeoutError as err:
            raise DietarioConnectionError("Tiempo de espera agotado") from err

    async def summary(self) -> dict[str, Any]:
        return await self._request("GET", "/summary")

    async def meals(self, start: str, end: str) -> list[dict[str, Any]]:
        data = await self._request("GET", "/meals", params={"from": start, "to": end})
        return data["meals"]

    async def shopping(self) -> list[dict[str, Any]]:
        return (await self._request("GET", "/shopping"))["items"]

    async def add_item(self, name: str, qty: str = "") -> dict[str, Any]:
        return await self._request("POST", "/shopping", json={"name": name, "qty": qty})

    async def set_checked(self, item_id: str, checked: bool) -> dict[str, Any]:
        return await self._request("PATCH", f"/shopping/{item_id}", json={"checked": checked})

    async def remove_item(self, item_id: str) -> None:
        await self._request("DELETE", f"/shopping/{item_id}")
