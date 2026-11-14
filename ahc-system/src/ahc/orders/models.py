"""Parsed-order dataclasses for the intake pipeline.

These are the in-memory representation produced by an `OrderParser` and
consumed by `OrderManager.ingest`. They deliberately mirror the columns of
the `orders` / `order_items` tables so persistence is a field-by-field copy
with no transformation. Anything the parser could not extract is left
``None`` rather than guessed - Chapter 7: unverified values never enter the
cost model.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class ParsedOrderItem:
    """One line item requested by the buyer.

    Every field except ``quantity`` is optional: the email template may omit
    brand, colorway or size, and the parser must not raise on a miss.
    """

    requested_brand: Optional[str] = None
    requested_model: Optional[str] = None
    requested_colorway: Optional[str] = None
    requested_size: Optional[str] = None
    quantity: int = 1
    sale_price_minor: Optional[int] = None
    sale_currency: Optional[str] = None


@dataclass
class ParsedOrder:
    """A single order extracted from one email.

    ``source`` is the platform slug ("buyma" / "after_hours") and
    ``external_order_id`` is the platform's own order id; together they form
    the natural key used by ``OrderManager.ingest`` to deduplicate.
    """

    source: str
    external_order_id: str
    buyer_name: Optional[str] = None
    buyer_email: Optional[str] = None
    ship_country: Optional[str] = None
    ship_address: Optional[str] = None
    sale_price_minor: Optional[int] = None
    sale_currency: Optional[str] = None
    placed_at: Optional[datetime] = None
    items: List[ParsedOrderItem] = field(default_factory=list)
    raw_email_path: Optional[str] = None
