<?php
/**
 * Plugin Name: AHC SOLD OUT display
 * Description: Owner decision 2026-11-20 (docs/owner-decisions-2026-11-20-soldout-golf.md):
 * products/sizes without stock are shown as "SOLD OUT"; listing itself is not stopped by stock.
 * - Out-of-stock products stay listed (hide_out_of_stock_items forced to "no").
 * - Product cards: "SOLD OUT" badge when the product is out of stock (all sizes, for variable products).
 * - Product page / selected size: WooCommerce's out-of-stock text becomes "SOLD OUT"; WooCommerce
 *   itself already refuses add-to-cart for out-of-stock items (no purchase control is added or changed).
 * - Size buttons: sold-out sizes are disabled and labelled "SOLD OUT" by theme/main.js.
 * Only WooCommerce's stock status is used; nothing is asserted without it.
 */
if (!defined('ABSPATH')) exit;

// Keep out-of-stock products listed (the shop setting cannot hide them).
add_filter('pre_option_woocommerce_hide_out_of_stock_items', function () { return 'no'; });

// Product page and selected variation: "在庫切れ" -> "SOLD OUT".
add_filter('woocommerce_get_availability_text', function ($text, $product) {
    return ($product && !$product->is_in_stock()) ? 'SOLD OUT' : $text;
}, 20, 2);
add_filter('woocommerce_out_of_stock_message', function () { return 'SOLD OUT'; }, 20);

// Product cards (shop, category, search, [products] shortcode).
add_action('woocommerce_before_shop_loop_item_title', function () {
    global $product;
    if ($product && !$product->is_in_stock()) {
        echo '<span class="ahc-soldout-badge">SOLD OUT</span>';
    }
}, 9);

add_action('wp_head', function () {
    echo '<style>.woocommerce ul.products li.product,.products li.product{position:relative}'
        . '.ahc-soldout-badge{position:absolute;top:8px;left:8px;z-index:2;padding:4px 8px;background:#111;color:#fff;'
        . 'font-size:11px;font-weight:700;letter-spacing:.08em;line-height:1.2;pointer-events:none}'
        . '.single-product .stock.out-of-stock{font-weight:700;letter-spacing:.06em}</style>';
});
