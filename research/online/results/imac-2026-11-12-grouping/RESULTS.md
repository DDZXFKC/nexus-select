# Grouping verification — iMac execution report (2026-11-12)

Executor: 魔王ちゃん (Muse) on the user's iMac. Target: the grouping changes and
runbook `docs/collector-grouping-runbook.md` (commits up to 7a9c47df).
New files were staged on the iMac from commit 7a9c47df
(`shopify_variants.py`, `test_shopify_variants.py`). A fresh DB
(`pkg/nexus_grouping_new.sqlite`) and output dir (`pkg/export_grouping_new/`)
were used; the production-path DB was not touched. All rows remain HOLD /
REVIEW_ONLY, published=0.

## Verdict

| Check | Result |
|---|---|
| Step 1: copy new files with backups | PASS |
| Step 2: py_compile + full unittest suite | PASS — 14 tests, all OK |
| Step 3: five-page real run | exit 0, 51/51 rows accepted, 0 rejected |
| Goal: 5 pages group into 5 products | **NOT achieved — 39 products** |
| Notre product_name | Still missing (26/26 rows), root cause pinpointed (Step 5) |

## Step 1 — files copied

- `shopify_variants.py` → pkg, sha256 prefix `e95403bb548f874c`, 4375 bytes.
  Backup: `shopify_variants.py.bak-grouping-20261112`.
- `test_shopify_variants.py` → pkg, sha256 prefix `ef2175041f210c0e`, 2495 bytes.
  Backup: `test_shopify_variants.py.bak-grouping-20261112`.

## Step 2 — compile and tests

- `py_compile collector.py shopify_variants.py merchant_to_channels.py` → exit 0.
- `unittest -v` over the four modules → **Ran 14 tests in 0.053s, OK**.
  New identity tests pass: `test_page_identity_shared_across_sizes`,
  `test_page_identity_not_cross_merchant`. All previous tests still pass,
  including `test_notre_json`, `test_patta_aggregate_offer`,
  `test_multi_shop_grouping_and_conservative_profit`.

## Step 3 — five-page run (exit 0)

Pages parsed: BSTN adidas Adilette 13 sizes; Notre J Balvin AJ4 16;
Notre Novalis GEL-Teremoa II 10; Patta Leather Hooded Bomber 6;
Patta Square Quilted Puffer 6. Total size rows 51, DB accepted 51, rejected 0.

Output counts: **products 39**, WooCommerce rows 90, BUYMA rows 39,
profit rows 51, published 0, status REVIEW_ONLY.

Per-page grouping outcome (from channel_report_v4 review entries):

- BSTN: **1 product, size_count 13** — grouped correctly.
- Patta Leather Hooded Bomber: 6 products, size_count 1 each — split.
- Patta Square Quilted Puffer: 6 products, size_count 1 each — split.
- Notre J Balvin AJ4: 16 products, size_count 1 each — split, name missing.
- Notre Novalis: 10 products, size_count 1 each — split, name missing.

## Root cause (from the runbook's own downstream inspection)

The page-level identity added in `shopify_variants.py` never reaches the
downstream grouping:

- `merchant_to_channels.py` FIELDS has no `product_id`; rows are written with
  the extractor's `sku` as-is. `product_id` is not mentioned in the file.
- `production_pipeline.py` keys `merchant_evidence` and
  `product_enrichment` by `(source_url, merchant_sku, size)`.
  `product_id` is not mentioned in the file.
- `channel_ready_v4.py` groups by `(source_url, merchant_sku, color_claim)`
  (line 26: `groups[(r[0],r[1],r[5])]`). `product_id` is not mentioned.

For Shopify pages the `sku` is per-variant, so each size forms its own
(source_url, sku, color) group and sizes never merge. BSTN grouped only
because its SKU is product-level (same value across its 13 sizes).

One measurement caveat: `extracted_evidence.csv` has no `product_id` column
(columns: product_url, shop, brand, name, sku, manufacturer_sku, color, size,
price, currency, availability_claim, observed_utc, image_urls, description,
category, ship_from, shipping_cost, import_tax, partner_fee,
international_shipping, platform_fee_rate, fx_jpy, selling_price_jpy,
image_rights), so any per-host "distinct product_id" count over that CSV
collapses to per-host totals (13 / 26 / 12). The authoritative grouping
evidence is the channel report above.

Name presence in extracted evidence: BSTN 13/13 present, Patta 12/12 present,
Notre 0/26 (all missing).

## Step 5 — Notre parent title investigation

For both Notre pages the runner found, inside the page scripts, a single JSON
object that contains both `vendor` and `variants`, with keys:
`gid, handle, id, remote, type, variants, vendor` — and, one level in the same
object, a **non-empty `title` field is present**
(`same_object_title_or_name_field_present: "title"` on both pages).
`title_from_variants()` currently finds no single candidate
(`title_from_variants_single_candidate_present: false`).

Concrete fix path: in `shopify_variants.py`, read `title` from the same parent
object that supplies `vendor`/`variants` for Notre. The data is on the page;
no new source is needed.

## What is asked back (one batch, per the standing rule)

1. Carry the page identity through the pipeline: add the identity to
   `merchant_to_channels` output and key `production_pipeline` /
   `channel_ready_v4` grouping by it (keeping the never-merge-across-shops
   rule), so Shopify sizes merge into one product per page.
2. Notre: populate `name` from the parent object's `title` (same object as
   vendor/variants).
3. Send the next runbook in one batch; the executor will run it as-is and
   return results the same way.

## Artifacts (on the iMac, available on request)

- `/Users/discodadz/nexus-run/grouping_result.json` (36,513 bytes)
- `/Users/discodadz/nexus-run/grouping.log` (11,515 bytes)
- DB: `/Users/discodadz/nexus-run/pkg/nexus_grouping_new.sqlite`
- Out: `/Users/discodadz/nexus-run/pkg/export_grouping_new/`
  (woocommerce_review_v4.csv 90 rows, buyma_review_v4.csv 39 rows,
  profit_review.csv 51 rows)
