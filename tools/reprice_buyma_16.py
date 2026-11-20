#!/usr/bin/env python3
"""Owner owner 16% BUYMA price repricer (read-only sources).

No price is guessed: exact USD source + approved cost components required.
Inputs are never overwritten. Output paths must be new.
"""
import argparse
import csv
import json
import math
from decimal import Decimal, ROUND_CEILING
from pathlib import Path

USD_TO_JPY = Decimal("158")
CARD_FACTOR = Decimal("1.02")
FIXED_JPY = Decimal("2200") + Decimal("1500") + Decimal("60")
OLD_DIVISOR = Decimal("0.755")
NEW_DIVISOR = Decimal("0.785")


def price(usd, divisor=NEW_DIVISOR):
    value = Decimal(str(usd))
    if not value.is_finite() or value <= 0:
        raise ValueError("missing or invalid USD")
    exact_cost = value * USD_TO_JPY * CARD_FACTOR + FIXED_JPY
    final = (exact_cost / divisor / Decimal(100)).to_integral_value(
        rounding=ROUND_CEILING) * Decimal(100)
    return int(final), exact_cost


def read(path):
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError("bad CSV header " + str(path))
        rows = list(reader)
        if any(None in row or None in row.values() for row in rows):
            raise ValueError("bad CSV row " + str(path))
        return list(reader.fieldnames), rows


def write(path, headers, rows):
    if path.exists():
        raise ValueError("output exists " + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)


def mapping_from_margin(path):
    headers, rows = read(path)
    required = {"sku", "usd", "cost_jpy", "price_jpy"}
    if not required.issubset(headers):
        raise ValueError("margin missing columns " + str(required - set(headers)))
    result = {}
    audit = []
    for row in rows:
        sku = row["sku"].strip()
        if not sku or sku in result:
            raise ValueError("missing/duplicate SKU " + sku)
        before, exact_cost = price(row["usd"], OLD_DIVISOR)
        after, _ = price(row["usd"])
        if int(row["price_jpy"]) != before:
            raise ValueError("old price mismatch " + sku)
        if int(row["cost_jpy"]) != round(float(exact_cost)):
            raise ValueError("old cost mismatch " + sku)
        result[sku] = (before, after)
        audit.append({"sku": sku, "price_old_jpy": before,
                      "price_19_jpy": after, "change_jpy": after - before})
    return result, audit


def reprice_margin(source, dest):
    mapping, audit = mapping_from_margin(source)
    fields, rows = read(source)
    for row in rows:
        new = mapping[row["sku"]][1]
        row["price_jpy"] = str(new)
        row["formula_price_jpy"] = str(new)
        row["price_match"] = "yes"
        gross = new - int(row["cost_jpy"])
        row["gross_profit_jpy"] = str(gross)
        row["margin_pct"] = f"{gross / new * 100:.1f}"
    write(dest, fields, rows)
    return audit


def reprice_linked(source, dest, mapping, key, price_field, allow_unmapped=False):
    fields, rows = read(source)
    if key not in fields or price_field not in fields:
        raise ValueError("missing price/key columns")
    changed, unmatched = 0, []
    for row in rows:
        sku = row[key].strip()
        if sku not in mapping:
            unmatched.append(sku)
            continue
        old, new = mapping[sku]
        if row[price_field].strip() != str(old):
            raise ValueError("linked old price mismatch " + sku)
        row[price_field] = str(new)
        changed += 1
    if unmatched and not allow_unmapped:
        raise ValueError("no approved cost for SKUs: " + repr(unmatched[:12]))
    write(dest, fields, rows)
    return {"total": len(rows), "repriced": changed, "unmapped": len(unmatched),
            "unmapped_skus": unmatched}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--margin", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--mode", choices=["margin", "linked"], required=True)
    parser.add_argument("--linked", type=Path, help="list/items source for linked mode")
    parser.add_argument("--key", default="sku")
    parser.add_argument("--field", default="price_jpy")
    parser.add_argument("--allow-unmapped", action="store_true",
                        help="retain explicitly excluded non-saleable rows; report IDs")
    args = parser.parse_args()
    if args.mode == "margin":
        evidence = reprice_margin(args.margin, args.output)
        print(json.dumps({"rows": len(evidence), "changed": sum(
            r["price_old_jpy"] != r["price_19_jpy"] for r in evidence)}, ensure_ascii=False))
    else:
        if args.linked is None:
            raise ValueError("linked input required")
        mapping, _ = mapping_from_margin(args.margin)
        result = reprice_linked(args.linked, args.output, mapping, args.key,
                                args.field, args.allow_unmapped)
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
