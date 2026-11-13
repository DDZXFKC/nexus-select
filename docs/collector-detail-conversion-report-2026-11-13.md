# Collection ② — detail conversion evidence audit report — 2026-11-13 (Muse execution)

Batch: docs/collector-detail-conversion-batch-2026-11-13.md (commit 611b0519). Baseline: the stage-① report at commit 847bd137 (six saved pages, 52 accepted, 0 rejected, 6 products, Woo 58, BUYMA 6, profit 52, 17 tests). This batch is offline only: no installs, no live fetching, no WordPress changes, no imports, no publications.

## 1. Baseline reproduction (isolated copy, new output paths)

- New isolated copy of the validated package: `/Users/discodadz/nexus-run/pkg_stage2_20261113` (original package preserved untouched). `verify_six_pages.py` / `test_verify_six_pages.py` copied in from snapshot 5f0896ca (sha256 65f5da94… / 5050b6db…, as in the stage-① report). All other module hashes identical to stage ①.
- Exact commands (package root):
```
python3 -m py_compile collector.py shopify_variants.py verify_six_pages.py merchant_to_channels.py production_pipeline.py channel_ready_v4.py
python3 -m unittest -v test_shopify_variants test_verify_six_pages
python3 -m unittest -v test_merchant_to_channels test_channel_ready_v4 test_production_pipeline test_grouping_e2e
python3 verify_six_pages.py --source-manifest input_pages_multi/manifest.csv --source-manifest input_pages_multi/manifest_bstn2.csv --manifest input_pages_multi/manifest_six_brand_s2.csv --db nexus_six_brand_s2.sqlite --out export_six_brand_s2
```
- Results: py_compile OK; unittest **10/10 OK** and **7/7 OK** (17 total, exit 0/0); verify verdict **PASS**, exit 0.
- Comparison with baseline: per-page HTML sha256 **identical for all 6 pages**; parsed/stored counts identical (BSTN 13+1, Notre 16+10, Patta 6+6 = 52); stage accepted 52 / rejected 0 (rejection_reasons {}); channels 6 products / Woo 58 / BUYMA 6 / profit 52; published 0; approved_for_import false. **Baseline reproduced exactly.**

## 2. Actual source structure (from the executed code)

Flow: `collector.parse` → `merchant_to_channels.run` → `production_pipeline.stage` + `profit_review` → `channel_ready_v4.export`.

- **Extraction — BSTN** (`collector.py`, JSON-LD Product nodes): brand/sku/name/color from the Product node; per offer: price (`offer.price`, else `priceSpecification.price`; must be > 0), `priceCurrency`, availability (schema.org suffix), size = `offer.size` or product `size` (empty string when absent). In-page dedup key (brand, sku, color, size, offer_url, price). `product_id` = sha256(brand|sku|color|size)[:18] — **per-variant**.
- **Extraction — Notre/Patta** (`shopify_variants.py`): the largest inline `variants` array containing sku/price; brand = JSON-LD brand, else the single unambiguous `"vendor"` string in the variants-bearing script (fails closed to empty); name = JSON-LD name, else the parent object's title; size = variant `public_title`/`title`/`option1`; price = variant price (`amount` if a Money dict); currency = variant `currencyCode`/`currency`, else JSON-LD offer `priceCurrency`; **`availability_claim` is always ''** (variant availability is never read); `product_id` = sha256('merchant-page|'+url)[:18] — **per-page**. The parser's own hold reasons flag PRICE_UNIT_UNVERIFIED / SIZE_STOCK_UNVERIFIED / MANUFACTURER_CODE_UNVERIFIED / IMAGE_RIGHTS_UNVERIFIED.
- **Record build** (`merchant_to_channels.run`): fixed FIELDS list; **`manufacturer_sku` and `image_rights` are forced to '' for every record**; everything else passes through from the parser.
- **Stage** (`production_pipeline.stage`): mandatory sku/size/brand/price/currency/observed_utc; price must be finite ≥ 0; currency must match `[A-Z]{3}`. Primary key **(source_url, merchant_sku, size)** in both `merchant_evidence` and `product_enrichment`. INSERT … ON CONFLICT DO UPDATE (see §5). Every row gets verification_state='UNVERIFIED', decision='HOLD'.
- **Profit** (`production_pipeline.profit_review`): cost = (source_price + shipping_cost) × fx_jpy + import_tax + partner_fee + international_shipping; profit = selling_price_jpy × (1 − platform_fee_rate) − cost. Computed only when all 7 cost inputs are valid money; otherwise cost/profit stay blank and the missing inputs are listed. Structure note (confirming the batch doc): a single `import_tax` lump (no separate duty vs import-consumption-tax lines), no explicit FX fee, no fixed channel fee (percent only).
- **Channels** (`channel_ready_v4.export`): group key (source_url, discriminator, color_claim); discriminator = product_id **iff** exactly one distinct non-empty product_id covers the whole page, else merchant_sku; group display fields come from the group's **first row**; parent SKU = `NX-HOLD-` + sha256(group key)[:16]; variation SKU = parent + '-' + sha256(size)[:8]; Woo prices always blank, Published 0, catalog hidden; BUYMA emits one review row per group with a `size_stock_claims` JSON map; images are dropped unless image rights clear the gate.

