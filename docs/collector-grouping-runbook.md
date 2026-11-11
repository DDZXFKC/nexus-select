# Muse batch: Shopify product grouping and name evidence — 2026-11-12

## Input and goal
Read docs/collector-vendor-fix-report.md. Vendor fix passed 12/12 tests and 51/51 staged rows. Five-page exports had 39 products and 90 Woo rows because Shopify size rows were treated as distinct products; Notre lacked product_name. Goal: validate a conservative source-page-scoped temporary product_id and investigate real product name source. Do NOT claim a verified manufacturer style code or cross-shop dedup.

## Code
Updated research/online/shopify_variants.py: every variant on the same source URL gets the same deterministic SHA256 temporary product_id, while different merchant URLs cannot be merged; missing name may be filled only from one unambiguous title/name string in the script containing variants (if multiple candidates, remains blank). All rows HOLD. Tests added in research/online/test_shopify_variants.py. Code is untested against saved iMac pages. DO NOT change the pipeline or assume this will fix downstream grouping; it depends on unseen local channel_ready_v4.py.

## Execute once, no user relay
1. Copy latest two files from integration/grok-review to local validated package, backup originals; leave LocalWP unchanged.
2. Run `python3 -m py_compile collector.py shopify_variants.py merchant_to_channels.py`; `python3 -m unittest -v test_shopify_variants test_merchant_to_channels test_channel_ready_v4 test_production_pipeline`.
3. Run original five-row manifest.csv (BSTN1 Notre2 Patta2) using a **new** DB nexus_grouping_new.sqlite and output export_grouping_new, via `python3 merchant_to_channels.py --manifest input_pages_multi/manifest.csv --db nexus_grouping_new.sqlite --out export_grouping_new`. Do not fetch or overwrite previous runs.
4. Report: 5-page parsed/staged counts, products per host, Woo/BUYMA rows, grouping by product_id or other field, missing product_name counts, HOLD and published=0. Compare against previous 39 products / 90 Woo rows. If unchanged, do not patch unseen dependencies: inspect local channel_ready_v4.py grouping key and stage FIELDS, report the relevant **non-secret** grouping-key logic/field names, and indicate whether product_id is included in FIELDS. Do not upload local source code if it contains secrets.
5. For Notre, inspect locally whether the **parent product title/name** is available in the same JSON object as vendor and variants; report only the field path and whether 2/2 pages contain it, not product names or raw HTML. Never substitute variant size title as product name.
6. If parse/stage/export fails, record exact error and stop that run; preserve outputs and continue to report. No manual publication, product import, theme edits or order changes.
7. Save one sanitized report to docs/collector-grouping-test-report.md on integration/grok-review. Include test pass count, row/product counts, fields, exceptions, and next code-change target. No Grok involvement.

## Acceptance
The batch is complete when factual staging/grouping/name evidence is returned. Full product grouping is only accepted if 5 pages yield 5 merchant-page products (BSTN1 Notre2 Patta2) with 51 variants, while all records remain HOLD; otherwise ChatGPT will patch the actual downstream grouping based on returned code evidence. The separately saved BSTN2 is not in the five-page manifest.
