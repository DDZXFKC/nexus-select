# オーナー決定の訂正：SOLD OUTの24時間共有を廃止、ライブ確認結果を双方向即時反映（2026-11-22）

## 正式な判断
2026-11-21オーナー確定事項および2026-11-22追加決定を優先し、コミット `94bacdef` / `a297181d` の「24時間品切れの印を別ユーザーに共有する」方針と、「承認済み」という説明を**撤回**する。

**在庫は各ユーザーがその場で実行した、選択商品・カラー・サイズのライブ照会だけで判断する。** 保存した在庫スナップショット、Wooの過去在庫フラグ、他ユーザーが行った確認結果で判断しない。売切確定はすぐ SOLD OUT と表示し、後の新規確認で在庫ありと判定されたらすぐ買付・カート追加可能な表示に戻す。両方向に自動の期限切れや24時間の保持はしない。

在庫あり＝選択した商品・サイズが、ライブ照会に加えてWooカートに追加できること。仕入先ページを読めない・サイズの一致を確認できない・価格再計算不能・Wooが現在購入不可なら、買えると表示しない（判定不能として再確認をお願いする）。品切れを自動的に再試行しない。顧客が再び「在庫を確認する」を押した時だけ新規確認する。最安確認と400円価格差ルールは変更しない。

## 実コード修正
- `tools/ahc-stock-inline-endpoints-staging.php`:
  - `_ahc_inline_oos_until` の参照、書込、24時間品切れ時の開始拒否、カート直前の同印による拒否を削除
  - `ahc_inline_shared_oos_variation` のWoo variation dataフィルターを削除
  - OUT_OF_STOCKはその問い合わせの結果だけに返す。IN_STOCKは、選択Woo商品の現在の `is_purchasable`/`is_in_stock` も満たす場合だけ購入許可する
  - カート直前に仕入先の在庫・現価を再確認する既存仕様は保持（自動再試行ではなくカート追加時の誤販売防止）
- `local-snapshot-2026-11-15/mu-plugins/ahc-stock-check-ui.php`:
  - Woo variation dataへ24時間品切れを注入するフィルターを削除
  - Simple商品でも古いWoo在庫表示にかかわらずライブ照会ボタンを表示
- `local-snapshot-2026-11-15/mu-plugins/ahc-stock-check-ui.js`:
  - 個別確認結果を受信したら即 `data-live-availability` と画面内案内を更新し、売切→在庫あり/在庫あり→売切を即切替
  - 売切時も「在庫を確認する」を有効に保ち、顧客が再確認できるようにする
  - Wooの `data-product_variations` と jQuery キャッシュを品切れへ書き換える従来コードを削除
  - Woo保存在庫の `is_in_stock` の真偽で新しいライブ確認ボタンを封鎖しない
  - `marked_oos` サーバー応答をライブのSOLD OUTとして偽装する旧分岐を削除
- `tools/ahc-sp-clear-legacy-oos-meta.php`:
  - 旧版がWordPress DBに書いた `_ahc_inline_oos_until` を、後方互換のため無視するだけでなく**明示的に除去できるWP-CLIコマンド**を追加
  - デフォルトは件数表示だけのdry-run。DBバックアップの後に `--execute` でそのキーの行だけ削除。自動実行しない
- `.github/workflows/stockcheck-inline-php.yml`:
  - アクティブなPHP/JSの24時間品切れ印が戻った場合にCIを失敗させる防止検査
  - PHP/Javascript回帰テストを実行

## テスト受入
- `qa/php-tests/stockcheck_inline_endpoint_stub_test.php`:
  - OOS確定後にメタが書かれない
  - 別セッションで即再照会でき、在庫ありならすぐpermit取得
  - 過去の `_ahc_inline_oos_until` が残っていても新しい照会・カートを阻害しない
  - Wooが購入不可の場合は「在庫あり」を断定しないが、購入可能に戻ったら即照会し直せる
- `qa/php-tests/stockcheck_sp158_full_chain_stub_test.php`、`qa/php-tests/stockcheck_sp_chain_stub_test.php`: 実証CSVと商店モックにより売切→在庫復活を確認
- `qa/js-tests/stock_check_ui_flow_test.js`: 両方向の画面反映、新規手動照会、Woo変数の非破壊、旧marked_oosの未使用を確認
- GitHub Actions `Inline stock server PHP draft validation` の完走・合格で確認する

## 実環境について
**本件のGitHub変更はステージング実装の修正であり、XServer上で有効化・DB削除をしたとする証拠ではない。** 既存ライブ画面が旧バージョンなら、反映担当が最新コードと旧フックの有効化状態を確認し、バックアップ→反映→端末実測を行う。XServerのmeta除去もWP-CLI cleanupを実機で実行するまでは未完了。

今回の仕様訂正はサイト公開を許可するものではなく、商品ID・SKU・サイズや表示デザインの変更も伴わない。
