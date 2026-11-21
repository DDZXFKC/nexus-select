"""Load reviewed Shoe Palace XServer evidence into a HOLD-first mapping.

Records are a snapshot of ID+variant evidence, NOT live stock or prices.
No URL guessing, network access, Woo writes, or permit granting.
"""
from __future__ import annotations
import csv
import re
from pathlib import Path
from tools.stockcheck_sp_join_contract import link_sp_variation

SOURCE = Path(__file__).resolve().parents[1] / "data/xserver-export/supplier-url-evidence-sample-2026-11-21.csv"
REQUIRED = ("product_id","variation_id","shop_code","supplier_product_id",
            "source_url","merchant_variant_id","requested_size","requested_color",
            "match_evidence","verified_at_jst","status")
ALLOWED_HOST = "www.shoepalace.com"

def verified_sp_rows(path=SOURCE):
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or not set(REQUIRED).issubset(set(reader.fieldnames)):
            raise ValueError("source evidence columns missing")
        out=[]
        for index,row in enumerate(reader,2):
            from urllib.parse import urlparse
            parsed=urlparse(row["source_url"])
            if row["status"]!="verified":
                continue
            if not row["product_id"].isdigit() or not row["variation_id"].isdigit() or not row["supplier_product_id"].isdigit() or not row["merchant_variant_id"].isdigit():
                raise ValueError(f"invalid IDs at line {index}")
            if parsed.scheme!="https" or parsed.hostname!=ALLOWED_HOST or parsed.username or parsed.password or not parsed.path.startswith("/products/"):
                raise ValueError(f"invalid official SP URL line {index}")
            if not row["match_evidence"].strip() or not row["verified_at_jst"].strip():
                raise ValueError(f"missing evidence line {index}")
            # Do not deduce supplier size from Woo. Read the explicitly
            # witnessed Shopify option1 value in the review evidence.
            option = re.search(r"\boption1\s*=\s*([0-9]+(?:\.[0-9]+)?Y?)\b",
                               row["match_evidence"], flags=re.IGNORECASE)
            if option is None:
                raise ValueError(f"missing witnessed merchant option1 line {index}")
            merchant_size = option.group(1).upper()
            out.append({
                "woo_product_id":int(row["product_id"]),
                "variation_id":int(row["variation_id"]),
                "shop_code":row["shop_code"],"supplier_product_id":row["supplier_product_id"],
                "merchant_variant_id":row["merchant_variant_id"],
                "source_url":row["source_url"],
                "requested_size":row["requested_size"],
                "requested_color":row["requested_color"],
                "merchant_size":merchant_size,
                "verified":True,
                "evidence_ref":f"{Path(path).name}:{index}",
            })
    keys=[(r["woo_product_id"],r["variation_id"]) for r in out]
    if len(keys)!=len(set(keys)):
        raise ValueError("duplicate Woo variation in evidence")
    return out

def match_snapshot(product,variation,rows):
    """For missing Woo product/variation IDs the result is HOLD."""
    allowed=[r for r in rows if r["woo_product_id"]==product.get("product_id")]
    return link_sp_variation(product,variation,allowed)
