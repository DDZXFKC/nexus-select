# 商品ページの海外買付注意文言を削除（2026-11-19、オーナー指示・実行: 魔王ちゃん）

オーナー指示（2026-11-19 17:55 JST）: 商品ページの文言「海外から買い付ける商品は、在庫・価格・配送予定が変わる場合があります。ご注文前に各商品条件をご確認ください。」をやめる。

## 実施内容
- 出所: テーマ `functions.php` 11行目の `add_action('woocommerce_single_product_summary', ...)` で `<p class="nexus-notice">` として出力されていた（テーマ・mu-plugins・プラグイン・uploads を全検索し、この1か所のみ）。
- Local（kaitsuke-shop.local）の functions.php から該当行を削除。バックアップ: iMac `~/ahc-swatch-check/functions.php.bak-20261119-notice`。`php -l` で構文エラーなし。
- 検証: 商品ページ（SP-8808947646670、Premium Old Skool）をサーバー側で再取得し、本文中の当該文言と `nexus-notice` が 0件であることを確認（ページ自体は正常、タイトル等は表示）。
- GitHub 側も同期: 本コミットで repo の functions.php から同じ1行のみを削除した（repo版との差分はこの1行だけであることを確認済み）。

## 注意（未同期の差分）
Local の functions.php には、repo 版にない `nexus_term_has_products`（商品のないカテゴリーを隠すヘルパー、91行目以降）が存在する。これは今回の変更とは無関係の既存差分なので、本コミットには含めていない。担当側で把握済みかどうか確認されたい。
