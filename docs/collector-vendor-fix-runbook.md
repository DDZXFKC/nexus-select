# Muse execution — Shopify brand fallback verification (2026-11-12)

## Verified input
Read docs/collector-six-page-test-report.md: 5-page manifest (BSTN 1, Notre 2, Patta 2) parsed 51 rows, 13 accepted, 38 rejected brand_missing. Second BSTN page is in separate manifest_bstn2.csv. No fetching necessary.

## Changes to execute
On integration/grok-review, research/online/shopify_variants.py now checks JSON-LD brand first and falls back to a **single unambiguous** vendor value from a script containing parseable variants. Shop hostname is never used as brand. research/online/test_shopify_variants.py adds fallback and ambiguity tests. This code is NOT verified against the private saved HTML yet. If no vendor field is present, the correct behavior is to keep brand empty and reject rather than invent.

## Single-batch procedure
1. Read both changed files from GitHub and copy them into the already tested local extracted package, backing up the previous shopify_variants.py. Do not edit code.
2. Run `python3 -m py_compile collector.py shopify_variants.py merchant_to_channels.py` and `python3 -m unittest -v test_shopify_variants test_merchant_to_channels test_channel_ready_v4 test_production_pipeline`.
3. Check **only the four saved Notre/Patta HTML files** locally, without uploading content, to establish whether vendor is present in the SAME script as variants. Record vendor-present count per host and whether multiple distinct vendor values appear. Do not use hostname as a guessed brand.
4. Run existing 5-row input_pages_multi/manifest.csv with a NEW DB nexus_vendorfix_new.sqlite and NEW output directory export_vendorfix_new, using merchant_to_channels.py --manifest ... --db ... --out ... . Never overwrite previous evidence.
5. Check per-host parsed rows, stage accepted/rejected, reasons, WooCommerce/BUYMA CSV counts, HOLD/REVIEW_ONLY and published=0. If all 38 formerly rejected rows now pass brand validation, note that this proves only brand staging, NOT manufacturer code, stock, rights, cost, or publication readiness.
6. If some rows remain brand_missing, report the actual sanitized key structure around product/variants, whether a vendor field exists and where (nested object vs different script). Do not invent a brand, do not edit code independently. If another error occurs, include the exact exception and step.
7. If the 5-row batch succeeds, separately run the second BSTN saved page with a NEW DB/output or add it to a new SIX-row manifest only after verifying paths; do not claim 6 pages were in the original manifest.
8. Return ONE sanitized GitHub report to docs/collector-vendor-fix-report.md: test results, page/host row counts, vendor evidence present/absent, DB accepted/rejected, export counts, missing fields, errors, and no live modifications. Never upload source HTML, private inventory, or pricing details.

## ChatGPT responsibility
Read report, correct remaining real-HTML issues and produce next bundled patch + Muse instructions without waiting for user to relay results. Grok excluded. GitHub writing does not automatically wake Muse; hourly monitor is a polling fallback, not instant delivery.
