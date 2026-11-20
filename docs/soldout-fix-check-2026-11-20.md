# sold out修正（threshold 200）Local再確認結果 — 2026-11-20

宛先：Claude（サイト専任）
報告：魔王ちゃん（実機確認）
対象コミット：`19568bbd`（woocommerce_ajax_variation_threshold を200へ引き上げ）

## 差し替え結果

- 成功。GitHub正本（コミット `19568bbd`、`local-snapshot-2026-11-15/mu-plugins/ahc-soldout.php`、md5 `f6017a549d09fc7b23c0348e241bf330`）をLocalへ反映し、md5完全一致を確認した。
- 旧版は iMac の `/Users/discodadz/ahc-backup-2026-11-20-soldout-fix/` にバックアップ済み。

## 再確認結果

対象商品：id=18743「Patta x Nike Air Max 1 '87 "Waves"」（全44バリエーション在庫切れ）
確認方法：変更後に再読み込みされた画面で確認。

### 1. 在庫切れサイズが押せなくなるか → ならなかった

- カラー選択後もUS 9.0はクリックで選択状態（黒枠・checked）になる。
- 取り消し線・グレーアウトもなし。
- ただし、全サイズ・両カラーのラベルに「SOLD OUT」が付与されるようにはなった。threshold 200によるバリエーションデータのインライン化は効いている。

### 2. SOLD OUT表示 → 表示された

- カラー＋サイズ選択後、太字赤色の「SOLD OUT」が表示された。

### 3. カート阻止 → 阻止された（ただし従来経路）

- 「お買い物カゴに追加」で WooCommerce標準アラート「この商品は対応しておりません。異なる組み合わせを選択してください。」が出て阻止され、BAGは(0)のまま。
- 阻止経路は差し替え前と同じ標準アラートで、ボタン無効化によるものではない。

## 結論

- SOLD OUT表示とカート阻止は機能している。
- 「サイズボタンが押せなくなる」点は未実現。実現にはClaude側の追加修正が必要（サイズボタン自体の無効化）。

## Claudeへの依頼

- サイズボタン自体の無効化（在庫切れサイズを選択できないようにする）の追加修正を検討してほしい。
- 修正版ができたら、正本をGitHubへ登録してもらえれば、魔王ちゃんがLocalへ反映して再確認する。

## 証拠スクリーンショット（GitHubへは上げていない。魔王ちゃんのワークスペースに保管）

`~/workspace/soldout-check/` 配下：

- `shot_product18743_after_fix_initial.jpg`
- `shot_product18743_after_fix_color_selected.jpg`
- `shot_product18743_after_fix_size_clicked.jpg`
- `shot_product18743_after_fix_addtocart_alert.jpg`
