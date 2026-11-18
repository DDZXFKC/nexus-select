#!/usr/bin/env python3
"""Shoe Palace only: offline information repair, never price or image processing."""
import argparse
import csv
import json
import re
from pathlib import Path
from decimal import Decimal, InvalidOperation
from urllib.parse import quote

SHOP = "shoe-palace"

def key(value):
    return str(value or "").strip().casefold()

def load_reference(path, fields):
    if not path:
        return {}
    result = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not set(fields).issubset(reader.fieldnames or []):
            raise ValueError(f"Missing reference fields: {fields}")
        for row in reader:
            k = tuple(key(row[n]) for n in fields[:-1])
            value = row[fields[-1]].strip()
            if not all(k) or not value:
                raise ValueError("Incomplete reference row")
            if k in result and result[k] != value:
                raise ValueError(f"Conflicting reference: {k}")
            result[k] = value
    return result

def money(value):
    if value is None or value == "":
        return None
    try:
        n = Decimal(str(value))
        if not n.is_finite() or n < 0 or n * 100 != (n * 100).to_integral_value():
            raise ValueError(f"Invalid USD amount: {value}")
        return int(n * 100)
    except InvalidOperation as e:
        raise ValueError(f"Invalid USD amount: {value}") from e

def size_value(p, v):
    opts = [o for o in p.get("options", []) if key(o.get("name")) in {"size", "shoe size"}]
    if len(opts) != 1 or opts[0].get("position") not in (1, 2, 3):
        return None
    return v.get("option" + str(opts[0]["position"]))

def repair(products, cm=None, ja=None):
    cm, ja = cm or {}, ja or {}
    rows, variants, issues = [], [], []
    seen = {}
    variant_ids = set()
    for p in products:
        pid = str(p["id"])
        if pid in seen:
            if p != seen[pid]:
                raise ValueError(f"Conflicting duplicate product {pid}; separate snapshots")
            continue
        seen[pid] = p
        tags = p.get("tags") or []
        if not isinstance(tags, list):
            raise ValueError("Expected Shopify tag list")
        title = p.get("title", "")
        match = re.search(r"\(([^()]*)\)\s*$", title)
        color = match.group(1).strip() if match else None
        color_tags = [t[6:] for t in tags if t.startswith("Color_")]
        departments = [t[11:] for t in tags if t.startswith("Department_")]
        department = departments[0] if len(departments) == 1 else None
        codes = sorted({t[5:] for t in tags if t.startswith("Code_") and t[5:]})
        handle = p.get("handle")
        if not handle:
            issues.append([pid, "", "missing_handle"])
        url = "https://www.shoepalace.com/products/" + quote(handle, safe="-") if handle else None
        vs = p.get("variants") or []
        states = [v.get("available") for v in vs]
        stock = True if any(s is True for s in states) else (False if states and all(s is False for s in states) else None)
        translation = ja.get((key(pid),))
        rows.append({"shop_code": SHOP, "product_id": pid, "title_original": title,
                     "title_without_color": title[:match.start()].rstrip() if match else title,
                     "color_name": color, "color_tags": color_tags, "brand": p.get("vendor"),
                     "department": department, "source_url": url,
                     "coupon_tag_codes": codes, "coupon_tag_status": "TAGGED_UNVERIFIED" if codes else "NOT_TAGGED",
                     "description_en_html": p.get("body_html"), "description_ja": translation,
                     "description_ja_status": "PROVIDED" if translation else "PENDING",
                     "in_stock": stock, "images": p.get("images"), "raw_product": p})
        if not color:
            issues.append([pid, "", "color_name_unknown"])
        if not translation:
            issues.append([pid, "", "japanese_description_pending"])
        for v in vs:
            vid = str(v["id"])
            if vid in variant_ids:
                raise ValueError(f"Duplicate variant {vid}")
            variant_ids.add(vid)
            size = size_value(p, v)
            ck = (key(p.get("vendor")), key(department), key(size))
            val = cm.get(ck) if all(ck) else None
            if val is not None:
                try:
                    d = Decimal(val)
                    if not d.is_finite() or d <= 0:
                        raise ValueError("Invalid cm")
                except InvalidOperation as e:
                    raise ValueError("Invalid cm reference") from e
            if size is None or val is None:
                issues.append([pid, vid, "cm_reference_missing"])
            current, compare = money(v.get("price")), money(v.get("compare_at_price"))
            if current is None:
                issues.append([pid, vid, "price_missing"])
            variants.append({"shop_code": SHOP, "product_id": pid, "variant_id": vid,
                             "sku": v.get("sku"), "size_original": size, "cm": val,
                             "currency": "USD", "price_minor": current,
                             "compare_at_price_minor": compare,
                             "regular_price_minor": compare if compare is not None and compare > 0 and current is not None and compare >= current else None,
                             "available": v.get("available") if type(v.get("available")) is bool else None,
                             "stock_quantity": None, "source_url": url,
                             "coupon_tag_codes": codes, "coupon_application": "UNKNOWN",
                             "raw_variant": v})
    stats = {"all_products": len(rows), "in_stock_products": sum(p["in_stock"] is True for p in rows),
             "out_of_stock_products": sum(p["in_stock"] is False for p in rows),
             "unknown_stock_products": sum(p["in_stock"] is None for p in rows),
             "all_variants": len(variants), "in_stock_variants": sum(v["available"] is True for v in variants),
             "unknown_stock_variants": sum(v["available"] is None for v in variants),
             "issues": len(issues)}
    return rows, variants, issues, stats

def write_csv(path, rows, omit=()):
    fields = [k for k in rows[0] if k not in omit] if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        if not fields:
            return
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: json.dumps(row[k], ensure_ascii=False) if isinstance(row[k], (list, dict)) else row[k] for k in fields})

def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--raw", nargs="+", required=True, type=Path)
    a.add_argument("--cm-reference", type=Path, help="CSV: brand,department,size_original,cm")
    a.add_argument("--ja-reference", type=Path, help="CSV: product_id,description_ja")
    a.add_argument("--output", required=True, type=Path)
    args = a.parse_args()
    products = []
    for path in args.raw:
        products.extend(json.loads(path.read_text(encoding="utf-8"))["products"])
    result = repair(products, load_reference(args.cm_reference, ["brand","department","size_original","cm"]),
                    load_reference(args.ja_reference, ["product_id","description_ja"]))
    rows, variants, issues, stats = result
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "repaired.json").write_text(json.dumps({"products": rows, "variants": variants, "issues": issues, "summary": stats, "input_files": [str(p) for p in args.raw]}, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(args.output / "products.csv", rows, ("raw_product",))
    write_csv(args.output / "variants.csv", variants, ("raw_variant",))
    write_csv(args.output / "issues.csv", [dict(product_id=p,variant_id=v,reason=r) for p,v,r in issues])
    print(json.dumps(stats, ensure_ascii=False))

if __name__ == "__main__":
    main()
