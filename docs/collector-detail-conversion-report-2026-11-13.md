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

## 10. Stage-2 sidecar first patch — execution results (2026-11-13, Muse)

Runbook: docs/collector-stage2-sidecar-runbook-2026-11-13.md. Patch commits 416b01d5 (stage2_review.py) and 31ce0a82 (test_stage2_review.py), copied into `/Users/discodadz/nexus-run/pkg_stage2_20261113` — sha256 stage2_review.py `79d409478adabc1d3ca34712fa700c5a1eb84687d4fbbe95f089813bd6807dbe`, test_stage2_review.py `6a579de93e737479f8cc854c2655ee9c95081727b2f0604b4c10495adb2d9784` (identical to the repo snapshot). The baseline pipeline was not replaced or modified.

Exact commands (package root):
```
python3 -m py_compile stage2_review.py test_stage2_review.py
python3 -m unittest -v test_stage2_review
python3 stage2_review.py --csv export_six_brand_s2/extracted_evidence.csv --manifest input_pages_multi/manifest_six_brand_s2.csv --db stage2_history_new.sqlite --out stage2_review_new
```
Results:
- py_compile OK.
- unittest **3/3 OK**, exit 0: test_identity (variant ID separates color and host; canonical_product_id stays ''; brand is not doubled in display_name), test_history (replay with a different parse timestamp does **not** create a second observation; a changed price under a new capture hash does), test_cost (explicit cost model: synthetic case cost_jpy **21850.00**, profit_jpy **5110.00** — independently recomputed and matching; missing duty or zero FX rate leaves cost/profit **blank**, never zero).
- Sidecar run, exit 0: `{"rows": 52, "observations": 52, "replay_observations": 52, "variant_ids": 52, "capture_time": "UNKNOWN", "published": 0, "approved_for_import": false, "status": "REVIEW_ONLY"}`. All runbook expectations met: 52 input rows → 52 observations; the built-in replay pass added **zero** new observations (replay dedup works on real data); **52 distinct provisional variant IDs**; every row decision HOLD (normalize() sets decision='HOLD'); no import, no publication.
- Coverage in the sidecar report matches §3 exactly (manufacturer_sku 0, color 0, availability_claim 14, all enrichment/cost fields 0).
- **Source URL/hash mapping**: the sidecar keyed observations by the sha256 of each manifest file. The merged manifest's URL→file→sha256 mapping equals the stage-① acceptance baseline for all 6 pages (bstn_01 cd089d68…, notre_01 649f1195…, notre_02 c0eada52…, patta_01 94a55789…, patta_02 dd366268…, bstn_02 53484dee…), as reproduced in §1.
- **Capture time stays UNKNOWN by design**: the sidecar deliberately excludes `observed_utc` (parse time) from the observation payload/key instead of treating it as capture evidence. This confirms the §3/§8 provenance finding rather than solving it — real capture timestamps still need a capture-side record.
- The new source_product_id / source_variant_id are **provisional sidecar IDs**, not replacements for existing export IDs (NX-HOLD-* parents, merchant product_id values). canonical_product_id is '' for all 52 rows; no cross-merchant merge was performed.
- This is **not** full stage-② acceptance. Remaining (per runbook): structured field extraction with per-field provenance, Shopify option mapping and price-unit evidence, verified stock, explicit accessory classification and simple-product export, canonical identity verification, cost evidence integration, channel conversion, full acceptance tests. The snippets in §11 are the input for the next patch.

## 11. Sanitized structure snippets from the saved pages (for the next patch)

Minimal excerpts only: field names, types, representative values (long strings truncated). No full HTML, no private data. Extracted offline from the same six saved files by a structure dumper (field inventory below; full snippet JSON is reproducible from the saved pages).

### 11.1 BSTN JSON-LD (collector.py path)
Product node keys (both pages): `@context` string, `@type` string, `name` string, `sku` string, **`mpn` string**, `category` object, `brand` object {`@type`: "Brand", `name`: string}, `image` string (URL), `description` string, `offers` array.
- The current parser reads none of: `mpn`, `category`, `image`, `description`. The JSON-LD path could therefore supply image_urls and description for BSTN pages, and `mpn` is a manufacturer-code **candidate** (unverified — it must not be promoted without the verification rule).
- Offer keys: `@type`, **`sku` (per-offer, size-suffixed)**, `gtin13`/`gtin12`, `price` (**JSON number**, e.g. 27.99), `priceCurrency` string, `availability` string (schema.org URL), `itemCondition`, `size` string, `url` string.
- Adilette: 13 offers; offer skus are "0009238-4" style (product sku + size suffix) — the current parser stages the **product-level** sku (0009238) for every size and ignores the offer-level sku and GTINs.
- Jason Markk: exactly **1 offer** — sku "0012650-1", gtin12 "810887023159", price 18.99, availability OutOfStock, size **"ONE SIZE"** in the offer itself. Confirms §6: a single-offer accessory whose only size value is the placeholder label.

