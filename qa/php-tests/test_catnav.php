<?php
/**
 * Unit tests for the category mu-plugins, with minimal WordPress stubs.
 * Run: php qa/php-tests/test_catnav.php   (no WordPress needed)
 */
define('ABSPATH', __DIR__);
$GLOBALS['nx_hooks'] = [];
function add_action($h, $cb, $p = 10, $n = 1) { $GLOBALS['nx_hooks'][$h][] = $cb; }
function is_wp_error($x) { return $x instanceof WP_Error; }
class WP_Error {}
function is_admin() { return false; }
function wp_unslash($v) { return $v; }
function sanitize_text_field($v) { return $v; }
function wp_parse_url($u, $c = -1) { return parse_url($u, $c); }
function trailingslashit($s) { return rtrim($s, '/') . '/'; }
class NxRedirect extends Exception { public $to; public $code; function __construct($to, $code) { $this->to = $to; $this->code = $code; } }
function wp_safe_redirect($to, $code) { throw new NxRedirect($to, $code); }

$base = dirname(__DIR__, 2) . '/local-snapshot-2026-11-15/mu-plugins/';
require $base . 'nexus-catnav-autoclassify.php';
require $base . 'nexus-catnav-redirects.php';

$fail = 0; $n = 0;
function check($name, $cond, $detail = '') { global $fail, $n; $n++; if (!$cond) { $fail++; echo "FAIL: $name $detail\n"; } }
function sorted($a) { sort($a); return $a; }

// ---- autoclassify: hooks
check('hooked after WooCommerce save (new)', !empty($GLOBALS['nx_hooks']['woocommerce_new_product']));
check('hooked after WooCommerce save (update)', !empty($GLOBALS['nx_hooks']['woocommerce_update_product']));
check('not hooked on save_post_product', empty($GLOBALS['nx_hooks']['save_post_product']));

// ---- classification
$r = nx_catnav_classify(['mens-sneakers'], 'Nike Air Max 90');
check('completes root + group', sorted($r['add']) === ['mens', 'mens-shoes'], json_encode($r));
check('plain sneaker gets no facet', $r['auto'] === [] && $r['review'] === '');

$r = nx_catnav_classify(['mens', 'mens-shoes', 'mens-sneakers'], 'ASICS Novablast 5');
check('running facet', $r['add'] === ['mens-running'] && $r['auto'] === ['mens-running'], json_encode($r));

$r = nx_catnav_classify(['mens-sneakers'], "Nike Air Force 1 '07 Jordan Retro");
check('AF1 never gets a facet', !in_array('mens-basketball', $r['add'], true), json_encode($r));
$r = nx_catnav_classify(['mens-sneakers'], 'Nike Dunk Low Retro');
check('Dunk never gets a facet', $r['auto'] === [], json_encode($r));

$r = nx_catnav_classify(['mens-sneakers'], 'Timberland Euro Hiker Mid');
check('Timberland Euro Hiker -> Boots via model name', in_array('mens-boots', $r['auto'], true), json_encode($r));
$r = nx_catnav_classify(['mens-sneakers'], 'Timberland Sprint Trekker Low');
check('Timberland low shoe is NOT Boots', $r['auto'] === [], json_encode($r));
$r = nx_catnav_classify(['mens-sneakers'], 'Timberland Killington Trekker Low');
check('Timberland non-boot is NOT Boots', $r['auto'] === [], json_encode($r));
$r = nx_catnav_classify(['mens-sneakers'], 'Timberland Premium 6-Inch Waterproof');
check('Timberland 6-Inch is Boots', $r['auto'] === ['mens-boots'], json_encode($r));

