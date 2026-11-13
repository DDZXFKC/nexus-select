# 新規買付先11店舗 フェーズ1検証結果（一次資料のみ）

- 実施日: 2026-11-13
- 根拠指示: GitHub DDZXFKC/nexus-select `docs/new-store-collection-verification-2026-11-13.md`（integration/grok-review）
- 方法: 各店の公式サイト（利用規約、robots.txt、配送ポリシー、アフィリエイト/フィード公式ページ、商品ページ1件）を一次資料で確認。403/ブロックは回避せず「確認不可」として記録。
- 注意: アフィリエイトフィードの利用許可は転売目的のデータ利用許可とは別物として、各店の規約文面どおりに記録した。

## 判定サマリー

| 店舗 | 判定 | 理由（1行） |
|---|---|---|
| END. (endclothing.com) | 許可待ち | 規約に収集禁止なし・robots は商品パス Allow・日本直送あり。ただし公式フィードは Impact 申請制で利用条件未確認 |
| HBX (hbx.com) | 除外 | 利用規約 §8 が robots/spiders による情報収集を明示禁止（アフィリエイトは上書きしない） |
| size? (size.co.uk) | 除外 | 現行サイトで利用規約の収集条項が確認できず、日本直送の明記も未確認（許可根拠なし） |
| Footpatrol (footpatrol.com) | 除外 | 規約 §9 が text/data mining・web scraping を明示禁止。Awin フィードは宣伝目的のみ |
| Footshop (footshop.eu) | 許可待ち | 規約に収集禁止なし・robots は商品パス許可。ただし許可根拠もなく、CJ XML フィードは登録＋広告主承認が必要 |
| SSENSE (ssense.com) | 除外 | 規約 §8 が data mining/robots/scraping を明示禁止、§5.2 が商用再利用を禁止 |
| Slam Jam (slamjam.com) | 許可待ち | 規約に収集禁止はないが複製・転売・利用には事前の書面許可が必要。公式アフィリエイトフィードあり（申請制） |
| SNIPES (snipes.com) | 除外 | EU GTC は収集許可なし、米国版 Terms が robot/spider によるコピーを明示禁止、日本配送なし |
| Queens (queens.global) | 許可待ち | 規約に収集禁止なし・robots は商品/カテゴリ許可。ただし直接収集の許可はなく CJ アフィリエイトが経路（フィード条件は CJ 内で要確認） |
| JD Sports (jdsports.com) | 除外 | Terms of Use §D が自動デバイスによる監視・コピーと価格収集等の商用利用を明示禁止。国際配送なし（日本配送なし） |
| Shooos (shooos.com) | 許可待ち | CJ/VIVnetworks 経由の公式 XML/CSV フィードあり（価格比較カテゴリ明記）だが承認制で条件は宣伝目的のみ。.com 規約の収集条項と日本配送は未確認 |

凡例: 収集可（許可根拠あり）／許可待ち（フィード申請等が必要）／除外（規約禁止・403等で確認不可）。今回「収集可」に該当した店舗はなし（全店、規約上の明示禁止か、申請・書面許可が前提）。

---

# Group A 検証結果（Phase-1）

検証日: 2026-11-13
方法: 各店公式サイトのページのみを `browser.open` / `browser.search` で取得。403・ブロックの回避は行っていない。取得できなかった項目は「未確認」と記録する。

---

## 1. END.（endclothing.com）

### 1. 利用規約（スクレイピング禁止の有無）
- 取得ページ: https://www.endclothing.com/en-eu/pages/terms-conditions
- 取得した本文（全131行、購入条件・価格・支払いが中心）の中に、scraping / spider / crawl / robot 等の自動収集を禁止する文言は**確認できなかった**（`browser.find` で "scrap" / "robot" ともにヒットなし）。
- 引用できる禁止条項なし。ただし「禁止がない＝収集が許可されている」ではない点に注意。

### 2. robots.txt
- URL: https://www.endclothing.com/robots.txt
- `User-agent: *` に `Allow: /`。商品・コレクション等の公開HTMLは crawlable と冒頭に明記。
- Disallow は主に取引系・内部系: `/admin`, `/cart/`, `/checkout`, `/checkouts/`, `/orders`, `/account`、フィルタ／ソートのクロールトラップ（`/collections/*sort_by*`, `/collections/*+*` 等）、AJAX系（`/cart.js`, `/recommendations/products`）。
- Sitemap 行あり: `Sitemap: https://www.endclothing.com/sitemap.xml`
- 冒頭にエージェント向け案内として UCP discovery / UCP・MCP endpoint への参照あり（robots.txt 内に記載された URL: `https://www.endclothing.com/.well-known/ucp`、`https://www.endclothing.com/api/ucp/mcp`）。その利用条件の本文は今回未取得・未確認。

### 3. 日本への直送
- 出典: https://www.endclothing.com/pages/shipping-information
- 日本は配送先表に明記あり。UK倉庫から発送。
  - Standard: ¥2,000 JPY（¥40,000未満）／ 6–8営業日
  - Free: ¥40,000以上で無料 ／ 6–8営業日
  - Express: ¥2,650 JPY ／ 4–5営業日
- 結論: **日本へ直接配送あり**。

### 4. 公式フィード / API / アフィリエイト
- 出典: https://www.endclothing.com/us/affiliate-program
- プログラム名: **END. Affiliate Program**（プラットフォームは **Impact**）。
- 同ページの記載（原文の趣旨）: プロモーション用に「Up-to-date product feeds available」「Product information and imagery available」とあり、参加は Impact 経由の申込が必要。問い合わせ先として affiliates@endclothing.com が記載されている。
- 規約上のデータ利用範囲: 同ページは「promote END. and the products we stock to your site visitors」＝**宣伝・送客目的**の説明のみで、再販目的のデータ利用を認める文言はない。フィードの詳細な利用条件（Impact 側規約）は今回未取得・未確認。
- 上記 2. のとおり robots.txt に UCP/MCP の公式エンドポイント参照もあるが、その利用条件は未確認。

### 5. 商品ページ構造（サンプル1件）
- サンプル: https://www.endclothing.com/products/end-x-adidas-lytham-spzl-sneaker-kj1978
- Shopify ストアフロント。商品名・説明・Style Code（KJ1978）・価格（135.00 GBP）がサーバーレンダリングされたHTML本文として取得できた。
- 価格は Open Graph メタデータ（og:price）でも提供。バリアント（サイズ別 Variant ID 一覧）がページ内データとして抽出できた。JSON-LD の Product スキーマは今回の取得では確認できなかった。

