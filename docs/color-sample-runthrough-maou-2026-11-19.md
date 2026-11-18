# 色分解保存：既存資産の照合と1商品の見本データ作成（魔王ちゃん実行報告）2026-11-19

対象設計：GPT確定設計 docs/color-components-sheet-design-gpt-2026-11-19.md（70ee0596）の実行順1。
今回は既存シート・rawタグ・既存パレットの照合と、1商品の見本データを2表の形で作成し、丸窓レンダリングとBUYMA下書きまで通した。実シートへのタブ作成・書き込みはまだ行っていない（GPT検収後に実施する）。

## 1. 既存シートの確認（商品管理ブック 1JdQnCxqS5gqrX6-4hcJBGEx_qFCuJsufUjedbkWnJsg）
タブ：サイズ別在庫／収集履歴／商品マスター（3,205行・34列）／収集サマリー／リサーチ商品／クーポン管理／Notre収集／Converse収集。
カラーマスター・商品カラーに相当するタブは無い。2表は新規作成になる。
商品マスターの色関連列は「カラー」（11列目、原文の色名）と「カラーコード」（25列目、例 GRN＝店舗の色コードでHEXではない）。分解・構成色の構造は無い。

## 2. Shoe Palace rawタグの照合（収集済みraw 48ファイル・11,777商品）
- Color_タグ：11,672商品（99.1%）に付与。値は13種のみ（Black 5,701／White 4,814／Red 1,789／Blue 1,787／Grey 1,785／Beige 1,501／Brown 1,159／Green 1,016／Pink 959／Yellow 577／Orange 383／Purple 334／Multi 184）。2色以上は8,237商品。
- MAIN_COLOR_タグ：1,730商品（14.7%）。値は13種（BLACK／WHITE／BLUE／BEIGE／BROWN／GREEN／RED／PINK／GREY／PURPLE／YELLOW／ORANGE／NOCOLOR 1件）。
- 複数のMAIN_COLOR_を持つ商品は0件。
- 真の矛盾は176件（大文字小文字を正規化してもMAIN_COLOR_がColor_集合に含まれない）。例：#4 French Fried Trucker（MAIN=WHITE、Color=RED/YELLOW）。設計どおり自動で解消せずCONFLICTとして保留する対象。
- どちらのタグも無い商品は52件。

## 3. 既存パレットの照合（theme/main.js）
EXACT_COLORS 86語＋BASIC_COLORS 25語＝111語。設計どおり近似候補として再利用し、公式HEXとしては扱わない。例：black #171717／navy #172B4D／gold #C6A34A。

## 4. 見本データ（1商品を通した結果）
商品：Nike Air Vapormax Plus Mens Running Shoes、supplier_product_id 7357135290574、style 924453-405、colorway原文「Midnight Navy/Metallic Gold/Black」。Shoe Palaceは色ごとに別商品IDのため supplier_color_key は single。
店タグ：Color_Black／Color_Blue／Color_Yellow、MAIN_COLOR_BLUE。

カラーマスター側（3トークン）：
- black（COMMON、既存）：ブラック／family black／#171717（APPROVED_APPROX）／BUYMA系統 ブラック
- midnight navy（新規）：ミッドナイトネイビー／family blue／#172B4D（DRAFT、navyの値を候補流用）／BUYMA系統 ブルー
- metallic gold（新規）：メタリックゴールド／family gold／#C6A34A（DRAFT、goldの値を候補流用）／BUYMA系統 ゴールド。店タグではYellowに分類される差異を備考に記録。

商品カラー側：components_json は原文順に [Midnight Navy, Metallic Gold, Black]（position 1〜3）。component_status は PARTIAL（2トークンが下書きのため）。main_family_internal は blue（出典 STORE_MAIN_TAG、TAG_SUPPORTED。構成色1のfamilyと整合）。派生 swatch_hex_1/2/3 = #172B4D／#C6A34A／#171717（swatch_status DRAFT）。BUYMA下書きは系統ブルー（公式IDは未確認のため空欄）、色名は原文全文を渡す前提。

丸窓レンダリング：派生HEXから3色・縦等分で描画し、オーナー承認済みの表示仕様（最大3色・縦等分・色名順）どおり表示できることを確認した。成果物はVMの ~/workspace/color-sample-2026-11-19/（color_master_sample.csv、product_color_sample.csv、sample_runthrough.png）。

## 5. 次の段階と未確認事項
- 少数fixture（単色・2色・4色以上・重複色・ブランド固有色・タグなし52件・矛盾176件・色名なし）を同じ形で通す。
- BUYMA公式colors.csvの取得と系統IDの照合（現時点では名称レベルのみ、IDは推測しない）。
- 未解決トークンの集約表（ブランド・適用範囲単位、件数順）を作り、共通トークンから確定していく。
- 実シートへの2タブ作成と見本行の投入は、本報告のGPT検収後に行う。
