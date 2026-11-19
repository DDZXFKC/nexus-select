# SOLD OUT 表示の実装（オーナー決定 2026-11-20、Claude）

根拠：docs/owner-decisions-2026-11-20-soldout-golf.md（「在庫がない商品はsold out表示でいい」）、GPT 整理 5bb0bd1 §A。表示だけの変更で、購入導線（在庫確認ボタン等、C工程）には触れていない。ゴルフカテゴリは提案段階のため未着手。

## 変更（正本 local-snapshot-2026-11-15/）
| ファイル | 内容 |
|---|---|
| mu-plugins/ahc-soldout.php（新規） | ①在庫切れ商品も一覧に残す（Woo設定「在庫切れを隠す」を常に無効）②商品カード（一覧・カテゴリ・検索・ホームの新着）に「SOLD OUT」バッジ③商品ページ・選択サイズの「在庫切れ」表示を「SOLD OUT」に。カート投入は WooCommerce 標準どおり在庫切れでは不可（新しいボタン等は追加していない）。 |
| theme/main.js | サイズボタン：WooCommerce のバリエーションデータで在庫切れのサイズは、既存の「選べないサイズ」と同じ見た目（薄く・取り消し線）で押せなくし、読み上げ・ツールチップに「SOLD OUT」を付ける。データが無い場合は SOLD OUT と言わない。 |

デザインは変えていない（サイズボタンの見た目は既存の選択不可と同じ。バッジは黒地白文字の小さな表示）。

## テスト（オフライン、全合格）
- qa/php-tests/soldout_stub_test.php 6件、qa/js-tests/soldout_size_test.js 6件。既存の single_color 10件・size_sort 17件も合格。

## Local 反映（魔王ちゃん、次回テーマ反映時にまとめて）
- 反映ファイル：theme/main.js（md5 下記）、theme/front-page.php・mu-plugins/ahc-fixture-guard.php（167465b の GLM 判断どおり）、mu-plugins/ahc-soldout.php（新規）。
- 確認：在庫切れのSP商品1点（全サイズ在庫切れ）でカードにバッジ・商品ページに SOLD OUT・カート不可。一部サイズだけ在庫切れの商品で、そのサイズが押せない・他は通常。在庫ありの商品に変化なし。PC/スマホ幅。
    3abad94a902191a9eed0a14d7cf6ed40  local-snapshot-2026-11-15/theme/main.js
    bf7023d9606fdc17f513ff0ad324fa34  local-snapshot-2026-11-15/mu-plugins/ahc-soldout.php
