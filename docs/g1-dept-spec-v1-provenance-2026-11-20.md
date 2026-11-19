# G-1 dept-spec v1 / provenance handling (2026-11-20)

## Status and ownership
GPT implementation, Muse fixture/real-data verification, GLM acceptance. G-1 conditional approval does not mean new changes are VERIFIED. Batch 2 (UGG 10) may proceed independently via the adapted generator; do not manually generate it. Muse owns sourcing the missing 78 A2 provenance URLs; this change does not invent or populate them.

## G-1 provenance behavior
- Input: approved A2 brand-size CSV and selected variants CSV. No source is mutated.
- A2 cm rows with missing or malformed HTTPS source URLs are **excluded as usable conversion candidates**, not fatal. Invalid rows remain represented only as evidence for HOLD attribution and exclusion counts.
- For each variant: if no usable cm remains but an applicable excluded cm row exists, status is `HOLD_NO_PROVENANCE`. Its cm/source_url stay empty. `excluded_no_provenance` counts applicable excluded rows.
- If an independently valid, provenance-backed candidate exists, it may match. Invalid entries never create false conflicts with valid candidates. Real conflicting **valid** cm values remain `HOLD_CONFLICT`.
- Summary stdout `excluded_a2.HOLD_NO_PROVENANCE` reports **A2 row count** across the input, not unique variants. Output `excluded_no_provenance` reports the **variant-applicable** row count. Scoped entries belonging to a different product are not applicable.
- An A2 row with no cm contributes to `HOLD_NO_JP_CM` if applicable and no usable cm exists; absent chart is `HOLD_NO_CHART`.
- Only nonblank cm requires URL; the URL check is HTTPS with non-whitespace host/string, not live external verification. Muse must verify the actual URL, authority, chart context and correct sizes.
- Known 3 UGG infant 4C variant IDs retain the `HOLD_UGG_INFANT_AMBIGUITY` override.

## dept-spec v1: department derivation contract
**Goal:** deterministic Men/Women/Kids classification with auditable dictionary and provenance, no gender inference.

1. Use explicit `department` CSV column with the versioned built-in dictionary: `men`, `mens`, `men's` → Men; `women`, `womens`, `women's` → Women; `kids`, `kid`, `children` → Kids. Case-insensitive exact matches after stripping outer whitespace.
2. Optional rules from `department_rules.a2` or `department_rules.variants`: each supplies a stable `id`, an existing `column`, and a finite exact-match `map` from raw source values to `Men`, `Women`, or `Kids`. This permits source-specific documented category/collection mappings, not arbitrary guesses. The operator must verify each mapping against originating shop taxonomy or authoritative source before adding it. A rule is scoped to the selected input; do not transplant other retailers' category semantics.
3. Every nonempty source field yields `department_evidence`: JSON array of `rule`, `column`, `raw`, `resolved`. `department_rule` records rule IDs used; `department_dictionary_version=dept-spec-v1` identifies the fixed built-in dictionary. Configured rule IDs and map must be retained alongside the run config in the audit evidence.
4. Exactly one resolved department and **no unexplained nonempty evidence** → that department. Conflicting resolved values, or a known department coexisting with an unmapped nonempty source value → `HOLD_DEPARTMENT_AMBIGUOUS`; no resolved department → `HOLD_DEPARTMENT_UNRESOLVED`. Both are human review, without guessed department or cm.
5. A2 rows with ambiguous/unresolved department are excluded from charts and counted in `excluded_a2`; selected variants with those conditions stay in the output with HOLD. An absent chart resulting from excluded A2 is not silently backfilled.
6. A category/brand, product name, shoe size, or adult/child numeric interval **must not** be used to guess department. `Unisex`, `Youth`, `GS`, `PS`, `TD`, `WMNS` are **not** mapped by default. Add only explicit source-confirmed mapping rules or request manual decision. The predefined labels are categorical output values, not evidence of real-world gender identity.

### Example config
```json
{
  "a2_columns": {
    "brand": "brand", "department": "department", "size_original": "size_original",
    "cm": "cm", "source_url": "source_url", "scope": "product_id"
  },
  "variant_columns": {
    "sku": "sku", "product_id": "product_id", "variant_id": "variant_id",
    "brand": "brand", "department": "department", "size_original": "size_original"
  },
  "department_rules": {
    "a2": [],
    "variants": [
      {"id": "approved_source_category_20261120", "column": "category",
       "map": {"mens shoes": "Men", "womens shoes": "Women", "kids shoes": "Kids"}}
    ]
  },
  "require_all_matched": false
}
```
Only use example category values if the particular vendor taxonomy was actually verified and the `category` header exists. Omit `scope` if A2 lacks `product_id`. Empty explicit department is permitted when an approved rule provides the value.

## Testing and acceptance
```bash
python3 -m unittest discover -s tests -p 'test_join_a2_brand_sizes.py' -v
python3 tools/join_a2_brand_sizes.py --a2 /local/A2.csv --variants /local/selected_variants.csv --config /local/g1.json --output /local/g1-audit.csv
```
Output is exclusive-create: supply a fresh path. For `require_all_matched=true`, HOLD causes exit 2 after writing the audit CSV. Test fixture is synthetic only: valid provenance, missing/invalid provenance, scope matching and mismatch, competing valid cm, missing cm, category-derived department, conflicting department, unknown department, A2 department exclusion, and known UGG hold. Inspect output counts and cited source URLs against actual inputs before marking VERIFIED. No real A2/variant exports or live source URLs were executed/verified by GPT during this commit.

## Compatibility
The prior ten output CSV columns remain in the same order. Four audit columns are appended: `excluded_no_provenance`, `department_rule`, `department_evidence`, `department_dictionary_version`. Consumers requiring exact ten-column headers must adapt deliberately before using the new file.
