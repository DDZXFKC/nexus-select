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
    """Exact quote scope. account_scope/basket_key are opaque, non-secret IDs."""
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
    """A-axis: Assess campaign confidence based on evidence provenance.
    
    Groups by origin/report IDs to deduplicate syndications.
    """
    grouped = {}
    for d in discoveries:
        campaign = d.get("campaign")
        if not campaign:
            continue
        origin = d.get("origin_group") or d.get("report_id") or d.get("raw_ref") or _id(d)
        
        if campaign not in grouped:
            grouped[campaign] = {
                "roots": {},
                "latest_observed_at": "",
                "conditions_conflict": False,
                "official_status": "ACTIVE",
                "negation": None
            }
        g = grouped[campaign]
        if origin not in g["roots"]:
            g["roots"][origin] = d
        if d.get("observed_at", "") > g["latest_observed_at"]:
            g["latest_observed_at"] = d.get("observed_at")
        if d.get("conditions_conflict"):
            g["conditions_conflict"] = True
        if d.get("official_status") in ("EXPIRED", "RETIRED"):
            g["official_status"] = d.get("official_status")
        if d.get("negation_evidence"):
            if not g["negation"] or d.get("observed_at", "") > g["negation"].get("observed_at", ""):
                g["negation"] = d

    results = []
    for campaign, data in grouped.items():
        status = "DISCOVERED"
        if data["conditions_conflict"]:
            status = "CONFLICT"
        elif data["official_status"] == "EXPIRED":
            status = "EXPIRED"
        elif data["official_status"] == "RETIRED":
            status = "RETIRED"
        elif data["negation"]:
            status = "LIKELY_INVALID"
        
        results.append({
            "campaign": campaign,
            "campaign_confidence": status,
            "roots_count": len(data["roots"]),
            "latest_observed_at": data["latest_observed_at"],
            "conditions": [root.get("conditions", {}) for root in data["roots"].values()]
        })
    return results


def evaluate_eligibility(campaign, scope, product_facts, conditions):
    """B-axis: Evaluate eligibility against rules without leaking check results."""
    if not conditions:
        return {"campaign": campaign, "eligibility": "UNKNOWN", "reasons": ["NO_CONDITIONS"]}
    
    reasons = []
    elig = "MATCH"
    
    # 明示除外優先
    excluded_brands = conditions.get("excluded_brands", [])
    if excluded_brands is False: excluded_brands = []
    if product_facts.get("brand") in excluded_brands:
        return {"campaign": campaign, "eligibility": "EXCLUDED", "reasons": ["BRAND_EXCLUDED"]}
    
    eligible_brands = conditions.get("eligible_brands", [])
    if eligible_brands is False: eligible_brands = []
    if eligible_brands and product_facts.get("brand") not in eligible_brands:
        elig = "EXCLUDED"
        reasons.append("BRAND_NOT_ELIGIBLE")
        
    eligible_categories = conditions.get("eligible_categories", [])
    if eligible_categories is False: eligible_categories = []
    if eligible_categories and product_facts.get("category") not in eligible_categories:
        elig = "EXCLUDED"
        reasons.append("CATEGORY_NOT_ELIGIBLE")

    if conditions.get("sale_exclusion") and product_facts.get("on_sale"):
        elig = "EXCLUDED"
        reasons.append("SALE_EXCLUDED")
        
    if conditions.get("first_order_only") and not product_facts.get("is_first_order"):
        elig = "UNKNOWN"
        reasons.append("REQUIRES_FIRST_ORDER")
        
    ship_region = conditions.get("ship_region")
    if ship_region and scope.get("destination") not in ship_region:
        elig = "EXCLUDED"
        reasons.append("REGION_EXCLUDED")
        
    min_spend_minor = conditions.get("min_spend_minor")
    if min_spend_minor and scope.get("base_minor") < min_spend_minor:
        elig = "EXCLUDED"
        reasons.append("MIN_SPEND_NOT_MET")

    if elig == "MATCH":
        reasons.append("ALL_RULES_MATCHED")
        
    return {"campaign": campaign, "eligibility": elig, "reasons": reasons}


