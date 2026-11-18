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
from decimal import Decimal, ROUND_HALF_UP
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


def assess_campaigns(discoveries, *, now):
    """A-axis: Assess campaign confidence based on evidence provenance."""
    now_dt = datetime.fromisoformat(_time(now))
    grouped = {}
    
    for d in discoveries:
        campaign = d.get("campaign")
        if not campaign: continue
        
        obs_at_str = d.get("observed_at")
        if not obs_at_str: continue
        try:
            obs_dt = datetime.fromisoformat(str(obs_at_str).replace("Z", "+00:00"))
            if obs_dt.utcoffset() is None: continue
            obs_dt = obs_dt.astimezone(timezone.utc)
        except: continue
        
        if obs_dt > now_dt: continue
        
        origin = d.get("origin_group") or d.get("report_id") or d.get("raw_ref")
        is_official = d.get("evidence_type") == "OFFICIAL"
        
        if campaign not in grouped:
            grouped[campaign] = {
                "roots": {}, "latest_official_obs": None, "latest_obs": datetime.min.replace(tzinfo=timezone.utc),
                "conditions_conflict": False, "official_status": None,
                "negations": [], "successes": [], "latest_conditions": {}, "official_rows": [], "third_party_rows": []
            }
        g = grouped[campaign]
        
        g["official_rows" if is_official else "third_party_rows"].append((obs_dt, d))
        # 公式優先で latest_conditions 更新
        if is_official:
            if g["latest_official_obs"] is None or obs_dt > g["latest_official_obs"]:
                g["latest_official_obs"] = obs_dt
                g["latest_conditions"] = d.get("conditions", {})
        elif g["latest_official_obs"] is None:
            if obs_dt > g["latest_obs"]:
                g["latest_obs"] = obs_dt
                g["latest_conditions"] = d.get("conditions", {})
                
        if origin:
            if origin not in g["roots"]:
                g["roots"][origin] = d
        # fallback _id(d) 廃止：出所不明は独立根拠に数えない

        if d.get("conditions_conflict"):
            g["conditions_conflict"] = True
        if is_official and d.get("official_status") in ("EXPIRED", "RETIRED", "ACTIVE"):
            g["official_status"] = d.get("official_status")
            
        def _get_dt(s):
            if not s: return None
            try:
                dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
                if dt.utcoffset() is None: return None
                return dt.astimezone(timezone.utc)
            except: return None
            
        succ_dt = _get_dt(d.get("success_at"))
        fail_dt = _get_dt(d.get("failure_at")) or obs_dt
        
        if d.get("negation_evidence"):
            # originも保存して独立性判定に使用
            g["negations"].append({"time": fail_dt, "reason": d.get("negation_reason"), "origin": origin})
        if d.get("success_evidence") and succ_dt is not None and succ_dt <= obs_dt:
            g["successes"].append({"time": succ_dt, "origin": origin})

    results = []
    for campaign, data in grouped.items():
        status = "DISCOVERED"
        roots_count = len(data["roots"])
        authority = data["official_rows"] or data["third_party_rows"]
        latest_at = max(t for t, _ in authority)
        latest_rows = [d for t, d in authority if t == latest_at]
        signatures = {_json([d.get("conditions", {}), d.get("official_status") if data["official_rows"] else None]) for d in latest_rows}
        data["conditions_conflict"] |= len(signatures) != 1
        data["latest_conditions"] = latest_rows[0].get("conditions", {}) if len(signatures) == 1 else {}
        data["official_status"] = latest_rows[0].get("official_status") if data["official_rows"] and len(signatures) == 1 else None
        
        latest_neg = max([n["time"] for n in data["negations"]], default=datetime.min.replace(tzinfo=timezone.utc))
        has_recent_success = any(s["time"] > latest_neg for s in data["successes"])
        has_2_indep_success = False  # no validated recency policy yet
        # 独立した（originが明確で異なる）失敗証拠が2件以上の場合のみ無効候補とする
        has_2_indep_negations = len({n["origin"] for n in data["negations"] if n["origin"]}) >= 2
        
        if data["official_status"] == "EXPIRED":
            status = "EXPIRED"
        elif data["official_status"] == "RETIRED":
            status = "RETIRED"
        elif data["conditions_conflict"]:
            status = "CONFLICT"
        elif has_2_indep_success or (data["official_status"] == "ACTIVE" and has_recent_success):
            status = "PROMISING"
        elif has_2_indep_negations and not has_recent_success:
            status = "LIKELY_INVALID"
            
        latest = latest_at
        results.append({
            "campaign": campaign,
            "campaign_confidence": status,
            "roots_count": roots_count,
            "latest_observed_at": latest.isoformat(timespec="microseconds"),
            "conditions": data["latest_conditions"]
        })
    return results