### 判定: **許可待ち（フィード申請等が必要）**
- 理由: 規約に自動収集禁止は確認できず robots は商品パスを Allow するが、公式フィード利用には Impact への申込が必要で、フィード利用条件が未確認のため「許可根拠あり」とは言えない。

---

## 2. HBX（hbx.com）

### 1. 利用規約（スクレイピング禁止の有無）
- 出典: https://hypebeast.com/terms （Hypebeast Hong Kong Limited の Terms & Conditions。本文冒頭で、適用対象サイトに HBX.com が明示されている。更新日: October 25, 2022）
- §8 General Rules of Conduct に自動収集の禁止あり。引用（原文）:
  > "Use any automated or non-automated means to access, copy or distribute any portion of the website or collect any information from the website"
  > "including without limitation, the use of so-called “robots”, “spiders”, “offline readers”, etc."
- 結論: **スクレイピング／スパイダー等による収集を明示禁止**。

### 2. robots.txt
- URL: https://hbx.com/robots.txt
- `User-agent: *` の Disallow はアカウント・ログイン系のみ: `/orders/invoice/`, `/api/v1/login_check`, `/account/`, `/login`, `/profile`, `/register` 等（各言語パス `/jp/`, `/tc/` 等も同様）。
- 商品・カテゴリパスへの Disallow は記載なし。
- Sitemap 行あり（2件）:
  - `Sitemap: https://hbx.com/s3/feed/sitemap.xml`
  - `Sitemap: https://hbx.com/s3/feed/product-sitemap.xml`
- 注意: robots で商品パスが開いていても、上記 1. の利用規約が自動収集を禁止しているため、robots の Allow 相当をもって許可とは扱えない。

### 3. 日本への直送
- 出典: https://hbx.com/delivery
- 配送先として日本が追跡キャリア一覧に明記: 「Japan: FedEx, Crane」。配送業者は住所により FedEx / DHL / SF Express / Yamato / Crane 等。
- 金額: 配送先をプルダウンで選んで見積もる方式で、同ページの静的本文に日本向けの送料額の明記はなし（未確認）。
- 補足出典: https://hbx.com/returns-policy — 返送送料を HBX が負担する対象国に日本が含まれる旨の記載あり。
- 結論: **日本へ直接配送あり**（送料額は同ページでは未確認）。

### 4. 公式フィード / API / アフィリエイト
- 出典: https://hbx.com/affiliates （今回、直接取得が 429 で失敗したため、同ページの検索スニペットで確認した範囲を記録する）
- プログラム名: **HBX affiliates program**。申込は affiliates@hbx.com へのメール申請方式。
- 同ページの記載（スニペット原文の趣旨）: 「Access our product data feed to promote the latest products」＝**最新商品を宣伝するための**プロダクトデータフィードへのアクセスが案内されている。
- 規約上のデータ利用範囲: フィードの目的は promotion（宣伝・送客）と書かれており、再販目的の利用を認める文言はない。アフィリエイト許可は再販許可ではない。
- 一般向けに公開された公式 API の存在は、公式ページでは今回確認できなかった。

### 5. 商品ページ構造（サンプル1件）
- サンプル: https://hbx.com/men/brands/puma/speedcat-mondaysleepingclub-green-terrain-warm-white
- 商品名・説明・Color / Material / Vendor Code（40884501）がサーバーレンダリングされたHTML本文として取得できた。
- **JSON-LD の Product.offers** があり、価格 115 USD / Availability: InStock が構造化データとして提供されている（取得結果に「Source: JSON-LD Product.offers」と明示）。

### 判定: **除外（規約禁止・403等で確認不可）**
- 理由: 利用規約 §8 が robots / spiders 等による情報収集を明示禁止。アフィリエイトフィードは宣伝目的の申請制であり、この禁止を上書きする根拠にはならない。

---

## 3. size?（size.co.uk）

### 1. 利用規約（スクレイピング禁止の有無）
- **未確認**。現行サイト（Shopify へ移行した後の構成）で、一般利用規約（Terms & Conditions）の本文ページを公式サイト内検索・フッターリンクから特定できなかった。
- 移行前のキャッシュ（customer-service 配下のページ、2026-06-03 時点の取得）には Help 一覧に「Terms & Conditions」の項目があったが、その本文 URL と条項（scraping / spider / crawl の禁止の有無）は今回取得できなかった。
- 引用できる条項なし。禁止の有無を断定しない。

### 2. robots.txt
- URL: https://www.size.co.uk/robots.txt
- 冒頭に「we use Shopify as our ecommerce platform」と記載された Shopify 標準構成。
- `User-agent: *` に `Allow: /`（商品・コレクションを含む）。Disallow は `/admin`, `/cart/`, `/checkout`, `/checkouts/`, `/orders`, `/account`、`/cart.js`, `/recommendations/products`、コレクションのソート／フィルタ系など。
- Sitemap 行あり: `Sitemap: https://www.size.co.uk/sitemap.xml`

### 3. 日本への直送
- 出典: https://www.size.co.uk/pages/frequently-asked-questions
  - 国際配送: 「International delivery is available from just £5.00」、発送後 7–21営業日、配送は DPD / Skynet / Pro Carrier。
  - EU 外宛ては輸入時の税・関税を受取人が負担する旨の記載あり。
- 出典（商品ページ共通表記）: https://www.size.co.uk/products/19754965
  - 「International Delivery — International Standard - from £5.00」
- ただし、取得した公式ページ本文の中で**日本が配送先として名指しされている箇所は確認できなかった**。検索スニペット上の旧 FAQ には「We deliver to 115 countries!」という記載があったが、日本の含否は未確認。
- 結論: 国際配送自体はあるが、**日本への直送は未確認**（日本明記なし）。

### 4. 公式フィード / API / アフィリエイト
- 出典: https://www.size.co.uk/customer-service/become-an-affiliate/
- プログラム名: **Become an Affiliate**（size? のアフィリエイト）。「Apply Now」のリンク先は **Awin**（ui.awin.com）。
- 同ページの記載（原文）:
  > "A regularly updated product feed ensures that affiliate's sites can continually display the very latest in-stock products."
