# 在庫確認フロー段階1 Local反映・実機確認結果（2026-11-20）

担当：魔王ちゃん（実行担当）／実装：Claude（コミット 4bb0c8e9）／設計：設計v2（docs/stock-check-flow-design-claude-2026-11-20.md、GLM判断 959420af 反映）

## 1. Localへの反映

- 正本：リポジトリ `local-snapshot-2026-11-15/mu-plugins/ahc-stock-check.php`
  - md5 `99bd26119550858896a5953e8c60bc34`、29,478バイト（md5記録コミット 877b1ccf）
- 配置先：`/Users/discodadz/Local Sites/kaitsuke-shop/app/public/wp-content/mu-plugins/ahc-stock-check.php`
  - 同名の既存ファイルは無かったため新規配置（バックアップ不要だった）
- 反映後の検証：Mac側の配置ファイルを吸い上げ、md5sum と cmp で**正本とバイト単位で完全一致**を確認した

## 2. 実装パラメータ（オーナー確定待ち3値の実装値）

- WPオプション `ahc_sc_params` は**未設定**のため、コード初期値がそのまま有効になっている（勝手な変更はしていない）
  - 自動期限切れ：**14日**
  - 返信目安：**3営業日**
  - 保持期間：**6ヶ月**
- 運営通知先オプション `ahc_sc_notify_email` も未設定のため、通知先は admin_email の **kaitsuke.shop@gmail.com**

## 3. 実機確認の結果

対象商品：21376「Premium Old Skool 36 Bandana Black」（フィクスチャでない公開中の可変商品）

### (1) 商品ページのフォーム表示：OK

- 価格（¥31,100）の下に「海外お取り寄せ / 国内送料無料」の表示
- 「ADD TO BAG」が「在庫を確認する」ボタンに置換されている
- 初期状態ではボタン無効＋理由「カラー・サイズを選択してください」を表示
- 「在庫確認は無料です。この時点では注文・決済は発生しません。」と案内3項目（ご注文後に海外ショップから買い付け／検品後にお届け／国内送料無料・配送状況の確認が可能）を表示
- 在庫切れサイズ（US 5〜7.5、11.5、12.5）は SOLD OUT で選択不可、在庫ありサイズ（US 8〜11、12、13）は選択可

### (2) テスト送信と受付ID：OK

- US 8 を選択すると理由表示が消えボタンが有効化、クリックでフォームが展開する
- 入力値：お名前「在庫確認テスト」、メール「stockcheck-test@example.com」、メール（確認）同値、メッセージ「段階1の実機確認テストです。」
- フォーム注記に「通常3営業日以内にメールでご返信します」とプライバシーポリシーへのリンクを確認
- 送信後の画面表示：**「在庫確認のご依頼を受け付けました。受付ID：SC-20261120-001（受付メールをお送りしました。届かない場合もこの受付IDでお問い合わせいただけます）」**
- 送信後はフォーム項目が無効化される

### (3) 保存と非公開設定：OK

- 依頼は1件保存された（投稿ID **21463**、受付ID SC-20261120-001、状態＝受付、投稿ステータスは private）
- CPT `ahc_stock_request` の登録値：public=false、publicly_queryable=false、show_in_rest=false、exclude_from_search=true、query_var=false、rewrite=false
- RESTルートは **0件**（CPTのREST露出なし）
- サイト内検索で受付ID・メールアドレスを検索しても **ヒット0件**
- 日次cron `ahc_sc_daily`（自動期限切れ・保持期間削除）のスケジュール登録あり

### (4) 管理画面：OK

- 管理サイドバーに「在庫確認依頼」メニューが追加されている
- 一覧にテスト依頼1件が表示され、カラム（受付ID／商品・カラー・サイズ／メール／状態／受付日時／更新日時／対応メモ）と行の内容（Premium Old Skool 36 Bandana Black / サイズ：US 8、stockcheck-test@example.com、受付、2026-11-20 12:14）が一致
- 編集画面のメタボックス「依頼内容と対応」に、受付ID・商品・表示価格（¥31,100）・お名前・メール・メッセージ・受付日時が表示される。状態セレクトには6状態（受付／確認中／確保可／確保不可／受付期限切れ／取消）が並び、対応メモのテキストエリアと「更新」ボタンがある
- 状態変更と対応メモの保存：**OK**。管理画面と同じ保存経路（nonce `ahc_sc_admin_save` の検証＋`manage_woocommerce` 権限＋`save_post` フック）を Local 実機上で実行し、次を確認した
  - 状態が 受付（received）→ **確認中（checking）** に変わった
  - 対応メモ「段階1実機確認テスト：状態を受付から確認中へ変更」が保存された
  - `_ahc_sc_updated_at` が前進し、管理一覧の状態列が「確認中」、更新日時が **2026-11-20 12:53**（受付日時 12:14 は不変）に変わったことを画面で確認した
  - 補足：Safari のネイティブプルダウンはリモート操作の仕組み上メニュー項目のマウス確定まで到達できなかったため、状態変更は保存経路の実機実行で検証した（画面表示・項目構成の確認は実機で行っている）

### (5) 重複送信の防止：OK

- 実装のAJAXハンドラ（`ahc_sc_handle_submit`）を Local 実機上で、初回と同じ条件（同一メール stockcheck-test@example.com・同一商品21376・同一サイズ US 8）で実行した
- 応答は `{"success":true,"data":{"duplicate":true,"receipt_id":"","message":"このメールアドレスで、同じ商品・カラー・サイズのご依頼をすでに受け付けています。受付時にお送りしたメールをご確認ください。"}}` で、設計どおりの重複案内が返った
- 新規の依頼は作成されなかった（管理一覧の件数は1件のまま）。既存の受付IDが応答に含まれない（receipt_id が空）ことも確認した

### (6) 通知メール経路：一部確認（Local環境の制約あり）

- メタ `_ahc_sc_mail_log` に `{"requester":true,"notify":true}` が記録され、依頼者宛・運営宛とも wp_mail は true を返した（Localのメールトランスポートが受理したところまで確認）
- ただし Mailpit の画面（http://localhost:10001）が「cannot parse response」エラーで開けず、**受信箱でのメール本文の画面確認はできていない**。実メール到達性の確認は本番側の送信経路確認時に必要

## 4. 証拠

- スクリーンショット（VM側）：`~/workspace/stockcheck-phase1/shots/`
  - shot_product21376_initial.jpg（フォーム初期表示）
  - shot_product21376_form_open.jpg（フォーム展開）
  - shot_product21376_form_filled.jpg（入力済み）
  - shot_product21376_submitted.jpg（送信完了・受付ID表示）
  - shot_admin_list.jpg（管理画面の一覧）
  - shot_admin_edit_metabox.jpg（編集画面のメタボックスと状態セレクト）
  - shot_admin_list_after_status_change.jpg（状態変更後の一覧：確認中・更新日時12:53）
- テスト依頼（投稿21463、受付ID SC-20261120-001、stockcheck-test@example.com）はテストデータとして Local 内に残置した（本番には存在しない）。状態変更テスト後のため、状態は「確認中」、対応メモにテスト記入あり

## 5. 後片付け

- 実機確認用に設置した一時ハーネス（サイトルートの ahc-harness-sc.php／ahc-harness-sc2.php／ahc-harness-sc3.php／ahc-harness-sc4.php／ahc-harness-sc5.php）は確認完了後にすべて削除した
