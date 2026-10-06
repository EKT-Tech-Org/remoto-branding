"""Register the Remoto theme in code and make it the default for all users.

No YAML is needed: the theme is added to the frontend's theme registry at
startup, and added again whenever an admin reloads themes from YAML.
"""

from __future__ import annotations

from collections.abc import Callable
import logging

from homeassistant.const import EVENT_THEMES_UPDATED
from homeassistant.core import Event, HomeAssistant, callback

_LOGGER = logging.getLogger(__name__)

# Frontend internals (homeassistant/components/frontend/__init__.py).
DATA_THEMES = "frontend_themes"
DATA_DEFAULT_THEME = "frontend_default_theme"
STOCK_THEME = "default"

ACCENT = "#59C7C4"  # brand teal
DARK_PRIMARY = "#7ED3CA"  # brand teal-soft, readable on dark grounds


def build_theme(primary: str) -> dict:
    """The Remoto theme for a given primary color."""
    return {
        "primary-color": primary,
        "accent-color": ACCENT,
        "app-header-background-color": primary,
        "app-header-text-color": "#FFFFFF",
        "sidebar-selected-icon-color": primary,
        "sidebar-selected-text-color": primary,
        "state-icon-active-color": ACCENT,
        "ha-card-border-radius": "16px",
        "modes": {
            "dark": {
                "primary-color": DARK_PRIMARY,
                "app-header-background-color": "#2B1F52",
                "sidebar-selected-icon-color": DARK_PRIMARY,
                "sidebar-selected-text-color": DARK_PRIMARY,
            }
        },
    }


async def async_install_theme(
    hass: HomeAssistant, name: str, primary: str
) -> Callable[[], None] | None:
    """Add the theme, make it default if no other theme was chosen. Returns undo."""
    if not isinstance(hass.data.get(DATA_THEMES), dict):
        _LOGGER.warning("Theme registry changed upstream; Remoto theme not installed")
        return None

    theme = build_theme(primary)

    async def _ensure(fire: bool) -> None:
        themes = hass.data.get(DATA_THEMES)
        if not isinstance(themes, dict):
            return
        missing = themes.get(name) != theme
        if missing:
            themes[name] = theme
        if hass.data.get(DATA_DEFAULT_THEME, STOCK_THEME) == STOCK_THEME:
            # The stock service persists the choice and notifies open browsers.
            await hass.services.async_call("frontend", "set_theme", {"name": name})
        elif missing and fire:
            hass.bus.async_fire(EVENT_THEMES_UPDATED)

    await _ensure(fire=True)

    @callback
    def _on_themes_updated(event: Event) -> None:
        # A YAML theme reload replaces the registry; put Remoto back.
        themes = hass.data.get(DATA_THEMES)
        if isinstance(themes, dict) and themes.get(name) != theme:
            hass.async_create_task(_ensure(fire=True))

    unsub = hass.bus.async_listen(EVENT_THEMES_UPDATED, _on_themes_updated)

    def _undo() -> None:
        unsub()

    return _undo
