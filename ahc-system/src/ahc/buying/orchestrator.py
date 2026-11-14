"""Concrete buy orchestrator (Chapter 6 + Chapter 9 safety).

Stops at "cart prepared" by default. Real payment requires
``settings.dry_run_only=False`` AND a valid per-run approval token AND an
explicit per-store checkout implementation (not provided here - see Chapter 9
/ 14). ``submit_payment`` deliberately refuses with :class:`BuyError` once the
dry-run and token guards pass, so a missing per-store implementation can never
silently charge a card.

Safety invariants enforced in :meth:`prepare_cart`:
  - Compliance gate must allow buy for the store.
  - Double-buy prevention: an existing PurchaseRecord in SUBMITTED / CONFIRMED
    / UNKNOWN blocks a new attempt (Chapter 9 - never auto-rebuy).
  - Cart total must not exceed ``settings.max_cart_amount``.
  - A PurchaseRecord is created/reused with ``requires_approval=True`` and only
    advanced to CART_PREPARED; payment needs a separate, token-gated call.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional, Tuple

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..compliance.policy import ComplianceGate
from ..config import settings
from ..db.models import (
    Coupon,
    CostComponent,
    CostType,
    OrderItem,
    PurchasePlan,
    PurchaseRecord,
    PurchaseStatus,
    Store,
    StoreProduct,
)
from ..db.session import SessionLocal, session_scope
from ..logging_setup import get_logger
from ..stores.base import StoreAdapterError
from ..stores.registry import get_adapter
from ..utils.money import to_minor
from .base import BuyError, BuyOrchestrator, BuyResult, BuyStatus
from .cart import CartBuilder
from .coupon_applier import CouponApplier

log = get_logger(__name__)


# Chapter 9: a plan with a record in any of these states is considered "already
# bought / in flight / unknown" and must NOT be re-attempted automatically.
_DOUBLE_BUY_STATUSES = frozenset(
    {
        PurchaseStatus.SUBMITTED.value,
        PurchaseStatus.CONFIRMED.value,
        PurchaseStatus.UNKNOWN.value,
    }
)


@contextmanager
def _get_browser_page() -> Iterator[Tuple[object, object]]:
    """Lazily start Playwright and yield ``(browser, page)``.

    Playwright is imported lazily so importing :mod:`ahc.buying` never requires
    the Playwright runtime. If Playwright is not installed or the browser
    binary cannot be launched, :class:`BuyError` is raised with install
    instructions. Exceptions raised inside the caller's ``with`` body propagate
    untouched (only setup errors are converted to :class:`BuyError`).
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:  # pragma: no cover - env dependent
        raise BuyError(
            "Playwright is not installed. Install it with:\n"
            "  pip install playwright\n"
            "  playwright install chromium"
        ) from e

    pw = sync_playwright().start()
    try:
        browser = pw.chromium.launch(headless=settings.playwright_headless)
    except Exception as e:  # pragma: no cover - env dependent
        try:
            pw.stop()
        except Exception:
            pass
        raise BuyError(
            f"failed to launch Playwright browser: {e}. "
            "If the browser binary is missing, run: playwright install chromium"
        ) from e
    try:
        page = browser.new_page()
    except Exception as e:  # pragma: no cover - env dependent
        try:
            browser.close()
        except Exception:
            pass
        try:
            pw.stop()
        except Exception:
            pass
        raise BuyError(f"failed to create Playwright page: {e}") from e

    try:
        yield browser, page
    finally:
        for _close in (
            lambda: page.close(),
            lambda: browser.close(),
            lambda: pw.stop(),
        ):
            try:
                _close()
            except Exception:  # pragma: no cover - best-effort cleanup
                pass


