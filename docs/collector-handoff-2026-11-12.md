# NEXUS SELECT — Collector handoff (2026-11-12)
Goal: Python extraction of merchant product information, then separate WooCommerce and BUYMA listing-preparation outputs.

## Roles
- ChatGPT owns architecture, code, fixes, tests and consolidated decisions.
- Muse only executes provided Python on iMac and returns results; no independent coding or design changes.
- Grok may review code if actually requested and available. Never claim consensus without actual review.

## Confirmed iMac report
- Python 3.9.6; one real BSTN HTML product page yielded 13 size rows.
- Six targeted tests passed.
- DB: accepted 13, rejected 0.
- WooCommerce review: 14 rows (parent 1 + variations 13). BUYMA review: 1 row.
- Profit review: 13 rows. Extracted evidence: 13 rows.
- Published 0; approved_for_import false; REVIEW_ONLY/HOLD.
- Missing manufacturer style code and color; BSTN merchant SKU must not be used as manufacturer style code.
- Page-declared stock is not verified checkout inventory.
- Previous full suite: 72 passed, 5 errors due to missing bs4 dependency in separate tests.

## Next work batch — ChatGPT responsible
1. Read-only inventory of existing merchant URLs and products in LocalWP; keep private data off public GitHub.
2. Build compliant multi-merchant product extraction and log field completeness/failures.
3. Preserve product/color/size and merchant SKU vs manufacturer code distinctions.
4. Generate separate WooCommerce parent/variation draft and BUYMA review records; HOLD unknown fees and costs.
5. Validate WooCommerce import in staging only; no production edits or publishing.
6. Deliver one combined iMac run procedure for Muse; process failures without repeated user requests to continue.

## Safety and workflow
- Public repository: no credentials, customer details, partner information, private prices or order data.
- Branch integration/grok-review only. Do not alter main, theme, or existing 401 products.
- No live listings, orders or purchasing.
- Avoid repeated milestone reports; finish work possible before requesting external execution.
- This document is a handoff summary, not a verbatim chat log; Muse must explicitly read it.