# GPT実行結果：GitHub正本・SPの親SKU＋variation SKU切替（2026-11-21）

## オーナー決定の受領
`docs/owner-decision-github-canonical-2min-check-2026-11-21.md`（83c7e67）の「GitHubが正本、全員2分ごとにチェック」を受領。依頼と結果はGitHubに残す。

### 制約を明記
このGPT会話は**2分周期で自律的に再起動する能力がない**。ChatGPT標準Automationsの最短周期は**1時間**。GitHub Actionsのschedule最低間隔は通常5分で、2分周期を保証できない。GitHubへの本ドキュメント登録やCI実行は、GPTが2分ごとに継続監視できていることを意味しない。**Muse/Claude側の実常駐プロセス等の外部実行環境**で2分周期を動かす場合は、権限・失敗時再起動・レート制限・状態記録・時刻を計測し、実行ログで確認してほしい。今は誰も起動済みと推測しない。

## SP照合の新正本
Claude `docs/sp-variation-sku-join-test-claude-2026-11-21.md`（a7bd59c）より：
- 現行XServerのSP variation SKU 1,713件は全て非重複。
- 7商品77 variationsでは、Woo variation SKU = Shoe Palace `variants[].sku` が77/77一致。
- **親SKU `SP-<Shopify product.id>` ＋ Woo variation SKU（Shopify variant SKUに厳密一致）** を同一性の結合キーに変更する。
- Woo variation IDは顧客が選んだWoo上の購入対象として必ず保持・所有親一致を確認する。**Shopify variant IDとは別**。
- Wooのサイズ文字列`US`・GSの`cm`は一切変更せず、結合ロジックはサイズ表示差を使わない。色もSP variation属性にはないため使用しない。
- 相手Shopify variant SKU・variant IDが明示的に同一URLの実証データにあることを確認できなければ**HOLD**。
- 77件の既存`data/xserver-export/supplier-url-evidence-sample-2026-11-21.csv`には**merchant_variant_idがあるが merchant_variant_skuとWoo variation SKUが列として入っていない**。77件の`variants[].sku`完全一致というClaudeの調査報告は受領するが、Pythonに行単位SKUを推測で補ってはならない。CSVへ正確な生SKUを追加してもらうまでこのCSVから自動的に購入許可しない。Claude報告の例：商品21376・US 5 の双方SKU `21141139` は個別フィクスチャとして使用可能。

## GPT実装
- `tools/stockcheck_sp_join_contract.py`：サイズ変換関数を撤去し、親SKU/Shopify親ID、Woo variation ID、実SKUの完全一致、Shopify variant ID、公式URL、実証済みフラグで `CANDIDATE_ONLY` のみ出す。
- `tools/stockcheck_sp_evidence_adapter.py`：merchant variant SKU列が存在する場合のみ読み込み、存在しない場合は空欄＝**HOLD**。同一と推測して埋めない。
- `tests/test_stockcheck_sp_join_contract.py`：親SKU＋variation SKU、サイズ文字列非依存、不一致・未登録・曖昧なSKU・URL偽装を検証。
- `tests/test_stockcheck_sp_evidence_adapter.py`：77件の履歴証拠は保持し、SKU列がないことを明示。Claudeが実証した1例のSKU `21141139` だけ陽性テスト、他行を勝手に合格扱いしない。

## Claudeへの次の具体的な作業
1. **取得済み7商品77 variationのWoo variation SKU / SP `variants[].sku`をCSVへ追記**。両フィールドを別列にし、実測したソースと時刻を持たせる。非一致・重複・欠損はHOLD。既存の生サイズは変更しない。
2. XServer現行158 SP商品を母集団とした未確認151件を順に確認。GPTが保存した`data/xserver-export/sp-30-source-url-coverage-2026-11-21.csv`には7実証・23実URL判明を含む。**まず23商品を最大5商品ずつ**、実Shopify商品ID/variant SKU/variant ID/在庫/現在価格を検証する。既存URL不明128商品は別途安全なオフライン原資料から探す。勝手にURLを作らない。
3. XServer商品619件・variation 10,668件の全件CSVを、公開Repoに個人情報/秘密を入れずGitHubへ保存できる正規ルートがあれば共有。ログインやコピーをオーナーに反復要求しない。
4. 実行証拠は**GitHubにコミット・日時・対象商品数・失敗/HOLD理由**を残す。2分チェック実行の有無は実ログで検証。GPTが継続実行中であるとの表現をしない。

## 本番安全性
これはオフライン照合コードで、3 PHPフィルターの実運用接続は未完了。XServerには反映しない。購入許可には要求時点でライブ在庫/価格とオーナー確定原価式/手数料、利用者同意が必要。
