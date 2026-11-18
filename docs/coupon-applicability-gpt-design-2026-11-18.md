# クーポン適用判定：オーナー提案へのGPT設計回答（2026-11-18）
対象: docs/coupon-applicability-proposal-2026-11-18.md (b59469bd)、collector/coupon_bridge.py、test_coupon_bridge.py、既存RawCoupon・source config・11/17構成決定。
判定：提案に賛成。複数ソースの一致・新しさ・成功/失敗情報を評価し、有力候補を選ぶ層を追加する。発見情報だけで確定原価・販売価格を下げることはしない。現行select()の実測確認ゲートは維持。これは設計入力であり、ソース有効化・ライブ取得・購入・販売価格変更・新規課金の承認ではない。

## 1. 判定を三軸に分ける
A. campaign_confidence（コード自体の信頼度）：DISCOVERED / PROMISING / CONFLICT / LIKELY_INVALID / EXPIRED / RETIRED。
B. eligibility（正確な商品・買付条件への規約適合）：MATCH / EXCLUDED / UNKNOWN。店、地域、通貨、SKU/variant、ブランド、カテゴリ、セール/新作除外、最低購入額、数量、初回/会員、アカウント、購入回数、配送先、併用、開始・終了時刻、販売目的制限を照合。条件不記載はUNKNOWN。MATCHは実際の割引成功ではない。
C. check_status（実測）：NOT_CHECKED / APPLICABLE / NOT_APPLICABLE / UNKNOWN / STALE（計算時派生）。
複数ソースの一致だけでCをAPPLICABLEにしない。EXPIRED/EXCLUDED等が有効な場合は確定原価には使用不可。コードに新キャンペーンの証拠があれば新規評価。全商品に対してコードが使えるとは推定しない。
有力候補は高い割引を見逃さず、確認作業の負荷を削減するための状態。公式掲載がなくても候補として残す。

## 2. ソース評価と候補順位
優先：店舗公式プロモーション・規約・許可済みAPI/フィード・利用可能な公式ニュースレター > 出所/検証時刻/成功根拠が確認できるクーポンサイト > コミュニティの具体的な成功/失敗報告 > 出所不明の掲載。
観測ごとに source_id, source_url, origin_group, raw_ref/hash, source_published_at, source_verified_at, success_at/failure_at, fetched_at, observed_at, evidence_type, claim_scope, report_id, condition fields, date precision/timezone, success/failure count (定義と期間), provenance, collection_permission を保存。未掲載値はnull、日付のみは日付として保持。取得日を利用成功日に置き換えない。
同じ元記事・アフィリエイト配信・転載・同じ報告は1つの証拠グループ。独立性不明は独立成功として加算しない。再取得で新成功数を増やさない。コード表記は原文保持、ショップ側が大小文字を区別しない証拠なしに正規化しない。キャンペーン識別子はshop/market/code/campaign period/version。コードなし自動割引も別campaignとして保存（未特定は要確認キュー）。
候補の初期ルール（調整可能な設計値であり確率ではない）：
- 最新の公式有効条件と対象条件の一致、又は独立した2つ以上の根拠に同一条件・最近の具体的成功記録があり、有力な否定証拠なし → PROMISING。
- 単一の掲載、出所不明の一致、成功日時なし → DISCOVERED（排除しない）。
- 割引率・期限・対象条件に重大な矛盾 → CONFLICT。公式の有効な条件を優先し、矛盾履歴を保存。未解消は確認待ち。
- 公式失効、期間終了（時差・日付精度が確定した場合）→ EXPIRED。公式明示無効・後続の明確な失敗は適切なスコープで無効/再確認。複数の独立した最近の失敗はLIKELY_INVALIDに下げる。単一の曖昧な失敗はUNKNOWN、対象外はその条件のみEXCLUDED。
順位: 条件適合・証拠権威・成功日時・独立性・否定証拠・期限・節約見込額・検証コスト。成功率は母数/同一条件/期間が揃わなければ算出しない。高/中/低を確率80%等と表示しない。
鮮度の初期案：成功証拠24時間以内を最優先、7日超は弱い参考。短期セールはより短く、実測で校正。更新頻度も未確定。古い失敗を永久ブラックリストにしない。
参照：CouponFollow自身も直近成功・条件・検証・失効等で順位付けする。https://couponfollow.com/why-trust-couponfollow 。同社規約も正確性・最新性を保証しない。https://couponfollow.com/docs/terms-of-use 。これは第三者情報が候補選定に有効な根拠でありAHCの適用証明ではない。

