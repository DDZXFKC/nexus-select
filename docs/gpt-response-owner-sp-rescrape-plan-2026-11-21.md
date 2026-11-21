# GPT返答・実行段取り：SPの再収集／取り直し決定（2026-11-21）

対象決定：`docs/owner-decision-sp-rescrape-2026-11-21.md`、コミット`def13b8`。**旧pricing CSVからのURL発掘を停止する。** この返答はオーナーの決定に対する実施順序であり、削除実行やXServerへの変更承認ではない。

## まず結論：全量を闇雲に再取得しない
魔王ちゃん実測の`ShoePalace_products.json`（2026-11-21、11,756商品）に`id`、`handle`、`variants[].sku`、`variants[].id`、`price`、`available`が存在するなら、**同日取得のその生JSONを取り直しの正本入力としてまず検証する**。データが完全なら二重スクレイピングは不要。足りない・壊れている・最新性が必要な対象だけ、ルールを守って再取得する。

現時点では11,756件のJSON本体は`integration/grok-review`に存在せず、GPTは**魔王ちゃんの保有報告のみ**確認。GitHubの`docs/ahc-collect/sample_shoepalace_products.json`はサンプルであり全件本体ではない。まずJSON本体をアクセス可能な安全な共有先に保存し、機械的な品質検査が必要。

## 一連の実行作業と完了ゲート

### A. 収集済み生JSONを確保・検収（Muse担当、GPTが検証）
1. ローカルの`ShoePalace_products.json`の実体と取得時刻・取得元・サイズ・ハッシュSHA-256を記録。11,756商品が本当に存在することをパースで確認。**GitHubへのアップロードはファイルサイズ・機密・GitHub制限を確認してから**。GitHubに置けなければ専用の保護された保管先に生JSONを残し、GitHubには再現可能なmanifest＋安全な取り込み結果のみを登録。
2. 必須項目：`product.id`、`handle`、`variants[].id`、`variants[].sku`、`variants[].available`、`variants[].price`、通貨根拠、取得日時。重複product.id、同一product内のvariant SKU重複、空handle、空SKU、JSONの切断、商品IDやShopify variant IDの不整合を検査。例外は理由付きHOLDに落とす。
3. **URLは公式の`https://www.shoepalace.com/products/`＋取得済handleから構成**する。これは同じShopify商品実体から原典handleを得た場合に限る。旧pricing CSVから推測・名称推測・検索しない。handleの安全な文字形式と公式ホストを検証。
4. **価格フィールドの単位が取得エンドポイントで違う**。`docs/ahc-collect/sample_shoepalace_products.json`では`variants[].price`が`"130.00"`等のドル文字列。一方、Claudeが実測した`/products/<handle>.js`では`price=12000`等の整数セント。JSON収集元を特定し、型/単位ごとに独立検証。**無条件で/100しない**。USD通貨確認がなければ価格不明。
5. 合格ゲート：実商品数とハッシュ、URLあり数、重複数、variant SKU/variant ID空欄数、価格型の分布、HOLD数をログに確定。

### B. 現行Woo SP商品との結合（ClaudeがXServer読み取り・GPTがコード/監査）
1. 現行XServerの**158 SP親商品**について、`woo_product_id,parent_sku`と`woo_variation_id,woo_variation_sku,parent_product_id`を安全な列に絞ってエクスポート。Woo側に保存された元データは**一切変更しない**。全件CSVが重すぎればSPに限定した小さい2 CSVを優先。
2. JOIN：親の`SP-<Shopify product.id>`＋ Woo variation SKU `=` Shopify `variants[].sku` **完全一致**。一致したShopify`variant.id`を保持。サイズ・GS表記・カラー名は結合キーにしない。Woo variation IDが所属する親との整合も厳密に確認。
3. 7商品/77variationは回帰検証のベース。それ以外の151商品は**個別の検証済み数**を計測。1対1だけMATCH、商品IDがJSONにない／SKU欠損／複数候補／variant不一致／URL欠損は理由付きHOLD。
4. 成果物：`data/xserver-export/sp-rescrape-join-results-2026-11-21.csv`（元データはそのまま、対応結果を別ファイルに書く）＋検証件数・HOLD理由別集計＋テスト。日時は実データの取得時刻として記録し、生成日時と混同しない。

