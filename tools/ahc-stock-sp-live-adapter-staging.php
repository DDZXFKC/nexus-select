<?php
/**
 * AFTER HOURS CLUB Shoe Palace live Shopify variant adapter — STAGING ONLY.
 * Requires owner-verified offers and verified currency from another provider.
 * Never determines retail price or authorizes cart entry.
 */
defined('ABSPATH') || exit;
if (!function_exists('ahc_sp_live_check_offer')) {
function ahc_sp_live_check_offer($previous, $offer, $woo_product_id, $woo_variation_id, $attrs) {
    if (!is_array($offer) || ($offer['shop'] ?? '') !== 'SP' || $previous !== null) return $previous;
    $unknown = ['stock' => 'UNCONFIRMED', 'reason' => 'supplier_unconfirmed'];
    if (!function_exists('wc_get_product') || !function_exists('wp_safe_remote_get')) return $unknown;
    if (!is_int($woo_product_id) || !is_int($woo_variation_id) || $woo_product_id <= 0 || $woo_variation_id <= 0) return $unknown;
    $parent = wc_get_product($woo_product_id);
    $variation = wc_get_product($woo_variation_id);
    if (!$parent || !$variation || !$parent->is_type('variable') || !$variation->is_type('variation') ||
        (int)$variation->get_parent_id() !== $woo_product_id) return $unknown;
    $parent_sku = (string)$parent->get_sku();
    $sku = (string)$variation->get_sku();
    $supplier_id = (string)($offer['supplier_product_id'] ?? '');
    $supplier_variant_id = (string)($offer['merchant_variant_id'] ?? '');
    $supplier_variant_sku = (string)($offer['merchant_variant_sku'] ?? '');
    if (!preg_match('/^SP-([0-9]+)$/D', $parent_sku, $m) || $m[1] !== $supplier_id ||
        !preg_match('/^[0-9]+$/D', $supplier_variant_id) || !$sku || $sku !== $supplier_variant_sku ||
        ($offer['identity_verified'] ?? null) !== true) return $unknown;
    // Shopify product.js has prices in minor units but no currency field.
    // An independently verified store currency is mandatory.
    if (($offer['verified_currency'] ?? '') !== 'USD') return ['stock'=>'UNCONFIRMED','reason'=>'currency_unverified'];
    $url = (string)($offer['url'] ?? '');
    $parts = wp_parse_url($url);
    if (!is_array($parts) || ($parts['scheme'] ?? '') !== 'https' ||
        ($parts['host'] ?? '') !== 'www.shoepalace.com' || isset($parts['user']) ||
        isset($parts['pass']) || isset($parts['port']) || isset($parts['query']) ||
        isset($parts['fragment']) || !preg_match('~^/products/[a-zA-Z0-9_-]+/?$~D', $parts['path'] ?? '')) return $unknown;
    $endpoint = rtrim($url, '/') . '.js';
    // Redirects disabled; no following merchant URL to another host.
    $response = wp_safe_remote_get($endpoint, [
        'timeout'=>10, 'redirection'=>0, 'limit_response_size'=>1000000,
        'headers'=>['Accept'=>'application/json'],
    ]);
    if (is_wp_error($response)) return ['stock'=>'UNCONFIRMED','reason'=>'supplier_unreachable'];
    if (wp_remote_retrieve_response_code($response) !== 200) return ['stock'=>'UNCONFIRMED','reason'=>'supplier_http_error'];
    $body = wp_remote_retrieve_body($response);
    if (!is_string($body) || strlen($body) > 1000000) return $unknown;
    $data = json_decode($body, true);
    if (!is_array($data) || !isset($data['id'], $data['variants']) ||
        !is_array($data['variants']) || (string)$data['id'] !== $supplier_id) return $unknown;
    $found = [];
    foreach ($data['variants'] as $variant) {
        if (!is_array($variant)) continue;
        if ((string)($variant['id'] ?? '') === $supplier_variant_id &&
            (string)($variant['sku'] ?? '') === $sku) $found[] = $variant;
    }
    if (count($found) !== 1) return ['stock'=>'UNCONFIRMED','reason'=>'variant_identity_mismatch'];
    $v = $found[0];
    if (!array_key_exists('available', $v) || !is_bool($v['available'])) return $unknown;
    if ($v['available'] === false) return ['stock'=>'OUT_OF_STOCK','reason'=>'verified_variant_oos'];
    $cents = $v['price'] ?? null;
    if (!is_int($cents) || $cents <= 0 || $cents > 100000000) return ['stock'=>'UNCONFIRMED','reason'=>'price_unverified'];
    return [
        'stock'=>'IN_STOCK', 'reason'=>'live_variant_verified',
        'current_price'=>['amount'=>number_format($cents / 100, 2, '.', ''), 'currency'=>'USD'],
        'supplier_variant_id'=>$supplier_variant_id,
        'supplier_variant_sku'=>$sku,
        'checked_at_utc'=>gmdate('c'),
    ];
}
}
add_filter('ahc_inline_check_one_offer', 'ahc_sp_live_check_offer', 20, 5);
