#!/usr/bin/env python3
"""G-1: auditable A2 size join. Never infer unverified size or department."""
import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

DEPT_DICTIONARY_VERSION = "dept-spec-v1"
DEPT_LABELS = {"men": "Men", "mens": "Men", "men's": "Men",
               "women": "Women", "womens": "Women", "women's": "Women",
               "kids": "Kids", "kid": "Kids", "children": "Kids"}
HOLD_UGG_IDS = {"41707750162638", "42228915372238", "42843176403150"}


def load(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError("invalid CSV header " + str(path))
        rows = list(reader)
        if any(None in row or None in row.values() for row in rows):
            raise ValueError("malformed CSV " + str(path))
        return rows, set(reader.fieldnames)


def require_headers(headers, column_map, required, name):
    for key in required:
        if key not in column_map or column_map[key] not in headers:
            raise ValueError("missing mapped header " + name + "." + key)


def size(value):
    match = re.fullmatch(r"(?:US\s*)?(\d+(?:\.\d+)?)([CY]?)", value.strip().upper())
    if not match:
        raise ValueError("unsupported size " + value)
    number = Decimal(match[1])
    if not number.is_finite() or number <= 0:
        raise ValueError("invalid size " + value)
    return format(number.normalize(), "f") + match[2]


def cm(value):
    if not value.strip():
        return ""
    number = Decimal(value.strip())
    if not number.is_finite() or number <= 0:
        raise ValueError("invalid cm " + value)
    return format(number.normalize(), "f")


def department(row, columns, rules, headers):
    """Resolve only explicit labels or configured exact dictionary entries.

    All nonempty evidence is recorded, including disagreeing evidence.
    """
    evidence = []
    raw = row[columns["department"]].strip()
    if raw:
        label = DEPT_LABELS.get(raw.casefold())
        evidence.append({"rule": "explicit_department", "column": columns["department"],
                         "raw": raw, "resolved": label or ""})
    for rule in rules:
        field = rule["column"]
        if field not in headers:
            raise ValueError("missing department rule header " + field)
        raw = row[field].strip()
        if raw:
            mapping = rule["map"]
            label = mapping.get(raw.casefold(), "")
            evidence.append({"rule": rule["id"], "column": field,
                             "raw": raw, "resolved": label})
    valid = {e["resolved"] for e in evidence if e["resolved"]}
    unknown = any(not e["resolved"] for e in evidence)
    if len(valid) > 1 or (valid and unknown):
        return "", "HOLD_DEPARTMENT_AMBIGUOUS", evidence
    if not valid:
        return "", "HOLD_DEPARTMENT_UNRESOLVED", evidence
    return next(iter(valid)), "", evidence


def validate_rules(rules):
    ids = set()
    for rule in rules:
        if not isinstance(rule, dict) or not all(k in rule for k in ("id", "column", "map")):
            raise ValueError("department rules require id, column, map")
        if not rule["id"] or rule["id"] in ids or not isinstance(rule["map"], dict):
            raise ValueError("duplicate/invalid department rule")
        ids.add(rule["id"])
        normalized = {}
        for raw, label in rule["map"].items():
            if not isinstance(raw, str) or not raw.strip() or label not in ("Men", "Women", "Kids"):
                raise ValueError("invalid department dictionary entry")
            key = raw.casefold()
            if key in normalized and normalized[key] != label:
                raise ValueError("conflicting department dictionary entry")
            normalized[key] = label
        rule["map"] = normalized


def join(a2_path, variants_path, config):
    a2, ah = load(a2_path)
    variants, vh = load(variants_path)
    ac, vc = config["a2_columns"], config["variant_columns"]
    require_headers(ah, ac, ("brand", "department", "size_original", "cm", "source_url"), "a2")
    require_headers(vh, vc, ("sku", "product_id", "variant_id", "brand",
                              "department", "size_original"), "variants")
    if ac.get("scope") and ac["scope"] not in ah:
        raise ValueError("missing scope header " + ac["scope"])
    rules = config.get("department_rules", {})
    if not isinstance(rules, dict):
        raise ValueError("department_rules must be object")
    a_rules, v_rules = rules.get("a2", []), rules.get("variants", [])
    validate_rules(a_rules)
    validate_rules(v_rules)
    charts = defaultdict(list)
    excluded = Counter()
    for row in a2:
        dept, issue, evidence = department(row, ac, a_rules, ah)
        if issue:
            excluded[issue] += 1
            continue
        key = (row[ac["brand"]].strip().upper(), dept, size(row[ac["size_original"]]))
        value = cm(row[ac["cm"]])
        url = row[ac["source_url"]].strip()
        scope = row[ac["scope"]].strip() if ac.get("scope") else ""
        # Keep invalid-provenance entries for row-level HOLD attribution.
        valid = bool(re.fullmatch(r"https://[^\s]+", url)) if value else False
        if value and not valid:
            excluded["HOLD_NO_PROVENANCE"] += 1
        charts[key].append((value, url if valid else "", scope, bool(value and not valid)))

    output = []
    seen = set()
    for row in variants:
        vid = row[vc["variant_id"]].strip()
        if not vid or vid in seen:
            raise ValueError("duplicate/empty variant ID " + vid)
        seen.add(vid)
        sku = row[vc["sku"]].strip()
        pid = row[vc["product_id"]].strip()
        if not sku or not pid:
            raise ValueError("missing identity")
        dept, issue, evidence = department(row, vc, v_rules, vh)
        original = size(row[vc["size_original"]])
        brand = row[vc["brand"]].strip().upper()
        applicable = charts.get((brand, dept, original), []) if not issue else []
        scoped = [(value, url, bad) for value, url, scope, bad in applicable
                  if not scope or scope == pid]
        good = {(value, url) for value, url, bad in scoped if value and not bad}
        values = {value for value, _ in good}
        chosen = ("", "")
        if issue:
            status = issue
        elif len(values) > 1:
            status = "HOLD_CONFLICT"
        elif len(values) == 1:
            chosen = sorted(good)[0]
            status = "MATCHED"
        elif any(bad for _, _, bad in scoped):
            status = "HOLD_NO_PROVENANCE"
        else:
            status = "HOLD_NO_JP_CM" if scoped else "HOLD_NO_CHART"
        if vid in HOLD_UGG_IDS:
            chosen = ("", "")
            status = "HOLD_UGG_INFANT_AMBIGUITY"
        output.append({
            "sku": sku, "product_id": pid, "variant_id": vid,
            "brand": brand, "department": dept, "size_original": original,
            "cm": chosen[0], "source_url": chosen[1], "status": status,
            "source_candidates": str(len(scoped)),
            "excluded_no_provenance": str(sum(bad for _, _, bad in scoped)),
            "department_rule": "|".join(e["rule"] for e in evidence),
            "department_evidence": json.dumps(evidence, ensure_ascii=False, sort_keys=True),
            "department_dictionary_version": DEPT_DICTIONARY_VERSION,
        })
    return output, excluded


FIELDS = ["sku", "product_id", "variant_id", "brand", "department",
          "size_original", "cm", "source_url", "status", "source_candidates",
          "excluded_no_provenance", "department_rule", "department_evidence",
          "department_dictionary_version"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--a2", required=True, type=Path)
    parser.add_argument("--variants", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("output exists")
    config = json.loads(args.config.read_text(encoding="utf-8"))
    rows, excluded = join(args.a2, args.variants, config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    stats = Counter(row["status"] for row in rows)
    print(json.dumps({"total": len(rows), "status": dict(sorted(stats.items())),
                      "excluded_a2": dict(sorted(excluded.items())),
                      "output": str(args.output)}, ensure_ascii=False))
    return 2 if config.get("require_all_matched", False) and any(
        row["status"] != "MATCHED" for row in rows) else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, KeyError, OSError, InvalidOperation, TypeError) as exc:
        sys.exit(str(exc))
