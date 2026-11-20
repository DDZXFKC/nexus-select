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


def _manifest_product_keys(entries, shop_code):
    """Strict manifest-backed normalization to shop+product semantic identity.

    Any ambiguous, unparseable or duplicate mapping is explicit FAIL evidence.
    This is NOT a fuzzy parser and never changes the corr source_id.
    """
    keys, failures = {}, []
    for entry in entries:
        sid = str(entry.get("source_id", ""))
        if entry.get("shop_code") != shop_code:
            continue
        try:
            raw_rows = restore([entry])
            if not raw_rows:
                raise ValueError("manifest has no rows")
            products = {str(row["source_product_id"]) for row in raw_rows}
            shops = {str(row["shop_code"]).strip().upper() for row in raw_rows}
            if len(products) != 1 or shops != {shop_code}:
                raise ValueError("manifest product or shop inconsistent")
            product = next(iter(products))
            if not product:
                raise ValueError("empty product identity")
            # Reconstruct strictly from manifest source metadata.
            style_field = ("corr_style", "corr_color") if shop_code == "SP" else ("corr_code",)
            variants = {tuple(str(row.get(k, "")) for k in style_field) for row in raw_rows}
            if len(variants) != 1:
                raise ValueError("manifest style/code disagreement")
            parts = ((shop_code, product) + next(iter(variants)) + ("",)
                     if shop_code == "FL" else (shop_code, product) + next(iter(variants)))
            if sid != _stable(parts):
                raise ValueError("source_id not reproducible from manifest")
            if sid in keys:
                raise ValueError("duplicate manifest source_id")
            keys[sid] = _stable((shop_code, product))
        except (ValueError, KeyError, TypeError) as exc:
            failures.append({"source_id": sid, "reason": str(exc)})
    # Never silently collapse colorways with the same product ID.
    reverse = defaultdict(list)
    for sid, key in keys.items():
        reverse[key].append(sid)
    for key, ids in reverse.items():
        if len(ids) > 1:
            failures.append({"source_id": "|".join(sorted(ids)),
                             "reason": "many-to-one product identity: " + key})
    return keys, failures


def compare_reference(adapted, reference, fields, manifest=None, shop_code=None):
    """Exact full-field semantic parity, with optional manifest-backed ID mapping.

    In strict mode, the production interface source_id remains a length-prefixed
    4-component ID; verification's raw product ID is mapped ONLY via manifest.
    Unmapped/duplicate IDs are enumerated; no partial PASS is possible.
    """
    if reference is None:
        raise ValueError("reference adapter output required for parity gate")
    use_manifest = manifest is not None or shop_code is not None
    if use_manifest and (manifest is None or shop_code not in ("SP", "FL")):
        raise ValueError("manifest and explicit SP/FL shop_code both required")
    mapping, invalid = ({}, [])
    method = "EXACT_SOURCE_ID"
    if use_manifest:
        mapping, invalid = _manifest_product_keys(manifest, shop_code)
        method = "MANIFEST_SHOP_PRODUCT_V1"

    def key_for(row, side):
        sid = str(row.get("source_id", ""))
        if not sid:
            invalid.append({"side": side, "source_id": sid, "reason": "missing source_id"})
            return None
        if not use_manifest:
            return sid
        if side == "production":
            if sid not in mapping:
                invalid.append({"side": side, "source_id": sid,
                                "reason": "no unique manifest mapping"})
                return None
            return mapping[sid]
        # Verifier emits RAW source_product_id by spec. Never parse or guess.
        return _stable((shop_code, sid))

    def make_index(rows, side):
        indexed = {}
        for row in rows:
            key = key_for(row, side)
            if key is None:
                continue
            if key in indexed:
                invalid.append({"side": side, "source_id": str(row.get("source_id", "")),
                                "reason": "normalized key collision " + key})
            else:
                indexed[key] = tuple(row.get(k, "") for k in fields if k != "source_id")
        return indexed

    actual, expected = make_index(adapted, "production"), make_index(reference, "reference")
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    differing = sorted(key for key in set(actual) & set(expected)
                       if actual[key] != expected[key])
    return {"pass": not (missing or extra or differing or invalid),
            "normalization": method, "missing": missing, "extra": extra,
            "differing": differing, "invalid_ids": invalid}


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
        parity = {"SP": compare_reference(sp, load(a.reference_sp), SP_HEADER,
                                             manifest, "SP"),
                  "FL": compare_reference(fl, load(a.reference_fl), FL_HEADER,
                                             manifest, "FL")}
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
