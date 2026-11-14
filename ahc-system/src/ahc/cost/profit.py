"""Profit calculation + best-plan picker.

Chapter 7 rules enforced here:
  - Unverified coupons / future cashback are NEVER counted in confirmed profit.
    They enter as `is_estimate=True` lines and are excluded from
    `confirmed_total_jpy_minor`.
  - Sale price minus *confirmed* total = confirmed profit.
  - `meets_min_profit` is computed against the confirmed profit, not the
    estimate-inflated number.
  - If `breakdown.has_estimates()`, the plan is marked as "needs more data"
    and not selectable unless explicitly allowed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from ..config import settings
from .models import CostBreakdown
from ..db.models import CostType


@dataclass
class ProfitResult:
    sale_price_jpy_minor: int
    confirmed_cost_jpy_minor: int
    estimated_cost_jpy_minor: int
    confirmed_profit_jpy_minor: int
    estimated_profit_jpy_minor: int   # includes estimates - preview only
    meets_min_profit: bool
    has_estimates: bool
    blocked_reason: Optional[str] = None


def compute_profit(
    sale_price_jpy_minor: int,
    breakdown: CostBreakdown,
    *,
    min_profit_jpy_minor: Optional[int] = None,
) -> ProfitResult:
    """Compute profit from a sale price and a cost breakdown.

    `min_profit_jpy_minor` defaults to settings.min_profit_jpy (Chapter 9:
    minimum-profit guardrail).
    """
    min_profit = (
        settings.min_profit_jpy if min_profit_jpy_minor is None else min_profit_jpy_minor
    )
    # Convert min_profit to minor: settings stores it as major JPY float.
    min_minor = int(round(min_profit)) if min_profit < 1000 else int(round(min_profit))
    # Be defensive: settings.min_profit_jpy is a float in major units (JPY),
    # so multiply by 1 (JPY has 0 decimals) -> int directly.
    min_minor = int(round(min_profit))

    confirmed = breakdown.confirmed_total_jpy_minor
    estimated = breakdown.estimated_total_jpy_minor
    confirmed_profit = sale_price_jpy_minor - confirmed
    estimated_profit = sale_price_jpy_minor - confirmed - estimated

    has_est = breakdown.has_estimates()
    meets = confirmed_profit >= min_minor

    blocked = None
    if has_est and not meets:
        blocked = "has_estimates_and_below_min_profit"
    elif has_est:
        blocked = "has_estimates"
    elif not meets:
        blocked = "below_min_profit"

    return ProfitResult(
        sale_price_jpy_minor=sale_price_jpy_minor,
        confirmed_cost_jpy_minor=confirmed,
        estimated_cost_jpy_minor=estimated,
        confirmed_profit_jpy_minor=confirmed_profit,
        estimated_profit_jpy_minor=estimated_profit,
        meets_min_profit=meets,
        has_estimates=has_est,
        blocked_reason=blocked,
    )


@dataclass
class PlanCandidate:
    """One (order_item, store, coupon?) candidate plan + its ProfitResult."""
    store_slug: str
    coupon_code: Optional[str]
    breakdown: CostBreakdown
    profit: ProfitResult

    @property
    def selectable(self) -> bool:
        return (
            self.profit.meets_min_profit
            and not self.profit.has_estimates
            and self.profit.blocked_reason is None
        )


def pick_best_plan(
    candidates: Iterable[PlanCandidate],
    *,
    allow_estimates: bool = False,
) -> Optional[PlanCandidate]:
    """Pick the highest-confirmed-profit plan that meets the min-profit rule.

    By default rejects plans with estimates. If `allow_estimates=True`,
    considers them but ranks confirmed-profit-first.
    """
    selectable = []
    for c in candidates:
        if not c.profit.meets_min_profit:
            continue
        if c.profit.has_estimates and not allow_estimates:
            continue
        selectable.append(c)

    if not selectable:
        return None

    # Sort: confirmed profit desc, then estimated profit desc, then fewer
    # estimate lines first.
    selectable.sort(
        key=lambda c: (
            -c.profit.confirmed_profit_jpy_minor,
            -c.profit.estimated_profit_jpy_minor,
            c.profit.has_estimates,
        )
    )
    return selectable[0]
