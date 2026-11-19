# 丸窓Local確認の実行結果（魔王ちゃん、2026-11-19）

Claude 420a82c5（docs/swatch-local-check-claude-2026-11-19.md）の確認仕様を、GPT再配置に基づき魔王ちゃんがiMacのLocalで先行実施した結果。**結論：指定の手順では確認を実行できない。前提がLocalの実態と2点で食い違っているためで、書き込みは1件も発生していない（--apply は未実施、Localは無変更）。**

## 実施したこと

1. 最新シートを取り直した（2026-11-19 13:19、カラーマスター1,673行／商品カラー11,778行）。
2. collector/color_woo_export.py で書き出し。再計算とシートの swatch_status の不一致0件で通過。分布は CONFIRMED 10,621／UNKNOWN 1,153／HOLD 3／構成なし21（全11,777商品、出力24,320行）。
3. tools/ahc_color_components_to_woo.php をLocalで dry-run（--only-confirmed なし）。

## dry-run の結果（全11,777商品）

- not_found: 11,619
- color_value_unclear: 158
- would_write: 0、shown_fully_colored: 0、shown_unconfirmed: 0、bad_group: 0、row_errors: 0

## 実態調査（wp eval-file のプローブ、619商品全数）

- Localの商品は619点（公開355／下書き264、全て variable）。うち SP- のSKUは158点のみ。確認用9商品は9点とも Local に存在しない（not_found）。
- **SP商品158点は全点、pa_color 属性を持っていない**（has=0 が158/158）。色は商品タイトル末尾の「(Black)」等にだけある。書き込みツールが要求する「色のバリエーション値がちょうど1つ」という条件を満たすSP商品は0点で、158点全てが color_value_unclear になった理由はこれ。
- pa_color をバリエーション属性として持つのは MERGED- 58点と PROTO- 2点だけ（いずれも色の値は2〜33個）。FL（345点）・CV（26点）等も pa_color なし。
- メタ `_ahc_color_components` を持つ商品は **0点**。現行の色詳細メタ `_nexus_color_details` は54点。
- Localのテーマ（nexus-select の main.js 全631行・functions.php）と mu-plugins・plugins を確認した範囲では、**`_ahc_color_components` を読む描画側コードは存在しない**。現在の丸窓は、pa_color のセレクトを対象に「その色の商品画像の切り抜き（無ければ色名パレット）」で描く現行実装（オーナー決定のB案系統）で動いている。GitHub側の main.js（11,203バイト）にも同メタの読み取りはない。

## 食い違いの整理（設計側で判断が要る点）

1. 書き込みツールの前提「SP商品は pa_color の値を1つ持つ」が、LocalへのSP取り込み実態（色属性なし、タイトルにのみ色名）と合っていない。取り込み側で pa_color を付けるのか、書き込みツールの突合方法を変えるのかの判断が要る。
2. GPT設計 70ee0596 の「テーマが _ahc_color_components を縦縞で描画する」は Local 未実装。テーマ変更か mu-plugin で読むのか、現行の画像切り抜き方式（B案）とどう併存・置換するのかの判断が要る。
3. Claude仕様の「Localに無ければ同じ観点の別商品を選び直す」は、SP商品の全点が条件を満たさないため今回は使えない。

## 証拠ファイル

- iMac ~/ahc-swatch-check/：dryrun.log（全行）、probe.log、probe2.log、probe3.log、woo_components.csv、使用スクリプト一式
- VM ~/workspace/swatch-local-check/：master_now.csv、products_now.csv、out/woo_components.csv、checkpoint.md

担当割り振り上、設計の修正は Claude（サイト）と GPT（技術統括）にお願いしたい。魔王ちゃんは修正版の手順が決まれば、Localでの再実行と実画面確認をすぐ行う。
