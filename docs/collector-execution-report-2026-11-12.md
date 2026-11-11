# Collector execution report — 2026-11-12 (Muse, execution only)

Executed per `docs/collector-next-execution-2026-11-12.md` and
`docs/collector-handoff-2026-11-12.md` on branch `integration/grok-review`.
Environment: iMac, Python 3.9.6, package `merchant_to_channels.py` et al.
from `NEXUS_IMAC_BATCH_PIPELINE.zip` (no code edits, no installs).
Aggregates only — no product/customer/order data, no credentials.

## Step 2 — WooCommerce source-URL inventory (read-only)

- Product posts scanned: 461 (199 published).
- Products with a merchant source URL in meta/content: **0**.
- Host counts: none.

Per step 7 of the execution order, the pages below are **alternate sources**
taken from local sourcing records. They did **not** come from the
WooCommerce products.

## Step 3 — Host permission checks

- `www.bstn.com`: checked in the earlier verified run (robots/terms do not
  prohibit low-frequency product-page reads). Included.
- `www.notre-shop.com`: storefront robots.txt declares public product HTML
  crawlable; no automated-reading prohibition found in the store's terms.
  Included for retrieval attempt.
- `patta.nl`: storefront robots.txt declares public product HTML crawlable;
  terms prohibit content copying/distribution (IP) but contain no explicit
  automated-reading ban found. Included for retrieval attempt.
- Foot Locker / Zalando: skipped per prior findings (terms prohibit
  scraping / HTTP 403), no bypass attempted.

## Step 5 — Targeted unit tests

`test_merchant_to_channels`, `test_channel_ready_v4`,
`test_production_pipeline`: **6 tests, OK**.

## Run A — one manifest, all hosts (NEW DB `nexus_multi_20261112.db`, NEW out `export_multi`)

- Hosts attempted: 3. Pages in manifest: 5 (BSTN x1 reused verified save,
  Notre x2, Patta x2).
- Retrieval results:
  - BSTN page 1: previously saved HTML reused; parsed, 13 size rows.
  - Notre x2 and Patta x2: **not retrieved**. The package's own
    `live_fetch.py` raised `ValueError: HTTPS approved merchant hostname
    required` for both hosts — its allowlist contains only BSTN,
    Foot Locker and Zalando hosts. The pipeline then reported
    `FileNotFoundError` for those 4 manifest rows.
- Totals (BSTN only): parsed size rows 13; DB accepted 13 / rejected 0;
  products 1; WooCommerce rows 14 (1 parent + 13 variations);
  BUYMA rows 1; profit rows 13; published 0; **non-HOLD rows: 0**
  (status REVIEW_ONLY).

## Run B — supplementary BSTN second page (NEW DB `nexus_bstn2_20261112.db`, NEW out `export_bstn2`)

- BSTN sitemap read via Python on the iMac listed 2,972 product URLs;
  `live_fetch.py` saved page 2 (540,981 bytes).
- Both BSTN pages parsed: size rows 14 (13 + 1 single-size product);
  DB accepted 14 / rejected 0; products 2; WooCommerce rows 16
  (2 parents + 14 variations); BUYMA rows 2; profit rows 14;
  published 0; **non-HOLD rows: 0** (status REVIEW_ONLY).
- Note: in Run A a PHP-curl fetch of the same sitemap returned no URL
  (runner-side failure, cause unverified; the Python path in Run B
  succeeded). Not a merchant-side issue.

## Missing fields by host

- `www.bstn.com` (both products, per `channel_report_v4.json`):
  category, channel_specific_price, color, description,
  image_usage_permission, images, manufacturer_style_code,
  platform_import_validation, shipping_and_tax_confirmation,
  verified_size_stock.
  Extracted: brand, name, merchant SKU (not a manufacturer style code),
  size, price (EUR), availability **claim** only.
- `www.notre-shop.com`: all fields missing — blocked before retrieval by
  the package host allowlist (see errors).
- `patta.nl`: all fields missing — same allowlist block.

## Per-host errors

- BSTN: none in fetch/parse (Run B). Run A runner-side sitemap failure
  noted above.
- Notre: `ValueError: HTTPS approved merchant hostname required`
  (live_fetch.validate_url), 2 of 2 pages; pipeline FileNotFoundError x2.
- Patta: same error, 2 of 2 pages; pipeline FileNotFoundError x2.

## Executor's factual summary

Multi-merchant extraction is currently blocked at the package level:
both the fetcher (`live_fetch.py`) and the parser (`collector.py`)
restrict hosts to `www.bstn.com` / `footlocker.*` / `zalando.*`.
BSTN works end-to-end for 2 pages / 2 products with all rows HOLD.
No products were published or imported; no site, theme or product data
was changed; nothing outside this report was uploaded.