- 規約上のデータ利用範囲: フィードの目的はアフィリエイトサイトに最新在庫商品を**表示して送客すること**と書かれており、再販目的の利用を認める文言はない。フィードの詳細条件（Awin 側規約）は今回未取得・未確認。
- 一般向けに公開された公式 API の存在は、公式ページでは今回確認できなかった。

### 5. 商品ページ構造（サンプル1件）
- サンプル: https://www.size.co.uk/products/19754965 （adidas Originals x size? x Billy's 'Japan City Series' Osaka）
- Shopify ストアフロント。商品名・説明・Product Code（794380）・価格（75.00 GBP）・サイズ／在庫（Sold Out 表示含む）がサーバーレンダリングされたHTML本文として取得できた。
- 価格は Open Graph メタデータ（og:price）でも提供。バリアント（Variant ID 一覧）がページ内データとして抽出できた。JSON-LD の Product スキーマは今回の取得では確認できなかった。

### 判定: **除外（規約禁止・403等で確認不可）**
- 理由: robots は商品パスを Allow し申請制フィードも存在するが、肝心の利用規約で自動収集禁止の有無を確認できず、日本への直送の明記も確認できないため、現段階では許可根拠なし＝確認不可として除外扱いにする。

---

## まとめ

| ストア | 判定 | 主な理由 |
|---|---|---|
| END. | 許可待ち | 規約に収集禁止なし・robots は商品を Allow するが、公式フィードは Impact 申請制で利用条件が未確認 |
| HBX | 除外 | 利用規約 §8 が robots / spiders 等による情報収集を明示禁止 |
| size? | 除外 | 現行サイトで利用規約の収集条項を確認できず、日本直送の明記も未確認 |

---

# Group B — Phase-1 Store Verification (Footpatrol / Footshop / SSENSE)

Verified: 2026-11-13 (JST). Method: primary sources only (store's own site, plus the affiliate network page that operates the store's own program where noted). No 403/block was circumvented; where a fact could not be confirmed from a primary page, it is recorded as unverifiable.

---

## 1. Footpatrol — footpatrol.com

### 1) Terms of service — scraping

**Prohibited, explicitly.** Website Terms of Use §9 "NO TEXT OR DATA MINING, OR WEB SCRAPING":

> "you are prohibited from conducting, facilitating, authorising or permitting any text or data mining or web scraping in relation to our Website" (§9.1, ~24 words)

§8.2 also limits downloads to "personal non-commercial use", and §6.1 states the website "is directed to people residing in the UK".

- Source: https://www.footpatrol.com/pages/website-terms-of-use

### 2) robots.txt

- Fetched OK. Header comment: "we use Shopify as our ecommerce platform".
- `User-agent: *`: `Allow: /` generally; product/collection paths allowed (`/products/`, `/collections/`, `/pages/`, `/blogs/` also expressly allowed for `adsbot-google`).
- Disallowed: `/admin`, `/cart/`, `/checkout`, `/checkouts/`, `/orders`, `/account`, `/recommendations/products`, plus collection filter/sort variants (`/collections/*sort_by*`, `/collections/*+*`, `/collections/*filter*&*filter*`) and tracking/preview query params.
- Sitemap line: `Sitemap: https://www.footpatrol.com/sitemap.xml`
- Note: robots.txt allowance does not override the Terms §9 scraping ban above.

- Source: https://www.footpatrol.com/robots.txt (fetched as https://footpatrol.com/robots.txt)

### 3) Shipping to Japan

- **International shipping exists, Japan specifically unverifiable from primary pages fetched.**
- Product pages state: "Standard International Shipping - From £5" and warn that delivery outside the UK "may be charged taxes or duties on import into the destination country".
- Terms of Sale §7.3 likewise refers to additional taxes/custom charges "if you place an order for international delivery". No country list naming Japan was found on a primary delivery page; the standalone Delivery page URL was not discoverable from the fetched primary pages, and Terms of Use §6 directs the site to UK residents.

- Sources: https://www.footpatrol.com/products/760639 ; https://www.footpatrol.com/pages/online-sale-of-goods ; https://www.footpatrol.com/pages/website-terms-of-use

### 4) Official product feed / API / affiliate feed

- **Affiliate feed exists via Awin — for promotion only, not resale/collection permission.**
- Footpatrol's own Cookie Policy lists "AWIN — Tracking for Affiliation". The Awin merchant profile (Footpatrol Affiliate Programme, merchant 5824) states: "A regularly updated product feed ensuring you can show the latest products as soon as they drop", 30-day cookie, commission 5% full-price / 2% voucher-code orders.
- Program terms restrict use to promotion: launch products must not be communicated by affiliates unless communicated by Awin/Footpatrol, and promoting products before launch time results in removal. Nothing in the program terms grants scraping, resale, or reuse of product data on another storefront.

- Sources: https://www.footpatrol.com/pages/cookie-policy ; https://ui.awin.com/merchant-profile/5824?setLocale=it_IT ; https://ui.awin.com/merchant-profile/5824/commission-groups?setLocale=en_US

### 5) Product page structure (sample)

- Sample: HOKA Stinson One7 — https://www.footpatrol.com/products/760639
- Server-rendered HTML (Shopify): title, price (£115.00, was £170.00), size list, description including style code `1168931-SGS` and product code `760639`, delivery/returns blocks all present in fetched HTML text.
- Variants are exposed as a structured variant table (size → Variant ID → Available / Out of stock), consistent with Shopify embedded product/variant JSON. JSON-LD Product markup was **not** confirmed in the fetched text.

### Verdict — Footpatrol: **除外（規約禁止・403等で確認不可）**

Terms §9 expressly prohibits any text/data mining or web scraping for any purpose. The Awin feed is an affiliate-promotion feed and does not override that ban or grant resale/collection rights.

---

## 2. Footshop — footshop.eu

### 1) Terms of service — scraping

**No scraping / spider / crawl / automated-collection prohibition found in the store's Terms and Conditions.** The full Terms (Footshop a.s., effective 1 Nov 2025, sections I–X: purchase contract, user account, delivery, defective performance, final provisions) were read end-to-end (477 lines in fetched text); searches for "scrap" and "automat" returned no matches, and no website-use / data-mining clause appears. This is a purchase-terms document — no separate website Terms of Use stating a collection permission was found either, so there is **no explicit permission**, only an absence of an explicit ban in this document.

