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
<?php
$nx_dd_children = function ($parent_term) {
    if (!$parent_term || is_wp_error($parent_term)) return [];
    $terms = get_terms(['taxonomy' => 'product_cat', 'parent' => $parent_term->term_id, 'hide_empty' => false, 'orderby' => 'term_id', 'order' => 'ASC']);
    if (is_wp_error($terms) || !$terms) return [];
    $items = [];
    foreach ($terms as $t) {
        $l = get_term_link($t);
        if (is_wp_error($l)) continue;
        $items[] = ['name' => $t->name, 'url' => $l, 'count' => (int) $t->count];
    }
    return $items;
};
$nx_dd_mens = $nx_dd_children($mens_term ?? null);
$nx_dd_womens = $nx_dd_children($womens_term ?? null);
$nx_dd_kids = $nx_dd_children($kids_term ?? null);
$nx_dd_render = function ($label, $url, $children) {
    if (!$url || is_wp_error($url)) return;
    echo '<span class="nx-dd"><a href="' . esc_url($url) . '">' . esc_html($label) . '</a>';
    echo '<span class="nx-dd__panel" role="menu">';
    echo '<a class="nx-dd__all" href="' . esc_url($url) . '">すべて見る</a>';
    $shown = 0;
    foreach ($children as $c) {
        if ($c['count'] < 1) continue;
        echo '<a href="' . esc_url($c['url']) . '">' . esc_html($c['name']) . '<small>' . esc_html($c['count']) . '</small></a>';
        $shown++;
    }
    if (!$shown) echo '<span class="nx-dd__empty">近日追加予定</span>';
    echo '</span></span>';
};
?>
<style>
.nx-dd{position:relative;display:inline-block}
.nx-dd__panel{position:absolute;top:100%;left:50%;transform:translateX(-50%) translateY(8px);min-width:200px;background:#fff;border:1px solid #e3e3e3;box-shadow:0 12px 32px rgba(0,0,0,.08);padding:8px 0;opacity:0;visibility:hidden;transition:opacity .18s ease,transform .18s ease,visibility .18s;z-index:300;text-align:left}
.nx-dd:hover .nx-dd__panel,.nx-dd:focus-within .nx-dd__panel{opacity:1;visibility:visible;transform:translateX(-50%) translateY(0)}
.nx-dd__panel a{display:block;padding:8px 20px;font-size:12px;letter-spacing:.12em;color:#111;white-space:nowrap;text-decoration:none}
.nx-dd__panel a small{color:#999;margin-left:8px;letter-spacing:.02em}
.nx-dd__panel a:hover{background:#f5f5f5}
.nx-dd__panel a.nx-dd__all{border-bottom:1px solid #eee;margin-bottom:6px;padding-bottom:12px}
.nx-dd__panel .nx-dd__empty{display:block;padding:8px 20px;font-size:12px;color:#999;letter-spacing:.12em;white-space:nowrap}
@media(max-width:640px){.nx-dd__panel{left:0;transform:translateY(8px)}.nx-dd:hover .nx-dd__panel,.nx-dd:focus-within .nx-dd__panel{transform:translateY(0)}}
.nx-brands-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:56px 24px;max-width:1080px;margin:48px auto;padding:0 20px}
.nx-brands-grid a.nx-brand-cell{display:flex;flex-direction:column;align-items:center;justify-content:flex-start;text-decoration:none;color:#111;transition:opacity .2s}
.nx-brands-grid a.nx-brand-cell:hover{opacity:.5}
.nx-brands-grid .nx-brand-cell img{width:auto;max-width:190px;object-fit:contain}
.nx-brands-grid .nx-brand-name{margin-top:16px;font-size:13px;letter-spacing:.14em}
.nx-brands-grid .nx-brand-count{font-size:11px;color:#999;margin-top:4px;letter-spacing:.08em}
@media(max-width:640px){.nx-brands-grid{grid-template-columns:repeat(2,1fr);gap:40px 16px;margin:32px auto}}
.nx-search{max-width:880px;margin:0 auto;padding:32px 20px 64px}
.nx-search__title{font-size:22px;margin:0 0 8px;letter-spacing:.06em}
.nx-search__note{color:#555;margin:0 0 20px}
.nx-search__list{list-style:none;margin:0;padding:0}
.nx-search__item{border-top:1px solid #e3e3e3;padding:14px 0}
.nx-search__link{font-weight:600;color:#111;text-decoration:none}
.nx-search__excerpt{margin:6px 0 0;color:#555;font-size:14px;line-height:1.6}
</style>
<?php if (is_front_page()) : ?>
<div class="nexus-pc-topbar" aria-label="PCホーム専用ナビゲーション">
  <a class="nexus-pc-topbar__logo" href="<?php echo esc_url(home_url('/')); ?>">NEXUS SELECT</a>
  <nav class="nexus-pc-topbar__nav" aria-label="PCホームナビゲーション">
    <?php $nx_dd_render('MEN', $mens_url, $nx_dd_mens); ?>
    <?php $nx_dd_render('WOMEN', $womens_url, $nx_dd_womens); ?>
    <?php $nx_dd_render('KIDS', $kids_url, $nx_dd_kids); ?>
    <a href="<?php echo esc_url(home_url('/brands/')); ?>">BRANDS</a>
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
      <a href="<?php echo esc_url(home_url('/brands/')); ?>">BRANDS</a>
      <?php $nx_dd_render("MEN'S", $mens_url, $nx_dd_mens); ?>
      <?php $nx_dd_render("WOMEN'S", $womens_url, $nx_dd_womens); ?>
      <?php $nx_dd_render('KIDS', $kids_url, $nx_dd_kids); ?>
    </nav>
    <a class="nexus-v08-logo" href="<?php echo esc_url(home_url('/')); ?>"><?php bloginfo('name'); ?></a>
    <div class="nexus-v08-header__actions">
      <a href="<?php echo esc_url(home_url('/?s=')); ?>">SEARCH</a>
      <a href="<?php echo esc_url(wc_get_cart_url()); ?>">BAG (<?php echo esc_html(WC()->cart ? WC()->cart->get_cart_contents_count() : 0); ?>)</a>
    </div>
  </div>
</header>
<main class="nexus-v08-main">
