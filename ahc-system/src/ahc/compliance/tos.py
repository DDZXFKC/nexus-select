"""ToS excerpt extraction.

A *very* conservative scanner: fetch the store's ToS page (if linked from
the homepage footer), look for explicit "no bots / no scraping / no
automated purchases" language. We deliberately bias toward False-negative
risk: if we cannot find a clear statement either way, we mark the policy
as `manual` (require a human to read it).

This is NOT a legal determination - it is a triage signal for the
compliance gate. The final word is the manual verdict in
config/compliance.yaml.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

import requests
from bs4 import BeautifulSoup

from ..config import settings
from ..logging_setup import get_logger

log = get_logger(__name__)


_NEGATIVE_PATTERNS = [
    re.compile(r"\bno\s+automated\s+(?:access|purchases|ordering|buying)\b", re.I),
    re.compile(r"\bprohibit(?:ed)?\s+(?:the\s+use\s+of\s+)?(?:bots|robots|spiders|scrapers)\b", re.I),
    re.compile(r"\bmay\s+not\s+use\s+(?:any\s+)?(?:automated|bot|robot)\b", re.I),
    re.compile(r"\bscrap(?:e|ing|ed)\b.*\bprohibit", re.I),
    re.compile(r"\bno\s+(?:spider|crawler|scraper|bot)\b", re.I),
]

_POSITIVE_PATTERNS = [
    re.compile(r"\ballows?\s+(?:automated\s+)?(?:access|scraping)\b", re.I),
    re.compile(r"\b(?:public|open)\s+api\b", re.I),
]


@dataclass
class TosPolicy:
    url: str
    excerpt: str = ""
    fetched_at: str = ""
    # allowed = True only when we found explicit permission; False when we found
    # explicit prohibition; None when unclear (fall back to manual).
    allowed: Optional[bool] = None
    matched_phrases: list[str] = field(default_factory=list)


def _find_tos_link(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    candidates = []
    for a in soup.find_all("a", href=True):
        text = a.get_text(" ", strip=True).lower()
        if any(k in text for k in ("terms", "terms of service", "terms of use",
                                    "agb", "impressum", "bedingungen",
                                    "conditions")):
            candidates.append(a["href"])
    if not candidates:
        return None
    # Prefer absolute https links; else resolve relative.
    href = candidates[0]
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        from urllib.parse import urlsplit, urlunsplit
        parts = urlsplit(base_url)
        return urlunsplit((parts.scheme, parts.netloc, href, "", ""))
    return None


def extract_tos_excerpt(
    base_url: str,
    *,
    http_session: Optional[requests.Session] = None,
    timeout: int | None = None,
) -> TosPolicy:
    """Fetch the homepage, follow the first ToS-looking link, scan the text.

    On any failure returns TosPolicy(url=base_url, allowed=None) - i.e. unknown.
    """
    sess = http_session or requests.Session()
    try:
        r = sess.get(
            base_url,
            timeout=timeout or settings.request_timeout,
            headers={"User-Agent": settings.user_agent},
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
    except Exception as e:
        log.warning("ToS scan: homepage fetch failed for %s: %s", base_url, e)
        return TosPolicy(url=base_url)

    tos_url = _find_tos_link(soup, base_url)
    if not tos_url:
        return TosPolicy(url=base_url)

    try:
        r2 = sess.get(
            tos_url,
            timeout=timeout or settings.request_timeout,
            headers={"User-Agent": settings.user_agent},
        )
        r2.raise_for_status()
        text = BeautifulSoup(r2.text, "lxml").get_text(" ", strip=True)
    except Exception as e:
        log.warning("ToS scan: ToS page fetch failed for %s: %s", tos_url, e)
        return TosPolicy(url=tos_url)

    # Take a window around the first negative or positive hit for the excerpt.
    matched: list[str] = []
    allowed: Optional[bool] = None
    for pat in _NEGATIVE_PATTERNS:
        m = pat.search(text)
        if m:
            matched.append(m.group(0))
            allowed = False
    for pat in _POSITIVE_PATTERNS:
        m = pat.search(text)
        if m:
            matched.append(m.group(0))
            if allowed is None:
                allowed = True

    excerpt = ""
    if matched:
        # 300 chars around the first match
        first = text.find(matched[0])
        excerpt = text[max(0, first - 150): first + 150]

    return TosPolicy(
        url=tos_url,
        excerpt=excerpt,
        allowed=allowed,
        matched_phrases=matched,
    )
