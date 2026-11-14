"""After Hours Club order-confirmation email parser.

TODO: the exact After Hours Club email template is not yet sampled, so this
parser reuses BUYMA-flavoured patterns (English + Japanese labels) as a
reasonable default. Once a real AHC confirmation email is captured, replace
the pattern tuples below with the platform's actual labels and any
platform-specific order-id format. Until then, behaviour mirrors
``BuymaParser`` and any miss degrades to ``None`` rather than raising.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional, Tuple

from ..base import OrderParser, register_parser
from ..models import ParsedOrder, ParsedOrderItem
from .buyma import (
    _BUYER_EMAIL_PATTERNS,
    _BUYER_NAME_PATTERNS,
    _ORDER_ID_PATTERNS,
    _PLACED_AT_PATTERNS,
    _SALE_PRICE_PATTERNS,
    _SHIP_ADDRESS_PATTERNS,
    _SHIP_COUNTRY_PATTERNS,
    _extract_body,
    _first_match,
    _money_to_minor,
)


@register_parser
class AfterHoursParser(OrderParser):
    """After Hours Club order parser.

    Shares BUYMA's regex vocabulary (see module TODO). Distinct class so
    the registry carries an explicit ``after_hours`` entry and a real
    template can be dropped in without touching ``BuymaParser``.
    """

    source = "after_hours"

    def parse(self, raw_bytes: bytes) -> Optional[ParsedOrder]:
        try:
            text, _from_value = _extract_body(raw_bytes)
        except Exception:
            return None
        if not text:
            return None

        order_id = _first_match(_ORDER_ID_PATTERNS, text)
        if not order_id:
            return None

        buyer_name = _first_match(_BUYER_NAME_PATTERNS, text)
        buyer_email = _first_match(_BUYER_EMAIL_PATTERNS, text)
        ship_country = _first_match(_SHIP_COUNTRY_PATTERNS, text)
        ship_address = _first_match(_SHIP_ADDRESS_PATTERNS, text)

        sale_currency: Optional[str] = None
        sale_minor: Optional[int] = None
        for p in _SALE_PRICE_PATTERNS:
            m = p.search(text)
            if m:
                sale_currency = (m.group(1) or "").upper() or None
                sale_minor = _money_to_minor(sale_currency, m.group(2))
                break

        placed_at: Optional[datetime] = None
        for p in _PLACED_AT_PATTERNS:
            m = p.search(text)
            if m:
                try:
                    placed_at = datetime.fromisoformat(m.group(1).replace(" ", "T"))
                except ValueError:
                    placed_at = None
                break

        items = self._parse_items(text)

        return ParsedOrder(
            source=self.source,
            external_order_id=order_id,
            buyer_name=buyer_name,
            buyer_email=buyer_email,
            ship_country=ship_country,
            ship_address=ship_address,
            sale_price_minor=sale_minor,
            sale_currency=sale_currency,
            placed_at=placed_at,
            items=items,
            raw_email_path=None,
        )

    @staticmethod
    def _parse_items(text: str) -> List[ParsedOrderItem]:
        """Single best-effort item (TODO: extend once AHC template known).

        Looks for one brand/model/size/qty/price occurrence and packs them
        into one item. If nothing matches, returns a placeholder item with
        all fields ``None`` and quantity 1.
        """
        from .buyma import (
            _ITEM_BRAND,
            _ITEM_COLORWAY,
            _ITEM_MODEL,
            _ITEM_PRICE,
            _ITEM_QTY,
            _ITEM_SIZE,
            _flatten_groups,
        )

        brand = _flatten_groups(_ITEM_BRAND.findall(text))
        model = _flatten_groups(_ITEM_MODEL.findall(text))
        colorway = _flatten_groups(_ITEM_COLORWAY.findall(text))
        size = _flatten_groups(_ITEM_SIZE.findall(text))
        qty_raw = _ITEM_QTY.findall(text)
        qty = 1
        if qty_raw:
            first = qty_raw[0]
            if isinstance(first, tuple):
                g = next((g for g in first if g), None)
                qty = int(g) if g else 1
            else:
                qty = int(first) if first else 1
        price_raw = _ITEM_PRICE.findall(text)
        currency: Optional[str] = None
        amount: Optional[str] = None
        if price_raw:
            first = price_raw[0]
            if isinstance(first, tuple):
                currency = next((g for g in (first[0], first[2]) if g), None)
                amount = next((g for g in (first[1], first[3]) if g), None)
            else:
                amount = first
            if currency:
                currency = currency.upper()

        return [
            ParsedOrderItem(
                requested_brand=brand[0].strip() if brand and brand[0] else None,
                requested_model=model[0].strip() if model and model[0] else None,
                requested_colorway=colorway[0].strip() if colorway and colorway[0] else None,
                requested_size=size[0].strip() if size and size[0] else None,
                quantity=qty,
                sale_price_minor=_money_to_minor(currency, amount),
                sale_currency=currency,
            )
        ]
