"""Chapter 11 tests: cost calculation + profit + cheapest-source selection."""
from __future__ import annotations

from ahc.cost.models import CostInput
from ahc.cost.calculator import CostCalculator
from ahc.cost.profit import compute_profit, pick_best_plan, PlanCandidate
from ahc.db.models import CostType
from ahc.cost.models import CostBreakdown, CostLine


def _bd(lines):
    """Build a CostBreakdown from a list of CostLine."""
    return CostBreakdown(lines=lines)


def _line(cost_type, jpy_minor, is_estimate=False):
    return CostLine(
        cost_type=cost_type, amount_minor=jpy_minor, currency="JPY",
        fx_rate=1.0, amount_jpy_minor=jpy_minor, is_estimate=is_estimate,
    )


def test_calculator_converts_eur_to_jpy(fx_table):
    calc = CostCalculator(fx_table)
    bd = calc.calculate([
        CostInput(CostType.ITEM_PRICE, amount_minor=10000, currency="EUR"),  # 100 EUR
    ])
    line = bd.lines[0]
    assert line.fx_rate == 160.0
    # 100 EUR * 160 JPY/EUR = 16000 JPY. JPY has 0 decimals so minor == major.
    assert line.amount_jpy_minor == 16_000
    assert bd.confirmed_total_jpy_minor == 16_000


def test_calculator_excludes_estimates_from_confirmed(fx_table):
    calc = CostCalculator(fx_table)
    bd = calc.calculate([
        CostInput(CostType.ITEM_PRICE, amount_minor=10000, currency="EUR"),
        CostInput(CostType.CASHBACK, amount_minor=500, currency="EUR", is_estimate=True),
    ])
    assert bd.confirmed_total_jpy_minor == 16_000
    # 5 EUR * 160 = 800 JPY
    assert bd.estimated_total_jpy_minor == 800
    assert bd.has_estimates() is True


def test_profit_min_profit_passes_when_no_estimates():
    sale = 2_000_000  # 20,000 JPY major -> 2,000,000 minor
    bd = _bd([_line(CostType.ITEM_PRICE, 1_500_000)])
    r = compute_profit(sale, bd, min_profit_jpy_minor=200_000)
    assert r.meets_min_profit is True
    assert r.has_estimates is False
    assert r.blocked_reason is None
    assert r.confirmed_profit_jpy_minor == 500_000


def test_profit_below_min_profit_blocked():
    sale = 2_000_000
    bd = _bd([_line(CostType.ITEM_PRICE, 1_900_000)])
    r = compute_profit(sale, bd, min_profit_jpy_minor=200_000)
    assert r.meets_min_profit is False
    assert r.blocked_reason == "below_min_profit"


def test_profit_with_estimates_blocked_even_if_above_min():
    """Chapter 7: unverified coupons / cashback never count as confirmed profit."""
    sale = 2_000_000
    bd = _bd([
        _line(CostType.ITEM_PRICE, 1_500_000),
        _line(CostType.CASHBACK, 800_000, is_estimate=True),
    ])
    r = compute_profit(sale, bd, min_profit_jpy_minor=200_000)
    # Confirmed profit is 500k which passes min, but estimates block selection.
    assert r.meets_min_profit is True
    assert r.has_estimates is True
    assert r.blocked_reason == "has_estimates"


# --- 最安仕入れ先の選択 ------------------------------------------------------

def _candidate(slug, item_jpy, est_jpy=0, min_profit=200_000):
    sale = 2_000_000
    lines = [_line(CostType.ITEM_PRICE, item_jpy)]
    if est_jpy:
        lines.append(_line(CostType.CASHBACK, est_jpy, is_estimate=True))
    bd = _bd(lines)
    profit = compute_profit(sale, bd, min_profit_jpy_minor=min_profit)
    return PlanCandidate(store_slug=slug, coupon_code=None, breakdown=bd, profit=profit)


def test_pick_best_plan_selects_lowest_cost():
    c_cheap = _candidate("bstn", 1_500_000)
    c_mid = _candidate("kith", 1_700_000)
    c_exp = _candidate("ssense", 1_900_000)
    best = pick_best_plan([c_exp, c_mid, c_cheap])
    assert best is not None
    assert best.store_slug == "bstn"


def test_pick_best_plan_rejects_estimates_by_default():
    c_with_estimate = _candidate("bstn", 1_500_000, est_jpy=800_000)
    c_clean = _candidate("kith", 1_700_000)
    best = pick_best_plan([c_with_estimate, c_clean])
    assert best is not None
    assert best.store_slug == "kith"


def test_pick_best_plan_all_below_min_profit_returns_none():
    c1 = _candidate("bstn", 1_950_000)  # profit 50k < 200k min
    c2 = _candidate("kith", 1_980_000)
    best = pick_best_plan([c1, c2])
    assert best is None
