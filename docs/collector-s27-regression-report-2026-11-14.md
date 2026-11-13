# §27 回帰突き合わせ報告（d9e66fb0 のレビュー要件への回答）

実行：魔王ちゃん（iMac）。ライブリクエストなし。公開・インポート0。

## 突き合わせ方法
- §26の隔離パッケージ `/Users/discodadz/nexus-run/pkg_bstn_probe_20261113`（182件を出した環境、`.venv-cat` 使用）を新規隔離コピー `pkg-s27-recon` へ複製（venv本体は元のものを実行に使用）。
- overlay は GitHub 最新の2ファイルのみ：`stage3_persistent_discovery.py`、`test_stage3_persistent_discovery.py`。
- overlay の SHA-256：
  - stage3_persistent_discovery.py: `657ae7b8bbe79b6decd622d993b3901f5d1f623d8f6d1d896c48e8d553089d2f`
  - test_stage3_persistent_discovery.py: `d3de0924e6f094e19f15c098fc7ef74dc070881fe461e2c312844ba2875714ec`

## テストID集合の比較
- 元パッケージのテストID：**182件**（unittest loader で列挙）。
- overlay 後：**192件**。
- 元の182件で欠けたもの：**0件**。
- 追加されたもの：**10件**（すべて test_stage3_persistent_discovery の新規テスト）。

## 全体実行結果
- `python -m unittest discover`：**192件すべて合格**（4.0秒）。
- 前回報告（431c6c67）の128件は、GitHub の local-pkg だけから組み立てた環境の数であり、iMac ローカルの蓄積モジュールを含んでいなかったことが原因と確定した。コード側の欠陥ではない。

## ステップ2ドライバ（同環境で再実行）
14項目すべて合格（同一raw＋同一時刻の再生で capture 1件・バイト完全一致・SHA一致、台帳OK後の再開で再取得なし、失敗時の自動リトライなし、未解決台帳で後続停止、catalog_complete は常に False、published=0）。

## 詳細キューの実完了（明示確認）
§26成果物 `s25-trial-001/report.json` の実測値：
- queue：DONE 5件、complete=true
- 詳細行：40件（Woo 行 45＝親5＋バリエーション40、BUYMA 行 5）
- structural_validation：PASS
- verification.json の判定は全件 HOLD（stock=UNKNOWN、権利=UNKNOWN、欠損項目を保持）
- published=0、approved_for_import=false、actual_import=NOT_RUN、catalog_complete=false、coverage=PARTIAL

## 実用データの先行提供（オーナー指示）
§26の候補データは、オーナーの内部仕入れ検討用として先行提供済み：候補URL 192件（商品187＋リリース5、全件 UNVERIFIED_HOLD）のCSVと、処理済み5商品／40バリエーションのレビューCSV。在庫・原価の検証済み主張は含まない。公開・インポートはしていない。

## 次
runbook ステップ3（ライブパイロット、cap 10、最大9リクエスト）の実施可否はチャッピーのゲートレビュー待ち。実施には `bstn-category-s27.json`（§26の承認済み単一シードと同内容、reviewed_at を当日に更新）と、BSTN 規約・robots の当日再確認が必要。
