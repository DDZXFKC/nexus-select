#!/usr/bin/env python3
"""Minimal lossless raw-offer envelope contract for FL/SP converter fixtures.

This is a testable staging contract, NOT the production SP/FL data converter.
"""
import base64
import csv
import hashlib
import json
import re
import unicodedata

REQUIRED = ("source_product_id", "model_code_full_raw", "color_code_raw",
            "currency", "item_price_local", "source_url", "stock_observed")


def brand_normalize(raw, aliases):
    value = unicodedata.normalize("NFKC", raw).strip()
    value = " ".join(value.split()).casefold()
    if value not in aliases:
        raise ValueError("unknown brand alias: " + raw)
    return aliases[value]


def model_normalize(raw):
    value = unicodedata.normalize("NFKC", raw).strip().upper()
    if not value:
        raise ValueError("missing complete model code")
    # Preserve leading zero and all punctuation; no guessed equivalences.
    return value


def stable_id(shop_code, product_id, variant_id=""):
    fields = (shop_code, product_id, variant_id or "COLORWAY")
    if not shop_code or not product_id:
        raise ValueError("missing stable ID component")
    return "".join(str(len(part)) + ":" + part for part in fields)


def encode_offer(shop_code, row, aliases):
    for key in REQUIRED:
        if key not in row:
            raise ValueError("missing required raw field " + key)
    # Store complete original CSV row for byte-exact *values* roundtrip.
    payload = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    raw_bytes = payload.encode("utf-8")
    return {
        "source_row_id": stable_id(shop_code, row["source_product_id"],
                                   row.get("source_variant_id", "")),
        "shop_code": shop_code,
        "brand_norm": brand_normalize(row["brand_raw"], aliases),
        "model_code_full_norm": model_normalize(row["model_code_full_raw"]),
        "color_code_raw": row["color_code_raw"],
        "raw_row_b64": base64.b64encode(raw_bytes).decode("ascii"),
        "raw_row_sha256": hashlib.sha256(raw_bytes).hexdigest(),
    }


def decode_offer(offer):
    original = base64.b64decode(offer["raw_row_b64"], validate=True)
    if hashlib.sha256(original).hexdigest() != offer["raw_row_sha256"]:
        raise ValueError("raw row hash mismatch")
    return json.loads(original.decode("utf-8"))


def uniqueness_audit(offers):
    ids = [offer["source_row_id"] for offer in offers]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate source row identity")
    keys = [(offer["shop_code"], offer["brand_norm"],
             offer["model_code_full_norm"]) for offer in offers]
    # Identical shop/colorway source rows are a collision; different shops are expected.
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate shop colorway key")
    return True
