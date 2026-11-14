"""Coupon source contract.

A "source" is one place we look for coupons: an aggregator (RetailMeNot),
a community deal site (mydealz), or a store's own promotions page. Each
source returns a list of `RawCoupon` dataclasses; the deduplicator and
validator then normalise / merge / verify them.

The source MUST ask the compliance gate before fetching (Chapter 4: each
source's terms and method must be checked). The base class enforces this
by calling `self._compliance.allow_scrape(source_slug)` in `fetch()`;
concrete sources do not have to repeat the check.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from ..utils.money import to_minor


class CouponSourceError(Exception):
    """Base for coupon-source errors."""


# Canonical discount types - everything is normalised to one of these.
NORMALISED_DISCOUNT_TYPES = frozenset({
    "percent",
    "fixed_amount",
    "free_shipping",
    "cashback",
    "bundle",
    "gift",
    "other",
})


@dataclass
class RawCoupon:
    """Raw, unverified coupon as extracted from one source.

    Fields use the *source's* currency and units; the deduplicator +
    validator normalise them. Anything unknown is left None rather than
    guessed - Chapter 7: unverified values never enter cost calculations.
    """
    store_slug: Optional[str]            # None if source is multi-store
    code: str
    title: Optional[str] = None
    description: Optional[str] = None

    discount_type_raw: str = ""          # free text from source
    discount_type: str = "other"         # normalised into NORMALISED_DISCOUNT_TYPES
    discount_value: Optional[float] = None
    discount_currency: Optional[str] = None

    min_spend_major: Optional[float] = None
    min_spend_currency: Optional[str] = None
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

    # --- normalisation helpers ---
    def discount_value_minor(self) -> Optional[int]:
        if self.discount_type != "fixed_amount" or self.discount_value is None:
            return None
        if not self.discount_currency:
            return None
        return to_minor(self.discount_value, self.discount_currency)

    def min_spend_minor(self) -> Optional[int]:
        if self.min_spend_major is None or not self.min_spend_currency:
            return None
        return to_minor(self.min_spend_major, self.min_spend_currency)


class AbstractCouponSource(abc.ABC):
    """Contract for every coupon source adapter."""

    #: Slug of this source - must match config/coupon_sources.yaml.
    slug: str = ""

    def __init__(self, source_config: dict, http_session=None, *, compliance=None):
        self.cfg = source_config
        self.slug = source_config.get("slug", self.slug)
        self.url = source_config.get("url", "")
        self.country = source_config.get("country", "US")
        self._http = http_session
        self._compliance = compliance  # ahc.compliance.ComplianceGate or None

    @abc.abstractmethod
    def fetch(self) -> list[RawCoupon]:
        """Return raw coupons. Must be idempotent: running twice yields
        equivalent data (modulo timestamps)."""

    # --- shared helpers ---
    def _require_http(self) -> None:
        if self._http is None:
            raise CouponSourceError(f"{self.slug}: HTTP session required")

    def _check_compliance(self) -> None:
        if self._compliance is None:
            # No gate configured - be conservative.
            raise CouponSourceError(
                f"{self.slug}: compliance gate not configured; refusing to fetch"
            )
        verdict = self._compliance.allow_scrape(self.slug)
        if not verdict.allowed:
            raise CouponSourceError(
                f"{self.slug}: compliance denied scrape ({verdict.reason})"
            )
