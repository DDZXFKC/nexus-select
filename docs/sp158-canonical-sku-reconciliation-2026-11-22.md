# Shoe Palace 158商品のSKU照合結果（2026-11-22 JST）

| 対象 | 一致 | 不一致 | HOLD | 合計 |
| --- | ---: | ---: | ---: | ---: |
| 商品 | 158 | 0 | 0 | 158 |
| バリエーション | 1,713 | 0 | 0 | 1,713 |

- [全158商品の判定・バリエーション件数](../data/xserver-export/sp158-product-match-summary-2026-11-22.csv)
- [全1,713バリエーションのWoo／Shoe Palace SKU・ID・証拠時刻](../data/xserver-export/sp158-variation-match-result-2026-11-22.csv)

CSVの `PASS` は一致を示す。不一致は両側の値が確認でき、完全一致しない行を指す。HOLDは、欠損・重複・証拠不足により判定を保留する行を指す。商品単位では全バリエーションが一致した場合に一致とした。

## 正本を直接読んだ再検算

1. [AFTER HOURS CLUB 商品管理／商品カラー](https://docs.google.com/spreadsheets/d/1JdQnCxqS5gqrX6-4hcJBGEx_qFCuJsufUjedbkWnJsg/edit#gid=886480828) の A:C・S 列を行1～12,000まで読み取った。対象158商品すべてで `shop_code=SP` の商品IDが一意に見つかり、同一行のURLは[158商品の対応表](../data/xserver-export/sp158-source-urls-from-sheet-2026-11-21.csv)と文字列で完全一致した。
2. [正本のSP価格検証タブ](https://docs.google.com/spreadsheets/d/1JdQnCxqS5gqrX6-4hcJBGEx_qFCuJsufUjedbkWnJsg/edit#gid=543441826) の A:B 列で、対象158件の親SKUとShoe Palace商品IDの組が [Woo出力](../data/xserver-export/sp-variation-skus-2026-11-21.csv) の親SKU `SP-<商品ID>` と完全一致した。タブで確認した163件のうち、Wooの対象に含まれない5件は集計対象外。
3. Wooの商品ID・variation IDの組で、[Shoe Palace公式データの取得結果](../data/xserver-export/sp158-live-sku-match-2026-11-22.csv) と[照合結果CSV](../data/xserver-export/sp158-variation-match-result-2026-11-22.csv) を突合した。正本で確認した親商品ID・URLの下で、Woo variation SKUとShoe Palace variant SKUが1,713件とも文字列で完全一致し、Shoe Palaceのvariant IDも両方の記録で一致した。Wooのvariation ID・SKU、Shoe Palaceのvariant ID・SKUはいずれも1,713件で一意。158商品ごとのバリエーション件数と商品別CSVの集計も確認した。

商品管理ブックで確認したのは親SKU・商品ID・URL。variation SKUの確認には、GitHubに保存済みのShoe Palace公式データの取得結果を使用した。今回の再検算はサイズ表記を維持し、在庫と現在価格を判定対象から外した。

## 再検算時のGitHubファイル

| ファイル | Git blob SHA |
| --- | --- |
| Woo出力 | `c3d435f440330091d83fa098fe27b17e1b1b0a6a` |
| 158商品の対応表 | `2672760a2731dd7129f3220e8be986851bc143f9` |
| Shoe Palace公式データ取得結果 | `009f52cd336fb7a175f4e51ed424382c0494f510` |
| 商品別判定 | `b718f8b471b5e12183f87d943fd8aee86ba6e9da` |
| バリエーション別判定 | `9255d4a943357eb0b6775b53e7c989711c059fc0` |
