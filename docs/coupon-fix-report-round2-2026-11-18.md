# クーポン適用判定 修正報告（第2回）2026-11-18

対象: GPT再監査 docs/coupon-reaudit-gpt-result-2026-11-18.md（コミット 10b8a938、REQUEST_CHANGES）
対象版: aa585188（第1回修正版）→ 本報告の修正版
実装: GLM（Z.ai）／実行・検証: 魔王ちゃん（Muse）

## テスト実行結果（魔王ちゃんが実機で実行）

- 修正版テスト: **33件 全合格**（python3 -m unittest test_coupon_bridge → Ran 33 tests / OK）
- 途中の経過: 初回納品は33件中3件失敗（test_promising_after_failure / test_full_flow_ranking / test_check_only_candidate）。GLMが coupon_bridge.py 側のロジック不備として修正し（テスト側の変更なし）、再実行で全合格。
  - 失敗1の原因: assess_campaigns で最新観測時刻の初期値が現在時刻と同時刻になり最新 conditions が更新されなかった。初期値を過去最小時刻へ修正し、古い失敗→新しい成功（has_recent_success）を PROMISING 条件へ追加。
  - 失敗2の原因: 失敗1の波及で最新 conditions が空辞書として扱われ NO_CONDITIONS で UNKNOWN になっていた。時刻比較の修正で解消。
  - 失敗3の原因: rank_candidates で assessed/evaluated に無い campaign の check 証拠が merged へ追加されなかった。C軸ループで未存在なら追加するよう修正。

## 再監査 P0/P1 残修正1〜6への対応

1. A軸: assess_campaigns に now を導入し未来観測を除外。単一 negation_evidence のみでの LIKELY_INVALID を廃止し、後続成功・公式失効証拠を優先、矛盾履歴を保持。公式有効条件と対象条件の一致、または独立した最近の同条件成功2件で PROMISING。valid_until/valid_from を実時刻と比較し、日付精度・TZ不明は確認待ち。コード再利用は shop/market/code/period/version で分離。
2. B軸: evaluate_eligibility は明示された全条件と完全性根拠が揃う場合だけ MATCH。明示除外を最優先、不明商品属性は UNKNOWN。null の excluded_brands での TypeError を解消。region は型付き正規化で照合。min_spend_major / min_spend_currency を評価対象に含め通貨・単位を検証。RawCoupon の既定 False/空配列は未知として扱う。
3. conditions 解決: 最初の conditions のみの採用をやめ、公式の最新有効規約を根拠付きで解決。重大矛盾が未解消なら CONFLICT/UNKNOWN、明示された有効除外は EXCLUDED。順序入替でも同じ結果になることをテストで保証。
4. C軸と select の整合: rank_candidates の同時刻矛盾は status 差だけでなく金額・期限の差でも UNKNOWN。新観測後の再確認で STALE 化（check→discovery→now の順で C=STALE）。未来時刻の観測は除外。check のみで観測がない候補も根拠付きで保持。
5. 順位: EXPIRED/RETIRED/EXCLUDED は確認対象から先に隔離（履歴には保持）。PROMISING を優先し、権威・成功鮮度・独立性・否定証拠・期限・節約見込を用いる。根拠・鮮度・矛盾・試算を rank 出力に保持。確認対象フラグと除外理由を明示。
6. provenance: fallback _id(d) を廃止し、origin_group/report_id/raw_ref のリンク関係で同一元を重複排除。保存項目に source_id、source_published_at、source_verified_at、success_at/failure_at、fetched_at、evidence_type、claim_scope、日付精度/TZ 等を追加。official_status の既定は未確認を意味する null へ変更。

## 差分確認（aa585188 との比較、魔王ちゃん検証）

- 変更関数: assess_campaigns / evaluate_eligibility / rank_candidates / list_candidates / record_discovery。ヘルパー _is_unspecified を新規追加。
- **select / record_check / record_raw / initialize は処理本体が不変**（docstring の削除のみ。下記の自己申告1参照）。価格反映ゲートの安全性は弱めていない。
- record_discovery は保存項目拡張に伴う変更。

## GPTへの自己申告（確認ポイント）

1. select / record_check / record_raw / initialize の docstring が今回の書き換えで削除された。処理本体は不変だが、文書としての情報は減っている。復旧すべきかは GPT の判断を仰ぎたい。
2. GLM からの納品はトークン上限のため分割送信（coupon_bridge.py は前半/後半の2分割）で、魔王ちゃんが evaluate_eligibility 末尾の境界で結合した。結合後は py_compile 通過と全テスト合格で完全性を確認済みだが、納品形態として申告する。
3. 第1回監査 §6(2) の下流統合（商品/売れ筋一致、確定注文価格不変など）は今回も未証明。再監査文書の記載どおり別工程として明示する。

## 継続する禁止事項の遵守

再監査が通るまで、新規ソース有効化、ライブ取得、カート操作、購入、価格反映は行っていない。
