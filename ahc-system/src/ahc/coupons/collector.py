"""Coupon collector: orchestrates source fetch -> dedup -> validate -> persist.

The collector is the entry point of the coupon collection module. Given a list
of ``AbstractCouponSource`` adapters it:

  1. Calls ``source.fetch()`` for each, inside try/except. One source failing
     must not stop the others (Chapter 10: independent work is isolated).
  2. Deduplicates within the source's batch.
  3. Converts each surviving raw coupon to a ``CouponRecord``, runs the
     collection-time validator (expiry).
  4. Persists each to the DB via ``Repository(Coupon).upsert_by(...)`` keyed on
     ``(store_id, code, source_id)`` — the same triple as the unique
     constraint on the ``coupons`` table — so re-running is idempotent.
  5. Records the per-coupon ``source_url`` and ``last_seen_at``.

``store_id`` is resolved from ``store_slug`` through the ``Store`` table
(None for multi-store coupons). ``source_id`` is resolved (and lazily
upserted) from the source's slug through the ``CouponSource`` table.

The collector never makes network calls itself — sources do that, and only
inside ``fetch()``. Construction is side-effect free.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any, Optional

from ..db.models import Coupon, CouponSource, Store
from ..db.repository import Repository
from ..db.session import SessionLocal
from ..logging_setup import get_logger
from .base import AbstractCouponSource
from .dedup import Deduplicator
from .validator import CouponValidator

log = get_logger(__name__)


class CouponCollector:
    """Run all configured coupon sources and persist the results."""

    def __init__(
        self,
        sources: list[AbstractCouponSource],
        *,
        dedup: Optional[Deduplicator] = None,
        validator: Optional[CouponValidator] = None,
        session=None,
    ):
        self._sources = list(sources)
        self._dedup = dedup or Deduplicator()
        self._validator = validator or CouponValidator()
        # Optional shared session. Repository opens its own session_scope when
        # none is supplied, so this is mainly a hook for tests / shared txns.
        self._session = session

    # ----- public API -----
    def run(self) -> dict:
        """Fetch, dedup, validate and persist coupons from every source.

        Returns a summary dict::

            {"sources_run": N, "coupons_upserted": M, "errors": [...]}
        """
        summary: dict[str, Any] = {
            "sources_run": 0,
            "coupons_upserted": 0,
            "errors": [],
        }

        for source in self._sources:
            summary["sources_run"] += 1
            slug = getattr(source, "slug", "") or ""

            # --- fetch (Chapter 10: isolate each source) ---
            try:
                raws = source.fetch()
            except Exception as exc:  # noqa: BLE001 - any source error is non-fatal
                log.warning("source %r fetch failed: %s", slug, exc)
                summary["errors"].append(
                    {"source": slug, "phase": "fetch", "error": str(exc)}
                )
                continue

            if not raws:
                log.info("source %r returned no coupons", slug)
                continue

            # --- process + persist ---
            try:
                deduped = self._dedup.dedup(raws)
                source_id = self._ensure_source_row(source)
                for raw in deduped:
                    record = self._validator.validate(self._dedup.to_record(raw))
                    self._persist(record, source_id)
                    summary["coupons_upserted"] += 1
                log.info(
                    "source %r: %d raw -> %d deduped -> persisted",
                    slug,
                    len(raws),
                    len(deduped),
                )
            except Exception as exc:  # noqa: BLE001
                log.warning("source %r processing failed: %s", slug, exc)
                summary["errors"].append(
                    {"source": slug, "phase": "process", "error": str(exc)}
                )

        return summary

    # ----- persistence helpers -----
    def _ensure_source_row(self, source: AbstractCouponSource) -> int:
        """Upsert the CouponSource row for ``source`` and return its id.

        The source's ``cfg`` dict mirrors a row of ``coupon_sources.yaml``;
        we use it to fill the columns so a freshly initialised DB (no
        CouponSource rows loaded yet) still works.
        """
        cfg = getattr(source, "cfg", {}) or {}
        slug = getattr(source, "slug", "") or ""
        repo = Repository(CouponSource, session=self._session)
        obj = repo.upsert_by(
            {"slug": slug},
            {
                "name": cfg.get("name") or slug,
                "url": cfg.get("url") or getattr(source, "url", "") or "",
                "country": cfg.get("country") or getattr(source, "country", "") or "US",
                "source_type": cfg.get("source_type", "aggregator"),
                "enabled": bool(cfg.get("enabled", False)),
                "adapter_class": cfg.get("adapter_class"),
                "notes": cfg.get("notes"),
            },
        )
        return obj.id

    def _resolve_store_id(self, store_slug: Optional[str]) -> Optional[int]:
        """Resolve a store_slug to its DB id; None for multi-store coupons."""
        if not store_slug:
            return None
        store = Repository(Store, session=self._session).get_by(slug=store_slug)
        if store is None:
            log.warning("store slug %r not found in DB; coupon stored with store_id=NULL", store_slug)
            return None
        return store.id

    def _persist(self, record, source_id: int) -> None:
        """Upsert one coupon keyed on (store_id, code, source_id)."""
        store_id = self._resolve_store_id(record.store_slug)

        # Date columns on the ORM are mapped as datetime but stored as DATE;
        # coerce so SQLite / Postgres both accept the value.
        last_seen = record.seen_at
        if isinstance(last_seen, datetime):
            last_seen = last_seen.date()
        last_verified = record.last_verified_at
        if isinstance(last_verified, datetime):
            last_verified = last_verified.date()

        filters = {
            "store_id": store_id,
            "code": record.code,
            "source_id": source_id,
        }
        defaults = {
            "title": record.title,
            "description": record.description,
            "discount_type": record.discount_type,
            "discount_value": record.discount_value,
            "discount_currency": record.discount_currency,
            "min_spend_minor": record.min_spend_minor,
            "min_spend_currency": record.min_spend_currency,
            "eligible_brands": json.dumps(record.eligible_brands) if record.eligible_brands else None,
            "excluded_brands": json.dumps(record.excluded_brands) if record.excluded_brands else None,
            "eligible_categories": json.dumps(record.eligible_categories) if record.eligible_categories else None,
            "first_order_only": record.first_order_only,
            "combinable": record.combinable,
            "ship_region": record.ship_region,
            "valid_from": record.valid_from,
            "valid_until": record.valid_until,
            "source_url": record.source_url,
            "last_seen_at": last_seen or date.today(),
            "last_verified_at": last_verified,
            "status": record.status,
        }
        Repository(Coupon, session=self._session).upsert_by(filters, defaults)
