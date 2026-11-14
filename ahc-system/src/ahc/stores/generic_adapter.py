"""Generic store adapter for platforms without a dedicated adapter.

Implements only the read-only :meth:`fetch_product` using JSON-LD
(``<script type="application/ld+json">`` with ``@type`` ``Product``) plus
the Open Graph product meta tags (``og:price``, ``product:price:amount``,
``product:availability``) as a fallback. This works on most modern
e-commerce pages regardless of platform.

Cart / coupon operations are intentionally NOT implemented here: a generic
store has no known cart selectors, so the base-class defaults raise
``NotImplementedError``. Stores that need the cart flow must configure a
specific platform adapter (shopify / magento / woocommerce) instead.

No network or browser calls at import or construction time.
"""
from __future__ import annotations

import json
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .base import (
    AbstractStoreAdapter,
    ComplianceBlockedError,
    ProductFetch,
)
from .http import new_http_session


class GenericAdapter(AbstractStoreAdapter):
    platform = "generic"

    def __init__(self, store_config, http_session=None, browser_page=None, *,
                 dry_run: bool = True, compliance=None):
        super().__init__(
            store_config,
            http_session=http_session,
            browser_page=browser_page,
            dry_run=dry_run,
        )
        self._compliance = compliance

    def _check_compliance(self, action: str) -> None:
        gate = self._compliance
        if gate is None:
            raise ComplianceBlockedError(
                f"{self.slug}: no compliance gate supplied; defaulting to deny "
                f"({action})"
            )
        if action == "scrape":
            verdict = gate.allow_scrape(self.slug)
        elif action == "buy":
            verdict = gate.allow_buy(self.slug)
        else:
            raise ComplianceBlockedError(f"{self.slug}: unknown action {action!r}")
        if not verdict.allowed:
            raise ComplianceBlockedError(
                f"{self.slug}: compliance denied {action}: {verdict.reason}"
            )

    def _resolve_product_url(self, ref: str) -> str:
        p = urlparse(ref)
        return ref if (p.scheme and p.netloc) else f"{self.base_url}/{ref.lstrip('/')}"

    def fetch_product(self, product_url_or_sku: str, *, http_session=None) -> ProductFetch:
        self._check_compliance("scrape")
        session = http_session or self._http or new_http_session()
        url = self._resolve_product_url(product_url_or_sku)
        resp = session.get(url, headers={"Accept": "text/html,application/xhtml+xml"})
        resp.raise_for_status()
        html = resp.text
        soup = BeautifulSoup(html, "lxml")
        price_minor, currency, stock, sku, sizes = self._parse_product(soup)
        return ProductFetch(
            store_slug=self.slug,
            url=url,
            sku=sku,
            price_minor=price_minor,
            currency=currency or self.currency,
            stock_status=stock,
            sizes_available=sizes,
            raw_html_bytes=html.encode("utf-8", errors="replace"),
        )

    def _parse_product(self, soup: BeautifulSoup):
        price_minor = 0
        currency = self.currency
        stock = "unknown"
        sku: Optional[str] = None
        # 1. JSON-LD is the most portable structured source.
        for tag in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(tag.string or "")
            except (json.JSONDecodeError, TypeError):
                continue
            if not isinstance(data, dict) or data.get("@type") not in (
                "Product", "IndividualProduct",
            ):
                continue
            sku = data.get("sku") or sku
            offers = data.get("offers")
            if isinstance(offers, dict):
                offers = [offers]
            for off in offers or []:
                if not isinstance(off, dict):
                    continue
                currency = off.get("priceCurrency") or currency
                p = off.get("price")
                if p is not None:
                    try:
                        price_minor = self._to_minor(float(p))
                    except (TypeError, ValueError):
                        pass
                avail = (off.get("availability") or "").lower()
                if "instock" in avail:
                    stock = "in_stock"
                elif "outofstock" in avail:
                    stock = "out_of_stock"
        # 2. Open Graph product meta tags fallback.
        if price_minor == 0:
            og_price = soup.select_one('meta[property="product:price:amount"]')
            og_currency = soup.select_one('meta[property="product:price:currency"]')
            if og_price:
                try:
                    price_minor = self._to_minor(float(og_price.get("content")))
                except (TypeError, ValueError):
                    pass
            if og_currency and og_currency.get("content"):
                currency = og_currency["content"] or currency
        og_avail = soup.select_one('meta[property="product:availability"], meta[name="product:availability"]')
        if og_avail:
            a = (og_avail.get("content") or "").lower()
            if "instock" in a:
                stock = "in_stock"
            elif "outofstock" in a:
                stock = "out_of_stock"
        # 3. Sizes: common variant selectors across platforms.
        sizes: list[str] = []
        for opt in soup.select(
            "select[name='id'] option, select[name='variant_id'] option, "
            "select[name*='attribute'] option"
        ):
            label = opt.get_text(strip=True)
            low = label.lower()
            if label and "choose" not in low and "select" not in low and low != "default":
                sizes.append(label)
        if not sizes:
            for el in soup.select(
                ".swatch input[type='radio'], .variant-options input[type='radio']"
            ):
                lbl = el.get("value") or el.get("aria-label")
                if lbl:
                    sizes.append(lbl)
        return price_minor, currency, stock, sku, sizes