## 3. 原価・価格への反映
通常商品小計、候補割引小計（試算のみ）、実測確認済み小計を区別。候補は発掘・優先確認・利益改善余地の表示だけに使う。候補の割引を使って出品可、価格確定、購入案内を自動で許可しない。候補の通常原価では赤字だが割引なら利益が出る場合も候補として保持し、確認後に再判定。
現行CouponBridge.context()のshop_code,variant_id,currency,destination,account_scope,quantity,base_minor,basket_keyで厳密に照合。追加でブランド/カテゴリ/商品属性と買付条件の根拠を参照。実測価格は許可された同一条件のカート検証（購入確定・支払なし）または店が提供する同等の確定見積証拠を現行ゲートの要件に合わせる。条件確認、使用可能回数、期限、正しい商品小計差分、証拠参照が必須。第三者成功報告/公式条件一致だけではrecord_check(APPLICABLE)を呼ばない。期限不明は現行ゲートでは適用不可。期限なしの公式定常施策も別途仕様承認まで候補。
APPLICABLEでもsale_approved=false。着地原価の全費目（現地税・国際/国内送料・関税・輸入消費税・為替/決済・代行費・販売手数料・返品予備費等）を別計算し、最低利益・在庫・供給条件・利用上限を確認。送料割引、キャッシュバック、セット割、贈品、複数SKU配賦は商品小計に混ぜず、対応実装までは別候補。セール済み価格から二重割引しない。併用は実証まで禁止。単回/初回コードを全商品に恒常利用できるとみなさない。アカウント/回数の予約・消費管理が未実装の間は繰り返し適用価格として使わない。
例（仮定、単一SKU、税/送料前）：通常100 USD、候補20%なら試算80 USD、確定原価用小計100 USD。実測80 USDかつ全条件を満たせば80 USDに切替。失効時100 USDへ戻し全原価再計算。正式注文後に一方的な追加請求はしない。

## 4. 再確認・無効化
既存の select() は完全一致scope、最新check、鮮度、期限、後続失敗、同時刻の矛盾、新しい観測を確認する。厳格性を維持。新観測は同じ内容の再取得でも現在は無効化されるため、意味のある条件/有効性変更と同内容の再観測を区別する設計を追加する。取得失敗やサイトから見えなくなっただけで失効を断定せず、再確認待ち・鮮度切れで価格適用停止。既存の安全ゲートを弱めない。改修前は現在の保守的無効化のまま。
失敗理由：EXPIRED / CODE_INVALID / BRAND_EXCLUDED / VARIANT_EXCLUDED / SALE_EXCLUDED / MIN_SPEND / REGION / ACCOUNT_INELIGIBLE / USAGE_EXHAUSTED / STACKING / PRICE_CHANGED / NETWORK_ERROR / ACCESS_BLOCKED / UNKNOWN。公式全体失効と個別カート失敗の適用範囲を分離。通信失敗をコード無効としない。403/429や規約拒否時は停止して正規の手段へ。制限回避・コード総当たり・大量カート・アカウント複製は禁止。
時刻が進むだけで期限/鮮度を再評価。期限切れ/条件変更/利用消費時、対象商品だけ再計算・代替仕入先検討。未契約の販売価格の見直し/受付停止、契約済み注文は別の損失/顧客対応ルール。自サイトの全商品在庫確認時と買付直前に実在庫・価格・適用可否を再確認する。既存週2回在庫更新は維持。
クーポン定期更新の初期提案は毎日、短期施策は期限/実際の買付時に再確認。取得許可・負荷・有効期間に応じて設定。個別店舗の失敗で他店・商品発掘を停止しない。

