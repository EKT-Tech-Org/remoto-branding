"""Remoto Branding: white-label the frontend."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlencode

from homeassistant.components.frontend import add_extra_js_url, remove_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import (
    CONF_BRAND_NAME,
    CONF_PRIMARY_COLOR,
    DEFAULT_BRAND_NAME,
    DEFAULT_PRIMARY_COLOR,
    DOMAIN,
    URL_BASE,
)
from .pages import async_patch_index, async_patch_login_page

WWW_DIR = Path(__file__).parent / "www"


def _brand(entry: ConfigEntry) -> str:
    return entry.options.get(
        CONF_BRAND_NAME, entry.data.get(CONF_BRAND_NAME, DEFAULT_BRAND_NAME)
    )


def _script_url(entry: ConfigEntry, version: str) -> str:
    """Build the script URL; options travel as query params read via import.meta.url."""
    params = {
        "v": version,
        "name": _brand(entry),
        "color": entry.options.get(
            CONF_PRIMARY_COLOR,
            entry.data.get(CONF_PRIMARY_COLOR, DEFAULT_PRIMARY_COLOR),
        ),
    }
    return f"{URL_BASE}/remoto.js?{urlencode(params)}"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Serve branding assets and inject the branding script."""
    domain_data = hass.data.setdefault(DOMAIN, {})

    # Static routes cannot be unregistered, so only add them once per run.
    if not domain_data.get("static_registered"):
        await hass.http.async_register_static_paths(
            [StaticPathConfig(URL_BASE, str(WWW_DIR), False)]
        )
        domain_data["static_registered"] = True

    integration = await async_get_integration(hass, DOMAIN)
    version = str(integration.version)
    brand = _brand(entry)
    url = _script_url(entry, version)
    add_extra_js_url(hass, url)
    domain_data["script_url"] = url
    domain_data["restore"] = [
        undo
        for undo in (
            await async_patch_login_page(hass, brand, version, url),
            await async_patch_index(hass, brand, version),
        )
        if undo
    ]

    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Stop injecting the branding script."""
    if url := hass.data.get(DOMAIN, {}).pop("script_url", None):
        remove_extra_js_url(hass, url)
    for undo in hass.data.get(DOMAIN, {}).pop("restore", []):
        undo()
    return True


async def _async_reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
