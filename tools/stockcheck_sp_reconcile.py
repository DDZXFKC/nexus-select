"""Deterministic Shoe Palace coverage reconciler, offline-only.

Reads a current XServer parent-SKU export when present. It NEVER treats URL
presence or historic Shopify availability as live purchase authorization.
"""
from __future__ import annotations
import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
URLS=ROOT/"data/xserver-export/sp-30-source-url-coverage-2026-11-21.csv"
EVIDENCE=ROOT/"data/xserver-export/supplier-url-evidence-sample-2026-11-21.csv"

def read_csv(path):
    with Path(path).open(encoding="utf-8-sig",newline="") as stream:
        return list(csv.DictReader(stream))

def reconcile(parents, urls=None, evidence=None):
    """List status for each current SP parent: VERIFIED_SAMPLE / URL_PENDING / NO_URL.

    "VERIFIED_SAMPLE" means identity evidence exists, NEVER live purchase stock.
    A missing or malformed parent source fails closed rather than being counted.
    """
    urls=read_csv(URLS) if urls is None else urls
    evidence=read_csv(EVIDENCE) if evidence is None else evidence
    url_map={}
    for r in urls:
        supplier=str(r.get("supplier_product_id","")).strip()
        url=str(r.get("source_url","")).strip()
        if not supplier.isdecimal() or not url.startswith("https://www.shoepalace.com/products/"):
            raise ValueError("malformed source URL row")
        if supplier in url_map and url_map[supplier]!=url:
            raise ValueError("conflicting source URLs for "+supplier)
        url_map[supplier]=url
    evidence_ids=set()
    for r in evidence:
        if r.get("status")=="verified":
            supplier=str(r.get("supplier_product_id","")).strip()
            if supplier.isdecimal():
                evidence_ids.add(supplier)
    output=[]
    seen=set()
    for parent in parents:
        sku=str(parent.get("parent_sku",parent.get("sku",""))).strip()
        if not sku.startswith("SP-") or not sku[3:].isdecimal():
            raise ValueError("invalid SP parent SKU: "+sku)
        supplier=sku[3:]
        if supplier in seen:
            raise ValueError("duplicate SP supplier product ID "+supplier)
        seen.add(supplier)
        recorded=str(parent.get("supplier_product_id","") or "").strip()
        if recorded and recorded!=supplier:
            status="HOLD_PARENT_ID_MISMATCH"
        elif supplier in evidence_ids and supplier in url_map:
            status="IDENTITY_SAMPLE_VERIFIED"
        elif supplier in url_map:
            status="SOURCE_URL_DOCUMENTED_ID_UNVERIFIED"
        else:
            status="NO_SOURCE_URL_EVIDENCE"
        output.append({"woo_product_id":parent.get("woo_product_id",parent.get("product_id","")),
                       "parent_sku":sku,"supplier_product_id":supplier,
                       "source_url":url_map.get(supplier,""),
                       "status":status,"live_stock_verified":"NO"})
    return output

def run(parent_csv,output_csv):
    parents=read_csv(parent_csv)
    rows=reconcile(parents)
    out=Path(output_csv)
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["woo_product_id","parent_sku","supplier_product_id","source_url","status","live_stock_verified"])
        w.writeheader()
        w.writerows(rows)
    return len(rows)

if __name__=="__main__":
    import sys
    if len(sys.argv)!=3:
        raise SystemExit("usage: python -m tools.stockcheck_sp_reconcile PARENT_EXPORT.csv OUT.csv")
    print(run(sys.argv[1],sys.argv[2]))