### 11.2 Shopify pages (shopify_variants.py path) — Notre and Patta have the same shape
The variants-bearing parent object is a Storefront-style object. Parent keys: `id` string, `handle` string, `isCollective` null, `title` string, `type` string, `untranslatedTitle` string, `url` string, `vendor` string, `remoteShopId` null, `variants` array. **There is no `options` array in this object** — option mapping cannot come from here.
Variant keys (identical on Notre and Patta): `id` string, `image` object {`src`: string}, `price` object {`amount`: **JSON number**, `currencyCode`: string}, `sku` string, `title` string, `untranslatedTitle` string.
- **No `available` field exists in these variant objects** — stock is not merely unread, it is absent from this data source. Verified stock needs a different source on the page (or stays UNKNOWN).
- Price evidence: `price.amount` is a decimal major-unit number in this object (Jordan 225.0 USD, ASICS 180.0 USD, Patta 498.0 EUR) with an explicit `currencyCode` beside it — consistent with the §3 values; the parser's PRICE_UNIT_UNVERIFIED flag can be revisited against this shape.
- Variant `image.src` is present per variant (color-specific imagery exists in the source; the parser does not extract it).
- Notre variant titles combine size and colorway: "6 M / Lemonade/Lemonade", "8 M / Dark Gull Grey/Black". The colorway also appears in the parent title suffix: "J Balvin Air Jordan 4 Retro Sneaker in Lemonade/Lemonade", "Novalis Gel-Teremoa II Sneaker in Dark Gull Grey/Black" — a possible colorway source for Notre (parent title after " in "), to be verified per page.
- Patta variant titles are pure sizes ("XS", "S", …); the colorway appears only in the parent title suffix: "Patta Leather Hooded Bomber Jacket (Moonless Night)", "Patta Square Quilted Puffer Jacket (Black)".
- Vendor values: "Jordan" (Notre), "ASICS" (Notre), "Patta" (Patta) — matching the staged brands.

## 12. Stage-2 detail patch 2 — execution results (2026-11-13, Muse)

Batch: `docs/collector-stage2-detail-runbook-2026-11-13.md` (commit 5dca9de9). Code `stage2_detail.py` (5db087e1), tests `test_stage2_detail.py`. Executed in the same isolated copy `pkg_stage2_20261113`; existing `shopify_variants.py` and the baseline were not modified.

Exact commands and results:

```
python3 -m py_compile stage2_detail.py test_stage2_detail.py   -> OK
python3 -m unittest -v test_stage2_detail                       -> 6/6 OK (test_ambiguous, test_bstn, test_mismatch, test_notre, test_patta, test_provenance), exit 0
python3 stage2_detail.py --manifest input_pages_multi/manifest_six_brand_s2.csv --out stage2_detail_review.json
                                                                -> exit 0, counts [13, 0, 0, 0, 0, 1], total 14, published 0; output 57,404 bytes
```

Per-page reconciliation against the baseline (13, 16, 10, 6, 6, 1 = 52):

- BSTN Adilette: 13 rows = baseline 13. Variant IDs use the same per-size suffix scheme (0009238-4, -15, -5, ...).
- Notre J Balvin: 0 rows (baseline 16). Notre Novalis: 0 rows (baseline 10). Patta bomber: 0 rows (baseline 6). Patta puffer: 0 rows (baseline 6). Cause below.
- BSTN Jason Markk: 1 row = baseline 1.

Field coverage over the 14 produced rows (all BSTN): category 14/14, currency 14/14, description 14/14, image 14/14, manufacturer_code_candidate 14/14, price 14/14, size 14/14, stock_claim 14/14 (values verbatim schema.org URLs: InStock 4, OutOfStock 10), gtin 13/14 (the Adilette 45 EU offer has no gtin13/gtin12), color 0/14 (BSTN JSON-LD carries no Product.color; the field stays UNKNOWN and no color was invented).

Hypotheses vs actual: image 52 -> 14 (BSTN only, because the Shopify pages produced no rows); BSTN mpn 14 -> 14 (met); BSTN description 14 -> 14 (met); Shopify color candidate 38 -> 0; Shopify stock UNKNOWN 38 -> 0 rows produced.

Identity and integrity checks: (source_product_id, source_variant_id) unique 14/14; decision HOLD on every row; canonical_product_id empty on every row (GTIN is recorded as a raw field only — no GTIN promotion); image_rights UNKNOWN on every row; no product other than each page's own appears.

