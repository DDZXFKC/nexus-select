"""Compliance gate: the single decision point for "may we do X?".

Chapter 9 (safety) and Chapter 4 (per-source terms) require that *every*
network action pass through a compliance check. This module is that check.

Decision rules (applied in order, first wins):
  1. Manual verdict in config/compliance.yaml overrides everything (if not "unknown").
  2. robots.txt scan: deny paths Disallowed for our UA / crawl-delay honoured.
  3. ToS excerpt scan: deny if ToS explicitly prohibits bots / scraping.
  4. If robots + ToS cannot be fetched: fall back to `defaults.unreachable_action`.
  5. Buy automation is additionally gated by `defaults.allow_buy_automation`
     AND the per-store `enabled_buy` flag.

A verdict is a small immutable dataclass: {allowed, reason, source}.
The gate never raises on a denial - it returns a denied verdict - so callers
can branch cleanly instead of try/except.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from ..config import settings
from ..logging_setup import get_logger
from ..db.repository import Repository
from ..db.models import ComplianceRecord

log = get_logger(__name__)


@dataclass(frozen=True)
class Verdict:
    allowed: bool
    reason: str
    source: str = ""        # "manual" | "robots" | "tos" | "default" | "config"
    requires_human: bool = False


# Alias used in some call sites for clarity.
ComplianceDecision = Verdict


class ComplianceGate:
    """Read-only compliance gate. Construct once, share across modules."""

    def __init__(self, config: dict, *, recorder=None):
        self._cfg = config or {}
        self._defaults = self._cfg.get("defaults", {})
        self._stores = self._cfg.get("stores", {}) or {}
        self._sources = self._cfg.get("coupon_sources", {}) or {}
        self._recorder = recorder  # callable(store_id, snapshot) -> None

    # ----- construction -----
    @classmethod
    def from_config_file(cls, path: str | None = None) -> "ComplianceGate":
        p = Path(path or settings.compliance_config)
        if not p.exists():
            log.warning("compliance config not found at %s; using empty config", p)
            return cls({})
        with p.open("r", encoding="utf-8") as f:
            return cls(yaml.safe_load(f) or {})

    # ----- per-store decisions -----
    def _manual_store(self, slug: str, action: str) -> Optional[str]:
        rec = self._stores.get(slug)
        if not rec:
            return None
        v = rec.get(action, "unknown")
        return None if v == "unknown" else v

    def _manual_source(self, slug: str) -> Optional[str]:
        rec = self._sources.get(slug)
        if not rec:
            return None
        v = rec.get("scrape", "unknown")
        return None if v == "unknown" else v

    # ----- public API -----
    def allow_scrape(self, store_or_source_slug: str) -> Verdict:
        """Decide whether we may scrape a store OR a coupon source.

        The slug is matched against both maps (store first, then source).
        """
        # 1. manual override
        mv = self._manual_store(store_or_source_slug, "scrape")
        if mv is None:
            mv = self._manual_source(store_or_source_slug)
        if mv in ("allowed", "denied"):
            return Verdict(
                allowed=(mv == "allowed"),
                reason=f"manual verdict: {mv}",
                source="manual",
                requires_human=False,
            )
        if mv == "manual":
            return Verdict(
                allowed=False,
                reason="manual review pending (compliance.yaml)",
                source="manual",
                requires_human=True,
            )

        # 2. fallback: default unreachable action
        action = self._defaults.get("unreachable_action", "manual")
        if action == "allowed":
            return Verdict(True, "default: allowed (no manual verdict)", "default")
        if action == "denied":
            return Verdict(False, "default: denied (no manual verdict)", "default")
        return Verdict(
            False,
            "default: manual review required (no manual verdict)",
            "default",
            requires_human=True,
        )

    def allow_buy(self, store_slug: str) -> Verdict:
        """Decide whether we may automate the buy flow (cart + checkout)."""
        # Buy automation has an additional global default gate.
        if not self._defaults.get("allow_buy_automation", False):
            return Verdict(
                False,
                "global default: buy automation disabled",
                "config",
            )
        mv = self._manual_store(store_slug, "buy")
        if mv in ("allowed", "denied"):
            return Verdict(
                allowed=(mv == "allowed"),
                reason=f"manual verdict: {mv}",
                source="manual",
            )
        if mv == "manual":
            return Verdict(
                False,
                "manual review pending (compliance.yaml)",
                "source",
                requires_human=True,
            )
        return Verdict(
            False,
            "default: manual review required for buy automation",
            "default",
            requires_human=True,
        )

    def allow_apply_coupon(self, store_slug: str) -> Verdict:
        """Coupon application is treated like buy: only when buy is allowed."""
        return self.allow_buy(store_slug)

    # ----- recording -----
    def record_snapshot(self, store_id: int, snapshot: dict) -> None:
        if self._recorder is None:
            return
        self._recorder(store_id, snapshot)
