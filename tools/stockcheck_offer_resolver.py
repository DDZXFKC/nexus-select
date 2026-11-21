"""Pure multi-store price/stock decision logic. No network or cart writes.

Caller must supply fresh variation-exact merchant observations, fully-costed
sale price and evidence from authorized store adapters; UNKNOWN is not OOS.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from stockcheck_inline_price_policy import resolve_price_case

def _timestamp(value):
    if not isinstance(value,str):
        raise ValueError('missing timestamp')
    dt=datetime.fromisoformat(value.replace('Z','+00:00'))
    if dt.utcoffset() is None:
        raise ValueError('timestamp requires timezone')
    return dt.astimezone(timezone.utc)

@dataclass(frozen=True)
class MerchantObservation:
    offer_id: str
    variation_id: int
    stock: str
    checked_at: str
    cached: bool = False
    sale_price_jpy: Optional[int] = None
    complete_cost: bool = False
    evidence_ref: str = ''

@dataclass(frozen=True)
class OfferDecision:
    status: str
    offer_id: Optional[str] = None
    checkout_jpy: Optional[int] = None
    recomputed_jpy: Optional[int] = None
    requires_quote_acceptance: bool = False
    reason: str = ''
    evidence_ref: str = ''

def choose_offer(*,listed_jpy,variation_id,candidate_offer_ids,observations,now,max_age_seconds=90):
    """Pick cheapest valid offer, and OOS only when every offer proves OOS."""
    if type(listed_jpy) is not int or listed_jpy<=0:
        raise ValueError('listed_jpy must be positive integer')
    if type(variation_id) is not int or variation_id<=0:
        raise ValueError('invalid variation_id')
    if type(max_age_seconds) is not int or max_age_seconds<=0:
        raise ValueError('invalid max_age_seconds')
    current=_timestamp(now)
    ids=tuple(candidate_offer_ids)
    if not ids or any(not isinstance(x,str) or not x for x in ids) or len(set(ids))!=len(ids):
        return OfferDecision('UNCONFIRMED',reason='NO_VALID_CANDIDATES')
    confirmed_oos,incomplete,verified=0,False,[]
    for offer_id in ids:
        obs=observations.get(offer_id)
        if not isinstance(obs,MerchantObservation) or obs.offer_id!=offer_id:
            incomplete=True
            continue
        try:
            checked=_timestamp(obs.checked_at)
        except ValueError:
            incomplete=True
            continue
        age=(current-checked).total_seconds()
        if (obs.variation_id!=variation_id or obs.cached or age<0 or
                age>max_age_seconds or not obs.evidence_ref):
            incomplete=True
            continue
        if obs.stock=='OUT_OF_STOCK':
            confirmed_oos+=1
            continue
        if obs.stock!='IN_STOCK' or not obs.complete_cost:
            incomplete=True
            continue
        if type(obs.sale_price_jpy) is not int or obs.sale_price_jpy<=0:
            incomplete=True
            continue
        verified.append(obs)
    if verified:
        winner=min(verified,key=lambda o:(o.sale_price_jpy,o.offer_id))
        policy=resolve_price_case(listed_jpy,winner.sale_price_jpy)
        return OfferDecision(policy.status,winner.offer_id,policy.checkout_jpy,
                             winner.sale_price_jpy,policy.requires_customer_confirmation,
                             evidence_ref=winner.evidence_ref)
    if confirmed_oos==len(ids) and not incomplete:
        return OfferDecision('OUT_OF_STOCK',reason='ALL_OFFERS_CONFIRMED_OOS')
    return OfferDecision('UNCONFIRMED',reason='MISSING_OR_UNVERIFIED_EVIDENCE')
