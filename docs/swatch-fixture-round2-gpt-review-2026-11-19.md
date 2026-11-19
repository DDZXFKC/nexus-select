# GPT検収 16:08 JST — fixture修正版・価格リレー
対象 57804fae / Claude実装報告 / Muse readonly prep。価格17c2440/316c5e1はMuseの直接送信、GLM ACK・Phase0着手を報告で確認。成果コードは未確認。厳格ゲート未成立につき価格更新なし。再送不要。

## Local丸窓
FX専用 mapping は承認：9件の合成fixtureに限り、同一のSP/USエクスポートのpidと生成manifestのFX-SP SKUを照合して作成。実商品158件はSP接頭辞だけではmarketの証明にならないので、仮mappingでの読み取りdry-runのみ、apply不可。既存商品変更なし。
fixtureツール実コードの残る安全欠陥：save()後にmarkerとmanifestを書くため、保存直後の例外/中断で孤児が残る。親子ともsave前にupdate_meta_dataでmarker/runを設定し、予定SKUをmanifestに先に記録、再開時にrun+予定SKUで照合・回収する。manifest初回は排他作成、更新はrun固有tmp。removeは子の削除結果も確認し、部分削除後に再開できるようにする。run_id空・重複IDを拒否。削除は個別承認ルール維持（catchのapply案内をdry-runへ変更）。子statusはpublishの場合があるため親draftとguardによる購入不可を実機で確認。Claudeはこの差分だけ修正し既存合格試験を無条件に繰り返さない。Museは並行してFX mapping準備、テーマ差分のバックアップ、既存商品読み取り確認。修正後は9件のLocal実機検証へ直行、公開158件applyなし。本番なし。

## Coordinator
GLM接続返信は設計成果、実機接続の新規検証とは区別。既存Coding Plan実測経路を使用し、旧429経路を再試験しない。bridge案の固定結果ファイルはtask/revision別の新規ファイルへ、空応答/不正応答を成功扱いしない、認証/契約エラーを無条件再試行しない。GPT coreは既存contract再利用、独立検収必須。価格・サイト優先。Issue #3–6の旧担当/状態は新配分と整合させる必要あり。直接受領未確認のものをACK扱いしない。
