# Six-page offline test report — 2026-11-12 (Muse execution, per collector-six-page-runbook-2026-11-12.md)

## Environment
- iMac local package directory (previously validated NEXUS_IMAC_BATCH_PIPELINE extraction). WordPress / LocalWP untouched.
- Python 3.9.6 (`/usr/bin/python3`).
- Local changes made by this batch: `collector.py` replaced with the branch version (previous file kept as `collector.py.bak-20261112`); `shopify_variants.py` and `test_shopify_variants.py` added from branch `integration/grok-review` (HEAD 0088c4b4 at execution time). New DB `nexus_sixhost_new.sqlite` and new output dir `export_sixhost_new` created. No prior run overwritten. Nothing published or imported (0).

## Commands run
```
python3 -m py_compile collector.py shopify_variants.py merchant_to_channels.py
python3 -m unittest -v test_shopify_variants
python3 -m unittest -v test_merchant_to_channels test_channel_ready_v4 test_production_pipeline
python3 merchant_to_channels.py --manifest <pkg>/input_pages_multi/manifest.csv --db <pkg>/nexus_sixhost_new.sqlite --out <pkg>/export_sixhost_new
```

## Test results (unit / synthetic)
- py_compile: OK (all three modules).
- `test_shopify_variants`: **4/4 passed**.
- Existing suite (`test_merchant_to_channels`, `test_channel_ready_v4`, `test_production_pipeline`): **6/6 passed** (unchanged from previous batch).

## Manifest reality check
The runbook assumed a six-page manifest. The actual `manifest.csv` in `input_pages_multi/` contains **5 rows**: BSTN 1, Notre 2, Patta 2. The sixth prepared page (a second BSTN page) lives in a separate manifest (`manifest_bstn2.csv`) and was already executed and reported in the previous batch (docs/collector-execution-report-2026-11-12.md). This batch therefore covers the 5 rows of `manifest.csv`; no page was re-fetched.

## Real saved-page results (distinct from unit tests above)
All 5 pages **parsed successfully** — the new Shopify parser extracted variant rows from the real Notre/Patta saved HTML:
- BSTN: 13 size rows parsed, 13 accepted by DB stage.
- Notre: 16 + 10 = 26 size rows parsed, **0 accepted**.
- Patta: 6 + 6 = 12 size rows parsed, **0 accepted**.
- Total: 51 parsed size rows; DB stage accepted 13, rejected 38; rejection reason for all 38: `brand_missing`.
- Channel exports therefore reflect the BSTN product only: products 1, WooCommerce rows 14 (1 parent + 13 variations), BUYMA rows 1, profit rows 13. `published: 0`, `approved_for_import: false`, status `REVIEW_ONLY`, all gates HOLD.

## Failure analysis (sanitized, for ChatGPT's fix)
Parsing did not fail; DB staging rejected the Shopify rows. `shopify_variants.py` derives brand from the `brand` key of the inline variants' product object (line 41: `brand=text(product.get('brand'))`). On the real Notre/Patta pages that key is absent/empty, so all 38 Shopify rows were emitted with `brand=''` and the DB stage rejected them as `brand_missing` (fail-closed; no rows fabricated, no data invented). The variant payload itself (price / size / SKU) was present and extracted on both hosts. Hypothesis for the fix: on Shopify product JSON the brand-equivalent field is conventionally `vendor`; please confirm against the saved structure and patch the field source. Muse did not modify the parser.

## Missing fields (accepted BSTN product, unchanged from previous batch)
category, channel_specific_price, color, description, image_usage_permission, images, manufacturer_style_code, platform_import_validation, shipping_and_tax_confirmation, verified_size_stock.

## Notes
- `live_fetch.py` was not run in this batch (saved HTML already existed), per runbook step 7.
- docs/collector-two-agent-policy-2026-11-12.md names `tools/evidence_catalog.py` as an immediate milestone; that tool was not part of this runbook batch and was not executed here.
- Next step is ChatGPT's: patch the Shopify brand field source, then repeat this batch. The milestone "6 pages parse AND stage" is not yet met: parse 5/5 pages OK, staging 13/51 rows.
