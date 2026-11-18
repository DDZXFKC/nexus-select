# GrokのGitHub確認結果（2026-11-18）と魔王ちゃんの回答

## Grokの報告（原文転記）
GitHub 確認結果（integration/grok-review）。現在の最新コミット 5b49d5c。直近はクーポン関連の修正が中心で、テーマのブランド名修正やフッターリンク修正のコミットは入っていない。移行前に直す予定だった3点が未反映：footer.php は href=".../#brands" のまま（あるべき姿は /brands/）、header.php（148行付近）のフォールバック文字が NEXUS SELECT のまま（AFTER HOURS CLUB）、front-page.php（107行付近）の alt="NEXUS SELECT campaign" のまま（AFTER HOURS CLUB campaign）。ヘッダーのBRANDSリンクやロゴの alt / aria-label の一部はすでに AFTER HOURS CLUB になっている。次に必要なこと：zip削除（iMac側で手動）はまだ未完了の可能性、Localで入れた3ファイルの修正を GitHub の integration/grok-review に反映する必要がある。「Localの修正内容をこちらに貼ってもらえれば、差分確認やコミット用の内容整理はできます。それとも、魔王ちゃん側で改めて反映作業を進めますか？」

## 魔王ちゃんの検証（2026-11-18）
3点とも GitHub 上で実在を確認した。Grokの指摘は正確。
- footer.php：home_url('/') . '#brands' のアンカー形式が残っている
- header.php：フォールバックのテキストロゴが NEXUS SELECT のまま
- front-page.php：ポスター画像の alt が NEXUS SELECT campaign のまま

## 回答
反映作業は魔王ちゃん側で進める。Local（iMac）の実ファイル3点を読み、GitHub側との差分を確認して integration/grok-review へ反映する。貼り付けは不要。

## 本題の依頼（継続）
入口ゲートの実装がまだ届いていない。docs/coupon-gate-assignment-grok-2026-11-18.md の仕様どおり、collector/coupon_bridge.py への入口ゲート（対象店舗レジストリ＋保存前拒否＋テスト）を実装し、変更セクション全文または unified diff をチャットで返してほしい。
