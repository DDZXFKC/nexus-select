"""In-memory coupon record - the deduplicator/validator output.

Distinct from the SQLAlchemy `Coupon` ORM model: this is what flows between
modules during a single pipeline run. The collector persists the final list
to the DB at the end.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class CouponRecord:
    store_slug: Optional[str]
    code: str
    title: Optional[str]
    description: Optional[str]
    discount_type: str           # normalised
    discount_value: Optional[float]
    discount_currency: Optional[str]
    min_spend_minor: Optional[int]
    min_spend_currency: Optional[str]
    eligible_brands: list[str] = field(default_factory=list)
    excluded_brands: list[str] = field(default_factory=list)
    eligible_categories: list[str] = field(default_factory=list)
    first_order_only: bool = False
    combinable: bool = False
    ship_region: Optional[str] = None
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    source_slug: str = ""
    source_url: str = ""
    seen_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "unverified"   # unverified / verified_valid / verified_invalid / expired / blacklisted
    last_verified_at: Optional[datetime] = None
    # dedup signature (code + store + discount_value + valid_until)
    signature: str = ""

    def is_expired(self, today: Optional[date] = None) -> bool:
        if self.valid_until is None:
            return False
        today = today or date.today()
        return self.valid_until < today

    def applies_to_brand(self, brand: Optional[str]) -> bool:
        if not brand:
            return True  # unknown brand - be permissive at filter stage, validator will narrow
        if brand.lower() in (b.lower() for b in self.excluded_brands):
            return False
        if self.eligible_brands and brand.lower() not in (b.lower() for b in self.eligible_brands):
            return False
        return True

    def meets_min_spend(self, cart_minor: int, currency: str) -> bool:
        if self.min_spend_minor is None:
            return True
        if (self.min_spend_currency or "").upper() != currency.upper():
            # Cross-currency comparison needs FX; treat as not-meetable until validator converts.
            return False
        return cart_minor >= self.min_spend_minor
