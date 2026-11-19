# 丸窓のWoo接続テスト準備（Claude、2026-11-19 11:20）

対象：魔王ちゃん登録のシート現行スナップショット（a87e6d2・bca30a1・781db30・0762867）。

## 見つけた不具合（直した）
- 書き込みツール tools/ahc_color_components_to_woo.php は shop_code「shoe-palace」しか受け付けていなかった。シートは「SP」のため、そのまま実行すると全行スキップで何も書けなかった。→「SP」を受け付けるよう修正（旧表記も可）。
- 書き込みツールは構成色1行ずつのCSVを読むが、シートは商品1行＋components_json。→ 変換スクリプト collector/color_woo_export.py を追加。

## 変換の規則
- 丸窓の状態は color_fullrun.swatch() で再計算し、シートの swatch_status と1件でも違えば停止。
- HEXを出すのは、状態がCONFIRMED/DRAFTで、構成色の参照に問題がなく、マスターが APPROVED_APPROX の色だけ。HOLD/UNKNOWNの商品は承認済みの色でも空欄（中立表示）。

## スナップショットでの結果（オフライン）
- 11,777商品、構成色24,299行。再計算とシートの不一致0件。分布 9,632／200／1,942／3（シートと一致）。
- 先頭3色すべてに承認HEXがある商品＝9,632（すべてCONFIRMED）。--only-confirmed で切り替わるのはこの9,632商品。
- 構成色が空の21商品（UNKNOWN）は出力に含まれず、Woo側は現状のまま。
- テスト：変換4件追加。色分解47件と合わせて全件成功。

## Local での実行手順（魔王ちゃん）
1. python3 collector/color_woo_export.py --master <マスターCSV> --products <商品CSV part1..3> --output <出力先>
2. wp eval-file tools/ahc_color_components_to_woo.php <出力先>/woo_components.csv --only-confirmed --path="<Local>/app/public"（dry-run。not_found と color_value_unclear の件数を確認）
3. 問題なければ同じコマンドに --apply。本番には使わない。

## 追記（12:45、69013b6 の「旧表示残存を防ぐ」に対応）
- 「確定のみ」で書くと、未確定・HOLD・構成なしの商品は旧来の丸窓（写真切り抜き／色名推定）が残る。→ 既定では全商品を書く方式に変更。
  - 未確定・HOLD：HEXなし → 中立表示（白地・点線）。
  - 構成色なし：変換で position 0 の目印行を出し、書き込みツールが空リストを保存 → 中立表示。
- 書き込みツールのオフライン検証 qa/php-tests/woo_writer_stub_test.php（WordPressなしの差し替え関数で実行）：確定=縦縞、未確定=HEXなし、構成なし=空リスト、未登録SKU=NOT FOUND、すべて合格。
- 手順の変更：手順2・3は --only-confirmed を付けない。スナップショットは最新のシート（確定10,621の版）から取り直す（9:09登録の版は古い）。
- dry-run で見る数字：not_found（シートにあるがLocalに無い商品）、color_value_unclear（色が複数・不明）、shown_unconfirmed（中立表示になる件数＝未確定＋HOLD＋構成なしの合計と一致するはず）。