### C. 在庫確認時のライブ参照・価格（GPTのPHP担当、Claudeのブラウザ実測）
1. 生JSONの`available`/`price`は**収集時点のスナップショット**。サイトで購入希望が来るたび、確定したURLとvariant SKU/IDを使って最新の公式商品JSONを取得し、該当variantの`available`と`price`を検証する。取得失敗・不整合時はUNKNOWNで購入許可しない。403/429の再試行連打は禁止。
2. 価格は「設定」タブの確定式（現地USD×158×1.02＋3,760円、丸め前原価÷0.785を100円切り上げ）を使用し、未確定費用を0扱いしない。在庫確定店の中で最安を選び、掲載価格差400円以上なら再確認、399円以下なら掲載価格のまま。
3. Wooのinstockフラグを仕入先のリアルタイム在庫証拠に使わない。PHPの3フィルターとカート直接API拒否がテスト合格するまでXServerへの新機能反映はしない。

### D. URLのないデータの削除候補を洗い出す（**削除しない**）
確認済みの**URL列を持たないか、商品別URLの正本として不適切な**候補は次のとおり。

- **URLを持たない旧価格計算・売可否資料**（判定用の古い派生データとして刷新対象）：
  - `data/pricing-16/sp_margin_16_2026-11-20.csv`
  - `data/pricing-16/sp_sellable_list_16_2026-11-20.csv`
  - `data/pricing-19/sp_margin_19_2026-11-20.csv`
  - `data/pricing-19/sp_sellable_list_19_2026-11-20.csv`
  - `collector/price-audit/sales-margin-sp-2026-11-19.csv`
  - `collector/price-audit/sales-sellable-sp-2026-11-19.csv`
  - 上記の同系派生ファイル`sp_batch3_pool_*`、`sales-sellable-sp-2026-11-20-batch3-pool.csv`等は**列と依存先を確認してから**削除候補を確定。
- **旧CSV URL発掘のためのGPT派生資料**：
  - `data/xserver-export/sp-30-source-url-coverage-2026-11-21.csv`（URLは30商品だけ存在するが、旧pricing CSVに依存するので新正本としては採用しない。旧成果物のアーカイブ/削除候補）
  - `data/pricing-16/batch{1,2,3}_items_16_2026-11-20.csv` および`data/pricing-19/batch{1,2,3}_items_19_2026-11-20.csv`は**30件に実URLあり**。一律に「URLなし」として削除しない。ただし新方式では参照停止、過去の作業根拠としてアーカイブ可。
- **WooCommerceの商品データ**：現行SP親158商品は買付先URL metaを保存していない。**現行Woo商品そのものを削除対象とはしない**。新しいURL対応表をSKUで作り、必要に応じてバックアップ・差分・承認後にWoo metaを補う。元SKU/サイズ/価格は無断変更しない。
- **77件の実測エビデンス** `data/xserver-export/supplier-url-evidence-sample-2026-11-21.csv` は実URLと双方variant SKUの証拠があるため、**削除対象に含めない**。
- 商品管理ブック`Shoe Palace店舗`は実URLを含むため**削除対象にしない**。

**削除実行ゲート**：オーナーの個別承認が得られ、対象ファイルパスと行/列・参照元・代替成果物・バックアップが揃うこと。GitHubファイル削除、Woo商品削除、シート行削除はいずれも今は実行しない。「取り直す」と「既存本番商品を無断削除する」は別である。

## 担当と自動実行の扱い
- Muse：11,756商品の生JSONの所在・完全性・受け渡し、URL欠損調査、収集の差分実行と証拠記録。
- Claude：現行XServer SP親158商品と1,713 variationsのread-only ID/SKUエクスポート、最新公開JSONの読み取り実証。
- GPT：検査とJOINコード・テスト・PHPの接続、安全な既存成果物の分類・削除候補提示。
- GitHubは正本。2分周期の実監視は、実行環境を持つ者が実ログで証明する。GPTのこのチャット自体は2分ごとに自律起動できない。

**次に進める作業の順番は A→B→C、Dは独立して並行。再取得はAの検収で欠損/旧データが判明した部分だけ。**
