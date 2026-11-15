# AFTER HOURS CLUB｜新規取得テスト参照価格監査（2026-11-15）
対象コミット dc21a68d、research/online/local-pkg/standalone-fresh-run-2026-11-15/ の candidates.csv / candidates.json / run-report.md。CSV/JSON全8行21項目一致（referencesはJSON、sourcesは連結表記を正規化）。原本変更なし。
## 集計
候補8、参照145（SNKRDUNK122、BUYMA23）、価格付き130（SNKRDUNK112、BUYMA18）。個別取得日時・サイズ全145欠落、候補SKU欠落2。SNKRDUNKは全122件が検索URLのみ。BUYMA価格付き18件は全件他商品。BUYMA価格なし5件は未確認であり取扱なしの証明ではない。SNKRDUNK価格なし10件。検証済み仕入・利益0。全件HOLD。新規取得テスト実行自体は合格。
## 候補別
- AHC-001 Samba OG B75806: SNKRDUNK20価格のうち Cloud White/Core Black/Clear Granite 11,898円のみ商品名/色が一致、品番は https://snkrdunk.com/products/B75806 で確認。残19件は別色/別仕様/コラボ。元の価格は検索URL・サイズ/状態/個別時刻なしのため未検証、成約価格とは認めない。選定根拠18,835円は別色のWomen's。
- AHC-002 GEL-Kayano 14: 24,900円のCream/Cocoa Powderは同名同色だが実品番1203A537-118（https://www.asics.com/jp/ja-jp/gel-kayano-14/p/1203A537-118.html および https://snkrdunk.com/products/1203A537-118）。候補1201A380とは不一致。最高63,000円はTHOM BROWNEコラボ。国内公式22,000円の掲載も確認。サイズ別在庫は未検証。
- AHC-003 Clifton 9: US限定カラーの具体色不明。20価格にはClifton One 9、GTX、Women、コラボ等混在。最高44,908円はSupervsnコラボ。全件同一性未確認。
- AHC-004 XT-6 GTX: 候補Black/Phantomと一致する明示色なし。20価格の最大59,800円はLichen/NocturneまたはWhite Pepper等。SKUの対応関係未確認。
- AHC-005 Chuck 70 Hi: 20価格はFEAR OF GOD ESSENTIALSまたはOff-Whiteコラボ。通常品161318Cと同一と認めない。46,000円はOff-White。
- AHC-006 Patagonia Snap-T: 12価格（重複含む）と8価格欠落、Oatmeal Heatherと一致する明示色なし。BUYMA5価格はTHE NORTH FACE4、adidasバッグ1。公式ページ取得成功でもJSON-LD商品なし、74 USDは想定。
- AHC-007 Nike x Stussy: SKU/カラー欠落。SNKRDUNK価格なし、BUYMA7価格すべて別商品。仕入7,360円はadidas Fleece Shoulder Bagの出品価格（https://www.buyma.com/item/127085662/）、最高59,980円はSupreme別商品。差額52,620円は無効。
- AHC-008 Carhartt WIP x Nike: SKU/カラー欠落。SNKRDUNK価格なし、BUYMA6価格すべて別商品。仕入13,535円はCalvin Klein Women's Cropped Down Jacketの出品（https://www.buyma.com/item/110510083/）、最高76,980円はThug Club別商品。差額63,445円は無効。商品の実在も未確認。
## 結論
同一商品レベルの根拠があるのは001の1参照のみ。002は同名同色でも品番不一致。サイズ・状態・日時・価格種別の証拠不足により全130価格は検証済み価格として不採用。全8候補のselection_reasonの最高価格は別商品/別色/未特定商品に由来し、差額は利益ではない。公式5ブランド取得失敗＋Patagonia想定＋007/008別商品出品価格流用で、実測仕入0。現時点のCSVを販売価格決定・出品・購入に使用しない。候補自体は削除せずHOLD。413点の実務拡張は正式改修依頼書に従う。監査は保存済み全参照の照合と001/002の公開商品ページの品番確認。全130価格の当時の実測値を再取得したわけではない。実行環境の回線対策・403回避は行わない。
