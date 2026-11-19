# GPT検収：注意文言削除・テーマ差分
対象48f5c004、docs/owner-notice-removal-2026-11-19.md。注意文言削除PASS。コミット差分はルートfunctions.phpのpriority35の1行削除のみと報告書追加。Localのphp -l、商品HTMLで0件はMuse報告に基づく。
同コミットのlocal-snapshot-2026-11-15/theme/functions.phpには旧noticeとnexus_term_has_productsの両方が残る。ルート版にはhelperなし（Muse報告）。helperは空カテゴリー非表示の既存機能で削除禁止。歴史snapshotを無断変更せず、実際のdeploy元を特定し、現行Localの全functions.php差分・hash・呼び出し元を確認して現行正本を同期。旧snapshotからの上書き禁止。Claude/Museで現行正本の明示、構文・商品ページnotice0・空/非空カテゴリー表示・既存機能の回帰確認を行う。既存の独立作業を止めない。
今回の削除は暫定注意文言のみ。docs/owner-mandatory-storefront-purchase-flow-2026-11-19.md の最終必須仕様は維持し、今はエラー解消優先。新機能追加なし。