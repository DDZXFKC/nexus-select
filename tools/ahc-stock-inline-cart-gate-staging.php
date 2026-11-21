<?php
/**
 * AFTER HOURS CLUB — guarded inline-stock cart admission, staging only.
 *
 * DO NOT LOAD ON XSERVER until Claude compares the live MU plugins and tests
 * both Woo's classic add-to-cart and Store API routes. This is not a full
 * Store API or checkout solution. No credentials, emails or background jobs.
 */
defined('ABSPATH') || exit;

if (!function_exists('ahc_inline_gate_error')) {
function ahc_inline_gate_error($code, $message, $status = 400) {
    wp_send_json_error(['code' => $code, 'message' => $message], $status);
}
}

/**
 * Fail closed: only an existing, session-bound and unexpired token is usable.
 * The token must match a real, unchanged variation and quoted JPY price.
 */
function ahc_inline_gate_permit($permit, $accept_quote) {
    if (!is_string($permit) || !preg_match('/^[a-f0-9]{48}$/D', $permit)) {
        return ['error' => 'permit_invalid'];
    }
    if (!function_exists('WC') || !WC() || !WC()->session) {
        return ['error' => 'permit_invalid'];
    }
    $record = get_transient('ahc_inline_permit_' . $permit);
    if (!is_array($record)) return ['error' => 'permit_expired'];

    $sid = (string) WC()->session->get_customer_id();
    if ($sid === '' || !isset($record['session']) ||
        !is_string($record['session']) ||
        !hash_equals($record['session'], hash('sha256', $sid))) {
        return ['error' => 'permit_invalid'];
    }
    $pid = (int) ($record['product_id'] ?? 0);
    $vid = (int) ($record['variation_id'] ?? 0);
    $price = $record['price'] ?? null;
    if ($pid <= 0 || $vid <= 0 || !is_int($price) || $price <= 0) {
        return ['error' => 'permit_invalid'];
    }
    if (!empty($record['quote']) && $accept_quote !== '1') {
        return ['error' => 'quote_not_accepted'];
    }
    $parent = wc_get_product($pid);
    $variation = wc_get_product($vid);
    if (!$parent || !$parent->is_type('variable') ||
        !$variation || !$variation->is_type('variation') ||
        (int) $variation->get_parent_id() !== $pid ||
        !$variation->is_purchasable()) {
        return ['error' => 'permit_invalid'];
    }
    $attrs = $record['attrs'] ?? null;
    if (!is_array($attrs)) return ['error' => 'permit_invalid'];
    foreach ($variation->get_variation_attributes() as $key => $actual) {
        if (!array_key_exists($key, $attrs)) return ['error' => 'permit_invalid'];
        if ($actual !== '' && $actual !== $attrs[$key]) return ['error' => 'permit_invalid'];
        if (!is_string($attrs[$key]) || $attrs[$key] === '') return ['error' => 'permit_invalid'];
    }
    if ((int) get_post_meta($vid, '_ahc_inline_oos_until', true) > time()) {
        return ['error' => 'permit_invalid'];
    }
    return ['record' => $record, 'product_id' => $pid,
            'variation_id' => $vid, 'attrs' => $attrs, 'price' => $price];
}

/**
 * Atomic admission marker: add_option relies on WP's unique option_name key.
 * Never unlock a token after a transient timeout or ambiguous cart failure.
 * Retention is bounded by a separately scheduled cleanup at deployment time.
 * Do not put secrets in this record.
 */
function ahc_inline_gate_claim($permit) {
    $name = 'ahc_sc_claim_' . hash('sha256', $permit);
    return add_option($name, (string) time(), '', false);
}

function ahc_inline_gate_add_to_cart() {
    if (!check_ajax_referer('ahc_sc_inline', 'nonce', false)) {
        ahc_inline_gate_error('nonce', '画面を再読み込みしてください。', 403);
    }
    $permit = isset($_POST['permit']) && is_scalar($_POST['permit'])
        ? (string) wp_unslash($_POST['permit']) : '';
    $accept = isset($_POST['accept_quote']) && is_scalar($_POST['accept_quote'])
        ? (string) wp_unslash($_POST['accept_quote']) : '0';
    $v = ahc_inline_gate_permit($permit, $accept);
    if (isset($v['error'])) {
        ahc_inline_gate_error($v['error'], 'もう一度在庫を確認してください。', 409);
    }
    // Claim before cart write to prevent replay / double-click duplication.
    if (!ahc_inline_gate_claim($permit)) {
        ahc_inline_gate_error('permit_invalid', 'もう一度在庫を確認してください。', 409);
    }
    if (!WC()->cart) {
        ahc_inline_gate_error('cart_unavailable', 'カートを利用できません。', 503);
    }

    // The cart line carries the verified price; no price is accepted from POST.
    $line = [
        'ahc_inline_checked' => true,
        'ahc_inline_permit_hash' => hash('sha256', $permit),
        'ahc_inline_sale_price' => $v['price'],
        'ahc_inline_checked_at' => time(),
        'ahc_inline_shop' => sanitize_key($v['record']['shop'] ?? ''),
        'ahc_inline_quote_accepted' => !empty($v['record']['quote'])
    ];
    // This endpoint must be paired with Woo classic + Store API validation,
    // cart price persistence, and order/checkout integrity checks before use.
    $key = WC()->cart->add_to_cart($v['product_id'], 1, $v['variation_id'], $v['attrs'], $line);
    if (!$key) {
        ahc_inline_gate_error('cart_unavailable', 'カートに追加できませんでした。', 409);
    }
    delete_transient('ahc_inline_permit_' . $permit);
    wp_send_json_success(['ok' => true, 'cart_url' => wc_get_cart_url()]);
}
add_action('wp_ajax_ahc_sc_add_to_cart', 'ahc_inline_gate_add_to_cart');
add_action('wp_ajax_nopriv_ahc_sc_add_to_cart', 'ahc_inline_gate_add_to_cart');

/**
 * Scope strict gate to products explicitly opted into inline verification.
 * Until both ordinary Woo and Store API admission are implemented and tested,
 * use of this module in production is forbidden. No global allow-cart flag.
 */
