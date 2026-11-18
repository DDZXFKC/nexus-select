# Shoe Palace価格情報の検証（GPT→Muse）
オーナーの訂正：今回のPythonで原価計算をする必要はない。価格が正しいものかのチェック。インボイスはMuse担当、GPTの開発は継続。原価・税・送料・売価計算は別工程。
追加コード collector/shoepalace_price_audit.py（07369d2d）。既存repair/reconcileを変更せず独立した検証処理。生JSONの商品ID＋variant IDによりサイズごとの取得価格・compare_at_price・定価の派生値・SKU・クーポンタグを全行照合。欠落、重複、価格0、異常額を検出。通貨はUSDという出力ラベルと、米国市場の公式情報による通貨根拠を別確認。タグは割引適用の証明にしない。過去スナップショットの一致と現時点の実販売価格の正しさを区別。
## 実行
前回と同じ163件の原本と最新版repairのrepaired.json、reconcileのsheet_repaired.csvで検証。実パスを設定し、以下を実行。
```sh
python3 collector/shoepalace_price_audit.py --raw "$UGG_RAW" "$HOKA_RAW" "$VANS_RAW" --repaired "$REPAIR_JSON" --sheet "$RECONCILED_CSV" --output "$NEW_AUDIT_JSON"
```
米国市場のUSD通貨根拠を実際に確認できた場合のみ --currency-evidence に根拠URL/記録IDを追加。インボイス未確認でも原本照合は実行可。終了0=照合合格、1=不一致、2=要確認（通貨根拠なし、定価逆転等）。既存WooのRegular priceはJPY売価でありUSD仕入価格との直接比較はしない。元20列は保持したまま、sp_price_minor等が原本と全行一致することを確認。既存店別収集CSVのpriceMin等が利用可能なら、同じ取得バッチに限り別途生JSONのmin/maxと照合し、既存CSVに差があれば具体例を記録。
受入：1796バリエーション、全行比較、欠落・重複・不一致0、通貨根拠確認、原本ハッシュ不変。意図的に1行のprice_minorを変えたコピー、欠落行、定価と現値入替、coupon_applicationを確定にしたコピーを検証し、終了1を確認。元データを変更しない。結果をGitHub docsへ。既存の色・cm作業（実行報告3の検収文書）も継続し、価格確認が未解決なら後工程への確定価格入力を保留する。インボイスを待つことを理由に他の検証を止めない。
GPT側はコード登録・照合済み。ローカル環境からGitHub rawへのDNS接続不可のため独立実行は未実施。Museの実行結果で検収。全店拡張は163件の見本接続と価格検証後。画像処理・ライブ取得・本番変更なし。