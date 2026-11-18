# Shoe Palace cm GPTサイズ表の統合・再適用報告（魔王ちゃん、2026-11-18）

## 受け取り
GPTの成果物3ファイルをChatGPTチャットからダウンロードして受領した。
- brand_size_chart_additions_2026-11-18.csv（673行：cm収録349行＋cm空欄324行）
- brand_size_chart_model_exceptions_2026-11-18.csv（74行）
- brand_size_chart_summary_2026-11-18.csv（ブランド別調査結果41行）
GPTの完成判定は「部分完成」。

## 魔王ちゃんの照合（統合前に実施）
GPT収録分349行について、公式ページと照合した。
- プログラム照合89行（SAUCONY男女・TIMBERLAND男女キッズ）：公式表と全件一致、不一致0。
- 目視照合：DC SHOES（dcshoes.comのCM列と完全一致）、CHAMPION（champion.comのCM列と完全一致）、DR. MARTENS（カナダ公式JPN列と完全一致）、HOKA Men（cl.hoka.comのCM（Japón）列と完全一致）、HOKA Womenモデル別2表（同ページに2表とも実在し、モデル分けと値が一致）、UNDER ARMOUR Kids（日本公式ボーイズ表。K表記→C表記の正規化も正しい）。
- UGG（ugg.com）は表がテキスト取得できず未照合。ON RUNNING Kidsは出典ページの表を確認できず、値はOn公式のJP表記として収録（小数値を含むOn独自表記）。
- 照合できなかった2ブランド分も含め、349行すべてを専用ブックへ収録した。未照合であることは本報告に明記する。

## 専用ブック「ブランドサイズ表」への統合
- 「サイズ表」タブへ349行を追記（合計941行＋見出し）。キー（ブランド＋区分＋USサイズ）で既存592行と重複・矛盾0。
- 「モデル別サイズ表」タブを新設し、モデル別74行を収録。
- 「ブランド調査結果」タブを新設し、調査結果41行を収録。
- cm空欄324行は換算用参照には入れていない（GPTの統合指示どおり）。

## repair再適用（v4参照941行、2回実行・出力完全一致）
- 合算MATCHED 67,196（v3の65,611から+1,585）
- 残りMISSING 10,241（11,826から-1,585）、NOT_APPLICABLE 26,387、SIZE_SYSTEM_REVIEW 10、issues 23,512

## 残りMISSING 10,241の主な内訳と理由
- ADIDAS Kids 2,073：公式が足長のみのため、ルール上入力不可。
- CONVERSE Men 969・Kids 208：JPラベル値が公式に無いため入力不可。
- HOKA Men 903・Women 549、UGG Kids 240・Women 188：今回の公式表はブックに収録済みだが、現行コードの仕様（HOKA・UGGは汎用適用から除外し製品単位のみ）により未適用。HOKA Menは単一の公式表が確認できたため、汎用適用に切り替えるかはGPTの設計判断として確認したい。HOKA Womenはモデルで値が分かれるため製品単位のままが妥当。UGG Kidsは年齢区分の注意あり。
- VANS Men 578・Kids 221：指定サイズの公式対応が未解決（GPT調査結果のとおり）。
- REEBOK Men 348：適用範囲の確認待ち（モデル別ファイル側）。
- BIRKENSTOCK Women 249：JPラベル値未確認。
- CHAMPION Kids 216：公式表未確認。
- ANTA Men 212、VEJA Women 209、NEWBALANCE Kids 197：JPラベル値なし／モデル別／公式表の飛び。

## 次
- HOKA Menの汎用適用可否はGPTの判断待ち。
- 残ブランド（公式表未確認・JPなし系）は、追加調査をしても公式JPラベル値が存在しないものが大半で、推測では埋めない。
