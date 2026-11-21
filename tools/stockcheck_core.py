"""AHC StockChecker core: one URL, no periodic crawling, no anti-bot bypass.

This module deliberately DOES NOT wire WP-CLI or production destinations.
Store adapters must supply explicit field selectors in a subsequent integration.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
import re
import time


class _Extractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.entries = []
        self._stack = []
        self.jsonld = []
        self._in_json = False
        self._json_parts = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        self._stack.append((tag, attributes))
        if tag == "script" and attributes.get("type") == "application/ld+json":
            self._in_json = True
            self._json_parts = []

    def handle_endtag(self, tag):
        if tag == "script" and self._in_json:
            self.jsonld.append("".join(self._json_parts))
            self._in_json = False
        if self._stack:
            self._stack.pop()

    def handle_data(self, data):
        if self._in_json:
            self._json_parts.append(data)
        elif data.strip():
            self.entries.append(data.strip())


@dataclass(frozen=True)
class CheckResult:
    stock: str
    reason: str
    current_price: dict | None = None
    other_sizes_in_stock: tuple = ()
    http_status: int | None = None
    fetched_at: str | None = None
    cache_hit: bool = False
    parser: str = "fallback"
    evidence: str = ""

    def as_dict(self):
        return asdict(self)


class StockChecker:
    """Safe bounded HTTP reader with explicit per-store parsing callback.

    Parser takes (html, variant) and returns (stock, price, other_sizes, evidence).
    Parser MUST fail closed on unknown size/color. No stock inference from the
    product page's generic "In stock" phrase for size-specific enquiries.
    """
    def __init__(self, parsers=None, fetch=None, clock=None, sleep=None):
        self.parsers = parsers or {}
        self.fetch = fetch or self._fetch
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.sleep = sleep or time.sleep
        self.cache = {}
        self.blocked_until = {}

    def _fetch(self, url):
        req = Request(url, headers={"User-Agent":"AfterHoursClubStockCheck/1.0 (customer-triggered)"})
        with urlopen(req, timeout=10) as response:
            return response.status, response.read(1_000_001)

    def check(self, url, shop, variant=None, *, use_cache=True, retry=True):
        now = self.clock()
        if not url or urlsplit(url).scheme != "https" or not urlsplit(url).hostname:
            return CheckResult("UNCONFIRMED", "NO_URL", fetched_at=now.isoformat())
        if self.blocked_until.get(shop, now) > now:
            return CheckResult("UNCONFIRMED", "BLOCKED", fetched_at=now.isoformat())
        variant = dict(variant or {})
        # cache includes shop+variant: same URL can have different size stock.
        key = (shop, url, tuple(sorted(variant.items())))
        old = self.cache.get(key)
        if use_cache and old and old[0] > now:
            return CheckResult(**dict(old[1].as_dict(), cache_hit=True))
        attempts = 2 if retry else 1
        for attempt in range(attempts):
            if attempt:
                self.sleep(5)
                now = self.clock()
            status = None
            try:
                status, payload = self.fetch(url)
                if status in (403, 429):
                    self.blocked_until[shop] = now + timedelta(minutes=30)
                    return CheckResult("UNCONFIRMED","BLOCKED",http_status=status,
                                       fetched_at=now.isoformat())
                if status in (404, 410):
                    r = CheckResult("OUT_OF_STOCK","NOT_FOUND_404" if status == 404 else "GONE_410",
                                    http_status=status,fetched_at=now.isoformat())
                    self.cache[key] = (now + timedelta(minutes=30),r)
                    return r
                if status >= 500:
                    reason = "UNREACHABLE"
                    continue
                if status != 200 or len(payload) > 1_000_000:
                    return CheckResult("UNCONFIRMED","UNREADABLE",http_status=status,
                                       fetched_at=now.isoformat())
                html = payload.decode("utf-8",errors="replace")
                parser = self.parsers.get(shop)
                if parser is None:
                    return CheckResult("UNCONFIRMED","UNREADABLE",http_status=status,
                                       fetched_at=now.isoformat())
                try:
                    stock, price, other_sizes, evidence = parser(html, variant)
                    if stock not in ("IN_STOCK","OUT_OF_STOCK","UNCONFIRMED"):
                        raise ValueError("invalid stock")
                    if price is not None and (
                        not isinstance(price,dict) or
                        not isinstance(price.get("amount"),(int,float,str)) or
                        price.get("currency") not in ("USD","EUR","GBP","JPY")):
                        raise ValueError("invalid price")
                    if stock == "IN_STOCK" and price is None:
                        stock, reason = "UNCONFIRMED","PRICE_UNKNOWN"
                    else:
                        reason = "OK" if stock != "UNCONFIRMED" else "UNREADABLE"
                    r = CheckResult(stock,reason,price,tuple(other_sizes or ()),status,
                                    now.isoformat(),False,"config:"+shop,str(evidence)[:500])
                    if stock in ("IN_STOCK","OUT_OF_STOCK"):
                        self.cache[key] = (now + timedelta(minutes=30),r)
                    return r
                except (ValueError,TypeError,KeyError,IndexError):
                    return CheckResult("UNCONFIRMED","UNREADABLE",http_status=status,
                                       fetched_at=now.isoformat())
            except HTTPError as err:
                if err.code in (403,429):
                    self.blocked_until[shop] = now + timedelta(minutes=30)
                    return CheckResult("UNCONFIRMED","BLOCKED",http_status=err.code,
                                       fetched_at=now.isoformat())
                if err.code in (404,410):
                    r = CheckResult("OUT_OF_STOCK","NOT_FOUND_404" if err.code == 404 else "GONE_410",
                                    http_status=err.code,fetched_at=now.isoformat())
                    self.cache[key] = (now + timedelta(minutes=30),r)
                    return r
                if err.code < 500:
                    return CheckResult("UNCONFIRMED","UNREADABLE",http_status=err.code,
                                       fetched_at=now.isoformat())
                reason = "UNREACHABLE"
            except (URLError,TimeoutError,OSError):
                reason = "UNREACHABLE"
        return CheckResult("UNCONFIRMED",reason,http_status=status,fetched_at=self.clock().isoformat())


def fixture_variant_parser(html, variant):
    """For mock tests ONLY. Never enable for a real merchant."""
    import json
    import html as html_module
    m = re.search(r'<script type="application/json" id="ahc-test-fixture">(.*?)</script>',
                  html,re.S)
    if not m:
        raise ValueError("fixture data missing")
    data = json.loads(html_module.unescape(m.group(1)))
    item = data.get("variants",{}).get(variant.get("size"))
    if item is None:
        return "UNCONFIRMED",None,(), "size not found"
    status = "IN_STOCK" if item["available"] else "OUT_OF_STOCK"
    return status,item.get("price"),(),("fixture size "+str(variant.get("size")))
