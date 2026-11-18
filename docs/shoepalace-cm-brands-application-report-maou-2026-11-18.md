# Shoe Palace cm：追加ブランド公式表の収録と適用結果（魔王ちゃん、2026-11-18）

統合参照 v3（592行、衝突0）で2回実行し、出力は完全一致。コード変更なし。

## 今回収録した公式表（全てJP/CMラベル値）

- PUMA：PUMA公式サイズガイド（vn.puma.com、JPN/CM列）を直接開いて確認。Men／Women／Kids（US表記をC／Y表記へ対応付け）。
- Crocs：crocs.comのサイズチャートのJP列（Men US+18、Women US+16）。キッズC11〜C13とJ1〜J6のJP値はLEGO公式ショップのCrocsサイズガイドでも同値を確認。キッズのJは当店表記のYへ対応付け。
- Salomon：Salomon公式サイズチャート（salomon.com）のJP列。Men／Women。キッズ表は公式に存在しない。
- New Balance Kids：ニューバランスジャパン公式サイズチャート（outlet.newbalance.jp/guide-sizechart.html）を直接開いて確認。公式表の飛び（6C、12.5C、2.5Y、6Y等は公式表に無い）はそのまま空欄にした。成人Men 4／4.5、Women 4／4.5も同ページから補った。

## 結果

- 汎用適用 v3 の cm MATCHED：65,174
- 製品単位参照との合算 MATCHED：65,611
- cm MISSING は 76,841 → 11,826（約85%解消）。issues は 25,097。

## 残り MISSING 11,826 の主な内訳と扱い

- Adidas Kids 2,073：公式キッズ表にJPラベル値なし（足長のみ）。JP/CM値を使うルールのため埋めない。
- Converse Men 969／Kids 208：公式cmは足長で日本の表示とずれる。かつ当店ではUSコンバースは取り扱い対象外。
- HOKA Men 903／Women 549、UGG Kids 240：モデル差の実例があるため製品単位参照の側で扱う。
- Saucony Men 873：JPラベル値の公式チャートが見つからなかった（公式US表は足長のみ、店舗掲載の換算表は公式ではないため使わない）。未収録として残す。
- Vans Men 578／Kids 221：収録済み公式表の範囲外（Men 6.5未満と12.5等のハーフ、Kids 10C以下のトドラー範囲）。
- その他は Reebok 348、Birkenstock Women 249、Champion Kids 216、Anta Men 212、Veja Women 209等のロングテールで、公式表を収録できれば同じ方式で適用できる。
