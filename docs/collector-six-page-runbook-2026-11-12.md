# Muse next one-batch execution — 2026-11-12 (ChatGPT/Muse only)

## Basis and goal
Read docs/collector-execution-report-2026-11-12.md INCLUDING its same-day addendum. Muse already has six saved pages at /Users/discodadz/nexus-run/pkg/input_pages_multi/ (BSTN 2, Notre 2, Patta 2), all locally. Do not fetch them again. Objective of THIS batch: test the newly added Shopify parser on Notre and Patta, and the existing BSTN parser on all 6 pages, then produce one sanitized report without altering WordPress.

## Code prepared
- research/online/collector.py: routes Notre/Patta to new Shopify parser.
- research/online/shopify_variants.py: Shopify inline variants, price/size/SKU evidence, no assumption about price units, all HOLD.
- research/online/test_shopify_variants.py: four synthetic parser tests.
- Existing research/online/merchant_to_channels.py remains available; its dependencies production_pipeline.py and channel_ready_v4.py are NOT in the public repo. For full channel export use your previously validated local NEXUS_IMAC_BATCH_PIPELINE.zip package and replace ONLY collector.py and add shopify_variants.py from this branch. Do not improvise missing dependencies or change code.

## Execution steps — do all feasible steps in one batch
1. On iMac in your EXISTING local extracted package directory, back up its collector.py. Copy the GitHub branch versions of collector.py and shopify_variants.py into that package directory. Put test_shopify_variants.py there too. Do not touch LocalWP theme, DB, or 461 posts.
2. From that directory run:
   `python3 -m py_compile collector.py shopify_variants.py merchant_to_channels.py`
   `python3 -m unittest -v test_shopify_variants`
   `python3 -m unittest -v test_merchant_to_channels test_channel_ready_v4 test_production_pipeline`
3. Check the existing six-page manifest in /Users/discodadz/nexus-run/pkg/input_pages_multi/. It must contain columns html_file,product_url. Do not rewrite source HTML. Do not assume specific filenames; inspect manifest to locate it.
4. Use a **new** database and **new** output directory:
   `python3 merchant_to_channels.py --manifest /Users/discodadz/nexus-run/pkg/input_pages_multi/MANIFEST.csv --db /Users/discodadz/nexus-run/pkg/nexus_sixhost_new.sqlite --out /Users/discodadz/nexus-run/pkg/export_sixhost_new`
   Replace MANIFEST.csv with the actual filename after inspecting. Do not overwrite any prior run.
5. Inspect end_to_end_report.json and channel_report_v4.json. Check rows per host, total pages, parsed size rows, parent/variation rows, BUYMA rows, all gates HOLD, published=0. If per-host parsing fails, record exact exception and continue to inspect other hosts; do not edit parser independently.
6. The new Shopify parser is a conservative first pass based on STRUCTURAL DESCRIPTION, not yet tested on actual Notre/Patta saved HTML. It handles literal JSON variants arrays; if the pages encode variants in a different JS structure, it MUST fail closed. Do not fabricate rows. For failed hosts, report a sanitized structural description (script types, JSON nesting, field names, no full product HTML or private URLs) for ChatGPT to fix.
7. If the package's live_fetch.py allowlist still excludes Notre/Patta, it does NOT matter for this batch: saved HTML already exists. Do not rerun live_fetch or bypass blocks. If manifest references missing files, report missing file count; do not fetch again unless independently permitted.
8. Publish a single sanitized report to docs/collector-six-page-test-report.md on integration/grok-review: exact commands (without private paths if needed), Python version, pass/fail tests, page count, per-host extracted row counts, missing fields, channel export counts, errors with module/exception, any change to local environment, publish/import count (must 0). Explicitly distinguish 'parser unit tests passed' from 'six live-saved HTML pages passed'. Do not upload private source records, product URLs, credentials, raw HTML or cost data.

## Next ChatGPT task (not Muse)
Read report from GitHub; patch real HTML structure issues and repeat this test until 6 pages parse, then implement canonical evidence/field precedence, channel-specific costs and WooCommerce staging import dry-run. Do not call the full system finished before these gates.

## Mandatory operational rule
Development + Muse execution instructions + return format are ONE task. Grok is removed. GitHub document publication is not proof Muse has read or executed it; Muse reads the branch during its next execution window. User is not a messenger.

## Follow-up after Muse's six-page test report (2026-11-12)

The first report found 5 manifest rows (BSTN 1, Notre 2, Patta 2), 51 parsed variants, and 38 Shopify rows rejected for brand_missing. The current branch's shopify_variants.py now includes a conservative vendor fallback and tests for ambiguous vendors; this patch is not yet proven on the saved Notre/Patta pages. Do not claim six-page acceptance from the earlier 5-page run.

**Single next execution batch (offline, read-only):**
1. Fetch the current branch versions of research/online/shopify_variants.py, research/online/collector.py, and research/online/test_shopify_variants.py into the previously validated local package, backing up replaced files. Do not fetch merchant pages or change WordPress.
2. Run `python3 -m py_compile collector.py shopify_variants.py merchant_to_channels.py` and `python3 -m unittest -v test_shopify_variants test_merchant_to_channels test_channel_ready_v4 test_production_pipeline`. Record exact totals and failures.
3. Inspect both `input_pages_multi/manifest.csv` and `input_pages_multi/manifest_bstn2.csv`. Construct a NEW six-row manifest (BSTN 2, Notre 2, Patta 2) preserving original `html_file,product_url` references, deduplicated by exact page URL. Resolve relative html_file paths against the same source directory; verify all six files exist before running. Do not modify either source manifest or HTML.
4. Execute `python3 merchant_to_channels.py --manifest <NEW_SIX_ROW_MANIFEST> --db <NEW_DB_PATH> --out <NEW_OUTPUT_DIR>` with never-before-used DB and output names. No import, publishing, or production writes.
5. For each host, record page count, parsed size rows, accepted/rejected DB rows and rejection reasons, brand provenance (JSON-LD brand vs unique inline vendor), missing fields, channel export counts, HOLD gates and published=0. If brand_missing persists, inspect only sanitized field/key structure of the saved inline product object and variants association; do not guess a brand from shop hostname or unrelated scripts.
6. Update `docs/collector-six-page-test-report.md` with a new clearly dated follow-up section including actual commands and results, and link the six-row manifest evidence without uploading private product URLs or raw HTML. If all six pages stage, continue to the separate evidence catalog milestone; otherwise return precise sanitized failure evidence for ChatGPT. No intermediate user handoff.

**Acceptance:** six distinct saved pages present and parsed; no ungrounded brand; all valid variant rows staged or explicitly rejected with reasons; zero publish/import; every export gate HOLD. The later evidence catalog and verified stock/price/style-code checks remain separate requirements.
