"""Cart builder (Chapter 6 - cart preparation step).

Wraps a store adapter's `add_to_cart` + `read_cart` pair and captures a
Playwright screenshot of the resulting cart page so every cart-preparation
attempt has an auditable image (Chapter 9 safety: never act without evidence).

This module never pays. In dry-run mode `add_to_cart` is still allowed (it
does not move money); we simply never proceed to checkout. The dry-run guard
lives on the adapter and the orchestrator, not here.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ..logging_setup import get_logger
from .base import BuyError
from ..stores.base import AbstractStoreAdapter, CartState

log = get_logger(__name__)


class CartBuilder:
    """Build a cart snapshot for one (product, size, qty) triple."""

    def __init__(self, adapter: AbstractStoreAdapter, *, screenshot_dir: Path):
        self._adapter = adapter
        self._screenshot_dir = Path(screenshot_dir)
        self._screenshot_dir.mkdir(parents=True, exist_ok=True)

    def build(
        self,
        store_product_url: str,
        size: Optional[str],
        qty: int,
        *,
        plan_id: Optional[int] = None,
    ) -> CartState:
        """Add the item to the cart, read the cart back, screenshot it.

        Args:
            store_product_url: product URL or SKU as understood by the adapter.
                The adapter decides whether to treat this as a URL or a SKU;
                the orchestrator passes ``StoreProduct.url``.
            size: requested size, or ``None`` for one-size products.
            qty: quantity to add (>= 1).
            plan_id: optional plan id used to name the screenshot file
                ``<plan_id>_<ts>.png``. When omitted, ``"cart"`` is used.

        Returns:
            The post-add :class:`CartState` with ``screenshot_path`` set when
            a Playwright page is available.

        Raises:
            BuyError: if qty is invalid or the adapter rejects the operation.
        """
        if qty is None or qty < 1:
            raise BuyError(f"CartBuilder.build: qty must be >= 1, got {qty!r}")

        log.info(
            "cart.build store=%s url=%s size=%s qty=%s dry_run=%s",
            self._adapter.slug,
            store_product_url,
            size,
            qty,
            self._adapter._dry_run,
        )

        # add_to_cart is allowed in dry-run: it stages the item without paying.
        # The adapter itself guards the *checkout* step, not the cart step.
        try:
            self._adapter.add_to_cart(store_product_url, size, qty)
        except NotImplementedError as e:
            raise BuyError(
                f"store {self._adapter.slug!r}: add_to_cart not implemented"
            ) from e

        cart = self._adapter.read_cart()
        cart.screenshot_path = self._screenshot(plan_id)
        return cart

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _screenshot(self, plan_id: Optional[int]) -> Optional[str]:
        """Take a Playwright screenshot of the current cart page.

        Returns the absolute path as a string, or ``None`` when the adapter
        has no browser page (HTTP-only adapters cannot screenshot).
        """
        page = getattr(self._adapter, "_page", None)
        if page is None:
            log.warning(
                "cart.screenshot: adapter %s has no Playwright page; "
                "skipping screenshot",
                self._adapter.slug,
            )
            return None

        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        name = f"{plan_id if plan_id is not None else 'cart'}_{ts}.png"
        path = self._screenshot_dir / name
        try:
            page.screenshot(path=str(path), full_page=True)
            log.info("cart.screenshot saved: %s", path)
            return str(path)
        except Exception as e:  # pragma: no cover - depends on live browser
            log.error("cart.screenshot failed for %s: %s", self._adapter.slug, e)
            return None