def evaluate_eligibility(campaign, scope, product_facts, conditions, *, now=None):
    """B-axis: Evaluate eligibility against rules without leaking check results."""
    if not conditions:
        return {"campaign": campaign, "eligibility": "UNKNOWN", "reasons": ["NO_CONDITIONS"]}
    
    reasons = []
    all_match = True
    
    def _is_unspecified(val):
        # None / 空リストは未指定。
        # 明示的な False は「制限なし」として指定済みと扱う。
        return val is None or (isinstance(val, list) and not val)

    for field in ("valid_from", "valid_until"):
        if field not in conditions:
            continue
        try:
            boundary, current = _time(conditions[field]), _time(now)
        except (ValueError, TypeError):
            all_match = False
            reasons.append("PERIOD_UNKNOWN:" + field)
            continue
        if (field == "valid_from" and current < boundary) or (field == "valid_until" and current >= boundary):
            return {"campaign": campaign, "eligibility": "EXCLUDED", "reasons": ["OUTSIDE_VALID_PERIOD"]}
    conditions = dict(conditions)
    for field in ("eligible_brands", "excluded_brands", "eligible_categories"):
        value = conditions.get(field)
        if value is not None and (not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value)):
            all_match = False
            reasons.append("INVALID:" + field)
            conditions[field] = None
    for field in ("sale_exclusion", "first_order_only"):
        value = conditions.get(field)
        if value is not None and type(value) is not bool:
            all_match = False
            reasons.append("INVALID:" + field)
            conditions[field] = None
    # 完全性チェック：全次元が明示されているか（False等の明示的无制限も含む）
    dims_present = {
        "brand": not _is_unspecified(conditions.get("excluded_brands")) or not _is_unspecified(conditions.get("eligible_brands")),
        "category": not _is_unspecified(conditions.get("eligible_categories")),
        "sale": not _is_unspecified(conditions.get("sale_exclusion")),
        "first_order": not _is_unspecified(conditions.get("first_order_only")),
        "region": not _is_unspecified(conditions.get("ship_region")),
        "min_spend": not _is_unspecified(conditions.get("min_spend_minor")) or (not _is_unspecified(conditions.get("min_spend_major")) and not _is_unspecified(conditions.get("min_spend_currency")))
    }
    if not all(dims_present.values()):
        all_match = False
        reasons.append("INCOMPLETE_RULES")

    # 明示除外優先
    excluded_brands = conditions.get("excluded_brands")
    if _is_unspecified(excluded_brands):
        if "excluded_brands" in conditions:
            all_match = False; reasons.append("UNIMPLEMENTED:excluded_brands")
    else:
        if product_facts.get("brand") is None:
            all_match = False; reasons.append("BRAND_UNKNOWN")
        elif product_facts.get("brand") in excluded_brands:
            return {"campaign": campaign, "eligibility": "EXCLUDED", "reasons": ["BRAND_EXCLUDED"]}
    
    eligible_brands = conditions.get("eligible_brands")
    if not _is_unspecified(eligible_brands):
        if product_facts.get("brand") is None:
            all_match = False; reasons.append("BRAND_UNKNOWN")
        elif product_facts.get("brand") not in eligible_brands:
            return {"campaign": campaign, "eligibility": "EXCLUDED", "reasons": ["BRAND_NOT_ELIGIBLE"]}
            
    eligible_categories = conditions.get("eligible_categories")
    if not _is_unspecified(eligible_categories):
        if product_facts.get("category") is None:
            all_match = False; reasons.append("CATEGORY_UNKNOWN")
        elif product_facts.get("category") not in eligible_categories:
            return {"campaign": campaign, "eligibility": "EXCLUDED", "reasons": ["CATEGORY_NOT_ELIGIBLE"]}

    sale_excl = conditions.get("sale_exclusion")
    if not _is_unspecified(sale_excl):
        if product_facts.get("on_sale") is None:
            all_match = False; reasons.append("SALE_STATUS_UNKNOWN")
        elif sale_excl and product_facts.get("on_sale"):
            return {"campaign": campaign, "eligibility": "EXCLUDED", "reasons": ["SALE_EXCLUDED"]}
        elif sale_excl is False:
            pass
            
    first_order = conditions.get("first_order_only")
    if not _is_unspecified(first_order):
        if product_facts.get("is_first_order") is None:
            all_match = False; reasons.append("FIRST_ORDER_UNKNOWN")
        elif first_order and not product_facts.get("is_first_order"):
            return {"campaign": campaign, "eligibility": "EXCLUDED", "reasons": ["NOT_FIRST_ORDER"]}

    ship_region = conditions.get("ship_region")
    if not _is_unspecified(ship_region):
        dest = scope.get("destination")
        if dest is None:
            all_match = False; reasons.append("REGION_UNKNOWN")
        else:
            if isinstance(ship_region, list):
                if dest not in ship_region:
                    return {"campaign": campaign, "eligibility": "EXCLUDED", "reasons": ["REGION_EXCLUDED"]}
            elif dest != ship_region:
                return {"campaign": campaign, "eligibility": "EXCLUDED", "reasons": ["REGION_EXCLUDED"]}
            
    min_spend_major = conditions.get("min_spend_major")
    min_spend_curr = conditions.get("min_spend_currency")
    min_spend_minor = conditions.get("min_spend_minor")
    
    if not _is_unspecified(min_spend_minor):
        if type(min_spend_minor) is not int or min_spend_minor < 0:
            all_match = False; reasons.append("MIN_SPEND_INVALID")
        elif scope.get("currency") != min_spend_curr:
            all_match = False; reasons.append("CURRENCY_MISMATCH")
        elif scope.get("base_minor", 0) < min_spend_minor:
            return {"campaign": campaign, "eligibility": "EXCLUDED", "reasons": ["MIN_SPEND_NOT_MET"]}
    elif not _is_unspecified(min_spend_major) and not _is_unspecified(min_spend_curr):
        try:
            major_dec = Decimal(str(min_spend_major))
            if not major_dec.is_finite() or major_dec < 0:
                all_match = False; reasons.append("MIN_SPEND_INVALID")
            elif scope.get("currency") != min_spend_curr:
                all_match = False; reasons.append("CURRENCY_MISMATCH")
            else:
                exp = {"USD": 2, "EUR": 2, "GBP": 2, "JPY": 0}.get(min_spend_curr, None)
                if exp is None:
                    all_match = False; reasons.append("UNSUPPORTED_CURRENCY")
                else:
                    calculated_minor = int((major_dec * (10 ** exp)).to_integral_value(rounding=ROUND_HALF_UP))
                    if scope.get("base_minor", 0) < calculated_minor:
                        return {"campaign": campaign, "eligibility": "EXCLUDED", "reasons": ["MIN_SPEND_NOT_MET"]}
        except Exception:
            all_match = False; reasons.append("MIN_SPEND_INVALID")

    unsupported = [k for k in conditions.keys() if k not in (
        "excluded_brands", "eligible_brands", "eligible_categories", "sale_exclusion",
        "first_order_only", "ship_region", "min_spend_major", "min_spend_currency", "min_spend_minor",
        "valid_from", "valid_until"
    )]
    if unsupported:
        all_match = False
        reasons.extend([f"UNIMPLEMENTED:{k}" for k in unsupported])

    if all_match and not reasons:
        return {"campaign": campaign, "eligibility": "MATCH", "reasons": ["ALL_RULES_MATCHED"]}
        
    return {"campaign": campaign, "eligibility": "UNKNOWN", "reasons": reasons}


