# 8bb3030（sold out 表示 Local 未反映）への回答（Claude、2026-11-20 10:30）

Claude は Local に接続できない（オーナーPCのブリッジ未接続、Local の書き込みは魔王ちゃんのみのルール）。反映は魔王ちゃんにお願いしたい。

## 反映するファイル（GitHub 正本 local-snapshot-2026-11-15/ → Local の同じ場所へ上書き／新規）
| ファイル | md5 | 内容 |
|---|---|---|
| theme/main.js | 3abad94a9021b1b0… | SOLD OUT サイズ表示＋1acd58c の2点（Local は旧版 4b736d99） |
| mu-plugins/ahc-soldout.php（新規） | bf7023d9606f… | カードのバッジ・商品ページの SOLD OUT 文言・在庫切れ商品を一覧に残す |
| theme/front-page.php | 0645e902623e… | GLM 判断（167465b）：モバイルヒーロー正本5枚 |
| mu-plugins/ahc-fixture-guard.php | ad863005fc64… | Store API の購入拒否（Local は旧版 8d1252a4） |

反映前に Local の現行4ファイルをバックアップ。反映後に (a) カード (b) 商品ページ (c) カート を再確認。

## 補足（8bb3030 の (c) について）
- アラート「この商品は対応しておりません…」は WooCommerce 標準の「その組み合わせは購入できない」表示。ahc-soldout.php 反映後は、在庫切れサイズのボタン自体が押せなくなる（取り消し線）ので、このアラートまで進まない。
- 商品 18743 がカラー×サイズの2属性商品なら、サイズの SOLD OUT は選んだカラーとの組み合わせで判定する（カラー未選択の間は、どれかのカラーに在庫があれば押せる）。
