# 横断統合 CSV interface v1 — GPT / GLM reconciliation (2026-11-20)

Status: **PROPOSED contract, not implemented**. GLM final decision controls. Scope: CSV-only source arbitration after FL cost validation; no integrated database, no source writes, no inventory polling. BUYMA batch3 proceeds through approved adapted generator.

## Decisions accepted
1. Cross-shop key = **normalized brand + complete manufacturer model code including color suffix**, both exact. No model code => exclude from cross-shop, preserve shop-only listing candidate. Never match by similar name, image, base model without color, UPC guess, or fuzzy text.
2. Winner = minimum verified procurement total (JPY), followed by source observed freshness (newest UTC), cost-calculated flag (true), fixed configured shop priority, finally stable source row ID for reproducibility. Cost-calculated=false or missing component => not eligible to win: do not treat missing as zero. Tie-breaker cost flag remains recorded even though eligible candidates have it true. If no eligible candidate, group HOLD. Incoming stock observation is not a promise of stock at purchase; verify at order placement/actual purchase, no periodic background stock recheck.
3. **FL cost validation and full-cost inputs first; cross-shop implementation second; BSTN integration last.** SP can remain independent while FL lacks verified costs. No premature cross-shop deployment.
4. Pure deterministic CSV transform from pinned input CSV snapshots + versioned config to pinned output CSVs. No merger DB; no source mutations. Outputs: chosen listing-facing rows, per-offer audit, non-crossable shop-only rows, HOLD rows. Re-runs with identical inputs/config give identical bytes, excluding run timestamps (timestamps belong in external manifest).

## Normalization and identity
- Brand aliases exist **only in a versioned, approved exact mapping**; use Unicode NFKC, trim and collapse whitespace, casefold for comparing brand tokens. Unknown alias => HOLD brand identity; do not automatically fold different brands.
- Model code: Unicode NFKC, trim and uppercase; collapse internal whitespace only if manufacturer-specific documented rule permits. No stripping hyphens, slashes, digits, model prefixes or suffixes, and especially no color-code truncation. If unconfirmed syntax, HOLD match. Require an evidence field for the complete code, preferably manufacturer's SKU or product detail; retailers' IDs are not substitutes.
- Matching key canonical serialization: `brand_norm + "|" + model_code_full_norm`. Validate delimiter escaping or use a length-delimited key in code; source CSV keeps separate columns.
- Same shop may have duplicate entries: use source listing ID plus snapshot and size for row identity, never silently collapse competing records.
- Matching at **product/colorway** level; per-size stock/price remains per-shop/per-offer evidence. Do not pretend a cheaper shop has sizes only offered elsewhere. If selection is size-specific, perform independent winner evaluation per size and retain product-level grouping; design gate before coding.

## Source offer input CSV v1 (one row per shop × colorway × sellable size or explicitly documented aggregate)
Required header | Type / semantic:
| Field | Rule |
|---|---|
| `source_row_id` | stable nonempty string, unique within each pinned input |
| `shop_code` | fixed code e.g. `SP`, `FL`, `BSTN` |
| `source_product_id` | original shop product identifier |
| `source_variant_id` | original variant/size identifier; blank only for documented product-level offers |
| `source_url` | canonical retailer URL |
| `brand_raw` | original brand |
| `brand_norm` | approved normalized canonical brand |
| `model_code_full_raw` | original complete manufacturer style/model code incl. color code, may be blank |
| `model_code_full_norm` | normalized full code, blank when unverifiable |
| `model_code_evidence_url` | proof of code + color suffix; nonblank for crossable |
| `department` | `Men` / `Women` / `Kids` / blank; use dept-spec v1 evidence |
| `department_evidence` | provenance/evidence JSON escaped in CSV |
| `size_original` | vendor source size, not guessed US conversion |
| `size_normalized` | verified normalized size, blank if unresolved |
| `observed_at_utc` | RFC3339 UTC source observation timestamp, not generation time |
| `stock_observed` | `IN_STOCK`, `OUT_OF_STOCK`, `UNKNOWN`; observation only |
| `currency` | original source ISO currency |
| `item_price_local` | Decimal original sale price |
| `shipping_local` | Decimal if confirmed |
| `local_tax_local` | Decimal if confirmed |
| `fx_to_jpy` | Decimal >0 from recorded rate source/time |
| `import_duty_jpy` | Decimal if confirmed |
| `import_tax_jpy` | Decimal if confirmed |
| `partner_fee_jpy` | Decimal if confirmed |
| `other_procurement_jpy` | Decimal if confirmed, including any relevant conversion/handling fees |
| `procurement_total_jpy` | Decimal rounded only after all components; independently auditable |
| `cost_calculated` | `1` only if every applicable component determined; 0 otherwise |
| `cost_evidence_ref` | local/URI audit reference to rate, tax, shipping and fees |
| `price_approved_jpy` | approved BUYMA customer sale price (not source procurement price), may be blank |
| `listing_title` | approved listing title |
| `listing_images` | JSON array of source image URLs |
| `description_en` | original description |
| `source_snapshot_sha256` | source snapshot identity |

