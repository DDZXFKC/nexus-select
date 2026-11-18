# AHC クーポン候補判定 GPT監査結果 2026-11-18
対象: bbc7a121、依頼754313e、設計3c6e3fc8。判定 REQUEST_CHANGES。§6(1)(2) 不合格。静的コード監査。18件合格はMuse報告でありGPTによる再実行ではない。
## 合格部分
純粋関数追加、既存select/record系の差分なし、候補出力にeffective_minor/sale_approvedなし、既存14テスト維持。これらは維持する。
## 必須修正
1. assess_campaigns: HIGH/MEDIUM/LOWを廃止し設計A軸6状態に戻す。ホスト数は独立性の証明ではない。origin_group/report_id/raw_refで転載と再取得を重複排除し、不明な独立性は加算しない。公式条件、成功/失敗時刻、出典権威、条件矛盾、期限、否定証拠を評価。取得時刻と成功時刻を分離。単なる2サイト掲載はDISCOVERED。公式失効/確実な期間終了はEXPIRED、明示無効はRETIRED、矛盾はCONFLICT、独立した最近の失敗はLIKELY_INVALID（個別条件の失敗は全体に一般化しない）。24h/7dは調整可能な初期値。
2. evaluate_eligibility(campaign,scope,product_facts): B軸MATCH/EXCLUDED/UNKNOWN。規約の全条件を照合、明示除外優先、欠損はUNKNOWN。実測結果をBに変換しない。条件不明のfalse/空配列を無条件と見なさない。商品属性・セール・初回・地域・数量・最低額・通貨・アカウント・併用・使用上限・販売目的等の根拠を保持。
3. P0 別scope混入: list_candidates(shop_code)が全checksを店舗だけで絞り、evaluate_eligibilityがcampaignだけで最新を選ぶ。例: v1/a1成功後v2/a2失敗でv1までREJECTED、逆順でv2までCONFIRMED。list_candidates(scope,now,max_age_seconds,product_facts)等に変更しcontext(**scope)の完全一致を使う。店舗一覧が必要ならC軸をNOT_CHECKEDにするかscope別に明示する。C軸はNOT_CHECKED/APPLICABLE/NOT_APPLICABLE/UNKNOWN/STALE。最新同時刻矛盾はUNKNOWN、未来記録無視、期限/鮮度/新観測でSTALE、UTC正規化。既存selectと同じ保守的無効化を維持し、候補からrecord_checkを生成しない。
4. P0 期限: 現実装はexpires_at/nowを参照せず期限切れ成功をCONFIRMEDにする。境界now>=expires_atを失効、日付のみ/時差不明は推測せずUNKNOWN。キャンペーン識別はshop/market/code/period/version、コード再利用を分離し旧証拠を新キャンペーンに流用しない。既存レコードの欠損はnull。コードなしは未特定確認キュー。
5. rank_candidates: 三軸と根拠/矛盾/鮮度/試算/確認優先度を保持。EXCLUDED/EXPIRED/RETIREDを有力候補にしない。DISCOVEREDは消さない。条件・権威・成功鮮度・独立性・否定・期限・節約見込・検証コストで決定的に順位付け。試算は通常価格/実測と別。現状は根拠と時刻を捨て、CONFIRMED優先だけなので不合格。
6. 保存層: observations payloadを互換拡張し設計§2のprovenance/時刻/条件/許可項目を保存。record_rawのFalse/空デフォルトと実際の明示値を区別。既存SQLite維持、別正本なし。チェック検索はcontext_id索引を使用し全件走査を避ける。純粋関数はnowを明示し再現性を担保。
## 受入テスト
既存14件をそのまま実行。追加4件は誤仕様を固定しているため期待値を修正する。設計§6(2)全項目を個別テスト化: 10転載=1、独立2新成功、取得≠成功、期限境界/時差/日付のみ、コード再利用、条件矛盾、未記載、商品除外、個別失敗≠全体無効、通信断、再取得重複、古い失敗後の新成功、単回/初回、通常/候補/実測分離、セール二重割引、別scope混入禁止（8項目を各々変える）、候補からAPPLICABLE不可、失効→通常価格、確定注文価格不変、商品/売れ筋同結果、既存DB保護。同時刻矛盾、未来時刻、順序入替、欠損入力も追加。未実装の下流統合項目は未合格と明記し別工程で証明。テスト数だけで合格にしない。
## 引継ぎ
GLMは上記を一括修正、Museは保存済み/合成fixtureで回帰と差分確認、コミットとテスト出力・設計条件対応表をdocsへ登録。既存selectの厳格性を弱めない。新ソース有効化、ライブ取得、カート操作、購入、価格反映は禁止のまま。独立した既存収集やサイト作業を止めない。