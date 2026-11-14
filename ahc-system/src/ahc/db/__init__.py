"""Database package.

Public API:
    from ahc.db import Base, SessionLocal, engine, init_db
    from ahc.db import Product, Store, Coupon, Order, ...
    from ahc.db.repository import Repository
"""
from .base import Base
from .session import SessionLocal, engine, init_db
from .models import (
    Store,
    Product,
    StoreProduct,      # store x product (sku / url / price / stock)
    Coupon,
    CouponSource,      # where a coupon was found
    CouponAttempt,     # every apply attempt (incl. failed) - ch.5(7), ch.9
    Order,
    OrderItem,
    PurchasePlan,      # chosen source + cost breakdown for an order item
    PurchaseRecord,    # outcome of a buy attempt
    CostComponent,     # one row per (plan, cost-type)
    ComplianceRecord,  # per-store robots/tos snapshot
)

__all__ = [
    "Base",
    "SessionLocal",
    "engine",
    "init_db",
    "Store",
    "Product",
    "StoreProduct",
    "Coupon",
    "CouponSource",
    "CouponAttempt",
    "Order",
    "OrderItem",
    "PurchasePlan",
    "PurchaseRecord",
    "CostComponent",
    "ComplianceRecord",
]
