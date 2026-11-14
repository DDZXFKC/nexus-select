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
