# Claude の回答：158 商品の照合はいつ終わるか（2026-11-21 19:58 JST）

97b430d「158商品どれくらいで終わるの？？？？」への回答。

## 受け渡し（済み）
- サイト側の SKU 一覧を登録した：**`data/xserver-export/sp-variation-skus-2026-11-21.csv`（a076ff9）**。
  - 内容：SP 158 商品・1,713 variation。列は product_id、parent_sku、variation_id、variation_sku。
  - XServer の Woo REST から読み取りだけで取得した。
  - ブラウザ上のデータと、件数・ID 合計・SKU 合計が完全に一致することを確認済み。SKU に重複はない。
- 全件 CSV（619 商品）を待たずに、158 商品分だけを先に渡した。GitHub へのログインはこの件では不要になった。

## 158 商品が終わるまでの段取りと時間
1. **GPT**：商品管理ブックの「商品カラー」シートから、SP の supplier_product_id → source_url を 158 商品分取り出し、GitHub に登録する。
   - 突き合わせは、サイト側の親 SKU `SP-<id>` と `parent_sku` の完全一致で行う。
   - 所要時間：GPT の作業次第。シートは横断済みなので短いはず。
2. **Claude**：その 158 件の URL を受け取り次第、Chrome で Shoe Palace 公式の `/products/<handle>.js` を 1 件 1.5 秒間隔で読む。
   - 取るもの：variant SKU・variant ID・available・price。
   - これを手順 1 の一覧と SKU で突き合わせ、結果を GitHub に登録する。
   - **所要時間：URL 一覧を受け取ってから約 20 分**（読み取り約 4 分＋突合と登録）。
3. 一致しないもの・Shoe Palace で消えている商品・シートに URL が無いものは、理由を付けて HOLD として一覧にする。削除はオーナーの承認があるまでしない。

**まとめ：GPT が 158 件の URL を GitHub に出してから、約 20 分で 158 商品すべての照合結果を出せる。**

## 止めたこと
古い CSV からの URL 探しと「23 商品を 5 件ずつ」の作業は、オーナー決定 def13b8 と GPT 訂正 b8e2da1 に従って停止した。
