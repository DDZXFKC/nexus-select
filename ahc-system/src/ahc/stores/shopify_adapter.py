"""Shopify storefront adapter.

fetch_product: Shopify's public /products/<handle>.js JSON endpoint (HTTP)
-- returns clean price / variant / availability data without HTML scraping.
add_to_cart / apply_coupon / read_cart: Playwright selectors for common
Shopify themes (Dawn/Debut/Impulse) -- form[action$="/cart/add"], #CartDrawer,
/cart?discount=CODE, and the /cart.js JSON endpoint for read-back.

No network or browser calls at import or construction time.
"""
from __future__ import annotations

from typing import Optional
from urllib.parse import urlparse

from .base import (
    AbstractStoreAdapter, CartState, ComplianceBlockedError,
    CouponApplyResult, ProductFetch, StoreAdapterError,
)
from .http import new_http_session


class ShopifyAdapter(AbstractStoreAdapter):
    platform = "shopify"

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

    def _handle_of(self, ref: str) -> str:
        p = urlparse(ref)
        if p.scheme and p.netloc:
            tail = p.path.rsplit("/products/", 1)
            return tail[-1].strip("/").split("?")[0] if len(tail) > 1 else ref
        return ref.strip("/").split("/")[-1]

    def _product_url(self, ref: str) -> str:
        return f"{self.base_url}/products/{self._handle_of(ref)}"

    # ---- HTTP read-only ----
    def fetch_product(self, product_url_or_sku: str, *, http_session=None) -> ProductFetch:
        self._check_compliance("scrape")
        session = http_session or self._http or new_http_session()
        url = self._product_url(product_url_or_sku)
        resp = session.get(f"{url}.js", headers={"Accept": "application/json"})
        resp.raise_for_status()
        data = resp.json()
        variants = data.get("variants", []) or []
        sizes = [v.get("title") for v in variants if v.get("title") and v.get("available", True)]
        sku = next((v.get("sku") for v in variants if v.get("sku")), None)
        # Shopify .js returns integer prices in the currency's minor unit
        # (cents for EUR/USD; whole yen for JPY stores).
        price_minor = int(data.get("price") or 0)
        stock = ("in_stock" if data.get("available")
                 else "out_of_stock" if variants else "unknown")
        return ProductFetch(
            store_slug=self.slug, url=url, sku=sku, price_minor=price_minor,
            currency=self.currency, stock_status=stock, sizes_available=sizes,
            raw_html_bytes=None)

    # ---- Browser cart flow (Playwright) ----
    def add_to_cart(self, sku: str, size: Optional[str], qty: int = 1) -> CartState:
        self._check_compliance("buy")
        self._require_browser()
        page = self._page
        page.goto(self._product_url(sku), wait_until="domcontentloaded")
        if size:
            radio = page.locator(
                f'fieldset.product-form__input input[type="radio"][value="{size}"], '
                f'.swatch input[type="radio"][value="{size}"]').first
            try:
                radio.check(timeout=4000)
            except Exception:
                try:
                    page.select_option('select[name="id"]', label=size, timeout=4000)
                except Exception as exc:
                    raise StoreAdapterError(f"{self.slug}: could not select size {size!r}: {exc}")
        try:
            page.locator('input[name="quantity"]').first.fill(str(qty), timeout=3000)
        except Exception:
            pass
        page.locator(
            'button[type="submit"][name="add"], button.add-to-cart, '
            'button[data-action="add-to-cart"]').first.click(timeout=10000)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        return self._read_cart_json()

    def apply_coupon(self, code: str) -> CouponApplyResult:
        self._check_compliance("buy")
        self._require_browser()
        page = self._page
        before_total = self._read_cart_json().total_minor
        page.goto(f"{self.base_url}/cart?discount={code}", wait_until="networkidle")
        for sel in ('input[name="discount"]', 'input[name="coupon"]', 'input#discount_code'):
            try:
                page.locator(sel).first.fill(code, timeout=3000)
                page.locator(
                    'button[name="button"][type="submit"], '
                    'button[type="submit"].cart__discount-apply').first.click(timeout=3000)
                page.wait_for_load_state("networkidle", timeout=8000)
                break
            except Exception:
                continue
        after = self._read_cart_json()
        applied = after.discount_minor > 0 or after.total_minor < before_total
        return CouponApplyResult(
            coupon_code=code, applied=applied,
            applied_discount_minor=after.discount_minor if applied else None,
            currency=self.currency,
            error_message=None if applied else "discount did not change cart total",
            raw_response_excerpt=None)

    def read_cart(self) -> CartState:
        self._check_compliance("scrape")
        return self._read_cart_json()

    def _read_cart_json(self) -> CartState:
        self._require_browser()
        page = self._page
        cart = page.evaluate(
            "async()=>{try{const r=await fetch('/cart.js',{credentials:'include'});"
            "return r.ok?await r.json():null;}catch{return null;}}")
        if not cart:
            raise StoreAdapterError(f"{self.slug}: /cart.js returned no cart")
        items: list[dict] = []
        subtotal_minor = 0
        for li in cart.get("items", []) or []:
            unit_minor = int(li.get("price") or 0)
            q = int(li.get("quantity") or 0)
            items.append({"sku": li.get("sku") or str(li.get("variant_id") or ""),
                          "qty": q, "unit_price_minor": unit_minor, "currency": self.currency})
            subtotal_minor += unit_minor * q
        discount_minor = abs(int(cart.get("total_discount") or 0))
        total_minor = int(cart.get("total_price") or 0)
        codes = [d.get("code") for d in cart.get("discounts", []) or [] if d.get("code")]
        return CartState(
            items=items, subtotal_minor=subtotal_minor, discount_minor=discount_minor,
            shipping_minor=0, tax_minor=0, total_minor=total_minor,
            currency=self.currency, applied_coupon_codes=codes)
