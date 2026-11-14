"""Auto-buying module (Chapter 6).

Stops at cart preparation by default (settings.dry_run_only=True). Real
payment requires explicit per-run approval AND per-store compliance clearance.

Public API:
    from ahc.buying import BuyOrchestrator, BuyResult, BuyStatus
"""
from .base import BuyOrchestrator, BuyResult, BuyStatus, BuyError
from .coupon_applier import CouponApplier
from .cart import CartBuilder
from .orchestrator import build_orchestrator

__all__ = [
    "BuyOrchestrator",
    "BuyResult",
    "BuyStatus",
    "BuyError",
    "CouponApplier",
    "CartBuilder",
    "build_orchestrator",
]
