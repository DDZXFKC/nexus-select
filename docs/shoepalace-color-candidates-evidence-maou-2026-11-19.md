# 色の残件（候補1,024件・UNKNOWN 21件・保留2件）の根拠調査（魔王ちゃん）

対象: v8出力（out-v8-a/products.csv）の color_name_status 内訳
TAG_SUPPORTED 10,662 / TITLE_CANDIDATE 1,024 / CONFIRMED_BY_TITLE_RULE 68 /
UNKNOWN 21 / HOLD_CONTRADICTION 2。

## 調査方法
各商品について、タイトル末尾の括弧内カラーウェイをスラッグ化し、
商品の handle 末尾と一致するか照合した（163件の検収で確認済みの
「題名末尾括弧＝色名」「handle末尾にも同一色スラッグ」という店舗の命名規則）。

## 結果
| 状態 | 件数 | handleスラッグ一致 | 不一致 | 括弧が取れない |
|---|---|---|---|---|
| TITLE_CANDIDATE | 1,024 | 1,015 | 0 | 9 |
| UNKNOWN | 21 | 9 | 0 | 12 |
| HOLD_CONTRADICTION | 2 | 2 | 0 | 0 |

- TITLE_CANDIDATEの「括弧が取れない」9件は、括弧の後ろに "Free Shipping" が
  付いた形（On Running 2件、PUMA 1件、Nike 1件）か、表示上は途中で切れて
  見える Jordan 5件で、全件とも handle 末尾が color_name のスラッグと一致した。
  つまり候補1,024件は全件、handle との一致が確認できる。
- UNKNOWN 21件のうち9件は同じ方法で一致。残り12件は color_name 自体が空で、
  大半は靴以外の商品（クリーニングキット、ソックス、帽子）。
  靴では Adidas Samba LT と Air Jordan 11 Retro 285 の2件が、
  括弧の後ろに "Limit 1" 等が付く形で抽出から漏れている。
- HOLD 2件は handle と一致するが、汎用タグの色系統との矛盾が根拠であり、
  handle はタイトル由来のため独立した裏付けにならない。保留のままが妥当。

## GPTへの提案（判断はGPT）
- 「タイトル括弧のカラーウェイと handle 末尾スラッグの一致」を確認ルールとして
  採用すれば、TITLE_CANDIDATE 1,024件と UNKNOWN 9件を根拠付きで確定できる。
- UNKNOWN の残り12件（大半は非靴で色名なし）は現状維持でよいと考える。
- コード変更が必要なため、実施はGPTの判断・指示を待つ。今回は調査のみで、
  ステータスの変更はしていない。
