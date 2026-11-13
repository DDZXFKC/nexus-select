# Stage 2 price representation retest — owner approved
Based on report §13 faac8df0. Copy stage2_detail.py (73b917cd) and test_stage2_detail.py (14ea3b2b) from integration/grok-review into isolated pkg_stage2_20261113. Preserve all prior outputs.
```
python3 -m py_compile stage2_detail.py test_stage2_detail.py
python3 -m unittest -v test_stage2_detail
python3 stage2_detail.py --manifest input_pages_multi/manifest_six_brand_s2.csv --out stage2_detail_price_retest.json
```
Expect 21/21 tests and counts [13,16,10,6,6,1], total52. Compare all 38 Shopify variant IDs, raw minor integer and Money amount/currency independently using Decimal; USD/EUR only for minor conversion, require same-variant explicit Money currency, no guessing. Null image is missing, not conflict. Conflicting values, malformed prices, unknown currency or unsupported minor currency stop page. Major-only currencies retain existing three-letter format validation. No change to raw-byte hashing or parent/variant conflict gates.
Verify zero duplicates/wrong merges, 52/52 original raw HTML hashes, all HOLD, canonical IDs blank, rights UNKNOWN, Shopify stock UNKNOWN, no publication/import. Compare all field coverage and baseline values, report any missing or unexpected data. Output price retains original Money amount type, not a new verified price. Use fresh output name if needed. If failures, record exact conflict and sanitized shapes; do not bypass.
Append results to collector-detail-conversion-report-2026-11-13.md under owner approval rules. No network, production DB, WordPress or main changes. ChatGPT has not independently executed tests. This is extraction retest only, not full stage 2 acceptance.
