"""Abstract store adapter contract.

Two execution backends are supported:
  - HTTP mode (requests + BeautifulSoup): read-only product info, no login.
    Used for price/stock comparison across many stores.
  - Browser mode (Playwright): cart + coupon apply, which usually requires
    JS-rendered pages and sometimes a session cookie.

Concrete adapters choose which methods to implement. Default implementations
raise NotImplementedError so a partial adapter fails loudly instead of
silently no-op'ing (Chapter 9 safety).
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ..utils.money import to_minor


class StoreAdapterError(Exception):
    """Base for all adapter errors."""


class ComplianceBlockedError(StoreAdapterError):
    """The compliance gate denied this action for this store."""


@dataclass
class ProductFetch:
    """Result of fetching one product page in HTTP mode."""
    store_slug: str
    url: str
    sku: Optional[str]
    price_minor: int
    currency: str
    stock_status: str  # "in_stock" | "out_of_stock" | "low_stock" | "unknown"
    sizes_available: list[str] = field(default_factory=list)
    fetched_at: datetime = field(default_factory=datetime.utcnow)
    raw_html_bytes: Optional[bytes] = None  # for debugging, never persisted by default


@dataclass
class CartState:
    """Snapshot of the cart after one or more operations."""
    items: list[dict]  # [{sku, qty, unit_price_minor, currency}]
    subtotal_minor: int
    discount_minor: int
    shipping_minor: int
    tax_minor: int
    total_minor: int
    currency: str
    applied_coupon_codes: list[str] = field(default_factory=list)
    screenshot_path: Optional[str] = None


@dataclass
class CouponApplyResult:
    """Outcome of a single coupon application attempt."""
    coupon_code: str
    applied: bool
    applied_discount_minor: Optional[int]
    currency: str
    error_message: Optional[str] = None
    raw_response_excerpt: Optional[str] = None


class AbstractStoreAdapter(abc.ABC):
    """Every store adapter implements this interface.

    The constructor receives a `store_config` dict (one row of config/stores.yaml
    expanded with DB metadata) plus shared HTTP/browser sessions.
    """

    #: EC platform key, e.g. "shopify", "magento", "woocommerce", "generic".
    platform: str = "generic"

    def __init__(
        self,
        store_config: dict,
        http_session=None,
        browser_page=None,
        *,
        dry_run: bool = True,
    ):
        self.cfg = store_config
        self.slug = store_config["slug"]
        self.base_url = store_config["base_url"].rstrip("/")
        self.currency = store_config.get("currency", "EUR")
        self._http = http_session
        self._page = browser_page
        self._dry_run = dry_run

    # ------------------------------------------------------------------
    # HTTP-mode (read-only) methods. Used by the price/stock comparison step.
    # ------------------------------------------------------------------
    @abc.abstractmethod
    def fetch_product(self, product_url_or_sku: str) -> ProductFetch:
        """Fetch one product page and return parsed price/stock/sizes.

        Must respect the compliance gate (caller is expected to check, but
        adapters should also refuse if `self._compliance_verdict` is set to
        denied - set by the registry at construction time).
        """

    def search(self, query: str, *, limit: int = 20) -> list[ProductFetch]:
        """Optional: search the store's catalog by free text."""
        raise NotImplementedError(f"{self.slug}: search not implemented")

    # ------------------------------------------------------------------
    # Browser-mode (Playwright) methods. Used by the cart / coupon flow.
    # ------------------------------------------------------------------
    def add_to_cart(self, sku: str, size: str | None, qty: int = 1) -> CartState:
        raise NotImplementedError(f"{self.slug}: add_to_cart not implemented")

    def apply_coupon(self, code: str) -> CouponApplyResult:
        raise NotImplementedError(f"{self.slug}: apply_coupon not implemented")

    def remove_coupon(self, code: str) -> CartState:
        raise NotImplementedError(f"{self.slug}: remove_coupon not implemented")

    def read_cart(self) -> CartState:
        raise NotImplementedError(f"{self.slug}: read_cart not implemented")

    def estimate_shipping(self, ship_country: str, *, zip_code: str | None = None) -> tuple[int, str]:
        """Return (shipping_minor, currency) for a destination.

        Default: not implemented. Override per adapter when the cart page
        exposes a shipping estimator.
        """
        raise NotImplementedError(f"{self.slug}: estimate_shipping not implemented")

    def estimate_tax(self, ship_country: str) -> tuple[int, str]:
        """Return (tax_minor, currency) at the current cart subtotal."""
        raise NotImplementedError(f"{self.slug}: estimate_tax not implemented")

    # ------------------------------------------------------------------
    # Helpers shared by concrete adapters
    # ------------------------------------------------------------------
    def _require_browser(self) -> None:
        if self._page is None:
            raise StoreAdapterError(
                f"{self.slug}: this operation requires a Playwright page"
            )

    def _require_http(self) -> None:
        if self._http is None:
            raise StoreAdapterError(
                f"{self.slug}: this operation requires an HTTP session"
            )

    def _dry_run_guard(self, action: str) -> None:
        if self._dry_run:
            raise StoreAdapterError(
                f"{self.slug}: {action} blocked by dry_run=True (Chapter 9 safety)"
            )

    def _to_minor(self, amount_major: float) -> int:
        return to_minor(amount_major, self.currency)
