"""Shared HTTP session factory for store adapters.

Provides a pre-configured ``requests.Session`` with:
  - the project User-Agent (``settings.user_agent``)
  - a default per-request timeout (``settings.request_timeout``)
  - a cooperative per-request rate limiter using ``time.sleep``

No network calls happen at import or construction time; the limiter only
sleeps when a request is actually sent through the session.
"""
from __future__ import annotations

import time
from typing import Optional

import requests

from ..config import settings


class RateLimitedSession(requests.Session):
    """``requests.Session`` subclass with a simple RPS limiter.

    Not thread-safe; create one session per worker. Sleeps *before* each
    request so calls are spaced at ``rps`` requests per second.
    """

    def __init__(self, *, rps: Optional[float] = None, timeout: Optional[int] = None):
        super().__init__()
        self._rps = rps if rps is not None else settings.request_rate_limit_rps
        self._timeout = timeout if timeout is not None else settings.request_timeout
        self._last_request_at = 0.0
        self.headers.update({
            "User-Agent": settings.user_agent,
            "Accept-Language": "en-US,en;q=0.9",
        })

    @property
    def min_interval(self) -> float:
        return 0.0 if self._rps <= 0 else 1.0 / self._rps

    def request(self, method, url, **kwargs):  # type: ignore[override]
        kwargs.setdefault("timeout", self._timeout)
        wait = self.min_interval - (time.monotonic() - self._last_request_at)
        if wait > 0:
            time.sleep(wait)
        self._last_request_at = time.monotonic()
        return super().request(method, url, **kwargs)


def new_http_session(
    *, rps: Optional[float] = None, timeout: Optional[int] = None
) -> RateLimitedSession:
    """Build a fresh rate-limited session configured from settings."""
    return RateLimitedSession(rps=rps, timeout=timeout)
