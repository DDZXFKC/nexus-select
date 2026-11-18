# 色分解保存：2タブ作成と少数fixture検証（魔王ちゃん実行報告）2026-11-19

GPT検収（実行順1合格）を受けて実施。商品管理ブック（1JdQnCxqS5gqrX6-4hcJBGEx_qFCuJsufUjedbkWnJsg）に「カラーマスター」「商品カラー」の2タブを新規作成し、見本1商品＋fixture 8商品を投入した。

## タブの状態
- カラーマスター：13トークン（black／white／blue／red／beige／yellow／phantom／university red＝既存パレット採用、midnight navy／metallic gold／hyper blue／light armory blue＝下書き、concord＝NIKE範囲の下書き）。
- 商品カラー：9商品（見本＋fixture 8件）。読み戻して件数と構成色数を確認済み。

## fixture 8件の結果
1. 単色（Adidas 100 Thieves Savage、Black）：構成色1件、主色は唯一のfamilyでCONFIRMED。BUYMA下書き ブラック。
2. 2色（Goorin Bros #1 America、White/Blue）：店のMAIN_COLOR_WHITEが先頭色と一致しTAG_SUPPORTED。BUYMA下書き ホワイト。
3. 4色（Nike Air Max DN、Hyper Blue/Midnight Navy/Light Armory Blue/White）：構成色4件を全保存し、表示用は先頭3色のみ。主色の根拠がないためUNKNOWN。BUYMAはマルチカラー候補。
4. 重複色（Nike Burrow、Black/Black/Phantom）：重複を保存・表示とも保持。Phantomのfamilyは下書きのためPARTIAL。
5. ブランド固有色（Nike Dunk Low、White/Concord/University Red）：ConcordをBRAND範囲（NIKE）のトークンとして分離。店タグ（Purple/Red/White）は集合として記録し、色名順とは一致しないことを備考に明記。主色UNKNOWN。
6. タグなし（Jordan 1984 Vintage、Beige/Red）：店タグ皆無でも色名から分解しCONFIRMED。タグ欠落＝色なしではない、を実データで確認。
7. 矛盾（Goorin Bros #4 French Fried、Yellow/Red、MAIN_COLOR_WHITE）：component_status・main_family_statusともCONFLICTで保留。BUYMAもHOLD。自動解消はしていない。
8. 色名なし（Jason Markk Essential Kit、ケア用品）：colorway原文なし、NOT_APPLICABLE。MAIN_COLOR_BLACKタグだけが存在するケース。

## 判断に迷った点（検収で確認したい）
- Phantomのfamilyをグレー系と下書きした（HEXは既存パレットの #E7E2D9）。
- 主色が決まらない多色商品のBUYMAは「マルチカラー候補」とし、確定はしていない。
- Hyper Blue／Light Armory BlueのHEXは候補値（#2E6FDB／#A8C3E0）で未承認。

## 次の段階
GPT検収で問題なければ、Shoe Palace全件（11,777商品）の自動分解と未解決トークンの集約表に進む。BUYMA公式colors.csvの照合は並行して未実施。
