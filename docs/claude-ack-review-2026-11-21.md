# Claude 本命セッションの受領とレビュー（2026-11-21 17:4x）

- 読んだ時点の先頭コミット：9098c69（integration/grok-review）。
- セッション：claude.ai のこのチャット（オーナー／魔王ちゃんとやり取りしている Claude）。
- 読んだファイル：
  - CLAUDE.md
  - handover-execution-to-claude-gpt-2026-11-21.md
  - claude-review-request-stockcheck-and-parallel-execution-2026-11-21.md
  - stockcheck-inline-cart-flow-redesign-gpt-2026-11-21.md
  - tools/ahc-stock-inline-endpoints-staging.php
  - owner-product-image-rules-consolidated-2026-11-21.md
- 読んでいないファイル：muse-owner-instructions-pull-and-delta-check / three-agent-reminders / muse-flow-stoppage。これから読む。
- 魔王ちゃんへの「未共有のオーナー指示はあるか」の確認：**未回答**（チャットで質問した）。

## 実サイト（XServer）
- **Chrome での操作**：可。魔王ちゃんが Basic 認証を通し、オーナーがログインした iMac の Chrome（Claude in Chrome）で操作した。
- **画像**：商品 21376 を差し替えた。実画面で確認したのは PC 幅のみ（docs/image-fix-log-2026-11-21.md）。スマホ幅は未確認。
- **在庫確認**：XServer の実画面は旧方式のまま（ボタンを押すと、入力フォームが下に開く段階1の形）。新しいポップアップ（ahc-stock-check-ui.*）はサーバーに未反映。サーバー側の ahc_sc_add_to_cart が無いため、反映してもカートへ進めない。

## GPT ステージング版（tools/ahc-stock-inline-endpoints-staging.php）への指摘
画面側（ahc-stock-check-ui.js）との境界で確かめた。

1. **【重大】初めて来たお客様では start→step がつながらない恐れ**
   - 原因：WC()->session->get_customer_id() は、カートが空のゲストではクッキーが保存されず、リクエストごとに ID が変わりうる。そのため step の照合（ahc_inline_session_check）で失敗する。
   - 直し方：start で WC()->session->set_customer_session_cookie(true) を呼ぶ。
   - 確認：シークレットウィンドウで XServer 上の実測が要る。
2. **在庫あり（掲載価格）のときの price_text**：listed_price_text だけで、price_text が無い。画面側を listed_price_text でも動くように直した。合意としては、どちらの名前でも可とする。
3. **SOLD OUT を他のお客様に見せる部分**：_ahc_inline_oos_until を読んで、バリエーションを在庫切れとして返すフィルターが無かった。画面側（ahc-stock-check-ui.php）に woocommerce_available_variation のフィルターとして追加した。同じフィルターを GPT 側で重ねて書かないこと。
4. **確認できず（unconfirmed）の reason が常に unreadable**：候補ゼロのときは no_candidate を返してほしい。画面の文言は同じだが、運営への通知を分けるため。
5. **単品（simple）商品**：invalid_selection になる。在庫確認できないまま「在庫を確認する」が出てしまう。単品も対象にするか、単品では別の表示にするかを決める必要がある（Claude 側の画面は単品にも対応済み）。
6. **ahc_sc_add_to_cart**：未公開。返してほしい形は、成功なら {ok:true, cart_url}、失敗なら {ok:false, code: permit_expired|permit_invalid|quote_not_accepted}。入力は permit、accept_quote（0/1）、nonce。
7. **入力名の一致**：nonce（ahc_sc_inline、引数名 nonce）、attribute_* のキー、marked_oos／rate_limited のコードは、画面側と一致している。

## 並行作業について
- 画像の差し替え（Claude）と、カートの門（GPT）は触るファイルが別なので、並行してよい。
- 商品ページの表示（ahc-stock-check-ui.php・js）は Claude だけが編集する。GPT は ahc-stock-check.php とサーバー側の処理だけを編集する。
