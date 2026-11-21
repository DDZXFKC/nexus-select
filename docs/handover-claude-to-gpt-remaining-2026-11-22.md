# Claude → GPT：残りのタスクの引き継ぎ（2026-11-22 05:00 JST、オーナー指示）

オーナー指示（04:50）：「それが終わったら、GPT に残存タスクを引き継いで」。
正本は GitHub（DDZXFKC/nexus-select、integration/grok-review）。

## Claude が終えたもの（参照）
- SP 158 商品・1,713 サイズの実測 SKU 照合：全件 PASS（f23c996）。
- SP 画像：Stadium Goods の PNG（白い正方形）を 121 件に適用。目視で色・形違いの 6 件は元に戻した（92f68ad）。
- 透明 PNG 420 商品に白い下地を入れた：添付 1,087 枚、メイン画像は 420/420 が白い正方形（f2edf2d）。
  - 元に戻す規則：白いコピーは添付 ID 21594 以降で、ファイル名が `<元のファイル名>-white.png`。
- 画像のない下書き 37 件のうち 6 件（Converse）に Stadium Goods の PNG を適用（docs/image-noimage-drafts-claude-2026-11-22.md）。
- 在庫確認ポップアップ（画面側）を確定仕様に修正し、テスト 24/24（6fdfde2）。**XServer には未反映**。
- 全商品のメイン画像の監査（c24e691）。

## GPT に引き継ぐ残りのタスク
### 1. 在庫確認 → カート → 購入画面（最優先、relay-to-claude-stockcheck-start-2026-11-22.md）
- **XServer への反映経路がまだ決まっていない（オーナーの回答待ち）。**
  - A：XServer のファイルマネージャーか SFTP（推奨）。旧 mu-plugin の `ahc-stock-check.php`（名前・メール入力の旧フォーム）を入れ替え・停止できる。
  - B：管理画面から ZIP でプラグインとしてアップロードする。旧フォームを止められないため、旧フォームと新ポップアップが二重に表示される。
- 反映するファイル：
  - Claude の画面側：`local-snapshot-2026-11-15/mu-plugins/ahc-stock-check-ui.php`・`.js`
  - GPT のサーバー側：endpoints、sp-live-adapter、sp158-owner-bridge、cost-coverage-provider
- `ahc-stock-inline-cart-gate-staging.php` は入れない（endpoints と `wp_ajax_ahc_sc_add_to_cart` が重複する）。
- **仕様違反の修正（GPT 担当）**：自動の期限切れを外す（docs/claude-to-gpt-no-auto-expiry-violation-2026-11-22.md）。
  - 購入許可の 300 秒（`set_transient(...permit..., 300)`）
  - カートの中身の 60 分（`ahc_inline_cart_line_valid`）
- **SOLD OUT 表示の重複**：`woocommerce_available_variation` のフィルターが、Claude の UI と GPT の endpoints の 2 か所にある。どちらか 1 か所にする（docs/claude-audit-oos-filter-duplicate-2026-11-22.md）。
- **オーナー確認待ち**：画面側で、買い付け先の応答が 45 秒ないときに「つながらない」と表示する動きでよいか。
- 実機テストの項目：
  - PC とスマホで、在庫確認 → カート追加 → 購入画面まで（決済はしない）。
  - 売り切れ表示、仕入れ費用の設定が未確定のときの止まり方。
  - 結果は GitHub に記録する。

### 2. シートの商品データをサイトへ入れる（オーナー指示 03:49、条件の回答待ち）
- 未確定の点：
  - 新規追加か、既存商品の更新か
  - 対象のショップと件数
  - 下書きにするか、公開まで進めるか
  - シートの読み方（GPT は Google Sheets を読める）
- 決まっているルール：
  - シートが正本。ショップごとに分け、同じ商品でもショップ別のデータを統合しない。
  - 販売価格＝仕入総額÷0.785（利益率 16％・BUYMA 手数料 5.5％）。
  - 原価＝現地価格×158×1.02＋国際送料 2,200 円＋パートナー費用 1,500 円＋梱包 60 円。
  - 画像は正方形・白背景・1 画面に 1 画像。公式 PNG は切り抜かず白い正方形に置くだけ。
  - SKU（型番）が同じなら Stadium Goods の PNG を優先する。型番がない商品には流用しない。

### 3. 画像の残り
- **画像のない下書き 31 件**（Converse 単品 19、Converse まとめ商品 4、Nike 8）。オーナー決定：情報がそろっているので消さない。
  - Stadium Goods では型番の完全一致が見つからなかった。
  - オーナーの質問「Stadium Goods の画像はシートの中にあるよね？」→ **GPT がシートを横断して、これらの型番の Stadium Goods 画像 URL があるか確認してほしい**。
  - 参考：A18154C には Stadium Goods に「A18154F」（末尾違い）がある。使うかはオーナー判断。
  - Converse のまとめ商品 4 件は、色ごとに元の単品の画像を割り当てる。
- **SP の HOLD 37 件**：オーナー決定により、当面グレーの写真のまま。他店の写真は、背景確認が済むまで流用しない。
- **FL の正方形でない 4 件**（6374・6546・6640・9834）：未対応。
- iMac の「書類/NEXUS SELECT 画像マスター」への保存：未実施（iMac のファイルにここから届かない）。
- **画像を適用するときの注意**：型番が一致しても、Stadium Goods 側の取り違えがあった。19207 では Grey Heather の型番にサンド色の画像が付いていた。必ず元の画像と並べて目で確認してから適用すること。

## 作業環境の注意
- サイトの管理画面は、Chrome の再起動などで Basic 認証と WordPress のログインが切れる。ログインはオーナー本人が入力する。
- サイトのデータ（SKU・サイズ・属性）は書き換えない（オーナー決定）。
