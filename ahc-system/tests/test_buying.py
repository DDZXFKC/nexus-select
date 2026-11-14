"""Chapter 11 tests: buy orchestrator safety invariants.

These tests do NOT launch Playwright and do NOT make real HTTP calls. We
monkey-patch `_get_browser_page` and `get_adapter` so the orchestrator
operates against an in-process fake adapter whose cart state is scripted.
"""
from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pytest

from ahc.buying.base import BuyStatus
from ahc.buying.orchestrator import BuyOrchestratorImpl, _DOUBLE_BUY_STATUSES
from ahc.compliance import ComplianceGate
from ahc.db.models import (
    Coupon,
    CouponSource,
    CouponStatus,
    Order,
    OrderItem,
    Product,
    PurchasePlan,
    PurchaseRecord,
    PurchaseStatus,
    Store,
    StoreProduct,
)
from ahc.stores.base import CartState, CouponApplyResult
from ahc.utils.money import to_minor


# ---------------------------------------------------------------------------
# Test scaffolding
# ---------------------------------------------------------------------------

class _FakeAdapter:
    """Adapter whose behaviour we script per-test via `script`."""

    platform = "shopify"

    def __init__(self, store_config, *, script=None, dry_run=True, **_):
        self.cfg = store_config
        self.slug = store_config["slug"]
        self.currency = store_config.get("currency", "EUR")
        self._dry_run = dry_run
        self._script = script or {}

    def add_to_cart(self, sku, size=None, qty=1):
        return self._script.get("add_to_cart_result")

    def read_cart(self):
        return self._script.get("read_cart_result")

    def apply_coupon(self, code):
        return self._script.get("apply_coupon_result", CouponApplyResult(
            coupon_code=code, applied=False, applied_discount_minor=None,
            currency=self.currency, error_message="not scripted",
        ))


def _build_plan(session, *, store_slug="bstn", currency="EUR", with_coupon=False):
    """Insert a minimal plan graph and return its id."""
    store = Store(
        slug=store_slug, name="BSTN", country="DE", currency=currency,
        base_url="https://www.bstn.com", ec_platform="shopify",
        enabled_buy=True,
    )
    session.add(store)
    session.flush()

    src = CouponSource(
        slug="retailmenot", name="RetailMeNot", url="https://www.retailmenot.com",
        country="US", source_type="aggregator", enabled=True,
    )
    session.add(src)
    session.flush()

    coupon = None
    if with_coupon:
        coupon = Coupon(
            store_id=store.id, source_id=src.id, code="SUMMER10",
            discount_type="percent", discount_value=10.0,
            discount_currency=currency, valid_until=date(2026, 12, 31),
            source_url="https://example.com/r/1",
            last_seen_at=date(2026, 11, 14),
            status=CouponStatus.UNVERIFIED.value,
        )
        session.add(coupon)
        session.flush()

    # Product must exist before StoreProduct (FK constraint).
    product = Product(
        external_source="existing", external_id="EXT-1",
        brand="Nike", model="Air Max 90", colorway="White/Black",
        sku="AM90-WB", gtin=None,
    )
    session.add(product)
    session.flush()

    sp = StoreProduct(
        store_id=store.id, product_id=product.id, store_sku="SKU-1",
        url="https://www.bstn.com/p/sku-1", price_minor=15000,
        currency=currency, stock_status="in_stock",
    )
    session.add(sp)
    session.flush()

    order = Order(
        source="buyma", external_order_id="BM-TEST",
        received_at=date(2026, 11, 14), status="received",
    )
    session.add(order)
    session.flush()

    item = OrderItem(
        order_id=order.id, requested_brand="Nike", requested_model="Air Max 90",
        requested_size="42", quantity=1,
    )
    session.add(item)
    session.flush()

    plan = PurchasePlan(
        order_item_id=item.id, store_id=store.id, store_product_id=sp.id,
        coupon_id=coupon.id if coupon else None,
        selected=True, meets_min_profit=True,
    )
    session.add(plan)
    session.flush()
    return plan.id, store.id


def _build_gate_allowing_buy():
    gate = ComplianceGate.from_config_file()
    gate._defaults["allow_buy_automation"] = True
    gate._stores["bstn"] = {"scrape": "allowed", "buy": "allowed"}
    return gate