- Source: https://www.footshop.eu/en/content/1-terms-conditions

### 2) robots.txt

- Fetched OK (513 lines).
- `User-agent: *`: product and category paths are **not** disallowed. Disallowed are `*/api/*`, `*/graphql/*`, internal paths (`*/config/`, `*/download/`, `*/mails/`, `*/modules/`, `*/translations/`, `*/tools/`, `/internal/pdf/return_label/`, `/cdn-cgi/`, `*/metrics/*`) and sorting/search/pagination query variants (`?orderby=`, `?search_query=`, `?p=`, `&n=`, etc.). Express allowance: `Allow: /*utm_source=CJ` (CJ affiliate traffic).
- Named bots fully blocked (`Disallow: /`): Baiduspider, SemrushBot, DotBot, BLEXBot and others; AhrefsBot / MJ12Bot get `Crawl-delay: 5` plus the standard rules.
- Sitemap lines: `Sitemap: https://sitemaps.footshop.eu/sitemaps/sitemap_6_index.xml` and `Sitemap: https://www.footshop.eu/blog/sitemap_index.xml`

- Source: https://www.footshop.eu/robots.txt (fetched as https://footshop.eu/robots.txt)

### 3) Shipping to Japan

- **Ships outside the EU by zone; Japan-specific price unverifiable, and a major brand restriction applies.**
- Product pages carry a zone shipping table: Asia "From €25.50" (Europe from €0.47, Americas from €29.58, Oceania from €48.96, Africa from €60.18). Japan is not named separately; the dedicated Delivery page is country-dynamic (the fetched render defaulted to Afghanistan, DHL Express Worldwide €61), so a Japan-specific fee/time could not be isolated from primary pages in this pass.
- Official FAQ states: "Items shipped outside of the EU may be required to pay additional tax in the country of delivery" — and critically: **"Due to Nike's new policy, we do not ship Nike and Jordan products outside of the European Union. Exceptions are Switzerland and the United Kingdom."** That exclusion covers Japan for Nike/Jordan.

- Sources: https://www.footshop.eu/en/delivery ; https://www.footshop.eu/en/mens-shoes/34653-air-jordan-1-mid-black-dark-concord-white.html ; https://www.footshop.com/en/faq

### 4) Official product feed / API / affiliate feed

- **Affiliate program exists via CJ (Commission Junction) — application required; product XML feed is gated by manual approval.**
- Footshop's own affiliate page: "Register in the CJ affiliate network", commission "up to 8% of the purchase value", purpose as written is earning commission "from the purchases of all customers you refer to us through sharing our affiliate links or banners" on your site/blog/social media. The page does not itself offer a public feed or API.
- The CJ program listing via VIVnetworks (CJ partner manager) states: "The XML feed: Only partners in the Google_Shopping_Access group will have access to the XML feed. Inclusion in the group is subject to manual approval by the advertiser and access to the group must be requested by CJ message or email." Terms as written cover affiliate promotion / Google Shopping access — not resale permission.

- Sources: https://www.footshop.com/en/content/33-affiliate-programme ; https://www.vivnetworks.com/en/affiliate-catalog/footshopsi/ ; https://www.vivnetworks.com/en/affiliate-katalog/footshopeu/

### 5) Product page structure (sample)

- Sample: Air Jordan 1 Mid Black/Dark Concord-White (554724-051) — https://www.footshop.eu/en/mens-shoes/34653-air-jordan-1-mid-black-dark-concord-white.html
- Server-rendered HTML: title with style code in the URL/title, price (€137.95 VAT incl), colour options, materials, Details block with `Reference 554724-051`, producer name/address, image URLs on `static.ftshp.digital`, and the zone shipping table — all present in fetched HTML text.
- JSON-LD Product Offer markup was **not** labelled/confirmed in the fetched text; robots.txt blocks the site's own `*/api/*` and `*/graphql/*` endpoints.

### Verdict — Footshop: **許可待ち（フィード申請等が必要）**

No scraping ban was found in its Terms and robots.txt does not block product/category paths for `*`, but there is also no explicit collection permission. The only official data route (CJ XML feed) requires CJ registration plus manual advertiser approval for the Google_Shopping_Access group — do not collect until that approval (and its data-use scope) is obtained. Nike/Jordan cannot be shipped to Japan in any case.

---

## 3. SSENSE — ssense.com

### 1) Terms of service — scraping

**Prohibited, explicitly.** General Terms and Conditions (last updated Feb 14, 2026), §8 Restricted Conduct:

> "Engage in or use any data mining, robots, scraping, or similar data gathering or extraction methods on or via the Services" (§8, ~20 words)

§5.2 additionally limits Site Content to a personal, non-commercial licence and bars reproducing/distributing content "for any commercial purpose whatsoever, without the prior written permission of SSENSE".

- Sources: https://www.ssense.com/en-us/terms-conditions ; (same clause) https://www.ssense.com/en-in/terms-conditions

### 2) robots.txt

- Fetched OK (2,193 lines).
- `User-agent: *`: product paths are not blanket-disallowed, but many paths/queries are: `/api/`, `/feeds/`, `/export/`, `/checkout`, `/account/`, `/wishlist`, `/shopping-bag`, `/editorial/queryProduct/`, and query variants `/*?isAjax=*`, `/*?size=*`, `/*?page=*`, `/*?q=*`, `/*?sort=*`, `/*?brands=*`, `/*?categories=*`, `/*?sizes=*`, `/*?colors=*`, etc. Hundreds of locale-country combinations (e.g. `/fr-jp`, `/ja-*`, `/zh-*` variants) are also disallowed.
- Sitemap lines: `Sitemap: https://www.ssense.com/sitemap.xml`, `https://www.ssense.com/sitemap_image.xml`, plus `sitemap_cn.xml`, `sitemap_cn_image.xml`, `sitemap_kr.xml`, `sitemap_kr_image.xml`.
- Note: robots.txt allowance does not override the Terms §8 scraping ban above.

- Source: https://www.ssense.com/robots.txt

### 3) Shipping to Japan

