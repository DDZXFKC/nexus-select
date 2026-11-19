<?php
/**
 * Plugin Name: AHC fixture guard
 * Description: Products marked _ahc_fixture=1 (swatch check fixtures, tools/ahc_create_swatch_fixture.php)
 * can never be purchased - not even by an admin who can view drafts. Local QA only; harmless elsewhere
 * because no real product carries the marker.
 */
if (!defined('ABSPATH')) exit;

function ahc_is_fixture_product($product) {
    if (!$product) return false;
    $id = $product->get_id();
    if (get_post_meta($id, '_ahc_fixture', true) === '1') return true;
    $parent = $product->get_parent_id();
    return $parent && get_post_meta($parent, '_ahc_fixture', true) === '1';
}

add_filter('woocommerce_is_purchasable', function ($ok, $product) {
    return ahc_is_fixture_product($product) ? false : $ok;
}, 99, 2);

add_filter('woocommerce_variation_is_purchasable', function ($ok, $variation) {
    return ahc_is_fixture_product($variation) ? false : $ok;
}, 99, 2);

add_filter('woocommerce_add_to_cart_validation', function ($ok, $product_id, $qty, $variation_id = 0) {
    foreach ([$product_id, $variation_id] as $id) {
        if ($id && ahc_is_fixture_product(wc_get_product($id))) {
            wc_add_notice('This is a test fixture and cannot be purchased.', 'error');
            return false;
        }
    }
    return $ok;
}, 99, 4);

// Belt and braces: drop any fixture line that is already in a cart.
add_action('woocommerce_check_cart_items', function () {
    if (!WC()->cart) return;
    foreach (WC()->cart->get_cart() as $key => $item) {
        if (ahc_is_fixture_product($item['data'] ?? null)) WC()->cart->remove_cart_item($key);
    }
});
