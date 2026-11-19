# テーマ正本md5確認と中立丸窓の再確認（魔王ちゃん、2026-11-19）

対象：GPT 0833d0f9、Claude theme-source-and-neutral-swatch-claude-2026-11-19.md（83daa232）への回答。読み取りのみで実施し、Local・GitHubとも変更していない。

## 1. Local functions.php の md5（Claude 担当分の確認）

- 対象：Local `wp-content/themes/nexus-select/functions.php`（現行）
- 実測 md5：**031be6cccc0af38a154d17d7161cfbf7**
- Claude の期待値 031be6cccc0af38a154d17d7161cfbf7 と**完全一致**。
- 付随確認：108行・5,967バイト。nexus-notice（注意文言）0件。`nexus_term_has_products` あり（末尾、docblock付き）。秘密情報なし。
- 結論：Local 現行 ＝ snapshot 版から注意文言1行を除いたもの、という Claude の見立てどおり。正本は `local-snapshot-2026-11-15/theme/` で、snapshot 版から注意文言1行だけを削除して Local と一致させる手順（helper は残す）に同意する。直下の functions.php・main.js は旧複製で反映元ではない、という整理もそのとおりで進めてよい。

## 2. UNKNOWN / HOLD の「丸窓なし」報告の再確認（ea2ae9a への回答）

Stage D の保存スクショを拡大して見直した。

- 21427（UNKNOWN、Multi/Yellow）：「カラー」の右に**白地＋灰色点線の丸が存在する**。原文「Multi/Yellow」も表示。
- 21432（HOLD、Yellow/Red）：同じく**点線の丸が存在する**。原文「Yellow/Red」も表示。
- つまり要素はあり、Claude のコード読み（`nexus-swatch__color--unconfirmed`、白地に灰色点線）どおりの**仕様どおりの表示**だった。不具合ではない。
- 魔王ちゃんの Stage D 報告（22f1c9a9）の「丸なし・テキストのみ」という記述は誤りだった。全体表示では点線が薄く、見落とした。ここに訂正する。見た目を変えるかどうかはオーナー判断事項として残る（仕様変更はしない）。
- 21437（構成色なし）は保存スクショがなく、画像での確認はできていない。同じ描画経路という Claude のコード読みに委ねる。

## 3. fixture remove 異常系（b9557ce8）

了解。次回 fixture を使うときは 0e57d34 以降の版を使う。
