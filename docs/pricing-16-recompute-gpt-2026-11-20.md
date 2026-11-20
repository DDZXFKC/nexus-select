# 16%価格改定・再計算監査（2026-11-20 / GPT）

## 最新オーナー決定
`docs/owner-decision-2026-11-20-margin-16.md`。同日暫定の19%利益率を**取り消し**、16%へ変更。原価とBUYMA手数料5.5%の旧前提を据え置いた計算式：
```
exact_procurement_jpy = USD * 158 * 1.02 + 2200 + 1500 + 60
old_19_price_jpy = ceil_to_100(exact_procurement_jpy / 0.755)
new_16_price_jpy = ceil_to_100(exact_procurement_jpy / 0.785)
```
価格は**丸め前の仕入総額から再計算**。丸め済み原価、旧19%販売価格、あるいは金額の比率換算から逆算しない。保管済み `cost_jpy` は不変（検収済みの偶数丸め）。旧 `margin_pct` は売上に対する表示上の粗利率であり、BUYMA手数料後の16%目標そのものではない。

## 19%から16%の再計算成果物
| 19%版の入力 | 16%版の出力 | SKU行数 | 19%の旧式全件照合 |
|---|---|---:|---|
| `data/pricing-19/fl_margin_19_2026-11-20.csv` | `data/pricing-16/fl_margin_16_2026-11-20.csv` | 4,781 | 4,781 PASS |
| `data/pricing-19/sp_margin_19_2026-11-20.csv` | `data/pricing-16/sp_margin_16_2026-11-20.csv` | 163 | 163 PASS |
| `data/pricing-19/sp_sellable_list_19_2026-11-20.csv` | `data/pricing-16/sp_sellable_list_16_2026-11-20.csv` | 163 | 163 PASS |
| `data/pricing-19/sp_batch3_pool_19_2026-11-20.csv` | `data/pricing-16/sp_batch3_pool_16_2026-11-20.csv` | 163 | 163 PASS |
| `data/pricing-19/batch1_items_19_2026-11-20.csv` | `data/pricing-16/batch1_items_16_2026-11-20.csv` | 10 | 10 PASS |
| `data/pricing-19/batch2_items_19_2026-11-20.csv` | `data/pricing-16/batch2_items_16_2026-11-20.csv` | 10 | 10 PASS |
| `data/pricing-19/batch3_items_19_2026-11-20.csv` | `data/pricing-16/batch3_items_16_2026-11-20.csv` | 10 | 10 PASS |

**Distinct cost-priced products = 4,944 (FL 4,781 + SP 163)**. BUYMA batch1–3 and SP list/pool are overlapping derivative datasets, not extra products. For all 4,944 rows old19 formula matched, and price changed for all 4,944.

## GitHub remote file differential
Immediately after upload GPT fetched all seven 16% outputs and corresponding 19% inputs from the repository, compared correct quoted/BOM CSV parsing row-by-row and cell-by-cell. All seven: identical headers, row counts, order and fields other than approved price-derived columns.

| File | Rows | Changed allowed cells | Other changes |
|---|---:|---:|---:|
| FL margin | 4,781 | 19,124 (4 columns) | **0** |
| SP margin | 163 | 652 (4 columns) | **0** |
| SP sellable | 163 | 163 (price_jpy) | **0** |
| SP batch3 pool | 163 | 163 (price_jpy) | **0** |
| Batch1 items | 10 | 10 (単価) | **0** |
| Batch2 items | 10 | 10 (単価) | **0** |
| Batch3 items | 10 | 10 (単価) | **0** |

The four allowable margin columns are `price_jpy`, `formula_price_jpy`, `gross_profit_jpy`, `margin_pct`. `price_match`, `cost_jpy`, `usd`, metadata and SKU unchanged. BUYMA `colorsizes` files have no price columns and remain unchanged; all category, stock, image, size, description and fixed fields in BUYMA `items` are byte-equivalent at cell level.

## Repeatable implementation
`tools/reprice_buyma_16.py` accepts a 19% margin source and new output; validates each old price against the 19% formula and independently revalidates saved rounded cost. The linked mode applies exact SKU mapping with old price guard. Tests: `tests/test_reprice_buyma_16.py`.
```sh
python3 -m unittest discover -s tests -p 'test_reprice_buyma_16.py' -v

python3 tools/reprice_buyma_16.py --mode margin \
 --margin data/pricing-19/fl_margin_19_2026-11-20.csv \
 --output /tmp/new-fl-margin16.csv

python3 tools/reprice_buyma_16.py --mode linked \
 --margin data/pricing-19/sp_margin_19_2026-11-20.csv \
 --linked data/pricing-19/batch3_items_19_2026-11-20.csv \
 --key 商品管理番号 --field 単価 \
 --output /tmp/new-batch3-items16.csv
```
All output paths must be new. The script may not mutate any source. No unverified or excluded SKU is assigned zero-cost or an invented price.

## Scope and limitations
- FL's non-saleable Converse 40 are **not priced** (not present in `fl_margin`). Full 4,821-row FL sellable list still needs local reconstruction if required, with 4,781 priced and 40 excluded. Do not treat this as permission to list them.
- BUYMA competitor matching not done; 16% remains revisable.
- USD158/card1.02/fixed fees are historical provisional source assumptions, not confirmation of today's payable shipping/taxes/fees. This is **recalculation against the existing audited cost model**, not full net profit certification.
- The live WooCommerce site, Google Sheets and BUYMA actual listings were not updated. All files are new copies in GitHub; old historical snapshots preserved.
- JavaScript-connected GitHub pipeline performed full formula checking and post-commit CSV differential audit. **Python script unit tests have not been run in an independent Python runtime**; Muse/GLM acceptance remains a separate gate.
