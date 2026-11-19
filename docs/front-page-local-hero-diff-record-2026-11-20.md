# front-page.php Local差分の記録（2026-11-20）

GLM判断（2026-11-20、docs/review-glm-reverify-2026-11-20.md §3）：**決定記録のないLocal変更は採用しない。正本（5枚）を現行とする。** Local側3枚版は破棄するが、将来の判断材料として本記録を残す。

## 差分の内容（Claude分析、docs/c1-site-error-inventory-claude-2026-11-19.md §5）
- 差分はモバイルのヒーロー画像のみ
- 正本（local-snapshot-2026-11-15）：5枚（添付ID 18930 / 18932 / 18933 / 18934（縦）/ 18935）
- Local：縦3枚（添付ID 18943 / 18944 / 18945）
- Localの3枚版ファイル自体は local-snapshot-2026-11-20-local/theme/front-page.php（ca3f7bdd）として登録済み
- Localを3枚に変えた決定の記録は GitHub に見当たらない

## 備考
- 縦3枚の選択には技術的合理性があり得る（モバイルの読み込み速度・縦画素対応）。将来「枚数削減」を検討する場合は本記録と上記の登録ファイルを参照し、正本へのコミットとして改めて行う
- E5実機確認のチェック項目に「モバイルヒーロー5枚の体感（読み込み速度・スクロール）」を追加済み
- 次回テーマ反映時に、正本の front-page.php / main.js / ahc-fixture-guard.php をLocalへ入れる（main.js と ahc-fixture-guard.php は正本が新しい版、Claude分析による）
