# Grok independent review — 2026-11-12

Source: user-relayed Grok review; Grok reports read access but no write access. This is a condensed faithful record, not a verbatim transcript. Grok cited f12233c, 00578c8, 48df7f1. ChatGPT independently checked branch head f12233c46e5012d9c744732b8fd8f06ded90f380 and research/online/results/imac-2026-11-12-groupfix/RESULTS.md.

## Review findings
- Offline BSTN/Notre/Patta extraction, vendor fallback, parent title extraction, HOLD staging and review exports are working on tested inputs.
- Latest groupfix: five-page manifest, 51/51 staged, five products, Woo review 56 rows, BUYMA review five rows, profit review 51 rows, Notre names 26/26, 16/16 tests, published zero. Separate second BSTN page is not part of this batch.
- Main gaps: verified manufacturer style code, cross-merchant canonical identity, field-level provenance and source priority, verified size stock, image rights, full landed cost, resumable processing, host expansion, live import acceptance.
- Grok proposes collecting SKU/MPN/GTIN/barcode candidates, separating merchant SKU, improving product identity, provenance, stock claims and price-unit checks, configuration-driven host allowlist, evidence catalog, resume and delta processing, tests for cross-merchant identity and gates.
- Site observations: Safari gallery peek/color mixing and size guide mapping require real-device checks; home visuals, image performance and order-progress UX merit attention. Grok could not verify order tracking code or live checkout from repository.
- Efficiency proposals: bundled code/test/runbook/report handoffs, WP-CLI wrappers for repetitive authorized local tasks, automated route checks, SQLite and review CSV/JSON.
- Grok proposes independent review only; no direct write access. No ongoing Grok dependency.

## ChatGPT disposition
Accept priorities: verified style identity, provenance, price units, stock claims, reproducible offline package and regression tests. Reject treating GTIN/barcode as style code; these are distinct identifiers. Merchant SKU and MPN are candidates until verified against brand evidence. Do not treat available as verified purchasability. Content hash plus normalized source URL and parser version are appropriate processing keys; observation timestamp is metadata, not a dedup key. curl does not validate rendered Safari UX. Do not execute the old evidence_catalog blindly: review its evidence uniqueness and transaction/export consistency first.

Muse groupfix deviation is accepted as a temporary tested compatibility measure, not a general identity model. BSTN product_id is variant-level while Shopify product_id is page-level; separate source_product_id, source_variant_id and verified canonical product identity explicitly. Preserve distinct colors and merchants; never merge unknown style codes. A five-page result is not a six-page result. Existing local-pkg source is now in GitHub, so next task should make the package reproducible from clean checkout and include actual regression fixtures without uploading private HTML.

No live import, publication, purchase, theme or order changes authorized by this review. Keep all HOLD gates. Review-only role for Grok; ChatGPT and Muse continue independently. Next implementation must include tests, exact commands, acceptance criteria and report path together.
