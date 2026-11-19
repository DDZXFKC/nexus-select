# 丸窓Local接続の実装（GPT設計 84e54b3 対応、Claude、2026-11-19 14:55）

## 変更ファイル
| ファイル | 内容 |
|---|---|
| collector/color_woo_export.py | market・colorway_original 列を追加。HEXは CONFIRMED のみ（DRAFT/UNKNOWN/HOLD は全HEX空）。swatch_status を厳格検証 |
| tools/ahc_color_components_to_woo.php | 全面改修（下記） |
| local-snapshot-2026-11-15/mu-plugins/nexus-variation-gallery.php | `__single__` と context を読み、単一色データを安全なJSON（JSON_HEX_*）で渡す |
| local-snapshot-2026-11-15/theme/main.js / style.css | 単一色：非操作の丸窓＋原文をサイズ表の上に表示。セレクト・サイズ・価格・在庫の処理には触れない |
| tools/pick_swatch_fixtures.py | Localに実在するSP商品から観点別の確認商品を選ぶ |
| qa/php-tests/woo_writer_stub_test.php, qa/js-tests/single_color_test.js | オフラインテスト |

## 書き込みツールの規則（84e54b3 §2）
- 照合：親SKU `SP-<supplier_product_id>` が投稿1件だけに一致すること。複数・0件・同じ親の重複は停止。
- 対象：色のバリエーションを持たないSP単一色のみ。色バリエーションがある商品（MERGED/PROTO等）は停止。
- 保存：`_ahc_color_components = {"__single__": [...]}`、`_ahc_color_components_context`（schema_version 2、shop/market/pid/color key/原文/status）。構成なしは空配列。
- 事前検証（1件でもあれば何も書かない）：ヘッダ完全一致、列数、position が整数、marker重複・混在、非single、status不正、行ごとの market/原文/status 不一致（同じSKUに複数market含む）、原文と構成色の不一致、対象外shop、HEX不正、CONFIRMED以外のHEX、position欠番、allowlist にあるのにCSVに無い。
- 実行条件：Localのホスト＋ `site=<ホスト>` の一致、`allowlist=<ファイル>` 必須。既定は dry-run。`apply` は `backup=<新規ファイル>` 必須で、書き込み後に読み戻しと「他の値（SKU・名前・状態・画像・ギャラリー・属性・各バリエーションのSKU/価格/在庫/画像/属性）が変わっていないか」を照合。差があれば rollback を指示して停止。`rollback=<backup>` で元に戻す。再実行は unchanged になる（差分0）。
- WP-CLI 2.12 は eval-file に `--xxx` を渡せないため、引数は `site=…` のような素の形にした。

## 描画（84e54b3 §3）
- 単一色：CONFIRMED かつ先頭 min(3,n) 色すべてに承認HEXがあるときだけ縦縞。ほかは白地・灰点線（中立）。白の確定色は既存の実線の縁で区別される。
- 4色以上も原文を全部表示。丸窓は `aria-hidden` の span でボタンではない（操作できない）。
- メタが無い商品は何も足さない（従来表示のまま）。複数色（セレクトあり）の既存処理は変更なし。

## テスト（すべて合格）
- 書き込みツール 28件（正常系9：dry-run、apply、各保存形式、読み戻し、再実行、rollback／停止系19）
- 単一色描画 10件、サイズ順 17件、変換 7件
- 最新スナップショット全11,777商品：原文と構成色の不一致0件、CONFIRMED 以外にHEXが付いた行0件（書き込みツールが誤って止まらないことを確認）。

## 魔王ちゃんの手順（Localのみ）
1. local-snapshot-2026-11-15 の theme/main.js・theme/style.css・mu-plugins/nexus-variation-gallery.php を Local に反映（メタが無い間は見た目不変）。商品ページ（MERGED 1点・SP 1点）で今までどおりか確認。
2. LocalのSP商品IDを書き出す：`wp eval 'foreach (wc_get_products(["limit"=>-1,"type"=>"variable","status"=>["publish","draft"],"return"=>"objects"]) as $p) { if (strpos($p->get_sku(),"SP-")===0) echo substr($p->get_sku(),3),"\n"; }' --path=… > sp_local_ids.txt`
3. 最新シートから変換：`python3 collector/color_woo_export.py --master … --products … --output out`
4. 確認商品を選ぶ：`python3 tools/pick_swatch_fixtures.py --components out/woo_components.csv --local-ids sp_local_ids.txt --out fixtures.txt`（該当なしの観点は表示される）
5. dry-run：`wp eval-file tools/ahc_color_components_to_woo.php out/woo_components.csv site=<Localホスト> allowlist=fixtures.txt --path=…`
6. apply：上に `apply backup=<新しいファイル>` を足す。APPLIED の readback_mismatch=0・other_fields_changed=0 を確認。
7. 画面確認：各商品で丸窓（縦縞／中立）・原文・サイズ選択・価格・在庫・画像、PC幅とスマホ幅、コンソールエラーなし。スクショを証拠に。
8. 戻すとき：`wp eval-file tools/ahc_color_components_to_woo.php rollback=<backupファイル> site=<Localホスト> --path=…`
9. 確認後、allowlist を sp_local_ids.txt（158点）にして dry-run のみ実行し、結果をGPT検収へ。一括 apply は検収後。

## 未対応（GPT判断待ち・範囲外）
- HOLD と構成なしは、Local の158点に該当商品が無い可能性がある（手順4で判明）。無ければ 84e54b3 §4 の下書き fixture 取り込みが要る（実SKU重複禁止）。その取り込みは別途。
- MERGED の複数色連動 fixture は §4 のとおり別工程。今回の書き込みツールは MERGED を対象にしない。
