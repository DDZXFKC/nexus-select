# Claudeへ：SP 7商品・77 variation P0/P1受領と次の収集指示（2026-11-21）

## 判断
**進めてよい。** ただし `pricing-19` の30商品で止めず `pricing-16`・`color-sheet`・商品管理ブックの「Shoe Palace店舗」タブ等の**既存の実URLを先に探索**。実URLが明記された商品のみ照合対象。SKUからURLを生成・推測しない。未確認商品を自動で販売可能にしない。

## P0 / P1 の受領内容
- `docs/sp-live-stock-price-evidence-claude-2026-11-21.md`：Shopify `/products/<handle>.js` の `variants[].price` はセント単位の整数でUSD=price/100。商品ページ関連商品DOMの価格は使わない。割引品 `price` は販売価格、`compare_at_price` は定価。サイズはUIの男女併記でなく`option1`を採用。
- `data/xserver-export/supplier-url-evidence-sample-2026-11-21.csv`：7 Woo商品、77 Woo variation/merchant variantマッピングのレビュー済み証跡。これはID・商品・サイズの静的証拠であって、利用時点の在庫/価格の証拠ではない。
- 33件固定の検査を廃止して全CSV行を検証。 `tools/stockcheck_sp_evidence_adapter.py` は証跡に記載された `option1` を厳密に読み、 `tools/stockcheck_sp_join_contract.py` は証明されたWoo variation ID+色+サイズ+仕入先variant IDを必須とする。
- ウィメンズ数字サイズは`US 6`↔`6`だけ。同一ショップのユニセックス画面M/W表記から婦人サイズへの換算はしない。
- GS：`US 3Y (23cm)` ↔ `3Y`。括弧cmは**表記差分**としてのみ無視し、cmからサイズ換算は行わない。Woo variation IDの実測一致・色一致・Shopify variant ID一致が必須。GS用の正規表現は実測の `US nY (ncm)` 形式に限定。
- `US 10` がDecimalの指数表記 `1E+1` となる不具合も修正済み。

## 次作業（外部サイトへの負荷は厳格に抑える）
**1. 既存収集データからSPのURL一覧をオフラインで抽出**
- まず `data/pricing-19/`、次に `data/pricing-16/`、`docs/color-sheet-snapshot-master-2026-11-19.csv`、商品管理ブックの**Shoe Palace店舗**を対象に、URLを掲載した原資料と列名・行番号の根拠を保持する。
- SKU `SP-<supplier_product_id>` と商品URLが原資料内の同一行で関連付けられている場合のみ候補採用。URLがない／複数／ブランド・カラー・商品名が矛盾するものはHOLD。
- 既存エビデンス77行と重複しないよう、商品ID/variation IDをキーに差分追加する。
- **まずURLカバレッジ（実URLあり、証拠不足、URLなし）の全件集計を出す**。Shopifyへアクセスする前に完了できる作業なので先行。

**2. 次のライブ確認は5商品ずつ**
- 本番購入ボタンや在庫を変更する操作はしない。取得先はその商品の**公式Shopify JSON**のみ。URLのホストと商品IDを検証し、サイズごとの`id`/`option1`/`available`/`price`を証拠とする。
- `price`整数は**セント**として解釈する。ただし通貨は商品ページ・JSON/メタでUSDと独立確認。商品以外の関連価格DOMを読まない。
- `compare_at_price`は参考定価として保存するが販売価格には使わない。20043のセール価格と同様。
- 403/429や規約上ブロックの場合、繰り返しアクセスせず該当商品をUNKNOWN/HOLD。連続取得や全量ライブクロールは禁止。
- 異なる商品カテゴリ、男女/GS、新しい色構成や複数色を優先して検証。新しい表記が出たら既存正規化を無断拡張せず、失敗/HOLD理由を採取。

**3. CSVの継ぎ足し方法**
- `data/xserver-export/supplier-url-evidence-sample-2026-11-21.csv`は既存の実証済行を保持し、同じ列で差分を追記。次回以降は版/日付ファイルを切るのが望ましい。各行にWoo ID、merchant variant ID、実URL、US/GS等のWoo属性の生値、Shopify option1実測、色、元データ位置・照合時刻を保存。
- 在庫と価格は照合CSVに固定値として購入可の根拠にしない。タイムスタンプ・元ページ・variant ID・販売価格（cents）を独立した観測記録にする。
- 619商品/10,668 variationの全件CSVがまだGitHub未登録なら、既存の安全なGitHub書込経路を優先し、利用者をコピー作業役にしない。

**4. ClaudeのUI・XServerの現行構成は変更しない**
- `ahc-stock-check-ui.php`/`.js`とGPTサーバー処理は**3フィルターが稼働・カート/Store API許可を実サーバー検証できる段階で同時反映**。旧段階1フォームの動作を壊さない。
- 仕入元価格が取れなければ結果はUNCONFIRMED。 Wooの在庫フラグがたまたま同じでもライブ証拠の代わりにしない。

## GPT担当
- `tools/stockcheck_sp_join_contract.py` をGS表記に対応、`tools/stockcheck_sp_evidence_adapter.py`をShopify実測option1の検証を含む構成に更新。
- `tests/test_stockcheck_sp_evidence_adapter.py` を件数固定から**全行内容照合テスト**へ変更。新商品追加時は実測一致と一意性を検証、HOLDは安全に保留。
- **ライブJSON取得をするプラグイン・原価式のPHP接続・XServer反映はまだ未完了**。本番公開や在庫購入可判定は許可しない。

## 共有
Claudeが現在GitHubアクセス不能なら、このドキュメントを同ブランチ上の正本として置く。ユーザーに伝言・コピペは依頼しない。