## 3. Per-field coverage (52 staged rows; extracted_evidence = merchant_evidence + product_enrichment)

| field | BSTN (14) | Notre (26) | Patta (12) | total | status |
|---|---|---|---|---|---|
| product_url | 14 | 26 | 12 | 52 | OBSERVED |
| brand | 14 | 26 | 12 | 52 | OBSERVED (JSON-LD brand or unique vendor evidence; fail-closed) |
| name | 14 | 26 | 12 | 52 | OBSERVED |
| sku (merchant) | 14 | 26 | 12 | 52 | OBSERVED |
| manufacturer_sku | 0 | 0 | 0 | **0** | UNKNOWN — blanked by design; merchant SKU is never promoted |
| color | 0 | 0 | 0 | **0** | UNKNOWN as a field on all hosts (see §5: colorway text is embedded in Shopify size labels) |
| size | 14 | 26 | 12 | 52 | OBSERVED |
| price | 14 | 26 | 12 | 52 | OBSERVED as a claim; Shopify unit flagged PRICE_UNIT_UNVERIFIED by the parser itself (values are consistent with major units — Notre 180.0–225.0 USD, Patta 278–498 EUR, BSTN 18.99–27.99 EUR — but not independently verified) |
| currency | 14 | 26 | 12 | 52 | OBSERVED (EUR 26, USD 26) |
| stock / availability claim | 14 | 0 | 0 | 14 | BSTN: OBSERVED claim (InStock 4, OutOfStock 10, varies per size). Shopify: UNKNOWN — parser never reads variant availability. All stock values are page claims, not verified purchase availability (verification_state UNVERIFIED on 52/52) |
| observed_utc | 14 | 26 | 12 | 52 | Parse-run timestamp (this run: 2026-11-12T23:26Z), **not** the page capture time — the saved HTML files date from 2026-11-11 (file mtimes). Provenance gap, §5 |
| image_urls / description / category / ship_from | 0 | 0 | 0 | **0** | UNKNOWN — parsers do not extract them |
| shipping_cost / import_tax / partner_fee / international_shipping / platform_fee_rate / fx_jpy / selling_price_jpy | 0 | 0 | 0 | **0** | UNKNOWN — profit cost/profit blank on 52/52, all 7 inputs listed as missing; unknown costs are blank, never zero |
| image_rights | 0 | 0 | 0 | **0** | UNKNOWN — blanked by design; the rights gate therefore drops all images from channel exports |
| product_enrichment payload (13 fields) | — | — | — | **0/52 rows have any payload field** | 52 enrichment rows exist (keys + product_id only) |

## 4. Channel reconciliation

- Counts reconcile exactly: extracted_evidence 52 = merchant_evidence 52 = product_enrichment 52 = Woo variations 52 = profit rows 52; groups 6 = Woo parents 6 = BUYMA rows 6.
- Woo: 58 rows; every parent Type='variable' (including the Jason Markk accessory, §6); Regular price blank 58/58; Published '0' 58/58. Parent Name = brand + name (+color) from the group's first row — for Patta this doubles the brand ("Patta Patta Leather Hooded Bomber Jacket (Moonless Night)" / "Patta Patta Square Quilted Puffer Jacket (Black)") because the product name already contains the brand.
- BUYMA: 6 review rows (not an official import schema); color '' on 6/6; `missing_information` is the same 10 items on all 6: category, channel_specific_price, color, description, image_usage_permission, images, manufacturer_style_code, platform_import_validation, shipping_and_tax_confirmation, verified_size_stock.
- Profit: 52 rows, cost_jpy and estimated_profit_jpy blank on 52/52, status HOLD on 52/52.

## 5. Collision and identity audit

- **Stage key has no color component, and the upsert overwrites.** `stage()` inserts with ON CONFLICT(source_url, merchant_sku, size) DO UPDATE that replaces brand, name, color_claim, price_claim, currency, stock_claim, observed_utc, manufacturer_sku, product_id and resets verification_state/decision. Consequences: (a) replaying changed evidence silently replaces the previous observation — no history is kept; the accepted counter increments per input row even when the row overwrites an existing key, so "accepted" can exceed stored rows; (b) two colorways sharing URL+SKU+size would collapse into one stored row, the later one winning.
- **Baseline data: no collision occurred.** The 52 extracted rows have 52 distinct (url, sku, size) keys, and stored rows = 52 = accepted. The risk is latent, not observed.
- **Color blindness is currently untestable from real pages**: color coverage is 0/52. On Notre pages the colorway survives only inside the size label (variant public_title, e.g. "6 M / Lemonade/Lemonade", "8 M / Dark Gull Grey/Black") — size and colorway are entangled in one string. On the two BSTN pages the JSON-LD color was empty (single-color products; the Adilette keeps one SKU 0009238 across all 13 sizes).
- **Grouping discriminator asymmetry**: BSTN product_id is per-variant (the Adilette page carries 13 distinct product_ids) so grouping falls back to merchant_sku; Shopify product_id is per-page so grouping uses it. A JSON-LD merchant page with per-variant product_ids **and** size-specific SKUs would split into one group per size (the pre-grouping-fix failure mode). Not triggered by the baseline pages.
- Variation SKUs are parent + sha256(size): unique per group because the parent prefix differs; sizes within a group are a deduplicated sorted set.
- No cross-store merge exists anywhere in the pipeline (every key includes source_url) — consistent with the no-merge-without-verified-identity rule.

