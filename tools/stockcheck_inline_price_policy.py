"""On-page stock-check offer price policy (owner 2026-11-21).

This is a pure pricing decision, not a merchant-cost calculator or Woo price
override. Recomputed price MUST come from a separately validated full cost
calculation; unverified discount/cost entries cannot be treated as zero.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class PriceDecision:
    status: str
    listed_jpy: int
    recomputed_jpy: int | None
    checkout_jpy: int | None
    difference_jpy: int | None
    requires_customer_confirmation: bool


def resolve_price_case(listed_jpy, recomputed_jpy, *, tolerance_jpy=400):
    """Owner rule: <400 JPY upward change absorbed; >=400 customer quote."""
    if type(listed_jpy) is not int or listed_jpy <= 0:
        raise ValueError("invalid listed price")
    if type(tolerance_jpy) is not int or tolerance_jpy < 0:
        raise ValueError("invalid tolerance")
    if recomputed_jpy is None:
        return PriceDecision("PRICE_UNKNOWN", listed_jpy, None, None, None, False)
    if type(recomputed_jpy) is not int or recomputed_jpy <= 0:
        raise ValueError("invalid recomputed price")
    difference = recomputed_jpy - listed_jpy
    if difference >= tolerance_jpy:
        return PriceDecision("QUOTE_CONFIRM_REQUIRED", listed_jpy,
                             recomputed_jpy, recomputed_jpy, difference, True)
    return PriceDecision("LISTED", listed_jpy, recomputed_jpy,
                         listed_jpy, difference, False)
