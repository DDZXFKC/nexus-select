# Exact batch1 two-file generator

Run with Python 3.9+:
```
python3 tools/build_buyma_batch.py --input selected.csv --output new_batch1 --prefix batch1 --config local.json --reproduce-batch1
python3 tools/compare_buyma_batch.py --actual new_batch1 --expected tools --prefix batch1
```
Local config JSON: selection_sku (default SKU), woo (original Woo prep CSV), size_table (original Google values JSON export or CSV brand,department,size_original,cm), brands (object keyed by actual Woo Brand). Each brand has source (original brand SP CSV productId,description_en,url), brand_id, brand_name, categories (Men/Women/Kids IDs). HOKA historical ID 6906, name HOKA ONE ONE, Men 3321 Women 3081. UGG ID 89; category IDs must come from approved BUYMA master. Normal mode also requires approved_buyma_prices (SKU→JPY), color_ids (exact color name→approved BUYMA ID), verified_kids_sizes (SKU→list of exact normalized verified US C/Y sizes). Use verified A2 joined brand chart for normal mode, not Woo old cm. No guessed IDs or price. Historical mode preserves old price, color rule, missing search sizes solely for reproduction, never for listing. All stock rows preserved as in original. Output exact headers, BOM, CRLF, two files.

Original local inputs named by build_batch1.py: /tmp/size_table.csv, /home/hatch/workspace/fl-scrape/shoepalace-hoka-all.csv, /home/hatch/workspace/fl-scrape/shoepalace-woo-import-prep.csv. None was registered in ca3f7bdd. The reference colorsizes has 156 data rows, 17 blank search cells, 139 filled. A separate final 56-cell correction artifact or before/after evidence is required to verify that correction; do not infer from output. No G-1 or batch2 until actual reproduction and correction verification pass. 
