# GPT検収1／再実行依頼（Shoe Palaceのみ）
実行報告 d8a7e6c4 を確認。基本処理は合格、全体検収は保留。
修正：21caec84（靴タグ判定・色タグと括弧の照合・NEWBALANCE alias）、86972dee（Woo prep SKU照合）。
既存 shoepalace-woo-import-prep.csv を利用する。新規シートの作成は不要。親SKU SP-<Shopify product ID> は既存 build_shoepalace_prep.py に根拠あり。variationは生JSONのSKUの一意性とParent一致を確認。既存列は保持し派生列を追加。全行のSKU重複、親子関係、未照合を記録する。
## 再実行
最新版2ファイルを取得。まず前回と同じ混合25件・靴25件のrepairを再実行。非靴のcm_status=NOT_APPLICABLE、靴の不足のみMISSING、公式表の未対応サイズは推測禁止。色の括弧はタグ裏付けのある場合に限り抽出し、100 Roses Mens Boxers (Red/Grey) Free Shipping の色を確認。色タグのない商品は要確認。NEWBALANCEとnew_balanceの対応を確認。日本語説明未生成はPENDING。
次に既存3ブランドの原本（163商品・1796 variant）と既存Woo prep CSVを同一範囲で照合する。最新全店バッチの先頭25件とは混ぜない。
```sh
python3 collector/shoepalace_sheet_reconcile.py --woo-prep --sheet "$PREP_CSV" --raw "$UGG_RAW" "$HOKA_RAW" "$VANS_RAW" --cm-reference "$CM_CSV" --output "$NEW_OUTPUT_DIR"
```
変数はMuseが実パスに設定。元CSVと原本のハッシュ前後一致、終了コード、親/variant照合数、未照合・重複・親不一致、元列保持、差分、再実行一致を報告。163+1796=1959行という報告値を現物で検算。全在庫なし商品も元データから消さない。出力のsp_列は派生列、Woo本番取り込み承認ではない。
追加の安全確認：靴タグの欠落・不明カテゴリを非靴と誤判定していないか、cmのブランド/年齢/性別/モデル差を正しく区別しているか、色以外の括弧を誤抽出していないか、SKU衝突を拒否するか。対象サイズの公式参照不足は具体的に列挙し、既存表を補う作業へ。価格・クーポン適用・画像加工・本番変更なし。GPT側で今回の修正コードの実行テストはまだ実施できていないため、Museの再実行証拠で検収する。全店11777件への拡張はこの検収後。