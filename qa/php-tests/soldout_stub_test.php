<?php
// Offline test for mu-plugins/ahc-soldout.php. Run: php qa/php-tests/soldout_stub_test.php
define('ABSPATH', '/');
$F = []; $A = [];
function add_filter($h, $f, $p = 10, $n = 1) { global $F; $F[$h] = $f; }
function add_action($h, $f, $p = 10, $n = 1) { global $A; $A[$h] = $f; }
class P { function __construct($s) { $this->s = $s; } function is_in_stock() { return $this->s; } }
include __DIR__ . '/../../local-snapshot-2026-11-15/mu-plugins/ahc-soldout.php';
$fail = 0; function check($n, $ok) { global $fail; echo ($ok ? 'PASS ' : 'FAIL ') . "$n\n"; if (!$ok) $fail++; }
check('out-of-stock products stay listed', $F['pre_option_woocommerce_hide_out_of_stock_items']() === 'no');
check('availability text OOS -> SOLD OUT', $F['woocommerce_get_availability_text']('在庫切れ', new P(false)) === 'SOLD OUT');
check('availability text in stock unchanged', $F['woocommerce_get_availability_text']('在庫あり', new P(true)) === '在庫あり');
check('variable all-OOS message', $F['woocommerce_out_of_stock_message']('x') === 'SOLD OUT');
global $product;
$product = new P(false); ob_start(); $A['woocommerce_before_shop_loop_item_title'](); $o = ob_get_clean();
check('card badge for OOS', strpos($o, 'SOLD OUT') !== false);
$product = new P(true); ob_start(); $A['woocommerce_before_shop_loop_item_title'](); $o = ob_get_clean();
check('no badge in stock', $o === '');
check('inline variation data up to 200', $F['woocommerce_ajax_variation_threshold'](30) === 200);
exit($fail ? 1 : 0);
