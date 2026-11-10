<?php if (!defined('ABSPATH')) exit; ?>
<!doctype html>
<html <?php language_attributes(); ?>>
<head>
<meta charset="<?php bloginfo('charset'); ?>">
<meta name="viewport" content="width=device-width, initial-scale=1">
<?php wp_head(); ?>
</head>
<body <?php body_class('nexus-v08'); ?>>
<?php wp_body_open(); ?>
<?php
$mens_term = get_term_by(
    'slug',
    'mens',
    'product_cat'
);

$kids_term = get_term_by('slug', 'kids', 'product_cat');

$womens_term = get_term_by(
    'slug',
    'womens',
    'product_cat'
);

$mens_url = (
    $mens_term &&
    !is_wp_error($mens_term)
)
    ? get_term_link($mens_term)
    : '';

$kids_url = ($kids_term && !is_wp_error($kids_term)) ? get_term_link($kids_term) : '';

$womens_url = (
    $womens_term &&
    !is_wp_error($womens_term)
)
    ? get_term_link($womens_term)
    : '';
?>
<?php if (is_front_page()) : ?>
<div class="nexus-pc-topbar" aria-label="PCホーム専用ナビゲーション">
  <a class="nexus-pc-topbar__logo" href="<?php echo esc_url(home_url('/')); ?>">NEXUS SELECT</a>
  <nav class="nexus-pc-topbar__nav" aria-label="PCホームナビゲーション">
    <?php if ($mens_url && !is_wp_error($mens_url)) : ?><a href="<?php echo esc_url($mens_url); ?>">MEN</a><?php endif; ?>
    <?php if ($womens_url && !is_wp_error($womens_url)) : ?><a href="<?php echo esc_url($womens_url); ?>">WOMEN</a><?php endif; ?>
    <?php if ($kids_url && !is_wp_error($kids_url)) : ?><a href="<?php echo esc_url($kids_url); ?>">KIDS</a><?php endif; ?>
    <a href="<?php echo esc_url(home_url('/')); ?>#nexus-pc-brands">BRANDS</a>
    <a href="<?php echo esc_url(home_url('/')); ?>#nexus-pc-arrivals-title">NEW ARRIVALS</a>
    <?php if (get_post(16) && get_post_status(16)==='publish') : ?><a href="<?php echo esc_url(get_permalink(16)); ?>">ABOUT</a><?php endif; ?>
  </nav>
  <div class="nexus-pc-topbar__actions">
    <form role="search" method="get" action="<?php echo esc_url(home_url('/')); ?>"><label class="screen-reader-text" for="nexus-pc-search">商品を検索</label><input id="nexus-pc-search" name="s" type="search" placeholder="SEARCH" required><input type="hidden" name="post_type" value="product"><button type="submit" aria-label="検索">⌕</button></form>
    <a aria-label="マイアカウント" href="<?php echo esc_url(function_exists('wc_get_page_permalink') ? wc_get_page_permalink('myaccount') : home_url('/my-account/')); ?>">♙</a>
    <a aria-label="カート" href="<?php echo esc_url(function_exists('wc_get_cart_url') ? wc_get_cart_url() : home_url('/cart/')); ?>">▢<span class="nexus-pc-topbar__count"><?php echo esc_html(function_exists('WC') && WC()->cart ? WC()->cart->get_cart_contents_count() : 0); ?></span></a>
  </div>
</div>
<?php endif; ?>
<header class="nexus-v08-header">
  <div class="nexus-v08-header__inner">
    <nav class="nexus-v08-nav nexus-v08-nav--left" aria-label="Primary">
      <a href="<?php echo esc_url(home_url('/shop/')); ?>">SHOP</a>
      <a href="<?php echo esc_url(home_url('/')); ?>#brands">BRANDS</a>
      <?php if ($mens_url && !is_wp_error($mens_url)) : ?>
        <a href="<?php echo esc_url($mens_url); ?>">MEN'S</a>
      <?php endif; ?>
      <?php if ($womens_url && !is_wp_error($womens_url)) : ?>
        <a href="<?php echo esc_url($womens_url); ?>">WOMEN'S</a>
      <?php endif; ?>
      <?php if ($kids_url && !is_wp_error($kids_url)) : ?>
        <a href="<?php echo esc_url($kids_url); ?>">KIDS</a>
      <?php endif; ?>
    </nav>
    <a class="nexus-v08-logo" href="<?php echo esc_url(home_url('/')); ?>"><?php bloginfo('name'); ?></a>
    <div class="nexus-v08-header__actions">
      <a href="<?php echo esc_url(home_url('/?s=')); ?>">SEARCH</a>
      <a href="<?php echo esc_url(wc_get_cart_url()); ?>">BAG (<?php echo esc_html(WC()->cart ? WC()->cart->get_cart_contents_count() : 0); ?>)</a>
    </div>
  </div>
</header>
<main class="nexus-v08-main">
