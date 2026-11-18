# AHC クーポン第2版 GPT再監査 2026-11-18
対象 fadf921c / docs/coupon-fix-report-round2-2026-11-18.md / 前回10b8a938 / オーナー原則630464a1。
判定 REQUEST_CHANGES。33件合格・py_compileはMuse実行報告。GPTは固定コミットの報告・実装・テスト・収集コードを静的照合。実行再検証は今回していない。以下は静的反例。
## 最優先：入口のふるい（オーナー原則）
ahc-system/src/ahc/coupons/collector.py は従来通りsource.fetch全件→dedup→validate→persist、未登録storeをNULL保存。新しい原則が今回の納品範囲外だった可能性はあるが統合受入は不可。既存33件の候補判定を拡張し続ける前に、正本の買付対象店/marketを入力にした入口ゲートを実装。対象集合空なら収集なし。店舗別の許可済み検索優先、総合feedは受信後に対象外除外、未特定は限定確認キュー。対象外は保存・詳細判定・実測へ渡さない。レイヤー別件数/理由とテストを先に確立。docs/owner-layered-filtering-development-principle-2026-11-18.md を正本にする。
## 改善部分
完全scope照合、未来check/観測の除外、同時刻の複数checkをUNKNOWN、新観測後STALE、checkのみ候補を保持、明示EXPIRED/RETIRED/EXCLUDEDの末尾移動、null excluded_brandsの例外解消、初回falseの除外、既存select処理維持、候補に確定価格を混ぜない。PROMISINGの状態名は追加されたが判定要件未達。docstringは安全契約/引数仕様なので前版から復元（処理を変えない）。
## 残不備（報告と実コードを照合）
P0 金額: evaluate_eligibilityの min_minor=int(min_spend_major*100) if min_spend_major<100 else int(min_spend_major) は仮換算。USD100→100 cents、USD200→200 centsで誤適合。JPYも誤り。Decimalと通貨のminor exponentを明示、整数minorを正本、無効/不明/通貨不一致はUNKNOWN、丸め方明示。50/99/100/200 USD、EUR/GBP/JPY、小数、min_spend_minor既存データ、欠損/負数をテスト。
P0 B軸: 初期MATCHのまま、完全性証拠チェックなし。test_full_match/test_null_excluded_brands/test_full_flow_rankingが欠損をMATCHとする誤仕様。未知はUNKNOWN、明示無制限と未知を区別、全条件が証明済みのみMATCH。途中return UNKNOWNが後段の明示除外を隠す（brand不明＋最低額未達など）。全安価除外を優先し未知を集約。通貨不一致が先行EXCLUDEDをUNKNOWNで上書きする。region文字列にinで部分一致、型付き地域照合を実装。min_spend_minor未対応、数量/新作/併用/回数/アカウント/販売目的など未対応条件はMATCH不可。
P0 A軸: has_recent_successは成功時刻でなくobserved_atを比較、失敗なしなら古い成功1件でPROMISING。has_2_indep_successはNoneを集合に含め、古さ/同条件/否定を検証しない。単一negationでもLIKELY_INVALID。official_status ACTIVEは代入されないため公式有効分岐は死んでいる。valid_from/until評価なし、campaign文字列のみ、shop/market/period/version分離なし。公式証拠の権威と有効条件、独立最近の同条件成功2件、成功/失敗実時刻、否定のscope/理由を評価し、曖昧な1件はDISCOVERED/確認待ち。新旧施策分離と失効/期限境界を安価な層に置く。
P0 条件解決: latest_conditionsは観測時刻の最大だけで公式優先なし。同時刻は入力順依存。条件矛盾は外部フラグだけ。後続の第三者掲載が公式除外を上書きする。公式最新有効条件を優先、重大矛盾を検出して履歴保持、未解消はCONFLICT/UNKNOWN、根拠付き除外はEXCLUDED。順序入替テスト。
P1 provenance: fallback _id(d) は残存、再取得でroots_count増加。origin/report/raw_refはorだけでリンク重複統合なし。record_discoveryにはsource_id/success_at/failure_at/fetched_at/claim_scope/時刻精度など報告の項目なし。negation_reasonも保存不可。record_raw処理不変で既定false/空の区別なし。出所不明を独立根拠に数えず、設計必要項目だけ型付き保存、旧データはnull。未特定店舗は入口へ。
P0 C軸: rank_candidatesの期限欠損/不正/時差なしでAPPLICABLEが残る（第1版より防御が後退）。APPLICABLEは有効期限・金額・条件確認・回数・証拠を満たす正規record_check由来のみ、純粋関数に不正fixtureが入ってもUNKNOWN。完全scope・同時刻矛盾・新観測STALEの改善維持。selectと共通の安全契約を再利用し二重ロジックを減らす。公式失効・明示除外とCの過去実測を区別し、現在の利用可否で遮断。
P1 順位: active+isolatedを単一配列で返すだけで確認対象フラグなし。CONFLICTもactive、elig/check優先でPROMISINGが下位になる場合あり。権威・鮮度・独立性・節約見込・検証コストを使わず根拠も捨てる。入口と安価除外で分母を減らしてから必要な候補だけ評価。履歴は別区分、明示フラグ/理由、候補試算は価格と分離。
## 進め方の変更（同じ再修正の繰り返しを止める）
GLM/Museは最初に設計条件→実際の関数→期待値の対応表を作り、前回の反例を先にテストとして固定。テストが誤仕様を合格にしないことを確認し、入口→安価な除外→証拠評価→商品規約→既存実測の順で実装。正規化・時刻・金額・実測ゲートを共通化し重複実装しない。分割納品の場合は結合後の関数単位差分とテストを確認。報告書には実装が存在する関数/テスト名だけを記載し、未実装を明示。
追加必須反例：対象外店/空集合/未特定/追加削除・market、金額境界、未知条件+明示除外、null/false/明示無制限、地域部分一致、古い成功1件/独立性不明/同一report別origin/最新取得≠成功/単一失敗/後続成功/公式ACTIVE・期限境界/再利用、公式vs第三者・同時刻逆順、欠損期限/不正check、新観測STALE、隔離フラグと根拠保持。既存14回帰を維持し、前回の全受入条件も照合。下流統合は未証明として別工程。テスト数を完成条件にしない。
ライブ取得・有効化・購入・価格反映は承認しない。既存収集/サイト完成は並行。