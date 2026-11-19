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

## GPT検収 5dc4c1b への修正（15:20）
- market：`mapping=<file>`（supplier_product_id,market,parent_sku）を必須に。CSVのmarketがLocal側根拠のmappingと違えば停止。SKUだけでmarketを決めない。
- 状態と構成：CONFIRMED なのに構成なし・先頭min(3,n)にHEX欠け、APPROVED_APPROX なのにHEX空、を拒否。原文（colorway・色名）は trim せずそのまま保存。
- rollback：形式名・サイト識別（host/home/blog_id）・投稿ごとのSKU・旧値と書込値を持つバックアップ。全件を先に検査し、現行値が「書いた値」か「旧値」以外なら1件も戻さない（CAS）。冪等なので途中で止まっても同じコマンドを再実行すれば戻る。バックアップは排他作成（既存なら停止）・書き込み後に読み戻し一致を確認してから本書き込み。書き込み中も1件ずつCAS。
- 保護スナップショットに親の価格・在庫と子の実効価格を追加。
- 初回は下書きのみ：公開中の商品は `allow_published=1` が無ければ停止。
- fixture：`tools/pick_swatch_fixtures.py` は下書きのSP商品だけから選び、足りない観点はシートからLocalに無い商品を選んで `fixtures.csv` に出す。`tools/ahc_create_swatch_fixture.php` が既存SP商品を型に隔離下書き（SKU `FX-SP-<id>`、非表示、`_ahc_fixture=1`）を作る。書き込みツールは `FX-SP-<id>` を、下書きかつ `_ahc_fixture=1` のときだけ受け付ける。`remove` で fixture だけ削除。
- テスト：書き込みツール 43件（停止系30件）すべて合格。

## GPT監査 c7e70d6（fixtureツール）への修正（15:30）
- create：CSV内の重複ID、親SKU・子SKU（FX-SP-<id>-<n>）・実SKU SP-<id> の衝突を全件事前に拒否。既定 dry-run。
- 実行ごとに run_id と manifest（新規ファイル）を作り、投稿を1件保存するたびに manifest を更新。保存結果・例外・読み戻しを確認し、失敗時は manifest で片付ける。
- remove：manifest に載った投稿だけ。親子それぞれの `_ahc_fixture`・run_id・FX-SP- SKU・親ID・下書き状態がすべて一致しなければ1件も消さない。既定 dry-run、`apply` で削除。
- 購入不可：mu-plugins/ahc-fixture-guard.php で `_ahc_fixture=1` の商品・バリエーションを購入不可・カート投入拒否（管理者が下書きを見られる場合も）。
- 複製した画像・価格・サイズは合成テスト値であることを `_ahc_fixture_note` とタイトル `[FIXTURE]` で明示。
- 書き込みツールは FX-SP-<id> を mapping で明示した場合のみ、下書きかつ `_ahc_fixture=1` を条件に受け付ける（39ffb24 のまま）。
- テスト：qa/php-tests/fixture_tool_stub_test.php 13件合格（重複・衝突・dry-run・remove の不一致拒否・購入拒否）。

## GPT検収 7f00676 への修正（16:20、fixtureツールのみ）
- 中断で孤児が残る問題：親・子とも `_ahc_fixture` と `_ahc_fixture_run` を save() の前に設定（同じ保存に含まれる）。manifest には保存前に予定SKU（親と子すべて）と run_id を記録。
- manifest：初回は排他作成（既存なら停止）・読み戻し確認、更新は run 固有の tmp から置き換え。
- remove：manifest の記録ではなく run_id のマーカーで投稿を探し、予定SKU・fixtureマーカー・親子関係・親が下書きであることを全件確認してから、子→親の順に1件ずつ削除結果を確認。途中で止まっても同じ remove を再実行すれば続きから消せる。run_id 空・予定SKU重複は拒否。
- 作成失敗時の案内は remove の dry-run（apply なし）に変更。
- テスト：変更部分のみ追加（remove 9件、孤児回収・部分削除からの再開・異物の子の拒否など）。fixture_tool_stub_test.php 全18件合格。
- mapping：FX 9件のみ承認（同じエクスポートの pid と manifest の FX-SP SKU を照合）。実商品158件は仮 mapping での dry-run のみ、apply しない。

