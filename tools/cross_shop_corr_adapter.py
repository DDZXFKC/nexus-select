#!/usr/bin/env python3
"""Lossless interface-v1 -> corr input adapter (no changes to corr or identity_key).

Requires VERIFIED corr mapping fields; does not guess manufacturer codes from
retailer SKUs. Produces one colorway row plus preserved source-size row records.
The adapter never invokes correlator or publishes a listing.
"""
import argparse
import base64
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

REQUIRED = (
    "source_row_id", "shop_code", "source_product_id", "source_variant_id",
    "brand_raw", "model_code_full_raw", "color_code_raw", "source_url",
    "currency", "item_price_local", "stock_observed",
    "corr_code", "corr_style", "corr_color", "sellable",
)
COST = ("cost_calculated", "cost_verified", "procurement_total_jpy",
        "procurement_unit", "official_price_current", "official_price_usd")
SP_HEADER = ("source_id", "brand", "style", "color", "sellable", "name") + COST
FL_HEADER = ("source_id", "brand", "code", "name", "evidence_tier") + COST


def _serialize(row):
    return json.dumps(row, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _stable(parts):
    return "".join(str(len(str(part))) + ":" + str(part) for part in parts)


def read_input(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames
        if header is None or len(header) != len(set(header)):
            raise ValueError("missing or duplicate input headers")
        missing = set(REQUIRED) - set(header)
        if missing:
            raise ValueError("missing interface v1 + corr evidence fields: " +
                             ",".join(sorted(missing)))
        rows = list(reader)
    if not rows:
        raise ValueError("empty interface source")
    if any(None in row or None in row.values() for row in rows):
        raise ValueError("malformed CSV values")
    return header, rows


def adapt(headers, rows):
    """Returns (sp,fl,lossless manifest); deterministic independent of process time."""
    if set(REQUIRED) - set(headers):
        raise ValueError("missing headers")
    groups = defaultdict(list)
    source_ids = set()
    for row in rows:
        shop = row["shop_code"].strip().upper()
        if shop not in ("SP", "FL"):
            raise ValueError("shop must be SP or FL")
        if not row["source_row_id"] or row["source_row_id"] in source_ids:
            raise ValueError("missing or duplicate source_row_id")
        source_ids.add(row["source_row_id"])
        if not row["source_product_id"] or not row["brand_raw"]:
            raise ValueError("missing source product or brand")
        if not row["source_url"] or not row["currency"] or not row["item_price_local"]:
            raise ValueError("missing source evidence")
        if not row["stock_observed"]:
            raise ValueError("missing observed stock")
        if not row["model_code_full_raw"]:
            raise ValueError("missing full manufacturer code")
        if shop == "SP":
            if not row["corr_style"]:
                raise ValueError("SP manufacturer style not verified")
            if not row["sellable"] in ("0", "1"):
                raise ValueError("SP sellable must be explicitly 0/1")
            if row["brand_raw"].strip().upper() in ("HOKA", "UGG") and not row["corr_color"]:
                raise ValueError("SP color code not verified")
            key = (shop, row["source_product_id"], row["corr_style"], row["corr_color"])
        else:
            if not row["corr_code"]:
                raise ValueError("FL listing code not verified")
            key = (shop, row["source_product_id"], row["corr_code"], "")
        groups[key].append(row)
    sp, fl, manifest = [], [], []
    for key in sorted(groups):
        shop, product, code, color = key
        records = groups[key]
        # For colorway-level facts, never hide contradictions between size rows.
        consistent = ("brand_raw", "name", "cost_calculated", "cost_verified",
                      "procurement_total_jpy", "procurement_unit",
                      "official_price_current", "official_price_usd")
        if shop == "SP":
            consistent += ("sellable", "corr_style", "corr_color")
        else:
            consistent += ("corr_code", "evidence_tier")
        for col in consistent:
            if len({rec.get(col, "") for rec in records}) > 1:
                raise ValueError("inconsistent colorway-level field " + col)
        first = records[0]
        source_id = _stable((shop, product, code, color))
        base = {"source_id": source_id, "brand": first["brand_raw"],
                "name": first.get("name", "")}
        base.update({col: first.get(col, "") for col in COST})
        if shop == "SP":
            sp.append({**base, "style": code, "color": color,
                       "sellable": first["sellable"]})
        else:
            fl.append({**base, "code": code,
                       "evidence_tier": first.get("evidence_tier", "")})
        manifest.append({
            "source_id": source_id, "shop_code": shop,
            "source_row_ids": [r["source_row_id"] for r in records],
            # Each record is complete, including unmapped interface v1 columns.
            "rows_b64": [base64.b64encode(_serialize(r)).decode("ascii") for r in records],
            "rows_sha256": [hashlib.sha256(_serialize(r)).hexdigest() for r in records],
        })
    return sp, fl, manifest


def restore(manifest):
    rows = []
    for entry in manifest:
        for encoded, expected in zip(entry["rows_b64"], entry["rows_sha256"]):
            raw = base64.b64decode(encoded, validate=True)
            if hashlib.sha256(raw).hexdigest() != expected:
                raise ValueError("raw source row checksum mismatch")
            rows.append(json.loads(raw.decode("utf-8")))
    return rows


def compare_reference(adapted, reference, fields):
    """Exact semantic row-set parity with pinned independent verification adapter.

    No missing reference file is treated as PASS. Sort by stable source_id.
    """
    if reference is None:
        raise ValueError("reference adapter output required for parity gate")
    index = lambda rows: {r["source_id"]: tuple(r.get(k, "") for k in fields)
                          for r in rows}
    actual, expected = index(adapted), index(reference)
    if len(actual) != len(adapted) or len(expected) != len(reference):
        raise ValueError("duplicate IDs in parity input")
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    differing = sorted(k for k in (set(actual) & set(expected))
                       if actual[k] != expected[k])
    return {"pass": not (missing or extra or differing),
            "missing": missing, "extra": extra, "differing": differing}


def write_csv(path, rows, fields):
    dest = Path(path)
    if dest.exists():
        raise ValueError("refusing to overwrite " + str(dest))
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--interface-v1", required=True)
    p.add_argument("--sp-out", required=True)
    p.add_argument("--fl-out", required=True)
    p.add_argument("--manifest-out", required=True)
    p.add_argument("--reference-sp")
    p.add_argument("--reference-fl")
    a = p.parse_args()
    headers, originals = read_input(a.interface_v1)
    sp, fl, manifest = adapt(headers, originals)
    if sorted(restore(manifest), key=lambda r: r["source_row_id"]) != sorted(
            originals, key=lambda r: r["source_row_id"]):
        raise ValueError("interface roundtrip mismatch")
    parity = {"status": "NOT_CHECKED"}
    if a.reference_sp or a.reference_fl:
        if not (a.reference_sp and a.reference_fl):
            raise ValueError("both SP and FL reference outputs required")
        def load(path):
            with Path(path).open(encoding="utf-8-sig", newline="") as file:
                return list(csv.DictReader(file))
        parity = {"SP": compare_reference(sp, load(a.reference_sp), SP_HEADER),
                  "FL": compare_reference(fl, load(a.reference_fl), FL_HEADER)}
        if not parity["SP"]["pass"] or not parity["FL"]["pass"]:
            raise ValueError("real reference parity mismatch: " +
                             json.dumps(parity, ensure_ascii=False))
    write_csv(a.sp_out, sp, SP_HEADER)
    write_csv(a.fl_out, fl, FL_HEADER)
    dest = Path(a.manifest_out)
    if dest.exists():
        raise ValueError("refusing to overwrite manifest")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps({"schema": "corr-adapter-v1",
                                "interface_headers": headers,
                                "entries": manifest, "parity": parity},
                               ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"SP": len(sp), "FL": len(fl), "raw": len(originals),
                      "roundtrip": "PASS", "reference_parity": parity},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
