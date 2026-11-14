# AHC sourcing gate: 検証済み引き渡し（2026-11-14）
## 実行証拠
GPTの作業環境で `python -m unittest -v test_sourcing_gate` と同等の全14テストを実行（実際のコマンドは `python -m unittest -v`）。
sourcing_gate.py の Git blob: 55951b60957fcbf4fe72a175c67c49aa9e74cede
stage2_review.py の Git blob: eb21a616ca7d778dd3e793d37987440b3f0f1211
test_sourcing_gate.py の Git blob: be1ff0d751300c0b9f6a84afa2cf79385e383490
3ファイルのローカルハッシュとGitHub blobが一致。テスト登録コミット 9a51f9c26ffb354950dc15d83e0d84c91b2d3ac6。
```
test_ask_separate ... ok
test_batch_continues ... ok
test_buyma_fallback ... ok
test_duplicate ... ok
test_expected ... ok
test_identity ... ok
test_median ... ok
test_mismatch_cost ... ok
test_missing_cost ... ok
test_missing_identity ... ok
test_negative ... ok
test_no_stock ... ok
test_positive ... ok
test_stale ... ok
Ran 14 tests in 0.003s
OK
```
## 適用範囲と限界
正規化された証拠入力を判定する独立モジュールのみ。実サイト、GLM原本、実際の出品・購入は未検証。成約相場がない商品もHOLD候補として残す。成約価格と出品価格を混同しない。入力の証拠真正性は取得側の責任。公開・本番反映は不可。
## Museが次に実行すること
1. 既存のGLM回収指示（docs/glm-sourcing-handover-2026-11-14.md）に従い、既存環境のソースとCSV/JSONを非公開経路で共有。GLMのコードが既に回収済みなら再回収不要。
2. GitHubの同一版を取得し、既存の隔離Python環境で `cd research/online/local-pkg && python -m unittest -v test_sourcing_gate` を実行。非執筆者としてコードも確認し、実行結果と受領を記録。
3. GPTはGLMの実データ構造に合わせてアダプターを実装する。SKU・カラー・サイズ・状態・取得証拠が不足する行をHOLDとし、推測で補完しない。
4. 既存許可済みのBSTN実収集は独立して続行。発掘シグナルに基づき優先対象を絞る。新規サイトの制限を回避しない。
## 状態
オフライン単体検証 PASS。実収集・GLM統合・Muse受領・非執筆者レビューは未確認。GitHub登録を通知受領とみなさない。iPhoneリマインダーの完了更新はしない。

## 追加実行：実際のパイロット報告書の隔離取り込み
実際のユーザー提供DOCXを読み込み、報告上の8候補・145参照記録を欠損なく分離保存。原本や価格・商品別情報は非公開のためGitHubに載せない。未確認の報告値は verified offer / sale に昇格させない。全8候補HOLD、検証済み買付・成約・利益は各0、公開0。元の14テストも同一blobで再実行して合格。実報告書の8件、参照145件、実行入力に未検証参照を混ぜないこと、全件HOLD、問題の2参照が隔離されたことをローカルassertで確認した。
実行コード: research/online/local-pkg/pilot_report_import.py (commit 73a7c92a5d754aedc2486df773b29615ffc6b17b, blob c8e0dd1e25d9b3b983f0a3d1567dbce5fe8512ff)。python-docxが利用できる環境で `python pilot_report_import.py --report <非公開の報告書.docx> --out <新規の非公開出力先>` を実行。既存ファイルは上書きしない。
出力: candidate_watchlist.csv, report_claims.json, decisions.json, audit_summary.json。報告書の構造専用の隔離処理であり、GLM原本の回収や実サイトからの取得の代用ではない。次に必要な入力はGLMのsourcing/ソースと実CSV/JSON。GPT環境ではgithub.comへの直接git接続がDNS失敗したため、GitHubコネクタでコードを保存し、ローカル実行済みコードとblob一致を確認した。Museの受領・実機実行は未確認。
