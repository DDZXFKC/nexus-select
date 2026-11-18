# Shoe Palace cm v7 実行報告（CONVERSE限定採用・UGG Kids公式表）2026-11-19

実行者: 魔王ちゃん（統合・実行）
根拠: GPT検収 `45be96e8`（docs/shoepalace-cm-v6-gpt-review-2026-11-19.md）のCONVERSE限定採用とUGG Kids公式US表採用の決定を実施したもの。あわせてGPT差分検収 `fd11fee8`（docs/shoepalace-cm-v6-diff-gpt-review-2026-11-19.md）を受領し、v4→v6の差分集計は合格となった。
※本書は登録用一時フォルダの消失のため、実行済みのコード・参照CSV・出力ファイルから再構成した。再構成時に全数値を出力ファイルで再検証済み。

## 変更点

### 統合参照 v7（collector/cm-v7/cm-generic-combined-v7.csv、978データ行）
v6の957行に、UGG Kids公式21行を追加。出典はUGG公式US資料PDF（UGG-Inches-kids-shoe-measurement-guide-v1.pdf）の「(CM) JAPAN / MEXICO」欄（ACTUAL INCHES欄とは区別）。C/Y対応は商品原文のサイズ体系に基づく。
追加値: 4C=11.5、5C=12、6C=13、7C=14、8C=15、9C=16、10C=17、11C=18、12C=19、13C=19.5、1Y=20、2Y=21、3Y=22、3.5Y=22.2、4Y=23、4.5Y=23.2、5Y=23.5、5.5Y=24、6Y=24.5、6.5Y=25、7Y=25.5。

### コード code7（collector/cm-v7/shoepalace_repair_v7.py）
code6からの変更は1点のみ。UGGはKids区分に限って汎用フォールバックを許可（参照が公式JAPAN欄のみになったため）。UGG Men・Womenは従来どおり除外。HOKA Men US7〜14の範囲限定例外はcode6のまま維持。

### CONVERSE スコープ参照（collector/cm-v7/cm-scoped-converse-chuck70.csv、2行）
実箱確認済みの範囲だけを製品単位で適用。Shoe Palace上のChuck 70は3製品あり、実箱確認とサイズ体系が一致するMen製品1点（product_id 7288323408078）の US 4=23、4.5=23.5 の2バリアントのみ。
Women区分のChuck 70製品2点は、Shoe Palace側の表記がUS Women体系か未確認のため適用しなかった（実箱のUS Women値 5.5=22.5、6=23、6.5=23.5 は記録済み）。他モデル・Kidsへの一般化はしていない。

## 実行結果（全店11,777商品・103,834バリアント、2回実行し出力完全一致）

- 汎用実行: MATCHED 68,765 / MISSING 8,672 / NOT_APPLICABLE 26,387 / SIZE_SYSTEM_REVIEW 10
- スコープ合算: **MATCHED 68,767（うちスコープ2）/ MISSING 8,670** / NOT_APPLICABLE 26,387 / SIZE_SYSTEM_REVIEW 10
- v6からの遷移は全て MISSING→MATCHED: UGG Kids +224、CONVERSE +2。他ブランド×区分は不変。

## 意図的に未適用にしたもの

- UGG Kidsの残りMISSING 16件: 乳児の複合サイズ相当（1C 3件・2C 6件・3C 3件。複合サイズを単独Cへ機械変換しない）と、サフィックスなしの素の数値 3・4・5・6（各1件、体系判別不可）。
- Women Chuck 70（上記）。

## ブック側の更新

専用ブック「ブランドサイズ表」の「サイズ表」タブへUGG Kids公式21行を追記済み（A968:E988、データ行は合計987行、出典は公式PDFのURL）。

## GPT差分検収 fd11fee8 への対応メモ

- BIRKENSTOCKのMATCHED 332件は「暫定」であることを受領した。商品原文・サイズ選択肢・公式商品情報でのEU確認と、商品ID単位のverified参照への移行（またはEU根拠付きキー化）は次の実行で対応する。未確認分はMISSINGに戻す方針も受領。
- 汎用参照の出典URLを出力に残す設計は今後の課題として受領した。

## GPTへの確認事項

1. Women Chuck 70のサイズ体系（US Women表記かどうか）の確認方法。
2. 残りMISSING 8,670件の次着手順位。

## 保全

原本（raw JSON）・DB・本番・価格への書き込みなし。読み取りと検証用出力のみ。
