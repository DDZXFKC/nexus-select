# GPT検収4・次工程（Shoe Palaceのみ）
根拠：069ade81 の実行報告4・色確認CSV・cm参照CSV。Muse実測に基づく。既存SKU照合1959行/0件、原本保護、再現性、色候補70件抽出は合格維持。
## 色
93 TAG_SUPPORTED、68 CONFIRMED_BY_TITLE_RULE、2 HOLD_CONTRADICTIONを採用する。68件は店舗原文の命名規則による確認でありブランド公式の独立確認ではない。2件の具体色は消さず保留。汎用タグとの不一致だけで公式色名が間違いとは断定しない。
a9ce54d6、182dd6df：--color-reference をrepair/reconcile両方に追加。product_id、抽出色、出典URLが原本と一致することを検査、判定と根拠を保存。現時点で実行未確認。
## cm
参照755行すべてを合格にしない。UGGのBelk掲載表（https://www.belk.com/size-charts/size-chart-ugg-koolaburra.html）をGPTが確認。大人表に掲載されるサイズと数値はCSVと一致。乳児単独・複合サイズ表は異なるためC/Yの適用範囲を商品・年齢区分で確認する必要がある。HOKA女性Clifton11は https://cl.hoka.com/p/hoka-clifton-11-mujer-black/ のJP表にUS5=21.5が掲載され、別表は22。日本公式 https://hoka-jp-api.hoka.com/clifton-11/1176573.html に22cmからの表示はあるがUS対応を確定できない。よって女性26行は保留。UGG Kids133行も保留。監査版 docs/shoepalace-cm-reference-audited-2026-11-18.csv (c8d10287) は159行のverifiedをfalseに変更、596行を維持。旧原本を保全。596行は他の参照も含むため全件の公式根拠が独立確認済みという意味ではない。Vans旧参照、HOKA男性表も適用モデル/体系を確認する。
## 次の実行
最新2ファイルで163件を再照合。前回の実行コマンドに --color-reference docs/shoepalace-color-confirmation-2026-11-18.csv --cm-reference docs/shoepalace-cm-reference-audited-2026-11-18.csv を指定（旧cm引数を置換）。1959行、元20列不変、色93/68/2、cm MATCHED 596・MISSING 1175・NOT_APPLICABLE 25 を期待値として検算する。実際の結果を記録。2回実行一致、原本ハッシュ、色証拠列、cm出典列確認。
## 次工程判断
163件で修正層の接続検証を締めることと全cmの補完完了は分ける。残るcmは同一モデル/年齢区分/サイズ体系の公式表を一度ずつ確認、既存資産に追記し再利用。HOKA残りモデル、Vans小サイズ/キッズ、UGG Kids/範囲外を順に確認。公式根拠がない行は空欄維持。根拠未確認のサイズを販売時の確定cmとして使わない。全ての調査が終わるまで別の独立処理を止めない。色とcmの保留が識別され、再実行合格後に全店バッチ11,777件の読み取り専用repairを実施し、欠落の分母を確定する。全店の価格反映や本番投入はしない。全件のcm補完を完了したと宣言しない。日本語説明は別レイヤー。画像加工なし。GPTのコード実行テストは未実施、Museの結果で検収する。オーナー操作不要。