def rank_candidates(assessed, evaluated, checks, *, scope, now, max_age_seconds):
    """Rank candidates across three axes without leaking pricing side effects."""
    now_str = _time(now)
    now_dt = datetime.fromisoformat(now_str)
    max_age = _minor(max_age_seconds, "max_age_seconds", True)
    cutoff_dt = now_dt - timedelta(seconds=max_age)
    scope_id = _id(scope)
    
    c_axis = {}
    for c in checks:
        if _id(c.get("scope", {})) != scope_id:
            continue
        campaign = c.get("campaign")
        checked_at = c.get("checked_at")
        if not campaign or not checked_at:
            continue
            
        # 未来記録無視および時刻の正規化
        try:
            chk_dt = datetime.fromisoformat(str(checked_at).replace("Z", "+00:00"))
            if chk_dt.utcoffset() is None:
                continue # タイムゾーン不明は無視
            chk_dt = chk_dt.astimezone(timezone.utc)
        except Exception:
            continue
            
        if chk_dt > now_dt:
            continue
            
        if campaign not in c_axis or chk_dt > c_axis[campaign]["chk_dt"]:
            c_axis[campaign] = {
                "status": c.get("status"),
                "chk_dt": chk_dt,
                "expires_at": c.get("expires_at")
            }
        elif chk_dt == c_axis[campaign]["chk_dt"]:
            if c.get("status") != c_axis[campaign]["status"]:
                c_axis[campaign]["status"] = "UNKNOWN" # 同時刻矛盾

    merged = {}
    for a in assessed:
        merged[a["campaign"]] = {
            "campaign": a["campaign"],
            "campaign_confidence": a.get("campaign_confidence", "DISCOVERED"),
            "eligibility": "UNKNOWN",
            "check_status": "NOT_CHECKED",
            "reasons": []
        }
    for e in evaluated:
        if e["campaign"] in merged:
            merged[e["campaign"]]["eligibility"] = e["eligibility"]
            merged[e["campaign"]]["reasons"] = e.get("reasons", [])
        else:
            merged[e["campaign"]] = {
                "campaign": e["campaign"],
                "campaign_confidence": "DISCOVERED",
                "eligibility": e["eligibility"],
                "check_status": "NOT_CHECKED",
                "reasons": e.get("reasons", [])
            }
            
    for campaign, c_data in c_axis.items():
        if campaign in merged:
            status = c_data["status"]
            expires_at_raw = c_data.get("expires_at")
            
            # 期限の評価
            is_expired = False
            if expires_at_raw is not None:
                try:
                    exp_dt = datetime.fromisoformat(str(expires_at_raw).replace("Z", "+00:00"))
                    if exp_dt.utcoffset() is None:
                        status = "UNKNOWN"
                    elif exp_dt.astimezone(timezone.utc) <= now_dt:
                        is_expired = True
                except Exception:
                    status = "UNKNOWN"
            else:
                # APPLICABLEの場合はexpires_atが必須だが、純粋関数としては防御的にUNKNOWN
                if status == "APPLICABLE":
                    status = "UNKNOWN"
            
            if is_expired:
                status = "STALE"
            elif c_data["chk_dt"] < cutoff_dt:
                status = "STALE"
                
            merged[campaign]["check_status"] = status
            merged[campaign]["latest_checked_at"] = c_data["chk_dt"].isoformat(timespec="microseconds")

    candidates = list(merged.values())
    conf_order = {"DISCOVERED": 0, "CONFLICT": 1, "LIKELY_INVALID": 2, "EXPIRED": 3, "RETIRED": 4}
    elig_order = {"MATCH": 0, "UNKNOWN": 1, "EXCLUDED": 2}
    check_order = {"APPLICABLE": 0, "UNKNOWN": 1, "NOT_CHECKED": 2, "STALE": 3, "NOT_APPLICABLE": 4}
    
    candidates.sort(key=lambda x: (
        elig_order.get(x["eligibility"], 9),
        check_order.get(x["check_status"], 9),
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
                         conditions, origin_group=None, report_id=None, raw_ref=None,
                         official_status="ACTIVE", conditions_conflict=False, negation_evidence=False):
        """A discovery is evidence only, never a verified discount."""
        if not isinstance(conditions, dict):
            raise ValueError("conditions must be an object")
        row = dict(shop_code=_required(shop_code, "shop_code"),
                   campaign=_required(campaign, "campaign"),
                   source_url=_url(source_url), observed_at=_time(observed_at),
                   conditions=conditions, origin_group=origin_group, report_id=report_id,
                   raw_ref=raw_ref, official_status=official_status,
                   conditions_conflict=conditions_conflict, negation_evidence=negation_evidence)
        key = _id(row)
        with self._connection() as db:
            db.execute("INSERT OR IGNORE INTO ahc_coupon_observations_v1 VALUES (?,?,?,?,?)",
                       (key, row["shop_code"], row["campaign"], row["observed_at"], _json(row)))
        return key

    def record_raw(self, raw, *, observed_at):
        """Reuse existing ahc.coupons.base.RawCoupon adapter output."""
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
        """Persist an authorized, exact-context cart observation or failure."""
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
        """Return price evidence for the exact context; never approve sale."""
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

    def list_candidates(self, scope, *, now, max_age_seconds, product_facts):
        """Return ranked coupon candidates for a scope, recomputed from saved observations."""
        scope = context(**scope)
        scope_id = _id(scope)
        now = _time(now)
        with self._connection() as db:
            obs_rows = db.execute("SELECT payload FROM ahc_coupon_observations_v1 WHERE shop_code=?", (scope["shop_code"],)).fetchall()
            chk_rows = db.execute("SELECT payload FROM ahc_coupon_checks_v1 WHERE context_id=?", (scope_id,)).fetchall()
        
        discoveries = [json.loads(r["payload"]) for r in obs_rows]
        checks = [json.loads(r["payload"]) for r in chk_rows]
        
        assessed = assess_campaigns(discoveries)
        
        evaluated = []
        for a in assessed:
            # 複数のconditionsがある場合は最初のものを代表として評価（設計上の単純化）
            conditions = a["conditions"][0] if a["conditions"] else {}
            evaluated.append(evaluate_eligibility(a["campaign"], scope, product_facts, conditions))
                
        return rank_candidates(assessed, evaluated, checks, scope=scope, now=now, max_age_seconds=max_age_seconds)

