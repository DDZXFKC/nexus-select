# 3-agent next execution and review — 2026-11-12

## Scope and source of truth
Branch integration/grok-review. ChatGPT authored tools/evidence_catalog.py (stdlib Python 3.9, offline saved HTML, any merchant hostname; no live fetching). Muse's latest report: docs/collector-execution-report-2026-11-12.md. Existing WooCommerce 461 posts yielded ZERO merchant URLs. Do not claim 401 source URLs exist. No live publishing, changes to theme/products, purchases, or secrets in public GitHub.

## Goal and acceptance
End goal: multiple permitted brand/retailer product sources, one canonical product by VERIFIED brand + manufacturer style code, distinct merchant offers, source provenance, complete WooCommerce and BUYMA review drafts with independently verified pricing, stock, image rights and channel fees. Unverified items remain HOLD. Current new code is **foundation only**, not the completed channel pipeline.

## Muse — next batch, execution only
1. Fetch tools/evidence_catalog.py from this branch. Do not edit.
2. Run `python3 -m py_compile tools/evidence_catalog.py` on iMac. Requires no third-party packages.
3. Prepare a local private directory with CSV `html_file,product_url,source_tier,verified_style_code`; tiers: brand_official, authorized_retailer, other_retailer. A style code is only entered if independently confirmed; otherwise leave blank. Keep saved HTML beside the manifest; do not upload raw HTML or private sourcing records.
4. Use two BSTN HTML pages already saved, then 2 pages each for Notre and Patta only if permitted and fetchable without bypass; if not, mark as skipped and substitute other permitted source pages. This script does NOT fetch URLs. Fetch permissions are a separate decision. Do not use blocked hosts.
5. Run `python3 tools/evidence_catalog.py --manifest /LOCAL/PRIVATE/manifest.csv --db /LOCAL/PRIVATE/evidence_new.sqlite --out /LOCAL/PRIVATE/review_new` (replace paths locally). Run a second time with same arguments to test unchanged-page skip.
6. Verify no publications or WooCommerce changes. Report: python compile pass/fail; pages attempted; parsed size rows; per-host errors; product dedup count; unchanged skip on second run; whether style codes were verified or blank; whether 2 different merchants with same verified style code map to ONE product. Do not manufacture style codes to make the test pass.
7. Publish a SANITIZED report only to docs/collector-catalog-test-report.md on the branch. Never publish product/customer data, private URLs, prices, or credentials. If missing a second merchant, state not tested.

## Grok — independent review requested
Read tools/evidence_catalog.py, docs/capability-review-2026-11-12.md and Muse report. Review for (a) JSON-LD product graph coverage, (b) safe host validation and local path traversal, (c) transactional correctness on failures, (d) idempotency and offers duplication, (e) false merging when style codes are unverified, (f) source priority, (g) Python 3.9 compatibility, (h) completeness gaps for WooCommerce/BUYMA. Return concrete findings with severity and line numbers to docs/grok-catalog-review.md if write access exists; otherwise GitHub PR/issue comment. Do not edit production theme. This is a REQUEST, not proof Grok has reviewed.

## ChatGPT next work on receiving reports
Address verified failures; add canonical field-level provenance and source precedence, explicit manufacturer code validation, channel-specific cost engine, stock timestamps, rights checks, and staging-only WooCommerce import dry run. Record tests and only then claim acceptance.

## Result handoff
Both agents use this public branch for sanitized status only; full sensitive data remains on iMac. No user copy/paste relay. The agents must independently poll/read GitHub; GitHub commits alone do not wake either agent.
