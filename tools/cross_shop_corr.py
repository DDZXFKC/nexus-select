#!/usr/bin/env python3
"""GLM-approved SP×FL correlation layer. Never changes identity_key.

Stages: (1) corr contract, (2) crosswalk + disposition, (3) attach to cost
eligibility and colorway-level winner selection. No scraping or listing writes.
All SP candidates MUST come from the full pinned source corpus, not sellable-only.
"""
import argparse
import csv
import json
import re
import unicodedata
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

VERSION = "corr-glm-final-nike-fl-v1"
HOKA_UGG = frozenset(("HOKA", "UGG"))
BRANDS = frozenset(("HOKA", "UGG", "VANS", "NIKE"))
NIKE_SKU = re.compile(r"^[A-Z][A-Z0-9]{5}-[0-9]{3}$")
NIKE_FL = re.compile(r"^[A-Z][0-9]{7}$")
HOKA_FL = re.compile(r"^(\d{3,})([A-Z]{2,})$")
NUMERIC = re.compile(r"^\d+$")
CANONICAL_BRANDS = {"HOKA": "HOKA", "HOKA ONE ONE": "HOKA",
                    "UGG": "UGG", "VANS": "VANS", "NIKE": "NIKE"}
# Fixed manually confirmed pairing, not a general truncation rule.
MANUAL_SEED = ({"brand": "VANS", "fl_code": "00ZB8CD", "sp_style": "ZB8CDA",
                "sp_color": "", "match_type": "MANUAL_TRUNCATED",
                "evidence_note": "GLM confirmed ZB8CDA↔00ZB8CD",
                "created_at": "2026-11-20"},)
CORR_FIELDS = ("brand", "fl_code", "status", "sp_style", "sp_color",
               "sp_source_id", "rule", "matched_key", "candidate_count",
               "tags", "hold_reason_codes", "evidence_tier", "notes")
HOLD = {"HOLD_AMBIG", "HOLD_SHORT_KEY", "HOLD_COLLISION", "HOLD_NO_COLOR",
        "HOLD_LEGACY_NUMERIC", "HOLD_TRUNCATED", "HOLD_MANUAL_INVALID",
        "HOLD_NOT_SELLABLE", "HOLD_UNVERIFIED_FORMAT", "HOLD_RULE_SUSPENDED"}
SEPARATOR_CHARS = "-‐–−ー"


def _nfkc(raw):
    return unicodedata.normalize("NFKC", str(raw or "")).strip().upper()


def brand_norm(raw):
    key = " ".join(_nfkc(raw).split())
    if key not in CANONICAL_BRANDS:
        raise ValueError("unknown approved brand alias: " + str(raw))
    return CANONICAL_BRANDS[key]


def plain_code(raw):
    """For HOKA/UGG/Vans codes only. No cast to int or guessed suffix removal."""
    return _nfkc(raw)


def nike_normalize(raw, keep_hyphen=False):
    """NFKC, uppercase, remove whitespace and specified hyphen variants only."""
    value = _nfkc(raw)
    value = re.sub(r"\s+", "", value)
    value = "".join("-" if x in SEPARATOR_CHARS else x for x in value)
    return value if keep_hyphen else value.replace("-", "")


def nike_k1(sku):
    """Return derived Nike K1 ONLY for a gated current-generation SKU."""
    form = nike_normalize(sku, keep_hyphen=True)
    if not NIKE_SKU.fullmatch(form):
        return None
    k1 = form.replace("-", "")[1:]
    return k1 if NIKE_FL.fullmatch(k1) else None


def nike_k2(k1):
    return k1[-7:] if k1 and NIKE_FL.fullmatch(k1) else None


def vans_strip_one(raw):
    code = plain_code(raw)
    for prefix in ("VN", "00", "V", "0"):
        if code.startswith(prefix):
            return code[len(prefix):]
    return code


def parse_fl(brand, raw):
    """Return (route, core, color), or a guarded exception reason."""
    code = plain_code(raw)
    if not code:
        return ("HOLD_NO_COLOR", "", "")
    if brand in HOKA_UGG:
        m = HOKA_FL.fullmatch(code)
        if m:
            return ("TAIL", m.group(1), m.group(2))
        if NUMERIC.fullmatch(code):
            return ("HOLD_LEGACY_NUMERIC", "", "")
        return ("HOLD_NO_COLOR", "", "")
    if brand == "VANS":
        if NUMERIC.fullmatch(code):
            return ("HOLD_LEGACY_NUMERIC", "", "")
        return ("VANS", vans_strip_one(code), "")
    if brand == "NIKE":
        norm = nike_normalize(raw)
        if NIKE_FL.fullmatch(norm):
            return ("NIKE", norm, "")
        return ("HOLD_UNVERIFIED_FORMAT", "", "")
    return ("HOLD_UNVERIFIED_FORMAT", "", "")


