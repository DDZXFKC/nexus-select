<?php if (!defined('ABSPATH')) exit; ?>
<?php get_header(); ?>
<?php
/* PC-only editorial homepage. Mobile/tablet markup below is unchanged. */
$nexus_pc_shop = function_exists('wc_get_page_permalink') ? wc_get_page_permalink('shop') : home_url('/shop/');
$nexus_pc_shop = $nexus_pc_shop ?: home_url('/shop/');
$nexus_pc_men = get_term_by('slug', 'mens', 'product_cat');
$nexus_pc_women = get_term_by('slug', 'womens', 'product_cat');
$nexus_pc_men_link = $nexus_pc_men && !is_wp_error($nexus_pc_men) ? get_term_link($nexus_pc_men) : $nexus_pc_shop;
$nexus_pc_women_link = $nexus_pc_women && !is_wp_error($nexus_pc_women) ? get_term_link($nexus_pc_women) : $nexus_pc_shop;
$nexus_pc_hero = absint(get_theme_mod('nexus_pc_hero_image', 0));
$nexus_pc_men_img = absint(get_theme_mod('nexus_pc_men_image', 0));
$nexus_pc_women_img = absint(get_theme_mod('nexus_pc_women_image', 0));
?>
<div class="nexus-pc-home" id="nexus-pc-home">
  <section class="nexus-pc-hero" aria-label="SELECTED WORLD">
    <?php if ($nexus_pc_hero) : ?>
      <?php echo wp_get_attachment_image($nexus_pc_hero, 'full', false, ['class'=>'nexus-pc-hero__image','loading'=>'eager','fetchpriority'=>'high','alt'=>'NEXUS SELECT editorial collection']); ?>
    <?php endif; ?>
    <div class="nexus-pc-hero__content">
      <p class="nexus-pc-hero__eyebrow">NEXUS SELECT</p>
      <h1>SELECTED<br>WORLD</h1>
      <p class="nexus-pc-hero__sub">GLOBAL FASHION SELECT SHOP</p>
      <span class="nexus-pc-hero__rule" aria-hidden="true"></span>
      <p class="nexus-pc-hero__jp">世界から、まだ知らない一着を。</p>
      <a class="nexus-pc-hero__cta" href="<?php echo esc_url($nexus_pc_shop); ?>">SHOP NOW <span aria-hidden="true">→</span></a>
    </div>
  </section>
  <div class="nexus-pc-benefits" aria-label="サービスの特徴">
    <div><span aria-hidden="true">✈</span> 海外限定アイテムをセレクト</div>
    <div><span aria-hidden="true">◇</span> 安心の購入サポート</div>
    <div><span aria-hidden="true">▣</span> 追跡で配送状況を確認</div>
  </div>
  <section class="nexus-pc-arrivals" aria-labelledby="nexus-pc-arrivals-title">
    <div class="nexus-pc-section-heading">
      <h2 id="nexus-pc-arrivals-title">NEW ARRIVALS</h2>
      <a href="<?php echo esc_url($nexus_pc_shop); ?>">VIEW ALL <span aria-hidden="true">→</span></a>
    </div>
    <?php
    if (function_exists('wc_get_products')) {
      $nexus_pc_ids = array_map('absint', wc_get_products(['status'=>'publish','limit'=>6,'orderby'=>'date','order'=>'DESC','return'=>'ids']));
      if ($nexus_pc_ids) {
        echo do_shortcode('[products ids="'.esc_attr(implode(',', $nexus_pc_ids)).'" columns="6" orderby="post__in"]');
      }
    }
    ?>
  </section>
  <section class="nexus-pc-categories" aria-label="コレクション">
    <a class="nexus-pc-category nexus-pc-category--men" href="<?php echo esc_url($nexus_pc_men_link); ?>">
      <?php if ($nexus_pc_men_img) echo wp_get_attachment_image($nexus_pc_men_img, 'large', false, ['loading'=>'lazy','alt'=>'MEN collection']); ?>
      <span class="nexus-pc-category__text"><strong>MEN</strong><small>COLLECTION <span aria-hidden="true">→</span></small></span>
    </a>
    <a class="nexus-pc-category nexus-pc-category--women" href="<?php echo esc_url($nexus_pc_women_link); ?>">
      <?php if ($nexus_pc_women_img) echo wp_get_attachment_image($nexus_pc_women_img, 'large', false, ['loading'=>'lazy','alt'=>'WOMEN collection']); ?>
      <span class="nexus-pc-category__text"><strong>WOMEN</strong><small>COLLECTION <span aria-hidden="true">→</span></small></span>
    </a>
  </section>
  <section class="nexus-pc-brand-index" id="nexus-pc-brands" aria-labelledby="nexus-pc-brand-title">
    <h2 id="nexus-pc-brand-title">SHOP BY BRAND</h2>
    <?php $nexus_pc_brands = taxonomy_exists('pa_brand') ? get_terms(['taxonomy'=>'pa_brand','hide_empty'=>true,'orderby'=>'count','order'=>'DESC','number'=>8]) : []; ?>
    <?php if (!is_wp_error($nexus_pc_brands) && $nexus_pc_brands) : ?>
      <nav class="nexus-pc-brand-index__links" aria-label="ブランド別商品一覧">
        <?php foreach ($nexus_pc_brands as $nexus_pc_brand) : ?>
          <a href="<?php echo esc_url(get_term_link($nexus_pc_brand)); ?>"><?php echo esc_html($nexus_pc_brand->name); ?></a>
        <?php endforeach; ?>
      </nav>
    <?php endif; ?>
  </section>
</div>
<div class="nexus-pc-home__original">


