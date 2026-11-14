"""Coupon applier (Chapter 5(7) + Chapter 9).

Applies coupon codes to a live cart through the store adapter and records
*every* attempt (success and failure) to the ``coupon_attempts`` table so a
known-bad coupon is never silently retried against the same store.

Rules (Chapter 9 safety):
  - One pass over the code list. A code that fails is recorded and skipped;
    it is NOT retried within this run.
  - Duplicate codes in the list are de-duplicated (a code is tried at most once
    per run).
  - When the applied coupon's ``combinable`` flag is ``False`` (the common
    case), we STOP after the first successful apply. We only continue to the
    next code when the successfully-applied coupon is explicitly combinable.
  - If the coupon record cannot be found (no session, or unknown code),
    combinable defaults to ``False`` (safe) and no DB row is written when the
    required ``coupon_id`` / ``store_id`` are missing.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import Coupon, CouponAttempt
from ..logging_setup import get_logger
from ..stores.base import (
    AbstractStoreAdapter,
    CartState,
    CouponApplyResult,
)

log = get_logger(__name__)


class CouponApplier:
    """Apply a list of coupon codes to a cart via a store adapter."""

    def __init__(self, adapter: AbstractStoreAdapter):
        self._adapter = adapter

    def try_coupons(
        self,
        codes: list[str],
        current_cart: CartState,
        *,
        session: Optional[Session] = None,
        store_id: Optional[int] = None,
        plan_id: Optional[int] = None,
    ) -> tuple[CartState, list[CouponApplyResult]]:
        """Try each coupon code in order against ``current_cart``.

        Args:
            codes: coupon codes to attempt, in priority order.
            current_cart: the cart snapshot before any coupon is applied.
            session: optional DB session. When provided (along with
                ``store_id``), every attempt is persisted to
                ``coupon_attempts`` and the coupon's ``combinable`` flag is
                read from the DB.
            store_id: store the cart belongs to. Needed to write attempts and
                to scope the coupon lookup.
            plan_id: purchase plan the attempt belongs to (optional FK).

        Returns:
            ``(final_cart, attempts)`` where ``attempts`` is the list of every
            :class:`CouponApplyResult` (success and failure), in order.
        """
        cart = current_cart
        attempts: list[CouponApplyResult] = []
        seen: set[str] = set()

        for code in codes:
            if not code:
                continue
            key = code.strip()
            if key in seen:
                log.warning(
                    "coupon.try: code %r already attempted this run; skipping",
                    key,
                )
                continue
            seen.add(key)

            coupon_rec = self._lookup_coupon(session, key, store_id)
            combinable = bool(coupon_rec.combinable) if coupon_rec else False
            coupon_id = coupon_rec.id if coupon_rec else None

            result = self._apply_one(key)
            attempts.append(result)

            self._record_attempt(
                session=session,
                coupon_id=coupon_id,
                store_id=store_id,
                plan_id=plan_id,
                result=result,
            )

            if result.applied:
                # Re-read the cart so the new subtotal/discount propagates to
                # the next iteration and to the caller.
                cart = self._adapter.read_cart()
                if not combinable:
                    log.info(
                        "coupon.try: %r applied (non-combinable); "
                        "stopping after first success",
                        key,
                    )
                    break
                log.info(
                    "coupon.try: %r applied (combinable); continuing",
                    key,
                )
            else:
                log.info(
                    "coupon.try: %r not applied (%s); moving on",
                    key,
                    result.error_message or "no reason",
                )

        return cart, attempts

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _apply_one(self, code: str) -> CouponApplyResult:
        """Apply one code via the adapter, normalising exceptions into a
        failure result so a thrown error never aborts the whole run."""
        try:
            return self._adapter.apply_coupon(code)
        except NotImplementedError:
            return CouponApplyResult(
                coupon_code=code,
                applied=False,
                applied_discount_minor=None,
                currency=self._adapter.currency,
                error_message=f"store {self._adapter.slug!r}: apply_coupon not implemented",
            )
        except Exception as e:  # pragma: no cover - depends on live adapter
            log.error("coupon.try: adapter raised for %r: %s", code, e)
            return CouponApplyResult(
                coupon_code=code,
                applied=False,
                applied_discount_minor=None,
                currency=self._adapter.currency,
                error_message=f"adapter error: {e}",
                raw_response_excerpt=str(e)[:500],
            )

    @staticmethod
    def _lookup_coupon(
        session: Optional[Session],
        code: str,
        store_id: Optional[int],
    ) -> Optional[Coupon]:
        """Find the Coupon row for ``code`` scoped to ``store_id`` when both
        are available; fall back to a code-only lookup; return None when no
        session is available."""
        if session is None:
            return None
        stmt = select(Coupon).where(Coupon.code == code)
        if store_id is not None:
            stmt = stmt.where(Coupon.store_id == store_id)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def _record_attempt(
        *,
        session: Optional[Session],
        coupon_id: Optional[int],
        store_id: Optional[int],
        plan_id: Optional[int],
        result: CouponApplyResult,
    ) -> None:
        """Persist one attempt to ``coupon_attempts``.

        Skipped silently when there is no session or when the NOT NULL
        ``coupon_id`` / ``store_id`` are unavailable (e.g. the code is not in
        the DB). The in-memory ``CouponApplyResult`` is always returned to the
        caller regardless.
        """
        if session is None or coupon_id is None or store_id is None:
            return
        # status vocabulary per the model comment: valid / invalid / error
        if result.applied:
            status = "valid"
        elif result.error_message and result.error_message.startswith("adapter error"):
            status = "error"
        else:
            status = "invalid"
        attempt = CouponAttempt(
            coupon_id=coupon_id,
            store_id=store_id,
            purchase_plan_id=plan_id,
            attempted_at=datetime.now(timezone.utc),
            applied_discount_minor=result.applied_discount_minor,
            currency=result.currency,
            status=status,
            error_message=result.error_message,
            raw_response=result.raw_response_excerpt,
        )
        session.add(attempt)
        try:
            session.flush()
        except Exception as e:  # pragma: no cover - DB-specific
            log.error("coupon.record: failed to persist attempt for %r: %s",
                      result.coupon_code, e)
            session.rollback()
