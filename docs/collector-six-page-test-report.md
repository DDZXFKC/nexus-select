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

---

## Follow-up — 2026-11-13 six-page brand batch (Muse execution, per docs/collector-six-page-brand-batch-2026-11-13.md)

### Environment and provenance
- Executed on the iMac in an **isolated copy** of the validated package (`pkg_six_20261113`); the original package was not modified. WordPress / LocalWP untouched. No installs, no store fetching, no imports, no publication.
- Python 3.9.6.
- Batch snapshot commit: `5f0896ca` (integration/grok-review). New files copied into the package root from that snapshot:
  - `verify_six_pages.py` — sha256 `65f5da94b535ebcf5900f76e41c9592ac38aacc0e16f49cc588d9f55cfd87e1b`
  - `test_verify_six_pages.py` — sha256 `5050b6db3c53e1daae936be3a189c12af8579947509cce8ce1d18502fdadb46e`
- The package copies of `collector.py` (sha256 `340982f2f8ab43a084810f4ffdf9c09a1b71bb59baa2fdb2da1508c724968954`), `shopify_variants.py` (`4b7cbef6cc4428469347ae473476b5a5ae877658a735440c625f084abfcf433a`) and `test_shopify_variants.py` (`02a8e0bae82d223e533151c6f9cf52e3b58956b71d066d798501432f2e20a528`) were verified byte-identical to the branch versions by hash; the vendor-fix behaviour is unchanged.
- Post-grouping channel set used as one consistent set: `merchant_to_channels.py` (`0bce505b99196251eac962f8bd46e8b08468799912b27983f5099b2becd20aa0`), `production_pipeline.py` (`f1c6f9a3dd84fd1629baf909aeb4d51bbd1c13d89dbc9ad23331965b4e71bb1f`), `channel_ready_v4.py` (`2bb6722fc35a8e80b1a7be78399b520b54a2ea1a1bf1c4221e2613affb47cb6b`), `bstn_integration.py` (`e2aeb6191f1fc6a246cecffe7f7e4726340ac7ac24ff5fd7d77c3be52f487393`).

### Commands run (exact, from the package root)
```
python3 -m py_compile collector.py shopify_variants.py verify_six_pages.py merchant_to_channels.py production_pipeline.py channel_ready_v4.py
python3 -m unittest -v test_shopify_variants test_verify_six_pages
python3 -m unittest -v test_merchant_to_channels test_channel_ready_v4 test_production_pipeline test_grouping_e2e
python3 verify_six_pages.py --source-manifest input_pages_multi/manifest.csv --source-manifest input_pages_multi/manifest_bstn2.csv --manifest input_pages_multi/manifest_six_brand_20261113.csv --db nexus_six_brand_20261113.sqlite --out export_six_brand_20261113
```

### Compile and unit tests
- py_compile: OK for all six modules.
- `test_shopify_variants` + `test_verify_six_pages`: **10 tests ran, all OK** (exit 0). Note: the branch version of `test_shopify_variants` now contains 9 tests (the earlier report's 4/4 was an older revision).
- `test_merchant_to_channels` + `test_channel_ready_v4` + `test_production_pipeline` + `test_grouping_e2e`: **7 tests ran, all OK** (exit 0).

### Six-page acceptance run
- Merged manifest: 6 distinct saved files / URLs — BSTN 2, Notre 2, Patta 2 (host counts as required).
- Per-page results (from `six_page_acceptance.json`):

| page | host | html_sha256 | parsed | stored | pass |
|---|---|---|---|---|---|
| 1 | bstn.com | cd089d684462a4a1350a9ab720e3f1539ead012effdba1868ce73e121b213713 | 13 | 13 | true |
| 2 | notre-shop.com | 649f1195e6a8fe6b2b70344919202596ce36466779a32a0faa3ffb6188cfb5af | 16 | 16 | true |
| 3 | notre-shop.com | c0eada5205be916bdaa5d943f50dfda65df4acca1cc07d0b2d8f62318021a403 | 10 | 10 | true |
| 4 | patta.nl | 94a557898c5c48d84e332c41b7490fcd232c40ab63f2ef38e7060be5cee47207 | 6 | 6 | true |
| 5 | patta.nl | dd366268f692a4c185f42a97904d63f29acc039e6b369b601205336dc9a8adff | 6 | 6 | true |
| 6 | bstn.com | 53484dee03532157209c7d8bb779bf8b0c97bab157928e0f34518b5241ec7937 | 1 | 1 | true |

- Parsed total: **52** (BSTN 13+1, Notre 16+10, Patta 6+6 — exactly the expected counts).
- DB stage (new DB `nexus_six_brand_20261113.sqlite`): **accepted 52, rejected 0, rejection_reasons {}** — `brand_missing` is 0. The 2026-11-12 result above (13/51, 38 × brand_missing) is superseded by this run.
- Brand association in the staged DB (grouped counts): ASICS 10, Adidas 13, Jason Markk 1, Jordan 16, Patta 12. The two BSTN pages resolved to Adidas and Jason Markk from page evidence — no hostname guessing. Decisions: **HOLD × 52** (all rows).
- `six_page_acceptance.json`: verdict **PASS**, failures [], published 0, approved_for_import false; runner exit code 0.

### Channel gate check (eyeballed in the output directory)
- `channel_report_v4.json`: products 6, woocommerce_rows 58, buyma_rows 6, published 0, approved_for_import false; all 6 review entries are HOLD (`NX-HOLD-…`, "Not approved for upload or publication").
- `end_to_end_report.json`: status **REVIEW_ONLY**, products 6, woo_rows 58, buyma_rows 6, profit_rows 52, published 0, approved_for_import false.
- Channel counts match the batch expectation exactly: **6 products, Woo 58 rows (6 parents + 52 variations), BUYMA 6, profit 52**.
- Actual imports performed: 0. Actual publications: 0.

### Errors and verdict
- Errors: none at any step (no installs attempted, no re-fetch, no parser edits).
- **Verdict: PASS** — all seven acceptance conditions in docs/collector-six-page-brand-batch-2026-11-13.md are met. Scope remains "six pages parse AND stage only"; nothing is approved for import or publication.
