# Claude 受領と coordinator 契約レビュー（2026-11-19 12:45）

## 受領（69013b6 / a6633d1 / f0b5f8c / b38dc0f）
- Claude担当：サイト専任（theme/Woo/UI）。丸窓接続、旧表示残存の防止、色・画像・型番・サイズ・価格・在庫連動、PC/スマホ、ホーム/カテゴリ/カート/チェックアウトのLocal完成検証。coordinatorは契約レビューのみ。
- 担当外のPython（color_fullrun.py 含む collector の色・価格・サイズ）は今後編集しない。Woo接続用の color_woo_export.py のみ担当として保守する。
- 現状：オーナーPCのブリッジ未接続（11:50〜12:36 で計5回確認）。Local検証は魔王ちゃんへ実行依頼（docs/color-woo-connect-claude・swatch-local-check-claude の手順）。その間コードとオフラインテストを進める。
- 本日の対応：旧表示残存の防止（未確定・HOLD・構成なしも中立表示で書く）と、書き込みツールのオフライン検証を追加（docs/color-woo-connect-claude-2026-11-19.md 追記参照）。

## contract.json レビュー（Claudeアダプタの立場から、誤りのみ）
1. **リース切れの行き先がない。** CLAIMED/RUNNING から READY への遷移が無いため、stale_lease_rejected で期限切れにしたタスクが動かせなくなる。→ CLAIMED→READY、RUNNING→READY（リース失効時のみ、dispatcherのみ）を追加。
2. **CANCELLED に入れる状態が WAIT_OWNER だけ。** 設計は「CANCELLED（許可済み）」を別扱いにしており、QUEUED/READY/BLOCKED から取り消せない。→ 許可済み取消として追加。
3. **Claudeは常駐しない。** Claudeはセッション起動時（現在10分間隔）にしか動けないため、heartbeat 60秒・lease 10分ではほぼ必ず失効する。→ エージェント別に heartbeat/lease を registry で持つ（Claudeは lease 30分以上、heartbeatはセッション単位）。
4. **全員が同じGitHubアカウント（DDZXFKC）でpushしている。** commitの作者では主体を区別できず、authenticated_actor_not_body_claim を満たせない（Co-Authored-By等の本文は自称）。→ 主体認証は dispatcher 側の別手段（エージェント別トークン等）で行う前提を明記。決まるまで commit 作者を主体証明に使わない。
