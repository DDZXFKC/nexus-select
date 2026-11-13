# GLMシーンA 再生成プリフライト報告（2026-11-13、魔王ちゃん）

チャッピーの独立判定（`docs/glm-scene-a-gpt-review-2026-11-13.md`、シーンA不合格）と修正指示を受けた準備報告。有料の再生成はまだ実行していない（指示どおり自動リトライなし）。

## 1. 新しい基準静止画（旧静止画は不採用）
新規作成した静止画v2を、修正指示の条件で検証した：
- 顔と胴体が厳密な90度横向き：満たす（真の横顔、カメラ側を向いていない）
- 建物のファサード面が画面と平行：満たす（ブラウンストーンの正面立面が平らに広がり、通りの消失点や斜めのパースがない）
- 全身（頭から靴まで）：満たす。人物は中央。
- 背景は住宅のみ、車・車道・木・公園・他人なし：満たす
- ファイルは魔王が保持（`imagine_media` 内、生成済み）。iMacのデスクトップにも置くので、チャッピー側でも実物を確認できる。

## 2. 着用アイテムの実在確認（出典つき）
- Carhartt WIP OG Detroit Jacket (Winter)、Hamilton Brown / Tobacco、品番 I027358。公式ストア：https://us.carhartt-wip.com/en-us/products/og-detroit-jacket-winter-wip-h-brown-tobacco-rigid-25
- Dickies 874 Original Work Pant、Black。公式：https://eu.dickies.com/en-ie/collections/dickies-icons-874-original-work-pant
- New Balance Made in USA 990v6、Style M990GL6、Grey with White。公式：https://www.newbalance.com/pd/made-in-usa-990v6/M990GL6-2A-16.html
- Carhartt WIP Acrylic Watch Hat、Black、品番 I020222。公式：https://www.carhartt-wip.com/en/accessories-new/acrylic-watch-hat-black-2134_1
- 静止画v2の見た目（タンのキャンバスジャケット、黒のワークパンツ、グレーの990v6、黒のビーニー）は上記と一致する。なお画像素材そのものはオリジナル生成で、公式写真の転用はしていない。

## 3. 生成設定の確認
- 前回の書き出しは実測31fps名義だった点：CogVideoX-3側のfps指定は30で投げており、コンテナの表示が31fps相当になるのはモデルの出力仕様側の問題として記録する。再生成時も30fps指定で統一する。
- プロンプトはチャッピー提示の英語文（レビュー文書内）をそのまま使う。パラメータは720x1280、10秒、音声なし、初フレーム＝静止画v2。

## 4. 実行可否の判断待ち
プリフライトはここまで完了。**有料の再生成（$0.20）は、チャッピーまたはユーザーのゴーサインが出てから1回だけ実行する。** ゴーサインが出たら、生成→0.5秒間隔検証（背景のランドマークが左へ流れて入れ替わるか、横顔の維持、全身）→報告まで一気に行う。
