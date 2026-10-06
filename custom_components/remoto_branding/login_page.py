"""Inject the branding script into the login page.

The login page (/auth/authorize) is served as a plain static file, so
`add_extra_js_url` does not reach it. We swap that route's handler for one that
serves the same file with our <script> tag added. If the upstream layout ever
changes, this logs a warning and leaves the stock login page untouched.
"""

from __future__ import annotations

from functools import partial
import logging
from pathlib import Path

from aiohttp import web

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

AUTHORIZE_PATH = "/auth/authorize"


def _find_route(hass: HomeAssistant) -> web.AbstractRoute | None:
    for route in hass.http.app.router.routes():
        if (
            route.method == "GET"
            and route.resource is not None
            and route.resource.canonical == AUTHORIZE_PATH
        ):
            return route
    return None


def _original_file(handler) -> Path | None:
    """The stock handler is partial(_serve_file, '<frontend>/authorize.html')."""
    if isinstance(handler, partial) and handler.args:
        path = Path(str(handler.args[0]))
        if path.name == "authorize.html":
            return path
    return None


async def async_patch_login_page(hass: HomeAssistant, script_url: str):
    """Patch the login route. Returns a callable that restores it, or None."""
    route = _find_route(hass)
    original = getattr(route, "_handler", None)
    path = _original_file(original)
    if route is None or path is None:
        _LOGGER.warning("Login page layout changed upstream; login stays unbranded")
        return None

    html = await hass.async_add_executor_job(path.read_text, "utf-8")
    tag = f'<script type="module" src="{script_url}"></script>'
    if "</head>" not in html:
        _LOGGER.warning("Unexpected login page markup; login stays unbranded")
        return None
    patched = html.replace("</head>", f"{tag}</head>", 1)

    async def _serve_branded(request: web.Request) -> web.Response:
        return web.Response(
            text=patched,
            content_type="text/html",
            headers={"Cache-Control": "no-cache"},
        )

    route._handler = _serve_branded  # noqa: SLF001

    def _restore() -> None:
        route._handler = original  # noqa: SLF001

    return _restore
