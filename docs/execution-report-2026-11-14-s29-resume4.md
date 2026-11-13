# 実行報告 2026-11-14：§29 収集バッチ resume4（改訂版コードでの初回本番実行）

実行者：魔王ちゃん（Muse）。実行環境：iMac、パッケージ pkg-s27-recon。コードは改訂版 695d9dc7（stage3_catalog.py MD5 645cd1e49c224ad962b913b329f59b64、本番反映済み・バックアップ取得済み）。

## バッチ結果（全カテゴリー exit=0）

| カテゴリー | DONE（今回+100） | PENDING | rows | published |
|---|---|---|---|---|
| Women Footwear | 410 | 1,831 | 4,753 | 0 |
| Men Apparel | 410 | 7,038 | 1,932 | 0 |
| Men Footwear | 200 | 3,023 | 2,402 | 0 |

- 開始前ゲート：test_stage3_catalog 9件合格
- 全カテゴリー approved_for_import=false、complete=false（継続中）
- Kids Footwear は全件完了済み（DONE 249/249、rows 1,970）のまま

## exports r4（レビューCSV再生成）

export_partial.py で3カテゴリー分を再生成し、sourcing-usable へレビュー用コピーを保存した。

| カテゴリー | rows | woo行数 | buyma行数 |
|---|---|---|---|
| Women Footwear | 4,753 | 5,163 | 410 |
| Men Apparel | 1,932 | 2,342 | 410 |
| Men Footwear | 2,402 | 2,602 | 200 |

## 次

- §29 は同方式で +100 バッチを継続（Women 残1,831 / Men Apparel 残7,038 / Men Footwear 残3,023）
- BSTN ライブパイロットの結果は docs/expansion-bridge-execution.md の追記を参照
