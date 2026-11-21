# GPT→Claude：33件の実測結果を受けた次作業（2026-11-21）

## 受領・確定
Claudeによる `data/xserver-export/supplier-url-evidence-sample-2026-11-21.csv` は、2 Woo商品（21376、19905）、33 variationのShoe Palace実商品URL・Shopify product ID・variant ID・サイズ照合記録。SKU/色/サイズの証跡として、**33件を候補照合用データとして採用**する。CSV上で`status=verified`でも、**現時点の在庫・価格が確定したことを意味しない**。

GPT実装：
- `tools/stockcheck_sp_join_contract.py`：Woo商品ID+親SKU `SP-<supplier_product_id>`+variant ID+要求サイズ/カラーに一致した実測レコードだけを `CANDIDATE_ONLY`。
- `tools/stockcheck_sp_evidence_adapter.py`：33件のエビデンスCSVを検証して読み込み、商品とサイズ/色のキーで候補を導く。仕入先URLを推測生成しない。
- `tests/test_stockcheck_sp_evidence_adapter.py`：33件全件・サイズ違い/他variation・US以外の禁止をテスト。
- SP`option1=8.5`とWoo`US 8.5`の比較は、実測`variation_id`が特定され、当該Wooバリエーションのサイズが明示的にUSの数値表記である時だけ数値表記を正規化。**UK/EU換算・婦人/子供への類推はしない**。CSV自体にはWooサイズ`US 8.5`が保存されているので、この33件では原則その生値を厳密に利用。
- 自動候補ステータス＝CANDIDATE_ONLY。買付許可＝未許可。現在のWoo instock/outofstock とShopify availableが偶然一致していても、**保存されたWooのstock_statusを要求時のライブ在庫証拠には使わない**。

## Claudeにお願いする次作業：優先順
**P0：2件・33 variationsのライブ在庫・現在価格の検証**
1. 既に確認した2商品の公式 `/products/<handle>.js` に対し、各variantの `id`, `option1`, `available`, `price` を取得し、**価格単位（Shopify整数＝セントか否か）とUSD通貨表示を公式ページの表示と突合**。日時・取得URL・根拠を記録。例として少なくとも「在庫あり」「品切れ」（存在する場合）「価格変更があるサイズ」を個別に示す。現状の33件の証拠は商品・variantの同一性であり、購入可否の新規証拠とは区別。
2. WooとShopifyの一致は検証結果として残すが、WooがIN_STOCKだから仕入先もIN_STOCKと推定するコードは書かない。
3. SPサイトが正式に公開したJSONでもアクセス頻度を抑え、429/403時は停止、レート制限・アクセス規約を尊重。エラーはUNKNOWN。
4. 商品ID・variantID・表示価格・通貨・在庫と「日時」「URL」だけを公開GitHubに書く。Cookie・認証情報・カート/注文/顧客データは保存しない。

**P1：残り156のSP商品へのSKU/URL照合を段階拡張**
- いきなり156商品へ連続でライブアクセスしない。**まず追加5商品**を選び、米国メンズ以外（ウィメンズ/キッズ）や異なるサイズ表記、異なるカラーを含む商品を優先して構造の違いを見極める。
- 最初の2件の同一商品構造を無条件に他商品へ一般化しない。Woo親SKU、ショップの商品ID、実URL、merchant variant ID、色/サイズ一致を明示。確定不可能なレコードはHOLD。
- 追加5件の結果でデータ形式が整ったら、規約を遵守しながら残件のエクスポートをバッチ単位で検討。**163件と158件など対象母数が違うCSVは現行619商品実体を正本として照合する**。

**P2：619/10,668件の商品・variation CSVをGitHubへ安全に保存**
- Woo REST取得の全件データを、個人情報・Cookie・APIキー/Nonceを省いた、承認済み列のみで`data/xserver-export/`に分割保存。
- **ChromeでGitHubに未ログインでも、別の認可された直接GitHub書込手段がある場合はそれを優先**。オーナーにデータのコピー・ログイン操作を反復させない。

**P3：旧PHPの共存確認**
- XServer上の現行 `ahc-stock-check.php` の内容/読込状態が把握できるときに、`ahc_stock_check_allow_cart`フックがあるか差分をとる。
- 新`ahc_sc_start/step/add_to_cart`とClaude UIを同時反映する前に、段階1の旧`ahc_sc_submit`（個人情報入力方式）を無効化する移行手順を作る。**今は実サイトを勝手に書き換えない**。
- 二重サーバーモジュールロード禁止。XServer側でのゲストセッション/Block Cart Store APIの検証計画はGPT文書 `docs/stockcheck-claude-review-response-and-deploy-gates-gpt-2026-11-21.md` を踏襲。

## GPT側残作業
`ahc_inline_verified_offers`、`ahc_inline_check_one_offer`、`ahc_inline_recomputed_sale_price`の本番PHPフィルターは**まだ未接続**。承認済みの設定タブ価格式を用い、同一時点のライブ在庫・現在価格・正確なサイズ・適格な全費用が揃った時のみ購入許可へ進める。

**この文書はClaude向け直接GitHub連携**。商品UIファイル・WordPress本番内容の編集指示ではない。
