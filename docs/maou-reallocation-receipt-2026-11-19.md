# 再配置の受領と着手状況（魔王ちゃん、2026-11-19）

docs/team-reallocation-glm-return-gpt-2026-11-19.md、docs/ahc-ai-coordinator-design-2026-11-19.md、docs/ahc-ai-coordinator-kickoff-2026-11-19.md を読み、魔王の担当分に着手した。

## 着手済み

- GLMへ価格検証の着手指示を送信した（直接API経由）。内容：既存 collector/price-audit と shoepalace_price_audit.py を再利用し、v8出力に対して261差分と163商品・1,796行を再照合する。条件は最新確認済み観測時刻・同一variant・価格と在庫は同一snapshot。範囲は価格レイヤーのみで原価計算はしない。ライブ取得・カート・購入・価格反映は禁止のまま。並行でサイズ未照合の公式根拠整備と HOKA／UGG／BIRKENSTOCK ガードも指示した。
- 色の店タグ候補40色：GLM一次検収（可21・否3・保留16）は f9ceaf10 で登録済み。GPTの最終検収後に魔王が実シートへ反映する。Clear／Camo／柄／主色矛盾は自動承認しない。

## これから行う

- ClaudeのLocal検証（丸窓接続の実機確認）を iMac セッションで先行実施する。本書の登録時点では未実施。
- GLMから再照合の手順とコードが返り次第、ローカルで実行し、結果をGitHubへ登録する。

## Coordinator環境確認（魔王の担当分）

- GitHubコネクタ：読み書きとも可（本書の登録自体が証拠）。
- GLM：直接API経由で送受信可（復帰済み）。コネクタ保存キーの差し替えは未了。
- GPT／Claude：現状はチャット経由のみで、API adapter はない。
- dispatcher の iMac 常駐（launchd 等）は未検証のため、自動実行は宣言しない。初期は合成タスクのみ、実データ移行は往復検証の後という設計どおりに進める。

既存の権限ルール・公開条件・1店舗ずつの作業順序は変更していない。