## GPT最終検収 7bf74dd（CONDITIONAL PASS）の残件対応（17:40、fixtureツールのremoveのみ）
- 子SKUの実際の親が、manifest で予定した親SKUの投稿と一致しなければ停止（親が既に削除済みの再開時は、実際の親も存在しないこと）。
- 型の確認：親は variable・親ID 0・下書き、子は variation・親ID あり。違えば停止。
- 空SKUは自動削除しない（停止して DB スナップショットから復元）。
- 探索は全ステータス（trash・auto-draft 含む）。
- 説明を修正：Woo の save は DB トランザクションではなく、投稿作成とメタ保存の間で中断すると未マーカーの投稿が残り得る。その場合は DB スナップショットから復元する（removeでは消さない）。
- テスト：負例4件追加、fixture_tool_stub_test.php 全22件合格。
- 今回の隔離9件のLocal検証は、この修正を待たず 7bf74dd の保護条件（DBスナップショット・全差分保存）で進めてよい（GPT判断）。修正検収はこれが3回目だが、各回で残件が減っており進展あり（ff1c03a の停止条件には当たらない）。

## 反映するファイルの最新版（6d791c7 時点、c1e14f3 の比較表は旧版）
| ファイル | サイズ | md5 先頭12桁 |
|---|---|---|
| theme/main.js | 22,177 B | 4b736d99ce08 |
| theme/style.css | 48,220 B | 67e4be36a7dc |
| mu-plugins/nexus-variation-gallery.php | 15,560 B | 4f6602c773da |
| mu-plugins/ahc-fixture-guard.php（新規） | 1,624 B | 8d1252a4456e |

Local の SP 158点は全て公開中・下書き0（c1e14f3）なので、初回は9観点すべて FX fixture（tools/swatch_fixtures_fx_2026-11-19.csv）。手順4は省略可、手順5の template には公開中のSP商品を使ってよい（型として読むだけで変更しない）。

## 魔王ちゃんの手順（Localのみ・5dc4c1b修正後）
1. local-snapshot-2026-11-15 の theme/main.js・theme/style.css・mu-plugins/nexus-variation-gallery.php・mu-plugins/ahc-fixture-guard.php（fixtureの購入拒否）を Local に反映（メタが無い間は見た目不変）。商品ページ（MERGED 1点・SP 1点）で今までどおりか確認。
2. LocalのSP商品を書き出す（ID,状態）：`wp eval 'foreach (wc_get_products(["limit"=>-1,"type"=>"variable","status"=>["publish","draft"]]) as $p) { if (strpos($p->get_sku(),"SP-")===0) echo substr($p->get_sku(),3),",",$p->get_status(),"\n"; }' --path=… > sp_local.txt`
3. 最新シートから変換：`python3 collector/color_woo_export.py --master … --products … --output out`
4. 確認商品を選ぶ：`python3 tools/pick_swatch_fixtures.py --components out/woo_components.csv --local-ids sp_local.txt --out allow.txt --fixtures-out fixtures.csv`
5. 足りない観点の fixture を作る（fixtures.csv が空でなければ）：`wp eval-file tools/ahc_create_swatch_fixture.php create fixtures=fixtures.csv template=SP-<下書きのSP商品> manifest=<新しいファイル> site=<host> --path=…`（dry-run）→ 同じコマンドに `apply`。途中で失敗したら表示される remove コマンドで片付ける。作成後、fixture の商品ページでカートに入らないこと（購入不可）を確認。
6. mapping.csv を作る（読み取り専用の確認）：allow.txt の各IDについて `supplier_product_id,market,parent_sku`。market は Local 側の根拠（商品の仕入れ元URL等）で確認した値。fixture は parent_sku を `FX-SP-<id>`。
7. dry-run：`wp eval-file tools/ahc_color_components_to_woo.php out/woo_components.csv site=<host> allowlist=allow.txt mapping=mapping.csv --path=…`
8. apply：上に `apply backup=<新しいファイル>`。APPLIED の readback_mismatch=0・other_fields_changed=0 を確認。もう一度 apply（別のbackup名）して unchanged だけになること（差分0）を確認。
9. 画面確認：各商品で丸窓（縦縞／中立）・原文・サイズ選択・価格・在庫・画像、PC幅とスマホ幅、コンソールエラーなし。スクショを証拠に。
10. rollback の確認：`wp eval-file tools/ahc_color_components_to_woo.php rollback=<backup> site=<host> --path=…` で元に戻り、もう一度同じコマンドが OK（冪等）。確認後に再度 apply。
11. 158点（公開含む）は仮 mapping で dry-run のみ（`allow_published=1` を付けた dry-run、apply しない。GPT 7f00676）。結果をGPT検収へ。一括 apply は検収後。fixture は検証後 `remove manifest=<作成時のファイル> site=<host>`（dry-run）→ `apply` で削除。

## 未対応（GPT判断待ち・範囲外）
- HOLD と構成なしは、Local の158点に該当商品が無い可能性がある（手順4で判明）。無ければ 84e54b3 §4 の下書き fixture 取り込みが要る（実SKU重複禁止）。その取り込みは別途。
- MERGED の複数色連動 fixture は §4 のとおり別工程。今回の書き込みツールは MERGED を対象にしない。