class BuyOrchestratorImpl(BuyOrchestrator):
    """Concrete orchestrator. Subclasses the interface in ``base.py``."""

    def __init__(
        self,
        *,
        compliance: ComplianceGate,
        session: Optional[Session] = None,
        screenshot_dir: Optional[Path] = None,
    ):
        self._compliance = compliance
        self._session = session
        if screenshot_dir is not None:
            self._screenshot_dir = Path(screenshot_dir)
        else:
            self._screenshot_dir = settings.data_dir / "screenshots"
        self._screenshot_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # prepare_cart
    # ------------------------------------------------------------------
    def prepare_cart(self, plan_id: int) -> BuyResult:
        if self._session is not None:
            return self._prepare_cart(self._session, plan_id)
        with session_scope() as s:
            return self._prepare_cart(s, plan_id)

    def _prepare_cart(self, session: Session, plan_id: int) -> BuyResult:
        # 1. Load plan + store + store_product + order_item + coupon.
        plan = session.get(PurchasePlan, plan_id)
        if plan is None:
            log.error("prepare_cart: plan %s not found", plan_id)
            return BuyResult(
                plan_id=plan_id,
                store_slug="",
                status=BuyStatus.FAILED,
                error_message=f"plan {plan_id} not found",
                requires_approval=False,
            )
        store = session.get(Store, plan.store_id)
        if store is None:
            return BuyResult(
                plan_id=plan_id,
                store_slug="",
                status=BuyStatus.FAILED,
                error_message=f"plan {plan_id}: store {plan.store_id} not found",
                requires_approval=False,
            )
        store_product = (
            session.get(StoreProduct, plan.store_product_id)
            if plan.store_product_id
            else None
        )
        if store_product is None:
            return BuyResult(
                plan_id=plan_id,
                store_slug=store.slug,
                status=BuyStatus.FAILED,
                error_message=f"plan {plan_id}: no store_product attached",
                requires_approval=False,
            )
        order_item = session.get(OrderItem, plan.order_item_id)
        size = order_item.requested_size if order_item is not None else None
        qty = order_item.quantity if order_item is not None else 1
        coupon = (
            session.get(Coupon, plan.coupon_id) if plan.coupon_id else None
        )

        # 2. Compliance check.
        verdict = self._compliance.allow_buy(store.slug)
        if not verdict.allowed:
            log.warning(
                "prepare_cart: compliance blocked plan=%s store=%s: %s",
                plan_id,
                store.slug,
                verdict.reason,
            )
            return BuyResult(
                plan_id=plan_id,
                store_slug=store.slug,
                status=BuyStatus.BLOCKED_COMPLIANCE,
                error_message=verdict.reason,
                requires_approval=verdict.requires_human,
                notes=[f"compliance source: {verdict.source}"],
            )

        # 3. Double-buy check + (4) create/reuse PurchaseRecord.
        existing = session.execute(
            select(PurchaseRecord).where(PurchaseRecord.plan_id == plan_id)
        ).scalar_one_or_none()
        if existing is not None and existing.status in _DOUBLE_BUY_STATUSES:
            log.warning(
                "prepare_cart: double-buy blocked plan=%s existing_status=%s",
                plan_id,
                existing.status,
            )
            return BuyResult(
                plan_id=plan_id,
                store_slug=store.slug,
                status=BuyStatus.BLOCKED_DOUBLE_BUY,
                error_message=(
                    f"existing purchase record in status {existing.status!r}; "
                    "manual intervention required (Chapter 9)"
                ),
                requires_approval=True,
            )
        if existing is not None:
            record = existing
            record.status = PurchaseStatus.PLANNED.value
            record.requires_approval = True
            record.error_message = None
            record.cart_total_minor = None
            record.cart_currency = None
            record.final_price_minor = None
            record.screenshot_path = None
            record.store_order_id = None
            record.tracking_number = None
            record.tracking_url = None
        else:
            record = PurchaseRecord(
                plan_id=plan_id,
                status=PurchaseStatus.PLANNED.value,
                requires_approval=True,
            )
            session.add(record)
        session.flush()

        # 5. Build adapter with a Playwright page, then build + coupon + cost.
        store_config = {
            "slug": store.slug,
            "name": store.name,
            "base_url": store.base_url,
            "currency": store.currency,
            "ec_platform": store.ec_platform,
            "adapter_class": store.adapter_class,
            "enabled_scrape": store.enabled_scrape,
            "enabled_buy": store.enabled_buy,
            "country": store.country,
        }

        notes: list[str] = [f"dry_run={settings.dry_run_only}"]
        attempts_count = 0
        applied_count = 0

        with _get_browser_page() as (_browser, page):
            adapter = get_adapter(
                store_config,
                browser_page=page,
                dry_run=settings.dry_run_only,
            )
            builder = CartBuilder(
                adapter, screenshot_dir=self._screenshot_dir
            )
            try:
                # 6. Build cart.
                cart = builder.build(
                    store_product.url, size, qty, plan_id=plan_id
                )

                # 6b. Max-amount guard (Chapter 9).
                max_minor = to_minor(
                    settings.max_cart_amount, cart.currency
                )
                if cart.total_minor > max_minor:
                    record.status = PurchaseStatus.FAILED.value
                    record.error_message = (
                        f"cart total {cart.total_minor} {cart.currency} "
                        f"exceeds max_cart_amount {max_minor} minor"
                    )
                    record.cart_total_minor = cart.total_minor
                    record.cart_currency = cart.currency
                    record.screenshot_path = cart.screenshot_path
                    log.warning(
                        "prepare_cart: max amount blocked plan=%s total=%s",
                        plan_id,
                        cart.total_minor,
                    )
                    return BuyResult(
                        plan_id=plan_id,
                        store_slug=store.slug,
                        status=BuyStatus.BLOCKED_MAX_AMOUNT,
                        cart=cart,
                        final_price_minor=cart.total_minor,
                        currency=cart.currency,
                        screenshot_path=cart.screenshot_path,
                        error_message=record.error_message,
                        requires_approval=True,
                        notes=notes,
                    )

                # 7. Apply coupon if the plan has one.
                if coupon is not None and coupon.code:
                    applier = CouponApplier(adapter)
                    cart, attempts = applier.try_coupons(
                        [coupon.code],
                        cart,
                        session=session,
                        store_id=store.id,
                        plan_id=plan_id,
                    )
                    attempts_count = len(attempts)
                    applied_count = sum(
                        1 for a in attempts if a.applied
                    )
                    notes.append(
                        f"coupons tried={attempts_count} "
                        f"applied={applied_count}"
                    )

                # 8. Re-read cart and persist cost components.
                cart = adapter.read_cart()
                # read_cart returns a fresh CartState without a screenshot;
                # capture a fresh one reflecting the post-coupon cart.
                cart.screenshot_path = builder._screenshot(plan_id)
                self._persist_cost_components(session, plan_id, cart)
            except BuyError:
                raise
            except StoreAdapterError as e:
                log.error(
                    "prepare_cart: adapter error plan=%s: %s", plan_id, e
                )
                record.status = PurchaseStatus.FAILED.value
                record.error_message = f"adapter error: {e}"
                return BuyResult(
                    plan_id=plan_id,
                    store_slug=store.slug,
                    status=BuyStatus.FAILED,
                    error_message=record.error_message,
                    requires_approval=True,
                    notes=notes,
                )
            except Exception as e:  # pragma: no cover - defensive
                log.exception(
                    "prepare_cart: unexpected error plan=%s", plan_id
                )
                record.status = PurchaseStatus.FAILED.value
                record.error_message = f"cart operation failed: {e}"
                return BuyResult(
                    plan_id=plan_id,
                    store_slug=store.slug,
                    status=BuyStatus.FAILED,
                    error_message=record.error_message,
                    requires_approval=True,
                    notes=notes,
                )

        # 9. Advance the record to CART_PREPARED.
        record.status = PurchaseStatus.CART_PREPARED.value
        record.cart_total_minor = cart.total_minor
        record.cart_currency = cart.currency
        record.screenshot_path = cart.screenshot_path
        # requires_approval stays True: cart preparation is NOT payment.

        # 10. Return.
        return BuyResult(
            plan_id=plan_id,
            store_slug=store.slug,
            status=BuyStatus.CART_PREPARED,
            cart=cart,
            final_price_minor=cart.total_minor,
            currency=cart.currency,
            screenshot_path=cart.screenshot_path,
            requires_approval=True,
            notes=notes,
        )

    # ------------------------------------------------------------------
    # submit_payment
    # ------------------------------------------------------------------
    def submit_payment(
        self, plan_id: int, *, approval_token: str
    ) -> BuyResult:
        store_slug = self._lookup_store_slug(plan_id)

        # Chapter 9: real purchases disabled unless explicitly turned off.
        if settings.dry_run_only:
            return BuyResult(
                plan_id=plan_id,
                store_slug=store_slug,
                status=BuyStatus.BLOCKED_DRY_RUN,
                error_message=(
                    "settings.dry_run_only=True: real payment disabled "
                    "(Chapter 9 safety)"
                ),
                requires_approval=True,
            )

        # Per-run approval token (separate from the global dry-run switch).
        expected = os.environ.get("AHC_APPROVAL_TOKEN", "deny")
        if approval_token != expected:
            log.warning(
                "submit_payment: invalid approval token plan=%s", plan_id
            )
            return BuyResult(
                plan_id=plan_id,
                store_slug=store_slug,
                status=BuyStatus.FAILED,
                error_message="invalid approval token",
                requires_approval=True,
            )

        # Not implemented: per-store checkout requires its own compliance
        # sign-off + a store-specific payment adapter (Chapter 9 / 14).
        raise BuyError(
            "submit_payment requires explicit per-store implementation "
            "+ compliance sign-off"
        )

    # ------------------------------------------------------------------
    # Cost component persistence
    # ------------------------------------------------------------------
    @staticmethod
    def _persist_cost_components(
        session: Session, plan_id: int, cart
    ) -> None:
        """Delete old CostComponent rows for the plan and insert fresh ones
        observed from the cart (item price, discount, shipping, tax)."""
        session.execute(
            delete(CostComponent).where(
                CostComponent.plan_id == plan_id
            )
        )

        rows = [
            _make_cost_component(
                plan_id,
                CostType.ITEM_PRICE,
                cart.subtotal_minor,
                cart.currency,
                note="cart subtotal (pre-discount)",
            ),
        ]
        # Record a discount line only when a coupon actually reduced the cart.
        if cart.discount_minor and cart.discount_minor > 0:
            rows.append(
                _make_cost_component(
                    plan_id,
                    CostType.COUPON_DISCOUNT,
                    -cart.discount_minor,  # negative = saving
                    cart.currency,
                    note="applied coupon discount",
                )
            )
        # Shipping + tax are always observed values (free shipping = 0 is
        # meaningful, not unknown), so persist them even when zero.
        rows.append(
            _make_cost_component(
                plan_id,
                CostType.LOCAL_SHIPPING,
                cart.shipping_minor,
                cart.currency,
                note="cart shipping",
            )
        )
        rows.append(
            _make_cost_component(
                plan_id,
                CostType.LOCAL_TAX,
                cart.tax_minor,
                cart.currency,
                note="cart tax",
            )
        )
        for r in rows:
            session.add(r)
        session.flush()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _lookup_store_slug(self, plan_id: int) -> str:
        """Best-effort store-slug lookup for early-return BuyResults."""

        def _do(s: Session) -> str:
            plan = s.get(PurchasePlan, plan_id)
            if plan is None:
                return ""
            store = s.get(Store, plan.store_id)
            return store.slug if store is not None else ""

        if self._session is not None:
            try:
                return _do(self._session)
            except Exception:
                return ""
        try:
            with session_scope() as s:
                return _do(s)
        except Exception:
            return ""