Unknown shipping/tax/fees = blank; **0 only with positive evidence of zero liability**. No amount or missing value interpreted as zero.

## Cross-shop output CSV v1: `crosswalk_selected_v1.csv`
One row per **eligible selected offer** (product-colorway-size if per-size model); one non-crossable shop-only offer also may pass if independently eligible for listing. Header and rules:

| Column | Meaning |
|---|---|
| `schema_version` | constant `crosswalk-selected-v1` |
| `listing_group_key` | canonical brand+full style code key, or `SHOP_ONLY:<shop_code>:<source_product_id>` when no model |
| `selection_scope` | `CROSS_SHOP` or `SHOP_ONLY` |
| `winner_source_row_id` | exact input lineage |
| `selected_shop_code` | winning shop |
| `selected_source_product_id` | original source product ID |
| `selected_source_variant_id` | variant reference |
| `source_url` | selected shop listing URL |
| `brand_norm` | full canonical brand |
| `model_code_full_norm` | full model with color code; empty only SHOP_ONLY |
| `department` | fixed via dept-spec v1 |
| `department_evidence` | evidence, no guess |
| `size_original` | selected shop original size |
| `size_normalized` | validated size |
| `stock_observed` | source snapshot observation, not promise |
| `observed_at_utc` | source observation freshness |
| `procurement_total_jpy` | eligible complete cost |
| `cost_calculated` | must be 1 on selected rows |
| `cost_evidence_ref` | cost audit lineage |
| `price_approved_jpy` | approved selling price, independently checked |
| `listing_title` | downstream listing title |
| `listing_images` | escaped JSON array |
| `description_en` | downstream description |
| `selection_reason` | `LOWEST_COST` / `FRESHNESS_TIE` / `CALC_FLAG_TIE` / `SHOP_PRIORITY_TIE` / `SHOP_ONLY` |
| `input_snapshot_sha256` | specific input lineage |

Output CSV accompanying files:
- `crosswalk_audit_v1.csv`: **all** candidates, group key, eligibility, cost completeness, match basis, rank, winner ID, rejection/HOLD reason; never destroy loser evidence.
- `crosswalk_hold_v1.csv`: invalid/missing full model identity (when attempting cross-match), ambiguous model/brand, unconfirmed amounts, conflicting evidence, unavailable sizes. Shop-only rows with absent model are **not automatically HOLD** if independently eligible.
- `crosswalk_manifest_v1.json`: sha256 per input/config/output, normalization config version, fixed shop priority, cost rounding convention, UTC snapshot collection dates, transform version. No time-dependent value in selected CSV.

## Generator compatibility: verified current code constraints
Current `tools/build_buyma_batch.py` `main()` reads a selection CSV containing SKU (10 distinct), but then requires:
- `cfg['woo']` CSV with `Type=variable|variation`, `SKU`, `Parent`, `Brand`, `Name`, `Images`, `Regular price`, `In stock?`, `Attribute 1 value`;
- `cfg['brands'][brand]['source']` CSV keyed by `productId`, `description_en`, `url`, and extracts `sku.removeprefix('SP-')`;
- approved `brand_id`, `brand_name`, `categories[department]`, `color_ids`, `approved_buyma_prices[sku]`, A2 `size_table`, UGG `verified_kids_sizes`;
- product department guessed from product name in current version, size rows derived from Woo variants; output two BUYMA CSVs with exact columns; hard-coded purchase shop `Shoe Palace`.

**Therefore direct swapping only `--input` to the selected crosswalk CSV is NOT compatible today.** Do not claim it is. Migration:
1. During FL cost stage, freeze full source offer evidence and verify cost completeness; do not modify legacy generator.
2. Build a strict **crosswalk-to-generator adapter** after crosswalk approval: selected offer CSV + lineage -> generator-facing canonical parent/variant/source CSVs in a temporary directory, with exact size/stock attributes and unique canonical SKU; keep seller-specific ID separate.
3. Change only generator's **input normalization** and **buying-shop value** to accept canonical selected offer and source records, while preserving the BUYMA output headers, approved prices, category IDs, colors and sizes. No manual edit of generated BUYMA CSVs. Regression-test SP-only golden outputs to assure zero differences, aside from explicitly approved change.
4. Do not invent Woo stock or fake variants; if necessary source variant fields are missing, HOLD. Size matches and pricing must be verified per selected shop.
5. Add E-1 category preflight described in `docs/batch3-e1-category-preflight-plan-2026-11-20.md` before approving batch3.

## Gates
- FL: all relevant cost components evidenced, counted and audited; uncertain != zero. Failure => no cross-shop winner.
- Full model evidence: exact complete model incl color; no model => shop-only, not fuzzy combined.
- Output uniqueness: each selected group+size has at most one chosen source; audit covers every input row.
- Tie-break: minimum Decimal cost, newest observed timestamp, cost flag, versioned shop priority, stable row ID. Distinct shops may win different sizes; no unsupported mixed-shipping discount.
- Batch3 category preflight passes before generation; output category automatically matches approved exception.
- Muse real-input test, GLM final verdict before production. **Do not hold batch3 solely for future cross-shop layer.**