- **Yes — Japan is an explicitly listed direct-shipping destination.**
- Shipping & Handling (Japan locale page): "We ship to over 40 countries with duties and taxes included… shipped DDP (Delivered Duty Paid)."
- Japan row: **Express (2–5 days); free-shipping threshold ¥35,000; shipping fee below threshold ¥2,750.** Product pages for Japan repeat "Japan: Free shipping on orders over ¥35000 JPY and free returns on all orders" (some pages show a ¥57,000 "Other orders" threshold in the table).

- Source: https://www.ssense.com/en-jp/customer-service/shipping

### 4) Official product feed / API / affiliate feed

- **Affiliate program exists — application by email, promotion-only role as written; no public API/feed terms granting collection or resale.**
- SSENSE's own Affiliates page invites "established websites, blogs, influencers and personal stylists" to apply by emailing affiliates@ssense.com (name, email, website/social URL; review within one week). Benefits listed: competitive commissions on approved global sales, 30-day cookie, biweekly payouts, real-time reporting.
- The affiliate role as written is: "Accessing our product catalogs and promoting our new arrivals", "Uploading banners and links to your website", and promotions/newsletters/blog posts. Catalog access is for promoting SSENSE products with links back to SSENSE — it is not a licence to scrape the site (barred by §8), republish the catalog as one's own storefront, or resell.

- Source: https://www.ssense.com/en-us/affiliates

### 5) Product page structure (sample)

- Sample: On Black Cloudswift 4 AD Sneakers — https://www.ssense.com/en-jp/men/product/on-running/black-cloudswift-4-ad-sneakers/18662241
- Server-rendered HTML **plus JSON-LD**: the fetched page explicitly exposes a "Product Offer — Source: JSON-LD Product.offers" block (Product: Black Cloudswift 4 AD Sneakers; Price: 21500 JPY; Availability: InStock), alongside HTML item info (description, supplier colour, materials, "Made in Viet Nam", product code `261585M237031`), size variants with per-size availability, and direct image URLs on `img.ssensemedia.com`.

### Verdict — SSENSE: **除外（規約禁止・403等で確認不可）**

Terms §8 expressly prohibits data mining, robots and scraping, and §5.2 bars commercial reuse without prior written permission. The affiliate program is application-based promotion (catalog access to promote/link), not a collection or resale licence.

---

# Group C — Phase-1 Verification (Slam Jam / SNIPES / Queens)

