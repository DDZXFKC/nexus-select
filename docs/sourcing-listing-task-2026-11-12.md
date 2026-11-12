# 商品発掘・出品タスク 2026-11-12
ユーザー指示：過去の発掘商品を出品し、Grokにも新規商品を探させる。原価計算の正確性は絶対厳守。以下はChatGPTからの作業依頼であり、合意済み・実行済みではない。

## 既出候補（過去の表示価格、現在の在庫ではない）
|商品|型番|過去価格|仕入れ先|扱い|
|---|---|---|---|---|
|Kith Suede Alonzo Jacket Eternal|khma010081-246|USD1250|https://kith.com/products/khma010081-246|再検証|
|Stussy Tile Oval Hoodie Navy|1925169|USD180|https://www.ebay.com/itm/376962649416|型番・真正性・配送保留|
|New Era Timberland Mets|60959499|USD50|https://extrabutterny.com/products/new-era-x-timberland-1920-new-york-mets-snapback-hats-60959499|再検証|
|New Era Timberland Astros|60959502|USD50|https://freshcaphats.com/products/new-era-19twenty-houston-astros-snapback-wheat|正規性保留|
|New Era Knicks Tee|15375771|USD40|https://extrabutterny.com/collections/30-apparel-sale/products/new-era-x-new-year-knicks-mens-tee-15375771|国内根拠保留|
|visvim 101XX JKT G.CORDS Navy|0126205013018|通貨要確認|https://havenshop.com/products/visvim-101xx-jkt-g-cords-navy-fw26|再検証|
|Kith Pouch Java|khma040073-3004|USD245|https://kith.com/products/khma040073-3004|再検証|
|Kith Yankees Cap|khma050115-413|USD60|https://kith.com/products/khma050115-413|米国内配送条件確認|
|Kith Kids Sherpa Cap|khka050085-185|USD60|https://kith.com/products/khka050085-185|再検証|
|Kith Boucle Sweater|khma030153-3060|USD245|https://kith.com/products/khma030153-3060|サイズ在庫保留|
|Stussy Tote Green|134253|USD70|https://www.stussy.com/products/134253-canvas-extra-large-tote-green|再検証|
|Stussy New Era Brown|1311107|USD50|https://www.stussy.com/products/1311107-9twenty-basic-cap-brown|再検証|
|Kith Cardholder Studio|khma340092-030|USD150|https://kith.com/products/khma340092-030|再検証|
|Kith MagSafe Black|khma340091-001|USD125|https://kith.com/products/khma340091-001|再検証|
|Kith MagSafe Legacy|khma340091-265|USD125|https://kith.com/products/khma340091-265|再検証|
|Converse EDGLRD Chuck 70|A20013C|USD100|https://www.converse.com/shop/p/converse-x-edglrd-chuck-70-unisex-high-top-shoe/A20013C.html|商標・輸入適法性と在庫保留。日米仕様差は価値として評価|

## Grokへの依頼
国内需要起点（BUYMA、国内完売、再販希望、実売相場）と海外供給起点（地域別公式、正規店の新着・セール・再入荷）を並行。米英独を中心にEU・アジアも調査。スニーカーと衣類を含む全カテゴリ、ブランド横断。SKU・カラー・サイズ単位で突合し、国内根拠、海外在庫、販売者、配送先制限、価格通貨、素材・原産国、実売相場、確認日時、直接URLを返す。検索結果だけで確定しない。海外限定でも需要・利益・継続供給が弱ければ優先しない。既出と重複排除。Converseは仕様差で除外せず適法性を個別確認。
## 原価絶対厳守
商品代、現地税/VAT、現地送料、実際の決済為替・手数料、国際送料（梱包後重量・容積・配送先）、保険、関税、輸入消費税、通関費、代行・検品・梱包、国内送料、販売手数料・決済費を個別記録。DDP等の二重計上禁止。商業輸入に個人使用の0.6掛けを適用しない。税関評価額は実際の決済換算と区別し、品目・素材・原産地・適用税率・端数処理を確認。輸入消費税の課税標準は関税課税価格＋関税等。参考 https://www.jetro.go.jp/world/qa/04M-100421.html https://www.nta.go.jp/taxes/shiraberu/taxanswer/shohi/6563.htm 。輸入者と税負担者、税額控除可否も区別。未確定費用をゼロにしない。原価と販売価格、手数料控除後利益を独立再計算し照合。将来の為替・税額は確定値と呼ばず上限見積と実績を分ける。利益基準が未設定なら勝手に確定しない。
## Museへの依頼
上記16候補を既存商品とSKU照合し、再検証・原価照合を通過した商品だけ登録。WooCommerceは下書き（サイト公開条件を維持）、BUYMAは配送体制・規約・画像使用権・価格・在庫が確認できた場合のみ出品。サイズ・カラー、白背景正方形画像、説明、配送日数、仕入れURL、在庫更新を整備。購入・決済・取り置きは行わない。未確定品は公開しない。作業結果を同ブランチに記録し、GrokとChatGPTのレビューを受ける。ユーザーを伝言係にしない。
