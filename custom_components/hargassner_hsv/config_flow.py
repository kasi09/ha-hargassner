"""Config flow for the Hargassner HSV integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from . import api_supported
from .api import HargassnerApi, HargassnerApiError, HargassnerAuthError
from .const import DEFAULT_PORT, DOMAIN

TOKEN_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=65535)
        ),
        vol.Required(CONF_TOKEN): TOKEN_SELECTOR,
    }
)


async def _validate(hass, data: Mapping[str, Any]) -> tuple[dict | None, str | None]:
    api = HargassnerApi(
        async_get_clientsession(hass), data[CONF_HOST], data[CONF_PORT], data[CONF_TOKEN]
    )
    try:
        info = await api.info()
    except HargassnerAuthError:
        return None, "invalid_auth"
    except HargassnerApiError:
        return None, "cannot_connect"
    if not api_supported(info) or "installation_id" not in info:
        return None, "unsupported_api"
    return info, None


class HargassnerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hargassner HSV."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            info, error = await _validate(self.hass, user_input)
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(info["installation_id"])
                self._abort_if_unique_id_configured(updates=user_input)
                return self.async_create_entry(
                    title=f"{info.get('manufacturer', 'Hargassner')} {info.get('model', '')}".strip(),
                    data=user_input,
                )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(USER_SCHEMA, user_input),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            data = {**entry.data, CONF_TOKEN: user_input[CONF_TOKEN]}
            info, error = await _validate(self.hass, data)
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(info["installation_id"])
                self._abort_if_unique_id_mismatch(reason="wrong_installation")
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_TOKEN: user_input[CONF_TOKEN]}
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_TOKEN): TOKEN_SELECTOR}),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            info, error = await _validate(self.hass, user_input)
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(info["installation_id"])
                self._abort_if_unique_id_mismatch(reason="wrong_installation")
                return self.async_update_reload_and_abort(entry, data_updates=user_input)
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                USER_SCHEMA, user_input or entry.data
            ),
            errors=errors,
        )
