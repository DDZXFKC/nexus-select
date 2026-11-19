# 旧商品ページ隔離復元 実施報告（魔王ちゃん、2026-11-19）

依頼：docs/owner-old-product-page-isolated-restore-2026-11-19.md（d1bad5ae）への実施報告。

## 実施方法

- Local で現行サイトの clone「kaitsuke-shop-1115」（ドメイン kaitsuke-shop-1115.local）を作成し、テーマと mu-plugins を 2026-11-15 スナップショット（Downloads/local-snapshot-2026-11-15.zip、2026-11-15 05:51）に差し替えた。
- 現行サイト・本番・商品データは変更していない。差し替え後に現行サイトの functions.php の md5 が 031be6cccc0af38a154d17d7161cfbf7 のまま不変で、注意文言の出現数も 0 のままであることを確認した。

## 版の同定（差し替え後の clone の md5）

- themes/nexus-select/functions.php: b174e1c00ad7668785b4f6b166747856
- themes/nexus-select/main.js: 50638080d60d9a22d8d230ee464f0937
- themes/nexus-select/style.css: 581014d4f431f22d7fbbc816ea708b62
- mu-plugins/nexus-variation-gallery.php: acb5504e76570819bbf5cc3f2a7f5602

## 注意文言（正確な文言と位置）

- clone の functions.php 11行目。フックは woocommerce_single_product_summary、優先度35。
- 文言：「海外から買い付ける商品は、在庫・価格・配送予定が変わる場合があります。ご注文前に各商品条件をご確認ください。」
- 表示位置の実測：商品ページのサマリー内で「お買い物カゴに追加」ボタンの直下、商品メタ（商品コード・カテゴリー）の直上。PC 表示とスマホ幅 430px の両方でスクリーンショットにより確認した。
- 確認に使った商品：Premium Old Skool 36 Bandana Black Mens Skate Shoes (Black)（商品コード SP-8798793826510、¥31,100）

## 補足1：文言の初出について

- 2026-11-09 の完全バックアップ（Desktop の kaitsuke-shop-backup-2026-11-09-before-nexus-v02.zip）内のテーマ functions.php 11行目にも同一文言が存在した。実 Local テーマでは少なくとも 2026-11-09 時点で文言があったことになる。
- Claude の調査（docs/old-product-page-wording-search-claude-2026-11-19.md）が示す GitHub 履歴上の初出 2026-11-14 とは出どころが異なる（repo の記録と実バックアップの差）。

## 補足2：「海外お取り寄せ」の検索結果

- 完全一致「海外お取り寄せ」は、テーマ・コード全履歴（Claude 調査）でも、DB バックアップ全件（2026-11-09 / 2026-11-12 / 2026-11-19 の3件）でも 0 件。部分一致「お取り寄せ」も DB では 0 件。
- 当時の商品ページにあったのは上記の注意文言であり、「海外お取り寄せ」という語は使われていなかった。

## 制約

- clone の DB は現行サイトの複製（商品データは現行のもの）。テーマと mu-plugins のみ 2026-11-15 版。
- スクリーンショット画像はバイナリのため GitHub には登録せず、オーナーへチャットで提示した（PC 1280px / スマホ 430px、2026-11-19 撮影）。
