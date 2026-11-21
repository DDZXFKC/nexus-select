"""Owner-verified spreadsheet price calculation, 2026-11-21.

Settings tab of AFTER HOURS CLUB 商品管理: FX 158 JPY/USD, card 2%,
international shipping 2200, partner 1500, packing 60,
BUYMA fee 5.5%, margin 16%, divisor 0.785.
The ¥100 ceil is applied to UNROUNDED cost. Displayed cost uses ROUND_HALF_UP.
No live merchant stock/price is asserted by this module.
"""
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP, InvalidOperation
from dataclasses import dataclass

FX = Decimal("158")
CARD_RATE = Decimal("0.02")
INTERNATIONAL = Decimal("2200")
PARTNER = Decimal("1500")
PACKING = Decimal("60")
DIVISOR = Decimal("0.785")

@dataclass(frozen=True)
class CostedPrice:
    source_usd: Decimal
    total_cost_unrounded_jpy: Decimal
    total_cost_rounded_jpy: int
    sale_price_jpy: int

def _money(value):
    if isinstance(value, bool) or value is None or isinstance(value, float):
        raise ValueError("USD amount must be a decimal string or integer")
    try:
        v = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("invalid USD") from exc
    if not v.is_finite() or v <= 0:
        raise ValueError("USD must be finite positive amount")
    return v

def owner_price_from_usd(source_usd, *, confirmed_inputs=True, complete_cost=True,
                         coupon_applied_usd=None):
    """USD price after any CONFIRMED coupon. No unknown tax/fee may be zeroed.

    confirmed_inputs is only an explicit evidence gate: callers must first
    confirm the exact requested variant, source price/currency and current FX
    and that all applicable local/import fees are covered by the approved rule.
    """
    if confirmed_inputs is not True or complete_cost is not True:
        raise ValueError("cost evidence incomplete; purchase not permitted")
    source = _money(coupon_applied_usd if coupon_applied_usd is not None else source_usd)
    raw = source * FX * (Decimal("1") + CARD_RATE) + INTERNATIONAL + PARTNER + PACKING
    rounded_cost = int(raw.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    sale = int((raw / DIVISOR / Decimal("100")).to_integral_value(rounding=ROUND_CEILING) * Decimal("100"))
    return CostedPrice(source, raw, rounded_cost, sale)
