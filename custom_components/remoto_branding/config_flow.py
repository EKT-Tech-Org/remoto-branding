"""Config flow for Remoto Branding."""

from __future__ import annotations

import re
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback

from .const import (
    CONF_BRAND_NAME,
    CONF_PRIMARY_COLOR,
    DEFAULT_BRAND_NAME,
    DEFAULT_PRIMARY_COLOR,
    DOMAIN,
)

HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_BRAND_NAME,
                default=defaults.get(CONF_BRAND_NAME, DEFAULT_BRAND_NAME),
            ): str,
            vol.Required(
                CONF_PRIMARY_COLOR,
                default=defaults.get(CONF_PRIMARY_COLOR, DEFAULT_PRIMARY_COLOR),
            ): str,
        }
    )


def _validate(user_input: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    if not user_input[CONF_BRAND_NAME].strip():
        errors[CONF_BRAND_NAME] = "empty_name"
    if not HEX_COLOR.match(user_input[CONF_PRIMARY_COLOR]):
        errors[CONF_PRIMARY_COLOR] = "invalid_color"
    return errors


class RemotoBrandingConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _validate(user_input)
            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_BRAND_NAME], data=user_input
                )
        return self.async_show_form(
            step_id="user", data_schema=_schema(user_input or {}), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return RemotoBrandingOptionsFlow()


class RemotoBrandingOptionsFlow(OptionsFlow):
    """Change brand name or color later."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _validate(user_input)
            if not errors:
                return self.async_create_entry(data=user_input)
        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init", data_schema=_schema(user_input or current), errors=errors
        )
