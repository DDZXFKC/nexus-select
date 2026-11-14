"""Chapter 11 tests: order email parsing + order manager integration."""
from __future__ import annotations

import datetime as dt

from ahc.orders import parse_email, parsers
from ahc.orders.manager import OrderManager
from ahc.orders.models import ParsedOrder, ParsedOrderItem
from ahc.db.models import Order, OrderItem, OrderSource, OrderStatus


SAMPLE_BUYMA = b"""From: notify@buyma.com
Subject: [BUYMA] Order confirmed #BM20261114-12345
Date: Sat, 14 Nov 2026 10:00:00 +0000

Dear Seller,

You have received a new order.

Order ID: BM20261114-12345
Buyer: Taro Yamada
Ship to: Japan

Item 1:
  Brand: Nike
  Model: Air Max 90
  Colorway: White/Black
  Size: 27.0
  Qty: 1
  Price: JPY 35,000

Thank you.
"""


def test_parsers_registry_has_both():
    assert "buyma" in parsers
    assert "after_hours" in parsers


def test_parse_email_extracts_buyma_order():
    parsed = parse_email(SAMPLE_BUYMA)
    assert parsed is not None
    assert parsed.source == "buyma"
    assert parsed.external_order_id == "BM20261114-12345"
    assert parsed.buyer_name == "Taro Yamada"
    assert len(parsed.items) >= 1
    item = parsed.items[0]
    assert item.requested_brand == "Nike"
    assert item.requested_model == "Air Max 90"
    assert item.requested_size == "27.0"
    assert item.quantity == 1


def test_parse_email_returns_none_when_no_order_pattern():
    """parse_email parses by content patterns, not sender. An email with no
    recognisable order-id pattern returns None.

    Sender filtering is the ImapOrderFetcher's job (settings.order_senders),
    not the parser's.
    """
    other = b"""From: random@example.com
Subject: Hello world

Just a friendly hello - no order here.
"""
    assert parse_email(other) is None


def test_order_manager_ingest_idempotent(session):
    mgr = OrderManager(session=session)
    parsed = ParsedOrder(
        source="buyma",
        external_order_id="BM-TEST-1",
        buyer_name="Test Buyer",
        buyer_email="buyer@example.com",
        ship_country="JP",
        items=[ParsedOrderItem(
            requested_brand="Nike", requested_model="Air Max 90",
            requested_size="27.0", quantity=1,
            sale_price_minor=3500000, sale_currency="JPY",
        )],
        placed_at=dt.datetime(2026, 11, 14, 10, 0, 0),
    )
    o1 = mgr.ingest(parsed)
    assert o1.id is not None
    # Ingest again - must not create a duplicate.
    o2 = mgr.ingest(parsed)
    assert o2.id == o1.id
    # And no duplicate items.
    items = session.query(OrderItem).filter_by(order_id=o1.id).all()
    assert len(items) == 1


def test_order_manager_list_pending_and_mark_status(session):
    mgr = OrderManager(session=session)
    parsed = ParsedOrder(
        source="buyma", external_order_id="BM-PENDING",
        buyer_name=None, items=[], placed_at=None,
    )
    o = mgr.ingest(parsed)
    assert o.status == OrderStatus.RECEIVED.value

    pending = mgr.list_pending()
    assert any(p.id == o.id for p in pending)

    mgr.mark_status(o.id, OrderStatus.PLANNED)
    session.commit()
    session.refresh(o)
    assert o.status == OrderStatus.PLANNED.value


def test_order_manager_to_manual_sets_status_and_reason(session):
    mgr = OrderManager(session=session)
    parsed = ParsedOrder(
        source="buyma", external_order_id="BM-MANUAL",
        buyer_name=None, items=[], placed_at=None,
    )
    o = mgr.ingest(parsed)
    mgr.to_manual(o.id, "compliance denied for all stores")
    session.commit()
    session.refresh(o)
    assert o.status == OrderStatus.MANUAL.value
    assert "MANUAL:" in (o.raw_email_path or "")
