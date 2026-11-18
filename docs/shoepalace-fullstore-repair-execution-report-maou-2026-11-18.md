# Shoe Palace 全店バッチ読み取り専用repair：実行報告（魔王ちゃん、2026-11-18）

実行：2026-11-18 22:49〜22:52 JST、VM上。原本・DB・シート・本番・価格への書き込みなし。オーナーの明示承認（2026-11-18 22:48「どうぞ」）を受けて実施。

## 入力

- 原本：iMac の ahc_data/raw_json/Shoe_Palace/20261118_045314/（page_1.json〜page_48.json、48ページ）をVMへ転送して使用。旧バッチは混ぜていない。
- 実行前検査：総行数 11,777、distinct商品ID 11,777、同一IDの内容衝突 0。
- 対象コード：検収済み版 code5（shoepalace_repair.py、色確認CSV対応版）。
- 参照：cm監査版（real5/cm-audited.csv）、色確認CSV（real5/color-confirmation.csv）。

## 実行結果（2回実行、出力は完全一致・diff差分なし、終了コード0×2回）

- 全商品 11,777（在庫あり 6,244／全在庫なし 5,533／不明 0）
- バリアント総数 103,834（在庫あり 30,191／不明 0）
- issues 89,675

## 内訳

- 色（商品単位）：TAG_SUPPORTED 10,662、TITLE_CANDIDATE 1,024、CONFIRMED_BY_TITLE_RULE 68、UNKNOWN 21、HOLD_CONTRADICTION 2
- cm（バリアント単位）：MATCHED 596、MISSING 76,841、NOT_APPLICABLE 26,387、SIZE_SYSTEM_REVIEW 10
- クーポンタグ付き商品 881
- 価格なしバリアント 0、画像あり 11,777、英語説明あり 11,777、URLあり 11,777
- issues内訳：cm_reference_missing 76,841、japanese_description_pending 11,777、color_name_needs_review 1,026、color_name_unknown 21、footwear_alpha_size_review 10

## 保存先

- VM：~/workspace/sp-fullstore/out-full-a/（products.csv、variants.csv、issues.csv、repaired.json）。163件の成果物とは別保存。
- 全cm補完の完了ではない。cm MATCHED は163件検証時と同じ596件で、残りは公式表の確認が取れた分だけ既存参照資産へ追記する独立作業として継続する。色のTITLE_CANDIDATE 1,024件とUNKNOWN 21件も未確定のまま保持する。
