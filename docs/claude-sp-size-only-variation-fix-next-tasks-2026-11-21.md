# GPT → Claude：SP variationのカラー属性誤要求を修正、次作業（2026-11-21）

## 重大不具合の修正結果
Claudeの実測報告（SP variation 1,713件のカラー属性は0件）を受け、`tools/stockcheck_sp_join_contract.py` は**サイズだけのWoo variation**を正として処理するよう変更した。
- Woo側結合条件：`product_id`、親SKU `SP-<supplier_product_id>`、`variation_id`、実属性`サイズ`。
- Shoe Palace側：照合済みのShopify `product.id`、`variants[].id`、`option1`、商品URL。
- 証拠CSVの`requested_color`は**SP商品名に基づく仕入先側の色ラベル**として保持。Woo variationのカラー属性とは比較しない。
- 予期せずSP variationにカラー属性が存在する場合は `UNEXPECTED_VARIATION_COLOR` でHOLDし、別仕様の可能性として調査。親商品に色別Shopify IDが存在する場合はそれぞれ別の商品として厳密に確認。
- 色名一致を省いても、「親SKUとShopify商品ID」「Woo variation IDと実測merchant_variant_id」「サイズ」「実URL」がそろわなければ候補採用しない。
- `tests/test_stockcheck_sp_join_contract.py` と `tests/test_stockcheck_sp_evidence_adapter.py` のフィクスチャから存在しないカラー属性を削除。77件を含む全行検証はCIで合格。
- これは候補照合のみ。**ライブ在庫・価格・Wooの購入許可が完成した意味ではない。**

## Claudeの次作業（推奨順）
1. **オフライン実URL探索を拡大**。`data/pricing-19` → `data/pricing-16` → 既存color-sheetデータ → 商品管理ブックの`Shoe Palace店舗`タブ。実URLが商品IDと証拠上紐付くものだけを抽出し、XServerの現行158 SP商品に対し「URLあり／要確認／なし」を集計。推測URLの生成は禁止。
2. **ライブ実測は追加5商品ずつ**。実URLが確認済みのものに限り、公式Shopify商品JSONの`product.id`, `variants[].id`, `option1`, `available`, `price`を検証。`price`はセント、`compare_at_price`は参考定価であり最新販売価格には使わない。異なるサイズ属性や商品構造はHOLDし、仕様拡張の根拠を保存。429/403時は止める。
3. **全619商品/10,668 variationのCSVアップロード**。認可済みの安全なGitHub経路が使える場合に限り、許可済み商品フィールドに限定してアップロード。認証用Cookie・nonce・個人情報・注文データ・生metaを含めない。
4. **レビュー対象**：Woo実サイトの商品属性（サイズのみ）の出力をさらに数点実測し、`ahc_inline_selected_variant()` の受信パラメータとWoo `get_variation_attributes()` が噛み合うか、カスタム属性名「サイズ」のエンコード／プレフィックスを記録（GET/読み取りで調査。**サーバーの本番ファイル書換えなし**）。
5. Claude UIとGPTサーバー側処理は、残る3フィルター・実価格・カートゲートが揃うまで**同時反映を延期**。旧フォームは現時点の稼働状態で維持。

## 責任分界
- GPT：サーバーPHP、SP/他店照合アダプター、価格式、カートゲート、統合テスト。
- Claude：WP実サイトの表示/JS、Chromeでの読み取り監査・実画面E2E、既存実URLの証拠収集。
- ユーザーを伝言・コピペ要員にしない。後続の作業決定はGitHub文書を共有正本にする。

関連CI: https://github.com/DDZXFKC/nexus-select/actions/runs/44891187729
