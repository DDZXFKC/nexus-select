# iMac 実サイト接続検証 結果（2026-11-12）

実施環境：NORIHIROのiMac（macOS 15.8.2）／Python 3.9.6／Git 2.39.5（いずれも CLT 付属）。
実行経路：Mac には直接のシェルがないため、Local（kaitsuke-shop）の PHP ハーネスから
`/usr/bin/python3` を起動する実証済みの経路を使用。スクリプトは Python 標準ライブラリのみ。
販売サイトの商品データ・既存データは変更していない。

## 1. 接続検証（iMac の Python から実測）

| ショップ | DNS | HTTPS | robots.txt |
|---|---|---|---|
| BSTN (www.bstn.com) | OK（18.238.238.110） | 200（/eu_en へリダイレクト） | 200（1,623 B） |
| Foot Locker (www.footlocker.com) | OK（151.101.90.132） | 200 | 200（1,050 B） |
| Zalando (www.zalando.de) | OK（92.123.135.68） | **403 Forbidden** | **403**（本文はエラーページ） |

- チャッピー側環境で発生した DNS 名前解決エラーは、iMac でも Muse の VM でも再現しなかった。
  障害はテストを実行した環境側のネットワーク制限とみられる。
- Zalando は DNS は引けるが HTTP 層で遮断。Muse の VM からも 403 で、環境を変えても同じ結果。

## 2. robots.txt と利用規約の判定

- **BSTN**：robots.txt は商品ページを禁止していない（禁止は /api/ /checkout/ /customer/ /catalogsearch/ 等）。
  商品サイトマップも公開されている。利用規約（AGB §§1–13）でボット禁止が明記されているのは
  「In-App Chases（購入・ラッフル）への技術的補助」についてのみで、商品ページの読み取り・
  データ抽出の禁止条項は確認できなかった。→ **低頻度での商品ページ取得は可と判断**（購入系の自動化は不可）。
- **Foot Locker**：robots.txt は商品ページを禁止していないが、利用規約（USE OF SERVICES）が
  「robot / bot / spider / scraper 等の自動手段によるページ・データ・コンテンツの監視・コピーを、
  事前の書面許可なく禁止」と明示。→ **自動収集は行わない**（技術的には 200 で接続可）。
- **Zalando**：robots.txt 自体が 403 で取得できず、自動取得の可否を確認できない。
  オーナールール「確認できない場合は収集しない」に従い **自動収集は行わない**。

## 3. 実データ取得（BSTN・1商品のみ検証）

- BSTN 公式サイトマップ（media.bstn.com/sitemap/eu_en/）→ 子サイトマップ 41件、
  その1件に URL 1,920件。実商品ページを1件だけ取得：
  `https://www.bstn.com/eu_en/p/adidas-adilette-280647-0009238`（200、583,398 B、JSON-LD 1件）。
  保存 HTML は同フォルダの `bstn_product.html`。
- `collector.py` で **13行**（サイズ別）を抽出 → `candidates.csv`：
  brand=Adidas / sku=0009238 / name=ADILETTE SLIDES / price=27.99 EUR /
  size=37 EU〜（13サイズ）/ availability_claim=InStock（サイズ別）。
- 全行 gate=**HOLD**、auto_publish=**disabled**。hold_reasons：
  `COLOR_MISSING`（この商品の JSON-LD に色フィールドなし）＋
  `SIZE_STOCK_REQUIRES_MANUAL_CONFIRMATION`（設計上常時付与）。
- サイズ別在庫について：JSON-LD の availability はページ側の申告値であり、
  実際にサイズを選択して確認した在庫ではない。**UNVERIFIED として扱い、HOLD を維持**する（コードの設計通り）。
- 型番の注意：sku=0009238 は BSTN の店舗商品番号。メーカー型番（adidas のスタイルコード）は
  この JSON-LD の sku には含まれていない。マスター登録時は型番の出所を別途確認すること。

## 4. SQLite 保存と CSV 出力

- collector の出力CSV（13行）を SQLite（nexus_collect.db、テーブル candidates）へ投入し、
  読み戻し件数 13・gate は HOLD のみ、を確認。チェーン「実ページ → パーサ → CSV → SQLite」は成立。
- DB 本体は転送制限（.db のアップロード不可）で本フォルダ未収載。内容は candidates.csv と同一。
- このブランチの collector.py 自体に SQLite 層はない（v3 統合版は ChatGPT 共有 ZIP 側）。
  今回の SQLite は検証用の最小シンク（fetch_and_store.py 内）である。

## 5. 単体テスト（iMac 上）

- `python3 -m unittest -v test_collector.py` → **10件すべて OK**（unittest-imac.txt）。

## 6. 作業中の付随事項

- 作業開始時、Local の Live Link が全パス 404 を返す障害が発生。Live Link の作り直しでは直らず、
  **サイトの停止→開始で復旧**した（Live Link の URL・認証情報は従来通り lyrical-tooth.localsite.io）。
- 検証用の一時ファイルはサイトのルートに置いたが、検証完了後にすべて撤去済み。

## 収載ファイル

- probe_conn.py（接続検証スクリプト、research/online/ 直下）
- fetch_and_store.py（サイトマップ→取得→解析→CSV→SQLite の検証スクリプト、同上）
- probe-report.json（接続検証の生結果）／fetch-report.json（抽出の生結果）
- candidates.csv（抽出13行）／bstn_product.html（取得した実ページ）
- robots-bstn.txt／robots-footlocker.txt（取得時点のスナップショット）
- unittest-imac.txt（iMac 上のテスト結果）
