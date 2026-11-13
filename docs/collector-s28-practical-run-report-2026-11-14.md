# §28 実用収集 実行報告（オーナー開始指示 9b49c5dd への実行結果）

実行：魔王ちゃん（iMac）。§26で検証済みのコレクタをそのまま使用し、新規開発はしていない。

## 実行前の再確認（2026-11-14）
- BSTN robots.txt：シード・一覧ページ・商品ページすべて取得可。クロール間隔・レート指定なし。
- BSTN 利用規約：scrap / crawler / crawling / spider / automated / robot / data mining の記載は0件。スクレイピング禁止条項なし（ログ terms-recheck-2026-11-14.log）。

## 実行条件
- 設定：bstn-category-s28.json（§26承認済みと同一スコープ＝単一シード Men Footwear、間隔5秒、リクエスト予算10、reviewed_at は当日に更新）。
- DB・運用は新規（bstn-s28.sqlite / s28-practical-001）。リトライなし。

## 結果
- 候補URL：192件（商品187件＋リリース5件）。前回（§26）と同数。
- 詳細処理：先頭5商品が完了（キュー DONE 5件）、バリエーション40行、Woo形式45行、BUYMA形式5行。構造検証 PASS。
- 全件 HOLD のまま。公開0件、インポート未実施（actual_import=NOT_RUN、approved_for_import=false）。
- カバレッジは PARTIAL、catalog_complete=false（全件取得の主張はしない）。

## 成果物の場所
- iMac `/Users/discodadz/nexus-run/sourcing-usable/bstn_candidates_s28.csv`（候補192件）
- iMac `/Users/discodadz/nexus-run/sourcing-usable/bstn_review_s28.csv`（処理済み5商品）
- オーナーへはチャット添付で同内容を納品済み（2026-11-14）。

在庫・原価は未検証のまま（UNVERIFIED_HOLD）。実仕入れの判断時は商品ページで個別確認が必要。
