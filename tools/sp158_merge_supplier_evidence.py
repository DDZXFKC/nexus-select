"""Merge reviewable Shoe Palace identity evidence into the 158 Woo SKU snapshot.

No Woo writes, no claims about stock, current price, or sale readiness.
Merges new Shopify read-only evidence with independently checked legacy 77.
All identity conflicts fail closed; original Woo IDs/SKUs never change.
"""
from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WOO = ROOT / "data/xserver-export/sp-variation-skus-2026-11-21.csv"
URLS = ROOT / "data/xserver-export/sp158-source-urls-from-sheet-2026-11-21.csv"
LEGACY = ROOT / "data/xserver-export/supplier-url-evidence-sample-2026-11-21.csv"
COLUMNS = [
    "product_id", "parent_sku", "variation_id", "variation_sku",
    "supplier_product_id", "source_url", "supplier_variant_id",
    "supplier_variant_sku", "evidence_timestamp_utc", "match_status",
    "reason_codes", "evidence_source"
]
PRODUCT_COLUMNS = [
    "product_id", "parent_sku", "supplier_product_id", "source_url",
    "total_variations", "pass_variations", "hold_variations",
    "product_status", "reason_codes"
]


def read_csv(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def index_unique(rows, keys, label):
    result = {}
    for row in rows:
        key = tuple(row[k] for k in keys)
        if key in result:
            raise ValueError(f"Duplicate {label} {key}")
        result[key] = row
    return result


def validated_identity(row, canonical, *, source):
    if not row:
        return None, "NO_EVIDENCE"
    if source == "LIVE":
        if row.get("status") != "PASS":
            return None, row.get("reason") or "LIVE_HOLD"
        variation_id = row.get("supplier_variant_id", "")
        sku = row.get("supplier_variant_sku", "")
        observed = row.get("observed_at_utc", "")
        provenance = row.get("source_sha256", "")
        if not re.fullmatch(r"[0-9a-f]{64}", provenance):
            return None, "MISSING_BODY_HASH"
        proof = "SP_LIVE_SHOPIFY_BODY_SHA256:" + provenance
    elif source == "LEGACY":
        if row.get("status") != "verified":
            return None, "LEGACY_NOT_VERIFIED"
        variation_id = row.get("merchant_variant_id", "")
        sku = row.get("merchant_variant_sku", "")
        observed = row.get("sku_verified_at_utc", "")
        if not row.get("sku_evidence"):
            return None, "LEGACY_SKU_EVIDENCE_MISSING"
        proof = "SP_LEGACY_SKU_REVIEW:" + observed
    else:
        raise ValueError(source)
    if (row.get("product_id") != canonical["product_id"] or
        row.get("variation_id") != canonical["variation_id"] or
        row.get("supplier_product_id") != canonical["supplier_product_id"] or
        row.get("source_url") != canonical["source_url"] or
        sku != canonical["variation_sku"] or
        not variation_id.isdecimal() or not observed):
        return None, source + "_IDENTITY_MISMATCH"
    return {
        "supplier_variant_id": variation_id,
        "supplier_variant_sku": sku,
        "evidence_timestamp_utc": observed,
        "evidence_source": proof
    }, ""


def reconcile(live, woo=None, urls=None, legacy=None):
    woo = read_csv(WOO) if woo is None else woo
    urls = read_csv(URLS) if urls is None else urls
    legacy = read_csv(LEGACY) if legacy is None else legacy

    url_map = index_unique(urls, ["supplier_product_id"], "supplier URL")
    live_map = index_unique(live, ["product_id", "variation_id"], "live evidence")
    old_map = index_unique(legacy, ["product_id", "variation_id"], "legacy evidence")
    woo_map = index_unique(woo, ["product_id", "variation_id"], "Woo variation")
    if woo is not None and len(woo_map) != 1713:
        raise ValueError(f"Expected exactly 1713 Woo variations, got {len(woo_map)}")
    parents = set()
    result = []

    # Snapshot integrity: no evidence for unknown Woo variation may be silently accepted.
    for key in live_map:
        if key not in woo_map:
            raise ValueError("Supplier evidence has unknown Woo key: " + str(key))
    for original in woo:
        product_id = original["product_id"]
        parent_sku = original["parent_sku"]
        if not re.fullmatch(r"SP-[0-9]+", parent_sku):
            raise ValueError("Invalid Woo supplier parent SKU: " + parent_sku)
        supplier_id = parent_sku[3:]
        parents.add((product_id, supplier_id))
        mapped = url_map.get((supplier_id,))
        if mapped is None:
            raise ValueError("Source URL missing for " + supplier_id)
        url = mapped["source_url"]
        canonical = dict(product_id=product_id, parent_sku=parent_sku,
                         variation_id=original["variation_id"], variation_sku=original["variation_sku"],
                         supplier_product_id=supplier_id, source_url=url)
        if not canonical["variation_sku"]:
            raise ValueError("Empty Woo variation SKU")
        key = (product_id, original["variation_id"])
        matched_new, reason_new = validated_identity(live_map.get(key), canonical, source="LIVE")
        matched_old, reason_old = validated_identity(old_map.get(key), canonical, source="LEGACY")
        reason = ""
        accepted = None
        if matched_new and matched_old:
            if matched_new["supplier_variant_id"] != matched_old["supplier_variant_id"]:
                reason = "CONFLICT_LIVE_VS_LEGACY_SUPPLIER_VARIANT_ID"
            else:
                accepted = matched_new
        elif matched_new:
            accepted = matched_new
        elif matched_old:
            # If live observation explicitly says SKU is ambiguous/mismatched,
            # do not silently reuse old proof of identity.
            if key in live_map and reason_new in (
                "SUPPLIER_SKU_AMBIGUOUS", "SUPPLIER_PRODUCT_ID_MISMATCH",
                "LIVE_IDENTITY_MISMATCH"):
                reason = reason_new
            else:
                accepted = matched_old
        else:
            reason = reason_new if key in live_map else reason_old
        if not accepted:
            reason = reason or reason_new or reason_old or "NO_VERIFIED_SUPPLIER_VARIANT"
        result.append({
            **canonical, "supplier_variant_id":accepted["supplier_variant_id"] if accepted else "",
            "supplier_variant_sku":accepted["supplier_variant_sku"] if accepted else "",
            "evidence_timestamp_utc":accepted["evidence_timestamp_utc"] if accepted else "",
            "match_status":"PASS" if accepted else "HOLD",
            "reason_codes":"" if accepted else reason,
            "evidence_source":accepted["evidence_source"] if accepted else "",
        })
    if len(parents) != 158:
        raise ValueError(f"Expected 158 Woo parents, got {len(parents)}")

    # An individual merchant variant may back exactly one Woo variation.
    # Even if independent SKU fields appear to match, duplicate supplier
    # IDs for different Woo variation keys are ambiguous and must HOLD.
    merchant_ids = defaultdict(list)
    for item in result:
        if item["match_status"] == "PASS":
            merchant_ids[(item["supplier_product_id"], item["supplier_variant_id"])].append(item)
    for candidates in merchant_ids.values():
        if len(candidates) > 1:
            for item in candidates:
                item["match_status"] = "HOLD"
                item["reason_codes"] = "DUPLICATE_SUPPLIER_VARIANT_ID"
                item["supplier_variant_id"] = ""
                item["supplier_variant_sku"] = ""
                item["evidence_timestamp_utc"] = ""
                item["evidence_source"] = ""

    grouped = defaultdict(list)
    for r in result:
        grouped[(r["product_id"], r["parent_sku"], r["supplier_product_id"], r["source_url"])].append(r)
    products = []
    for (pid, parent, supplier, url), variants in grouped.items():
        yes = sum(v["match_status"] == "PASS" for v in variants)
        hold = len(variants) - yes
        reasons = sorted({v["reason_codes"] for v in variants if v["reason_codes"]})
        products.append({
            "product_id":pid,"parent_sku":parent,"supplier_product_id":supplier,
            "source_url":url,"total_variations":str(len(variants)),
            "pass_variations":str(yes),"hold_variations":str(hold),
            "product_status":"PASS" if hold == 0 else "PARTIAL" if yes else "HOLD",
            "reason_codes":";".join(reasons)
        })
    if len(products) != 158 or len(result) != 1713:
        raise ValueError("Unexpected final coverage")
    return result, products


def save(path, fields, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", required=True)
    parser.add_argument("--variations", required=True)
    parser.add_argument("--products", required=True)
    args = parser.parse_args()
    matches, products = reconcile(read_csv(args.live))
    save(args.variations, COLUMNS, matches)
    save(args.products, PRODUCT_COLUMNS, products)
    print("Products", len(products), "full PASS", sum(p["product_status"] == "PASS" for p in products),
          "partial", sum(p["product_status"] == "PARTIAL" for p in products),
          "HOLD", sum(p["product_status"] == "HOLD" for p in products))
    print("Variations", len(matches), "PASS", sum(r["match_status"] == "PASS" for r in matches),
          "HOLD", sum(r["match_status"] == "HOLD" for r in matches))
    print("Buyer authorization: NO. Stock and landed cost are not confirmed.")


if __name__ == "__main__":
    main()