<style>
.nx-hero-slides{position:relative;aspect-ratio:4/5}
.nx-hero-slides img{position:absolute;inset:0;width:100%;height:100%;max-height:none;object-fit:cover;opacity:0;animation:nxHeroFade 28s infinite}
.nx-hero-slides img:first-child{opacity:1}
.nx-hero-slides img:nth-child(2){animation-delay:7s}
.nx-hero-slides img:nth-child(3){animation-delay:14s}
.nx-hero-slides img:nth-child(4){animation-delay:21s}
@keyframes nxHeroFade{0%{opacity:0}4%{opacity:1}25%{opacity:1}29%{opacity:0}100%{opacity:0}}
@media (prefers-reduced-motion:reduce){.nx-hero-slides img{animation:none;opacity:0}.nx-hero-slides img:first-child{opacity:1}}
</style>
<section class="nexus-v08-hero">
  <div class="nexus-v08-hero__content">
    <p class="nexus-v08-hero__eyebrow">WORLDWIDE STREET SELECTION</p>
    <h1 class="nexus-v08-hero__title">BEYOND<br>BORDERS.</h1>
    <p class="nexus-v08-hero__lead">世界のストリートから、まだ出会っていない一足を。</p>
    <a class="nexus-v08-button" href="<?php echo esc_url(home_url('/shop/')); ?>">EXPLORE COLLECTION</a>
  </div>
  <figure class="nexus-v08-hero__media nx-hero-slides">
    <img src="<?php echo esc_url(content_url('/uploads/2026/11/nexus-hero-season-autumn.jpg')); ?>" alt="NEXUS SELECT 季節のエディトリアル（秋）" loading="eager" fetchpriority="high">
    <img src="<?php echo esc_url(content_url('/uploads/2026/11/nexus-hero-season-winter.jpg')); ?>" alt="NEXUS SELECT 季節のエディトリアル（冬）" loading="lazy">
    <img src="<?php echo esc_url(content_url('/uploads/2026/11/nexus-hero-season-spring.jpg')); ?>" alt="NEXUS SELECT 季節のエディトリアル（春）" loading="lazy">
    <img src="<?php echo esc_url(content_url('/uploads/2026/11/nexus-hero-season-summer.jpg')); ?>" alt="NEXUS SELECT 季節のエディトリアル（夏）" loading="lazy">
  </figure>
</section>

<?php
$nexus_new_ids = [];
$nexus_featured_ids = [];

if (class_exists('WooCommerce')) {
    /*
     * NEW ARRIVALS
     * Latest 8 published products.
     */
    $nexus_new_ids = wc_get_products([
        'status'  => 'publish',
        'limit'   => 8,
        'orderby' => 'date',
        'order'   => 'DESC',
        'return'  => 'ids',
    ]);

    $nexus_new_ids = array_map('absint', $nexus_new_ids);

    /*
     * FEATURED DROPS
     * Exclude every product already shown in NEW ARRIVALS.
     */
    $nexus_featured_ids = wc_get_products([
        'status'   => 'publish',
        'limit'    => 8,
        'featured' => true,
        'exclude'  => $nexus_new_ids,
        'orderby'  => 'date',
        'order'    => 'DESC',
        'return'   => 'ids',
    ]);

    $nexus_featured_ids = array_map('absint', $nexus_featured_ids);
}
?>

<section class="nexus-v08-section">
  <div class="nexus-v08-section__head">
    <h2>NEW ARRIVALS</h2>
    <a href="<?php echo esc_url(home_url('/shop/')); ?>">VIEW ALL</a>
  </div>
  <?php
  if (!empty($nexus_new_ids)) {
      echo do_shortcode(
          '[products ids="' .
          esc_attr(implode(',', $nexus_new_ids)) .
          '" columns="4" orderby="post__in"]'
      );
  }
  ?>
</section>

<section class="nexus-v08-section">
  <div class="nexus-v08-section__head">
    <h2>FEATURED DROPS</h2>
    <a href="<?php echo esc_url(home_url('/shop/')); ?>">VIEW ALL</a>
  </div>
  <?php
  if (!empty($nexus_featured_ids)) {
      echo do_shortcode(
          '[products ids="' .
          esc_attr(implode(',', $nexus_featured_ids)) .
          '" columns="4" orderby="post__in"]'
      );
  }
  ?>
</section>

<section class="nexus-v08-section" id="brands">
  <div class="nexus-v08-section__head">
    <h2>SHOP BY BRAND</h2>
  </div>
  <?php
  $nexus_brands = get_terms([
    'taxonomy' => 'pa_brand',
    'hide_empty' => true,
    'orderby' => 'count',
    'order' => 'DESC',
  ]);
  if (!is_wp_error($nexus_brands) && !empty($nexus_brands)) :
  ?>
  <div class="nexus-v08-brands">
    <?php foreach ($nexus_brands as $nexus_brand) : ?>
      <a class="nexus-v08-brand" href="<?php echo esc_url(get_term_link($nexus_brand)); ?>">
        <span><?php echo esc_html($nexus_brand->name); ?></span>
        <small><?php echo esc_html(number_format_i18n($nexus_brand->count)); ?></small>
      </a>
    <?php endforeach; ?>
  </div>
  <?php endif; ?>
</section>

<section class="nexus-v08-guide">
  <h2>HOW IT WORKS</h2>
  <p>掲載商品は通常購入できます。掲載のない商品は「買付リクエスト」から相談できます。海外から取り寄せるため、到着まで約2〜3週間かかります。</p>
  <?php if (get_post(16) && 'publish' === get_post_status(16)) : ?>
  <a class="nexus-v08-button nexus-v08-button--ghost" href="<?php echo esc_url(get_permalink(16)); ?>">買付リクエスト</a>
  <?php endif; ?>
</section>


</div>
<?php get_footer(); ?>
