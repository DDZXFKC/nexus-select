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
.nx-hsearch{display:inline-flex;align-items:center;gap:2px;margin:0}
.nx-hsearch input[type=search]{width:0;opacity:0;padding:0;border:0;background:transparent;font:inherit;transition:width .2s,opacity .2s}
.nx-hsearch:focus-within input[type=search],.nx-hsearch:hover input[type=search]{width:110px;opacity:1;padding:2px 0;border-bottom:1px solid #111}
.nx-hsearch button{background:none;border:0;padding:0;font:inherit;cursor:pointer;letter-spacing:.08em}
.nx-search__form{display:flex;gap:8px;margin:0 0 14px}
.nx-search__form input[type=search]{flex:1;padding:10px 12px;border:1px solid #ccc;font-size:16px}
.nx-search__form button{padding:10px 18px;background:#111;color:#fff;border:0;cursor:pointer;letter-spacing:.08em}
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
    <a href="<?php echo esc_url(home_url('/')); ?>">HOME</a>
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
<?php if (is_front_page()) : ?>
<header class="nx-home-mobile-header" aria-label="モバイルホーム">
  <details class="nx-home-menu">
    <summary aria-label="メニュー"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h18"/></svg></summary>
    <nav aria-label="モバイルメニュー">
      <a href="<?php echo esc_url(home_url('/')); ?>">HOME</a>
      <a href="<?php echo esc_url(home_url('/shop/')); ?>">SHOP</a>
      <?php foreach ([["MEN", $mens_url, $nx_dd_mens], ["WOMEN", $womens_url, $nx_dd_womens], ["KIDS", $kids_url, $nx_dd_kids]] as $nx_group) : ?>
        <?php if ($nx_group[1] && !is_wp_error($nx_group[1])) : ?>
          <a href="<?php echo esc_url($nx_group[1]); ?>"><?php echo esc_html($nx_group[0]); ?></a>
          <?php foreach ($nx_group[2] as $nx_child) : if ($nx_child['count'] < 1) continue; ?>
            <a class="nx-home-menu-child" href="<?php echo esc_url($nx_child['url']); ?>"><?php echo esc_html($nx_child['name']); ?></a>
          <?php endforeach; ?>
        <?php endif; ?>
      <?php endforeach; ?>
      <a href="<?php echo esc_url(home_url('/brands/')); ?>">BRANDS</a>
      <a href="<?php echo esc_url(function_exists('wc_get_page_permalink') ? wc_get_page_permalink('myaccount') : home_url('/my-account/')); ?>">MY ACCOUNT</a>
    </nav>
  </details>
  <?php
  // Only the approved uploaded PNG is used; never substitute a generated font.
  $nx_logo_id = absint(get_theme_mod('nexus_mobile_approved_logo', 0));
  $nx_logo_url = $nx_logo_id && get_post_mime_type($nx_logo_id) === 'image/png' ? wp_get_attachment_url($nx_logo_id) : '';
  ?>
  <a class="nx-home-mobile-logo<?php echo $nx_logo_url ? ' nx-home-mobile-logo--approved' : ''; ?>" href="<?php echo esc_url(home_url('/')); ?>"<?php if ($nx_logo_url) echo ' aria-label="AFTER HOURS CLUB"'; ?>><?php if ($nx_logo_url) : ?><img src="<?php echo esc_url($nx_logo_url); ?>" alt="AFTER HOURS CLUB" style="display:block;width:100%;height:auto;max-width:100%;"><?php else : ?>NEXUS SELECT<?php endif; ?></a>
  <div class="nx-home-mobile-actions">
    <details class="nx-home-search">
      <summary aria-label="商品検索"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></svg></summary>
      <form role="search" action="<?php echo esc_url(home_url('/')); ?>" method="get"><label for="nx-home-search-input">商品検索</label><input id="nx-home-search-input" type="search" name="s" required><input type="hidden" name="post_type" value="product"><button type="submit">検索</button></form>
    </details>
    <a class="nx-home-bag" aria-label="カート" href="<?php echo esc_url(function_exists('wc_get_cart_url') ? wc_get_cart_url() : home_url('/cart/')); ?>"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M5 8h14l1 13H4L5 8Z M9 9V6a3 3 0 0 1 6 0v3"/></svg><span><?php echo esc_html(function_exists('WC') && WC()->cart ? WC()->cart->get_cart_contents_count() : 0); ?></span></a>
  </div>
</header>
<?php endif; ?>
<header class="nexus-v08-header">
  <div class="nexus-v08-header__inner">
    <nav class="nexus-v08-nav nexus-v08-nav--left" aria-label="Primary">
      <a href="<?php echo esc_url(home_url('/')); ?>">HOME</a>
      <a href="<?php echo esc_url(home_url('/shop/')); ?>">SHOP</a>
      <a href="<?php echo esc_url(home_url('/brands/')); ?>">BRANDS</a>
      <?php $nx_dd_render("MEN'S", $mens_url, $nx_dd_mens); ?>
      <?php $nx_dd_render("WOMEN'S", $womens_url, $nx_dd_womens); ?>
      <?php $nx_dd_render('KIDS', $kids_url, $nx_dd_kids); ?>
    </nav>
    <a class="nexus-v08-logo" href="<?php echo esc_url(home_url('/')); ?>"><?php bloginfo('name'); ?></a>
    <div class="nexus-v08-header__actions">
      <form class="nx-hsearch" role="search" method="get" action="<?php echo esc_url(home_url('/')); ?>"><label class="screen-reader-text" for="nx-hsearch-input">商品を検索</label><input id="nx-hsearch-input" name="s" type="search" placeholder="SEARCH" required><input type="hidden" name="post_type" value="product"><button type="submit" aria-label="検索">SEARCH ⌕</button></form>
      <a href="<?php echo esc_url(wc_get_cart_url()); ?>">BAG (<?php echo esc_html(WC()->cart ? WC()->cart->get_cart_contents_count() : 0); ?>)</a>
    </div>
  </div>
</header>
<main class="nexus-v08-main">
