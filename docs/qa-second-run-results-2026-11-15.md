# QA再検査（第2回）結果 — 2026-11-15

- run: 20261115-085102（--fresh、08:51開始 → 09:36完了）
- 対象: http://kaitsuke-shop.local/（商品197点、巡回1,459ページ、画像8,771枚）
- 結果: **CRITICAL 0 / HIGH 121 / MEDIUM 4 / LOW 1 / REVIEW 1**（新規113、解決788）
- 初回（20261115-071551）: CRITICAL 1 / HIGH 796 / MEDIUM 4

## 内訳

| 種別 | 件数 | 内容 |
|---|---|---|
| CAT_CURRENT_HIGHLIGHT | 108（HIGH・新規） | カテゴリーナビで現在地がハイライトされていない（mens 47 / womens 32 / kids 29）。判定はClaudeへ依頼中 |
| BRAND_RESIDUE | 3（HIGH・集約） | サイトタイトル設定、ページタイトル363ページ、本文363ページ。名称統一はオーナー判断待ち |
| PURCHASE_FLOW | 4（HIGH） | 全4組合せとも「注文追跡ページが表示されません（404）」のみ。カートは全組合せで通過 |
| INV_EMPTY_CATEGORY_HIDDEN | 1（HIGH・集約） | 空カテゴリー（KIDS）へのリンク31ページ分。下記のテーマ反映で解消確認済み |
| IMAGE_FILE_MISSING / IMAGE_HTTP_ERROR / IMAGE_SIZE_FILE_MISSING | 9 | 全て Vans LX Old Skool 36 Rivets 分。巡回終了（9:35）より後（9:44以降）に修正済みのため次回runで消える見込み |
| SCHEME_MISMATCH | 1（LOW・集約） | http/https混在リンク |
| CAT_SPEC_EXTRA | 1（REVIEW） | 設計外カテゴリー「スニーカー」（日本語slug）。カテゴリー設定はオーナー指示なしに変更しないため記録のみ |

## 優先課題への回答（GPT監査 Issue #2 の優先順位）

1. **WebKit/PCのカート動作：解消。** 初回のCRITICAL（カートが空）は消え、全4組合せ（webkit/chromium × PC/SP）でカートに入ることを確認。検査側の待機・選択子修正（fc2271f8）が有効だった。
2. **Vans商品画像：修正済み。** 1枚目＝公式ALT1（白背景化）、2枚目＝シーン写真、3枚目＝後ろ姿（オーナー指示で追加）。巡回が修正前だったため本runには旧状態で記録された。
3. **/brands/ 画像エラー16件：本runでは発生せず。** Local自己署名証明書による検証失敗が原因でサイト側の不具合ではない（初回所見どおり）。
4. **KIDS空カテゴリーリンク：テーマ修正をLocalへ反映し解消を確認。** daa013f3 の front-page.php / functions.php / taxonomy-product_cat.php をLocal実物へ適用（差分は空カテゴリー非表示の変更のみであることを事前確認）。実HTML検証：トップのKIDSカード消滅（kids_links=0、MEN'Sリンクは正常）、KIDSページはNO ITEMS表示のままALL KIDS ITEMSリンク消滅、MEN'SページからもKIDSへのリンク無し。旧ファイルは ~/ahc-qa-reports/backup/theme-before-issue2-2026-11-15/ に退避。
5. **本番HTTPSリンク確認：移行後に実施。**

## 残る確認事項

- 注文追跡ページ404（PURCHASE_FLOW×4）：GPT監査では検査側のURL想定違いと判定され、fc2271f8で検査対象外になったはずだが本runでも残った。理由をClaudeへ確認中。
- CAT_CURRENT_HIGHLIGHT 108件：確定仕様にハイライト要件は含まれていない認識。検査側の想定かテーマ側の対応事項か、Claudeへ判定を依頼中。
- 旧名称「NEXUS SELECT」の統一（BRAND_RESIDUE 3件）：オーナー判断待ち。

## 記録

- レポート実物: ~/ahc-qa-reports/runs/20261115-085102/（report.html / findings.json / findings.csv / run.log）
- 照合メモ: goals/wordpress-own-site-store/hidden_files/qa-run2-reconciliation-notes-2026-11-15.md
