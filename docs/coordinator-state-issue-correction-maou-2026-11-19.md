# 訂正： 状態保存 Issue は #7 に一本化（魔王ちゃん・2026-11-19 23:12 JST）

14e0f8b3（coordinator-startup-readiness）の §1 を訂正する。

- 起動報告の登録後に確認したところ、オーナー自身が先に Issue #7「AHC Coordinator State」を作成していた（魔王ちゃんが #8 を作る約14分前）。
- 状態の二重正本を避けるため、魔王ちゃんが作成した #8 は「Duplicate of #7」のコメント付きで **Closed** にした。
- **dispatcher の状態保存先は Issue #7 に確定**： https://github.com/DDZXFKC/nexus-select/issues/7
- GPT は初回本番サイクルの初期化（envelope 投入）を #7 に対して行うこと。
- トークン等の他の前提に変更はない。
