"""Shared L2 coupon evidence/selection; no network or purchase side effects.

Caller passes the collection SQLite path explicitly. Existing source adapters
feed discoveries; an authorized cart check feeds exact-context price evidence.
Money is integer minor units, merchandise subtotal only (not landed cost).
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit


def _time(value):
    if not isinstance(value, str):
        raise ValueError("timestamp must be an offset-aware ISO string")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.utcoffset() is None:
        raise ValueError("timestamp requires timezone")
    return dt.astimezone(timezone.utc).isoformat(timespec="microseconds")


def _required(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing {name}")
    return value.strip()


def _minor(value, name, positive=False):
    if type(value) is not int or value < int(positive):
        raise ValueError(f"invalid {name}: integer minor units required")
    return value


def _url(value):
    value = _required(value, "source_url")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("HTTPS evidence URL required")
    return value


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _id(value):
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def context(*, shop_code, variant_id, currency, destination, account_scope,
            quantity, base_minor, basket_key):
    """Exact quote scope. account_scope/basket_key are opaque, non-secret IDs.

    base_minor is the current merchandise subtotal, including quantity and
    any already-applied public sale price, but before the coupon being tested.
    basket_key identifies the entire basket/pricing context, not just a SKU.
    """
    currency = _required(currency, "currency").upper()
    if currency not in {"USD", "EUR", "GBP", "JPY"}:
        raise ValueError("unsupported currency")
    return dict(shop_code=_required(shop_code, "shop_code"),
                variant_id=_required(variant_id, "variant_id"), currency=currency,
                destination=_required(destination, "destination"),
                account_scope=_required(account_scope, "account_scope"),
                quantity=_minor(quantity, "quantity", True),
                base_minor=_minor(base_minor, "base_minor", True),
                basket_key=_required(basket_key, "basket_key"))


def assess_campaigns(discoveries):
    """Normalize and group discovery evidence, returning campaign confidence.
    
    Aggregates sources by hostname to treat syndications or identical sources 
    as a single root evidence. Confidence is based on distinct source count.
    """
    grouped = {}
    for d in discoveries:
        campaign = d.get("campaign")
        source = d.get("source_url")
        if not campaign or not source:
            continue
        host = urlsplit(source).hostname or source
        if campaign not in grouped:
            grouped[campaign] = {"sources": set(), "latest": ""}
        grouped[campaign]["sources"].add(host)
        if d.get("observed_at", "") > grouped[campaign]["latest"]:
            grouped[campaign]["latest"] = d.get("observed_at")

    results = []
    for campaign, data in grouped.items():
        sources_count = len(data["sources"])
        if sources_count >= 2:
            conf = "HIGH"
        elif sources_count == 1:
            conf = "MEDIUM"
        else:
            conf = "LOW"
        results.append({
            "campaign": campaign,
            "campaign_confidence": conf,
            "sources": sorted(list(data["sources"])),
            "latest_observed_at": data["latest"]
        })
    return results


def evaluate_eligibility(checks):
    """Evaluate eligibility based on authorized cart checks."""
    grouped = {}
    for c in checks:
        campaign = c.get("campaign")
        status = c.get("status")
        checked_at = c.get("checked_at")
        if not campaign or not status or not checked_at:
            continue
        if campaign not in grouped or checked_at > grouped[campaign]["checked_at"]:
            grouped[campaign] = {
                "status": status,
                "checked_at": checked_at
            }
    results = []
    for campaign, data in grouped.items():
        status = data["status"]
        if status == "APPLICABLE":
            elig = "CONFIRMED"
        elif status == "NOT_APPLICABLE":
            elig = "REJECTED"
        else:
            elig = "UNKNOWN"
        results.append({
            "campaign": campaign,
            "eligibility": elig,
            "check_status": status,
            "latest_checked_at": data["checked_at"]
        })
    return results


def rank_candidates(assessed, evaluated):
    """Rank candidates across three axes without leaking pricing side effects."""
    merged = {}
    for a in assessed:
        merged[a["campaign"]] = {
            "campaign": a["campaign"],
            "campaign_confidence": a.get("campaign_confidence", "LOW"),
            "eligibility": "UNTESTED",
            "check_status": "UNTESTED"
        }
    for e in evaluated:
        if e["campaign"] in merged:
            merged[e["campaign"]]["eligibility"] = e["eligibility"]
            merged[e["campaign"]]["check_status"] = e["check_status"]
        else:
            merged[e["campaign"]] = {
                "campaign": e["campaign"],
                "campaign_confidence": "LOW",
                "eligibility": e["eligibility"],
                "check_status": e["check_status"]
            }
    
    conf_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    elig_order = {"CONFIRMED": 0, "UNKNOWN": 1, "UNTESTED": 2, "REJECTED": 3}
    
    candidates = list(merged.values())
    candidates.sort(key=lambda x: (
        elig_order.get(x["eligibility"], 9),
        conf_order.get(x["campaign_confidence"], 9),
        x["campaign"]
    ))
    return candidates


class CouponBridge:
    def __init__(self, db_path):
        self.path = Path(db_path).expanduser()
        if not self.path.parent.is_dir():
            raise ValueError("existing collection DB directory required")

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(str(self.path), timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def initialize(self):
        """Explicit, additive migration only; no import-time DB writes."""
        with self._connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS ahc_coupon_observations_v1 (
                    id TEXT PRIMARY KEY, shop_code TEXT NOT NULL,
                    campaign TEXT NOT NULL, observed_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ahc_coupon_obs_shop_v1
                    ON ahc_coupon_observations_v1(shop_code, campaign, observed_at);
                CREATE TABLE IF NOT EXISTS ahc_coupon_checks_v1 (
                    id TEXT PRIMARY KEY, context_id TEXT NOT NULL,
                    campaign TEXT NOT NULL, checked_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ahc_coupon_check_context_v1
                    ON ahc_coupon_checks_v1(context_id, campaign, checked_at);
            """)

    def record_discovery(self, *, shop_code, campaign, source_url, observed_at,
                         conditions):
        """A discovery is evidence only, never a verified discount."""
        if not isinstance(conditions, dict):
            raise ValueError("conditions must be an object")
        row = dict(shop_code=_required(shop_code, "shop_code"),
                   campaign=_required(campaign, "campaign"),
                   source_url=_url(source_url), observed_at=_time(observed_at),
                   conditions=conditions)
        key = _id(row)
        with self._connection() as db:
            db.execute("INSERT OR IGNORE INTO ahc_coupon_observations_v1 VALUES (?,?,?,?,?)",
                       (key, row["shop_code"], row["campaign"], row["observed_at"], _json(row)))
        return key

    def record_raw(self, raw, *, observed_at):
        """Reuse existing ahc.coupons.base.RawCoupon adapter output.

        Do not infer store from an aggregator title or treat defaults as facts.
        Storeless/non-code deals require a separate review, not a guessed store.
        """
        if not raw.store_slug or not raw.code:
            raise ValueError("unresolved store/campaign; manual review required")
        data = {name: getattr(raw, name, None) for name in (
            "title", "description", "discount_type", "discount_value",
            "discount_currency", "min_spend_major", "min_spend_currency",
            "eligible_brands", "excluded_brands", "eligible_categories",
            "first_order_only", "combinable", "ship_region", "valid_from", "valid_until",
            "source_slug")}
        for key in ("valid_from", "valid_until"):
            if data[key] is not None:
                data[key] = data[key].isoformat()
        return self.record_discovery(shop_code=raw.store_slug, campaign=raw.code,
                                     source_url=raw.source_url, observed_at=observed_at,
                                     conditions=data)

    def record_check(self, *, scope, campaign, source_url, checked_at, expires_at,
                     status, post_minor=None, conditions_confirmed=False,
                     usage_available=False, evidence_ref):
        """Persist an authorized, exact-context cart observation or failure.

        Only APPLICABLE with confirmed conditions, usage and known expiry can
        supply a discounted subtotal. No code guessing, cart creation or payment.
        """
        scope = context(**scope)
        checked = _time(checked_at)
        expires = _time(expires_at) if expires_at is not None else None
        if status not in {"APPLICABLE", "NOT_APPLICABLE", "UNKNOWN"}:
            raise ValueError("invalid status")
        if status == "APPLICABLE":
            if conditions_confirmed is not True or usage_available is not True:
                raise ValueError("conditions and available usage must be confirmed")
            if expires is None or expires <= checked:
                raise ValueError("known future expiry required")
            if _minor(post_minor, "post_minor") >= scope["base_minor"]:
                raise ValueError("no proven merchandise discount")
        elif post_minor is not None:
            raise ValueError("unverified discount cannot contain an applied price")
        row = dict(scope=scope, campaign=_required(campaign, "campaign"),
                   source_url=_url(source_url), checked_at=checked, expires_at=expires,
                   status=status, post_minor=post_minor,
                   conditions_confirmed=conditions_confirmed is True,
                   usage_available=usage_available is True,
                   evidence_ref=_required(evidence_ref, "evidence_ref"))
        key = _id(row)
        with self._connection() as db:
            db.execute("INSERT OR IGNORE INTO ahc_coupon_checks_v1 VALUES (?,?,?,?,?)",
                       (key, _id(scope), row["campaign"], checked, _json(row)))
        return key

    def select(self, scope, *, now, max_age_seconds):
        """Return price evidence for the exact context; never approve sale.

        Later failures supersede earlier successes. Conflicting same-time checks
        fail closed. Newer discovery evidence triggers re-check. No stacking.
        """
        scope = context(**scope)
        now = _time(now)
        max_age = _minor(max_age_seconds, "max_age_seconds", True)
        cutoff = (datetime.fromisoformat(now) - timedelta(seconds=max_age)).isoformat(timespec="microseconds")
        with self._connection() as db:
            rows = db.execute("SELECT id, campaign, checked_at, payload FROM ahc_coupon_checks_v1 WHERE context_id=? AND checked_at<=? ORDER BY checked_at DESC, id", (_id(scope), now)).fetchall()
            observations = db.execute("SELECT campaign, MAX(observed_at) AS latest FROM ahc_coupon_observations_v1 WHERE shop_code=? AND observed_at<=? GROUP BY campaign", (scope["shop_code"], now)).fetchall()
        latest = {r["campaign"]: r["latest"] for r in observations}
        groups = {}
        for r in rows:
            group = groups.setdefault(r["campaign"], [])
            if not group or r["checked_at"] == group[0]["checked_at"]:
                group.append(r)
        eligible = []
        for campaign, group in groups.items():
            if len(group) != 1:
                continue
            r = group[0]
            check = json.loads(r["payload"])
            if (check["status"] != "APPLICABLE" or r["checked_at"] < cutoff
                    or check["expires_at"] <= now
                    or latest.get(campaign, "") > r["checked_at"]):
                continue
            eligible.append((check["post_minor"], campaign, r["id"], check))
        base = scope["base_minor"]
        if not eligible:
            return dict(status="NO_VERIFIED_DISCOUNT", normal_minor=base,
                        effective_minor=base, campaign=None, check_id=None,
                        sale_approved=False)
        amount, campaign, key, check = min(eligible, key=lambda x: x[:3])
        return dict(status="APPLICABLE", normal_minor=base, effective_minor=amount,
                    campaign=campaign, check_id=key, checked_at=check["checked_at"],
                    expires_at=check["expires_at"], sale_approved=False)

    def list_candidates(self, shop_code):
        """Return ranked coupon candidates for a shop, recomputed from saved observations."""
        with self._connection() as db:
            obs_rows = db.execute("SELECT payload FROM ahc_coupon_observations_v1 WHERE shop_code=?", (shop_code,)).fetchall()
            chk_rows = db.execute("SELECT payload FROM ahc_coupon_checks_v1").fetchall()
        
        discoveries = [json.loads(r["payload"]) for r in obs_rows]
        checks = []
        for r in chk_rows:
            p = json.loads(r["payload"])
            if p.get("scope", {}).get("shop_code") == shop_code:
                checks.append(p)
                
        return rank_candidates(assess_campaigns(discoveries), evaluate_eligibility(checks))
