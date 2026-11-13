# §27 限定ライブパイロット（ステップ3）実行報告

実行：魔王ちゃん（iMac、pkg-s27-recon＝§26環境＋§27の2ファイル、突き合わせ192/192合格済みの環境）。

## 条件
- 設定：bstn-category-s27.json（承認済み単一シード Men Footwear、間隔5秒、予算10、reviewed_at は実行当日へ更新。許可根拠は当日の規約・robots再確認ログ terms-recheck-2026-11-14.log）。
- 実行：`stage3_persistent_discovery.py --cap 10 --start 1 --end 2 --detail-run s27p-001 --detail-limit 5`
- 永続DB：bstn-s27.sqlite（新規キャンペーン）。

## 結果
- リクエスト：**8件すべてOK**（robots 1＋一覧 2＋詳細 5）。失敗・リトライなし。上限（cap 10／予算10）内。
- 候補：ユニーク **187件**を永続台帳へ記録。キャプチャ2件、ドリフトなし。
- 詳細：先頭5商品が完了（キュー DONE 5件、40行、構造検証 PASS、detail_queue_complete=true）。
- 全件 HOLD のまま。published=0、approved_for_import=false、actual_import=NOT_RUN。
- coverage=PARTIAL、catalog_complete=false（全件取得の主張はしない）。

## 状態
永続キャンペーンは継続可能（同じDB・同じスコープで次ページ以降を上限管理しながら進められる）。§27の残ゲートはこれで消化済み。
