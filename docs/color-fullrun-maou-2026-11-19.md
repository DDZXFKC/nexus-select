# 色分解保存：Shoe Palace全件自動分解と2タブ反映（魔王ちゃん実行報告）2026-11-19

GPT phase2検収（c51beeec）の条件を反映して実施。対象はShoe Palaceのみ、全11,777商品。生成物はすべて候補（DRAFT／UNKNOWN／CONFLICTを含む）で、確定扱い・本番UI反映・BUYMA出品はしていない。原本・既存商品マスター・価格・Woo本番は変更なし。

## 先行訂正（GPT条件の反映）
- Phantom：カラーマスターでBRAND／NIKE範囲に変更し、familyはUNKNOWN（#E7E2D9は表示用近似値として保持し、系統の根拠にしない）。Burrow行の検索familyからgreyを除外。
- Jason Markk Essential Kit：各ステータスをNOT_APPLICABLEからUNKNOWNへ変更。
- **事実訂正**：同商品についてphase2報告で「MAIN_COLOR_BLACKタグだけが存在」と書いたのは誤り。rawにはColor_Blackタグも存在する（表示フィルタの見落とし）。fixture行のstore_color_tags_jsonを ["Color_Black"] に訂正済み。生成候補では店タグから主色blackが立つが、シートの見本行はGPT指示どおりUNKNOWNのまま保持した。この扱いの最終判断はGPT検収に委ねる。

## 処理方法
- 入力：v8出力 products.csv（color_name／color_name_status／brand／source_url／in_stock）＋収集済みraw（Color_／MAIN_COLOR_／STYLE_タグ）。
- 分解：color_nameを「/」でのみ分割（ハイフン・空白・andは分割しない）。順序と重複を保持。トークン正規化はNFKC＋casefold＋空白正規化。
- 照合：既存カラーマスター13トークンは自動上書きせずそのまま使用。新規トークンは既存パレット（EXACT 86＋BASIC 25）と基本色単語からfamily候補を付け、根拠がないものはUNKNOWN。パレット採用の新規HEXはすべてDRAFT（APPROVED_APPROXにしない）。
- TITLE_CANDIDATE 1,024件はGPT指示（c4aac99c）によりCONFIRMED_BY_TITLE_RULEとして処理（colorway_statusの内訳に反映）。

## 結果の内訳
- 入力 11,777商品 → 生成 11,777行。既存の見本9商品は同じキーで保持し重複追加なし。新規追加 11,768行。
- カラーマスター：既存13＋新規1,656＝1,669トークン。新規の内訳はCOMMON 1,068／BRAND 588、family状態はCONFIRMED 19／DRAFT 878／UNKNOWN 759、HEXはDRAFT 56／UNKNOWN 1,600。
- 構成色数の分布：0色 21／1色 3,028／2色 5,825／3色 2,054／4色 796／5色 43／6色 10。
- component_status：CONFIRMED 6,798／PARTIAL 4,956／UNKNOWN 23。
- main_family_status：TAG_SUPPORTED 1,500／CONFIRMED 1,644／DRAFT 1,482／UNKNOWN 6,979／CONFLICT 172。
- BUYMA状態：DRAFT_MAIN_FAMILY 4,409／DRAFT_MULTI_CANDIDATE 6,438／HOLD_CONFLICT 172／UNKNOWN 758。公式colors.csvの照合は未実施のため、IDはすべて空欄で確定扱いにしていない。
- swatch状態：CONFIRMED 6,827／DRAFT 4,929／UNKNOWN 21。
- タグ付与：両方あり 1,677／Colorのみ 9,995／MAINのみ 53／両方なし 52。

## 176件の不一致の再分類
- 粗分類差（タグ集合に主色はないが色名の系統と主色タグが整合）4件。
- 真の矛盾候補（主色タグがColor集合・色名系統のどちらとも一致しない）172件 → 主色CONFLICT・BUYMA HOLDで保留し、分解自体は保持。内訳は同梱の reclass_inconsistency.csv。
- MAINのみ53件とNOCOLOR 1件（商品7255562977486）は上記とは別分類で集計した。

## 負テスト（実データで確認）
- Multiトークンを含む商品 66件（色コードは付けていない）。
- NOCOLOR 1件。MAINのみ 53件。未知HEXを含む商品 4,651件（該当スロットは空欄にし、繰り上げをしていない）。
- 同名トークンの異ブランド出現 346トークン（COMMON／BRANDのscope分離で対応。例：white は80超のブランドに出現しCOMMONのまま）。
- 解析不能（色名なし）21件はUNKNOWNで理由を備考に記録。

## 検証
- 同一入力で生成を2回実行し、出力ハッシュが一致（d140ee9f…）。
- シート読み戻し：商品カラー 11,778行（見出し＋11,777商品）、商品IDの重複0件。カラーマスター 1,670行（見出し＋1,669トークン）。抜き取り照合（行5,000・最終行）で生成CSVと一致。
- 既存の手動確定（見本9行・既存13トークン）は、GPT指示の訂正（Phantom／Jason Markk／Jasonのタグ訂正）を除き変更していない。

## 同梱ファイル
- docs/color-fullrun-unresolved-tokens-2026-11-19.csv（未解決・下書きトークン1,662件。family UNKNOWN 760／DRAFT 883／残りはHEX未承認の基本色。件数・在庫あり件数順）
- docs/color-fullrun-reclass-2026-11-19.csv（不一致176件の再分類）
- docs/color-fullrun-master-new-2026-11-19.csv（新規マスター1,656トークン）
- 全商品の生成CSV（7.6MB）はVMの ~/workspace/color-fullrun-2026-11-19/product_color_full.csv に保持。生成スクリプトも同フォルダ。

## 残件
- 未解決トークンの解決作業（family UNKNOWN 760トークンが本丸。件数の多い順に確認し、1語の解決を関連商品へ再計算する工程が次）。
- BUYMA公式colors.csvの取得と系統ID照合（未実施・保留のまま）。
- 画像描画の独立証拠は次回登録（GPTの次回報告指定どおり）。
