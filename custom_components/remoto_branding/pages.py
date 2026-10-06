"""Server-side branding of the HTML shells (main app and login page).

remoto.js handles everything after the app boots, but two things load before it:
- the main app's launch screen (logo, "a project from..." footer, tab title)
- the login page, a static file that `add_extra_js_url` never reaches.

Both are patched here with plain string replacements. If upstream markup
changes, unmatched replacements are skipped and the page is served
unchanged, so the UI never breaks. The e2e check reports the regression.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
import html
import logging
from pathlib import Path
import re

from aiohttp import web
import jinja2

from homeassistant.core import HomeAssistant

from .const import URL_BASE

_LOGGER = logging.getLogger(__name__)

AUTHORIZE_PATH = "/auth/authorize"
INDEX_RESOURCE_NAME = "frontend:index"

_ITUNES_META = re.compile(r'<meta name="apple-itunes-app"[^>]*>\s*')
_TITLE = re.compile(r"<title>[^<]*</title>")


def brand_html(markup: str, brand: str, version: str, script_url: str | None) -> str:
    """Rewrite the static shell of a page. Safe to call on any upstream HTML."""
    name = html.escape(brand).replace("{", "").replace("}", "")  # also Jinja-safe
    v = f"?v={version}"
    replacements = {
        'content="Home Assistant"': f'content="{name}"',
        'alt="Home Assistant"': f'alt="{name}"',
        "/static/images/home-assistant-logo-loading.svg": f"{URL_BASE}/icons/logo.svg{v}",
        'href="/manifest.json"': f'href="{URL_BASE}/manifest.json{v}"',
        "/static/icons/favicon-apple-180x180.png": f"{URL_BASE}/icons/apple-touch-icon.png{v}",
        'href="/static/icons/favicon.ico"': f'href="{URL_BASE}/icons/favicon.png{v}"',
    }
    for old, new in replacements.items():
        markup = markup.replace(old, new)
    markup = _TITLE.sub(f"<title>{name}</title>", markup, count=1)
    markup = _ITUNES_META.sub("", markup)

    head = "<style>.ohf-logo{display:none!important}</style>"
    if script_url:
        head += f'<script type="module" src="{script_url}"></script>'
    return markup.replace("</head>", f"{head}</head>", 1)


def _find_authorize_route(hass: HomeAssistant) -> web.AbstractRoute | None:
    for route in hass.http.app.router.routes():
        resource = route.resource
        if route.method == "GET" and resource and resource.canonical == AUTHORIZE_PATH:
            return route
    return None


def _find_index_view(hass: HomeAssistant):
    for resource in hass.http.app.router.resources():
        if getattr(resource, "name", None) == INDEX_RESOURCE_NAME and hasattr(
            resource, "get_template"
        ):
            return resource
    return None


async def async_patch_login_page(
    hass: HomeAssistant, brand: str, version: str, script_url: str
) -> Callable[[], None] | None:
    """Serve a branded copy of the login page. Returns an undo callable."""
    route = _find_authorize_route(hass)
    original = getattr(route, "_handler", None)
    # The stock handler is partial(_serve_file, "<frontend>/authorize.html").
    if not (
        isinstance(original, partial)
        and original.args
        and Path(str(original.args[0])).name == "authorize.html"
    ):
        _LOGGER.warning("Login page layout changed upstream; login stays unbranded")
        return None

    path = Path(str(original.args[0]))
    markup = await hass.async_add_executor_job(path.read_text, "utf-8")
    patched = brand_html(markup, brand, version, script_url)

    async def _serve_branded(request: web.Request) -> web.Response:
        return web.Response(
            text=patched, content_type="text/html", headers={"Cache-Control": "no-cache"}
        )

    route._handler = _serve_branded  # noqa: SLF001

    def _restore() -> None:
        route._handler = original  # noqa: SLF001

    return _restore


async def async_patch_index(
    hass: HomeAssistant, brand: str, version: str
) -> Callable[[], None] | None:
    """Brand the main app shell (launch screen, title, icons). Returns an undo callable."""
    view = _find_index_view(hass)
    if view is None or getattr(view, "repo_path", None) is not None:
        _LOGGER.warning("Frontend index layout changed upstream; launch screen unbranded")
        return None

    original = await hass.async_add_executor_job(view.get_template)
    path = await hass.async_add_executor_job(_index_path)
    if path is None:
        return None
    markup = await hass.async_add_executor_job(path.read_text, "utf-8")
    # The script is already injected through extra_modules on this page.
    view._template_cache = jinja2.Template(brand_html(markup, brand, version, None))  # noqa: SLF001

    def _restore() -> None:
        view._template_cache = original  # noqa: SLF001

    return _restore


def _index_path() -> Path | None:
    try:
        import hass_frontend  # noqa: PLC0415

        path = Path(hass_frontend.where()) / "index.html"
    except (ImportError, AttributeError):
        _LOGGER.warning("Frontend package not found; launch screen unbranded")
        return None
    return path if path.is_file() else None
