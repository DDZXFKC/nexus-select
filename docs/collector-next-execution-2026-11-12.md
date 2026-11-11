# Next execution order — NEXUS SELECT collector

## Final goal (work backwards)
A repeatable pipeline: existing merchant sources -> lawful product data extraction -> common evidence store -> complete WooCommerce draft import and BUYMA listing preparation -> separate accurate channel profitability -> staging verification -> release readiness. No live publishing or ordering without authorization.

## Current proven checkpoint
One BSTN page / 13 size rows; DB accepted 13; WooCommerce review 1 parent + 13 variations; BUYMA review 1 product; all HOLD. No multi-merchant proof and no staging import proof. Missing color, manufacturer style code, verified stock, rights-cleared images, costs.

## Next execution: Muse (execution-only, no coding)
1. Read this document and collector-handoff-2026-11-12.md on integration/grok-review. Do not edit scripts or theme.
2. On iMac, **read-only** inventory of LocalWP WooCommerce products' existing merchant source URLs. Report total products, number with source URL, and shop host counts only. Do NOT put product/customer/order data or URLs containing private identifiers into public GitHub. If no safe export mechanism exists, report blocker; do not improvise database changes.
3. Select 3 distinct permitted merchant hosts from existing URLs where possible, and 2 product pages per host. Check robots and terms before retrieval. Skip any prohibited or blocked host (including previously blocked Foot Locker/Zalando) without bypassing access controls.
4. For each allowed page, save the HTML locally (not public GitHub). Make a private CSV manifest with columns html_file,product_url pointing to saved pages. Keep paths within manifest directory, and avoid customer or credential content.
5. Execute the **existing** merchant_to_channels.py package with one manifest containing all pages; use a NEW SQLite DB and NEW output directory (never overwrite the previous BSTN evidence). Run documented targeted unit tests first. If dependencies missing, report exact error and stop that step, not the entire unrelated audit.
6. Report only: host count, page count, extracted product/size rows, DB accepted/rejected, WooCommerce parent/variation rows, BUYMA product rows, missing fields by host, per-host errors, and whether any non-HOLD rows appeared (expected zero). Do not publish/import products.
7. If safe read-only source inventory is impossible, use existing publicly sourced product pages already available in local collector records, but clearly label them as alternate sources and do not claim they came from the 401 products.

## ChatGPT's immediate follow-up once results arrive
Fix parser and grouping failures, add merchant-specific extractors as necessary, validate WooCommerce staging import and BUYMA field requirements, then execute a single final acceptance batch. Do not stop at test counts or ask the user to say 'continue'.

## Strict controls
- Muse executes and reports; ChatGPT writes and fixes.
- No code edits, plugin installs, LocalWP theme changes, live product edits, automatic publishing, orders, or purchases.
- No secrets, private records, customer data or sensitive business data in public GitHub.
- A check marked passed only after observed evidence; do not imply complete before multi-merchant and staging validations.