def sp_parts(row):
    brand = brand_norm(row["brand"])
    style = plain_code(row["style"])
    color = plain_code(row.get("color", ""))
    if brand == "NIKE":
        k1 = nike_k1(row["style"])
        return brand, plain_code(row["style"]), "", k1
    if not style:
        raise ValueError("SP style absent; source id=" + row.get("source_id", ""))
    if brand in HOKA_UGG and not color:
        raise ValueError("SP color absent; full corpus must include actual color")
    return brand, style, color, None


def canonical_sp(rows):
    """Validate corpus (includes unsellable), retaining every SKU/colorway."""
    out, seen = [], set()
    for raw in rows:
        row = dict(raw)
        for key in ("brand", "style", "source_id", "sellable"):
            if key not in row:
                raise ValueError("SP missing " + key)
        brand, style, color, k1 = sp_parts(row)
        source_id = str(row["source_id"]).strip()
        if not source_id or source_id in seen:
            raise ValueError("missing or duplicated full-corpus SP source ID")
        seen.add(source_id)
        if str(row["sellable"]).strip().lower() not in ("1", "0", "true", "false"):
            raise ValueError("SP sellable must be 0/1")
        out.append({**row, "_brand": brand, "_style": style, "_color": color,
                    "_k1": k1, "_sellable": str(row["sellable"]).strip().lower() in ("1", "true")})
    if not out:
        raise ValueError("full SP source corpus is empty")
    return out


def build_index(rows):
    """Use FULL SP corpus. Distinct source IDs are kept to detect collisions."""
    idx = defaultdict(list)
    for row in canonical_sp(rows):
        if row["_brand"] in HOKA_UGG:
            idx[("TAIL", row["_brand"], row["_color"])].append(row)
        elif row["_brand"] == "VANS":
            idx[("VANS", row["_brand"], row["_style"])].append(row)
        elif row["_k1"]:
            idx[("NIKE", row["_brand"], row["_k1"])].append(row)
    for k in idx:
        idx[k].sort(key=lambda r: r["source_id"])
    return idx


def base_result(fl):
    brand = brand_norm(fl["brand"])
    code = plain_code(fl["code"])
    return dict(brand=brand, fl_code=code, status="NO_MATCH", sp_style="",
                sp_color="", sp_source_id="", rule="", matched_key="",
                candidate_count=0, tags="", hold_reason_codes="", evidence_tier="",
                notes="")


def mark(row, status, notes=""):
    row["status"] = status
    row["hold_reason_codes"] = status if status in HOLD else ""
    row["notes"] = notes
    return row


def _manual_index(entries):
    table = {}
    for item in entries:
        brand, fl_code = brand_norm(item["brand"]), plain_code(item["fl_code"])
        key = (brand, fl_code)
        if key in table:
            raise ValueError("duplicate manual mapping")
        if item["match_type"] not in ("MANUAL_TRUNCATED", "NAME_CONFIRMED"):
            raise ValueError("invalid manual confirmation")
        if not item.get("evidence_note") or not item.get("created_at"):
            raise ValueError("manual mapping lacks confirmation evidence")
        table[key] = dict(item)
    return table


def correlate(fl_rows, sp_rows, manual=MANUAL_SEED, suspended_nike=False):
    idx = build_index(sp_rows)
    full = [item for values in idx.values() for item in values]
    by_style = defaultdict(list)
    for row in full:
        by_style[(row["_brand"], row["_style"], row["_color"])].append(row)
    table = _manual_index(manual)
    out = []
    for fl in fl_rows:
        for req in ("brand", "code", "source_id"):
            if req not in fl:
                raise ValueError("FL missing " + req)
        result = base_result(fl)
        brand, code = result["brand"], result["fl_code"]
        manual_entry = table.get((brand, code))
        if manual_entry:
            matches = by_style.get((brand, plain_code(manual_entry["sp_style"]),
                                    plain_code(manual_entry.get("sp_color", ""))), [])
            # For Vans, manual seed style+color is one literal full SP code.
            result.update(rule=manual_entry["match_type"], matched_key="MANUAL",
                          candidate_count=len(matches))
            if len(matches) == 1 and matches[0]["_sellable"]:
                chosen = matches[0]
                result.update(status="AUTO", sp_style=chosen["_style"],
                              sp_color=chosen["_color"], sp_source_id=chosen["source_id"],
                              notes=manual_entry["evidence_note"])
            else:
                mark(result, "HOLD_MANUAL_INVALID",
                     "manual mapping target absent, ambiguous or not sellable in full corpus")
            out.append(result)
            continue
        route, core, color = parse_fl(brand, fl["code"])
        if route.startswith("HOLD"):
            mark(result, route)
            out.append(result)
            continue
        if route == "NIKE" and suspended_nike:
            mark(result, "HOLD_RULE_SUSPENDED", "first-party counterexample stop")
            out.append(result)
            continue
        key = (route, brand, color if route == "TAIL" else core)
        candidates = idx.get(key, [])
        if route == "TAIL":
            candidates = [item for item in candidates if item["_style"].endswith(core)]
        result["candidate_count"] = len(candidates)
        result["rule"] = {"TAIL": "glm_tail_v1", "VANS": "vans_prefix_v1",
                          "NIKE": "nike_fl_v1"}[route]
        result["matched_key"] = (core + color) if route == "TAIL" else core
        if route == "NIKE":
            result["evidence_tier"] = str(fl.get("evidence_tier", "")).strip()
        if len(candidates) > 1:
            mark(result, "HOLD_AMBIG", "full SP corpus has multiple candidates")
        elif not candidates:
            mark(result, "NO_MATCH")
        else:
            chosen = candidates[0]
            if not chosen["_sellable"]:
                mark(result, "HOLD_NOT_SELLABLE", "full corpus candidate currently not sellable")
            elif route == "TAIL" and len(core) + len(color) < 7:
                mark(result, "HOLD_SHORT_KEY", "core plus color code below seven characters")
            else:
                tags = []
                if route == "TAIL" and len(core) == 3:
                    tags.append("TAIL3")
                if str(fl.get("name", "")).strip() and str(chosen.get("name", "")).strip():
                    if _nfkc(fl["name"]) != _nfkc(chosen["name"]):
                        tags.append("ADV_NAME_NOTE")
                if route == "TAIL" and len(code) >= 9:
                    tags.append("LOG_FL_CODE_LONG")
                result.update(status="AUTO", sp_style=chosen["_style"],
                              sp_color=chosen["_color"], sp_source_id=chosen["source_id"],
                              tags="|".join(tags))
        out.append(result)
    # Entire run collision: none of the FL records pointing to same SP may AUTO.
    by_sp = defaultdict(list)
    for r in out:
        if r["status"] == "AUTO":
            by_sp[r["sp_source_id"]].append(r)
    for group in by_sp.values():
        if len(group) > 1:
            for row in group:
                mark(row, "HOLD_COLLISION", "multiple FL source rows map to one SP row")
    return out


