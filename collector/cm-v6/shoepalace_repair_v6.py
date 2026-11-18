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

def brand_key(value):
    k = key(value)
    return {"new_balance": "newbalance", "new balance": "newbalance"}.get(k, k)

def load_reference(path, fields):
    if not path:
        return {}
    result = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not set(fields).issubset(reader.fieldnames or []):
            raise ValueError(f"Missing reference fields: {fields}")
        for row in reader:
            k = tuple(brand_key(row[n]) if n == "brand" else key(row[n]) for n in fields[:-1])
            value = row[fields[-1]].strip()
            if not all(k) or not value:
                raise ValueError("Incomplete reference row")
            if k in result and result[k] != value:
                raise ValueError(f"Conflicting reference: {k}")
            result[k] = value
    return result

def load_cm_reference(path):
    """Exact product-level verified JP/CM evidence; legacy rows kept separate."""
    if not path:
        return {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = set(reader.fieldnames or [])
        if "product_id" not in fields:
            return load_reference(path, ["brand", "department", "size_original", "cm"])
        required = {"product_id", "size_original", "cm", "brand", "department",
                    "model", "age_group", "size_system", "source_url", "verified"}
        if not required.issubset(fields):
            raise ValueError("Incomplete scoped cm reference headers")
        result = {}
        for row in reader:
            if key(row["verified"]) != "true":
                continue
            if not all(row[n].strip() for n in required):
                raise ValueError("Incomplete verified cm evidence")
            if not row["source_url"].startswith("https://"):
                raise ValueError("Missing HTTPS evidence URL")
            k = (key(row["product_id"]), key(row["size_original"]))
            entry = dict(row)
            if k in result and result[k] != entry:
                raise ValueError(f"Conflicting product size evidence: {k}")
            result[k] = entry
        return result

def load_color_reference(path):
    if not path:
        return {}
    result = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"product_id", "color_name", "source_url", "evidence", "status"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Incomplete color reference")
        for row in reader:
            if not all(row[k].strip() for k in required):
                raise ValueError("Incomplete color evidence")
            if row["status"] not in {"CONFIRMED_BY_TITLE_RULE", "HOLD_CONTRADICTION"}:
                raise ValueError("Unsupported color reference status")
            pid = row["product_id"].strip()
            if pid in result and result[pid] != row:
                raise ValueError("Conflicting color reference: " + pid)
            result[pid] = row
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

def repair(products, cm=None, ja=None, color_reference=None):
    cm, ja, color_reference = cm or {}, ja or {}, color_reference or {}
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
        color_tags = [t[6:] for t in tags if t.startswith("Color_")]
        # A specific colorway name need not contain the broad Color_ taxonomy.
        # Preserve the title evidence separately; never use a generic tag as the colorway.
        candidates = [m for m in re.finditer(r"\(([^()]*)\)", title) if m.group(1).strip()]
        matches = [m for m in candidates
                   if any(re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", m.group(1), re.I) for t in color_tags)]
        match = matches[0] if len(matches) == 1 else None
        color_status = "TAG_SUPPORTED" if match else "UNKNOWN"
        # A single terminal bracket (optionally followed by the known shipping suffix)
        # is a candidate, not verified color evidence. Do not strip it from the title.
        if not match and len(candidates) == 1:
            candidate = candidates[0]
            suffix = title[candidate.end():].strip().casefold()
            value = candidate.group(1).strip()
            noncolor = re.search(r"^(?:\d+(?:\.\d+)?\s*(?:cm|mm|oz|ml|pack)?|\d+[- ]?pack|wide|narrow|standard|regular|limited edition|online only|unisex|mens|womens|kids|gs|ps|td|2e|4e)$", value, re.I)
            if suffix in {"", "free shipping"} and not noncolor:
                match = candidate
                color_status = "TITLE_CANDIDATE"
        color = match.group(1).strip() if match else None
        footwear = any(key(t) in {"category_footwear", "footwear", "product_shoes", "shoes"} for t in tags)
        departments = [t[11:] for t in tags if t.startswith("Department_")]
        department = departments[0] if len(departments) == 1 else None
        codes = sorted({t[5:] for t in tags if t.startswith("Code_") and t[5:]})
        handle = p.get("handle")
        if not handle:
            issues.append([pid, "", "missing_handle"])
        url = "https://www.shoepalace.com/products/" + quote(handle, safe="-") if handle else None
        color_evidence = color_reference.get(pid)
        if color_evidence:
            if (color_evidence["color_name"] != color or color_evidence["source_url"] != url
                    or color_status != "TITLE_CANDIDATE"):
                raise ValueError(f"Color reference does not match raw evidence: {pid}")
            color_status = color_evidence["status"]
        vs = p.get("variants") or []
        states = [v.get("available") for v in vs]
        stock = True if any(s is True for s in states) else (False if states and all(s is False for s in states) else None)
        translation = ja.get((key(pid),))
        rows.append({"shop_code": SHOP, "product_id": pid, "title_original": title,
                     "title_without_color": (title[:match.start()] + title[match.end():]).strip() if match and color_status == "TAG_SUPPORTED" else title,
                     "color_name": color, "color_name_status": color_status,
                     "color_evidence": color_evidence["evidence"] if color_evidence else None, "color_tags": color_tags, "brand": p.get("vendor"),
                     "department": department, "source_url": url,
                     "coupon_tag_codes": codes, "coupon_tag_status": "TAGGED_UNVERIFIED" if codes else "NOT_TAGGED",
                     "description_en_html": p.get("body_html"), "description_ja": translation,
                     "description_ja_status": "PROVIDED" if translation else "PENDING",
                     "in_stock": stock, "images": p.get("images"), "raw_product": p})
        if not color:
            issues.append([pid, "", "color_name_unknown"])
        elif color_status in {"TITLE_CANDIDATE", "HOLD_CONTRADICTION"}:
            issues.append([pid, "", "color_name_needs_review"])
        if not translation:
            issues.append([pid, "", "japanese_description_pending"])
        for v in vs:
            vid = str(v["id"])
            if vid in variant_ids:
                raise ValueError(f"Duplicate variant {vid}")
            variant_ids.add(vid)
            size = size_value(p, v)
            ck = (brand_key(p.get("vendor")), key(department), key(size))
            # Exact product ID scopes model/age/size-system evidence; no generic
            # fallback for HOKA or UGG, where model/age differences are known.
            alpha_size = key(size) in {"xs", "s", "m", "l", "xl", "xxl", "os", "one size"}
            applicable = footwear and not alpha_size
            scoped = cm.get((key(pid), key(size))) if applicable and size else None
            if scoped is not None and (brand_key(scoped["brand"]) != ck[0] or key(scoped["department"]) != ck[1]):
                raise ValueError(f"CM evidence product metadata mismatch: {pid}")
            # GPT-approved scoped exception (docs/shoepalace-cm-gpt-integration-review-2026-11-18.md):
            # HOKA Men adult US 7-14 (the 15 sizes verified against the official
            # chart) may use the brand-generic fallback. All other HOKA and all
            # UGG remain excluded from the generic fallback.
            hoka_men_scoped = ck[0] == "hoka" and ck[1] == "men" and ck[2] in {"7", "7.5", "8", "8.5", "9", "9.5", "10", "10.5", "11", "11.5", "12", "12.5", "13", "13.5", "14"}
            generic_ok = ck[0] not in {"hoka", "ugg"} or hoka_men_scoped
            val = scoped["cm"] if scoped else (cm.get(ck) if applicable and all(ck) and generic_ok else None)
            if val is not None:
                try:
                    d = Decimal(val)
                    if not d.is_finite() or d <= 0:
                        raise ValueError("Invalid cm")
                except InvalidOperation as e:
                    raise ValueError("Invalid cm reference") from e
            if applicable and (size is None or val is None):
                issues.append([pid, vid, "cm_reference_missing"])
            if footwear and alpha_size:
                issues.append([pid, vid, "footwear_alpha_size_review"])
            current, compare = money(v.get("price")), money(v.get("compare_at_price"))
            if current is None:
                issues.append([pid, vid, "price_missing"])
            variants.append({"shop_code": SHOP, "product_id": pid, "variant_id": vid,
                             "sku": v.get("sku"), "size_original": size, "cm": val,
                             "cm_status": ("MATCHED" if val is not None else "MISSING") if applicable else ("SIZE_SYSTEM_REVIEW" if footwear else "NOT_APPLICABLE"),
                             "cm_source_url": scoped["source_url"] if scoped else None,
                             "cm_model": scoped["model"] if scoped else None,
                             "cm_age_group": scoped["age_group"] if scoped else None,
                             "cm_size_system": scoped["size_system"] if scoped else None,
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
    a.add_argument("--color-reference", type=Path)
    a.add_argument("--ja-reference", type=Path, help="CSV: product_id,description_ja")
    a.add_argument("--output", required=True, type=Path)
    args = a.parse_args()
    products = []
    for path in args.raw:
        products.extend(json.loads(path.read_text(encoding="utf-8"))["products"])
    result = repair(products, load_cm_reference(args.cm_reference),
                    load_reference(args.ja_reference, ["product_id","description_ja"]),
                    load_color_reference(args.color_reference))
    rows, variants, issues, stats = result
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "repaired.json").write_text(json.dumps({"products": rows, "variants": variants, "issues": issues, "summary": stats, "input_files": [str(p) for p in args.raw]}, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(args.output / "products.csv", rows, ("raw_product",))
    write_csv(args.output / "variants.csv", variants, ("raw_variant",))
    write_csv(args.output / "issues.csv", [dict(product_id=p,variant_id=v,reason=r) for p,v,r in issues])
    print(json.dumps(stats, ensure_ascii=False))

if __name__ == "__main__":
    main()
