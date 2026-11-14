"""RetailMeNot coupon source adapter.

RetailMeNot does **not** permit scraping of its public pages; it offers an
official API partnership program instead. Accordingly this adapter:

  * Has ``requires_api = True`` so the registry / collector can flag it.
  * ``fetch()`` checks the compliance gate (which is configured as ``manual``
    in ``config/compliance.yaml`` and will therefore deny by default), then
    returns an empty list with a clear log message. No HTML is fetched.
  * ``fetch_via_api(api_key)`` is the intended integration point but is left
    as ``NotImplementedError`` until an API key and endpoint are contracted.

The class exists so ``adapter_class: ahc.coupons.sources.retailmenot.RetailMeNotSource``
in ``config/coupon_sources.yaml`` resolves cleanly, and so a future API
integration has a home.
"""
from __future__ import annotations

from ..base import AbstractCouponSource, RawCoupon
from ...logging_setup import get_logger

log = get_logger(__name__)


class RetailMeNotSource(AbstractCouponSource):
    """RetailMeNot — API-only source (no scraping)."""

    slug = "retailmenot"

    #: RetailMeNot requires an API partnership; scraping is not allowed.
    requires_api = True

    def fetch(self) -> list[RawCoupon]:
        # Compliance first (Chapter 4 / Chapter 9): every source must ask the
        # gate before doing anything. With the shipped config the gate denies
        # retailmenot, so this normally raises CouponSourceError here.
        self._check_compliance()

        # An HTTP session is part of the contract even though we return early;
        # requiring it keeps the adapter honest if the API path is enabled.
        self._require_http()

        log.info(
            "RetailMeNot requires API partnership; configure API key to enable"
        )
        return []

    def fetch_via_api(self, api_key: str) -> list[RawCoupon]:
        """Fetch coupons through RetailMeNot's partner API.

        Not yet integrated. Implement once an API key + endpoint contract is
        in place; until then this raises so callers fail loudly instead of
        silently no-op'ing (Chapter 9 safety).
        """
        raise NotImplementedError("API not yet integrated")
