# SP出品プール 158件→163件 更新レポート（2026-11-20）

## 背景
オーナー決定（2026-11-20）：在庫ステータスは出品可否に一切使わない（BUYMAは無在庫販売が前提）。在庫以外の除外理由（USコンバース輸入差止等）は従来どおり。
この決定に基づき、在庫なしで販売不可になっていた5件を販売可能へ復帰させ、出品プールを158件→163件に更新した。

## 復帰対象5件と除外理由の確認
5件すべて Vans Premium Old Skool 36。`sp_sellable_list.csv` の記録上の除外理由は全件「在庫なし（全サイズ在庫切れ）」のみで、価格未検証HOLD（variants_hold=0）や輸入差止等の在庫以外の理由は混ざっていないことを確認した。全件復帰が妥当と判断した。

価格は SP元データ `~/workspace/fl-scrape/shoepalace-vans-premium-old-skool-36-all.csv` の priceMin を使用（既存の build_margin.py と同一の取得方法）。5件とも isSale=False・compareAtMin=0.0 のためセール品ではなく、割引後価格との区別は発生しない。

計算式（確定式）：仕入総額＝USD×158×1.02＋2,200＋1,500＋60／販売価格＝仕入総額÷0.745を¥100単位で切り上げ。既存158件と同じ build_margin.py の計算ロジックで再現した。

| SKU | 商品名 | USD | 仕入総額（円） | 販売価格（円） | 式価格一致 | 粗利（円） | 粗利率 | ステータス |
|---|---|---:|---:|---:|:---:|---:|---:|---|
| SP-7706357956814 | Premium Old Skool 36 Paint Splatter Mens Skate Shoes (Charcoal Grey) | 110.0 | 21,488 | 28,900 | yes | 7,412 | 25.6% | 候補継続 |
| SP-7716199235790 | Premium Old Skool 36 Souvenir Mens Lifestyle Shoes (Souvenir Oatmeal Beige) | 125.0 | 23,905 | 32,100 | yes | 8,195 | 25.5% | 候補継続 |
| SP-7716200317134 | Premium Old Skool 36 Souvenir Mens Lifestyle Shoes (Souvenir Faded Black) | 125.0 | 23,905 | 32,100 | yes | 8,195 | 25.5% | 候補継続 |
| SP-8796638675150 | Premium Old Skool 36 Souvenir Mens Lifestyle Shoes (Souvenir Navy Blue) | 125.0 | 23,905 | 32,100 | yes | 8,195 | 25.5% | 候補継続 |
| SP-8855807131854 | Premium Old Skool 36 Pearlized Grade School Lifestyle Shoes (Pearlized Black/Marshmallow White) | 110.0 | 21,488 | 28,900 | yes | 7,412 | 25.6% | 候補継続 |

販売価格は5件とも既存リスト記載の price_jpy と式価格が一致（price_match=yes）。全件粗利がプラスで「欠損のため保留」はなし。

## 実施した更新
1. `sp_sellable_list.csv`：5件の verdict を「販売不可」→「販売可能」へ変更。reason 列に変更記録を残した：
   「在庫なし（全サイズ在庫切れ）だったが、オーナー決定2026-11-20（在庫は出品可否に使わない）により販売可能へ復帰」
   変更したのは verdict と reason の2列のみ（価格・バリアント数等の数値は元のまま）。
2. `sp_margin_152.csv`：同じ列構成で5行を末尾に追記（ファイル名は変更なし）。追記後の行数は163行。
3. `summary.json`：従来の値が古い実行時点のまま（ok:152／ng:11）だったため、現行状態 {total:163, ok:163, ng:0} に合わせて更新した。

## 検証結果（全て合格）
- 更新後の販売可能：163件／販売不可：0件。
- margin 側：163件。販売可能SKU集合と margin のSKU集合が完全一致。
- 既存158件の無変更：sellable 側は対象5件以外の全行が更新前と完全一致（差分0行）。margin 側は更新前のファイル内容が更新後ファイルのバイト単位の前方一致（既存部分に一切手を入れていない）ことを確認。
- 対象5件の sellable 行は verdict・reason 以外の列に変更なし。

## 留意点（1件）
- SP-8855807131854 は Shoe Palace 側データに pre-launch／pre-release のタグがあり、発売日が 2026-11-27 と表示されている商品（未発売のため在庫0だったもの）。記録上の除外理由は在庫なしのみだったため、オーナー決定どおり復帰させた。受注後に買い付ける無在庫販売の前提では発売日以降に買い付け可能になる想定だが、発売前の受注が入った場合の扱いは親エージェント側で必要なら確認されたい。

## 未実施事項
- GitHub push・Google Sheets 書き込みは行っていない（指示どおり）。
- 価格が取得できない件はなかったため、保留扱いの件はなし。
