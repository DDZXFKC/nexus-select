# Batch 3 E-1 preflight execution contract — GPT (2026-11-20)

## Decision references
- `docs/decision-log-batch3-preflight-2026-11-20.md`: GLM conditional approval.
- `docs/review-glm-batch2-2026-11-20.md`: E-1 Tasman slippers categorized as boots, historical manual correction.
- Current code: `tools/batch3_category_preflight.py`, `tools/build_buyma_batch.py` and `tests/test_batch3_category_preflight.py`.

## Actual available SP pool
Repository `collector/price-audit/sales-sellable-sp-2026-11-19.csv` contains **163 physical rows**: **152 販売可能 and 11 販売不可** based on the file's verdict column. This is a **163-row candidate pool**, not a claim of 163 currently sellable rows. Existing `tools/buyma_batch2.py` expects 158 eligible items and is **not suitable for batch3 as-is**. Do not reuse the 158 check or silently remove Vans. In particular, the five returned Vans are within the 163-row pool and must be checked against category evidence before selection.

The repository source has lowercase `sku,brand,name,verdict` and **no department**; preflight supports `sku` or `SKU`, but requires category and department evidence for chosen products. Do NOT infer department silently from product titles. Supply verified `product_metadata_by_sku` on a frozen, versioned rules file, or a new upstream verified department column in a separately pinned source export. This validation cannot be bypassed by accepting blank source department. Rows with `verdict != 販売可能` cannot PASS.

The 163-row source CSV SHA256 **must be calculated from exact source bytes and entered as `--pool-sha256`**. A Git blob SHA1 is not a substitute for SHA256. The real checksum has not been computed or asserted by GPT in this document. Use `shasum -a 256 collector/price-audit/sales-sellable-sp-2026-11-19.csv` on the actual pinned file. The preflight compares actual raw byte hash and requires 163 rows; wrong file, contents, or row count fails.

## Inputs and rules
Prepare approved selected ten SKU CSV (`sku` or `SKU` column), approved category master CSV (`category_id,product_type`), and JSON rules with:
- `version`, `dictionary_version`.
- `product_metadata_by_sku`: exact SKU -> `department` (Men/Women/Kids), `department_evidence_ref`, `verified_on`, optional source-verified `source_product_type`. Each override must derive from documented evidence.
- `category_overrides_by_sku`: exact SKU -> `category_id,evidence_ref,verified_on`; known E-1 `SP-7061016871118` is `3320` with the GLM E-1 evidence reference. A legacy single blanket Men=boots override is forbidden.
- `category_dictionary`: source-confirmed `brand,department,source_product_type,category_id,evidence_ref,verified_on` mapping entries; exact-match only.
- `brand_dept_defaults`: optional last-resort `brand,department,category_id,evidence_ref,verified_on,verified_count,verified_pool_sha256,all_items_same_category_confirmed`. The verified count must equal the **entire 163-pool brand/dept count** (requires corresponding verified metadata for the pool), otherwise default expires and HOLD. If the brand+dept contains different types without explicit overrides, do not claim all-items-same-category; prefer exact dictionary or SKU exception.

The `product_type` values of the category master must have clear semantics (boots, sandals, sneakers, etc). The warning detector checks slipper/sandal versus boot and reverse. It is a negative safety net, **not a substitute for positive category evidence and human verification**. Exact dictionary/exception entries must be approved before execution. HOLD resolution is versioned: update the relevant approved exception or dictionary, re-run frozen inputs, keep prior audits, and never patch generated BUYMA CSVs.

## Commands
```sh
python3 -m unittest discover -s tests -p 'test_batch3_category_preflight.py' -v
shasum -a 256 collector/price-audit/sales-sellable-sp-2026-11-19.csv
python3 tools/batch3_category_preflight.py \
  --pool collector/price-audit/sales-sellable-sp-2026-11-19.csv \
  --selection /actual/selected_batch3.csv \
  --category-master /actual/approved_categories.csv \
  --rules /actual/approved_e1_rules.json \
  --pool-sha256 FULL_64_CHARACTER_SHA256 \
  --output /new/batch3-preflight
# Only if exit 0 AND all ten rows PASS:
python3 tools/build_buyma_batch.py \
  --input /actual/selected_batch3.csv \
  --output /new/batch3-listing \
  --config /actual/batch3-generator-config.json \
  --prefix batch3 \
  --preflight-dir /new/batch3-preflight
```
The selected ten are exactly the ten rows in selected CSV; **selection algorithm and confirmed ten-SKU subset are separate evidence**, not invented by preflight. Preflight exits 2 when any HOLD exists, and returns zero only on all-pass. It produces `preflight.csv` and `preflight_manifest.json`, each on a new output directory. It records per-SKU `category_source=exception_map|dictionary|brand_dept_default`, pass/hold reasons, version IDs, pool, selection, category master and rule SHA256, and preflight CSV hash. Manifest `unreferenced_overrides` lists unused mappings for traceability.

Generator `--prefix batch3` now REQUIRES `--preflight-dir`. It validates receipt version, 163 count, selected input SHA, preflight CSV SHA, exact selected ten IDs, ten PASS, and category IDs. Its item category comes from approved preflight per-SKU categories, not global brand-department categories. Batch1 and batch2 output paths do not require this new flag and remain unchanged.

## Acceptance / boundaries
- Pass full tests and independent syntax checks on execution environment; compare synthetic negative routes for unknown SKU, contrary type, invalid default count, invalid pool hash, omitted evidence, and real lowercase SP columns.
- Independently compare generated BUYMA category value for each SKU against audit CSV; Tasman 3320, Neumel boot 3323 only where individually approved.
- Validate previous batch1/batch2 generator regression remains unchanged; never regenerate and overwrite their accepted outputs.
- Generated files remain drafts, not publication.
- GPT has registered source and fixtures; **no local runtime test, real 163-file SHA verification, actual category-master validation, or batch3 generation has been reported by GPT**. Muse performs real execution and GLM final acceptance. Do not claim VERIFIED before this evidence.
