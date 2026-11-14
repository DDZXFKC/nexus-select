"""Coupon deduplication and RawCoupon -> CouponRecord conversion.

The deduplicator collapses raw coupons that describe the *same* offer across
one source's batch (and, for store-specific coupons, across sources once the
collector feeds batches through). Two coupons are "the same offer" when their
dedup signature matches:

    (store_slug or "", code.lower(), discount_type, discount_value or 0,
     valid_until or date.max)

When several raws share a signature we keep the one with the most-recent
``seen_at``; ties are broken by the longest ``valid_until`` (Chapter 7:
prefer the offer that is valid longest, so we don't drop a still-live coupon
in favour of an about-to-expire duplicate).

Multi-store coupons (``store_slug`` is None, e.g. mydealz deals that are not
tied to one retailer) get their *own bucket per source*: the source slug is
appended to the bucket key so mydealz deals and dealabs deals never merge,
even though both have ``store_slug=None`` and ``code=""``.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from .base import RawCoupon
from .models import CouponRecord


class Deduplicator:
    """Collapse equivalent raw coupons within a batch."""

    # ----- signature -----
    @staticmethod
    def _signature_tuple(raw: RawCoupon) -> tuple:
        """The canonical dedup signature (without the per-source extension).

        Returned as a tuple so it is hashable and usable as a dict key.
        """
        return (
            raw.store_slug or "",
            (raw.code or "").lower(),
            raw.discount_type or "other",
            raw.discount_value or 0,
            raw.valid_until or date.max,
        )

    def _bucket_key(self, raw: RawCoupon) -> tuple:
        """Bucket key: the signature, extended with the source slug when the
        coupon is multi-store so each source keeps its own deal stream."""
        sig = self._signature_tuple(raw)
        if raw.store_slug is None:
            # Multi-store: keep deals from different sources in separate buckets.
            return sig + (raw.source_slug or "",)
        return sig

    @staticmethod
    def _signature_str(raw: RawCoupon) -> str:
        sig = Deduplicator._signature_tuple(raw)
        vu = sig[4]
        vu_str = vu.isoformat() if isinstance(vu, date) else str(vu)
        return "|".join((str(sig[0]), sig[1], sig[2], str(sig[3]), vu_str))

    @staticmethod
    def _prefer(new: RawCoupon, current: RawCoupon) -> bool:
        """True if ``new`` should replace ``current`` in a bucket.

        Most-recent ``seen_at`` wins; tie broken by longest ``valid_until``.
        """
        if new.seen_at > current.seen_at:
            return True
        if new.seen_at < current.seen_at:
            return False
        new_vu = new.valid_until or date.max
        cur_vu = current.valid_until or date.max
        return new_vu > cur_vu

    # ----- public API -----
    def dedup(self, raws: list[RawCoupon]) -> list[RawCoupon]:
        """Return one representative RawCoupon per dedup bucket.

        Order of the input is not guaranteed to be preserved; callers that
        care about ordering should sort the result.
        """
        buckets: dict[tuple, RawCoupon] = {}
        for raw in raws:
            key = self._bucket_key(raw)
            current = buckets.get(key)
            if current is None or self._prefer(raw, current):
                buckets[key] = raw
        return list(buckets.values())

    def to_record(self, raw: RawCoupon) -> CouponRecord:
        """Convert a RawCoupon into a CouponRecord and compute its signature.

        Money fields are normalised to minor units here (the only place a
        float major amount should appear is on RawCoupon; CouponRecord and
        the DB stay in minor units).
        """
        return CouponRecord(
            store_slug=raw.store_slug,
            code=raw.code,
            title=raw.title,
            description=raw.description,
            discount_type=raw.discount_type or "other",
            discount_value=raw.discount_value,
            discount_currency=raw.discount_currency,
            min_spend_minor=raw.min_spend_minor(),
            min_spend_currency=raw.min_spend_currency,
            eligible_brands=list(raw.eligible_brands),
            excluded_brands=list(raw.excluded_brands),
            eligible_categories=list(raw.eligible_categories),
            first_order_only=raw.first_order_only,
            combinable=raw.combinable,
            ship_region=raw.ship_region,
            valid_from=raw.valid_from,
            valid_until=raw.valid_until,
            source_slug=raw.source_slug,
            source_url=raw.source_url,
            seen_at=raw.seen_at,
            status="unverified",
            last_verified_at=None,
            signature=self._signature_str(raw),
        )
