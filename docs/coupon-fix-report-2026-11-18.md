# クーポン候補判定 修正報告 2026-11-18

対象監査: docs/coupon-audit-gpt-result-2026-11-18.md（cef433f2、REQUEST_CHANGES）
対象実装: bbc7a121 → 本報告のコミット
実装: GLM / 検証・登録: 魔王ちゃん

## テスト結果（魔王ちゃん実行）

- 修正版初回: 24件中1件失敗（test_expired_check_is_stale: APPLICABLE != STALE）
- GLMが原因を特定し修正（expires_at/checked_atを文字列比較していたためTZ表記差で誤判定 → datetime化しUTC正規化）
- 修正後: **24件全合格**（python -m unittest、Ran 24 tests OK）
- 内訳: 既存14件維持＋監査対応の追加・期待値修正10件

## 設計条件対応表

| GPT必須修正 | 実装 | 対応テスト |
|---|---|---|
| 1. assess_campaigns をA軸6状態へ（転載の重複排除、ホスト数廃止） | origin_group/report_id/raw_refで重複排除。DISCOVERED/CONFLICT/LIKELY_INVALID/EXPIRED/RETIREDを評価 | test_dedup_syndication, test_independent_sources, test_conflict_and_negation |
| 2. evaluate_eligibility(campaign, scope, product_facts) でB軸 MATCH/EXCLUDED/UNKNOWN | 規約条件を照合し実測を混入させない。明示除外優先、欠損はUNKNOWN | test_brand_excluded, test_min_spend_not_met, test_full_match |
| 3. P0 別scope混入の解消、C軸分離 | list_candidates(scope, now, max_age_seconds, product_facts)へ変更しcontext完全一致＋context_id索引で検索。C軸は NOT_CHECKED/APPLICABLE/NOT_APPLICABLE/UNKNOWN/STALE、同時刻矛盾はUNKNOWN、未来記録は無視 | test_scope_isolation_in_ranking, test_conflicting_same_time, test_future_check_not_used |
| 4. P0 期限 | now>=expires_atで失効しSTALE。TZ不明はUNKNOWN。境界はdatetimeでUTC正規化して比較 | test_expiry_boundary, test_expired_check_is_stale, test_staleness |
| 5. rank_candidates が三軸と根拠を保持 | 三軸＋reasons/鮮度を保持。EXCLUDED/EXPIRED/RETIREDは有力候補にしない決定的順序 | test_no_leak_effective_minor, test_full_flow_ranking |
| 6. 保存層の互換拡張 | record_discoveryに任意引数（origin_group/report_id/raw_ref/official_status/conditions_conflict/negation_evidence、既定値あり）を追加。既存SQLite・テーブル維持 | test_existing_table_preserved, test_raw_adapter_candidate |

## 魔王ちゃんの差分確認（bbc7a121との比較）

- select / record_check / record_raw / context: 変更はdocstringのみで処理本体は不変。既存の価格反映ゲートの厳格性は維持。
- record_discovery: 任意引数の追加のみ（互換拡張）。
- 変更の中心は assess_campaigns / evaluate_eligibility / rank_candidates / list_candidates。

## GPTへの確認ポイント（自己申告）

1. A軸の PROMISING 状態は実装されていない（DISCOVEREDから他の状態への遷移のみ）。設計§の6状態との差異として再監査で判断されたい。
2. list_candidates は複数conditionsがある場合に最初の1件を代表として評価している（GLMのコメントで「設計上の単純化」と明示あり）。
3. assess_campaigns の LIKELY_INVALID は negation_evidence の有無で判定しており、「独立した最近の失敗」の鮮度・独立性の厳密な評価は限定的。

## 継続する禁止事項

新ソース有効化、ライブ取得、カート操作、購入、価格反映は行っていない。次はGPTの再監査待ち。
