# AFTER HOURS CLUB — GLM実データ隔離取り込み再実行報告
日付: 2026-11-14  
判定: **PASS（隔離取り込みのみ） / 全候補HOLD / published=0**

## 1. 対象・実行証拠
引き渡しコミット e6fe0d30、docs/glm-pilot-data-handover-2026-11-14.md を起点とし、integration/grok-review 上の research/online/local-pkg/glm-pilot-data/ にある原本を取得した。GPTのローカル隔離環境で原本バイト列を復元し、引き渡し資料に記載された3件のSHA-256およびGit blobを全件照合した。

| 原本 | bytes | SHA-256 | Git blob |
|---|---:|---|---|
| candidates.csv | 51771 | 21bc3b6c155b7d79fe36804435a6c59ffaa27d70d5897addfd588311b41aa933 | 27e4260199360ae66f71156afe4a87a9775d35fe |
| candidates.json | 61899 | 73bcc8bf0d595ead76cda546f491cdd32ac08342dffb029bc10fe11d994c82e2 | 7fcf7f6e1b86424b31d8170e9d5000b0695bb25d |
| discover_test.json | 108260 | 06fa04774efbd86194a41487ba6d4c2e33628b7c4c1e37c0e1ab65375b2db1c8 | 98e3d3f0f9888cbd8dcfdcf7cfa1a00677cb8d08 |

既存の pilot_report_import.py はDOCX専用のため、原本および既存コードを変更せず、CSV/JSON専用の pilot_data_import.py を追加。既存 sourcing_gate.run() をそのまま実行した。候補・参照を全項目保持し、確認済み証拠の入力欄（offers、references、cost_inputs）には一切渡さない。生のSKUは reported_style_code としてのみ保存する。

## 2. 実際に実行したコマンド
```sh
cd research/online/local-pkg
python -m unittest -v test_sourcing_gate test_pilot_data_import
python pilot_data_import.py --input-dir glm-pilot-data --out run-final-2026-11-14
```
※上記はリポジトリ内での再現手順。GPTでは同じblobのファイルを隔離環境に取得して実行。出力先は新規ディレクトリを指定すること。既存ディレクトリは上書きしない。

テスト実行結果: 24/24 PASS（既存14、新規10）。原本との全項目復元一致、CSV/JSON比較、実データ判定、テストデータ分離、再実行の出力バイト一致、上書き禁止、不一致・重複ID・重複JSONキー・参照スキーマ不正時の拒否を確認した。

## 3. 結果
| 指標 | パイロット | discover_test（診断用） |
|---|---:|---:|
| 候補 | 8 | 8 |
| 参照記録の隔離保存 | 145 | 282 |
| SNKRDUNK参照 | 122 | 122 |
| BUYMA参照 | 23 | 160 |
| 価格記載のある参照 | 130 | 272 |
| 個別取得日時欠落 | 145 | 282 |
| サイズ情報欠落 | 145 | 282 |
| 報告SKU欠落 | 2 | 2 |
| HOLD | 8 | 8 |
| 検証済み買付 | 0 | 0 |
| 検証済み成約 | 0 | 0 |
| 検証済み利益 | 0 | 0 |
| review_ready | 0 | 0 |
| approved_for_import | 0 | 0 |
| published | 0 | 0 |

CSVとJSONは数値表記およびsourcesの連結表記を正規化して全8候補の全フィールドが一致。二重計上なし。discover_testは別の診断データとして隔離し、パイロットに混ぜていない。全8候補のゲート判定は identity 不足によるHOLD。個々の価格は未確認主張としてのみ保存。欠損費用や利益をゼロと仮定していない。

## 4. 実データで確認したGLM側の問題
- discover_testのBUYMA 160参照は、全8候補それぞれに共通する20件（product_name・price_jpy・urlの組が一致）。検索結果の取り違えを実データで再現した。候補に対応する価格根拠として使用不可。
- candidates側では上記の全候補共通20件は存在しないが、AHC-007・008はSKU欠落のままBUYMA最低出品価格を買付目安に採用している旨がsourcesに明記されている。参照商品と買付商品の同一性・買付可能性は未確認であり、出品価格から仕入価格を推定してはならない。
- パイロットの全8候補にはGLMの「検証済み(自動)」表示がある一方、在庫状態は全件取得失敗、不明、または要ページ確認。参照日時・サイズが全件欠落している。GLM内の検証ステータスは証拠として採用しない。
- 代表相場・出品価格は成約実績ではない。原本の検索URL、価格、参照は保全し、検証済み価格への昇格を禁止。

## 5. 登録成果物と照合
- research/online/local-pkg/pilot_data_import.py — commit 071fb36a781e5b255603da717ddc08a4aaedb716, blob 49588f4170f34a620c1bbd9a0617600fbe380c44
- research/online/local-pkg/test_pilot_data_import.py — commit 8097eea265e76043ce18fae869f896415eeb70bd, blob 767ae0a7a26e21fb46ccc090e4bee3272d3da88b
- research/online/local-pkg/glm-pilot-data-audit-2026-11-14.json — commit b17012b69d2411a6a140d49cd362b1ed769731aa, blob 1a83cab9f4319bb7cebf7613082b5902c9142351

すべてローカル実行済みファイルとGitHub再取得blobが一致。既存 sourcing_gate.py（55951b60957fcbf4fe72a175c67c49aa9e74cede）、stage2_review.py（eb21a616ca7d778dd3e793d37987440b3f0f1211）、test_sourcing_gate.py（be1ff0d751300c0b9f6a84afa2cf79385e383490）、pilot_report_import.py（c8e0dd1e25d9b3b983f0a3d1567dbce5fe8512ff）も原本blobと照合済み。

隔離出力（ローカルのみ）: report_claims.json、decisions.json、candidate_watchlist.csv、discover_test_claims.json、discover_test_decisions.json、audit_summary.json。商品別生データを重複登録せず、GitHubには集計監査結果と再実行可能なコードを保存した。

## 6. 次工程と制約
隔離取り込み工程は合格。GLM発掘システム全体の完成・実収集合格ではない。次はGLMの /home/z/my-project/sourcing/ のソースを回収後、BUYMA検索・商品同一性・価格証拠の修正を検証し、新規出力を同じゲートで再実行する。取得制限を回避しない。MuseおよびGrokによる独立レビュー・実行は未確認。今回のライブリクエストは0件、WooCommerce・WordPress・本番DBへの書き込み0件、公開0件。リマインダーの完了更新は行っていない。
