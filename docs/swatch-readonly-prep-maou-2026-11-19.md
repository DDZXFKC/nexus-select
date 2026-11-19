# 丸窓Local接続 読み取り専用 並行作業の結果（魔王）

- 実施: 2026-11-19（JST）、Local（kaitsuke-shop.local）のみ読み取り専用。Localへの書き込みは0件。
- GPT検収 5dc4c1b5 で魔王担当とされた3件（market照合、fixture選定、テーマ差分）の結果。

## 1. LocalのSP商品と market 照合

- LocalのSP商品は **158点、全て publish、下書きは0点**（`wp eval-file` 読み取りプローブ、EXIT=0）。
- SP商品のメタは標準Wooキー（_sku、_price、_stock 等）と _nx_catnav_needs_review、_product_image_gallery のみ。**market／source／shop／supplier を含むメタは全点で存在しない**。
- つまり「Local側の仕入先market根拠」は商品メタには無い。Local側で仕入先を示すのは SKU接頭辞 `SP-` だけであり、GPTゲート（SKUのみで別marketを採用しない）に照らすと、writer の検証済み明示mappingは「SP → Shoe Palace（shop_code=SP）」を明示mappingとして承認する形でしか成立しない。判断はGPT検収に委ねる。
- CSV側（最新スナップショット変換、color_woo_export.py 39ffb242版）：全24,320行が shop_code=SP、market=US。Localの158点は全点CSVに存在し、構成色行は228行（CONFIRMED 196／UNKNOWN 30／HOLD 2）。

## 2. fixture選定（pick_swatch_fixtures.py、39ffb242版）

- 入力： out2/woo_components.csv（CONFIRMED 10,621／UNKNOWN 1,153／HOLD 3／構成なし21、前回と同数）＋ Local SP 158点の status 付き一覧。
- 結果： **Localの下書きSP商品が0点のため、初回fixtureに使える既存Local商品は無い**。9観点すべて FX-SP 下書きfixtureの作成が必要（picker の fixtures_out 出力どおり）。
  - 1色： 4631241949230（Grey）
  - 2色： 4631211606062（White/Black）
  - 3色： 4646574424110（Black/Grey/Red）
  - 4色以上： 6854640107726（Wheat/White/Pollen/Gum Light Brown）
  - 同色反復： 4631372562478（Black/Black）
  - 未確定： 4633028263982（Pink/Rock Rose）
  - 特殊色Multi： 4771571925198（Multi/Yellow）
  - HOLD： 7236286218446（Yellow/Red）
  - 構成色なし： 4631353360430
- fixture作成は ahc_create_swatch_fixture.php のGPT監査（c7e70d62）で修正事項が出ているため、その修正と再検収の後に実行する。

## 3. テーマ差分（Local 実物 vs GitHub local-snapshot-2026-11-15）

3ファイルとも差分あり（Localが旧い、いわゆる deploy gap）。

| ファイル | Local md5 | Localサイズ | snapshotサイズ | diff行数 |
|---|---|---|---|---|
| theme/main.js | 3e4dafc07ea21ed228578254face0459 | 18,821B | 20,314B | 85 |
| theme/style.css | d90546fe29a29fd8eda7f0f734999c26 | 47,537B | 47,730B | 30 |
| mu-plugins/nexus-variation-gallery.php | a7afd3ae6d2a82da2e028688865cd367 | 12,611B | 14,216B | 52 |

- 反映は writer／fixture のゲートが解けてから、fixture 作成と合わせて行う（現時点でLocalは無変更）。

## 次の動き

- Claude： fixture作成ツールの監査修正（c7e70d62）。
- GPT： 再検収と、上記1の明示mapping（SP→Shoe Palace）の可否判断。
- 魔王： ゲートが解けたら fixture作成 → writer dry-run/apply（fixtureのみ）→ PC/スマホ実画面確認 → rollback・再実行差分0の確認。158点は dry-run まで。
