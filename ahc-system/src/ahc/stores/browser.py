"""Thin Playwright wrapper for store adapters.

Exposes :func:`new_browser_context`, a context manager yielding a
``(browser, page)`` tuple. Reads ``settings.playwright_headless`` for the
launch mode and applies a realistic desktop User-Agent + viewport so
JS-rendered storefronts (cart drawers, coupon inputs) behave like a real
browser session.

Playwright is imported **lazily**: this module never imports it at load
time, so the rest of the package works on a host where Playwright (or its
browser binaries) is not installed. The ``ImportError`` is raised only
when a caller actually enters the context manager.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Optional, Tuple

from ..config import settings

_DESKTOP_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
_DESKTOP_VIEWPORT = {"width": 1366, "height": 768}


def _import_playwright():
    """Import ``playwright.sync_api`` lazily, with a helpful error if missing."""
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError(
            "Playwright is required for browser-mode store operations but is "
            "not installed. Install it with:\n"
            "  pip install 'playwright>=1.42'\n"
            "  python -m playwright install chromium\n"
            "Then retry."
        ) from exc
    return sync_playwright


@contextmanager
def new_browser_context(
    *, headless: Optional[bool] = None
) -> Iterator[Tuple[object, object]]:
    """Yield a ``(browser, page)`` tuple for browser-mode adapter operations.

    The browser is closed when the context exits. ``headless`` defaults to
    ``settings.playwright_headless``.
    """
    sync_playwright = _import_playwright()
    headless = settings.playwright_headless if headless is None else headless
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        try:
            context = browser.new_context(
                user_agent=_DESKTOP_UA,
                viewport=_DESKTOP_VIEWPORT,
            )
            page = context.new_page()
            yield browser, page
        finally:
            browser.close()
