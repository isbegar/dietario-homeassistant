"""Alta de la integración desde la interfaz: URL de Dietario y token."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DietarioApi, DietarioAuthError, DietarioError
from .const import CONF_TOKEN, CONF_URL, DOMAIN


class DietarioConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _validate(self, url: str, token: str) -> tuple[dict[str, str], str | None]:
        errors: dict[str, str] = {}
        family = None
        try:
            data = await DietarioApi(async_get_clientsession(self.hass), url, token).summary()
            family = data.get("family") or "Dietario"
        except DietarioAuthError:
            errors["base"] = "invalid_auth"
        except DietarioError:
            errors["base"] = "cannot_connect"
        return errors, family

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            url = user_input[CONF_URL].strip().rstrip("/")
            if not url.startswith(("http://", "https://")):
                errors["base"] = "invalid_url"
            else:
                errors, family = await self._validate(url, user_input[CONF_TOKEN].strip())
                if not errors:
                    await self.async_set_unique_id(f"{url}")
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=family, data={CONF_URL: url, CONF_TOKEN: user_input[CONF_TOKEN].strip()}
                    )
        schema = vol.Schema({vol.Required(CONF_URL): str, vol.Required(CONF_TOKEN): str})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            errors, _ = await self._validate(entry.data[CONF_URL], user_input[CONF_TOKEN].strip())
            if not errors:
                return self.async_update_reload_and_abort(
                    entry, data={**entry.data, CONF_TOKEN: user_input[CONF_TOKEN].strip()}
                )
        return self.async_show_form(
            step_id="reauth_confirm", data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}), errors=errors
        )
