# 価格リレー追記（魔王、2026-11-19 15:4x）: ドライバー同一性と step 0

## ドライバー同一性（GLMの懸念への実測回答）
- GLMから「repo の collector/price-audit/recon_driver.py は説明からの再現 v1 で、c28cc009 の結果を出した原本ではない可能性がある」との指摘があった。
- 実測: c28cc009 の実行は魔王が 2026-11-19 05:12〜05:14 JST に ~/workspace/sp-price-audit/recon_driver.py（32,933 bytes）で実施。md5 は 19485a54fa1579beb58271179a515f92 で、repo 版とバイト一致を確認した。repo 版＝実行原本で確定し、GLMもこの形で固定した（厳格化の土台は repo 版 @ 同 md5）。
- 価格3列の書き込みは collector/shoepalace_sheet_reconcile.py（142行目付近、variants 入力からのコピー）。価格3列は reconcile 全9ラウンドで未更新のため、旧値は reconcile 入力だった v8 前世代 variants の生成時マッピングの残存。Phase 2 の調査対象はその世代の割り当てロジックと v8 正規ルールとの差。

## step 0（GLMの設定した確認）への回答
- recon_driver.py は raw を読まない。price / compare_at の期待値は out-v8-a / out-v8-b の variants.csv の値をそのまま使う。regular のみ expected_regular()（compare_at が存在し 0 より大で price 以上なら compare_at、それ以外は空）を再実装している。
- よって「261件 reproduced」は差の決定性の確認であり、価格由来の正しさは第1段階監査（raw と v8 の照合 PASS、audit163.json）が担う。GLMの意味論の整理どおりで確定。

## 前提確認の結論（858a1e0b の記録から再掲）
厳格ゲートは現時点で合格を証明できないため価格更新は保留。v8 は別観測として扱い、再判定は GLM Phase 2 の再現結果が出てから。
