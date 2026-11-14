"""Chapter 11 tests: coupon dedup + expiry + applicability."""
from __future__ import annotations

from datetime import date, timedelta

from ahc.coupons.base import RawCoupon
from ahc.coupons.dedup import Deduplicator
from ahc.coupons.validator import CouponValidator


# --- 重複排除 ----------------------------------------------------------------

def test_dedup_collapses_case_and_value_duplicates(sample_raw_coupons):
    d = Deduplicator()
    out = d.dedup(sample_raw_coupons)
    # Two unique coupons: SUMMER10 (collapsed with summer10) and FREESHIP.
    codes_lower = {c.code.lower() for c in out}
    assert codes_lower == {"summer10", "freeship"}
    assert len(out) == 2


def test_dedup_keeps_most_recent_seen(sample_raw_coupons):
    # Force the second "summer10" to have a newer seen_at than the first.
    import datetime as dt
    sample_raw_coupons[0].seen_at = dt.datetime(2026, 11, 1)
    sample_raw_coupons[1].seen_at = dt.datetime(2026, 11, 10)
    d = Deduplicator()
    out = d.dedup(sample_raw_coupons)
    summer = next(c for c in out if c.code.lower() == "summer10")
    # The newer title "10% off sitewide" should win.
    assert summer.title == "10% off sitewide"


def test_dedup_multi_store_coupons_separate_by_source():
    """Coupons with store_slug=None must not merge across sources."""
    from datetime import date
    a = RawCoupon(
        store_slug=None, code="DEAL", discount_type="other",
        source_slug="mydealz", source_url="x",
    )
    b = RawCoupon(
        store_slug=None, code="DEAL", discount_type="other",
        source_slug="dealabs", source_url="y",
    )
    out = Deduplicator().dedup([a, b])
    assert len(out) == 2


# --- 有効期限判定 ------------------------------------------------------------

def test_validator_marks_expired():
    from ahc.coupons.dedup import Deduplicator
    rec = Deduplicator().to_record(
        RawCoupon(
            store_slug="bstn", code="OLD", discount_type="percent",
            discount_value=20.0, valid_until=date.today() - timedelta(days=1),
            source_slug="retailmenot", source_url="x",
        )
    )
    out = CouponValidator().validate(rec)
    assert out.status == "expired"


def test_validator_keeps_unverified_when_not_expired():
    from ahc.coupons.dedup import Deduplicator
    rec = Deduplicator().to_record(
        RawCoupon(
            store_slug="bstn", code="NEW", discount_type="percent",
            discount_value=20.0, valid_until=date.today() + timedelta(days=30),
            source_slug="retailmenot", source_url="x",
        )
    )
    out = CouponValidator().validate(rec)
    assert out.status == "unverified"


def test_validator_no_expiry_date_stays_unverified():
    from ahc.coupons.dedup import Deduplicator
    rec = Deduplicator().to_record(
        RawCoupon(
            store_slug="bstn", code="NOEXP", discount_type="percent",
            discount_value=20.0, valid_until=None,
            source_slug="retailmenot", source_url="x",
        )
    )
    out = CouponValidator().validate(rec)
    assert out.status == "unverified"


# --- 対象外商品判定 ----------------------------------------------------------

def test_applicability_excludes_excluded_brand():
    from ahc.coupons.dedup import Deduplicator
    rec = Deduplicator().to_record(
        RawCoupon(
            store_slug="bstn", code="NOTNIKE", discount_type="percent",
            discount_value=10.0, excluded_brands=["Nike"],
            source_slug="retailmenot", source_url="x",
        )
    )
    ok, reason = CouponValidator().is_applicable(
        rec, brand="Nike", cart_minor=10000, currency="EUR", is_first_order=False
    )
    assert ok is False
    assert "brand" in reason.lower() or "excluded" in reason.lower()


def test_applicability_eligible_brand_passes():
    from ahc.coupons.dedup import Deduplicator
    rec = Deduplicator().to_record(
        RawCoupon(
            store_slug="bstn", code="ADIDAS", discount_type="percent",
            discount_value=10.0, eligible_brands=["Adidas"],
            source_slug="retailmenot", source_url="x",
        )
    )
    ok, _ = CouponValidator().is_applicable(
        rec, brand="Adidas", cart_minor=10000, currency="EUR", is_first_order=False
    )
    assert ok is True


def test_applicability_min_spend_currency_mismatch_fails():
    """Cross-currency min spend should fail (not silently pass)."""
    from ahc.coupons.dedup import Deduplicator
    rec = Deduplicator().to_record(
        RawCoupon(
            store_slug="bstn", code="MIN100", discount_type="percent",
            discount_value=10.0, min_spend_major=100.0, min_spend_currency="EUR",
            source_slug="retailmenot", source_url="x",
        )
    )
    ok, reason = CouponValidator().is_applicable(
        rec, brand=None, cart_minor=10000, currency="USD", is_first_order=False
    )
    assert ok is False
    assert "currency" in reason.lower() or "min" in reason.lower()


def test_applicability_first_order_only_blocks_repeat():
    from ahc.coupons.dedup import Deduplicator
    rec = Deduplicator().to_record(
        RawCoupon(
            store_slug="bstn", code="FIRST", discount_type="percent",
            discount_value=10.0, first_order_only=True,
            source_slug="retailmenot", source_url="x",
        )
    )
    ok, reason = CouponValidator().is_applicable(
        rec, brand=None, cart_minor=10000, currency="EUR", is_first_order=False
    )
    assert ok is False
    assert "first" in reason.lower()
