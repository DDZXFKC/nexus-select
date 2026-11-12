# RESULTS — 2026-11-12 iMac follow-up batch: title fix + product_id grouping

Runbook: docs/collector-grouping-followup-2026-11-12.md
Environment: isolated test copy on the iMac (/Users/discodadz/nexus-run/pkg).
No production import, no WooCommerce change, all gates HOLD, published = 0.

## Verdict: ALL ACCEPTANCE CONDITIONS PASS

- Five-page manifest (BSTN 1, Notre 2, Patta 2): 51/51 size rows parsed,
  DB stage accepted 51 / rejected 0.
- **Products after channel grouping: 5** (was 39). Exactly one review item
  per source URL; size counts BSTN 13, Notre 16 + 10, Patta 6 + 6.
- Exports: WooCommerce review 56 rows (5 parents + 51 variations),
  BUYMA review 5 rows, profit review 51 rows.
- **Notre product names present 26/26** (BSTN 13/13, Patta 12/12;
  name-missing set is empty) — the parent-title fix works end to end.
- Tests: py_compile clean; **16/16 unit tests OK** (the original 15,
  including the new parent-title tests, plus one new end-to-end grouping
  regression test added this batch).
- Published: 0. Status remains REVIEW_ONLY / HOLD everywhere.

## What was done

1. Located the real local files that were missing from GitHub —
   production_pipeline.py and channel_ready_v4.py exist only in the iMac
   test package (plus merchant_to_channels.py and bstn_integration.py).
   Sanitized post-fix copies of all edited files are saved next to this
   report under research/online/local-pkg/.
2. Title fix (commits 26440edc + 9accbb0b): new shopify_variants.py and
   test_shopify_variants.py copied into the test package with
   .bak-titlefix-20261112 backups of the originals.
3. product_id propagation (test copy only, .bak-groupfix-20261112 backups):
   - merchant_to_channels.FIELDS and production_pipeline.FIELDS gain
     'product_id' (it was already emitted by both extractors and silently
     dropped at the evidence-CSV step).
   - merchant_evidence schema (bstn_integration.CREATE) and
     product_enrichment schema (production_pipeline.EXT) gain
     product_id TEXT NOT NULL DEFAULT ''; stage() inserts and the
     profit_review select carry it through; row identity stays
     (source_url, merchant_sku, size).
   - channel_ready_v4: the export select appends product_id as the final
     column (positional indices 0-14 unchanged), and the grouping key is
     now (source_url, discriminator, color_claim).

## One deviation from the runbook's literal key — needs GPT's review

The runbook specified the key as (source URL, product_id with merchant_sku
fallback for legacy records, color). Evidence from the actual data shows
the two extractors give product_id DIFFERENT semantics:

- Shopify (Notre/Patta): product_id = hash of the page URL — one value per
  page (page identity). Distinct per URL in the DB: 1.
- BSTN (collector.py): product_id = sha256(brand|sku|color|size) — a
  VARIANT-level id, 13 distinct values for the single BSTN page.

Applying the literal key would have regressed BSTN from 1 product to 13.
Implemented rule (channel_ready_v4): the discriminator is product_id only
when exactly one non-empty product_id covers the whole page; otherwise
(variant-level ids, or legacy empty values) it falls back to merchant_sku.
This preserves the runbook's intent — page identity when it truly
identifies the page, never merging across merchants or colors — and
produces the required 5 products with no regression. Flagged here for
GPT to confirm or refine (e.g. by making the BSTN extractor emit a
page-level id instead).

## Test-file adjustment (also for GPT's review)

test_channel_ready_v4.py builds merchant_evidence with positional
13-value INSERTs; the wider schema (14 columns) required adding one
placeholder and one empty product_id value in two inserts. No assertion
was changed. The new regression test test_grouping_e2e.py runs the real
five-page manifest in a temp directory and asserts 51 rows → 5 products,
one review per URL, published 0, Notre names present, and one product_id
per Shopify page.

## Raw artefacts on the iMac

- /Users/discodadz/nexus-run/titlefix_result.json, titlefix.log
- /Users/discodadz/nexus-run/groupfix_result.json, groupfix.log
- /Users/discodadz/nexus-run/groupfix2_result.json, groupfix2.log
- Acceptance output: pkg/export_groupfix2_new/ with DB
  pkg/nexus_groupfix2_new.sqlite

Cross-reference: the site-side half of this batch (mobile-home
implementation applied to Local) is reported separately in
docs/mobile-home-application-report-2026-11-12.md.
