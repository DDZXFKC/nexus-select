"""Sheet (カラーマスター + 商品カラー) -> CSV for tools/ahc_color_components_to_woo.php.

One output row per color component. Every sheet product is exported (CONFIRMED or not), so no product keeps the old
photo/name-based swatch: non-confirmed products get null hex = neutral circle, and
products without components get one position-0 marker row (= empty list).
display_hex is filled only when the component
master row is APPROVED_APPROX *and* the product's recomputed swatch status is not
HOLD/UNKNOWN (so a HOLD product never shows a partly-approved stripe).
The product's swatch status is recomputed here with color_fullrun.swatch() and
compared with the sheet's swatch_status; any mismatch stops the export.

Run:
  python3 collector/color_woo_export.py --master M.csv --products P1.csv [P2.csv ...] --output out_dir
Outputs: woo_components.csv, summary.json
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import color_fullrun as cf  # noqa: E402

FIELDS = ["shop_code", "supplier_product_id", "supplier_color_key", "position",
          "token_original", "display_hex", "hex_status", "swatch_status"]


def export(master_rows, product_rows):
    master = cf.Master(master_rows)
    out, stats, mismatches = [], Counter(), []
    for row in product_rows:
        status, _, _, _ = cf.swatch(row, master)
        if status != (row.get("swatch_status") or "").strip():
            mismatches.append((row.get("supplier_product_id"), row.get("swatch_status"), status))
        stats[f"status_{status}"] += 1
        if row.get("supplier_color_key") != "single":
            stats["skipped_multi_color_key"] += 1
            continue
        brand, pkey = row.get("brand_id", ""), cf.product_key(row)
        comps = json.loads(row.get("components_json") or "[]")
        if not comps:
            # Marker row (position 0): the writer stores an empty list so the theme shows the
            # neutral circle instead of keeping the old photo/name-based swatch.
            out.append({"shop_code": row.get("shop_code"), "supplier_product_id": row.get("supplier_product_id"),
                        "supplier_color_key": row.get("supplier_color_key"), "position": 0,
                        "token_original": "", "display_hex": "", "hex_status": "NO_COMPONENTS",
                        "swatch_status": status})
            stats["exported_no_components"] += 1
        for c in comps:
            m = master.by_id.get(c.get("color_id"))
            ok = (status in ("CONFIRMED", "DRAFT") and m is not None
                  and cf.ref_problem(c, master, brand, pkey) is None
                  and (m.get("hex_status") or "").strip() == cf.APPROVED
                  and cf.HEX.fullmatch((m.get("display_hex") or "").strip()))
            out.append({"shop_code": row.get("shop_code"), "supplier_product_id": row.get("supplier_product_id"),
                        "supplier_color_key": row.get("supplier_color_key"), "position": c.get("position"),
                        "token_original": c.get("token_original"),
                        "display_hex": m["display_hex"].strip().upper() if ok else "",
                        "hex_status": cf.APPROVED if ok else "NOT_SHOWN", "swatch_status": status})
        stats["exported_products"] += 1
    return out, stats, mismatches


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", required=True)
    ap.add_argument("--products", required=True, nargs="+")
    ap.add_argument("--output", required=True)
    a = ap.parse_args(argv)
    products = [r for p in a.products for r in cf.read_table(p)]
    ids = Counter(cf.product_key(r) for r in products)
    dup = [k for k, n in ids.items() if n > 1]
    if dup:
        raise cf.DataError(f"duplicate product rows across parts: {dup[:5]}")
    rows, stats, mismatches = export(cf.read_table(a.master), products)
    if mismatches:
        raise cf.DataError(f"sheet swatch_status differs from recompute for {len(mismatches)} products: {mismatches[:5]}")
    outdir = Path(a.output)
    outdir.mkdir(parents=True, exist_ok=True)
    cf.write_csv(outdir / "woo_components.csv", rows, FIELDS)
    summary = dict(stats, products_in=len(products), component_rows=len(rows))
    (outdir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
