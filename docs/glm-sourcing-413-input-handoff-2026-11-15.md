# GLM改修用資料の引き渡し（2026-11-15）
状態：部分引き渡し。既存コード取得済み。依頼書原文と413点正本は未取得。以下の要件は確認できた指示の再構成であり原文の代替ではない。

## 1. ソース
固定版: dc21a68dc80cfd5bebc85012b412d3de8afc03f5
- [sourcing_gate.py](https://github.com/DDZXFKC/nexus-select/blob/dc21a68dc80cfd5bebc85012b412d3de8afc03f5/research/online/local-pkg/sourcing_gate.py)
- [stage2_review.py（依存）](https://github.com/DDZXFKC/nexus-select/blob/dc21a68dc80cfd5bebc85012b412d3de8afc03f5/research/online/local-pkg/stage2_review.py)
- [test_sourcing_gate.py](https://github.com/DDZXFKC/nexus-select/blob/dc21a68dc80cfd5bebc85012b412d3de8afc03f5/research/online/local-pkg/test_sourcing_gate.py)
- [既存実行仕様](https://github.com/DDZXFKC/nexus-select/blob/dc21a68dc80cfd5bebc85012b412d3de8afc03f5/docs/sourcing-gate-runbook-2026-11-14.md)
- [VM単独実行報告](https://github.com/DDZXFKC/nexus-select/blob/dc21a68dc80cfd5bebc85012b412d3de8afc03f5/research/online/local-pkg/standalone-fresh-run-2026-11-15/run-report.md)
現行gateは正規化済み証拠のオフライン判定であり、スクレイパーではない。外部リストの読込・収集・再開は別層で実装し、既存のHOLDゲートを維持する。

## 2. 依頼書（確認できた指示の再構成、原文未取得）
原文名: docs/glm-sourcing-413-modification-request-2026-11-15.md。GitHub両ブランチで404、完全なClaude共有URLも未取得。
- 商品×カラー×サイズを1行とし、不明値は内部null・CSV「不明」。推測補完なし。原本の行ID・SKU・URL・確認日時・サイズ体系を追跡する。
- 価格の観測状態（実測／想定／不明）と用途（仕入価格／出品価格／成約価格）を別フィールドで保持。サイズ・SKU・カラー・状態・確認日時が一致しない参照価格を成約根拠にしない。BUYMA検索不成立を該当なしとしない。原価の全項目が確認できた実測仕入のみ利益判定に使う。想定価格で確定利益を計算しない。公式で取得不可なら許可された正規取扱店を調査。
- 自動出品なし、全行HOLDを初期状態とする。承認は人のみ。人が承認しても必須条件不足ならHOLD維持。承認と適格性の判定を分離。
- 403等は理由を記録し独立対象を継続。プロキシ等で制限を迂回しない。手入力価格の入口 manual_prices.csv は証拠・確認日時・識別子を要求し、入力だけで実測認定しない。
- 413点の外部リストを対象とする。間隔設定、途中再開、正常結果の保存、requirements.txt。GLM担当は改修のみ、実行は魔王ちゃんのiMac。原本仕様確定前に架空のヘッダーを固定しない。
- 差分計画は evaluate/run/main と別の読込・収集アダプター、既存回帰テストへの影響を特定すること。データ取得・価格の正確性・利益・承認を独立検証する。WordPress書込・買付・公開・新規課金なし。

## 3. 413点対象リスト（正本待ち）
オーナーが魔王ちゃんに直接依頼してスクレイピングさせたデータ。GLMの8候補、VM新規取得8件、公開済み197件とは別。正本のパス・形式・ヘッダー・件数の単位・ハッシュは未確認。公開GitHubの既存candidates.csv/jsonは代替しない。
魔王ちゃんへ：iMac上の元の413点リストと依頼書原文を特定し、原本を変更せず、非公開の共有経路でGLMに提供する。ファイル名、形式、文字コード、ヘッダー（JSONならキーと階層）、413の集計単位、行数、SHA256を添える。個人情報・秘密・非公開仕入データを公開リポジトリに載せない。公開側には受領可否と非機密の構造情報のみ記録。ユーザーにコピペを依頼しない。
GLMへ：ソース構造分析と外部入力に依存しない差分計画は先行可能。原本の読込マッピング確定・413点実データ検証は正本受領後。原文とこの再構成が異なる場合は原文と最新のオーナー指示を優先。未取得を取得済みと報告しない。
