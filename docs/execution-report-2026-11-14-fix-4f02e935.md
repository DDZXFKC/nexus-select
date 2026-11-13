# 検証報告 2026-11-14: 修正コミット 4f02e935（stage3_catalog.py）の実機検証

実行者: 魔王ちゃん（Muse）／ 環境: iMac、pkg-s27-recon、venv python

## 結論: 不合格（回帰1件）。パッケージは旧版へ復元済み

## 手順と結果
1. 旧 `stage3_catalog.py`（MD5 b96ed74576e3df22be72be64bc1b23e8）をバックアップ（`stage3_catalog.py.bak-pre4f02e935`）
2. 新版（MD5 19825e8d68ef48c91b75afac42a97216 = コミット 4f02e935 の内容）を投入、py_compile 合格
3. パッケージ全体の回帰テスト 29ファイル・199件を実行 → **198件合格、1件失敗**

## 失敗の詳細
- `test_stage3_catalog.py`（7件中1件失敗）: **test_stop**
- 内容: `process(c, 'a', lambda u: b'bad', extract, 1)` が ValueError を送出することを期待するが、新版では送出されなかった（AssertionError: ValueError not raised）
- 旧版ベースライン: 同テスト 7/7 合格（同条件で再実行して確認済み）
- 他の28ファイルは新版でも全件合格

## 実行側の解釈
今回の修正（個別商品の解析エラーを ERROR 記録して継続）が、test_stop が「全体が読めない応答では停止すべき」とするケースまで継続扱いにしてしまった可能性が高い。商品詳細レベルの解析エラー（継続）と、応答全体が不正なケース（停止）の切り分けが論点。

## 実施した措置
- pkg-s27-recon の `stage3_catalog.py` は旧版へ復元済み（MD5 b96ed745…で確認）
- §29 継続バッチ（Women +100 / Men Apparel +100 / Men Footwear 初回100）は旧版コードで実行中
- 新版ファイルは iMac の `/Users/discodadz/nexus-run/stage3_catalog_new.py` に保持

## GPTへの依頼
test_stop の期待（不正応答では停止）と両立する形に切り分けを修正し、再登録してほしい。こちらは再検証する。
