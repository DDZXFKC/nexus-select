# GLM担当分の引き継ぎ（2026-11-18、オーナー指示）

GLM（Z.ai）が利用制限（429）で停止中のため、GLMの残作業を Grok へ振り替える。GPTは監査役のまま変更なし。

## 対象作業：クーポンテストの残り2件の整合

- 現状：collector/coupon_bridge.py は GPT検収テスト（test_coupon_acceptance_owner.py）8/8合格。collector/test_coupon_bridge.py は 38件中36件合格。
- 失敗1：test_full_match — 全次元をそろえたfixtureでも evaluate_eligibility が UNKNOWN / INCOMPLETE_RULES を返す。完全性チェックが要求する次元とfixtureのずれを解消する。
- 失敗2：test_full_flow_ranking — 統合テストのfixtureが部分条件のため UNKNOWN になる。fixtureを全次元にそろえる。

## 制約
- GPT検収テスト8件の合格を崩さないこと。期待値を弱めて通すのは禁止。
- 変更は unified diff または差し替え全文をチャットで返す（Grokはpush不可のため）。

## 完了条件
- test_coupon_bridge.py 38/38 かつ test_coupon_acceptance_owner.py 8/8。
