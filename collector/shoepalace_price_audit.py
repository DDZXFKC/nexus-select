#!/usr/bin/env python3
"""Offline source-price verification only. No landed-cost or selling-price calculation."""
import argparse
import csv
import json
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

def cents(value):
    if value is None or value == "":
        return None
    try:
        n = Decimal(str(value))
        if not n.is_finite() or n < 0 or n * 100 != (n * 100).to_integral_value():
            raise ValueError("invalid amount")
        return int(n * 100)
    except (InvalidOperation, ValueError, OverflowError) as exc:
        raise ValueError(f"Invalid monetary value: {value!r}") from exc

def audit(raw, rows, currency_evidence=None):
    source, dup = {}, set()
    for p in raw:
        for v in p.get("variants", []):
            k = (str(p["id"]), str(v["id"]))
            if k in source:
                dup.add(k)
            source[k] = (p, v)
    seen, findings, results = set(), [], []
    for row in rows:
        k = (str(row.get("product_id", "")), str(row.get("variant_id", "")))
        errors, warnings = [], []
        if k in seen:
            errors.append("duplicate_output")
        seen.add(k)
        if k in dup:
            errors.append("duplicate_raw_key")
        pair = source.get(k)
        if pair is None:
            errors.append("missing_raw_variant")
        else:
            p, v = pair
            try:
                price = cents(v.get("price"))
                compare = cents(v.get("compare_at_price"))
                expected = compare if compare is not None and compare > 0 and price is not None and compare >= price else None
                if price is None or price == 0:
                    errors.append("source_price_missing_or_zero")
                for field, value in (("price_minor", price), ("compare_at_price_minor", compare), ("regular_price_minor", expected)):
                    actual = row.get(field)
                    if (actual is not None and type(actual) is not int) or actual != value:
                        errors.append(field + "_mismatch")
                if compare is not None and compare > 0 and price is not None and compare < price:
                    warnings.append("compare_below_current")
            except ValueError:
                errors.append("invalid_source_amount")
            if str(row.get("sku") or "") != str(v.get("sku") or ""):
                errors.append("sku_mismatch")
            tags = sorted({t[5:] for t in p.get("tags", []) if t.startswith("Code_") and t[5:]})
            if row.get("coupon_tag_codes") != tags:
                errors.append("coupon_tag_mismatch")
            if row.get("coupon_application") != "UNKNOWN":
                errors.append("unverified_coupon_application")
            if row.get("currency") != "USD":
                errors.append("currency_label_mismatch")
            if not currency_evidence:
                warnings.append("currency_evidence_pending")
        status = "FAIL" if errors else ("REVIEW" if warnings else "PASS")
        results.append(dict(product_id=k[0], variant_id=k[1], status=status,
                            errors=errors, warnings=warnings))
    for k in sorted(set(source)-seen):
        results.append(dict(product_id=k[0], variant_id=k[1], status="FAIL",
                            errors=["missing_output_variant"], warnings=[]))
    counts = Counter(r["status"] for r in results)
    return {"source_variants":len(source),"output_rows":len(rows),
            "pass":counts["PASS"],"review":counts["REVIEW"],"fail":counts["FAIL"],
            "currency_evidence":currency_evidence,
            "scope":"saved_snapshot_consistency_not_live_checkout_or_tax_verification",
            "results":results}

def audit_sheet(report, repaired, sheet):
    index = {(str(v["product_id"]), str(v["variant_id"])):v for v in repaired}
    seen, issues = set(), []
    fields = ("price_minor","compare_at_price_minor","regular_price_minor","currency")
    for i, row in enumerate(sheet, 2):
        if row.get("Type") != "variation":
            continue
        k = (row.get("sp_product_id",""),row.get("sp_variant_id",""))
        v = index.get(k)
        if k in seen or v is None:
            issues.append({"row":i,"key":k,"reason":"duplicate_or_missing_variant"})
            continue
        seen.add(k)
        for f in fields:
            expected = "" if v.get(f) is None else str(v[f])
            if row.get("sp_"+f) != expected:
                issues.append({"row":i,"key":k,"reason":f+"_mismatch"})
        if row.get("SKU") != str(v.get("sku") or "") or row.get("Parent") != "SP-"+k[0]:
            issues.append({"row":i,"key":k,"reason":"sku_or_parent_mismatch"})
    for k in sorted(set(index)-seen):
        issues.append({"key":k,"reason":"missing_sheet_variant"})
    report["sheet_issues"] = issues
    report["sheet_variants_checked"] = len(seen)
    report["legacy_woo_regular_price"] = "JPY selling price; not compared to USD source price and not validated here"

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw",nargs="+",required=True,type=Path)
    p.add_argument("--repaired",required=True,type=Path)
    p.add_argument("--sheet",type=Path)
    p.add_argument("--currency-evidence",help="Reference to independently verified US-market USD evidence; never guessed")
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    raw=[]
    for f in a.raw:
        raw.extend(json.loads(f.read_text(encoding="utf-8"))["products"])
    repaired=json.loads(a.repaired.read_text(encoding="utf-8"))["variants"]
    report=audit(raw,repaired,a.currency_evidence)
    if a.sheet:
        with a.sheet.open(encoding="utf-8-sig",newline="") as f:
            audit_sheet(report,repaired,list(csv.DictReader(f)))
    with a.output.open("x",encoding="utf-8") as f:
        json.dump(report,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k not in {"results","sheet_issues"}},ensure_ascii=False))
    return 1 if report["fail"] or report.get("sheet_issues") else (2 if report["review"] else 0)

if __name__ == "__main__":
    raise SystemExit(main())
