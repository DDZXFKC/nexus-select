# §27 実行報告（ステップ1＋2：オフラインゲート）

実行：魔王ちゃん（iMac）。対象コミット：b07fcbbf（実装）、ebfcc0c5（応答の先行保存）、a12bad82（回帰テスト）、a309c417／d36348bc（runbook `docs/collector-persistent-discovery-runbook-2026-11-14.md`）。
ライブリクエストは未実施。公開・インポートは0。

## 環境
- 新規隔離ディレクトリ `/Users/discodadz/nexus-run/pkg-s27` を使用（既存pkgとは分離、新規DBのみ）。
- Python は `/usr/bin/python3` 3.9.6（既存ステージと同じ。想定パスに venv は存在しなかった）。
- パッケージ構成の注記：`research/online/local-pkg` の33ファイルだけでは import が完結しなかったため、同ブランチ `research/online/` 直下のモジュール（shopify_variants.py、collector.py、fetch_and_store.py、verify_six_pages.py とそのテスト3件）を追加した。テスト用フィクスチャ `input_pages_multi/` と `input_pages/` は GitHub に存在しないため、旧iMac pkg からコピーした（コード変更は一切していない）。

## ステップ1結果
- `python -m py_compile stage3_persistent_discovery.py test_stage3_persistent_discovery.py`：OK。
- 対象テスト `python -m unittest -v test_stage3_persistent_discovery`：**10件すべて合格**（runbookの想定どおり）。
- 全体 `python -m unittest discover`：**128件すべて合格**。
- 想定との差異（要確認）：runbookの想定は「baseline 182 + 10 = 192」だが、GitHub上のパッケージから組み立てた環境では discover は128件だった。182という数字には、リポジトリのパッケージに含まれていない iMac ローカル側のテストモジュール（test_batch_import、test_live_fetch、test_online_workflow、test_pipeline、test_readiness、test_merchant_evidence、test_bstn_review_export 等）が含まれていたとみられる。取得したパッケージの範囲では失敗は0件。ベースラインの数え直しが要るかどうかはチャッピーの判断を待つ。

## ステップ2結果（オフライン統合チェック）
実行ハーネス `s27_step2_driver.py`（パッケージ本体は無変更）で14項目すべて合格：
- 同一 raw＋同一タイムスタンプの2回再生：capture は1件のみ、キーは同一、保存された raw はバイト完全一致、SHA-256 一致（26432526291e092b…）。
- 台帳 OK（raw保存済み）の直後で落ちた想定：保存済みバイトから再開し、ネットワーク再取得なし（Fetch.read 呼び出し0回）、台帳への追加記録なし、候補95件・capture 1件で復旧。
- 失敗時：自動リトライなし（read 呼び出しは1回のみ）、台帳に FAILED が残り、未解決の台帳がある間は後続取得が止まる。
- 全経路で `catalog_complete` は False のまま、`published=0`、`approved_for_import=False`。

## 次
ステップ3（ライブパイロット）は runbook の条件どおり、チャッピーの相互レビューとオフラインゲート合格の確認が済んでから。あわせて BSTN の規約・robots の再確認と `bstn-category-s27.json` の用意が必要（現パッケージには同 config は含まれていなかった）。
