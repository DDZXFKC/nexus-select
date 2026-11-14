"""SQLAlchemy models for AHC.

Schema overview (Chapter 7 cost model + Chapter 12 deliverables):

  stores              - retailer master + compliance snapshot link
  products            - canonical product (existing collection DB mirror)
  store_products      - per-store SKU / URL / price / stock
  coupon_sources      - where coupons come from (RetailMeNot, mydealz, ...)
  coupons             - coupon master, dedup, validity
  coupon_attempts     - every apply attempt (incl. failed) - Ch.5(7), Ch.9
  orders              - BUYMA / After Hours Club order
  order_items         - one row per (order, product, size, qty)
  purchase_plans      - chosen source + cost breakdown per order item
  cost_components     - one row per (plan, cost type) - Ch.7
  purchase_records    - outcome of a buy attempt (idempotency key Ch.9)
  compliance_records  - per-store robots / ToS snapshot

All amounts are stored as integers in the *minor unit* of their currency
(cents / pence / yen) plus an explicit currency code. This avoids float
rounding bugs across EUR / USD / GBP / JPY.
"""
from __future__ import annotations

import enum
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, PkMixin, TimestampMixin


# ---------------------------------------------------------------------------
# Lookups / enums
# ---------------------------------------------------------------------------

class Currency(str, enum.Enum):
    JPY = "JPY"
    EUR = "EUR"
    USD = "USD"
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"


class CostType(str, enum.Enum):
    """Chapter 7 - every cost component tracked individually."""
    ITEM_PRICE = "item_price"
    COUPON_DISCOUNT = "coupon_discount"
    LOCAL_TAX = "local_tax"
    LOCAL_SHIPPING = "local_shipping"
    INTL_SHIPPING = "intl_shipping"
    CUSTOMS_DUTY = "customs_duty"
    IMPORT_TAX = "import_tax"
    PROCUREMENT_FEE = "procurement_fee"
    DISPATCH_FEE = "dispatch_fee"
    FX_FEE = "fx_fee"
    PLATFORM_FEE = "platform_fee"
    CASHBACK = "cashback"          # future / unverified - always an estimate (Ch.7)
    OTHER = "other"


class OrderSource(str, enum.Enum):
    BUYMA = "buyma"
    AFTER_HOURS = "after_hours"


class OrderStatus(str, enum.Enum):
    RECEIVED = "received"
    PLANNED = "planned"
    BUYING = "buying"
    BOUGHT = "bought"
    FAILED = "failed"
    CANCELLED = "cancelled"
    MANUAL = "manual"  # Python cannot process -> human handoff (Ch.6)


class PurchaseStatus(str, enum.Enum):
    PLANNED = "planned"
    CART_PREPARED = "cart_prepared"  # Ch.4 buy level "cart preparation"
    AWAITING_APPROVAL = "awaiting_approval"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    UNKNOWN = "unknown"  # Ch.9: do NOT auto-rebuy when result is unknown
    FAILED = "failed"


class ComplianceVerdict(str, enum.Enum):
    """Decision returned by ahc.compliance for a given action."""
    ALLOWED = "allowed"
    DENIED = "denied"
    MANUAL = "manual"
    UNKNOWN = "unknown"


class CouponStatus(str, enum.Enum):
    UNVERIFIED = "unverified"
    VERIFIED_VALID = "verified_valid"
    VERIFIED_INVALID = "verified_invalid"
    EXPIRED = "expired"
    BLACKLISTED = "blacklisted"


# ---------------------------------------------------------------------------
# Stores
# ---------------------------------------------------------------------------

class Store(Base, PkMixin, TimestampMixin):
    __tablename__ = "stores"
    __table_args__ = (UniqueConstraint("slug", name="uq_stores_slug"),)

    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    base_url: Mapped[str] = mapped_column(String(255), nullable=False)
    ec_platform: Mapped[str] = mapped_column(
        String(32), nullable=False, default="generic"
    )  # shopify / magento / woocommerce / generic
    adapter_class: Mapped[Optional[str]] = mapped_column(String(128))
    enabled_scrape: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    enabled_buy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    products: Mapped[list["StoreProduct"]] = relationship(
        back_populates="store", cascade="all, delete-orphan"
    )
    coupons: Mapped[list["Coupon"]] = relationship(back_populates="store")


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