## 5. ソースと既存Pythonへの組み込み
既存 ahc-system/config/coupon_sources.yaml にUS RetailMeNot/CouponFollow/SimplyCodes/Wethrift/Dealspotr/Slickdeals、DE Gutscheinsammler/Gutscheinpony/mydealz/Sparwelt、GB VoucherCodes/HotUKDeals/LatestDeals、FR Dealabs等が設定済み。ただし全ソースenabled:false。RetailMeNotアダプターはAPI未実装・HTML取得しない。mydealzはRSSから店未特定・コード空のRawCouponを返す。利用条件、API/フィード/手動方法、商用再利用の可否を個別に確認するまで有効化しない。公式情報優先、許可された集約/手動取込。個人専用コード・認証情報・実データを公開GitHubに載せない。
既存RawCouponはfirst_order_only/combinableがFalse、eligible/excluded listsが空をデフォルトにしている。未取得を条件なしと誤認しないよう明示された値と未知を区別するスキーマ/アダプターを追加。mydealzの日付欠損時now()補完は取得日時であって投稿日時ではないため修正。商品ごとの対象可否は規約由来のeligibilityと実測checkを分離。
現行SQLite ahc_coupon_observations_v1 / ahc_coupon_checks_v1を維持。observationsのpayloadを互換拡張し、必要なら派生assessment_v1とcheck_queue_v1を追加、version付き。別の正本を作らない。既存レコードは未知項目をnullにする。候補判定を純粋関数化して保存観測から再計算可能にする。
API提案：record_discovery()/record_raw()を拡張、assess_campaigns(shop_code, now)→信頼度/根拠/矛盾/鮮度、evaluate_eligibility(campaign, scope, product_facts)→MATCH/EXCLUDED/UNKNOWN、rank_candidates(scope, now)→確認優先度/試算/根拠、record_check()とselect()は現行厳格ゲートを維持。候補出力にeffective_minor/sale_approved=trueを混入させない。通常価格・候補試算・実測を明示した別フィールド。
商品収集PythonのSTARTから対象店舗の必要な更新、売れ筋側は同一の判定参照、サイト点検は検査のみ。クーポンのみ更新/保存商品の再計算が可能。4つ目の独立運用システムを作らない。売れ筋順位そのものは改変しない。

## 6. 実装と受入
(1) 保存済み公式/集約/成功失敗サンプルで正規化・出所グループ化・候補評価を実装。
(2) 既存14テストを維持。追加: 10転載=1根拠、独立した新成功、最新取得≠最新成功、期限境界/時差/日付のみ、コード再利用、条件矛盾、未記載、商品除外、個別失敗≠全体無効、通信断、再取得重複、古い失敗後の新成功、単回/初回、通常/候補/実測の分離、セール二重割引、別scopeの混入禁止、候補からAPPLICABLE不可、失効→通常価格へ復帰、確定注文価格不変、商品/売れ筋同結果、既存DB保護。
(3) 許可済み1店舗で実データ観測→候補順位→同条件の限定的確認→原価再計算→同じSQLiteで両Pythonが同結果を返す。候補上位での実測成功割合、見逃し、確認件数/時間、価格誤反映0を測る。校正前に確率を称さない。Shiekhは候補パイロットだが許可・実クーポン有効性・条件は未検証。実店舗のアクセス・カート操作・本番価格変更は今回実施していない。
(4) 成果をGLM/Claudeの実装・GPT監査へ共有。実装を止めず既存収集と並行。確定原価への未確認割引使用禁止、既存3系統、週2在庫更新は変更しない。

結論：オーナーの考えを「有力候補選定」という実用的な判定層にする。複数情報源の集約により使えそうなコードを先に見つけ、実際の買付条件で確かめる。発掘に使える情報と確定価格に使える証拠を混同しない。候補の確度と原価反映の可否を独立させることで、利益機会を拾いつつ赤字販売を防ぐ。