def _valid_applied_check(check, scope):
    try:
        return (check.get("status") == "APPLICABLE"
                and context(**check["scope"]) == scope
                and check.get("conditions_confirmed") is True
                and check.get("usage_available") is True
                and _minor(check.get("post_minor"), "post_minor") < scope["base_minor"]
                and bool(_required(check.get("evidence_ref"), "evidence_ref"))
                and bool(_url(check.get("source_url")))
                and _time(check["expires_at"]) > _time(check["checked_at"]))
    except (ValueError, TypeError, KeyError):
        return False


def rank_candidates(assessed, evaluated, checks, discoveries, *, scope, now, max_age_seconds):
    """Rank candidates across three axes without leaking pricing side effects."""
    now_dt = datetime.fromisoformat(_time(now))
    cutoff_dt = now_dt - timedelta(seconds=_minor(max_age_seconds, "max_age_seconds", True))
    scope_id = _id(scope)
    
    c_axis = {}
    for c in checks:
        if _id(c.get("scope", {})) != scope_id: continue
        campaign = c.get("campaign")
        checked_at_str = c.get("checked_at")
        if not campaign or not checked_at_str: continue
            
        try:
            chk_dt = datetime.fromisoformat(str(checked_at_str).replace("Z", "+00:00"))
            if chk_dt.utcoffset() is None: continue
            chk_dt = chk_dt.astimezone(timezone.utc)
        except: continue
        
        if chk_dt > now_dt: continue
        
        if campaign not in c_axis:
            c_axis[campaign] = {"entries": []}
        c_axis[campaign]["entries"].append((chk_dt, c))

    obs_latest = {}
    for d in discoveries:
        c = d.get("campaign")
        # discoveriesにscopeがない場合はlist_candidatesから渡されるroot scopeとみなす
        d_scope = d.get("scope", scope)
        if not c or _id(d_scope) != scope_id: continue
        try:
            obs_dt = datetime.fromisoformat(str(d.get("observed_at")).replace("Z", "+00:00"))
            if obs_dt.utcoffset() is None: continue
            obs_dt = obs_dt.astimezone(timezone.utc)
        except: continue
        
        if obs_dt > now_dt: continue
        if c not in obs_latest or obs_dt > obs_latest[c]:
            obs_latest[c] = obs_dt

    merged = {}
    for a in assessed:
        merged[a["campaign"]] = {
            "campaign": a["campaign"], "campaign_confidence": a.get("campaign_confidence", "DISCOVERED"),
            "eligibility": "UNKNOWN", "check_status": "NOT_CHECKED", "reasons": []
        }
    for e in evaluated:
        if e["campaign"] in merged:
            merged[e["campaign"]]["eligibility"] = e["eligibility"]
            merged[e["campaign"]]["reasons"] = e.get("reasons", [])
        else:
            merged[e["campaign"]] = {
                "campaign": e["campaign"], "campaign_confidence": "DISCOVERED",
                "eligibility": e["eligibility"], "check_status": "NOT_CHECKED", "reasons": e.get("reasons", [])
            }
            
    for campaign, data in c_axis.items():
        if campaign not in merged:
            merged[campaign] = {
                "campaign": campaign, "campaign_confidence": "DISCOVERED",
                "eligibility": "UNKNOWN", "check_status": "NOT_CHECKED", "reasons": []
            }
        entries = sorted(data["entries"], key=lambda x: x[0], reverse=True)
        if not entries: continue
        
        top_chk_dt = entries[0][0]
        top_entries = [e for e in entries if e[0] == top_chk_dt]
        
        status = "UNKNOWN"
        if len(top_entries) == 1:
            c_data = top_entries[0][1]
            status = c_data.get("status", "UNKNOWN")
            expires_at_raw = c_data.get("expires_at")
            is_expired = False
            is_unknown_expiry = False
            
            if expires_at_raw:
                try:
                    exp_dt = datetime.fromisoformat(str(expires_at_raw).replace("Z", "+00:00"))
                    if exp_dt.utcoffset() is None:
                        is_unknown_expiry = True
                    elif exp_dt.astimezone(timezone.utc) <= now_dt:
                        is_expired = True
                except:
                    is_unknown_expiry = True
            else:
                # expires_at が欠落している場合
                is_unknown_expiry = True
            
            if is_expired or top_chk_dt < cutoff_dt:
                status = "STALE"
            elif obs_latest.get(campaign, datetime.min.replace(tzinfo=timezone.utc)) > top_chk_dt:
                status = "STALE"
            elif status == "APPLICABLE" and (is_unknown_expiry or not _valid_applied_check(c_data, scope)
                    or merged[campaign]["eligibility"] != "MATCH"
                    or merged[campaign]["campaign_confidence"] in {"EXPIRED", "RETIRED", "CONFLICT", "LIKELY_INVALID"}):
                status = "UNKNOWN" # 安全契約: 期限・条件確認・利用可能度が揃っていないAPPLICABLEはUNKNOWNへ
        else:
            # 同時刻に複数の異なる証拠がある場合は矛盾としてUNKNOWN
            status = "UNKNOWN"
            
        merged[campaign]["check_status"] = status
        merged[campaign]["latest_checked_at"] = top_chk_dt.isoformat(timespec="microseconds")

    candidates = list(merged.values())
    
    # 隔離対象
    excluded_status = {"EXPIRED", "RETIRED", "EXCLUDED"}
    active = [c for c in candidates if c["eligibility"] not in excluded_status and c["campaign_confidence"] not in excluded_status]
    isolated = [c for c in candidates if c["eligibility"] in excluded_status or c["campaign_confidence"] in excluded_status]
    
    conf_order = {"PROMISING": 0, "DISCOVERED": 1, "CONFLICT": 2, "LIKELY_INVALID": 3}
    elig_order = {"MATCH": 0, "UNKNOWN": 1}
    check_order = {"APPLICABLE": 0, "UNKNOWN": 1, "NOT_CHECKED": 2, "STALE": 3, "NOT_APPLICABLE": 4}
    
    active.sort(key=lambda x: (
        elig_order.get(x["eligibility"], 9),
        check_order.get(x["check_status"], 9),
        conf_order.get(x["campaign_confidence"], 9),
        x["campaign"]
    ))
    isolated.sort(key=lambda x: x["campaign"])
    
    return active + isolated