class Product(Base, PkMixin, TimestampMixin):
    """Canonical product (mirror of the existing collection DB).

    Keep the existing system's primary key in `external_id` so we can
    join without rewriting the other system.
    """
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("external_source", "external_id", name="uq_products_ext"),
    )

    external_source: Mapped[str] = mapped_column(String(32), nullable=False, default="existing")
    external_id: Mapped[str] = mapped_column(String(64), nullable=False)
    brand: Mapped[Optional[str]] = mapped_column(String(128))
    model: Mapped[Optional[str]] = mapped_column(String(128))  # silhouette
    colorway: Mapped[Optional[str]] = mapped_column(String(255))
    sku: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    gtin: Mapped[Optional[str]] = mapped_column(String(32))  # EAN/UPC for cross-store match
    gender: Mapped[Optional[str]] = mapped_column(String(16))
    release_date: Mapped[Optional[date]] = mapped_column(Date)
    image_url: Mapped[Optional[str]] = mapped_column(String(512))

    store_products: Mapped[list["StoreProduct"]] = relationship(
        back_populates="product"
    )


class StoreProduct(Base, PkMixin, TimestampMixin):
    """Per-store listing of a canonical product."""
    __tablename__ = "store_products"
    __table_args__ = (
        UniqueConstraint("store_id", "store_sku", name="uq_sp_store_sku"),
        Index("ix_sp_product", "product_id"),
    )

    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    store_sku: Mapped[str] = mapped_column(String(128), nullable=False)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    price_minor: Mapped[int] = mapped_column(Integer, nullable=False)  # cents etc.
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    stock_status: Mapped[str] = mapped_column(String(32), default="unknown")
    sizes_available: Mapped[Optional[str]] = mapped_column(Text)  # JSON array
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(
        Date, nullable=True
    )

    store: Mapped["Store"] = relationship(back_populates="products")
    product: Mapped["Product"] = relationship(back_populates="store_products")


# ---------------------------------------------------------------------------
# Coupons
# ---------------------------------------------------------------------------

class CouponSource(Base, PkMixin, TimestampMixin):
    __tablename__ = "coupon_sources"
    __table_args__ = (UniqueConstraint("slug", name="uq_cs_slug"),)

    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False, default="US")
    source_type: Mapped[str] = mapped_column(String(32), default="aggregator")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    adapter_class: Mapped[Optional[str]] = mapped_column(String(128))
    notes: Mapped[Optional[str]] = mapped_column(Text)


