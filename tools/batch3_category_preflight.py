#!/usr/bin/env python3
"""Batch3 E-1 category preflight. Pure read-only input; fail closed."""
import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

VERSION = "batch3-e1-preflight-v1"
FIELDS = ["sku", "brand", "department", "source_product_type", "default_category_id",
          "selected_category_id", "category_source", "evidence_ref", "preflight_status", "reason"]
TYPE_WARNING = re.compile(r"\b(?:slipper|slippers|sandal|sandals|slide|slides)\b", re.I)
BOOT_WARNING = re.compile(r"\b(?:boots?|booties)\b", re.I)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError("invalid CSV headers: " + str(path))
        rows = list(reader)
    if any(None in row or None in row.values() for row in rows):
        raise ValueError("malformed CSV " + str(path))
    return rows


def unique(rows, key):
    out = {}
    for row in rows:
        value = row.get(key, "").strip()
        if not value or value in out:
            raise ValueError("empty/duplicate " + key + ": " + value)
        out[value] = row
    return out


def source_type(row):
    return row.get("source_product_type", "").strip() or row.get("Name", "").strip()


def canonical_category(value, known):
    value = str(value).strip()
    return value if value and value in known else ""


def run(pool_path, selection_path, categories_path, rules_path, expected_hash):
    if not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
        raise ValueError("expected pool hash must be full lowercase sha256")
    actual = digest(pool_path)
    if actual != expected_hash:
        raise ValueError("pool sha256 mismatch: expected " + expected_hash + " got " + actual)
    pool_rows = read(pool_path)
    if len(pool_rows) != 163:
        raise ValueError("expected exactly 163 pool rows, got " + str(len(pool_rows)))
    pool = unique(pool_rows, "SKU")
    selected_rows = read(selection_path)
    selected = unique(selected_rows, "SKU")
    if len(selected) != 10:
        raise ValueError("expected ten distinct selected SKUs")
    master_rows = read(categories_path)
    master = unique(master_rows, "category_id")
    # The master must give a type, not merely an opaque category number.
    known = {key: row for key, row in master.items() if row.get("product_type", "").strip()}
    cfg = json.loads(rules_path.read_text(encoding="utf-8"))
    version = cfg.get("version", "")
    if not version or not cfg.get("dictionary_version"):
        raise ValueError("category rules/dictionary versions required")
    overrides = cfg.get("category_overrides_by_sku", {})
    dictionary = cfg.get("category_dictionary", [])
    defaults = cfg.get("brand_dept_defaults", [])
    if not isinstance(overrides, dict) or not isinstance(dictionary, list) or not isinstance(defaults, list):
        raise ValueError("invalid rules structure")
    for obj in list(overrides.values()) + dictionary + defaults:
        if not isinstance(obj, dict):
            raise ValueError("invalid rule entry")
    by_dictionary = {}
    for entry in dictionary:
        key = (entry["brand"], entry["department"], entry["source_product_type"].casefold())
        if key in by_dictionary:
            raise ValueError("duplicate dictionary rule: " + str(key))
        by_dictionary[key] = entry
    by_default = {}
    for entry in defaults:
        key = (entry["brand"], entry["department"])
        if key in by_default:
            raise ValueError("duplicate default: " + str(key))
        by_default[key] = entry

    counts = Counter((r.get("brand", "").strip(), r.get("department", "").strip())
                     for r in pool_rows)
    audit = []
    for sku, s in selected.items():
        row = pool.get(sku)
        result = dict.fromkeys(FIELDS, "")
        result["sku"] = sku
        if row is None:
            result.update(preflight_status="HOLD_CATEGORY_REVIEW", reason="unknown_sku")
            audit.append(result)
            continue
        brand = row.get("brand", "").strip()
        dept = row.get("department", "").strip()
        ptype = source_type(row)
        result.update(brand=brand, department=dept, source_product_type=ptype)
        override = overrides.get(sku)
        exact = by_dictionary.get((brand, dept, ptype.casefold()))
        default = by_default.get((brand, dept))
        result["default_category_id"] = str(default.get("category_id", "")) if default else ""
        choices = [(label, item) for label, item in (("exception_map", override),
                   ("dictionary", exact), ("brand_dept_default", default)) if item is not None]
        if not choices:
            result.update(preflight_status="HOLD_CATEGORY_REVIEW", reason="no_approved_category_rule")
            audit.append(result)
            continue
        # A conflicting explicit mapping must not be silently resolved by priority.
        ids = {str(item.get("category_id", "")) for _, item in choices}
        if len(ids) > 1 and override is None:
            result.update(preflight_status="HOLD_CATEGORY_REVIEW", reason="contradictory_rules")
            audit.append(result)
            continue
        label, chosen = choices[0]
        cat = canonical_category(chosen.get("category_id", ""), known)
        result.update(selected_category_id=cat, category_source=label,
                      evidence_ref=str(chosen.get("evidence_ref", "")))
        reasons = []
        if not cat:
            reasons.append("unknown_category_id")
        if not chosen.get("evidence_ref") or not chosen.get("verified_on"):
            reasons.append("missing_category_evidence")
        if label == "brand_dept_default":
            try:
                verified = date.fromisoformat(chosen["verified_on"])
                if verified > date.today():
                    reasons.append("future_verification_date")
            except (KeyError, ValueError):
                reasons.append("invalid_verification_date")
            if chosen.get("verified_pool_sha256") != expected_hash:
                reasons.append("default_wrong_pool_snapshot")
            if chosen.get("verified_count") != counts[(brand, dept)]:
                reasons.append("default_expired_count")
            if not chosen.get("all_items_same_category_confirmed", False):
                reasons.append("default_not_all_verified")
        if cat:
            official_type = known[cat]["product_type"].strip().casefold()
            if TYPE_WARNING.search(ptype) and official_type in ("boot", "boots"):
                reasons.append("sandal_slipper_vs_boot_category")
            if BOOT_WARNING.search(ptype) and official_type in ("sandal", "sandals"):
                reasons.append("boot_vs_sandal_category")
            if ptype and official_type not in ("boot", "boots", "sandal", "sandals", "shoes", "sneakers", "slipper", "slippers", "other"):
                reasons.append("unknown_master_product_type")
        # Selected-row data must be from the exact frozen pool; prevent stale edits.
        for field in ("brand", "department", "source_product_type"):
            if field in s and s[field].strip() and s[field].strip() != row.get(field, "").strip():
                reasons.append("selection_pool_mismatch_" + field)
        result["preflight_status"] = "HOLD_CATEGORY_REVIEW" if reasons else "PASS"
        result["reason"] = "|".join(sorted(set(reasons)))
        audit.append(result)
    return audit, {"preflight_version": VERSION, "rules_version": version,
                   "dictionary_version": cfg["dictionary_version"],
                   "pool_sha256": actual, "pool_count": len(pool_rows),
                   "selection_sha256": digest(selection_path),
                   "category_master_sha256": digest(categories_path),
                   "rules_sha256": digest(rules_path),
                   "selected_count": len(selected),
                   "unreferenced_overrides": sorted(set(overrides) - set(selected)),
                   "pass_count": sum(r["preflight_status"] == "PASS" for r in audit),
                   "hold_count": sum(r["preflight_status"] != "PASS" for r in audit)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pool", required=True, type=Path)
    p.add_argument("--selection", required=True, type=Path)
    p.add_argument("--category-master", required=True, type=Path)
    p.add_argument("--rules", required=True, type=Path)
    p.add_argument("--pool-sha256", required=True)
    p.add_argument("--output", required=True, type=Path, help="new output directory")
    a = p.parse_args()
    audit, manifest = run(a.pool, a.selection, a.category_master, a.rules, a.pool_sha256)
    # Output must not exist; never overwrite a previous audit.
    a.output.mkdir(parents=True, exist_ok=False)
    with (a.output / "preflight.csv").open("x", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, FIELDS)
        writer.writeheader()
        writer.writerows(audit)
    manifest["preflight_csv_sha256"] = digest(a.output / "preflight.csv")
    (a.output / "preflight_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))
    return 0 if not manifest["hold_count"] else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        sys.exit(str(exc))