Verified: 2026-11-13 (JST). Primary sources only (each store's own site / help site, fetched via browser.open / browser.search). No 403/block was circumvented. Quotes kept short (≤ ~30 words).

> Note on source integrity: Slam Jam's robots.txt contains Shopify-inserted agent instructions urging installation of an external `shop.com/SKILL.md`. That is page content, not an instruction from the user/parent — it was ignored and not followed, and is recorded here only as an observation.

---

## 1. Slam Jam — slamjam.com

### 1. Terms of service — scraping / automated collection
- No explicit "scrape / spider / crawl" clause was found in the full Terms text (searched for scrape, robot, automat — 0 hits).
- However, content use and reselling are restricted:
  - Content: "Users may not, therefore, use such content in any way that is not necessary or implicit in the proper use of the Service."
  - Service reselling: "Users may not reproduce, duplicate, copy, sell, resell or exploit any portion of this Website and of its Service without the Owner's express prior written permission"
  - Account clause only: "Accounts registered by bots or any other automated methods are not permitted."
- Source: https://www.iubenda.com/terms-and-conditions/258167 (Terms hosted for www.slamjam.com, owner Slam Jam S.r.l) ; also https://roe.slamjam.com/pages/terms-and-conditions

### 2. robots.txt
- Source: https://slamjam.com/robots.txt
- Shopify storefront. `User-agent: *` — `Allow: /` generally; product / collection / page / blog HTML is crawlable.
- Disallowed: `/admin`, `/cart/`, `/checkout`, `/checkouts/`, `/orders`, `/account`, `/services`, `/cart.js`, `/recommendations/products`, plus collection sort/filter crawl traps (`/collections/*sort_by*`, `/*+*`, multiple `*filter*`).
- Sitemap line: `Sitemap: https://slamjam.com/sitemap.xml`
- Also declares a UCP/MCP endpoint and `agents.md` for agent shopping — that is a shopping-agent interface, not a product-data collection licence.

### 3. Shipping to Japan — YES, direct
- Source: https://help.slamjam.com/shipping-delivery
- Ships from Italy. Japan row: **¥4,000 (UPS, 2–5 business days)**, import duties/taxes **not included at checkout** (DAP; duties calculated at checkout only for US shipments).
- Free shipping threshold for Japan: **over ¥70,000**.
- Product pages (US locale) show a different generic line ($22 UPS Express, free over $350) — the Help Center country table above is the Japan-specific primary source.

### 4. Official product feed / API / affiliate feed
- Program: **Slam Jam Affiliate Program** — apply by email to affiliates@slamjam.com with website/blog/social profile and main markets; review within one week.
- Feed existence (as written on the store's own affiliates page): "use our up-to-date product feed to display the latest products", "Data feed updated multiple times per day", "Custom data feed available upon request".
- Terms as written are about **linking and commission only**: place text links/banners provided by Slam Jam, commission on valid sales excl. shipping/VAT/returns, 45-day cookie, no bidding on the Slam Jam brand name or product names, Slam Jam may exclude products and may end the relationship at any time. **Nothing in these terms grants resale rights or a general right to copy/reuse product data outside affiliate display.**
- Source: https://slamjam.com/en-us/pages/affiliates

### 5. Product page structure (sample)
- Sample: https://slamjam.com/en-us/products/undercover-footwear-sneakers-green-j299164
- Shopify. Product name, price ($266.00 USD, was $591.00), colour, sizes, details and style code (UC2D9F02 2) are present in **server-rendered HTML** as returned by text fetch.
- Price/availability were also surfaced from **Open Graph metadata** (og:price:amount / og:price:currency; Availability: InStock) and a variant table with Variant IDs was present. JSON-LD presence was **not confirmed** from the extracted text.

### Verdict — 許可待ち（フィード申請等が必要）
Direct scraping has no permission basis (copy/resell/exploit requires prior written permission), but an official affiliate product feed exists. Do not collect until the affiliate application is approved and the feed is used under its terms.

---

## 2. SNIPES — snipes.com

### 1. Terms of service — scraping / automated collection
- EU sales GTC for snipes.com (SNIPES SE, Cologne): **no scrape/spider/crawl/automated-collection clause was found** in the fetched full text (searched for scrap — 0 hits). It is a sales contract (prices, withdrawal, raffle), not a website-use licence, so it gives no collection permission either.
  - Source: https://prd.snipes.com/en-eu/s/termsandconditions
- The brand's website Terms of Use (SNIPES USA, separate domain/entity — recorded for risk, not conflated with the EU GTC) **explicitly prohibit** automated access:
  - "Use any robot, spider or other automatic device, process or means to access the Site for any purpose, including monitoring or copying any of the materials on the Site"
  - Source: https://www.snipesusa.com/terms-of-use.html (§7 Security and Restrictions, effective 2026-02-19)

### 2. robots.txt
- Source: https://www.snipes.com/robots.txt
- `User-agent: *` — Disallow: `/login`, `/wishlist`, `/cart`, `/api`, `*/undefined`, and parameter pages (`/*?prices=`, `/*?color=`, `/*?size=`, `/*?sale=`, `/*?filters[...]`, `/*?sort=...`). Product and category paths themselves are **not** disallowed.
- Sitemap lines (EU locales only): e.g. `https://www.snipes.com/de-de/de-de-sitemap-index.xml`, de-at, de-ch, pl-pl, nl-nl, nl-be, fr-fr, fr-ch, fr-be, pt-pt, es-es, hr-hr, it-it.

### 3. Shipping to Japan — NO evidence of direct shipping
- Source: https://prd.snipes.com/en-eu/s/termsandconditions (Prices & Shipping)
- "Shipping costs are charged additionally only for orders below €59.99. From an order value of €60, shipping is free of charge." Product pages state DHL delivery in 1–3 / 1–4 business days, free over €60.
- The storefront/sitemap locales are EU countries only; **no Japan (or any non-EU) shipping destination, cost, or timeframe was found on snipes.com primary pages.** Japan direct shipping is therefore not confirmed / treated as unavailable.

### 4. Official product feed / API / affiliate feed
- On snipes.com primary pages, **no official product feed/API or EU affiliate terms were found.**
- Third-party (non-primary, for reference only, terms not verified): an Awin listing "Snipes EU Partnerprogramm" (contact affiliate@snipes.com, European countries) — https://ui.awin.com/merchant-profile/122628 ; SNIPES USA runs a separate affiliate program at https://www.snipesusa.com/affiliates.html for snipesusa.com links.
- Because neither is a snipes.com primary source with data-use terms, feed permission for snipes.com is **unverified**. Affiliate linking permission, even if granted via Awin, is not resale permission.

### 5. Product page structure (sample)
- Sample: https://www.snipes.com/en-eu/p/adidas-originals-japan-w-sneaker-black-47881
- Product data is in **server-rendered HTML** as returned by text fetch: price (€40.00, was €119.99, incl. VAT), sold-out status, description, features, and structured fields — Gender: Women, Product type: Fashion Sneakers, Article number: 11680310, Product code: 02483523, manufacturer information, material/care.
- No JSON-LD or embedded JSON block was visible in the extracted text.

### Verdict — 除外（規約禁止・403等で確認不可）
No collection permission can be confirmed from snipes.com primary sources, the only SNIPES website-use terms found (USA) expressly ban robot/spider copying, and there is no Japan shipping. Exclude from collection; revisit only with written permission / verified Awin feed terms for snipes.com specifically.

---

## 3. Queens — queens.global

Operator: Footshop a.s., Prague (Queens has been part of the Footshop family since 2021).

### 1. Terms of service — scraping / automated collection
- Full Terms and Conditions (effective 2025-11-01) were read end-to-end (sections I–XI): **no scrape / spider / crawl / automated data-collection prohibition was found** (searched for scrap — 0 hits), and no general website-content copying licence was found either. Section VIII ("Other rights and obligations") contains no data-use clause.
- Source: https://www.queens.global/en/content/1-terms-conditions

### 2. robots.txt
- Source: https://www.queens.global/robots.txt
- `User-Agent: *` — Disallow: `*/api/*`, `*/graphql/*`, sorting/search/pagination parameters (`/*?orderby=`, `/*?search_query=`, `/*?p=`, `/*&n=` etc.), `*/config/`, `*/download/`, `*/mails/`, `*/modules/`, `*/translations/`, `*/tools/`, `*?ajax=`, `/cdn-cgi/`, `*/metrics/*`. Product and category paths themselves are **not** disallowed.
- Allow includes `*/download/sitemaps/*` and notably `Allow: /*utm_source=CJ` (consistent with the CJ affiliate program below).
- Named bad bots (Baiduspider, SemrushBot, DotBot, etc.) get `Disallow: /`; AhrefsBot/MJ12Bot get crawl-delay 5.
- Sitemap line: `Sitemap: https://sitemaps.queens.global/sitemaps/sitemap_6_index.xml`

### 3. Shipping to Japan — Asia zone offered; Japan-specific price unverifiable in text fetch
- Delivery page is a per-country selector; the text fetch renders only the first country (Afghanistan: DHL Express Worldwide – Zone 5, €60). A Japan-specific row could not be extracted — recorded as unverifiable, not as absent.
  - Source: https://www.queens.global/en/delivery
- Product-page shipping table (primary, see §5 sample) gives zone pricing: **Asia — from €24.00**, Europe from €0.47, Americas from €60, Africa from €60, Oceania from €39. Japan falls in the Asia zone as presented, but is not named on that page.
- FAQ (primary): "Items shipped outside of the EU may be required to pay additional tax in the country of delivery" and an important restriction: "Due to Nike's new policy, we do not ship Nike and Jordan products outside of the European Union. Exceptions are Switzerland and the United Kingdom."
  - Source: http://www.queens.global/en/faq

### 4. Official product feed / API / affiliate feed
- Program: **Queens.global Affiliate Program via CJ** — Queens' own affiliate page states: register in the CJ affiliate network, place Queens tracking links/banners on your site/blog/social media, up to **8% commission** on purchase value (typical $6–$30), regular monthly payouts, individual conditions negotiable, contact affiliate@queens.cz.
  - Source (Queens regional primary site, page is for Queens.global): https://www.queens.hu/en/content/33-affiliate-programme
- Terms as written cover **banners/tracking links and commission only — no resale permission, and the primary page does not itself mention a product feed.**
- A product feed for "Queens Global" via CJ is listed by a third-party tool site (non-primary, terms not verified): https://www.affiliate-toolkit.com/program/queens-global/ ("Product feed? Available", 8%, 14-day cookie, PPC ads not allowed). Feed existence/terms must be confirmed inside CJ after application before any use.

### 5. Product page structure (sample)
- Sample: https://www.queens.global/en/mens-shoes/171910-birkenstock-boston-bs-mocha.html
- PrestaShop-style storefront (URL pattern, `*/modules/` in robots). Product data is in **server-rendered HTML** as returned by text fetch: name, price (€148.49 VAT incl., was €165.00, −10%), description, materials (upper/footbed/sole), **Reference: 660461**, producer name/address, and the zone shipping table quoted in §3.
- No JSON-LD or embedded JSON block was visible in the extracted text.

### Verdict — 許可待ち（フィード申請等が必要）
No scraping prohibition in the Terms and robots allows product/category paths, but there is also no permission basis for direct collection. The legitimate route is CJ affiliate registration; collect only via the CJ feed, and only after confirming its data-use terms inside CJ. Note the Nike/Jordan non-EU shipping restriction for any Japan-facing use.

---

## Summary

| Store | Verdict | One-line reason |
|---|---|---|
| Slam Jam (slamjam.com) | 許可待ち | No scraping ban, but copy/resell needs prior written permission; official affiliate product feed exists — apply first. Japan shipping ¥4,000 / free over ¥70,000. |
| SNIPES (snipes.com) | 除外 | No permission/feed confirmed from snipes.com primary sources, SNIPES website Terms of Use ban robot/spider copying, and no Japan shipping (EU locales only). |
| Queens (queens.global) | 許可待ち | No scraping ban and robots allows products, but no direct-collection permission; CJ affiliate (≤8%) is the route — feed terms must be confirmed in CJ. Asia shipping from €24; Nike/Jordan not shipped outside EU. |

---

# Group D — Store Verification (Phase 1)

Verified: 2026-11-13. Method: primary sources only (each store's own site pages, fetched via browser.open / browser.search). No 403/block was circumvented; blocks are recorded as unverifiable. Affiliate-network listings are labelled as such where the store's own site carries no feed page.

---

## 1. JD Sports — jdsports.com (US storefront, operated by The Finish Line, Inc. d/b/a JD Sports)

### 1. Terms of service — scraping / automated collection: **PROHIBITED**

Terms of Use (updated March 2024), Section D "Use Restrictions". The user agrees not to:

> "use any automatic device, process or means to access the Site for any purpose, including monitoring or copying any of the Site Content"

Same section also bans commercial use:

> "use the Site for any commercial purposes (including, without limitation, for the purposes of advertising, soliciting funds, collecting product prices and selling products)"

Section C additionally states Site Content may not be copied/reproduced/distributed without prior written consent, and grants only a personal, non-commercial licence.

- Source: https://www.jdsports.com/terms-of-use

### 2. robots.txt

Fetched in full. For `User-agent: *` (and an equivalent named-bot group):

- Disallow: `/search?query=*`, `/cart`, `/checkout*`, `/account*`, `/myaccount/`, `*sort*=*`, `*filter*=*`, `*utm_*`, `*mnid=*`, `*icid=*`, `*lid=*`, `/undefined*`, `/write-a-review*`, `/catalog/_next/image`
- Allow: `/login`, `/resetPassword`, `/register`
- Product (`/pdp/…`) and category (`/plp/…`) paths are **not** disallowed in themselves (only their sort/filter/tracking query variants are).
- `archive.org_bot` is fully disallowed (`Disallow: /`); `Pinterestbot` has Crawl-delay: 1.
- Sitemap line: `Sitemap: https://www.jdsports.com/index.xml`

Note: robots.txt being permissive does **not** override the Terms of Use prohibition in item 1.

- Source: https://www.jdsports.com/robots.txt

### 3. Shipping to Japan — **No (US site does not ship internationally)**

JD's own shipping terms on jdsports.com state orders are deliverable to U.S. residential/commercial addresses only, and:

> "Orders may not be shipped to Puerto Rico, Guam, APO/FPO Boxes or international addresses."

Pricing stated on the same page: free standard shipping on orders over $75; $9.99 flat rate on orders of $75 or less. Japan is therefore not served by jdsports.com directly. (Separate storefronts such as global.jdsports.com advertise delivery to 180+ countries, but that is a different storefront from the one under verification.)

- Source: https://www.jdsports.com/coupon-exclusions?icid=SC_GL_UMB_UMB1_ShippingDetails_TXT_undefined

### 4. Official product feed / API / affiliate feed

- No public product API or open data feed was found on jdsports.com itself.
- An affiliate product feed exists through affiliate networks. The Awin merchant profile for JD Sports (Sweden programme shown) states:

> "A product feed that is regularly updated, showing you the latest products as soon as they are available"

  with a 30-day cookie period; some products are excluded from commission. JD programmes also appear on other networks (e.g. Sovrn Commerce) per network listings.
- Terms as written: the feed is an **affiliate promotion** tool (publishers promote JD products and earn commission on referred sales). Nothing in the public programme description grants scraping rights, catalogue reuse outside affiliate promotion, or any resale permission. Full feed data-use terms are only available inside the network after joining/approval — not publicly retrievable in this pass.

- Sources: https://ui.awin.com/merchant-profile/8841?setLocale=de_DE ; https://merchants.sovrn.com/merchants/25055/jd-sports-affiliate-program

### 5. Product page structure (sample)

Sample PDP fetched: "Men's Nike LeBron Witness 9 Basketball Shoes" — price $105.00, product features and description present in the fetched (server-rendered) page text. The page also carries structured data: the extraction layer reports a **JSON-LD `Product.offers`** block (Product / Price: 105.00 USD / Availability: InStock). Product data is therefore available in HTML + JSON-LD — technically easy to parse, but see the Terms prohibition in item 1.

- Source: https://www.jdsports.com/pdp/nike-lebron-witness-9-basketball-shoes/prod1010134/II7520/100

### Verdict: **除外（規約禁止）**

The store's own Terms of Use explicitly prohibit automatic access/monitoring/copying and commercial use including collecting product prices. robots.txt does not rescue this. The only sanctioned data channel is the affiliate feed, whose terms cover affiliate promotion only.

---

## 2. Shooos — shooos.com (operator: Shooos s.r.o., Bratislava, Slovakia)

### 1. Terms of service — scraping clause: **未確認 (could not be verified on shooos.com)**

- Multiple searches of shooos.com returned only product/category pages; no Terms page on the .com domain could be located or fetched in this pass, so **no scraping/spider/crawl clause can be quoted for shooos.com**.
- The operator's own privacy page (same company, Shooos s.r.o.) states that services are governed by a separate document, "General Business Terms and Conditions", covering "websites under Shooos domains (.hu/.ro/.at/.de etc)", but the full text of that document was not retrievable from shooos.com in this pass. Its data-use/scraping wording therefore remains unverified — it must be confirmed before any collection, e.g. at affiliate application.

- Sources: https://www.shooos.ie/page/cookies (operator's privacy page referencing the General Business Terms and Conditions); shooos.com site searches (product pages only)

### 2. robots.txt

Fetched in full for `User-agent: *`:

- `Crawl-delay: 10`
- Allow: `/static/`, `/media/`, `/_next/image`, `/_next/static`, `/*?p=`, `/*?currency=`, and at the end `/*?page=`, `/*?currency=`, `/*?shoeSize=`
- Disallow (directories): `/app/`, `/cgi-bin/`, `/downloader/`, `/errors/`, `/includes/`, `/magento/`, `/media/xmlFeedExport/`, `/pkginfo/`, `/report/`, `/scripts/`, `/shell/`, `/stats/`, `/var/`, `/control/`, `/contacts/`, `/customer/`, `/customize/`, `/newsletter/`, `/poll/`, `/review/`, `/sendfriend/`, `/tag/`, `/wishlist/`, `/shopby/`
- Disallow (catalogue, legacy Magento paths): `/catalog/product_compare/`, `/catalog/category/view/`, `/catalog/product/view/`, `/catalogsearch/`, `/catalog/product/gallery/`, **`/catalog/`** (blanket)
- Disallow (generic): `/*.php$`, **`/*?*`** (any query-string URL, subject to the Allow exceptions above), `/*SID=`, `/index.php/`, `/category/*,*`, `/onestepcheckout/`
- Sitemap line: `Sitemap: https://www.shooos.com/sitemap.xml`
  - Note: fetching that sitemap URL returned a Cloudflare "Attention Required!" block page in the crawler cache; the block was **not** circumvented. The sitemap's existence is taken from robots.txt itself.

Interpretation: clean product URLs (e.g. `/product/…`, `/<slug>`) are not literally listed, but the blanket `/catalog/` ban, the `/*?*` query ban, and Crawl-delay 10 make ordinary site crawling heavily constrained. The sanctioned route is the affiliate feed (item 4).

- Source: https://shooos.com/robots.txt

### 3. Shipping to Japan — **未確認 (no direct Japan shipping confirmed on primary sources)**

- No shipping/delivery policy page for shooos.com could be located via site search in this pass, and no Japan delivery terms (regions/cost) could be quoted from the store's own pages.
- Context from the operator's own pages: Shooos s.r.o. runs country storefronts under EU domains (.sk/.cz/.hu/.ro/.at/.de/.ie/.nl/.it/.pl/.co.uk etc.); the .com storefront prices in USD. The operator's return page (shooos.ie) is built around EU consumer rules (14-day withdrawal, returns to a Slovak address / DHL label) — an EU-centric operation. No Japan storefront or Japan delivery offer was found.

- Sources: https://www.shooos.ie/page/cookies ; https://www.shooos.ie/page/return ; https://www.shooos.com/ (USD pricing, homepage)

### 4. Official product feed / API / affiliate feed — **Exists (affiliate XML/CSV feed, application required)**

- Shooos runs an affiliate programme via **CJ / VIVnetworks**. The network's programme listing for Shooos states "XML Feed: ✅" and gives programme terms by publisher type:
  - Content portals: 5–12% commission, 30-day cookies
  - Cashback and discount portals: 3–8%, 3-day cookies
  - **Catalogs and price comparators: 4–9% commission, 7-day cookies**
  - Prohibited: SEM on brand, and direct domain redirection
- Affiliate tooling documentation for the same programme describes joining at CJ, then importing products via the feed ("Product feed: Available"; CSV Feed module; import and display in boxes, lists, comparison tables and price comparison).
- Terms as written: this is an **affiliate** programme — the feed may be used by approved publishers, expressly including catalogue / price-comparison sites, to promote Shooos products for commission. It is **not** a resale permission, and the detailed data-use licence is only issued inside CJ after application/approval. Contact given in the programme text: podpora@shooos.com / vivnetworks.com.

- Sources: https://www.vivnetworks.com/hr/affiliate-katalog/shooos-com/ ; https://www.affiliate-toolkit.com/program/shooos/
- Note: no feed/API page was found on shooos.com itself; the above are the programme's official network listings.

### 5. Product page structure (sample)

Sample PDP fetched: "adidas Superstar" — 144 USD, "lowest price in the last 30 days: 115.2 USD", Details block in page text (SKU: EG4957, Gender: Men, Color: Black, Category: Sneakers, Model: adidas Superstar), full description and size chart in the fetched text, i.e. product data is present in server-rendered HTML. Other Shooos PDPs in search results expose a structured **Product Offer** block (Product / Price / Availability, e.g. OutOfStock), indicating embedded structured data (JSON-LD/microdata-style offers) alongside the HTML.

- Source: https://www.shooos.com/product/adidas-superstar-eg4957

### Verdict: **許可待ち（フィード申請等が必要）**

No scraping prohibition could be confirmed on shooos.com (Terms text unverifiable in this pass — to be confirmed at application), and robots.txt heavily restricts direct crawling. However, an official affiliate XML/CSV product feed exists whose programme terms expressly include catalogue / price-comparison use. Collection should proceed **only** via that feed after CJ/VIVnetworks application and approval, not via scraping. Japan direct shipping is unverified on primary sources.

---

## Summary

| Store | Verdict | Key reason |
|---|---|---|
| JD Sports (jdsports.com) | 除外 | Terms of Use §D explicitly bans automatic access/copying and commercial price collection; US site does not ship to Japan |
| Shooos (shooos.com) | 許可待ち | Official CJ/VIVnetworks affiliate XML feed exists with a "Catalogs and price comparators" category, but joining/approval is required; Terms scraping clause and Japan shipping unverified on shooos.com |

---

