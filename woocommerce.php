<?php
/** WooCommerce routing: product pages use the theme's dedicated template. */
defined('ABSPATH') || exit;
if (is_singular('product')) {
    wc_get_template('single-product.php');
    return;
}
get_header('shop');
woocommerce_content();
get_footer('shop');
