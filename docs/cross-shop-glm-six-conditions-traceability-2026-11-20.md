# GLM cross-shop conditional re-review — original six conditions traceability (2026-11-20)

Status: **cross-shop RE-REVIEW PENDING**. This matrix is a precise design-to-file map, not a false declaration that production SP/FL converters or winner selector have been implemented. GLM original condition 1 is **one combined condition** (observations + divergence flag).

## 6 original conditions → file/line → verification
| GLM original condition | Contract location (line, current branch) | Executable test ID or acceptance method | Status |
|---|---|---|---|
| **C1** chosen source all size-level price and stock observations, time/source provenance, **and** `size_price_divergent` (single condition, never split) | `docs/cross-shop-csv-interface-v1-gpt-2026-11-20.md:119-122` | On final converter fixture: compare selected-size observation JSON against all source variants incl OOS; inject a differing observed size price, assert divergence=1 but winner unchanged; check timestamp/source fields. | Spec only; adapter test pending |
| **C2** verified procurement total unit and comparability | same `:117-124`, specifically `:123` `COLORWAY_ONE_UNIT` | Feed SP/FL one-price-per-colorway evidence, ensure no row-level size allocation, reject unsupported per-size cost and all missing components. FL GLM fixed HALF_EVEN pipeline is separate costing concern. | Source-unit specified; integration pending |
| **C3** eligibility = cost-calculated AND total-verified | same `:124` | Inject (0,1),(1,0),(1,1) and assert only last eligible; cost-flag tie break redundant defensive no-op. | Spec only; selector test pending |
| **C4** candidate-level HOLD reason codes | same `:125` | For absent fee/unknown total model, ensure audit has `cost_uncalculated`/`total_unverified` per candidate, none silently zeroed. | Spec only; selector test pending |
| **C5** normalization fixtures, FL/SP raw→offer conversion roundtrip and duplicate-key audit | same `:129-131`; executable lossless envelope `tools/cross_shop_offer_contract.py:17-75`; tests `tests/test_cross_shop_offer_contract.py:24-77` | **Runnable IDs:** `test_C5_SP_RAW_OFFER_ROUNDTRIP`, `test_C5_FL_RAW_OFFER_ROUNDTRIP`, `test_C5_BRAND_ALIAS_AND_FULLWIDTH`, `test_C5_MODEL_LEADING_ZERO_AND_SEPARATOR_NOT_COLLAPSED`, `test_C5_UNKNOWN_ALIAS_HOLD`, `test_C5_RAW_TAMPERING_DETECTED`, `test_C5_DUPLICATE_SHOP_KEY_REJECTED`, `test_C5_SP_FL_SAME_COLORWAY_ALLOWED`. The current tests are **synthetic testable raw-offer envelope contracts**, NOT actual FL/SP source schema conversion. Actual retailer converter roundtrip and FL six-point checklist transfer remain pending. | Contract and executable fixture files registered; production conversion pending |
| **C6** final stable source row identity | same `:129`; `tools/cross_shop_offer_contract.py:33-38`; `tests/test_cross_shop_offer_contract.py:67-71` | `test_C6_STABLE_ID_UNAMBIGUOUS` (length-prefixed identity) and `test_C5_DUPLICATE_SHOP_KEY_REJECTED` | Identity contract + tests registered; selector pending |

### Execution commands / test discovery
```sh
python3 -m unittest discover -s tests -p 'test_cross_shop_offer_contract.py' -v
python3 -m unittest discover -s tests -p 'test_buyma_batch3_stock_gate.py' -v
python3 -m unittest discover -s tests -p 'test_batch3_category_preflight.py' -v
```

## Specific distinctions for GLM review
- C1 is a **single original condition**, observations and divergent flag together.
- Cross-shop selection is **one winning shop at colorway level**, never size-specific. Source's observed variants are attached to that winner as read-only evidence. Source actual stock is confirmed **at purchase**, not an input to cross-shop acceptance or BUYMA batch3 generation.
- SP/FL margin feed currently gives one colorway-level price, not per-size landed costs; observed per-size price and stock are separate non-ranking fields. If source cost granularity changes, do not compare without new approval.
- The FL six-point checklist GLM confirmation: `docs/review-glm-fl-checklist-2026-11-20.md` (all six closed, ties to Python round HALF_EVEN semantics and pre-rounded threshold); converter real-data fixture cannot be claimed complete until the actual six-point report + source raw CSV mapping are embedded. The file `data/fl-sellable/fl-checklist-report.md` is the relevant source report.
- Existing `docs/cross-shop-csv-interface-v1-gpt-2026-11-20.md` contains older per-size text **superseded by its GLM amendment**. Do not implement the older text.
- No real production cross-shop selector exists at these paths today. C1–C4 remain **spec with future acceptance tests**, not demonstrated executable pass; C5–C6 have **runnable synthetic contract test IDs** with no claim of real retailer conversion.

## Separate batch3 stock resolution (not one of six cross-shop conditions)
- `tools/build_buyma_batch.py:72,97-98,159`: `allow_zero_stock` changes only for prefix=batch3, and passes original `In stock?` through to `colorsizes`; missing variations still error.
- `tests/test_buyma_batch3_stock_gate.py` has `test_stock_b1_b2_zero_still_rejected`, `test_stock_b3_zero_preserved_in_colorsizes`, `test_stock_b1_b2_in_stock_unchanged`, `test_stock_b3_does_not_allow_missing_variants`, `test_batch3_flag_only_set_by_prefix`.
- Muse's blocker document `docs/batch3-generation-blocker-maou-2026-11-20.md` was referenced in user handoff but **not present in this branch at GPT fetch time**. The precise blocking expression was independently read from current generator. Do not invent its content or claim to have inspected it.

## Test evidence
Source and fixtures committed, but GitHub connector cannot execute Python. Until Muse or independent runtime executes these exact IDs, treat them as **registered, not VERIFIED**. GLM acceptance should distinguish executable synthetic contract tests from actual SP/FL converter integration.
