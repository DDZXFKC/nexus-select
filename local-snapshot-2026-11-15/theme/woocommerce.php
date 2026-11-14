<?php
/** WooCommerce routing: product pages use the theme's dedicated template. */
defined('ABSPATH') || exit;
if (is_singular('product')) {
    wc_get_template('single-product.php');
    return;
}
if (is_product_category()) {
    $nx_cat_template = locate_template('taxonomy-product_cat.php');
    if ($nx_cat_template) {
        include $nx_cat_template;
        return;
    }
}
get_header('shop');
woocommerce_content();
get_footer('shop');
