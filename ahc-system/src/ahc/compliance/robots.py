"""robots.txt fetcher + path checker.

Uses Python's stdlib `urllib.robotparser` plus a thin wrapper to remember
crawl-delay and to make network failures safe (return an empty ruleset that
denies everything by default - Chapter 9 safety).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

from ..config import settings
from ..logging_setup import get_logger

log = get_logger(__name__)


@dataclass
class RobotsRules:
    """Parsed robots.txt snapshot. Empty rules deny everything by default."""
    base_url: str
    fetched_at: str = ""
    raw: str = ""
    crawl_delay: Optional[float] = None
    # The underlying parser is not serialisable; keep it as a private field.
    _parser: Optional[RobotFileParser] = field(default=None, repr=False)

    def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        if self._parser is None:
            return False
        try:
            return self._parser.can_fetch(user_agent, url)
        except Exception:
            return False


def fetch_robots_txt(base_url: str, *, timeout: int | None = None) -> RobotsRules:
    """Fetch and parse robots.txt for `base_url`.

    On any error (network, parse), returns an empty RobotsRules whose
    `can_fetch()` returns False - this is intentional (Chapter 9: when in
    doubt, deny).
    """
    parts = urlsplit(base_url)
    if not parts.scheme or not parts.netloc:
        return RobotsRules(base_url=base_url)

    robots_url = urlunsplit((parts.scheme, parts.netloc, "/robots.txt", "", ""))
    parser = RobotFileParser()
    parser.set_url(robots_url)

    try:
        # urllib.robotparser uses urllib underneath; we set a UA + timeout via
        # constructing the request manually for politeness.
        import urllib.request
        req = urllib.request.Request(
            robots_url,
            headers={"User-Agent": settings.user_agent},
        )
        with urllib.request.urlopen(req, timeout=timeout or settings.request_timeout) as r:
            body = r.read().decode("utf-8", errors="replace")
        parser.parse(body.splitlines())
        rules = RobotsRules(
            base_url=base_url,
            raw=body,
            _parser=parser,
        )
        try:
            rules.crawl_delay = parser.crawl_delay(settings.user_agent) or parser.crawl_delay("*")
        except Exception:
            pass
        return rules
    except Exception as e:
        log.warning("robots.txt fetch failed for %s: %s", base_url, e)
        return RobotsRules(base_url=base_url)


def is_path_allowed(rules: RobotsRules, path_or_url: str, user_agent: str = "*") -> bool:
    return rules.can_fetch(path_or_url, user_agent)
