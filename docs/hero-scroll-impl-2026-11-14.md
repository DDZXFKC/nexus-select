# AFTER HOURS CLUB — PCホーム ヒーロー縦スクロール実装案
2026-11-14 / オーナー採用済みの方針 / 実装担当: Muse

## 確定事項
- PCホームのみ。動画（メディアID 18928）を廃止し、ヒーロー（18882）、MEN'S、WOMEN'Sの正式画像を順に縦配置する。
- スライドショー、自動切替、横並びは禁止。通常の縦スクロールに控えめなパララックスを加える。
- 各パネルの高さは現行の clamp(470px,43.7vw,650px)。画像間の余白なし。現行の文字オーバーレイを維持する。
- モバイルの見た目・挙動は変更しない。
- 3枚分の高さは実装後、実表示でオーナー確認。現行PHP/CSSとの照合・調整はMuseが担当。

## front-page.php — PCヒーロー部分
以下は統合用の全文。MEN'S/WOMEN'SのIDは未確認のため0（仮値）。現行テンプレートのオーバーレイを所定位置へ移植し、既存モバイルヒーローには既存クラスを残して ahc-legacy-hero を追加する。既存モバイル用コードの実物を推測で置換しない。

```php
<?php
$ahc_hero_id = 18882;
$ahc_mens_id = 0; // MEN'S 正式画像のメディアIDに置換
$ahc_womens_id = 0; // WOMEN'S 正式画像のメディアIDに置換

$ahc_images = [
    $ahc_hero_id,
    $ahc_mens_id,
    $ahc_womens_id,
];
?>

<section class="ahc-desktop-hero">
    <?php foreach ($ahc_images as $index => $image_id) : ?>
        <?php if (!$image_id) continue; ?>
        <div class="ahc-hero-panel">
            <div class="ahc-hero-image">
                <?php
                echo wp_get_attachment_image(
                    $image_id,
                    'full',
                    false,
                    [
                        'class' => 'ahc-hero-photo',
                        'loading' => $index === 0 ? 'eager' : 'lazy',
                        'fetchpriority' => $index === 0 ? 'high' : 'auto',
                        'decoding' => 'async',
                    ]
                );
                ?>
            </div>
            <?php if ($index === 0) : ?>
                <?php
                /*
                 * 現行のヒーローテキスト・オーバーレイの
                 * HTMLを変更せずここに移植する。
                 */
                ?>
            <?php endif; ?>
        </div>
    <?php endforeach; ?>
</section>
```

## CSS — 全文
1024pxは仮設定。既存テーマのPC境界に揃え、動画制御側にも同じ境界を適用する。

```css
.ahc-desktop-hero {
    display: none;
}

@media screen and (min-width: 1024px) {
    .ahc-legacy-hero {
        display: none !important;
    }

    .ahc-desktop-hero {
        display: block;
        width: 100%;
        margin: 0;
        padding: 0;
    }

    .ahc-hero-panel {
        position: relative;
        width: 100%;
        height: clamp(470px, 43.7vw, 650px);
        overflow: hidden;
        margin: 0;
        padding: 0;
        isolation: isolate;
    }

    .ahc-hero-image {
        position: absolute;
        inset: 0;
        z-index: -1;
        overflow: hidden;
    }

    .ahc-hero-photo {
        display: block;
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center;
    }
}

@supports (animation-timeline: view()) {
    @media screen and (min-width: 1024px)
        and (prefers-reduced-motion: no-preference) {
        .ahc-hero-photo {
            animation: ahc-image-flow linear both;
            animation-duration: auto;
            animation-timeline: view();
            animation-range: entry 0% exit 100%;
        }
    }
}

@keyframes ahc-image-flow {
    from {
        transform: translateY(-2%) scale(1.06);
    }
    to {
        transform: translateY(2%) scale(1.06);
    }
}
```

## 動画停止と統合上の必須事項
CSSで非表示にするだけでは動画の通信・自動再生は停止しない。現行の動画HTML・初期化JSを確認し、モバイル専用の遅延初期化等によりPCで動画ソースの取得・再生を発生させないこと。モバイルでは現行の再生条件を維持する。画面幅変更時にもPCで停止すること。既存HTMLが未提供のため、この部分の具体的な差分はMuseが実物に基づいて作成する。
画像IDを確定し、3枚全ての表示を確認してから適用する。既存テキストの重なり、位置、リンク、可読性を維持する。既存のモバイルテキストは残す。PC・モバイル双方で不要な画像・動画の取得が発生していないかネットワークで確認する（CSS非表示だけでは画像取得も防げない）。
スクロールアニメーション非対応または動きの低減設定時は通常の静止画縦スクロールにフォールバックする。パララックスは装飾であり必須コンテンツを隠さない。

## 合格条件
- PCで正式画像3枚が順に表示され、動画が取得・再生されない。
- 自動切替・横並び・余白・横スクロールなし。各パネルの高さが指定clampに一致。
- 現行オーバーレイとリンクが維持される。画像のトリミング・文字重なり・視認性を確認。
- 対応ブラウザで控えめなパララックス。非対応ブラウザと動きの低減設定で静止画表示。
- モバイルの表示・動画挙動が従来通り。PCとの境界とリサイズも確認。
- 商品一覧までの距離を含め、3枚分の高さは実表示でオーナー確認。
- 商品ページ、注文機能、データベース、本番環境はこの変更の対象外。

## 状態
本書は採用済み方針の実装引き継ぎ資料であり、現行テーマとの照合、Grokの独立レビュー、実機テスト、本番反映は未実施。前回提示CSSに animation-duration: auto を明示し、スクロール連動の意図を明確化した。