class Coupon(Base, PkMixin, TimestampMixin):
    __tablename__ = "coupons"
    __table_args__ = (
        UniqueConstraint(
            "store_id", "code", "source_id", name="uq_coupon_store_code_source"
        ),
        Index("ix_coupon_status", "status"),
        Index("ix_coupon_expiry", "valid_until"),
    )

    store_id: Mapped[Optional[int]] = mapped_column(ForeignKey("stores.id"))
    source_id: Mapped[int] = mapped_column(
        ForeignKey("coupon_sources.id"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Discount representation
    discount_type: Mapped[str] = mapped_column(String(16), nullable=False)
    # one of: percent / fixed_amount / free_shipping / cashback / bundle / gift
    discount_value: Mapped[Optional[float]] = mapped_column(Float)  # percent or amount
    discount_currency: Mapped[Optional[str]] = mapped_column(String(3))

    # Restrictions (Chapter 4 collection items)
    min_spend_minor: Mapped[Optional[int]] = mapped_column(Integer)
    min_spend_currency: Mapped[Optional[str]] = mapped_column(String(3))
    eligible_brands: Mapped[Optional[str]] = mapped_column(Text)  # JSON list
    excluded_brands: Mapped[Optional[str]] = mapped_column(Text)
    eligible_categories: Mapped[Optional[str]] = mapped_column(Text)
    first_order_only: Mapped[bool] = mapped_column(Boolean, default=False)
    combinable: Mapped[bool] = mapped_column(Boolean, default=False)
    ship_region: Mapped[Optional[str]] = mapped_column(String(64))

    valid_from: Mapped[Optional[date]] = mapped_column(Date)
    valid_until: Mapped[Optional[date]] = mapped_column(Date, index=True)

    source_url: Mapped[str] = mapped_column(String(512), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(Date, nullable=False)
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=CouponStatus.UNVERIFIED.value, nullable=False
    )

    store: Mapped[Optional["Store"]] = relationship(back_populates="coupons")
    source: Mapped["CouponSource"] = relationship()
    attempts: Mapped[list["CouponAttempt"]] = relationship(
        back_populates="coupon", cascade="all, delete-orphan"
    )


class CouponAttempt(Base, PkMixin, TimestampMixin):
    """Chapter 5(7) + Chapter 9: every apply attempt, including failed ones,
    so we never retry a known-bad coupon against the same store."""
    __tablename__ = "coupon_attempts"
    __table_args__ = (
        Index("ix_ca_coupon_status", "coupon_id", "status"),
    )

    coupon_id: Mapped[int] = mapped_column(ForeignKey("coupons.id"), nullable=False)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)
    purchase_plan_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("purchase_plans.id")
    )
    attempted_at: Mapped[datetime] = mapped_column(Date, nullable=False)
    applied_discount_minor: Mapped[Optional[int]] = mapped_column(Integer)
    currency: Mapped[Optional[str]] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(32), nullable=False)  # valid / invalid / error
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    raw_response: Mapped[Optional[str]] = mapped_column(Text)

    coupon: Mapped["Coupon"] = relationship(back_populates="attempts")


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

