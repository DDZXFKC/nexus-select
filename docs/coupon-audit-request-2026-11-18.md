# クーポン適用判定 実装の監査依頼（2026-11-18）

対象: collector/coupon_bridge.py / collector/test_coupon_bridge.py（コミット bbc7a121）
設計の正本: docs/coupon-applicability-gpt-design-2026-11-18.md（3c6e3fc8）
実装: GLM。検証: 魔王ちゃん（テスト実行と差分確認のみ。コードの変更はしていない）

## 実装内容
- 純粋関数 assess_campaigns / evaluate_eligibility / rank_candidates と、CouponBridge.list_candidates を追加
- 既存の select()・record 系・既存14テストは無変更（差分は追加のみであることを確認済み）
- テスト18件全合格（既存14＋追加4）を魔王ちゃんが実行して確認済み
- 候補の出力に effective_minor / sale_approved は混入していない

## 設計との差異（登録前に魔王ちゃんが気づいた点。判定はGPTに委ねる）
1. campaign_confidence の値が、設計の DISCOVERED / PROMISING / CONFLICT / LIKELY_INVALID / EXPIRED / RETIRED ではなく、出典ホストの数による HIGH / MEDIUM / LOW になっている。CONFLICT や EXPIRED などの状態がない
2. eligibility が、設計の「規約条件の照合（MATCH / EXCLUDED / UNKNOWN）」ではなく、実測チェック結果からの変換（APPLICABLE→CONFIRMED、NOT_APPLICABLE→REJECTED）になっており、B軸（規約適合）とC軸（実測）が分離されていない
3. 出所のグループ化が origin_group ではなくホスト名単位。転載チェーンの同一元判定は未実装
4. 鮮度（成功証拠の新しさ）、条件の矛盾検出、期限切れの候補評価への反映が assess_campaigns に入っていない
5. evaluate_eligibility の引数が設計案（campaign, scope, product_facts）ではなく、checks のリストになっている

## 監査のお願い
- 上記が設計書 §6(1)(2) の受入条件を満たすか、判定をお願いします
- 不足がある場合は、修正指示を docs/ へ登録してください。GLM へ引き継ぎます
- 今回もクーポンソースの有効化・ライブ取得・価格への反映は対象外です
