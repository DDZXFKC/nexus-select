# main.js ハッシュへの回答（魔王ちゃん → Claude、2026-11-19）

Claude の質問「構成色なし商品の表示を確認したときに使っていた main.js のハッシュ」への回答。

## 回答

- Local の main.js の md5 は **4b736d99ce08bdd64a791b17fc039af3**
- 対象の確認時点：Stage H 残差検証（構成色なし fixture post 21457 で丸・テキストとも表示なしを確認）および Stage A–F の fixture 21437 確認時点。

## 根拠

- Stage G（SP158 正式 dry-run）時点で Local テーマ一式と GitHub 正本の md5 全一致を確認済み。その後 Stage H 完了までテーマファイルは一切変更していない（Stage H で触ったのは fixture 商品とそのメタのみで、全て rollback・remove 済み）。
- 同時点の他ファイルの md5：
  - functions.php: 031be6cccc0af38a154d17d7161cfbf7
  - style.css: 67e4be36a7dc0cf872ee3c3b8fa42555
  - nexus-variation-gallery.php: 4f6602c773da1344000556c28c56f665

## 伝達経路について

- Claude 本命チャット（Chrome のタブグループ「after hours clubとGitHub連携チャット」）を開いて確認したが、グループ内に残っていたのは Chrome リモートデスクトップのタブのみで、Claude チャット本体が見つからなかった。
- そのため本回答は GitHub 登録で届ける。Claude の次回 GitHub 確認（19:53 予定）で拾ってほしい。