def _to_jpy(amount_minor: int, currency: str) -> Tuple[Optional[float], int, bool]:
    """Convert a source-currency minor amount to JPY minor.

    Returns ``(fx_rate, amount_jpy_minor, is_estimate)``. JPY is identity. For
    other currencies there is no FX service wired into the buying flow yet, so
    per Chapter 7 we do NOT invent a rate: the line is marked as an estimate
    with a zero JPY amount and must be recomputed by the cost calculator once
    an FX rate is available.
    """
    if currency and currency.upper() == "JPY":
        return 1.0, amount_minor, False
    return None, 0, True


def _make_cost_component(
    plan_id: int,
    cost_type: CostType,
    amount_minor: int,
    currency: str,
    *,
    note: str = "",
) -> CostComponent:
    fx_rate, jpy_minor, is_estimate = _to_jpy(amount_minor, currency)
    return CostComponent(
        plan_id=plan_id,
        cost_type=cost_type.value,
        amount_minor=amount_minor,
        currency=currency,
        fx_rate=fx_rate,
        amount_jpy_minor=jpy_minor,
        is_estimate=is_estimate,
        note=note if not is_estimate else (note + " | FX pending"),
    )


def build_orchestrator() -> "BuyOrchestratorImpl":
    """Wire a default orchestrator from settings.

    Compliance from the configured compliance.yaml, a SessionLocal-based
    session (opened per call), and screenshots under ``data/screenshots``.
    """
    compliance = ComplianceGate.from_config_file()
    screenshot_dir = settings.data_dir / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    return BuyOrchestratorImpl(
        compliance=compliance,
        session=None,
        screenshot_dir=screenshot_dir,
    )