def _patch_browser_and_adapter(script):
    """Patch the orchestrator's Playwright + adapter factory."""
    browser_cm_called = {"value": False}

    from contextlib import contextmanager

    @contextmanager
    def fake_browser():
        browser_cm_called["value"] = True
        yield (object(), object())  # (browser, page) - never used by fake adapter

    def fake_get_adapter(store_config, *, browser_page=None, dry_run=None, **_):
        return _FakeAdapter(store_config, script=script)

    return (
        patch("ahc.buying.orchestrator._get_browser_page", fake_browser),
        patch("ahc.buying.orchestrator.get_adapter", fake_get_adapter),
        browser_cm_called,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_prepare_cart_blocked_when_compliance_denies_buy(session):
    """Default compliance.yaml denies buy automation globally."""
    plan_id, _ = _build_plan(session)
    gate = ComplianceGate.from_config_file()  # buy not allowed by default
    orch = BuyOrchestratorImpl(compliance=gate, session=session,
                               screenshot_dir="/tmp/ahc-test-shots")
    r = orch.prepare_cart(plan_id)
    assert r.status == BuyStatus.BLOCKED_COMPLIANCE


def test_prepare_cart_succeeds_when_compliance_allows(session, monkeypatch):
    """Happy path: cart prepared, status CART_PREPARED, requires_approval=True."""
    plan_id, store_id = _build_plan(session)
    gate = _build_gate_allowing_buy()

    cart_state = CartState(
        items=[{"sku": "SKU-1", "qty": 1, "unit_price_minor": 15000, "currency": "EUR"}],
        subtotal_minor=15000, discount_minor=0, shipping_minor=0,
        tax_minor=0, total_minor=15000, currency="EUR",
        applied_coupon_codes=[],
    )
    script = {"add_to_cart_result": cart_state, "read_cart_result": cart_state}

    p_browser, p_adapter, called = _patch_browser_and_adapter(script)
    monkeypatch.setattr("ahc.buying.orchestrator._get_browser_page", p_browser.__enter__())
    # The above is awkward; use the raw patches directly instead.
    p_browser.__exit__(None, None, None)

    with patch("ahc.buying.orchestrator._get_browser_page") as mock_bw, \
         patch("ahc.buying.orchestrator.get_adapter") as mock_ga:
        from contextlib import contextmanager

        @contextmanager
        def _bw():
            yield (object(), object())

        mock_bw.side_effect = _bw
        mock_ga.side_effect = lambda sc, *, browser_page=None, dry_run=None, **_: _FakeAdapter(
            sc, script=script, dry_run=dry_run
        )

        # CartBuilder._screenshot writes a file; patch it out.
        with patch.object(__import__("ahc.buying.cart", fromlist=["CartBuilder"]).CartBuilder,
                          "_screenshot", return_value="/tmp/fake.png"):
            orch = BuyOrchestratorImpl(compliance=gate, session=session,
                                       screenshot_dir="/tmp/ahc-test-shots")
            r = orch.prepare_cart(plan_id)

    assert r.status == BuyStatus.CART_PREPARED
    assert r.requires_approval is True
    assert r.cart is not None
    assert r.cart.total_minor == 15000


def test_double_buy_blocked_when_record_already_submitted(session):
    """Chapter 9: a plan with a SUBMITTED / CONFIRMED / UNKNOWN record must
    not be re-attempted automatically."""
    plan_id, _ = _build_plan(session)
    gate = _build_gate_allowing_buy()

    # Pre-create a record in SUBMITTED state.
    rec = PurchaseRecord(
        plan_id=plan_id, status=PurchaseStatus.SUBMITTED.value,
        requires_approval=False,
    )
    session.add(rec)
    session.flush()

    orch = BuyOrchestratorImpl(compliance=gate, session=session,
                               screenshot_dir="/tmp/ahc-test-shots")
    r = orch.prepare_cart(plan_id)
    assert r.status == BuyStatus.BLOCKED_DOUBLE_BUY
    assert "manual intervention" in r.error_message


def test_double_buy_blocked_when_record_unknown(session):
    """Chapter 9: UNKNOWN result is the dangerous case - never auto-retry."""
    plan_id, _ = _build_plan(session)
    gate = _build_gate_allowing_buy()
    rec = PurchaseRecord(
        plan_id=plan_id, status=PurchaseStatus.UNKNOWN.value,
        requires_approval=True,
    )
    session.add(rec)
    session.flush()

    orch = BuyOrchestratorImpl(compliance=gate, session=session,
                               screenshot_dir="/tmp/ahc-test-shots")
    r = orch.prepare_cart(plan_id)
    assert r.status == BuyStatus.BLOCKED_DOUBLE_BUY


@pytest.mark.parametrize("bad_status", list(_DOUBLE_BUY_STATUSES))
def test_all_double_buy_statuses_blocked(session, bad_status):
    plan_id, _ = _build_plan(session)
    gate = _build_gate_allowing_buy()
    session.add(PurchaseRecord(plan_id=plan_id, status=bad_status, requires_approval=True))
    session.flush()
    orch = BuyOrchestratorImpl(compliance=gate, session=session,
                               screenshot_dir="/tmp/ahc-test-shots")
    r = orch.prepare_cart(plan_id)
    assert r.status == BuyStatus.BLOCKED_DOUBLE_BUY


def test_max_cart_amount_blocks(session):
    """Cart total above settings.max_cart_amount must abort."""
    plan_id, _ = _build_plan(session, currency="EUR")
    gate = _build_gate_allowing_buy()

    # Build a cart whose total is huge (well over the 300,000 default * 100 = 30M cents).
    huge = to_minor(400_000.0, "EUR")  # 400k EUR -> 40M cents > 30M default
    cart_state = CartState(
        items=[{"sku": "SKU-1", "qty": 1, "unit_price_minor": huge, "currency": "EUR"}],
        subtotal_minor=huge, discount_minor=0, shipping_minor=0,
        tax_minor=0, total_minor=huge, currency="EUR",
    )
    script = {"add_to_cart_result": cart_state, "read_cart_result": cart_state}

    from contextlib import contextmanager

    @contextmanager
    def _bw():
        yield (object(), object())

    with patch("ahc.buying.orchestrator._get_browser_page") as mock_bw, \
         patch("ahc.buying.orchestrator.get_adapter") as mock_ga, \
         patch.object(__import__("ahc.buying.cart", fromlist=["CartBuilder"]).CartBuilder,
                      "_screenshot", return_value="/tmp/fake.png"):
        mock_bw.side_effect = _bw
        mock_ga.side_effect = lambda sc, *, browser_page=None, dry_run=None, **_: _FakeAdapter(
            sc, script=script, dry_run=dry_run
        )
        orch = BuyOrchestratorImpl(compliance=gate, session=session,
                                   screenshot_dir="/tmp/ahc-test-shots")
        r = orch.prepare_cart(plan_id)

    assert r.status == BuyStatus.BLOCKED_MAX_AMOUNT
    assert "exceeds max_cart_amount" in r.error_message


def test_submit_payment_blocked_by_dry_run_default(session, monkeypatch):
    """Chapter 9: real purchases disabled by default."""
    plan_id, _ = _build_plan(session)
    gate = _build_gate_allowing_buy()
    # Make sure dry_run_only is True (test default).
    monkeypatch.setattr("ahc.buying.orchestrator.settings.dry_run_only", True)
    orch = BuyOrchestratorImpl(compliance=gate, session=session,
                               screenshot_dir="/tmp/ahc-test-shots")
    r = orch.submit_payment(plan_id, approval_token="anything")
    assert r.status == BuyStatus.BLOCKED_DRY_RUN


def test_submit_payment_rejects_invalid_token(session, monkeypatch):
    """Even with dry_run_only off, an invalid token must fail."""
    plan_id, _ = _build_plan(session)
    gate = _build_gate_allowing_buy()
    monkeypatch.setattr("ahc.buying.orchestrator.settings.dry_run_only", False)
    monkeypatch.setenv("AHC_APPROVAL_TOKEN", "expected-secret")
    orch = BuyOrchestratorImpl(compliance=gate, session=session,
                               screenshot_dir="/tmp/ahc-test-shots")
    r = orch.submit_payment(plan_id, approval_token="wrong")
    assert r.status == BuyStatus.FAILED
    assert "approval token" in r.error_message


def test_submit_payment_with_valid_token_raises_buyerror(session, monkeypatch):
    """Chapter 9 / 14: even a valid token must not silently charge - the
    per-store checkout is not implemented. The orchestrator raises BuyError
    rather than returning a success result."""
    from ahc.buying.base import BuyError

    plan_id, _ = _build_plan(session)
    gate = _build_gate_allowing_buy()
    monkeypatch.setattr("ahc.buying.orchestrator.settings.dry_run_only", False)
    monkeypatch.setenv("AHC_APPROVAL_TOKEN", "expected-secret")
    orch = BuyOrchestratorImpl(compliance=gate, session=session,
                               screenshot_dir="/tmp/ahc-test-shots")
    with pytest.raises(BuyError, match="per-store implementation"):
        orch.submit_payment(plan_id, approval_token="expected-secret")


def test_plan_not_found_returns_failed(session):
    gate = _build_gate_allowing_buy()
    orch = BuyOrchestratorImpl(compliance=gate, session=session,
                               screenshot_dir="/tmp/ahc-test-shots")
    r = orch.prepare_cart(999999)
    assert r.status == BuyStatus.FAILED
    assert "not found" in r.error_message
