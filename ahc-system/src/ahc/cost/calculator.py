"""Cost calculator: turns a list of CostInput into a CostBreakdown.

The calculator never invents numbers: if a CostInput is missing for a
required cost type (e.g. customs duty is unknown), it is simply not added;
the breakdown's `has_estimates()` and confirmed-vs-estimated split make the
gap visible. Chapter 7 explicitly forbids treating unknowns as zero.
"""
from __future__ import annotations

from typing import Iterable

from ..utils.money import FxTable
from .models import CostBreakdown, CostInput, CostLine


class CostCalculator:
    """Stateless calculator parameterised by an FX table."""

    def __init__(self, fx: FxTable):
        self._fx = fx

    def calculate(self, inputs: Iterable[CostInput]) -> CostBreakdown:
        breakdown = CostBreakdown()
        for inp in inputs:
            rate = self._fx.get(inp.currency).rate
            jpy_minor = self._fx.to_jpy_minor(inp.amount_minor, inp.currency)
            breakdown.lines.append(
                CostLine(
                    cost_type=inp.cost_type,
                    amount_minor=inp.amount_minor,
                    currency=inp.currency,
                    fx_rate=rate,
                    amount_jpy_minor=jpy_minor,
                    is_estimate=inp.is_estimate,
                    note=inp.note,
                )
            )
        return breakdown

    def add_line(self, breakdown: CostBreakdown, inp: CostInput) -> CostBreakdown:
        """Convenience: append one more cost line to an existing breakdown."""
        rate = self._fx.get(inp.currency).rate
        jpy_minor = self._fx.to_jpy_minor(inp.amount_minor, inp.currency)
        breakdown.lines.append(
            CostLine(
                cost_type=inp.cost_type,
                amount_minor=inp.amount_minor,
                currency=inp.currency,
                fx_rate=rate,
                amount_jpy_minor=jpy_minor,
                is_estimate=inp.is_estimate,
                note=inp.note,
            )
        )
        return breakdown
