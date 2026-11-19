# バッチ1再現テスト報告書（魔王ちゃん、2026-11-20）

GPT適応版ジェネレータ（tools/build_buyma_batch.py、f19e95c6）＋比較器（tools/compare_buyma_batch.py、db62ef01）で、バッチ1を同一インプットから再生成し、正本（tools/batch1_items.csv / batch1_colorsizes.csv、ca3f7bdd）と照合した。GLM再検証で B-2gen は VERIFIED（docs/review-glm-reverify-2026-11-20.md）。

## 再現インプット（未登録のローカル原本、build_buyma_batch.md の指定どおり）
- 選択SKU：正本 items の10件（順序も正本どおり）を selected.csv（列名 SKU）として投入
- Woo原本：/home/hatch/workspace/fl-scrape/shoepalace-woo-import-prep.csv
- ブランド元データ：/home/hatch/workspace/fl-scrape/shoepalace-hoka-all.csv（productId / description_en / url）
- サイズ表：ブランドサイズ表ブック（ID 1tocT7WKqiwO1Ku3DP2EnliUUV8F7ux30VGjuaYH4O1k、「サイズ表」タブ）の現在値JSONエクスポート（966行。2026-11-20追加のHOKA Women 15行を含む）
- 設定（local.json）：brands のキーは Woo の Brand 値 'HOKA'、brand_id=6906、brand_name='HOKA ONE ONE'、categories Men=3321 / Women=3081 / Kids=4531、--reproduce-batch1（歴史再現モード）、prefix=batch1

## 結果
- items：10件、**バイト完全一致（差分0）**
- colorsizes：156行生成。検索用サイズ空欄は生成・正本とも17件で一致。**差分は16セルのみ**（下記の既知差分リスト）
- 56セル補完の再現：レディース4 SKU（SP-7560264057038、SP-7608023384270、SP-7719430357198、SP-8824175722702）の検索用サイズ56セルは、サイズ表（HOKA Women行追加後の現在値）からの再生成で全て一致。検索用サイズ列の差分は0件。これにより、2026-11-20の外科的修正（対象4 SKU・56セルのみ変更、他は差分0を検証済み）とサイズ表ブック（HOKA公式 Women チャート由来・出典列付き）が、GPTの求めた別証拠として成立する

## 既知差分リスト（GLM指示により登録。以後の再現テストではこのリスト照合で処理する）
| # | ファイル | SKU | 列 | 再生成値 | 正本値 | 原因 |
|---|---|---|---|---|---|---|
| 1 | batch1_colorsizes.csv | SP-8813225869518 Clifton UTL Mens (Frost/Black) 全16行 | 色系統 | 99 | 1 | 色名の第1要素 'frost' が原典 build_batch1.py・適応版どちらの COLORSYS 辞書にも無いため 99 に落ちる。正本の 1（ホワイト）は 'frost' を白系とする人的判断値で、オーナー決定「色系統はメインの色で判断し、判断しかねる場合だけ99」と整合する。原典スクリプト自体も同じ辞書・同じ挙動のため、適応版の移植ミスではない |

## 通常モードの運用（GLM確定 2026-11-20）
- 未登録色名の色系統は、辞書フォールバックではなく color_ids 側で色名→色系統を明示指定する（判断の記録がバッチインプットに残る）
- 未登録色名が color_ids 指定なしで出現した場合は、黙って99に落とさず生成時警告ログを出す（GPTへ伝達済み・推奨事項）
- 任意確認：frost=1 を color_ids で指定してバッチ1が差分0で再現できることの確認（実施はGPTの判断）