Shopify zero rows — candidate structure (read-only analysis reapplying the module's own candidate rule): each Shopify page contains several distinct JSON serializations of the SAME product, so the candidate count is not 1 and extraction fails closed by design:

- notre_01: 2 candidates, both id 15601990500463 (vendor Jordan, 16 variants); one carries the title, one has no title.
- notre_02: 2 candidates, both id 14990230519919 (vendor ASICS, 10 variants); same pattern.
- patta_01: 3 candidates, all id 15499861524811 (vendor Patta, 6 variants); two carry the title (the two titled dumps still differ elsewhere in the JSON), one has no title.
- patta_02: 3 candidates, all id 15499859231051 (vendor Patta, 6 variants); same pattern.

No genuinely different product was among the candidates on any page. The fail-closed stop was not bypassed, per the runbook.

Hash provenance discrepancy (anticipated by the runbook): the module's html_sha256 is the sha256 of the UTF-8 decoded text (Path.read_text), not of the raw file bytes. BSTN files contain no CRLF, and there raw == text == recorded. The four Shopify files all differ between raw bytes and decoded text (CRLF counts: notre_01 1, notre_02 1, patta_01 562, patta_02 562; no BOM anywhere). No Shopify rows were produced in this run, so no mismatched hash was recorded; but any future Shopify record's html_sha256 would not equal the source file's raw-bytes sha256. Reported as a discrepancy, not a match.

Jason Markk row: source_product_id 0012650, variant 0012650-1, manufacturer_code_candidate "JM3691 / 1201- OLD" (verbatim), size "ONE SIZE", 18.99 EUR, OutOfStock, gtin 810887023159 recorded as a raw field only.

Acceptance position: the synthetic tests pass 6/6 and the BSTN extraction meets every hypothesis. The Shopify extraction produced 0 of 38 baseline rows because candidate disambiguation fails closed on duplicate serializations of a single product. Patch 2 is therefore not fully accepted; the candidate selection rule is the remaining fix (ChatGPT's side, per the division of labor). This remains prototype acceptance only — stage 2 is not complete.

Artifacts (iMac): `/Users/discodadz/nexus-run/pkg_stage2_20261113/stage2_detail_review.json`; logs `/Users/discodadz/nexus-run/stage2-detail-run-2026-11-13.log` and `/Users/discodadz/nexus-run/stage2-detail-analysis-2026-11-13.log`; the read-only analysis script `analyze_stage2_detail.py` is kept beside the package.

## 13. Stage-2 detail retest (candidate merge + raw-byte hash) — execution results (2026-11-13, Muse)

Batch: `docs/collector-stage2-detail-retest-2026-11-13.md` (commit ecaa2a7c), approved by the owner (the approval was relayed to ChatGPT in the working thread). Code `stage2_detail.py` (8006f06d), tests `test_stage2_detail.py` (f7279c94). Same isolated copy `pkg_stage2_20261113`; prior outputs and the baseline were preserved.

Exact commands and results:

```
python3 -m py_compile stage2_detail.py test_stage2_detail.py   -> OK
python3 -m unittest -v test_stage2_detail                       -> 13/13 OK, exit 0
python3 stage2_detail.py --manifest input_pages_multi/manifest_six_brand_s2.csv --out stage2_detail_retest.json
                                                                -> exit 0, counts [13, 0, 0, 0, 0, 1], total 14, published 0
```

The expected counts [13, 16, 10, 6, 6, 1] were NOT met: the Shopify pages still produce zero rows.

What the fix achieved:

- Raw-byte hashing is in effect. Every field hash in the retest output equals sha256 of the original file bytes, verified independently for all 6 manifest files; the section-12 discrepancy is closed for produced rows.
- No value conflicts exist on the real pages. Replaying the merge inputs shows vendor/title/type/handle single-valued on all 4 Shopify pages, and no sku/title/price/image value ever conflicts across serializations.

Why the merge still returns zero rows (exact replay of merge_candidates with instrumentation):

- Each Shopify page carries two serialization families of the same product. Family A (the variants-JSON form) has the variant price as a dict {amount, currencyCode} and the image as a dict {src}. Family B (the standard product-JSON form) has the variant price as an int in cents and the image as null.
- merge_candidates raises ValueError('invalid price') when a variant's price is present but not a dict, so the whole page fails closed. First failure points: notre_01 candidate 1, variant 67756848971887, price int 22500; notre_02 candidate 1, variant 53031454081135, price int 18000; patta_01 candidate 1, variant 56417358577995, price int 49800; patta_02 candidate 1, variant 56417329971531, price int 27800.
- The two forms are value-consistent: for all 38 Shopify variants, the int price equals dict amount x 100 exactly (Notre USD, Patta EUR). No variant disagrees on price. The blocker is representation shape only, not a data conflict.
- Candidate structure is unchanged from section 12 (2/2/3/3 candidates, all sharing the page's single product id; variant sets 16/10/6/6; no missing variant ids). Family B's image is null — absence, not a conflicting URL.

Retest verification of the produced rows: total 14 (BSTN only, same scope as section 12); duplicate (url, product, variant) triples 0; decision HOLD on all rows; canonical_product_id blank on all rows; image_rights UNKNOWN; BSTN coverage unchanged (category/currency/description/image/manufacturer_code_candidate/price/size/stock_claim 14/14, gtin 13/14, color 0/14).

Verdict: the retest is NOT accepted against the stated criteria (52 rows). The hash half of the fix is verified good. The merge half fails on the cents-int price representation of the standard product-JSON serialization — a projected-field shape the merger does not currently accept. The remaining fix is ChatGPT's: decide how the merger treats the cents-int form (for example, ignore a non-dict price as a non-projected representation, or normalize cents to major units before comparison), keeping fail-closed behavior for genuine value conflicts. Not bypassed on this side.

Artifacts (iMac): `/Users/discodadz/nexus-run/pkg_stage2_20261113/stage2_detail_retest.json`; logs `/Users/discodadz/nexus-run/stage2-retest-run-2026-11-13.log`, `stage2-retest-analysis-2026-11-13.log`, `stage2-conflict-analysis-2026-11-13.log`, `stage2-mergefail-analysis-2026-11-13.log`, `stage2-priceform-analysis-2026-11-13.log`; read-only analysis scripts `analyze_stage2_retest.py`, `analyze_stage2_conflicts.py`, `analyze_stage2_mergefail.py`, `analyze_stage2_priceforms.py` beside the package.

## 14. Stage-2 price representation retest — execution results (2026-11-13, Muse)

Batch: `docs/collector-stage2-price-retest-2026-11-13.md` (commit c9599572), approved by the owner (the approval was relayed to ChatGPT in the working thread). Code `stage2_detail.py` (73b917cd), tests `test_stage2_detail.py` (14ea3b2b). Same isolated copy `pkg_stage2_20261113`; all prior outputs preserved. ChatGPT did not independently execute the tests; the verdict below is from this execution.

Exact commands and results:

```
python3 -m py_compile stage2_detail.py test_stage2_detail.py   -> OK
python3 -m unittest -v test_stage2_detail                       -> 21/21 OK, exit 0
python3 stage2_detail.py --manifest input_pages_multi/manifest_six_brand_s2.csv --out stage2_detail_price_retest.json
                                                                -> exit 0, counts [13, 16, 10, 6, 6, 1], total 52, published 0
```

The 21 tests include the 8 new price-representation tests: minor/major match, reversed JSON order, minor conflict stop, currency conflict stop, minor without currency stop, unsupported minor currency stop, invalid prices stop, Decimal exactness.

Criteria check: tests 21/21 met; BSTN 14 / Notre 26 / Patta 12 / total 52 met; duplicates 0; wrong merges 0; hash mismatches 0.

Independent verification:

- Every field hash in all 52 rows equals sha256 of the original file bytes (all 6 manifest files, 0 mismatched fields).
- Duplicate (url, product, variant) triples: 0. Produced variant sets equal the candidate variant sets on all 4 Shopify pages (16/10/6/6); exactly one product id per page; no cross-product or cross-store merge.
- All 38 Shopify rows match the dict-form (Money) serialization exactly on price (compared as Decimal), currency, raw title and merchant SKU; every produced price also reconciles with the cents-int form (price x 100 == int) for all 38 variants.
- decision HOLD on all 52 rows; canonical_product_id blank on all rows; image_rights UNKNOWN; Shopify stock_claim UNKNOWN on all 38 rows (BSTN stock_claim remains the JSON-LD claim, 14 OBSERVED).
- Coverage: category 52/52, currency 52/52, image 52/52, price 52/52, size 52/52; Shopify color_candidate 38/38, merchant_sku 38/38, raw_title 38/38; BSTN description 14/14, manufacturer_code_candidate 14/14, gtin 13/14 (one Adilette size carries no GTIN in the source; recorded as-is, not invented), BSTN color 0/14 (absent from the source JSON-LD).
- Method note: an intermediate comparison pass reported apparent field differences because it read expectations from the cents-form serialization, where price is an int and amount/currency are absent in that shape. Comparing against the Money-form serialization and reconciling the cents form with Decimal gives 0 differences; the produced data was never at fault.

Verdict: the price retest is ACCEPTED against the stated criteria. The stage-2 detail patch series (sections 10–14) is closed: all 52 detail rows now extract with original-byte provenance, and the fail-closed conflict gates remain intact. This is still an extraction-stage result — the remaining stage-2 integration work (stable canonical IDs and history, single-item accessory output, cost/rights/stock verification, channel conversion, regression tests) is ChatGPT's next batch definition, and full stage 2 acceptance is outstanding.

Artifacts (iMac): `/Users/discodadz/nexus-run/pkg_stage2_20261113/stage2_detail_price_retest.json` (192,649 bytes); logs `/Users/discodadz/nexus-run/stage2-price-retest-run-2026-11-13.log`, `stage2-price-retest-analysis-2026-11-13.log`, `stage2-fielddiff-analysis-2026-11-13.log`, `stage2-familya-analysis-2026-11-13.log`; read-only analysis scripts `analyze_stage2_fielddiff.py`, `analyze_stage2_familyA.py` beside the package.

## 15. Stage-2 integration batch — execution results (2026-11-13, Muse)

Batch: `docs/collector-stage2-integration-runbook-2026-11-13.md` (commit da2f3b81; code 289507f1, tests 7be5f47d), approved by the owner. Executed in the same isolated copy `pkg_stage2_20261113` with the accepted `stage2_detail.py` (73b917cd) and `stage2_review.py`; all prior outputs preserved. The baseline export (`export_six_brand_s2/`) and all baseline test modules were already present in the copy; nothing had to be copied in. ChatGPT did not independently execute the tests; the verdict below is from this execution.

Exact commands and results:

```
python3 -m py_compile stage2_integrate.py test_stage2_integrate.py   -> OK
python3 -m unittest -v test_shopify_variants test_verify_six_pages test_merchant_to_channels test_channel_ready_v4 test_production_pipeline test_grouping_e2e test_stage2_review test_stage2_detail test_stage2_integrate
                                                                     -> 50/50 OK, exit 0
python3 stage2_integrate.py --manifest input_pages_multi/manifest_six_brand_s2.csv --baseline export_six_brand_s2/extracted_evidence.csv --detail stage2_detail_price_retest.json --db stage2_integrated_new.sqlite --out stage2_integrated_new
                                                                     -> exit 0
{"rows": 52, "observations": 52, "replay": 52, "products": 6, "woo_rows": 57, "variable": 5, "variations": 51, "simple": 1, "buyma_rows": 6, "profit_rows": 52, "published": 0, "approved_for_import": false, "status": "REVIEW_ONLY"}
```

Criteria check: tests 50/50 (17 baseline + 3 sidecar + 21 detail + 9 integration); integrated rows 52; history 52; replay duplicates 0; product groups 6; WooCommerce 5 variable parents + 51 variations + 1 simple = 57; BUYMA 6 products; profit rows 52; publication/import 0. All met.

Independent verification:

- `integrated_evidence.json`: 52 rows; decision HOLD on all; canonical_product_id blank on all; observed price/currency retained per row as evidence, and every row's price/currency matches the accepted detail output (section 14) — 0 unmatched. Stock claims carried through unchanged: BSTN InStock 4 / OutOfStock 10 as schema.org claims, Shopify 38 blank (UNKNOWN). No verified availability inferred anywhere.
- SQLite `stage2_integrated_new.sqlite`: the observations table holds the 52 history rows.
- `id_mapping.json`: 52 legacy-to-new-SKU mappings.
- `woocommerce_review.csv`: 57 rows; SKUs unique 57/57 with no blanks; every variation's Parent resolves to a produced parent; Regular price and Images blank on all rows; Published 0 and Visibility hidden on all rows. The single simple product is the Jason Markk kit, with no size attribute and stock 0. Variation sizes are in natural ascending order (numeric EU/US sizes ascending; apparel in XS, S, M, L, XL order).
- `buyma_review.csv`: 6 product rows. `profit_review.csv`: 52 rows with cost_jpy blank on all rows — no verified cost inputs exist, so no cost or profit was invented; only the observed source price is carried.
- No live fetch, no production DB / WordPress / main changes, no import.

Verdict: the integration batch is ACCEPTED. Stage 2 offline integration is complete. Per the runbook, the remaining gates before any sale readiness are verified canonical identity, cost/rights/stock verification, category mapping, size guides and platform import validation; Stage 3 starts only after review of these results.

Artifacts (iMac): `/Users/discodadz/nexus-run/pkg_stage2_20261113/stage2_integrated_new.sqlite` (229,376 bytes) and `stage2_integrated_new/` (integrated_evidence.json, id_mapping.json, woocommerce_review.csv, buyma_review.csv, profit_review.csv, report.json); logs `/Users/discodadz/nexus-run/stage2-integrate-run-2026-11-13.log`, `stage2-integrate-analysis-2026-11-13.log`, `stage2-integrate2-analysis-2026-11-13.log`; read-only analysis scripts `analyze_stage2_integrate.py`, `analyze_stage2_integrate2.py` beside the package.

## 16. Stage-3 verification gate batch — execution results (2026-11-13, Muse)

Batch: `docs/collector-stage3-verification-runbook-2026-11-13.md` (commit 74046edc; code `stage3_verify.py` 3262cffb, tests `test_stage3_verify.py` e45c8d39), approved by the owner (the approval was relayed to ChatGPT in the working thread before the batch was registered). Executed in the same isolated copy `pkg_stage2_20261113` against the accepted stage-2 integrated outputs; all prior outputs preserved. ChatGPT did not independently execute the tests; the verdict below is from this execution.

This batch is an offline evidence gate, not catalog collection and not a platform import: with no evidence inputs supplied, every row must stay unverified and on HOLD, and the contradiction gates (identity conflicts, stale stock) must stop the batch rather than guess.

Exact commands and results:

```
python3 -m py_compile stage3_verify.py test_stage3_verify.py   -> OK
python3 -m unittest (all modules incl. test_stage3_verify)     -> 58/58 OK, exit 0
python3 stage3_verify.py (no evidence inputs)                  -> exit 0
{"woo_rows": 57, "buyma_rows": 6, "structural_validation": "PASS", "actual_import": "NOT_RUN", "rows": 52, "hold": 52, "review_complete": 0, "canonical_verified": 0, "published": 0, "approved_for_import": false}
```

Criteria check: tests 58/58 (50 prior + 8 new Stage-3 cases: cost, empty, exports, identity, rights, stale, stock, unknown); structural validation of the Woo 57-row and BUYMA 6-product exports PASS; actual import NOT_RUN; all 52 rows HOLD with 0 review-complete and 0 canonical-verified; published 0; approved_for_import false. All match the runbook's expected values.

Independent verification (read-only analysis script `analyze_stage3_verify.py`):

- `report.json` matches the main run output field for field.
- `verification.json` is a list of exactly 52 rows, each with the keys canonical_product_id, cost_jpy, decision, image_rights, missing, profit_jpy, review_complete, source_variant_id, stock.
- On all 52 rows: canonical_product_id blank, stock UNKNOWN, image_rights UNKNOWN, cost_jpy and profit_jpy blank, decision HOLD, review_complete false.
- The `missing` list on every row names all six gates — identity, purchasable_stock, image_rights, cost, WooCommerce_validation, BUYMA_validation — so no gate was silently treated as satisfied.
- No live fetch, no production DB / WordPress / main changes, no import, nothing published.

Verdict: the verification-gate batch is ACCEPTED as an offline gate: the verifier fails closed on absent evidence and invents nothing. This does not complete Stage 3. Still outstanding per the runbook: catalog discovery, authorized collection, incremental update and resume, live evidence verification (manufacturer identity, purchasable stock within 24h, full cost inputs, image rights), and platform testing in an isolated WooCommerce staging import plus the official BUYMA procedure.

Artifacts (iMac): `/Users/discodadz/nexus-run/pkg_stage2_20261113/stage3_verification_empty/` (report.json 233 bytes, verification.json 23,194 bytes); logs `/Users/discodadz/nexus-run/stage3-verify-run-2026-11-13.log`, `stage3-verify-analysis-2026-11-13.log`; read-only analysis script `analyze_stage3_verify.py` beside the package.

## 17. Stage 3 catalog batch — execution results (2026-11-13, Muse)

Batch: runbook `docs/collector-stage3-catalog-runbook-2026-11-13.md` (f2016b66); code `stage3_catalog.py` (824af372), tests `test_stage3_catalog.py` (5a8d9246), store template `stage3_stores.json` (ca4fd4f5). Owner approved registration of this batch; execution followed the runbook order. Executed in the isolated copy `pkg_stage2_20261113` on the iMac; prior outputs preserved. ChatGPT has not independently run these tests.

Steps 1–2 (offline) — PASS. py_compile OK. Full regression: unittest 65/65 OK (prior 58 + 7 new catalog tests). Offline re-validation of the six saved pages through `stage3_catalog.extract`: counts 13/16/10/6/6/1 = 52; variant IDs, prices and currencies identical to the §14 accepted output on every row; every field hash equals sha256 of the original page bytes; brand and name observed on all 52 rows; all rows HOLD. Log: `stage3cat-step1-2026-11-13.log`; analysis script `analyze_stage3cat_offline.py`.

Step 3 (store permission and scope review) — completed, network read only, reviewer Muse, 2026-11-13. Local records on the iMac under `/Users/discodadz/nexus-run/stage3-review-2026-11-13/` (`review-record.md`, `summary.json`, `probe2.json`, `robots-*.txt`, `terms-*.html`, `sitemap-sample-*.xml`, per-store local configs, all `enabled=false`).

- BSTN (www.bstn.com): robots.txt (200) disallows only /api/, /checkout/, /customer/, /catalogsearch/, /raffle/ and similar; product pages are not disallowed and no crawl-delay is set. Terms (AGB, https://www.bstn.com/eu_en/terms-and-conditions) were re-read today; a keyword scan for scrap/spider/crawl/robot/automated found no prohibition of product-page reading or extraction, consistent with the 2026-11-12 review (the bot prohibition covers In-App Chases purchase/raffle automation). Permission basis is documented. However the official sitemaps are served from media.bstn.com (robots-listed, 17 locales; the eu_en index has 41 children, all on media.bstn.com), https://www.bstn.com/sitemap.xml returns 404, and `stage3_catalog.scope()` requires sitemap seeds and child sitemaps on the storefront host. Separately, one child sitemap (sitemap-1-1.xml) has Content-Length 10,487,622 bytes, above the collector's 10,000,000-byte read cap. BSTN therefore cannot be collected with the code as registered and was NOT enabled. Required fix (ChatGPT): allow the robots-listed media host for sitemap fetches while keeping product URLs scoped to www.bstn.com, and handle sitemap files larger than 10 MB.
- Notre (www.notre-shop.com): robots allows /products/; the sitemap index is on-host with 3 product sitemaps (784 URLs in the first, 783 product URLs). Terms of Service (https://www.notre-shop.com/policies/terms-of-service) list "(i) to spam, phish, pharm, pretext, spider, crawl, or scrape" among prohibited uses — a terms restriction on automated collection, so the store was stopped per the runbook and NOT enabled. Additional incompatibility: child sitemap URLs require ?from/to query parameters (bare URLs return HTTP 400) and scope() rejects query strings.
- Patta (patta.nl): robots allows /products/; 1 product sitemap (680 URLs, 679 product URLs). Terms of Service (https://patta.nl/policies/terms-of-service) contain the same prohibited-use clause (spider, crawl, or scrape), so the store was stopped per the runbook and NOT enabled.
- Foot Locker and Zalando remain excluded (terms prohibition / permission unverifiable, 2026-11-12).

Step 4 (live collection) — NOT RUN. No store could be enabled: BSTN is blocked by the code constraints above; Notre and Patta are stopped on terms. The collector performed no live product fetch.

Steps 5–6 (incremental update, interruption/resume) — live incremental run NOT RUN (no completed live run exists). Isolated fixture DB test (no network): interruption after 1 of 2 fixture pages leaves the queue DONE/PENDING with the run incomplete; resume completes without refetching DONE pages (2 observations, published 0); a second fixture run with one price change yields delta {new: 0, missing_candidates: 0, price_or_stock_changed: 1}; a corrupted page marks the queue ERROR and the resume guard refuses to continue. FIXTURE_PASS (log `stage3cat-fixture-2026-11-13.log`, script `fixture_stage3cat.py`). The 7 new unit tests also cover discover/scope/XML/permission/resume/stop/scope-change.

Step 7 (evidence and sales-prep validation) — NOT RUN for catalog output, because no completed catalog run exists. All data remains HOLD; nothing was imported or published.

Verdict: steps 1–2 PASS; step 3 completed with BSTN permission documented but code-blocked and Notre/Patta stopped on terms; steps 4 and 7 not run; fixture-level resume/delta/error behavior PASS. Stage 3 catalog collection remains incomplete pending (a) a ChatGPT code fix for the BSTN sitemap host scope and large-sitemap handling, and (b) an owner decision on Notre/Patta (written permission or continued exclusion). No production / WordPress / main changes; no platform import; no external submission.

Artifacts (iMac): logs `stage3cat-step1-2026-11-13.log`, `stage3cat-review-2026-11-13.log`, `stage3cat-probe2-2026-11-13.log`, `stage3cat-fixture-2026-11-13.log` in `/Users/discodadz/nexus-run/`; review records in `/Users/discodadz/nexus-run/stage3-review-2026-11-13/`; scripts `analyze_stage3cat_offline.py`, `review_stage3_stores.py`, `review_stage3_probe2.py`, `fixture_stage3cat.py` beside the package.

## 18. BSTN retest after §17 — execution results (2026-11-13, Muse)

Batch: runbook `docs/collector-stage3-bstn-retest-2026-11-13.md` (a97157df); fix code `stage3_catalog.py` (3a528495, robots-listed BSTN media XML only + bounded large-sitemap parsing), new tests `test_stage3_bstn.py` (30331a22). The owner approved registration of this patch on 2026-11-13 12:53 JST and Muse relayed the approval to ChatGPT. Executed in a new isolated copy `pkg_bstn_20261113` on the iMac; the §17 package `pkg_stage2_20261113` was left untouched. ChatGPT has not independently run these tests.

Step 1 (regression) — PASS. py_compile OK (`stage3_catalog.py`, `test_stage3_catalog.py`, `test_stage3_bstn.py`). Regression set: unittest 73/73 OK (the §17 set of 65 + 8 new BSTN tests). Offline re-validation of the six saved pages through the patched `stage3_catalog.extract`: counts 13/16/10/6/6/1 = 52, every check OK (OFFLINE_CHECK_PASS). Interruption/delta/error fixture re-run: FIXTURE_PASS. Log: `bstn-step1-2026-11-13.log`. Note: a full `unittest discover` over every module in the package runs 152 tests with 5 errors, identical in count and kind to the pre-patch package (144 tests, same 5 errors); the batch regression set is the 73 above.

Step 2 (permission refresh) — storefront confirmed, media host unavailable. Fresh fetches on 2026-11-13 with the review agent `AHC-CatalogReview/1.0` (no redirects, identity encoding); records in `/Users/discodadz/nexus-run/bstn-retest-2026-11-13/` (`probe.json`, both robots files, `terms-agb.html`); log `bstn-probe-robots.log`.

- `https://www.bstn.com/robots.txt`: HTTP 200, valid robots; 17 Sitemap lines; the EU English seed `https://media.bstn.com/sitemap/eu_en/sitemap.xml` is listed; no crawl-delay; product paths are not disallowed.
- Terms (AGB, `https://www.bstn.com/eu_en/terms-and-conditions`) re-fetched: HTTP 200; keyword scan scrap / crawl / spider / robot / automated = 0 hits (the 23 `bot` hits are substrings of unrelated words). No new prohibition; the §17 permission basis for product-page reading stands.
- `https://media.bstn.com/robots.txt`: **HTTP 403** (0 bytes), confirmed on two identical fetches. The media host's robots permission therefore cannot be verified.

Step 3 (first collection, `--limit 5`) — STOPPED BY DESIGN before discovery. Local config `bstn-local.json` was prepared in the isolated package (host www.bstn.com, enabled, permission reference to the §17 review and this runbook, reviewer Muse, reviewed_at 2026-11-13T04:29:54Z, interval_seconds 5, request_budget 5000, product regex `/eu_en/p/[^/]+`, seed as above). Exact command: `python3 stage3_catalog.py --config bstn-local.json --db stage3_bstn.sqlite --run bstn-first --out bstn-first-001 --limit 5`. The collector stopped inside `Fetch.init_robots` with `Stop: HTTP 403 https://media.bstn.com/robots.txt` (exit 1). No sitemap or product URL was fetched; the isolated DB holds no runs, queue entries, captures or observations (all counts 0). Log: `bstn-first-2026-11-13.log`. Per the runbook this is the deliberate outcome when media robots is unavailable: no bypass was attempted and no exception was taken. Notre / Patta / Foot Locker / Zalando were not enabled.

Steps 4–5 of the runbook (resume to completion, incremental run, exports, evidence verification, §18 counts for discovery/queue/delta) — NOT RUN, because no BSTN run exists. No full-catalog claim is made. All data remains HOLD; nothing was imported or published; no production / WordPress / main changes.

Verdict: the patch itself behaves exactly as specified — regression green, media-XML scope and robots gating enforced — but BSTN catalog collection remains stopped at the media host's robots gate. Open point for documented review (ChatGPT + owner): `media.bstn.com/robots.txt` returns HTTP 403 to the review agent. Until media-host permission is verifiable (robots retrievable and allowing, or written permission from BSTN), BSTN stays stopped; the next decision belongs to that review, not to an executor exception.

Artifacts (iMac): package `/Users/discodadz/nexus-run/pkg_bstn_20261113/` (patched code, `bstn-local.json`, schema-only `stage3_bstn.sqlite`); logs `bstn-step1-2026-11-13.log`, `bstn-probe-robots.log`, `bstn-first-2026-11-13.log` in `/Users/discodadz/nexus-run/`; probe records in `/Users/discodadz/nexus-run/bstn-retest-2026-11-13/`; scripts `probe_bstn_robots.py`, `run_bstn_*.sh` beside the package.

## 19. BSTN store-side category route — decision and investigation (2026-11-13, Muse)

Decision history: after §18, the owner first chose option A (treat the storefront robots' listing of the media sitemap as the permission basis and proceed with media XML only). Muse relayed this to ChatGPT. ChatGPT replied that a sitemap listing evidences location, not permission to override another host's restriction; the 403 is on media's robots.txt itself; it would not lift the stop condition, and proposed the store-side category-listing route as top priority (or asking BSTN directly). The owner then adopted the store-side category route (2026-11-13 14:46 JST). ChatGPT asked Muse to investigate: BSTN category structure, pagination, full-product reachability, and the details of the 5 pre-existing test errors. Results below; probes ran on the iMac, store host only, a handful of requests at 2s intervals. Artifacts: `/Users/discodadz/nexus-run/bstn-catprobe-2026-11-13/` (probe.json, probe2.json … probe5.json, saved HTML), scripts `probe_bstn_categories*.py` beside it.

Test errors (§18's "5 errors") — identified. All 5 are in the legacy `test_pipeline.py` (BUYMA pipeline), every one failing at the same line: `pipeline.py` line 37, `from bs4 import BeautifulSoup` → `ModuleNotFoundError: No module named 'bs4'`. The iMac's Python environment lacks beautifulsoup4; the errors are an environment dependency issue, unrelated to the collector code. Affected: `test_parse`, `test_idempotent`, `test_no_auto_link`, `test_url_reject` (PipelineTests), `test_evidence_kind_exported` (AdditionalSafetyTests). Full run: 152 tests, 147 passed, 5 errors as above. Log: `test-errors-2026-11-13.log`.

Category structure (www.bstn.com, EU English):
- `https://www.bstn.com/eu_en/` returns 308 → `https://www.bstn.com/eu_en` (200).
- Gender landings `/eu_en/men`, `/eu_en/women`, `/eu_en/kids` return 200 (~1.0–1.2 MB); their static HTML exposes only ~22–23 featured product anchors — they are landing pages, not full listings.
- Real listings live at `/eu_en/<gender>/all-products?categories=...` and subcategory paths (`/eu_en/<gender>/accessories/...`, `apparel?...`); filters are query params (`categories=Men~All Products~Footwear`, `brand=`, `groupextra=`).
- Listing state is server-rendered in `__NEXT_DATA__` (Next.js, page route `/[gender]/[level2]`) under `props.pageProps.serverState.initialResults.magento2_eu_products.results[]` — Algolia-style responses. Listing pages contain ZERO product anchors in static HTML; product discovery must read the embedded results, not hrefs.

Pagination — verified server-side. Each result carries `nbHits`, `nbPages`, `hitsPerPage=96`, `page` (0-based) and 96 embedded hits. Test on the men footwear subset (`categories=Men~All Products~Footwear`, casual/boots/loafers filter): nbHits 381, nbPages 4. No param and `?page=1` both return page index 0 (first hit `p/sebago-tala-mid-suede-76111sw-906-0353318`); `?page=2` returns page index 1 with disjoint hits (first `p/timberland-boat-shoe-tb0a2pdqani1-0359555`). So the URL page parameter is 1-based and fully server-rendered: iterating `page=1..nbPages` per listing URL reaches every hit. A broader men total seen in the landing JSON: 3,447 hits / 36 pages at 96 per page.

Product identity from hits: each hit carries `url` (e.g. `p/sebago-tala-mid-suede-76111sw-906-0353318` → product URL `https://www.bstn.com/eu_en/` + url), plus `sku`, `article_number`, `brand`, `categories.level0–3`, `gender`, `color`, `price.EUR.*`, and image references on `img.bstn.com` (a separate image host; noted for the design — discovery itself needs no image fetches). Product pages remain on the store host under the existing permission basis and the existing extractor already handles `/eu_en/p/...` pages.

Conclusion: full-catalog discovery is feasible using only the store host — enumerate listing URLs (gender × category, via the `categories=` parameter space), page through each with `?page=N`, and collect hit `url` values as the product queue. No media-host access is needed at any step. Design of the category-based discovery (listing enumeration, dedupe across overlapping filters, budgets) is ChatGPT's next step; Muse executed investigation only. Nothing was collected into any DB in this step; nothing imported or published.

Addendum to §19 (2026-11-13, later): the owner re-decided option A as the final call (staged rollout, watch and see) and Muse relayed it to ChatGPT as the owner's final decision. ChatGPT again declined to implement the stop release: it understands the 403 is on media's robots.txt, not on the sitemap XML itself, but will not unconditionally permit an unverifiable other-host access control on the basis of the storefront listing alone. Its evaluation: the 5 test errors are a bs4 dependency issue (install the dependency in the isolated environment and re-verify); the category route is a viable alternative; extraction/storage/delta code is reusable as-is; staged verification starting from 5 items is adopted. So the implementable path is the category route, whose design ChatGPT is positioned to prepare. Owner's next call pending.
Owner's note (2026-11-13): from the owner's own past scraping experience, hitting access restrictions after long scraping sessions amounted to temporary rate limits that cleared after a while, not permanent bans.
