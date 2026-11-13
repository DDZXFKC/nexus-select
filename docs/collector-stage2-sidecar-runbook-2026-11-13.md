# Stage 2 sidecar first patch — 2026-11-13
Audit reviewed. New isolated prototype stage2_review.py (416b01d5) and test_stage2_review.py (31ce0a82) under research/online/local-pkg. Do not replace baseline pipeline. This is not full stage 2 acceptance.
Copy both into pkg_stage2_20261113. Run:
```
python3 -m py_compile stage2_review.py test_stage2_review.py
python3 -m unittest -v test_stage2_review
python3 stage2_review.py --csv export_six_brand_s2/extracted_evidence.csv --manifest input_pages_multi/manifest_six_brand_s2.csv --db stage2_history_new.sqlite --out stage2_review_new
```
Expect 52 input, 52 observations, replay 52, 52 provisional variant IDs, all HOLD, no import. Compare source URL/hash mapping. Capture time deliberately unknown, not parse time. Synthetic cost test 21850 cost, 5110 profit; missing cost blank. New IDs are provisional, not replacements for existing export IDs. No cross-merchant merge. No live fetch.
Remaining work: actual extraction of structured product fields and per-field provenance, Shopify option mapping and price unit evidence, verified stock, explicit accessory classification and simple export, canonical identity verification, cost evidence integration, channel conversion and full acceptance tests. Sidecar does not yet solve these. For next patch provide sanitized minimal actual JSON-LD Product/Offer and Shopify parent options/variant snippets (field names, types, representative values; no full HTML or private data), including Jason Markk and Notre combined titles. Report exact tests and results in collector-detail-conversion-report-2026-11-13.md. No user relay, no WordPress changes.