## 6. Jason Markk accessory — determination

- The single staged row: brand "Jason Markk", name "4 oz. Premium Shoe Cleaning Kit", merchant SKU 0012650, price 18.99 EUR, availability claim **OutOfStock**, size **"ONE SIZE"**.
- Evidence: the string `ONE SIZE` occurs 3 times in the saved page HTML (bstn_02.html) and 0 times in the other BSTN page; `collector.py` emits size='' when the JSON-LD carries no size, so "ONE SIZE" is **the merchant's own structured-data label for a size-less product — a placeholder, not a real size**. The page has a single offer / single SKU (no size run).
- Current conversion types it as a Woo 'variable' parent with one "ONE SIZE" variation, which misrepresents a simple product. Recommendation for the patch (no code changed in this batch): treat single-offer accessories with placeholder size labels (ONE SIZE / OS / equivalent) as simple products and do not fabricate a size attribute.

## 7. Dependencies returned to the repository

- `research/online/local-pkg/` already held the executed post-grouping set — merchant_to_channels.py (3,502 B), production_pipeline.py (6,575 B), channel_ready_v4.py (5,477 B), bstn_integration.py (2,593 B), test_channel_ready_v4.py, test_grouping_e2e.py — byte-identical to the executed package (hash-verified in the stage-①/② runs).
- Missing from the repo and added in a separate commit (sanitized: source code and synthetic test fixtures only; scanned — no credentials, no private data, no raw HTML):
  - `channel_exports.py` — sha256 ee4393c13081cbec0d0b2205a257b3b85ea805e7bc92c87f3874831063b4096f — **runtime import of channel_ready_v4** (`from channel_exports import safe`)
  - `channel_exports_v2.py` — sha256 65ca53ca3c9a3cbca94eccc5479abadd7e82ba5d713e4a7d574c693615c1cf24 — **runtime import of production_pipeline**
  - `test_merchant_to_channels.py` — sha256 0edca343259fe17f2c454fd659e7e195263c98d00a19f65243fc0cd6072ccd42
  - `test_production_pipeline.py` — sha256 ac60b45e07874e7d8d14363cd65a7e63b26e10efa8d82cbc2e6aca3712a6dcf8
  - `test_channel_exports.py` — sha256 e26dde108add9753f0acdbbd8c0124bfbd25b6f2453a789b3b105091543e4e62
  - `test_channel_exports_v2.py` — sha256 ed814d274551f3b6373e3217ab26fa296dca8fa9eded8216a164195ff28434ee
  - `test_bstn_integration.py` — sha256 05150b9f1b6caf590854f90938ad875d8705579556b5a7c1b0bff26d30ad62a7
- Stale-copy warning: `research/online/` (top level) holds **older** copies of merchant_to_channels.py (2,208 B) and bstn_integration.py (2,054 B) than `research/online/local-pkg/` (3,502 B / 2,593 B). Patch against local-pkg.

## 8. Discrepancies and open items (nothing invented)

- observed_utc records parse time, not capture time (HTML saved 2026-11-11; runs on 2026-11-12/13 restamp it). Stale-observation handling belongs to the patched converter.
- Stock evidence is asymmetric: BSTN claims exist per size; Shopify availability is never extracted (38 rows UNKNOWN).
- Size and colorway are not separate fields for Shopify rows (colorway embedded in the size label).
- Woo parent names double the brand when the product name already contains it (Patta ×2).
- The profit formula's structure (single import_tax lump; no FX fee; no fixed channel fee) is documented in §2; independently calculated synthetic cases are part of the patched-converter acceptance, not this audit.
- This report does **not** claim the converter is complete. Stage-② acceptance awaits ChatGPT's patch and the acceptance tests listed in the batch doc.

## 9. Artifact paths (iMac)

- Stage-② run dir: `/Users/discodadz/nexus-run/pkg_stage2_20261113` — outputs `input_pages_multi/manifest_six_brand_s2.csv`, `nexus_six_brand_s2.sqlite`, `export_six_brand_s2/`; logs `s2_stage1.log`, `s2_stage2.log`, `audit2.log` (DB schema/coverage dump).
- Stage-① run dir: `/Users/discodadz/nexus-run/pkg_six_20261113`. Original package preserved: `/Users/discodadz/nexus-run/pkg`.
- Actual imports performed: 0. Actual publications: 0.
