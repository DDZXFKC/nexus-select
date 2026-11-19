# BUYMA batch generator — local execution

`python3 tools/build_buyma_batch.py --input selected.csv --output batch2 --config local.json`

Wrapper generator argv: `["python3","tools/build_buyma_batch.py","--input","{input}","--output","{output}","--config","local.json"]`.

The original build_batch1.py and its output schema are not in GitHub. The generator therefore uses explicit local mappings rather than inventing BUYMA category IDs, search-size codes, price formulas or column names. The following is the configuration contract, not a ready-to-run config. Muse must copy actual mappings from the local batch1 output and approved BUYMA masters. No secrets in GitHub.

- selection_sku: actual selected CSV SKU header (default sku).
- brands: object keyed by brand name, e.g. UGG or HOKA.
- Each brand config: source (local variant CSV path), brand_id (UGG 89), columns (canonical keys sku, product_id, variant_id, department, size, stock, category_key, price mapped to actual CSV headers), stock_values (actual source strings mapped to JSON true/false), categories (actual category_key mapped to approved BUYMA category ID), search_sizes (Men/Women/Kids objects mapping exact normalized cm string to actual BUYMA search-size value; use category-specific source if codes differ and do not guess), size_chart (non-UGG verified CSV with brand, department, size_original, cm, source_url, optional product_id).
- price must be approved BUYMA JPY selling price, not AHC price or supplier USD. Source must be final approved variant-level data with stock and listing fields.
- output_columns: ordered object keyed by actual batch1 CSV headers. Each value is one of {"derived":"sku"}, {"source":"actual_source_header"}, {"literal":"approved fixed value"}. Derived keys: sku, brand, brand_id, category_id, size_original, size_cm, search_size, size_source, price_jpy, product_id, variant_id.
- Output listing.csv has one row per in-stock variant. size_evidence.csv preserves original normalized US size, official cm and evidence URL. If batch1 requires a different layout (one row per product, multiple files, images, JSON, etc.), this version does NOT reproduce it; send actual build_batch1.py and sample output for exact adaptation before use.
- UGG uses repository official adult chart and official kids PDF-derived v8 chart, with product-specific age evidence and quarantined infant variants blocked. Missing or ambiguous size stops generation; no rounding to a search bucket without approved mapping.
- No publication or network calls. New output directory only. All source files read-only.
- Local execution and exact batch1 format compatibility not verified by GPT.
