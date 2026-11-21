# Claudeへ：在庫確認3フィルターの実データ接続調査（2026-11-21）

## 結論
**同時反映に賛成。現在の段階でXServerへ入れるのは不可。** `tools/ahc-stock-inline-endpoints-staging.php` には3つのフィルターの呼び出し口があるが、3つとも本番仕入先データを供給する接続コードは未実装。モック16件合格は実在庫判定の証拠ではない。

### 1. ahc_inline_verified_offers
候補：GitHubの `tools/cross_shop_sku_core_v2.py` による**SKU核の完全一致**の照合結果（AUTO、GLM検収済のみ）、`tools/cross_shop_offer_contract.py` の元データ保存契約、`collector/batch3/output/batch3_items.csv` 等。

**不足しているもの：**
- XServer上のWoo商品/バリエーションID ↔ 検収済みの照合ペア ↔ 仕入先別URL/店舗IDの確定対応。
- 色・サイズとその店舗ページ内バリエーション識別子との厳密な対応。
- 候補店別の現地送料・税・関税等を含む原価見込み。
- これらのデータの本番投入先と更新の責任分界。

単にメーカーSKU・商品名が似ているだけでURLを作らず、証跡のないレコードは候補ゼロ `no_candidate` とする。

### 2. ahc_inline_check_one_offer
候補：`tools/stockcheck_core.py`（HTTP取得のタイムアウト、ブロック、証跡・判定の枠組み）、`ahc-system/src/ahc/stores/shopify_adapter.py` および `research/online/shopify_variants.py` 等の収集コード。

**不足しているもの：** XServer上の実際の仕入先商品ページで、要求した色・サイズについての在庫と現在価格・通貨を**同じ照会で取得する店舗別パーサー**。静的なCSVや過去の在庫スナップショットは購入許可の根拠にならない。403/429、構造変更、価格不明はすべて `UNCONFIRMED`。サイト実接続と実例の検証が必要。

### 3. ahc_inline_recomputed_sale_price
候補：`ahc-system/src/ahc/cost/calculator.py`／`models.py` は原価内訳とFX計算を支えるが、**WooCommerce販売価格の完全な決定式ではない**。`tools/reprice_buyma_19.py` は**BUYMA固有の式**で自社ECへ転用不可。`data/pricing-19/sp_margin_19_2026-11-20.csv` は過去価格のスナップショットで、要求時点の最新現地価格ではない。

**不足しているもの：** AFTER HOURS CLUB 自社ECに対しオーナーが承認した最終価格式・通貨/為替時点・現地税・国内送料・関税・輸入消費税・買付代行・決済/販売手数料・確認済クーポン・丸め規則、実データの参照元。必要項目が欠けた場合は販売価格を未確定にする。400円閾値は計算後にのみ適用。

## 次の実装・検収の順序
1. XServerの商品ID/variation IDとSKU、候補URLとサイズ対応、原価入力の**読み取り専用データ検証**。公開GitHubの旧スナップショットをそのまま本番正本としない。
2. 3フィルターの接続実装。URLと完全な原価がない場合、**絶対にカート許可しない**。
3. 商品3ケース（在庫あり、全店品切れ、確認不能）で現物実行・証跡・適正価格の照合、400円上下と複数店のケース。
4. XServerの稼働中の`ahc-stock-check.php` と`ahc_stock_check_allow_cart` の内部許可が働くことを**ステージング/Basic認証下で実測**。HTTP 200だけでなく、カートの品目・variation・価格の一致、Store API直打ち拒否・シークレット初回ゲストを確認。
5. **ClaudeのUIとGPTの唯一のサーバー側モジュールを同時反映**。二重モジュール `tools/ahc-stock-inline-cart-gate-staging.php` はロードしない。ロールバックとDBバックアップを確保。

### 「いつまでに」への返答
実際のXServer環境・上記のSKU対URL/サイズ/現地費用の正本データがまだ利用できないため、確約できる時刻は提示しない。**情報がそろったことを根拠にE2Eを終えた時点で「接続完了」と判定**する。未実装なのに見込みだけで反映を促さない。

**担当区分**：GPTサーバー/データアダプター。Claude UI・XServerでの実画面確認。ClaudeのUIファイルはGPT側では変更しない。
