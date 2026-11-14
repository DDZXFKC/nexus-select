"""Magento 2 storefront adapter (default Luma theme).

fetch_product: JSON-LD + Luma price box (HTTP). Cart flow drives Playwright
against /checkout/cart and #discount-coupon-form. Magento has no stable
cart-JSON endpoint like Shopify's /cart.js, so totals are parsed from the
rendered HTML. Where a selector genuinely does not match the live theme,
the method raises NotImplementedError rather than fabricating data.

No network or browser calls at import or construction time.
"""
from __future__ import annotations

import json
import re
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ..utils.money import to_minor
from .base import (
    AbstractStoreAdapter, CartState, ComplianceBlockedError,
    CouponApplyResult, ProductFetch, StoreAdapterError,
)
from .http import new_http_session

_AMOUNT_RE = re.compile(r"[-+]?\d[\d.,]*")


def _parse_amount(text, currency: str) -> Optional[int]:
    """Best-effort parse of a localized price string into minor units."""
    if not text:
        return None
    m = _AMOUNT_RE.search(text)
    if not m:
        return None
    s = m.group(0)
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".") if re.search(r",\d{1,2}$", s) else s.replace(",", "")
    try:
        return to_minor(float(s), currency)
    except ValueError:
        return None


class MagentoAdapter(AbstractStoreAdapter):
    platform = "magento"

    def __init__(self, store_config, http_session=None, browser_page=None, *,
                 dry_run: bool = True, compliance=None):
        super().__init__(store_config, http_session=http_session,
                         browser_page=browser_page, dry_run=dry_run)
        self._compliance = compliance

    def _check_compliance(self, action: str) -> None:
        gate = self._compliance
        if gate is None:
            raise ComplianceBlockedError(
                f"{self.slug}: no compliance gate supplied; defaulting to deny ({action})")
        if action == "scrape":
            verdict = gate.allow_scrape(self.slug)
        elif action == "buy":
            verdict = gate.allow_buy(self.slug)
        else:
            raise ComplianceBlockedError(f"{self.slug}: unknown action {action!r}")
        if not verdict.allowed:
            raise ComplianceBlockedError(
                f"{self.slug}: compliance denied {action}: {verdict.reason}")

    def _resolve_product_url(self, ref: str) -> str:
        p = urlparse(ref)
        return ref if (p.scheme and p.netloc) else f"{self.base_url}/{ref.lstrip('/')}"

    # ---- HTTP read-only ----
    def fetch_product(self, product_url_or_sku: str, *, http_session=None) -> ProductFetch:
        self._check_compliance("scrape")
        session = http_session or self._http or new_http_session()
        url = self._resolve_product_url(product_url_or_sku)
        resp = session.get(url, headers={"Accept": "text/html"})
        resp.raise_for_status()
        html = resp.text
        soup = BeautifulSoup(html, "lxml")
        price_minor, currency, stock, sku = self._parse_product(soup)
        sizes = [o.get_text(strip=True) for o in soup.select(
            "select.super-attribute-select option, select[name*='super_attribute'] option")
            if o.get_text(strip=True) and o.get("value")]
        return ProductFetch(
            store_slug=self.slug, url=url, sku=sku, price_minor=price_minor,
            currency=currency or self.currency, stock_status=stock,
            sizes_available=sizes, raw_html_bytes=html.encode("utf-8", "replace"))

    def _parse_product(self, soup: BeautifulSoup):
        price_minor, currency, stock, sku = 0, self.currency, "unknown", None
        for tag in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(tag.string or "")
            except (json.JSONDecodeError, TypeError):
                continue
            if not isinstance(data, dict) or data.get("@type") != "Product":
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
        if price_minor == 0:
            box = soup.select_one(".price-box .price, .product-info-price .price")
            if box:
                m = _parse_amount(box.get_text(), self.currency)
                if m is not None:
                    price_minor = m
        return price_minor, currency, stock, sku

    # ---- Browser cart flow (skeletal; Luma theme) ----
    def add_to_cart(self, sku: str, size: Optional[str], qty: int = 1) -> CartState:
        self._check_compliance("buy")
        self._require_browser()
        page = self._page
        page.goto(self._resolve_product_url(sku), wait_until="domcontentloaded")
        if size:
            try:
                page.select_option("select.super-attribute-select", label=size, timeout=5000)
            except Exception as exc:
                raise StoreAdapterError(f"{self.slug}: could not pick Magento option {size!r}: {exc}")
        try:
            page.locator("input#qty").first.fill(str(qty), timeout=3000)
        except Exception:
            pass
        page.locator("button#product-addtocart-button, button.tocart").first.click(timeout=10000)
        try:
            page.wait_for_selector("#minicart-content-wrapper, .message.success", timeout=10000)
        except Exception:
            pass
        return self._read_cart_state()

    def apply_coupon(self, code: str) -> CouponApplyResult:
        self._check_compliance("buy")
        self._require_browser()
        page = self._page
        before_total = self._read_cart_state().total_minor
        page.goto(f"{self.base_url}/checkout/cart/", wait_until="domcontentloaded")
        try:
            page.locator("input#coupon_code").first.fill(code, timeout=5000)
            page.locator("button.action.apply, button[value='applyCoupon']").first.click(timeout=5000)
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception as exc:
            return CouponApplyResult(
                coupon_code=code, applied=False, applied_discount_minor=None,
                currency=self.currency,
                error_message=f"Magento coupon form not interactable: {exc}")
        after = self._read_cart_state()
        applied = after.discount_minor > 0 or after.total_minor < before_total
        return CouponApplyResult(
            coupon_code=code, applied=applied,
            applied_discount_minor=after.discount_minor if applied else None,
            currency=self.currency,
            error_message=None if applied else "Magento: coupon did not change total")

    def read_cart(self) -> CartState:
        self._check_compliance("scrape")
        return self._read_cart_state()

    def _read_cart_state(self) -> CartState:
        self._require_browser()
        page = self._page
        page.goto(f"{self.base_url}/checkout/cart/", wait_until="domcontentloaded")
        soup = BeautifulSoup(page.content(), "lxml")
        items: list[dict] = []
        for row in soup.select(".cart.item, .item-info"):
            sku_el = row.select_one(".sku")
            qty_el = row.select_one("input.qty")
            price_el = row.select_one(
                ".col.price .price, .subtotal .price, .product-item-price .price")
            if not price_el:
                continue
            unit = _parse_amount(price_el.get_text(), self.currency)
            if unit is None:
                raise NotImplementedError(
                    f"{self.slug}: Magento unit-price selector did not parse on this theme")
            q = int(qty_el.get("value") or 1) if qty_el else 1
            items.append({"sku": (sku_el.get_text(strip=True) if sku_el else ""),
                          "qty": q, "unit_price_minor": unit, "currency": self.currency})
        if not items:
            raise NotImplementedError(
                f"{self.slug}: Magento cart row selector .item-info not matched on this theme")
        grand = soup.select_one(".grand.totals .price, .grand_total .price")
        if not grand:
            raise NotImplementedError(
                f"{self.slug}: Magento grand-total selector not matched on this theme")
        total_minor = _parse_amount(grand.get_text(), self.currency) or 0
        sub_el = soup.select_one(".totals.sub .price, .subtotal .price")
        subtotal_minor = (_parse_amount(sub_el.get_text(), self.currency) if sub_el
                          else sum(i["unit_price_minor"] * i["qty"] for i in items))
        disc_el = soup.select_one(".totals.discount .price")
        discount_minor = abs(_parse_amount(disc_el.get_text(), self.currency) or 0) if disc_el else 0
        tax_el = soup.select_one(".totals.tax .price")
        tax_minor = (_parse_amount(tax_el.get_text(), self.currency) or 0) if tax_el else 0
        codes = [c.get_text(strip=True)
                 for c in soup.select(".cart-discount .coupon-code, .discount .title")]
        return CartState(
            items=items, subtotal_minor=subtotal_minor, discount_minor=discount_minor,
            shipping_minor=0, tax_minor=tax_minor, total_minor=total_minor,
            currency=self.currency, applied_coupon_codes=codes)