class Order(Base, PkMixin, TimestampMixin):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("source", "external_order_id", name="uq_orders_ext"),
    )

    source: Mapped[str] = mapped_column(String(32), nullable=False)  # buyma / after_hours
    external_order_id: Mapped[str] = mapped_column(String(64), nullable=False)
    buyer_name: Mapped[Optional[str]] = mapped_column(String(128))
    buyer_email: Mapped[Optional[str]] = mapped_column(String(255))
    ship_country: Mapped[Optional[str]] = mapped_column(String(2))
    ship_address: Mapped[Optional[str]] = mapped_column(Text)
    sale_price_minor: Mapped[Optional[int]] = mapped_column(Integer)
    sale_currency: Mapped[Optional[str]] = mapped_column(String(3))
    placed_at: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    received_at: Mapped[datetime] = mapped_column(Date, nullable=False)
    raw_email_path: Mapped[Optional[str]] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(
        String(32), default=OrderStatus.RECEIVED.value, nullable=False
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base, PkMixin, TimestampMixin):
    __tablename__ = "order_items"
    __table_args__ = (Index("ix_oi_order", "order_id"),)

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id"))
    requested_brand: Mapped[Optional[str]] = mapped_column(String(128))
    requested_model: Mapped[Optional[str]] = mapped_column(String(128))
    requested_colorway: Mapped[Optional[str]] = mapped_column(String(255))
    requested_size: Mapped[Optional[str]] = mapped_column(String(32))
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    sale_price_minor: Mapped[Optional[int]] = mapped_column(Integer)
    sale_currency: Mapped[Optional[str]] = mapped_column(String(3))

    order: Mapped["Order"] = relationship(back_populates="items")
    plans: Mapped[list["PurchasePlan"]] = relationship(
        back_populates="order_item", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# Plans + cost + purchase outcome
# ---------------------------------------------------------------------------

class PurchasePlan(Base, PkMixin, TimestampMixin):
    """One candidate source + its cost breakdown for an order item.

    Multiple plans per item let us compare; the chosen one is marked
    `selected=True`.
    """
    __tablename__ = "purchase_plans"
    __table_args__ = (
        Index("ix_pp_oi_selected", "order_item_id", "selected"),
    )

    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.id"), nullable=False)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)
    store_product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("store_products.id"))
    coupon_id: Mapped[Optional[int]] = mapped_column(ForeignKey("coupons.id"))

    # Final landed cost in JPY minor (sum of cost_components with same plan).
    # Computed by ahc.cost - never set manually.
    total_cost_jpy_minor: Mapped[Optional[int]] = mapped_column(Integer)
    estimated_profit_jpy_minor: Mapped[Optional[int]] = mapped_column(Integer)
    meets_min_profit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    selected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rejected_reason: Mapped[Optional[str]] = mapped_column(String(255))

    order_item: Mapped["OrderItem"] = relationship(back_populates="plans")
    cost_components: Mapped[list["CostComponent"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )
    purchase: Mapped[Optional["PurchaseRecord"]] = relationship(
        back_populates="plan", uselist=False
    )


class CostComponent(Base, PkMixin, TimestampMixin):
    """Chapter 7: each cost tracked individually.

    amount_minor is in *source currency* minor units; amount_jpy_minor is the
    FX-converted JPY minor. Both stored so we can audit either view.
    """
    __tablename__ = "cost_components"
    __table_args__ = (Index("ix_cc_plan_type", "plan_id", "cost_type"),)

    plan_id: Mapped[int] = mapped_column(ForeignKey("purchase_plans.id"), nullable=False)
    cost_type: Mapped[str] = mapped_column(String(32), nullable=False)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    fx_rate: Mapped[Optional[float]] = mapped_column(Float)  # 1 unit currency -> JPY
    amount_jpy_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    is_estimate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    note: Mapped[Optional[str]] = mapped_column(String(255))

    plan: Mapped["PurchasePlan"] = relationship(back_populates="cost_components")


class PurchaseRecord(Base, PkMixin, TimestampMixin):
    """Outcome of one buy attempt. Idempotency: a plan can have at most one
    non-failed record (Chapter 9 double-buy prevention)."""
    __tablename__ = "purchase_records"
    __table_args__ = (
        UniqueConstraint("plan_id", name="uq_pr_plan"),
    )

    plan_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_plans.id"), nullable=False, unique=True
    )
    store_order_id: Mapped[Optional[str]] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(
        String(32), default=PurchaseStatus.PLANNED.value, nullable=False
    )
    cart_total_minor: Mapped[Optional[int]] = mapped_column(Integer)
    cart_currency: Mapped[Optional[str]] = mapped_column(String(3))
    final_price_minor: Mapped[Optional[int]] = mapped_column(Integer)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(128))
    tracking_url: Mapped[Optional[str]] = mapped_column(String(512))
    screenshot_path: Mapped[Optional[str]] = mapped_column(String(512))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    requires_approval: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )  # Ch.9: needs human approval before payment

    plan: Mapped["PurchasePlan"] = relationship(back_populates="purchase")


# ---------------------------------------------------------------------------
# Compliance
# ---------------------------------------------------------------------------

class ComplianceRecord(Base, PkMixin, TimestampMixin):
    """Per-store robots.txt + ToS snapshot. The compliance module appends a
    new row on every refresh (history, never overwritten)."""
    __tablename__ = "compliance_records"
    __table_args__ = (
        Index("ix_cr_store_checked", "store_id", "checked_at"),
    )

    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)
    checked_at: Mapped[datetime] = mapped_column(Date, nullable=False)
    robots_txt: Mapped[Optional[str]] = mapped_column(Text)
    robots_allows_scrape: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    robots_allows_buy: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tos_excerpt: Mapped[Optional[str]] = mapped_column(Text)
    tos_allows_scrape: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tos_allows_buy: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    manual_verdict_scrape: Mapped[str] = mapped_column(
        String(16), default=ComplianceVerdict.UNKNOWN.value, nullable=False
    )
    manual_verdict_buy: Mapped[str] = mapped_column(
        String(16), default=ComplianceVerdict.UNKNOWN.value, nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text)