// correction: previously auto-added facet that no longer matches is removed
$r = nx_catnav_classify(['mens', 'mens-shoes', 'mens-sneakers', 'mens-boots'], 'Timberland Killington Trekker Low', ['mens-boots']);
check('auto facet removed when rule no longer matches', $r['remove'] === ['mens-boots'] && $r['auto'] === [], json_encode($r));
// a facet set by a person is never removed
$r = nx_catnav_classify(['mens', 'mens-shoes', 'mens-sneakers', 'mens-boots'], 'Timberland Killington Trekker Low', []);
check('manual facet kept', $r['remove'] === [], json_encode($r));
// never remove the last leaf
$r = nx_catnav_classify(['mens', 'mens-shoes', 'mens-boots'], 'Some Shoe', ['mens-boots']);
check('last leaf kept', $r['remove'] === [], json_encode($r));
// still-matching auto facet is kept and remembered
$r = nx_catnav_classify(['mens', 'mens-shoes', 'mens-sneakers', 'mens-running'], 'ASICS Novablast 5', ['mens-running']);
check('matching auto facet kept', $r['remove'] === [] && $r['auto'] === ['mens-running'], json_encode($r));

// unisex: both genders completed with one product
$r = nx_catnav_classify(['mens-sneakers', 'womens-sneakers'], 'ASICS Novablast 5');
check('unisex completes both genders', sorted($r['add']) === sorted(['mens', 'mens-shoes', 'mens-running', 'womens', 'womens-shoes', 'womens-running']), json_encode($r));

// unclassifiable
$r = nx_catnav_classify([], 'Unknown');
check('no gender -> review', $r['review'] === 'gender-missing' && $r['add'] === []);
$r = nx_catnav_classify(['womens'], 'Unknown tee');
check('no leaf -> review', $r['review'] === 'leaf-missing', json_encode($r));

// clothing leaf
$r = nx_catnav_classify(['kids-hoodie'], 'Kids Hoodie');
check('clothing group', sorted($r['add']) === ['kids', 'kids-clothing'], json_encode($r));

// ---- redirects
$terms = [
    'mens-sneakers' => (object) ['term_id' => 30, 'slug' => 'mens-sneakers', 'parent' => 20],
    'mens-shoes' => (object) ['term_id' => 20, 'slug' => 'mens-shoes', 'parent' => 10],
];
function get_term_by($f, $v, $t) { global $terms; return $terms[$v] ?? false; }
function get_term($id, $t) { global $terms; foreach ($terms as $x) if ($x->term_id == $id) return $x; return null; }
function get_term_link($term) { return 'http://shop.local/product-category/mens/mens-shoes/' . $term->slug . '/'; }
$redirect = $GLOBALS['nx_hooks']['template_redirect'][0];
function go($uri, $qs = '') {
    global $redirect;
    $_SERVER['REQUEST_URI'] = $uri . ($qs !== '' ? '?' . $qs : '');
    $_SERVER['QUERY_STRING'] = $qs;
    try { $redirect(); } catch (NxRedirect $e) { return [$e->to, $e->code]; }
    return null;
}
check('basic 301', go('/product-category/mens/mens-sneakers/') === ['http://shop.local/product-category/mens/mens-shoes/mens-sneakers/', 301]);
check('paged 301', go('/product-category/mens/mens-sneakers/page/3/') === ['http://shop.local/product-category/mens/mens-shoes/mens-sneakers/page/3/', 301], json_encode(go('/product-category/mens/mens-sneakers/page/3/')));
check('query kept', go('/product-category/mens/mens-sneakers/', 'orderby=price&filter_size=27') === ['http://shop.local/product-category/mens/mens-shoes/mens-sneakers/?orderby=price&filter_size=27', 301]);
check('paged + query', go('/product-category/mens/mens-sneakers/page/2', 'orderby=date')[0] === 'http://shop.local/product-category/mens/mens-shoes/mens-sneakers/page/2/?orderby=date');
check('unsafe query dropped', go('/product-category/mens/mens-sneakers/', 'x=<script>')[0] === 'http://shop.local/product-category/mens/mens-shoes/mens-sneakers/');
check('new URL not redirected', go('/product-category/mens/mens-shoes/mens-sneakers/') === null);
check('group URL not redirected', go('/product-category/mens/mens-shoes/') === null);
check('unknown leaf not redirected', go('/product-category/mens/mens-foo/') === null);

echo ($fail ? "FAILED $fail / $n\n" : "OK $n tests\n");
exit($fail ? 1 : 0);
