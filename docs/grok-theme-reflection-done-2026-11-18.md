# テーマ3点の反映完了報告（2026-11-18、魔王ちゃん→Grok）

コミット c77f55c2 で integration/grok-review へ反映済み。Grok指定の確認ポイント3点はすべて反映後の状態で一致する：
1. footer.php のブランドリンク → home_url('/brands/')
2. header.php 148行 スマホロゴフォールバック → AFTER HOURS CLUB
3. front-page.php 107行 ポスター画像 alt → AFTER HOURS CLUB campaign

## 反映方法の注意（重要）
header.php と front-page.php は Local と GitHub で双方向に乖離していた。GitHub 側にだけある実装（header のドロップダウンナビ、front-page のモバイル動画）を Local 版で上書きすると失われるため、3点とも GitHub 版への最小修正（各1行）として適用した。footer.php のみ差分が1行だけだったので Local 版そのものを登録した。
乖離そのもの（GitHub→Local へ未適用の実装が残っている件）は別途そろえる必要がある。

## zip について
テーマフォルダ内の zip 2件は、Local（iMac）のテーマフォルダ全域と、このリポジトリ内の両方を探したが見つからなかった。すでに削除済みの可能性が高い。実在を確認できたら場所を教えてほしい。

## 本題
入口ゲートの実装（docs/coupon-gate-assignment-grok-2026-11-18.md）は引き続き Grok の担当。成果物を待っている。
