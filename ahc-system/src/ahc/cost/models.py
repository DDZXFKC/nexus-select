"""Dataclasses for cost inputs and outputs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..db.models import CostType


@dataclass
class CostInput:
    """One raw cost input (pre-FX, in source currency)."""
    cost_type: CostType
    amount_minor: int          # source-currency minor units
    currency: str
    is_estimate: bool = False
    note: str = ""

    def __post_init__(self) -> None:
        if self.amount_minor < 0 and self.cost_type != CostType.COUPON_DISCOUNT:
            raise ValueError(
                f"Cost {self.cost_type}: negative amount only allowed for coupon_discount"
            )


@dataclass
class CostLine:
    """A cost line *after* FX conversion to JPY minor."""
    cost_type: CostType
    amount_minor: int          # source currency
    currency: str
    fx_rate: float
    amount_jpy_minor: int
    is_estimate: bool
    note: str = ""


@dataclass
class CostBreakdown:
    """Full breakdown for one purchase plan."""
    lines: list[CostLine] = field(default_factory=list)

    @property
    def confirmed_total_jpy_minor(self) -> int:
        """Sum of non-estimate lines. Chapter 7: estimates excluded."""
        return sum(l.amount_jpy_minor for l in self.lines if not l.is_estimate)

    @property
    def estimated_total_jpy_minor(self) -> int:
        """Sum of estimate lines only."""
        return sum(l.amount_jpy_minor for l in self.lines if l.is_estimate)

    @property
    def total_jpy_minor(self) -> int:
        return self.confirmed_total_jpy_minor + self.estimated_total_jpy_minor

    def has_estimates(self) -> bool:
        return any(l.is_estimate for l in self.lines)

    def line(self, cost_type: CostType) -> Optional[CostLine]:
        for l in self.lines:
            if l.cost_type == cost_type:
                return l
        return None
