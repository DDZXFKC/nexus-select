# AFTER HOURS CLUB / BUYMA provisional 19% price recomputation — GPT 2026-11-20

## Governing decision
`docs/owner-decision-2026-11-20-margin-19.md`: provisional target profit 19%, BUYMA fee 5.5%. Formula `price_jpy = ceil_100(exact_procurement_total_jpy / 0.755)`. All results subject to future BUYMA market comparison and reassessment of exchange/card/shipping assumptions. **Not a confirmed net realized profit**, and not a site-specific fee model.

## Source and calculation fidelity
Both historical SP and FL margin snapshots used **the same verified cost expression**:
```text
exact_cost = USD * 158 * 1.02 + 2200 + 1500 + 60
old_price = ceil_100(exact_cost / 0.745)
new_price = ceil_100(exact_cost / 0.755)
```
Calculate price from exact, unrounded cost; do **not** use rounded `cost_jpy` as price numerator. Preserve original `cost_jpy` (previously accepted Python round half-even). `gross_profit_jpy` follows historical report definition `new_price - cost_jpy`; `margin_pct` is the historical gross profit/price display metric, **not** the target 19% after BUYMA fees. Old formula reproduced for every repriced row, preventing accidental underlying price drift.

## Produced files and committed acceptance counts

| Input frozen source | Repriced output (new file, old data untouched) | Count / gate |
|---|---|---|
| `data/fl-sellable/fl_margin.csv` | `data/pricing-19/fl_margin_19_2026-11-20.csv` | 4,781 / 4,781 old formula matches; all prices changed |
| `data/sp-sellable/sp_margin_152.csv` (now 163 rows despite legacy filename) | `data/pricing-19/sp_margin_19_2026-11-20.csv` | 163 / 163 old formula matches; all prices changed |
| `data/sp-sellable/sp_sellable_list.csv` | `data/pricing-19/sp_sellable_list_19_2026-11-20.csv` | 163/163 IDs and old prices matched |
| `collector/price-audit/sales-sellable-sp-2026-11-20-batch3-pool.csv` | `data/pricing-19/sp_batch3_pool_19_2026-11-20.csv` | 163/163 IDs and old prices matched |
| `tools/batch1_items.csv` | `data/pricing-19/batch1_items_19_2026-11-20.csv` | 10/10 old BUYMA prices matched |
| `data/buyma-batch2/batch2_items.csv` | `data/pricing-19/batch2_items_19_2026-11-20.csv` | 10/10 old BUYMA prices matched |
| `collector/batch3/output/batch3_items.csv` | `data/pricing-19/batch3_items_19_2026-11-20.csv` | 10/10 old BUYMA prices matched |

Each output is a new audit-preserving CSV. No automatically published listings, Woo/Supabase/Sheets updates, or BUYMA mutations. Batch1–3 `colorsizes` files are **unchanged** because there are no price fields in them. Category, stock, image and size metadata in BUYMA `items` were copied unchanged; only `単価` was replaced.

## Known non-repriced and application boundary
- The FL sellable list has 4,821 total source rows, of which 4,781 are saleable and included in the margin file. The remaining **40 Converse classified non-sellable** have no accepted `fl_margin.csv` cost/price decision; they are **not** silently assigned a price by this job. Preserve existing HOLD/non-saleable status. This job does **not** authorize their sale.
- A complete rewritten `fl_sellable_list.csv` is **not** committed in this batch: repository connector returned empty content for that large source file, while `fl_margin.csv` was available and recalculated in full. New repricer supports regenerating the full list from local original input with `--allow-unmapped` and must report each unmapped SKU, retaining exclusions unchanged.
- The live WooCommerce site catalog, including products without traceable links to these two source pools, was not repriced or modified. These product IDs need verified original cost lineage before applying the 19% formula; do not backsolve a supposed cost from previous sale price. Any other shop absent from the documented snapshots is not included and must be accounted for when its audited cost data becomes available.
- Historical margin/sellable source CSV filenames and links remain untouched. Publication status remains previous state, except no listing mutation took place.
- Current USD158 / card1.02 / handling etc is the **documented historical assumption**, not a guarantee of actual payable taxes/duties/fees. Missing costs cannot be treated as zero. If true cost assumptions are incomplete, this is a *provisional formula-based repricing*, not a verified profitable listing. BUYMA competitor check is deferred to Muse VPN-enabled iMac.

## Reproduce / complete linked FL file (Muse local)
```sh
python3 -m unittest discover -s tests -p 'test_reprice_buyma_19.py' -v

python3 tools/reprice_buyma_19.py --mode margin \
 --margin data/fl-sellable/fl_margin.csv \
 --output /new/fl_margin_19.csv

python3 tools/reprice_buyma_19.py --mode linked \
 --margin data/fl-sellable/fl_margin.csv \
 --linked data/fl-sellable/fl_sellable_list.csv \
 --key sku --field price_jpy --allow-unmapped \
 --output /new/fl_sellable_list_19.csv
```
The second command must report 4,821 total, 4,781 repriced, 40 explicitly unmapped, with all excluded SKU identities enumerated; recheck the 40 remain non-saleable before acceptance. Do not run `--allow-unmapped` on BUYMA listing batches. Other new CSVs can be regenerated using `--mode linked --key '商品管理番号' --field '単価'` and SP margin source.

## Validation gates
1. Confirm exact SKU/row count and full original-lineage hashes; re-run old and new formulas on 100% input rows. Match old prices before updating any value.
2. Check that output differences affect only price-derived fields: margin `price_jpy/formula_price_jpy/gross_profit_jpy/margin_pct`; linked rows `price_jpy` or `単価` alone.
3. Compare exact approved category and contents of BUYMA batch1–3, source counts (10 each), no changes in `colorsizes`.
4. Run `tests/test_reprice_buyma_19.py` and real-data sample/independent recalculation (not yet executed via repository connector); GLM/Muse may sign off from executed evidence.
5. Compare BUYMA competitive listing/sold prices separately before deciding whether 19% remains valid. Any source-cost re-baseline requires re-run of entire affected pool.

## Evidence status
The GitHub-connected JS pass generated and committed seven outputs and recorded old-formula 100% matches. Python script and synthetic tests are committed but **their actual Python execution on local environment is not yet verified**. No claim of website price application or net profit verification.