def join_adoption(corr_rows, fl_rows, sp_rows):
    """Stage 3: pair eligible colorway offers; do not publish or infer missing costs."""
    fl_map = {str(r["source_id"]): r for r in fl_rows}
    sp_map = {str(r["source_id"]): r for r in sp_rows}
    output = []
    for corr, fl in zip(corr_rows, fl_rows):
        if corr["status"] != "AUTO":
            output.append({**corr, "adoption": "HOLD_OR_UNMATCHED",
                           "adoption_reason": corr["hold_reason_codes"] or "NO_MATCH",
                           "winner_shop": "", "winner_source_id": ""})
            continue
        sp = sp_map.get(corr["sp_source_id"])
        if not sp:
            raise ValueError("corr SP source not found")
        offers = [("FL", fl), ("SP", sp)]
        accepted, problems = [], []
        for shop, offer in offers:
            if str(offer.get("cost_calculated", "")) != "1":
                problems.append(shop + ":cost_uncalculated")
                continue
            if str(offer.get("cost_verified", "")) != "1":
                problems.append(shop + ":total_unverified")
                continue
            if str(offer.get("procurement_unit", "")) != "COLORWAY_ONE_UNIT":
                problems.append(shop + ":unit_unverified")
                continue
            try:
                amount = Decimal(str(offer.get("procurement_total_jpy", "")))
                if not amount.is_finite() or amount <= 0:
                    raise InvalidOperation
            except (InvalidOperation, ValueError):
                problems.append(shop + ":total_unverified")
                continue
            accepted.append((amount, {"SP": 0, "FL": 1}[shop],
                             str(offer["source_id"]), shop))
        if not accepted:
            output.append({**corr, "adoption": "HOLD",
                           "adoption_reason": "|".join(problems),
                           "winner_shop": "", "winner_source_id": ""})
        else:
            winner = sorted(accepted)[0]
            output.append({**corr, "adoption": "SELECTED",
                           "adoption_reason": "|".join(problems),
                           "winner_shop": winner[3], "winner_source_id": winner[2]})
    return output


def load_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    dest = Path(path)
    if dest.exists():
        raise ValueError("output must be a new file (no overwrite): " + str(dest))
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("x", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    p = argparse.ArgumentParser(description=VERSION)
    p.add_argument("--sp-full-corpus", required=True)
    p.add_argument("--fl", required=True)
    p.add_argument("--manual")
    p.add_argument("--out", required=True)
    p.add_argument("--adoption-out")
    p.add_argument("--nike-suspended", action="store_true")
    a = p.parse_args()
    sp, fl = load_csv(a.sp_full_corpus), load_csv(a.fl)
    manual = load_csv(a.manual) if a.manual else MANUAL_SEED
    corr = correlate(fl, sp, manual, a.nike_suspended)
    write_csv(a.out, corr, CORR_FIELDS)
    if a.adoption_out:
        rows = join_adoption(corr, fl, sp)
        write_csv(a.adoption_out, rows, CORR_FIELDS + ("adoption", "adoption_reason",
                                                   "winner_shop", "winner_source_id"))
    print(json.dumps({"version": VERSION, "SP_FULL_CORPUS": len(sp), "FL": len(fl),
                      "statuses": {status: sum(r["status"] == status for r in corr)
                                   for status in sorted({r["status"] for r in corr})}},
                     ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
