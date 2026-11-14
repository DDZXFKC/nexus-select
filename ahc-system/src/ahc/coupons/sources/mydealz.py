"""mydealz (https://www.mydealz.de) coupon / deal source adapter.

mydealz exposes a single public RSS feed at ``https://www.mydealz.de/rss/v2/threads``
which we parse with the stdlib ``xml.etree.ElementTree``. We do **not** scrape
HTML — only this one RSS endpoint is used, which is the documented public
interface.

mydealz posts are community deals, not always code-based coupons, so each
item is emitted as a ``RawCoupon`` with an empty ``code`` and
``discount_type='other'``. The deduplicator handles the empty-code case
(multi-store coupons are bucketed per source).
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional

from ..base import AbstractCouponSource, RawCoupon
from ...config import settings
from ...logging_setup import get_logger

log = get_logger(__name__)

#: The only public mydealz endpoint we use. Do not scrape HTML.
MYDEALZ_RSS_URL = "https://www.mydealz.de/rss/v2/threads"


class MyDealzSource(AbstractCouponSource):
    """mydealz RSS deal feed adapter."""

    slug = "mydealz"

    def fetch(self) -> list[RawCoupon]:
        # Compliance first (Chapter 4 / Chapter 9).
        self._check_compliance()

        self._require_http()

        # Allow the feed URL to be overridden per source config, defaulting to
        # the documented public RSS endpoint.
        url = self.cfg.get("rss_url") or MYDEALZ_RSS_URL
        timeout = self.cfg.get("timeout") or settings.request_timeout

        try:
            resp = self._http.get(url, timeout=timeout)
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001 - any fetch error is non-fatal
            log.warning("mydealz: RSS fetch failed (%s): %s", url, exc)
            return []

        try:
            root = ET.fromstring(resp.content)
        except ET.ParseError as exc:
            log.warning("mydealz: RSS feed did not parse: %s", exc)
            return []

        items = root.findall(".//item")
        raws: list[RawCoupon] = []
        for item in items:
            title = _text(item.find("title"))
            link = _text(item.find("link"))
            pub_date_raw = _text(item.find("pubDate"))

            if not link:
                # A deal with no link is not actionable; skip rather than guess.
                continue

            seen_at = _parse_pubdate(pub_date_raw)

            raws.append(
                RawCoupon(
                    store_slug=None,  # mydealz deals are multi-store
                    code="",          # deals are not always code-based
                    title=title or None,
                    source_url=link,
                    source_slug="mydealz",
                    discount_type="other",
                    seen_at=seen_at,
                )
            )

        log.info("mydealz: fetched %d deal(s) from RSS", len(raws))
        return raws


# --- small helpers (module-private) ---

def _text(el: Optional[ET.Element]) -> str:
    if el is None or el.text is None:
        return ""
    return el.text.strip()


def _parse_pubdate(raw: str) -> datetime:
    """Parse an RFC-822 ``pubDate`` into a UTC datetime; fall back to now()."""
    if not raw:
        return datetime.utcnow()
    try:
        dt = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return datetime.utcnow()
    if dt is None:
        return datetime.utcnow()
    return dt
