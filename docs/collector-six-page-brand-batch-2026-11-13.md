# Six-page brand/stage batch — 2026-11-13

## Verified state and scope
Reviewed branch snapshot 759d5be17447421e33270e9bc2cd99a472a50881.
The initial 13/51 result in collector-six-page-test-report.md is superseded for brand staging by collector-vendor-fix-report.md: saved-page vendor inspection, 51 accepted / 0 rejected. Later research/online/results/imac-2026-11-12-groupfix/RESULTS.md reports 5 products, 56 Woo rows and Notre names present.
Neither report proves a single SIX-page run. Do not add totals from overlapping runs.

The repository tree contains BSTN saved HTML, but NOT the four Notre/Patta HTML files. Those remain on the iMac. ChatGPT inspected code and returned evidence, not those private bytes. No claim of direct saved-HTML inspection is made.

Current shopify_variants.py already implements JSON-LD brand then unique vendor from scripts containing parseable variants. Retain that proven fix; do not replace it with hostname or a hardcoded brand. It is a script-level association, not a general proof that vendor belongs to the selected product. If a saved page has competing products/variants or brand/vendor conflict, STOP and return sanitized structural evidence; this batch cannot certify such input. JSON escapes and unrelated JSON-LD products are also outside the evidence established by the earlier report.

## Files, preparation, and commands
Use an isolated copy of the previously validated /Users/discodadz/nexus-run/pkg package (Python 3.9.6); preserve original files. No installs, merchant fetches, WordPress changes, imports or publishing.
From snapshot above use research/online/collector.py, shopify_variants.py, test_shopify_variants.py. Use post-grouping local-pkg merchant_to_channels.py, production_pipeline.py, channel_ready_v4.py and bstn_integration.py only as a consistent set; retain the validated package's other dependencies and existing tests. New files in this batch: research/online/verify_six_pages.py and test_verify_six_pages.py. Copy them into the package root. Record GitHub commit and SHA256 of copied files. Do not execute a mixture of pre/post grouping files.
Validate that vendor evidence from the previous report still applies to the same four input files, including a single product association; keep values, URLs and HTML local.

Run from the isolated package root:
```sh
python3 -m py_compile collector.py shopify_variants.py verify_six_pages.py merchant_to_channels.py production_pipeline.py channel_ready_v4.py
python3 -m unittest -v test_shopify_variants test_verify_six_pages
python3 -m unittest -v test_merchant_to_channels test_channel_ready_v4 test_production_pipeline test_grouping_e2e
python3 verify_six_pages.py --source-manifest input_pages_multi/manifest.csv --source-manifest input_pages_multi/manifest_bstn2.csv --manifest input_pages_multi/manifest_six_brand_20261113.csv --db nexus_six_brand_20261113.sqlite --out export_six_brand_20261113
```
If names already exist, select a NEW common suffix in all three output arguments; never delete/overwrite prior evidence. Source manifests must be in the same input directory, with html_file,product_url columns. Duplicate exact URL references may merge only when the resolved file is identical. The helper requires six distinct URLs AND files and exactly two pages per host. HTML paths are resolved against each source manifest. It writes a new manifest beside them, preserving relative paths. It never fetches.

The runner parses every page, requires nonempty grounded brands, checks duplicate staging identities, invokes the actual package pipeline once with a fresh DB, and compares per-page (source URL, SKU, size) identities against stored DB rows, brand presence and HOLD decisions. It writes sanitized six_page_acceptance.json, using page numbers and HTML hashes instead of URLs/SKUs/prices. end_to_end_report.json and CSV exports remain local because they contain product URLs and details.
Local verification in ChatGPT: current Shopify synthetic suite 9/9 plus manifest regression test 1/1 passed. This does not replace the iMac package suite or real six-page run.

## Acceptance: all conditions required
1. Compilation and BOTH test commands pass; report actual counts, not assumed counts.
2. One merged manifest has six distinct saved files/URLs: BSTN 2, Notre 2, Patta 2. Record input HTML SHA256 and per-page counts.
3. Every page parses nonzero rows. Same unchanged saved inputs are expected to yield BSTN 13+1, Notre 16+10, Patta 6+6 = 52 rows. Any difference requires explanation against source evidence; do not silently lower expected counts.
4. Every parsed row has evidenced brand; vendor ambiguity/conflict or unassociated product data is a failure. No hostname inference.
5. One NEW DB accepts all 52 expected rows, rejects 0 (including brand_missing=0), stores the exact per-page identity sets, and all stored decisions remain HOLD. Explicitly explained rejection is diagnostic evidence, NOT a pass.
6. six_page_acceptance.json verdict PASS and exit code 0. Review channel_report_v4.json separately: all gates HOLD, REVIEW_ONLY, approved_for_import=false, published=0, imports actually performed=0. Helper PASS alone does not certify this manual evidence review.
7. With the post-grouping package, expected channel sanity counts are 6 products, Woo 58 rows (6 parents+52 variants), BUYMA 6, profit 52. A mismatch fails this batch pending explanation. These are expectations, not observed six-page results.

Only after all seven checks may the report say “6 pages parse AND stage PASS”. This is not verified price units/stock, image rights, style code, costs, or import/publication readiness.

## Failure handling and return
Compilation/test/missing dependency/input/association errors: stop before stage; report exact module, exception and step. Do not install, refetch, fabricate data or edit parser ad hoc.
Runtime count/HOLD/identity failure: retain fresh outputs, mark FAIL; do not rerun into the same DB/output. Reuse requires new paths.
Return one sanitized follow-up section in docs/collector-six-page-test-report.md on integration/grok-review with commit/file hashes, Python, exact commands, test totals, manifest host counts, per-page HTML hash/parse/stored counts, accepted/rejected/reasons, vendor association checks, channel counts and gate checks, actual import/publish counts, errors and verdict. Include six_page_acceptance.json data, not source manifest URLs/raw HTML. Github publication does not wake Muse or prove execution. Execution remains pending until that report arrives.
