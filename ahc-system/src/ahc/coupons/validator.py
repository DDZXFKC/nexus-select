"""Coupon validation + applicability checks.

Two distinct concerns live here:

  * ``validate`` — collection-time expiry check. A coupon whose ``valid_until``
    is in the past is marked ``expired``. Otherwise its status is left alone
    (freshly converted records are ``unverified``; already-verified coupons
    keep their verification state). Real verification only happens when a
    coupon is actually applied in the buying flow, because that is the only
    moment we learn from the store whether the code is accepted.

  * ``is_applicable`` — pre-filter used when choosing a coupon for a cart.
    Checks brand restrictions, minimum spend, first-order-only, and region.
    It deliberately does NOT re-check expiry or final verification: the
    caller is expected to have run ``validate`` / ``mark_verified`` first and
    to have excluded expired / blacklisted coupons before filtering.

  * ``mark_verified`` — set the verification outcome after an apply attempt.
"""
from __future__ import annotations

import dataclasses
from datetime import date, datetime
from typing import Optional

from .models import CouponRecord


class CouponValidator:
    """Stateless coupon validation and applicability logic."""

    # ----- collection-time validation -----
    def validate(self, record: CouponRecord, *, today: Optional[date] = None) -> CouponRecord:
        """Return a new CouponRecord with status updated for expiry.

        - If ``valid_until`` is set and strictly before ``today``: status
          becomes ``expired`` (this overrides any prior status, because an
          expired coupon cannot remain "verified_valid").
        - Otherwise the status is preserved. For freshly converted records
          that means it stays ``unverified``; already-verified or blacklisted
          coupons are not clobbered, so re-running ``validate`` on a loaded
          record is safe and idempotent.
        """
        today = today or date.today()
        if record.valid_until is not None and record.valid_until < today:
            new_status = "expired"
        else:
            # Preserve verification / blacklist state; default stays unverified.
            new_status = (
                record.status
                if record.status in ("verified_valid", "verified_invalid", "blacklisted")
                else "unverified"
            )
        return dataclasses.replace(record, status=new_status)

    # ----- pre-apply applicability filter -----
    def is_applicable(
        self,
        record: CouponRecord,
        *,
        brand: Optional[str],
        cart_minor: int,
        currency: str,
        is_first_order: bool,
    ) -> tuple[bool, str]:
        """Check the four collection-time restrictions.

        Returns ``(applicable, reason)``. The first failing restriction
        short-circuits and is named in the reason; on success the reason
        explains the result (and flags any restriction that still needs
        checkout-time confirmation).

        Status / expiry filtering is the caller's job; this method only
        evaluates the four restrictions listed in the spec.
        """
        # 1. brand restrictions (eligible / excluded lists)
        if not record.applies_to_brand(brand):
            if brand and record.excluded_brands:
                return (
                    False,
                    f"brand '{brand}' is excluded for this coupon",
                )
            if record.eligible_brands:
                return (
                    False,
                    f"brand '{brand}' not in eligible brands {record.eligible_brands}",
                )
            return (False, f"brand '{brand}' not eligible for this coupon")

        # 2. minimum spend
        if not record.meets_min_spend(cart_minor, currency):
            if (
                record.min_spend_minor is not None
                and (record.min_spend_currency or "").upper() != (currency or "").upper()
            ):
                return (
                    False,
                    f"min spend currency {record.min_spend_currency} does not match cart currency {currency}",
                )
            return (
                False,
                f"cart {cart_minor} {currency} below min spend "
                f"{record.min_spend_minor} {record.min_spend_currency}",
            )

        # 3. first-order-only
        if record.first_order_only and not is_first_order:
            return (False, "first-order-only coupon; this is not a first order")

        # 4. region / ship_region
        # We do not have a ship destination at filter time. Following the same
        # "be permissive at filter stage, narrow at checkout" philosophy as
        # ``applies_to_brand`` for unknown brands, a set ship_region is noted
        # but not used to reject here.
        if record.ship_region:
            return (
                True,
                f"applicable; ship_region='{record.ship_region}' requires "
                "destination check at checkout",
            )

        return (True, "applicable")

    # ----- post-apply verification -----
    def mark_verified(self, record: CouponRecord, valid: bool) -> CouponRecord:
        """Record the outcome of an apply attempt.

        Sets status to ``verified_valid`` or ``verified_invalid`` and stamps
        ``last_verified_at`` with the current UTC time.
        """
        new_status = "verified_valid" if valid else "verified_invalid"
        return dataclasses.replace(
            record,
            status=new_status,
            last_verified_at=datetime.utcnow(),
        )
