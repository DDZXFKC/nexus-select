# §23 — BSTN two-result category retest
Owner rule: GitHub writes no longer require prior approval; the other agent reviews each write. Muse reviews this batch before execution. No production changes, publication, import, or paid purchases authorized.

Code d6b9b630; six tests f3aee4db. Base §22 report 4c33db64. Use fresh isolated copy of §22 package and existing isolated venv with beautifulsoup4; no global updates. Review exact diffs. Only accept result counts 1,2,3; primary index 0; every auxiliary page must be integer zero. All existing scope, release exclusion and coverage guards remain.

## 1. Regression
Run using isolated venv Python:
```sh
python3 -m py_compile stage3_catalog.py test_stage3_bstn_two_results.py
python3 -m unittest test_stage3_bstn_two_results test_stage3_bstn_primary test_stage3_bstn_listing test_stage3_bstn_release test_stage3_catalog test_stage3_bstn
python3 -m unittest discover
```
Expected full count 176 (170+6), not a claimed pass. Save stdout/stderr and exit codes. Stop on failure.

## 2. Saved seed
Use §22 seed_page_1.html, verify SHA256 6faa2c518f7dea91bc910896114149a77586ab8269519f1f3d0f3c9a5f57b8ac. listing_hits(raw,1) must return 96 URLs, 3443 hits, 36 pages, zero release URLs. No new request needed for saved page.

## 3. Live identity
Recheck storefront terms and robots, fresh permission record. Use existing Fetch gate, >=5s interval, bounded budget, no redirects. Fetch seed page 2; save raw/hash, check primary page=1, auxiliary page=0. Compare actual rendered grid for exact seed pages 1 and 2 using permitted browser; record card URLs, counts, boundaries, differences and timestamps. No media/image/release fetch. If current totals differ from saved page, record drift; use fresh same-run pages for coverage, never combine historical pages as proof. Stop if primary identity uncertain, robots disallow, HTTP error or unexpected shape.

## 4. Discovery and 5-product trial
Follow existing docs/collector-bstn-category-runbook-2026-11-13.md and §22 safeguards. Validate configured category seeds and their actual coverage; do not claim entire catalog from men's footwear alone. Fresh isolated DB and output. Complete discovery within approved budget; per seed raw unique count equals nbHits, stable totals/pages, no overlap within seed; dedupe across seeds; count excluded r/ separately, never fetch them. Then process limit 5 product pages only. All HOLD, canonical identity unverified unless separately evidenced, no publication. Verify extraction, hashes, observations, queue, exports. Stop on any inconsistency. Only after acceptance proceed to full/resume and delta per existing runbook; no budget reset to evade restrictions. Report exact counts, commands, logs, hashes, errors, remaining gates and published=0 in §23 of collector-detail-conversion-report-2026-11-13.md. ChatGPT reviews Muse's report.

## §23 regression correction (after report 89fd095c)
Legacy test_shape contradicted the new two-result contract. Commit f613d65e updates that test to assert primary-only acceptance of two results and rejection of zero/four results. No runtime changes. Muse must review the diff and rerun Step 1 including the primary suite (expected targeted 39, full 176; counts are expectations, not execution evidence). Only after full pass resume saved seed validation and subsequent gates. Preserve previous failure logs. Report correction results in §23 or §24 with exact commands and counts.
