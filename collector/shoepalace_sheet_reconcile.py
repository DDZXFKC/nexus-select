#!/usr/bin/env python3
"""Reconcile a Shoe Palace sheet CSV against one saved raw batch; no live writes."""
import argparse
import csv
import json
from pathlib import Path
from shoepalace_repair import repair, load_reference

def encode(value):
    if value is None:
        return ""
    if isinstance(value, (list, dict, bool)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)

def reconcile(headers, existing, products, variants, product_col, variant_col=None):
    if product_col not in headers or (variant_col and variant_col not in headers):
        raise ValueError("Configured ID column missing from sheet")
    if any(not str(row.get(product_col, "")).strip() for row in existing):
        raise ValueError("Blank sheet product ID; reconcile only data rows")
    by_product = {p["product_id"]: p for p in products}
    by_variant = {(v["product_id"], v["variant_id"]): v for v in variants}
    grouped = {}
    for v in variants:
        grouped.setdefault(v["product_id"], []).append(v)
    fields = ["sp_source_url", "sp_color_name", "sp_color_tags",
              "sp_coupon_tag_codes", "sp_coupon_tag_status",
              "sp_description_ja", "sp_description_ja_status",
              "sp_variant_details"]
    if variant_col:
        fields += ["sp_size_original", "sp_cm", "sp_compare_at_price_minor",
                   "sp_regular_price_minor"]
    output, changes, issues, seen = [], [], [], set()
    for index, old in enumerate(existing, 2):
        pid = str(old[product_col]).strip()
        vid = str(old.get(variant_col, "")).strip() if variant_col else ""
        identity = (pid, vid)
        if identity in seen:
            raise ValueError(f"Duplicate sheet key {identity}; do not guess row identity")
        seen.add(identity)
        new = dict(old)
        p = by_product.get(pid)
        v = by_variant.get(identity) if variant_col else None
        if p is None or (variant_col and v is None):
            issues.append({"row": index, "product_id": pid, "variant_id": vid,
                           "reason": "not_in_raw_batch"})
            output.append(new)
            continue
        updates = {"sp_source_url": p["source_url"], "sp_color_name": p["color_name"],
                   "sp_color_tags": p["color_tags"], "sp_coupon_tag_codes": p["coupon_tag_codes"],
                   "sp_coupon_tag_status": p["coupon_tag_status"],
                   "sp_description_ja": p["description_ja"],
                   "sp_description_ja_status": p["description_ja_status"],
                   "sp_variant_details": [{k: item[k] for k in (
                       "variant_id", "sku", "size_original", "cm", "currency",
                       "price_minor", "compare_at_price_minor", "regular_price_minor",
                       "available", "coupon_application")} for item in grouped.get(pid, [])]}
        if v is not None:
            updates.update({"sp_size_original": v["size_original"], "sp_cm": v["cm"],
                            "sp_compare_at_price_minor": v["compare_at_price_minor"],
                            "sp_regular_price_minor": v["regular_price_minor"]})
        for field, value in updates.items():
            before = old.get(field, "")
            after = encode(value)
            # Derived columns are regenerated, never silently retain stale evidence.
            if before != after:
                changes.append({"row": index, "product_id": pid, "variant_id": vid,
                                "field": field, "before": before, "after": after})
            new[field] = after
        output.append(new)
    for pid in sorted(by_product):
        if not any(k[0] == pid for k in seen):
            issues.append({"row": "", "product_id": pid, "variant_id": "",
                           "reason": "raw_product_not_in_sheet"})
    return headers + [f for f in fields if f not in headers], output, changes, issues

def read_sheet(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        if len(set(headers)) != len(headers) or not all(headers):
            raise ValueError("Duplicate or blank sheet headers")
        rows = list(reader)
        if any(None in row or any(v is None for v in row.values()) for row in rows):
            raise ValueError("Malformed sheet CSV")
        return headers, rows

def write(path, fields, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet", required=True, type=Path)
    parser.add_argument("--product-id-column", required=True)
    parser.add_argument("--variant-id-column")
    parser.add_argument("--raw", required=True, nargs="+", type=Path)
    parser.add_argument("--cm-reference", type=Path)
    parser.add_argument("--ja-reference", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    raw = []
    for path in args.raw:
        raw.extend(json.loads(path.read_text(encoding="utf-8"))["products"])
    products, variants, repair_issues, summary = repair(
        raw, load_reference(args.cm_reference, ["brand","department","size_original","cm"]),
        load_reference(args.ja_reference, ["product_id","description_ja"]))
    headers, old = read_sheet(args.sheet)
    fields, rows, changes, issues = reconcile(headers, old, products, variants,
                                               args.product_id_column, args.variant_id_column)
    args.output.mkdir(parents=True, exist_ok=False)
    write(args.output / "sheet_repaired.csv", fields, rows)
    write(args.output / "changes.csv", ["row","product_id","variant_id","field","before","after"], changes)
    write(args.output / "sheet_issues.csv", ["row","product_id","variant_id","reason"], issues)
    write(args.output / "repair_issues.csv", ["product_id","variant_id","reason"],
          [dict(product_id=p,variant_id=v,reason=r) for p,v,r in repair_issues])
    summary.update(sheet_rows=len(old), changed_cells=len(changes), sheet_issues=len(issues))
    (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))

if __name__ == "__main__":
    main()