class CouponBridge:
    def __init__(self, db_path, allowed_shops=None):
        """allowed_shops: iterable of shop_code. Empty/None = reject all (no allow-all fallback)."""
        self.path = Path(db_path).expanduser()
        if not self.path.parent.is_dir():
            raise ValueError("existing collection DB directory required")
        if allowed_shops is None:
            self._allowed_shops = frozenset()
        else:
            if isinstance(allowed_shops, (str, bytes, dict)):
                raise ValueError("allowed_shops must be a collection of shop codes")
            self._allowed_shops = frozenset(_required(s, "allowed shop") for s in allowed_shops)

    def _assert_allowed_shop(self, shop_code):
        code = _required(shop_code, "shop_code")
        if code not in self._allowed_shops:
            raise ValueError(f"shop_code not in allowed registry: {code}")
        return code

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
                         official_status=None, conditions_conflict=False, negation_evidence=False,
                         success_evidence=False, evidence_type=None):
        """A discovery is evidence only, never a verified discount."""
        shop_code = self._assert_allowed_shop(shop_code)
        if not isinstance(conditions, dict):
            raise ValueError("conditions must be an object")
        row = dict(shop_code=_required(shop_code, "shop_code"),
                   campaign=_required(campaign, "campaign"),
                   source_url=_url(source_url), observed_at=_time(observed_at),
                   conditions=conditions, origin_group=origin_group, report_id=report_id,
                   raw_ref=raw_ref, official_status=official_status,
                   conditions_conflict=conditions_conflict, negation_evidence=negation_evidence,
                   success_evidence=success_evidence, evidence_type=evidence_type)
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
        self._assert_allowed_shop(scope["shop_code"])
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

    def select(self, scope, *, now, max_age_seconds, product_facts=None):
        """Return price evidence for the exact context; never approve sale.

        Later failures supersede earlier successes. Conflicting same-time checks
        fail closed. Newer discovery evidence triggers re-check. No stacking.
        """
        scope = context(**scope)
        base = scope["base_minor"]
        if scope["shop_code"] not in self._allowed_shops:
            return dict(status="NO_VERIFIED_DISCOUNT", normal_minor=base, effective_minor=base, campaign=None, check_id=None, sale_approved=False)
        now = _time(now)
        max_age = _minor(max_age_seconds, "max_age_seconds", True)
        cutoff = (datetime.fromisoformat(now) - timedelta(seconds=max_age)).isoformat(timespec="microseconds")
        with self._connection() as db:
            rows = db.execute("SELECT id, campaign, checked_at, payload FROM ahc_coupon_checks_v1 WHERE context_id=? AND checked_at<=? ORDER BY checked_at DESC, id", (_id(scope), now)).fetchall()
            observations = db.execute("SELECT campaign, observed_at, payload FROM ahc_coupon_observations_v1 WHERE shop_code=? AND observed_at<=?", (scope["shop_code"], now)).fetchall()
        latest = {}
        for r in observations:
            latest[r["campaign"]] = max(latest.get(r["campaign"], ""), r["observed_at"])
        assessed = {a["campaign"]: a for a in assess_campaigns([json.loads(r["payload"]) for r in observations], now=now)}
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
            if (not _valid_applied_check(check, scope) or r["checked_at"] < cutoff
                    or _time(check["expires_at"]) <= now
                    or latest.get(campaign, "") > r["checked_at"]):
                continue
            a = assessed.get(campaign)
            if a is None or a["campaign_confidence"] in {"EXPIRED", "RETIRED", "CONFLICT", "LIKELY_INVALID"}:
                continue
            if evaluate_eligibility(campaign, scope, product_facts or {},
                                    a["conditions"], now=now)["eligibility"] != "MATCH":
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
        if scope["shop_code"] not in self._allowed_shops:
            return []
        scope_id = _id(scope)
        now_t = _time(now)
        with self._connection() as db:
            obs_rows = db.execute("SELECT payload FROM ahc_coupon_observations_v1 WHERE shop_code=?", (scope["shop_code"],)).fetchall()
            chk_rows = db.execute("SELECT payload FROM ahc_coupon_checks_v1 WHERE context_id=?", (scope_id,)).fetchall()
        
        discoveries = [json.loads(r["payload"]) for r in obs_rows]
        for d in discoveries: d["scope"] = scope
            
        checks = [json.loads(r["payload"]) for r in chk_rows]
        
        assessed = assess_campaigns(discoveries, now=now_t)
        
        evaluated = []
        for a in assessed:
            evaluated.append(evaluate_eligibility(a["campaign"], scope, product_facts, a.get("conditions", {}), now=now_t))
                
        return rank_candidates(assessed, evaluated, checks, discoveries, scope=scope, now=now_t, max_age_seconds=max_age_seconds)
