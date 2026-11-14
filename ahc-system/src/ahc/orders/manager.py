"""Persist parsed orders into the DB and move them through the lifecycle.

``OrderManager`` is the bridge between the in-memory ``ParsedOrder``
(produced by a parser) and the ORM ``Order`` / ``OrderItem`` rows. The
natural key for upsert is ``(source, external_order_id)`` - the same pair
that the ``orders`` table enforces via its unique constraint - so a given
platform order is ingested at most once even if its email is fetched twice.

The ``orders.raw_email_path`` column is intentionally overloaded here as a
notes column: it normally holds the on-disk path of the source ``.eml``,
and ``to_manual`` writes a ``MANUAL:<reason>`` note into it (preserving any
prior path) so the handoff reason survives alongside the audit trail.
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import Order, OrderItem, OrderStatus
from ..db.session import SessionLocal
from ..logging_setup import get_logger
from .models import ParsedOrder

log = get_logger(__name__)


class OrderManager:
    """Upsert parsed orders and drive their status transitions."""

    def __init__(self, session: Optional[Session] = None) -> None:
        # If no session is passed we open (and own) a fresh SessionLocal per
        # call, committing / closing it ourselves. If one is passed, the
        # caller owns its transaction lifecycle and we only mutate objects.
        self._session = session

    # ------------------------------------------------------------------
    # session handling
    # ------------------------------------------------------------------
    def _get_session(self) -> Session:
        if self._session is not None:
            return self._session
        return SessionLocal()

    def _owns_session(self) -> bool:
        return self._session is None

    # ------------------------------------------------------------------
    # write
    # ------------------------------------------------------------------
    def ingest(self, parsed: ParsedOrder) -> Order:
        """Upsert by ``(source, external_order_id)``.

        On a new order: create the ``orders`` row plus one ``order_items``
        row per ``ParsedOrderItem``. On an existing order: refresh mutable
        fields (filling blanks the parser may have resolved on a re-fetch)
        but never duplicate items.
        """
        s = self._get_session()
        own = self._owns_session()
        try:
            existing = s.execute(
                select(Order).filter_by(
                    source=parsed.source,
                    external_order_id=parsed.external_order_id,
                )
            ).scalar_one_or_none()

            if existing is None:
                order = Order(
                    source=parsed.source,
                    external_order_id=parsed.external_order_id,
                    buyer_name=parsed.buyer_name,
                    buyer_email=parsed.buyer_email,
                    ship_country=parsed.ship_country,
                    ship_address=parsed.ship_address,
                    sale_price_minor=parsed.sale_price_minor,
                    sale_currency=parsed.sale_currency,
                    placed_at=parsed.placed_at,
                    received_at=date.today(),
                    raw_email_path=parsed.raw_email_path,
                    status=OrderStatus.RECEIVED.value,
                )
                s.add(order)
                s.flush()  # populate order.id

                for item in parsed.items or []:
                    s.add(
                        OrderItem(
                            order_id=order.id,
                            requested_brand=item.requested_brand,
                            requested_model=item.requested_model,
                            requested_colorway=item.requested_colorway,
                            requested_size=item.requested_size,
                            quantity=item.quantity,
                            sale_price_minor=item.sale_price_minor,
                            sale_currency=item.sale_currency,
                        )
                    )
                s.flush()
                if own:
                    s.commit()
                s.refresh(order)
                log.info(
                    "Ingested new order %s/%s id=%d (%d item(s))",
                    parsed.source,
                    parsed.external_order_id,
                    order.id,
                    len(parsed.items or []),
                )
                return order

            # Existing order: refresh blanks only, do not duplicate items.
            if parsed.buyer_name and not existing.buyer_name:
                existing.buyer_name = parsed.buyer_name
            if parsed.buyer_email and not existing.buyer_email:
                existing.buyer_email = parsed.buyer_email
            if parsed.ship_country and not existing.ship_country:
                existing.ship_country = parsed.ship_country
            if parsed.ship_address and not existing.ship_address:
                existing.ship_address = parsed.ship_address
            if (
                parsed.sale_price_minor is not None
                and existing.sale_price_minor is None
            ):
                existing.sale_price_minor = parsed.sale_price_minor
            if parsed.sale_currency and not existing.sale_currency:
                existing.sale_currency = parsed.sale_currency
            if parsed.placed_at and not existing.placed_at:
                existing.placed_at = parsed.placed_at
            if parsed.raw_email_path and not existing.raw_email_path:
                existing.raw_email_path = parsed.raw_email_path
            if own:
                s.commit()
            s.refresh(existing)
            log.info(
                "Refreshed existing order %s/%s id=%d",
                parsed.source,
                parsed.external_order_id,
                existing.id,
            )
            return existing
        except Exception:
            if own:
                s.rollback()
            raise
        finally:
            if own:
                s.close()

    # ------------------------------------------------------------------
    # read
    # ------------------------------------------------------------------
    def list_pending(self) -> List[Order]:
        """Return orders still awaiting fulfilment work.

        "Pending" = ``received`` (just ingested, no plan yet) or ``planned``
        (a purchase plan exists but the buy has not started).
        """
        s = self._get_session()
        own = self._owns_session()
        try:
            stmt = select(Order).where(
                Order.status.in_(
                    [OrderStatus.RECEIVED.value, OrderStatus.PLANNED.value]
                )
            )
            rows = list(s.execute(stmt).scalars().all())
            if own:
                for r in rows:
                    s.expunge(r)
            return rows
        finally:
            if own:
                s.close()

    # ------------------------------------------------------------------
    # status transitions
    # ------------------------------------------------------------------
    def mark_status(self, order_id: int, status: OrderStatus) -> None:
        """Set ``orders.status`` to ``status`` for the given primary key."""
        s = self._get_session()
        own = self._owns_session()
        try:
            order = s.get(Order, order_id)
            if order is None:
                raise ValueError(f"Order id={order_id} not found")
            order.status = (
                status.value if isinstance(status, OrderStatus) else str(status)
            )
            if own:
                s.commit()
            log.info("Order %d -> status=%s", order_id, order.status)
        except Exception:
            if own:
                s.rollback()
            raise
        finally:
            if own:
                s.close()

    def to_manual(self, order_id: int, reason: str) -> None:
        """Flag an order for human handoff.

        Sets ``status = manual`` and writes ``MANUAL:<reason>`` into the
        overloaded ``raw_email_path`` notes column. If a real email path was
        already stored there, it is preserved after a ``|`` separator so the
        audit trail (where the email lives on disk) is not lost.
        """
        s = self._get_session()
        own = self._owns_session()
        try:
            order = s.get(Order, order_id)
            if order is None:
                raise ValueError(f"Order id={order_id} not found")
            note = f"MANUAL:{reason}"
            existing = order.raw_email_path or ""
            if existing and not existing.startswith("MANUAL:"):
                order.raw_email_path = f"{note}|{existing}"
            else:
                order.raw_email_path = note
            order.status = OrderStatus.MANUAL.value
            if own:
                s.commit()
            log.info("Order %d -> manual handoff: %s", order_id, reason)
        except Exception:
            if own:
                s.rollback()
            raise
        finally:
            if own:
                s.close()
