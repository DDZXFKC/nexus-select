"""Store adapters.

Each store has an adapter that knows how to:
  - search / fetch a product page (price, stock, sizes)
  - add to cart, apply coupon code, read back the applied discount
  - read shipping + tax totals from the cart page

The base class defines the contract. EC-platform common adapters
(Shopify, Magento, WooCommerce) implement most of it; store-specific
subclasses only override selectors that differ.
"""
from .base import (
    AbstractStoreAdapter,
    StoreAdapterError,
    ProductFetch,
    CartState,
    CouponApplyResult,
)
from .registry import adapter_for, get_adapter

__all__ = [
    "AbstractStoreAdapter",
    "StoreAdapterError",
    "ProductFetch",
    "CartState",
    "CouponApplyResult",
    "adapter_for",
    "get_adapter",
]
