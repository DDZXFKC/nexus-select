"""Buy orchestrator contract.

The orchestrator ties together: store adapter (cart + coupon) + compliance
gate + cost/profit + DB persistence. It MUST stop at "cart prepared" by
default; payment requires `settings.dry_run_only=False` AND an explicit
approval token passed at call time.

Chapter 9 safety invariants enforced here:
  - One PurchaseRecord per plan (UniqueConstraint on plan_id).
  - If a PurchaseRecord with status SUBMITTED/CONFIRMED/UNKNOWN already
    exists for the plan, refuse to start a new attempt (double-buy prevention).
  - If the cart total exceeds settings.max_cart_amount, abort.
  - If the result is UNKNOWN (page crashed, network dropped mid-submit),
    mark the record requires_approval=True and DO NOT auto-retry.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional

from ..stores.base import CartState


class BuyError(Exception):
    """Base for buy-flow errors."""


class BuyStatus(str, enum.Enum):
    PLANNED = "planned"
    CART_PREPARED = "cart_prepared"
    AWAITING_APPROVAL = "awaiting_approval"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    UNKNOWN = "unknown"          # Chapter 9: do NOT auto-retry
    FAILED = "failed"
    BLOCKED_COMPLIANCE = "blocked_compliance"
    BLOCKED_MIN_PROFIT = "blocked_min_profit"
    BLOCKED_MAX_AMOUNT = "blocked_max_amount"
    BLOCKED_DRY_RUN = "blocked_dry_run"
    BLOCKED_DOUBLE_BUY = "blocked_double_buy"


@dataclass
class BuyResult:
    plan_id: int
    store_slug: str
    status: BuyStatus
    cart: Optional[CartState] = None
    final_price_minor: Optional[int] = None
    currency: Optional[str] = None
    store_order_id: Optional[str] = None
    screenshot_path: Optional[str] = None
    error_message: Optional[str] = None
    requires_approval: bool = True
    notes: list[str] = field(default_factory=list)


class BuyOrchestrator:
    """Interface. Concrete implementation in orchestrator.py."""

    def prepare_cart(self, plan_id: int) -> BuyResult:
        raise NotImplementedError

    def submit_payment(self, plan_id: int, *, approval_token: str) -> BuyResult:
        """Only callable when dry_run_only=False AND a valid approval token
        is supplied. Default implementation always refuses.
        """
        raise BuyError("submit_payment not implemented; dry_run_only guard active")
