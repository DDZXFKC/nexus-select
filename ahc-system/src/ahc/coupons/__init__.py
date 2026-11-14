"""Coupon collection package."""
from .base import (
    AbstractCouponSource,
    CouponSourceError,
    RawCoupon,
    NORMALISED_DISCOUNT_TYPES,
)
from .models import CouponRecord
from .collector import CouponCollector
from .dedup import Deduplicator
from .validator import CouponValidator

__all__ = [
    "AbstractCouponSource",
    "CouponSourceError",
    "RawCoupon",
    "NORMALISED_DISCOUNT_TYPES",
    "CouponRecord",
    "CouponCollector",
    "Deduplicator",
    "CouponValidator",
]
