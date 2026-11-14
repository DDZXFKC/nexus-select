"""Money helpers.

All amounts in the DB are stored as integers in the *minor unit* of their
currency (e.g. 1999 = 19.99 EUR, 250000 = 2500.00 JPY). Zero-decimal
currencies (JPY, KRW) use 1 minor = 1 major.

This module is the ONLY place that converts between float major units and
integer minor units - everywhere else stays in minor units to avoid float
drift across EUR / USD / GBP / JPY.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

# ISO 4217 decimal places. 0-decimal currencies are explicit.
_DECIMALS: dict[str, int] = {
    "JPY": 0, "KRW": 0, "VND": 0, "CLP": 0, "ISK": 0,
    "EUR": 2, "USD": 2, "GBP": 2, "CAD": 2, "AUD": 2, "CHF": 2, "CNY": 2,
}


def decimals(currency: str) -> int:
    return _DECIMALS.get(currency.upper(), 2)


def to_minor(amount_major: float, currency: str) -> int:
    """19.99 EUR -> 1999. JPY has 0 decimals so 2500 -> 2500."""
    d = decimals(currency)
    return int(round(amount_major * (10 ** d)))


def to_major(amount_minor: int, currency: str) -> float:
    d = decimals(currency)
    return amount_minor / (10 ** d)


def format_money(amount_minor: int, currency: str) -> str:
    """Human-readable: 1999 EUR -> '19.99 EUR', 250000 JPY -> '2,500 JPY'."""
    major = to_major(amount_minor, currency)
    d = decimals(currency)
    if d == 0:
        return f"{int(major):,} {currency}"
    return f"{major:,.{d}f} {currency}"


# FX -------------------------------------------------------------------------

@dataclass(frozen=True)
class FxRate:
    """1 unit of `currency` -> `rate` units of JPY."""
    currency: str
    rate: float
    as_of: str  # ISO date

    def to_jpy_minor(self, amount_minor: int) -> int:
        """Convert a foreign-minor amount to JPY-minor."""
        d_from = decimals(self.currency)
        d_to = decimals("JPY")
        # major -> JPY major -> JPY minor
        major = amount_minor / (10 ** d_from)
        jpy_major = major * self.rate
        return int(round(jpy_major * (10 ** d_to)))


class FxTable:
    """Simple in-memory FX table. In production, refresh from a public API
    (e.g. ECB daily reference rates) once per day and persist to a table."""

    def __init__(self, rates: Iterable[FxRate]):
        self._rates: dict[str, FxRate] = {r.currency.upper(): r for r in rates}

    def get(self, currency: str) -> FxRate:
        c = currency.upper()
        if c == "JPY":
            return FxRate("JPY", 1.0, "")
        if c not in self._rates:
            raise KeyError(f"No FX rate for {c}")
        return self._rates[c]

    def to_jpy_minor(self, amount_minor: int, currency: str) -> int:
        return self.get(currency).to_jpy_minor(amount_minor)
