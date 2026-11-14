"""Concrete coupon source adapters.

Each module here implements ``ahc.coupons.base.AbstractCouponSource`` for one
external source. Sources are imported lazily by the registry (via
``adapter_class`` in ``config/coupon_sources.yaml``); nothing in this package
performs network work at import time.
"""
