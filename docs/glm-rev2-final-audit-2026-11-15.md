# AFTER HOURS CLUB｜改訂2 第8章監査（2026-11-15）
対象 e676cb2a / research/online/local-pkg/rev2-verification-2026-11-15/ と依頼書673966ff。判定：条件付き合格（安全側の回帰・出力確認）、実務完成は保留。ZIP本体・63テストのソースはGPT未取得。VM再実行は魔王ちゃん報告。
## 出力から独立確認
候補8、CSVデータ14行、JSON offers14、gate14（候補ID＋offer_id重複0）、全PENDING、HOLD14、approved0、review_ready0、expected_profit_jpy全null。仕入OBSERVED0、ESTIMATED6、UNKNOWN8。007/008の仕入はUNKNOWNのみ。gateのpurchase_price_jpyに想定6件の値が出るがpurchase_observation=ESTIMATEDで利益null。実測値として表示しない。
参照282（BUYMA160、SNKRDUNK122）、個別日時は全件記載、サイズ欠落282、品番欠落282、identity_match=true 0。BUYMAは各候補20件、product_name/price_jpy/urlの組の集合は全候補合計でも20種のみ（順序は異なる）。全候補にUGG/STONE ISLAND等が繰り返し出現。検索取り違え自体は未修正。ゲートが拒否するため誤利益は防止されたが、参考価格取得機能は未合格。SNKRDUNK全122件は検索URLのみ、価格種別ASK。代表価格を成約としない。候補のselection_reason/domestic_statusに未一致の参照件数を「参照価格取得あり」と表示しているため、同一商品確認済みの件数と生検索件数を分離する。
## 残件（最小修正・再検証）
1. BUYMA検索の取り違えと同一商品参考価格の出力を修正。規約に沿った検索/品番個別商品確認。取得不能なら未確認として保存、無関係な参照は診断用に隔離し候補の参考価格に表示しない。検索成功と同一商品の取得成功を区別する。SNKRDUNKも個別URLとサイズ/品番等を確認。少数の正しい商品で正の経路を確認する。
2. run_pilot.py OUT_DIR/STATE_DIR をプロジェクト基準または設定可能にし、iMacで起動・出力・再開確認。VMでパスを作れたことはiMac合格ではない。
3. AHC-002 Cream/Cocoa Powder の品番を1203A537-118に訂正。ASICS公式 https://www.asics.com/jp/ja-jp/gel-kayano-14/p/1203A537-118.html および https://www.asics.com/vn/en-vn/gel-kayano-14/p/1203A537-118.html にて確認。旧品番1201A380を正しい対象として扱わない。誤品番は回帰fixtureに保持可。
4. 第8章の残る実証：固定8候補リプレイは空状態からの新規発掘実証ではない。空の新規領域で既存リストなしの少数新規発掘→検証→承認用出力、許可された正規取扱店またはmanual_pricesの実測仕入とサイズ別在庫、同一商品参考価格、必要費用・利益計算、明示承認の正の経路を少数で確認。承認テストは隔離、実出品・購入・WP書き込みなし。手動価格・承認期限/証拠変更・再開・既存ゲート互換性のテスト詳細はZIP/DIFF/ログで確認。全件HOLDは負の経路の合格であり正の経路の証明ではない。成約のない候補も保持。全件取得や413件処理は要求しない。
コード全体の作り直し不要。未確認のテスト結果は推測しない。既存8候補の誤利益防止は維持。アクセス制限を回避しない。サイト変更なし。
