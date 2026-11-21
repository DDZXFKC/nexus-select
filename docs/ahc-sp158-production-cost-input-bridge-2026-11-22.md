# AFTER HOURS CLUB — Shoe Palace原価入力「本番接続」実装・実機ゲート（2026-11-22）

## 判定
**GitHub上の本番向け入力経路（原価計算→購入可否）は実装・CI合格。本物のXServer環境への配置・ルート別原価確認は未完了。**

`原価式は決定済み` と `あらゆる買付ルートの追加費用が原価式に含まれる` は別の命題。ユーザー確定式を変更せず、必要な追加費用を無断でゼロとみなして購入を許可する危険だけを防いだ。後者を明示的に確認した商品・仕入先・選択サイズ・ライブUSD価格のみ本番接続を許可する。

## 完了済みコード
- `tools/ahc-stock-sp158-owner-bridge-staging.php`
  - 158商品・1,713 variationの実測対応表を厳密照合。
  - `ahc_inline_recomputed_sale_price` に最新Shopify価格を渡して下記固定式でJPY価格を計算。
  - **新規** `ahc_sp158_live_cost_coverage_verified` フィルターで個別の買付・税・送料・販路決済の適用証拠がなければ **null / 判定不能** を返す。
- `tools/ahc-stock-sp158-cost-coverage-provider.php`（新規）
  - Woo側で使う**非公開の原価/ルート承認JSON**を参照する。
  - 対象 `product_id / variation_id / supplier_product_id / merchant_variant_id / SKU / 公式URL / ライブUSD価格` が一つでも違うと不許可。
  - 全10費目に個別のレビュー証跡・「確定式に含まれるか適用外の根拠」を必須にする。未確定はゼロ扱いしない。
  - 非公開JSONのSHA-256固定値と、ユーザー指定原価式のID、AHC販路除数の承認、承認参照番号が一致する場合だけ有効。見知らぬ上書きを自動受理しない。時刻経過で在庫に期限を設けない。
- `tools/ahc-sp158-staging-loader.php`：PHP3つ＋この原価プロバイダー1つの計4ファイルをステージング限定でロード。他の2種類の在庫確認AJAXハンドラーと同時有効化しない。
- `tests/test_ahc_sp158_cost_coverage.php`：ダミーのテスト専用承認JSONを一時ファイルに作り、15ケース（ID/SKU不一致、価格変化、JSON改変、異なる買付先等）を検証。**テスト用ダミー承認を本番の承認として扱わない**。
- `qa/php-tests/stockcheck_sp158_full_chain_stub_test.php`：原価承認なしではWoo在庫あり・SP在庫ありでもカートを許さないことをテスト。
- `.github/workflows/stockcheck-inline-php.yml`：上記に自動lint・PHPテストを追加。

## ユーザーの確定価格（変更なし）
```
原価（円、丸め前）＝選択バリエーションの現在価格USD × 158 × 1.02 + 2200 + 1500 + 60
販売価格（円）＝ ceil((原価 ÷ 0.785) ÷ 100) × 100
```
価格更新時は常に再計算。400円未満の増額/減額は掲載価格維持、400円以上の値上げは購入者同意を要求。売切表示中も再照会は可能、結果が両方向即時反映、自動再試行・24時間保管なし。

## 確認できた実商店ルールと未確定費用
Shoe Palace公式が説明している原価上の事実：
- 店舗は国際住所へ発送しない。米国内の受取/転送住所が必要。
- 米国内送料は商品種類・セール状況・数量・注文金額等に応じ変わり、**チェックアウトで確定**する。Shoe Palace送料ページ： https://www.shoepalace.com/pages/shipping
- 売上税は配送先州に応じて**チェックアウトで計算**。Shoe Palace規約： https://www.shoepalace.com/pages/terms-and-conditions

したがって、固定送料2200円、パートナー1500円、梱包60円を確定しただけでは、現地通販送料・現地売上税・日本への輸入費目・国内送料・実際のAHC決済料率が必ず原価に収まると実証されたことにはならない。値を勝手に足したり、無根拠でゼロにしない。

## XServer適用前の具体的な入力
1. 実際の受取州・郵便番号/買付方法・配送経路を確定。
2. 各SKUの買付実額に対応するShoepalaceチェックアウト送料・販売税を確認（又はその商品が対象条件下で本当に無料/非課税となる証拠を確認）。
3. 現地→日本→購入者の国際/国内運賃、税・関税・輸入消費税、パートナー、梱包、その他必須費用、および決済・チャネルの0.785適用根拠を確定。確定式に含まれない費用が出るなら、原価式を独断修正せずオーナーが価格適用を再決定するまでHOLD。
4. 公開GitHubに**実際の原価承認値・署名や個人住所を置かず**、サーバーのwebroot外に承認JSONを保管し、ファイルのSHA256を設定に固定する。
5. `AHC_SP158_COST_COVERAGE_FILE`、`AHC_SP158_COST_COVERAGE_SHA256`（いずれも非公開設定）、従来の `AHC_SP158_VERIFIED_CSV` を配置し、旧ハンドラーと競合がないXServerステージングで差分検証後、`AHC_SP158_STAGING_ENABLED` を使って有効化。
6. 実サーバーの `wp_safe_remote_get` からのShopify通信、価格再計算→400円ルール→カート→注文確認・Store API迂回防止を検証。本番公開は別途承認。

## 現在の区切り
- **合格**：ソース・原価式・価格再計算のPHP連携、監査がない場合のfail-closed、GitHub ActionsオフラインE2E。
- **未実施**：XServerに直接デプロイ、注文時実送料・実売上税などの購入ルート照合、非公開JSONの作成・XServer上の配置・実取引確認。
- **公開禁止**：全11公開要件・決済と買付運用が揃い、オーナー承認があるまで。

## GitHub Actions最終検証と追加の安全修正
- `Inline stock server PHP draft validation` [run 44935210764](https://github.com/DDZXFKC/nexus-select/actions/runs/44935210764) — **completed / success**。証拠1713件、価格式、民間原価承認の厳密照合、旧価格の迂回拒否、Wooカート模擬連携、JSポップアップ挙動を含むステップすべてPASS。
- `tools/ahc-stock-sp158-owner-bridge-staging.php` で古いSP価格コールバックから引き継いだ `$previous` 値をそのまま採用しないよう修正。非SPだけ以前の結果を保持。古いSP計算経路でプライベート原価審査を迂回しない。
- `tests/test_ahc_sp158_cost_coverage.php` の16検証項目のうち、承認ファイルの改変で結果が失効した際に以前の価格があっても購入許可しない試験を追加。

本番環境への実導入を意味するものではない。XServerサーバーの更新権限や秘密設定がこのGitHub接続からは提供されないため、サーバー実反映は実行していない。
