# sold out表示 Local反映結果（2026-11-20、魔王ちゃん実施）

対象：Claudeの依頼文書 docs/soldout-local-deploy-request-claude-2026-11-20.md（902a850e）

## 反映結果
正本4点（GitHub local-snapshot-2026-11-15/）を、反映前に現行ファイルを /Users/discodadz/ahc-backup-2026-11-20-soldout/ へバックアップしたうえで Local へ反映。反映後に吸い上げ直して md5 照合し、4点とも GitHub 正本と完全一致を確認した。

- wp-content/themes/nexus-select/main.js → 3abad94a902191a9eed0a14d7cf6ed40
- wp-content/themes/nexus-select/front-page.php → 0645e902623ea75d13f506275a55b06b
- wp-content/mu-plugins/ahc-soldout.php（新規） → bf7023d9606fdc17f513ff0ad324fa34
- wp-content/mu-plugins/ahc-fixture-guard.php → ad863005fc64fe0cd03f3621d9130fa8

注意：Claudeの文書に記載された main.js の md5 接頭辞（3abad94a9021b1b0…）は、正本ファイルの実 md5（3abad94a902191a9…）と13文字目以降が食い違う。ファイルサイズ（23,822バイト）は記載と一致し SOLD OUT 実装も含まれているため、正本は正しく、文書側の転記ミスと判断した。

## 再確認結果（再読み込み後の画面）
- (a) 商品カードの SOLD OUT バッジ：表示された。id=18743 と id=8474 のカード左上に黒い「SOLD OUT」バッジ。在庫のある商品には付いていない。カテゴリページでは対象商品が1ページ目に無いため、同一ショップループの検索結果一覧で確認。
- (b) 商品ページ（id=18743）：カラー＋サイズ選択後、在庫表示が太字赤色の「SOLD OUT」に変わった。ただしサイズボタン自体への取り消し線／無効化は起きていない。main.js の設計上、バリエーションが AJAX 読込の商品では SOLD OUT 判定をしない仕様のため（本商品は44バリエーション）。Claudeの文書にあった「ボタン自体が押せなくなる」という見込みとは異なる挙動なので、Claude側で要確認。
- (c) カート追加：既存の WooCommerce 標準アラートで阻止され、BAG は (0) のまま。購入できない結果は確認できた（阻止の経路はボタン無効化ではない）。

商品データ・在庫は変更していない。
