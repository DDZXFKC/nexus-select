# GPT検収：隔離fixture実機QA
対象 docs/swatch-fixture-local-qa-result-2026-11-19.md @22f1c9a9。判定 PASS（隔離fixtureの正常系・安全な復元削除の報告範囲）。SP158一括applyは未承認。
報告上、完全DBバックアップ、単一writer、親9子36、作成前後差分45件のみ、writer9/readback0/other0、再dryrun0、購入拒否、rollback9→0、remove45→0、inventoryバイト一致、注文0を確認。実機画像・ログは未添付でGPT独立再確認未実施。色は実export、画像価格サイズは合成。テーマ3ファイルは残置されておりinventory一致はテーマやDB全体一致を意味しない。
残差を一括確認：当初の指定9件と実際のfixture9件の対応表を提示。報告の実画面6ケースと430pxの3色品以外（同色反復、白、残りのfixture、サイズ変更時の価格在庫、コンソール、複数色way切替は別fixture）を既存証拠で確認し不足だけ再検証。UNKNOWN/HOLDは丸窓なし原文のみと報告、従前仕様の中立表示・未知位置保持と照合し、既知部分も隠すのか等を勝手に変更しない。スクショ/ログをアクセス可能な場所に共有。購入拒否は報告のUI経路に限るためguardの直接POST等のテスト証拠も確認。削除の異常系（空SKU・親不一致・trash・中断）に対する前回指摘は未解決ならClaudeが修正、既存実行成功とは別。
SP158: 仮mapping dryrun158/158/0は前進だが正本のshop+market+pid+単一colorway、SKU、対象meta、原文、状態、HEX、既存meta差分、重複・対象外・価格在庫画像サイズ保護を全行確認した正式dryrun manifestを提出。現在のLocalテーマとGitHubのハッシュも記録。適用直前バックアップ、単一writer、CAS相当の旧値確認、readback、再dryrun0、rollbackを計画。正式dryrunと残差確認後GPT判定までapply禁止。本番・購入禁止。
オーナーのエラー解消最優先指示に従い、新機能を増やさず残差と既存不具合の解消を優先。他の独立作業は止めない。