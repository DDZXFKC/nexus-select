# 辞書一括解決の実行結果と検収依頼（魔王ちゃん、2026-11-19）

GPT実装 collector/color_dictionary_resolver.py を実シートの現行マスター（active 1,669色）で実行した。テスト6件合格。辞書は固定コミット 4e9d724b の実物を取得し、キャッシュにハッシュ付きで保存した（colornames.csv 708,053 bytes）。照合は token_normalized で実施。

## 未解決815色の内訳（候補の方法別）

- DICTIONARY_EXACT 309色（辞書完全一致・HEX一意）
- BASIC_WORD 47色（基本色語が1つだけ）
- APPROVED22 19色（GPT承認22色のうち完全一致トークンが存在したもの。graphite／lime／mustard は完全一致トークン自体が存在しない）
- EXISTING 29色（DRAFTの下書きHEXをそのまま候補にしたもの。承認判断は別）
- AMBIGUOUS_BASIC 8色（基本色語が複数競合）
- SPECIAL 6色（multi系・単色HEXなし。利用頻度は最上位：multi 66件・multicolor 62件・multi color 37件・multi-color 17件）
- UNKNOWN 397色（辞書・基本色語とも一致なし）
- DICTIONARY_CONFLICT は0件だった

## APPROVED22による上書き（辞書・既存値との競合）

承認22色を辞書候補より優先した。辞書値が不適切だった代表例：

- navy blue：辞書 #000080 → 承認 #172B4D
- mint：辞書 #3EB489 → 承認 #A9D5BD
- lavender：辞書 #B56EDC → 承認 #B8A5D2
- lilac：辞書 #CEA2FD → 承認 #C4ADD5
- chestnut brown：辞書 #6D1008 → 承認 #996845（chestnut単体は承認済み #996845 と一致）
- turquoise：辞書 #06C2AC → 承認 #49A9AD
- coral：辞書 #FF7F50 → 承認 #E77D70
- indigo：辞書 #4B0082 → 承認 #34466E
- taupe：辞書 #B9A281 → 承認 #8B7D70

パレットJSONと承認22色の値が異なる7色（infrared 23／palomino／burgundy／maroon／tan／teal／lime）は、今回パレット完全一致のヒットが未解決側で0件だったため影響なし。

## Claude監査への対応：利用頻度の高いDICTIONARY_EXACT（目視確認用）

- sesame #BAA38B（構成色参照 25 件）
- muslin #D3D1C4（構成色参照 18 件）
- flax #EEDC82（構成色参照 17 件）
- hemp #987D73（構成色参照 17 件）
- linen #FAF0E6（構成色参照 17 件）
- starfish #E5BCA5（構成色参照 16 件）
- pearl #EAE0C8（構成色参照 15 件）
- pine #2B5D34（構成色参照 15 件）
- alabaster #F3E7DB（構成色参照 13 件）
- eclipse #3F3939（構成色参照 13 件）
- ice #D6FFFA（構成色参照 13 件）
- blue grey #758DA3（構成色参照 12 件）
- frost #E1E4C5（構成色参照 11 件）
- malachite #0BDA51（構成色参照 11 件）
- glacier #78B1BF（構成色参照 11 件）

## 商品単位dry-run（color_fullrun recompute、整合性問題0・再実行一致）

- 案A（辞書309＋基本色語47＋承認22の19＝375色を承認）：CONFIRMED 10,552／DRAFT 113／UNKNOWN 1,109／HOLD 3（確定率89.6%）
- 案B（案A＋DRAFT 29色を下書きHEXのまま承認＝404色）：CONFIRMED 10,665／DRAFT 0／UNKNOWN 1,109／HOLD 3（確定率90.6%）

## 残り411色について

UNKNOWN 397＋AMBIGUOUS 8＋SPECIAL 6。GPT実装文書の指示どおり、次は店タグ（Color_／MAIN_COLOR_）の単一・一意対応での自動処理を検討する。画像目視はしない。

## 検収依頼

1. 案Aの375色を一括承認してよいか。
2. 案BのDRAFT 29色の下書きHEX承認を案Aに含めるか、別途にするか。
3. 上記のDICTIONARY_EXACT上位色に、承認できない色があれば指摘してほしい。

候補全件は docs/color-dictionary-candidates-maou-2026-11-19.csv（815行、利用頻度順）。
