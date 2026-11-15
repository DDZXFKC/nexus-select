# Issue #2 への対応（Claude、2026-11-15）

対象：Issue #2「AFTER HOURS CLUB｜初回QA監査・公開前の修正優先順位」。
テーマの修正は `local-snapshot-2026-11-15/theme/` に入れた。**Localへの反映は、実行中の再検査（--fresh）が終わってから**。

## P1 KIDS空カテゴリー → 修正済み（テーマ）
- `functions.php`：`nexus_term_has_products()` を追加（そのカテゴリーか子孫に公開商品があるか）
- `front-page.php`（コレクションカード）：商品のないカテゴリーのカードを出さない
- `taxonomy-product_cat.php`（左ツリーの「ALL … ITEMS」）：ルートに商品がないときはリンクを出さない
- カテゴリー自体・URLは削除しない。直接アクセスは従来どおり NO ITEMS。商品が公開されれば自動で表示される

## P1 /brands/ → サイトの画像欠損ではなかった
初回レポート（findings.json）を確認した結果、16件はすべて `https://kaitsuke-shop.local/wp-content/themes/nexus-select/assets/brands/*.svg`（ewingは.png）への取得で、原因は **`CERTIFICATE_VERIFY_FAILED`（Localの自己署名証明書）**。404ではない。ロゴファイルはテーマに12個そろっている。

ただし、本番移行で問題になる点が2つある。
1. /brands/ は固定ページ本文に `https://kaitsuke-shop.local/...` の**絶対URL**が直書きされている（トップページのロゴはテーマ関数で出しているので問題なし）。移行時の URL 置換で `https://kaitsuke-shop.local` と `http://kaitsuke-shop.local` の**両方**を `https://after-hours-club.com` に置き換えること。漏れるとロゴが全部切れる
2. Localではページがhttp、ロゴがhttpsの混在。ブラウザがLocalの証明書を信頼していないと実際に表示されない。iMacのSafariで http://kaitsuke-shop.local/brands/ を開いて目視確認してほしい（表示されれば検査環境だけの問題で確定）

検査側：fc2271f の正規化で、次回からLocalではこの16件は出ない。

## P1 Vans（product 6374）→ データ修正が必要（iMac側）
- 原因は縮小画像の欠落ではなく、**元画像そのものがない**：`wp-content/uploads/2026/11/vans-lx-floral-rivet-pack-02.webp`（attachment ID はレポートの画像メタ、商品ID 6374）。縮小4サイズの欠落と404はその結果
- そのため再生成（`wp media regenerate`）はできない。元画像を復元できるか確認してほしい（ゴミ箱、商品発掘システムのダウンロード元、買付先の商品ページ）
- 復元できない場合の選択肢（オーナー判断）：①この画像だけを商品のギャラリーから外す（他の画像は残る）②商品ごと非公開。①を推奨

## P0 WebKit/PCカート → 再検査待ち
検査側を強化した（本コミット）：
- カートに入った商品が、追加した商品と一致するか（従来型カートは商品IDで、ブロック型は商品名で照合）
- 既存：通信完了待ち、カート・チェックアウトブロックの描画待ち、失敗時のCookie数記録
- 購入検査が実行できなかった場合は PURCHASE_SKIPPED（REVIEW）であり、合格扱いにはならない

## P5 本番HTTPS → 検査側を修正済み
http/https の揃え込みは **Local（.local など）でだけ**行う。本番では元のURLのまま巡回し、混在リンクも報告する（隠さない）。

## 確認
- 品質検査の単体テスト 22件合格（新規：カートの中身の照合）
- 自動分類・URL転送の単体テスト 31件合格（変更なし）
