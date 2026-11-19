# BUYMA Batch 3 plan: E-1 category prevention and preflight (2026-11-20)

Status: GPT plan, awaiting Muse execution / GLM acceptance. The current generator is unchanged by this plan. Continue approved batch generator workflow; do not manually edit generated output. Cross-shop integration is later than FL cost validation and **does not block batch3**.

## Evidence and failure
GLM batch2 acceptance: E-1 (SP-7061016871118, UGG Tasman Slipper Mens Sandals) generated category `3323` ("Men = boots") rather than approved sandal `3320`. The report recorded manual one-cell correction and accepted the exception, requiring prevention in the next run. This is a category *product-type* problem: department (`Men`) is not enough to infer category (`boots`, `sandals`, etc). Avoid inferring solely from department. Current generator `cfg['brands'][brand]['categories'][div]` cannot distinguish these.

## Proposed required rule order
1. Approved exact-SKU exception mapping `category_overrides_by_sku`: example `{"SP-7061016871118": {"category_id": "3320", "reason": "UGG Tasman Slipper Mens Sandals; GLM E-1 acceptance", "evidence_ref": "docs/review-glm-batch2-2026-11-20.md"}}`. This is **known precedent**, not an authorization to apply 3320 to other slippers.
2. Approved exact-model+shop product-type dictionary (optional in later version), only when backed by official product type evidence and BUYMA category lookup.
3. Brand + department default `cfg.brands[brand].categories[department]` only when **all selected items** under that brand+department were independently verified to share the same BUYMA category. Never make blanket Men=boots or Women=boots without checking exceptions.
4. Unknown or contradictory type, multiple candidate BUYMA categories, or missing category evidence -> `HOLD_CATEGORY_REVIEW`; block generation for that SKU, provide row-level audit; do not substitute general default.
5. SKU exception's exact ID must be checked against approved BUYMA categories master, and its reason and evidence retained in the run manifest. Missing/unknown category ID -> HOLD.

## Mandatory preflight before generator launch
Preflight runs on the *selected exact ten* (or approved selection count, retaining existing ten-SKU generator gate) and joins SKU, original retailer description/type, brand, department, intended BUYMA category ID, approved category-name, evidence ref, and exception resolution source. It MUST:
- detect slipper/sandal/boots/shoes type contradiction with broad brand/department default, using a warning keyword detector only; ambiguous matching remains human review, never an automatic category guess;
- flag all identified slipper/sandal products when inherited default is boots, even if SKU is not the historic Tasman SKU;
- enforce a concrete approved category ID per SKU; reject unknown products or no evidence and check against current approved BUYMA category master;
- ensure each exception SKU is among the selected IDs or report stale/unreferenced overrides separately; reject conflicting/multiple rules;
- verify approved price, color_ids, size HOLD status and source stock snapshot (existing generator checks still apply);
- emit a preflight CSV with `sku,brand,department,source_product_type,default_category_id,selected_category_id,category_source,evidence_ref,preflight_status,reason` and a JSON manifest with input hashes and exception dictionary version;
- fail closed (nonzero exit) if any selected SKU is `HOLD_CATEGORY_REVIEW`, **before** creating final BUYMA output.

## Generation and regression checks
1. Freeze input snapshots, current BUYMA category master and the approved exact-category rule set. Check against source product type and BUYMA category taxonomy first.
2. Run preflight; require all selected rows PASS, audit E-1 known fixture `SP-7061016871118` resolves 3320 and other verified UGG Men boots remain 3323.
3. Feed `approved_category_by_sku` into **adapted generator**. Replace the single-category expression at generation time with `category_overrides_by_sku.get(sku, default)` **only after preflight approval**; preserve other item/size columns. No manual correction of generated CSV.
4. Assert every resulting items row category equals preflight-approved ID, and all size rows remain correct; reject batch if mismatch. Preserve 10 selected rows, output exact same BUYMA header/order/BOM/CRLF.
5. Regression fixtures: (a) Tasman Men Sandals 3320, (b) UGG Men Neumel boots 3323, (c) mixed-category brand+department batch, (d) undisclosed new slipper conflicts with blanket boot mapping -> HOLD, (e) no category evidence -> HOLD, (f) expired/wrong category-ID override -> HOLD, (g) no category variation -> unchanged legacy output.
6. Save generation artifacts and sha256 immediately; Muse checks actual CSV and GLM verifies. Do not publish/list products automatically.

## Sequence and dependencies
Batch2: GLM accepted (exception E-1 historically documented). Batch3 starts via approved adapted generator; E-1 preflight/code enforcement is **mandatory before batch3 BUYMA CSV generation**. FL costing independently precedes future cross-shop work. The cross-shop adapter is a **later** task; do not make it a batch3 gate.

## Ownership
GPT: proposed category-rule preflight and generator change plus regression tests as a follow-on implementation. Muse: actual selected ten SKUs + category master validation + run + evidence. GLM: approve rule set and verify outputs. Claude: site-specific only. No source mutation.
