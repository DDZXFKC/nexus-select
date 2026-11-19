# テーマ正本の確認と中立丸窓の確認方法（Claude、2026-11-19 18:45）

GPT 0833d0f・ea2ae9a・b9557ce の Claude 担当分。新機能なし（エラー解消優先 9d852d2）。

## 1. functions.php の正本（0833d0f）
- リポジトリには2つある。
  - `functions.php`（直下）：90行。11-14 の古い複製。48f5c00 で注意文言の1行だけ削除済み。`nexus_term_has_products` は無い。
  - `local-snapshot-2026-11-15/theme/functions.php`：109行。注意文言（11行目）と `nexus_term_has_products`（97行目〜、空カテゴリー非表示）の両方がある。
- 直下版と snapshot 版の差は「注意文言1行」と「helper 18行」だけ（diff確認済み）。
- 期待値：Local の現行 functions.php ＝ snapshot 版から注意文言1行を除いたもの。その md5 は **031be6cccc0af38a154d17d7161cfbf7**。
- 魔王ちゃんへ（読み取りのみ）：Local の `wp-content/themes/<nexus-select>/functions.php` の md5 を取り、上と一致するか確認してほしい。
  - 一致すれば：正本は `local-snapshot-2026-11-15/theme/`（main.js・style.css・mu-plugins もここが現行）。Claude が snapshot 版から注意文言1行だけを削除して正本を Local と一致させる（helper は残す）。
  - 不一致なら：Local の functions.php の全差分を GitHub に（秘密が無いことを確認して）。旧 snapshot で Local を上書きしない。
- 直下の `functions.php`・`main.js` は旧複製で、Local への反映元ではない（main.js は 11-15 の 11,203B 版）。反映元に使わないこと。

## 2. UNKNOWN/HOLD の「丸窓なし」報告（ea2ae9a）
- コード上は、`_ahc_color_components` に `__single__` がある単一色商品では、状態に関係なく「ラベル・丸・原文」の3要素を必ず出す。CONFIRMED 以外の丸は白地に灰色の点線（`nexus-swatch__color--unconfirmed`、36px）。構成色なしでも丸は出る（原文は空）。
- 報告の「丸窓なし」が「点線の丸が見えにくかった」のか「要素が無い」のかを区別するため、既存のスクショを見直すか、該当の下書きプレビューでブラウザのコンソールに次を貼って結果を記録してほしい（読み取りのみ）：
  ```js
  [...document.querySelectorAll('.nexus-single-color')].map(b => ({
    label: b.querySelector('.nexus-single-color__label')?.textContent,
    swatchClass: b.querySelector('.nexus-single-color__swatch')?.className,
    size: (() => { const r = b.querySelector('.nexus-single-color__swatch')?.getBoundingClientRect(); return r ? [r.width, r.height] : null; })(),
    border: b.querySelector('.nexus-single-color__swatch') && getComputedStyle(b.querySelector('.nexus-single-color__swatch')).borderStyle,
    name: b.querySelector('.nexus-single-color__name')?.textContent
  }))
  ```
  - 期待値（UNKNOWN/HOLD/構成なし）：要素1つ、swatchClass に `nexus-swatch__color--unconfirmed`、size `[36, 36]`、border `dashed`。
  - 要素が0なら不具合（Claudeが直す）。点線が見えにくいだけなら仕様どおり（見た目を変えるならオーナー判断）。
- 仕様は変更しない（未確定は中立表示。既知の色だけ塗る・丸を消す等の変更はしない）。

## 3. fixture remove の異常系（b9557ce）
- 空SKU・親不一致・trash・型違いは 0e57d34 で修正済み（今回の実機は ab86a89 版で実行）。次回 fixture を使うときは 0e57d34 以降の版を使う。

## 4. 結果（18:50）
- 魔王ちゃん確認：Local の functions.php md5 = 031be6cccc0af38a154d17d7161cfbf7（期待値と一致）。→ 正本は `local-snapshot-2026-11-15/theme/`。snapshot 版から注意文言1行だけを削除し、md5 が Local と一致（031be6cc…）。helper `nexus_term_has_products` は残した。php -l OK。Local への反映は不要（既に同じ）。
- 中立丸窓：保存スクショで UNKNOWN/HOLD の点線の丸を確認（57a52ae で報告訂正）。仕様どおり、不具合なし。21437（構成色なし）はスクショ無しで未確認。必要になれば次回 fixture で確認（成功済みの手順は繰り返さない）。
