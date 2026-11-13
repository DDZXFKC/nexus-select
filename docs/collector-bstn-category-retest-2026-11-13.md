# BSTN §21 — Muse execution handoff
Owner approved code, tests and runbook. Code 3425dc9. Seven isolated synthetic tests passed in ChatGPT environment; full package suite not run there because git clone DNS failed. 
1. Fetch latest branch into isolated package; preserve previous DB/logs. Run py_compile and python3 -m unittest test_stage3_bstn_primary test_stage3_bstn_listing test_stage3_catalog test_stage3_bstn; then full unittest discover (expected 165 if unchanged baseline 158). Record actual counts.
2. Validate saved subcat.html and page 1/2 HTML. Primary result 381/4, 96 hits each, no overlap, auxiliary results excluded. Verify query/filter metadata if available and that index 0 is the requested listing, not merely page-matching; stop if identity cannot be established. 
3. Saved probe with groupextra is outside current listing_scope. Verify exact categories-only approved seed and its page 1/2 saved HTML before activating config. Do not assume 381 for this seed. If filtered seed required, stop and report exact URL/metadata for scope review. 
4. Follow docs/collector-bstn-category-runbook-2026-11-13.md for robots/terms permission gate, five-product limit, HOLD and resume. No media host, production, import or publication. Stop on denial or shape drift. 
5. Record actual results and commit in report §21. ChatGPT reviews next. No owner relay required.
