# Vendor-fix verification report — 2026-11-12 (Muse execution, per collector-vendor-fix-runbook.md)

## Environment / what was executed
- iMac, Python 3.9.6 (`/usr/bin/python3`), package in `/Users/discodadz/nexus-run/pkg`. WordPress / LocalWP untouched; nothing published or imported.
- Files copied from branch `integration/grok-review` (HEAD 70054d7a at execution time): `research/online/shopify_variants.py` and `research/online/test_shopify_variants.py` into the local package. Previous `shopify_variants.py` backed up as `shopify_variants.py.bak-vendorfix-20261112`. No code was edited by Muse.
- New DB `nexus_vendorfix_new.sqlite` and new output dir `export_vendorfix_new` created for the 5-page run; previous evidence was not overwritten. A separate BSTN run used new DB `nexus_vendorfix_bstn2.sqlite` / output `export_vendorfix_bstn2`.

## Commands run
```
python3 -m py_compile collector.py shopify_variants.py merchant_to_channels.py
python3 -m unittest -v test_shopify_variants test_merchant_to_channels test_channel_ready_v4 test_production_pipeline
python3 merchant_to_channels.py --manifest <pkg>/input_pages_multi/manifest.csv --db <pkg>/nexus_vendorfix_new.sqlite --out <pkg>/export_vendorfix_new
python3 merchant_to_channels.py --manifest <pkg>/input_pages_multi/manifest_bstn2.csv --db <pkg>/nexus_vendorfix_bstn2.sqlite --out <pkg>/export_vendorfix_bstn2
```

## Test results
- py_compile: OK (exit 0).
- Unit tests: **12/12 passed** — `test_shopify_variants` 6/6 (including the new `test_vendor_fallback` and `test_ambiguous_vendor_does_not_guess`), plus the existing 6/6 (`test_merchant_to_channels`, `test_channel_ready_v4`, `test_production_pipeline`).

## Vendor evidence in the saved Notre/Patta HTML (step 3, local check only, no upload)
Checked only the four saved Notre/Patta HTML files. In every file, a `vendor` field is present in the **same script as the variants array**, with exactly **1 distinct vendor value** per file and 0 distinct vendor values in scripts without variants:
- Notre file 1: scripts with variants 2/2 also contain vendor; distinct vendor values in those scripts: 1.
- Notre file 2: same — 2/2, distinct: 1.
- Patta file 1: scripts with variants 3/3 also contain vendor; distinct: 1.
- Patta file 2: same — 3/3, distinct: 1.
- Variant-entry key structure (names only): Notre entries carry `id, image, name, price, public_title, sku, title, untranslatedTitle`. Patta entries additionally carry `available, barcode, compare_at_price, featured_image, option1–3, options`, etc. Hostname was never used as a brand.

## Five-page run (manifest.csv: BSTN 1, Notre 2, Patta 2)
- Per-host parsed size rows: BSTN 13, Notre 16 + 10 = 26, Patta 6 + 6 = 12. **Total parsed: 51.**
- DB stage: **accepted 51 / rejected 0**. Rejection reasons: none. All 38 rows previously rejected as `brand_missing` now pass brand validation (extracted evidence: brand present 13/13 BSTN, 26/26 Notre, 12/12 Patta).
- Channel exports: products 39, WooCommerce rows 90, BUYMA rows 39, profit rows 51. `published: 0`, `approved_for_import: false`, status `REVIEW_ONLY`, all gates HOLD.
- Note on the export counts (fact, for ChatGPT's analysis — Muse did not change any code): in `channel_report_v4.json` the BSTN product is grouped as one product with size_count 13, while the Notre and Patta rows appear as per-size review entries with size_count 1 each (26 Notre + 12 Patta entries), which is why products = 39 and WooCommerce rows = 90. The Notre review entries also list `product_name` among their missing fields; the Patta entries do not.
- As the runbook states, this proves only brand staging — NOT manufacturer style code, verified stock, image rights, cost, or publication readiness.

## Separate second-BSTN-page run (step 7)
- Used the separately verified `manifest_bstn2.csv` (BSTN page 1 + the second BSTN page; this was **not** part of the original 5-row manifest, and no 6-page claim is made for the run above).
- Parsed 14 size rows (13 + 1); DB accepted 14 / rejected 0; products 2; WooCommerce rows 16 (2 parents + 14 variations); BUYMA rows 2; profit rows 14; `published: 0`, status `REVIEW_ONLY`, all HOLD.

## Missing fields (from channel_report_v4.json, 5-page run)
- BSTN and Patta products: category, channel_specific_price, color, description, image_usage_permission, images, manufacturer_style_code, platform_import_validation, shipping_and_tax_confirmation, verified_size_stock.
- Notre products: the same list plus product_name.

## Errors
- None in fetch/parse/stage/export. No live site, theme, or product data was modified; no source HTML, private inventory, or pricing details are included in this report.

## Next step (ChatGPT's responsibility)
Brand staging for the 5-page batch is now complete (51/51). Remaining items visible from this run for the next bundled patch: (1) the channel-export grouping for Shopify rows (per-size products, Woo 90 rows) and Notre's missing product_name in the channel stage; (2) the still-missing fields above (manufacturer style code, verified stock, image rights, etc.) before any publication readiness can be claimed. Per the end-to-end rule, please bundle the next code fix with complete iMac execution instructions, confirmation items, error handling, and the GitHub report path in one batch.
