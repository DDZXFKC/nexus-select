<?php
/**
 * AFTER HOURS CLUB inline stock-check server endpoints (staging implementation).
 *
 * This module must be loaded by the XServer WordPress MU-plugin bootstrap only
 * after comparing the production files. Fail closed until validated offer data,
 * merchant check and pricing callbacks are wired. No email or personal details.
 */
defined('ABSPATH') || exit;

if (!function_exists('ahc_inline_error')) {
function ahc_inline_error($code, $message, $status = 400) {
    wp_send_json_error(['code' => $code, 'message' => $message], $status);
}
}
function ahc_inline_session_id() {
    if (!function_exists('WC') || !WC() || !WC()->session) return '';
    return (string) WC()->session->get_customer_id();
}
function ahc_inline_nonce() {
    if (!check_ajax_referer('ahc_sc_inline', 'nonce', false)) {
        ahc_inline_error('nonce', '画面を再読み込みしてください。', 403);
    }
}
function ahc_inline_request($key) {
    return isset($_POST[$key]) && is_scalar($_POST[$key])
        ? sanitize_text_field(wp_unslash($_POST[$key])) : '';
}
function ahc_inline_selected_variant() {
    if (!function_exists('wc_get_product')) {
        ahc_inline_error('woocommerce', '現在確認できません。', 503);
    }
    $pid = absint(ahc_inline_request('product_id'));
    $vid = absint(ahc_inline_request('variation_id'));
    if (!$pid) ahc_inline_error('invalid_selection', '商品を選択してください。');
    $parent = wc_get_product($pid);
    if (!$parent || !$parent->is_visible() || $parent->get_status() !== 'publish') {
        ahc_inline_error('invalid_selection', '選択された商品を確認できません。');
    }
    // Simple products have no variation ID; stock-check the product itself.
    if ($parent->is_type('simple') && $vid === 0) {
        return [$parent, $parent, []];
    }
    if (!$parent->is_type('variable') || !$vid) {
        ahc_inline_error('invalid_selection', 'サイズを選択してください。');
    }
    $variation = wc_get_product($vid);
    if (!$variation || !$variation->is_type('variation')
        || (int) $variation->get_parent_id() !== $pid) {
        ahc_inline_error('invalid_selection', '選択された商品を確認できません。');
    }
    $actual = $variation->get_variation_attributes();
    foreach ($actual as $name => $value) {
        $posted = ahc_inline_request($name);
        if ($value !== '' && $posted !== $value) {
            ahc_inline_error('invalid_selection', '選択されたサイズ・カラーが一致しません。');
        }
        if ($value === '' && !$posted) {
            ahc_inline_error('invalid_selection', 'サイズまたはカラーを選択してください。');
        }
    }
    return [$parent, $variation, $actual];
}
function ahc_inline_session_check($record) {
    $id = ahc_inline_session_id();
    return $id !== '' && isset($record['session']) &&
           hash_equals($record['session'], hash('sha256', $id));
}
function ahc_inline_start() {
    ahc_inline_nonce();
    // Force persistence for first-time anonymous visitors with an empty cart.
    if (function_exists('WC') && WC() && WC()->session
        && method_exists(WC()->session, 'set_customer_session_cookie')) {
        WC()->session->set_customer_session_cookie(true);
    }
    $session = ahc_inline_session_id();
    if ($session === '') ahc_inline_error('session', 'カートを利用できません。', 503);
    [$parent, $variation, $attrs] = ahc_inline_selected_variant();
    $mark = (int) get_post_meta($variation->get_id(), '_ahc_inline_oos_until', true);
    if ($mark > time()) ahc_inline_error('marked_oos', 'このサイズは現在在庫がありません。', 409);
    $key = 'ahc_inline_rate_' . hash('sha256', $session);
    if (get_transient($key)) ahc_inline_error('rate_limited', '少し時間をおいて再度お試しください。', 429);
    set_transient($key, 1, 20);

    // Only owner-approved matched offers may be returned. Missing data => no candidate.
    $offers = apply_filters('ahc_inline_verified_offers', [], $parent->get_id(),
                           $variation->get_id(), $attrs);
    if (!is_array($offers)) $offers = [];
    $offers = array_values(array_filter($offers, function($offer) {
        return is_array($offer)
            && !empty($offer['shop']) && is_string($offer['shop'])
            && !empty($offer['url']) && is_string($offer['url'])
            && str_starts_with($offer['url'], 'https://')
            && isset($offer['estimated_total_jpy'])
            && is_numeric($offer['estimated_total_jpy'])
            && (float)$offer['estimated_total_jpy'] > 0;
    }));
    usort($offers, function ($a, $b) {
        return (float)$a['estimated_total_jpy'] <=> (float)$b['estimated_total_jpy'];
    });
    $check = bin2hex(random_bytes(20));
    $record = [
        'session' => hash('sha256', $session),
        'product_id' => $parent->get_id(),
        'variation_id' => $parent->is_type('simple') ? 0 : $variation->get_id(),
        'attrs' => $attrs,
        'started' => time(),
        'offers' => $offers,
        'cursor' => 0,
        'checks' => [],
        'best' => null,
        'listed' => (int) round((float)$variation->get_price()),
        'state' => 'running'
    ];
    set_transient('ahc_inline_check_' . $check, $record, 120);
    wp_send_json_success(['ok'=>true, 'state'=>'running', 'check_id'=>$check]);
}
add_action('wp_ajax_ahc_sc_start', 'ahc_inline_start');
add_action('wp_ajax_nopriv_ahc_sc_start', 'ahc_inline_start');

function ahc_inline_step() {
    ahc_inline_nonce();
    $id = ahc_inline_request('check_id');
    if (!preg_match('/^[a-f0-9]{40}$/', $id)) {
        ahc_inline_error('check_invalid', '確認を最初からやり直してください。', 404);
    }
    $k = 'ahc_inline_check_' . $id;
    $r = get_transient($k);
    if (!is_array($r) || !ahc_inline_session_check($r)) {
        ahc_inline_error('check_invalid', '確認を最初からやり直してください。', 404);
    }
    if ($r['state'] === 'done') {
        wp_send_json_success($r['public_result']);
    }
    if (time() - $r['started'] >= 45 || !$r['offers']) {
        $why = !$r['offers'] ? 'no_candidate' : 'timeout';
        $r['state'] = 'done';
        $r['public_result'] = ['ok'=>true, 'state'=>'done',
            'result'=>'unconfirmed', 'reason'=>$why];
        set_transient($k,$r,120);
        wp_send_json_success($r['public_result']);
    }
    if ($r['cursor'] < count($r['offers'])) {
        $offer = $r['offers'][$r['cursor']++];
        // No placeholder success: callback must confirm variant, price and evidence.
        $checked = apply_filters('ahc_inline_check_one_offer', null, $offer,
                $r['product_id'], $r['variation_id'], $r['attrs']);
        if (!is_array($checked) ||
            !in_array($checked['stock'] ?? '', ['IN_STOCK','OUT_OF_STOCK','UNCONFIRMED'], true)) {
            $checked = ['stock'=>'UNCONFIRMED','reason'=>'unreadable'];
        }
        $r['checks'][] = ['shop'=>$offer['shop'],'stock'=>$checked['stock'],
                          'reason'=>sanitize_key($checked['reason'] ?? 'unknown')];
        if ($checked['stock'] === 'IN_STOCK' && isset($checked['current_price'])) {
            // This callback MUST calculate complete landed cost with every fee.
            $new = apply_filters('ahc_inline_recomputed_sale_price', null,
                 $checked['current_price'], $offer, $r['product_id'], $r['variation_id']);
            if (is_int($new) && $new > 0) {
                if ($r['best'] === null || $new < $r['best']['price']) {
                    $r['best'] = ['shop'=>$offer['shop'],'price'=>$new];
                }
            } else {
                $r['checks'][count($r['checks'])-1]['stock'] = 'UNCONFIRMED';
                $r['checks'][count($r['checks'])-1]['reason'] = 'price_unknown';
            }
        }
    }
    if ($r['cursor'] < count($r['offers']) && time() - $r['started'] < 45
        && ($r['best'] === null || $r['best']['price'] > $r['listed'])) {
        set_transient($k,$r,120);
        wp_send_json_success(['ok'=>true,'state'=>'running']);
    }
    if ($r['best'] !== null && $r['listed'] > 0) {
        $quoted = $r['best']['price'] - $r['listed'] >= 400;
        $permit = bin2hex(random_bytes(24));
        set_transient('ahc_inline_permit_' . $permit, [
            'session'=>$r['session'], 'product_id'=>$r['product_id'],
            'variation_id'=>$r['variation_id'], 'attrs'=>$r['attrs'],
            'price'=>$quoted ? $r['best']['price'] : $r['listed'],
            'shop'=>$r['best']['shop'], 'quote'=>$quoted
        ], 300);
        $result = ['ok'=>true,'state'=>'done','result'=>'in_stock',
                   'price_case'=>$quoted?'quote':'listed',
                   'permit'=>$permit,
                   'listed_price_text'=>'¥' . number_format($r['listed']),
                   'quote_price_text'=>$quoted?'¥' . number_format($r['best']['price']):null];
    } elseif ($r['cursor'] >= count($r['offers']) && $r['checks']
              && count(array_filter($r['checks'], function($x){
                   return $x['stock']==='OUT_OF_STOCK';
              })) === count($r['offers'])) {
        $result = ['ok'=>true,'state'=>'done','result'=>'out_of_stock'];
        update_post_meta($r['variation_id'] ?: $r['product_id'],'_ahc_inline_oos_until',time()+24*3600);
    } else {
        $result = ['ok'=>true,'state'=>'done','result'=>'unconfirmed','reason'=>'unreadable'];
    }
    $r['public_result'] = $result;
    $r['state'] = 'done';
    set_transient($k,$r,120);
    wp_send_json_success($result);
}
add_action('wp_ajax_ahc_sc_step', 'ahc_inline_step');
add_action('wp_ajax_nopriv_ahc_sc_step', 'ahc_inline_step');

/**
 * A narrow gate: stage-1 plugin denies ordinary Woo and Store API cart adds.
 * Only our verified short-lived permit can open the gate INSIDE this request.
 */
function ahc_inline_allow_internal_cart($allowed) {
    return !empty($GLOBALS['ahc_inline_authorized_cart_add']);
}
add_filter('ahc_stock_check_allow_cart', 'ahc_inline_allow_internal_cart', 99, 1);

// The gate is also enforced if the legacy stage-1 blocker is deactivated.
// Never permit generic add-to-cart URLs or Store API calls without a checked permit.
function ahc_inline_only_authorized_add($valid) {
    if (!empty($GLOBALS['ahc_inline_authorized_cart_add'])) return $valid;
    if (function_exists('wc_add_notice')) {
        wc_add_notice('購入前に商品の在庫を確認してください。', 'error');
    }
    return false;
}
add_filter('woocommerce_add_to_cart_validation', 'ahc_inline_only_authorized_add', 999, 1);

function ahc_inline_only_authorized_store_api() {
    if (!empty($GLOBALS['ahc_inline_authorized_cart_add'])) return;
    $ex = '\\Automattic\\WooCommerce\\StoreApi\\Exceptions\\RouteException';
    if (class_exists($ex)) {
        throw new $ex('ahc_stock_check_only', '購入前に商品の在庫を確認してください。', 400);
    }
    throw new Exception('購入前に商品の在庫を確認してください。');
}
add_action('woocommerce_store_api_validate_add_to_cart', 'ahc_inline_only_authorized_store_api', 999, 0);

/**
 * A server-side one-use claim protects permits from concurrent replay.
 * Claim is recorded via unique option key and reclaimed after one day.
 */
function ahc_inline_claim_permit($token) {
    return add_option('ahc_inline_claim_' . hash('sha256', $token), time(), '', false);
}
function ahc_inline_gc_claims() {
    global $wpdb;
    $prefix = $wpdb->esc_like('ahc_inline_claim_') . '%';
    $before = time() - DAY_IN_SECONDS;
    $rows = $wpdb->get_results($wpdb->prepare(
        "SELECT option_name, option_value FROM {$wpdb->options} WHERE option_name LIKE %s", $prefix
    ));
    foreach ((array) $rows as $row) {
        if (ctype_digit((string) $row->option_value) && (int) $row->option_value < $before) {
            delete_option($row->option_name);
        }
    }
}
add_action('ahc_inline_gc_claims', 'ahc_inline_gc_claims');
add_action('init', function () {
    if (!wp_next_scheduled('ahc_inline_gc_claims')) {
        wp_schedule_event(time() + HOUR_IN_SECONDS, 'daily', 'ahc_inline_gc_claims');
    }
});

/** Attach a server-only signed quote to this exact cart line. */
function ahc_inline_cart_item_data($data, $product_id, $variation_id) {
    $ctx = $GLOBALS['ahc_inline_authorized_cart_add'] ?? null;
    if (!is_array($ctx)) return $data;
    if ((int) $ctx['product_id'] !== (int) $product_id
        || (int) $ctx['variation_id'] !== (int) $variation_id) return $data;
    $data['ahc_inline_price'] = (int) $ctx['price'];
    $data['ahc_inline_time'] = time();
    $data['ahc_inline_shop'] = (string) $ctx['shop'];
    $data['ahc_inline_unique'] = bin2hex(random_bytes(16));
    $data['ahc_inline_sig'] = hash_hmac('sha256',
        implode('|', [$data['ahc_inline_price'], $data['ahc_inline_time'],
                       $product_id, $variation_id, $data['ahc_inline_unique']]), wp_salt('auth'));
    return $data;
}
add_filter('woocommerce_add_cart_item_data', 'ahc_inline_cart_item_data', 50, 3);

function ahc_inline_cart_line_valid($line) {
    foreach (['product_id','variation_id','ahc_inline_price','ahc_inline_time',
              'ahc_inline_unique','ahc_inline_sig'] as $key) {
        if (!isset($line[$key])) return false;
    }
    if (!is_numeric($line['ahc_inline_price']) || (int)$line['ahc_inline_price'] <= 0) return false;
    if (!is_numeric($line['ahc_inline_time'])) return false;
    if (time() - (int)$line['ahc_inline_time'] > 60 * MINUTE_IN_SECONDS
        || (int)$line['ahc_inline_time'] > time() + 30) return false;
    $expected = hash_hmac('sha256', implode('|', [
        (int)$line['ahc_inline_price'], (int)$line['ahc_inline_time'],
        (int)$line['product_id'], (int)$line['variation_id'], (string)$line['ahc_inline_unique']
    ]), wp_salt('auth'));
    return hash_equals($expected, (string)$line['ahc_inline_sig']);
}
add_action('woocommerce_before_calculate_totals', function ($cart) {
    if (!$cart || !is_object($cart)) return;
    foreach ($cart->get_cart() as $line) {
        if (!ahc_inline_cart_line_valid($line)) continue;
        if (isset($line['data']) && is_object($line['data'])) {
            $line['data']->set_price((int)$line['ahc_inline_price']);
        }
    }
}, 999);
add_action('woocommerce_check_cart_items', function () {
    if (!function_exists('WC') || !WC() || !WC()->cart) return;
    foreach (WC()->cart->get_cart() as $line) {
        if (!ahc_inline_cart_line_valid($line)) {
            wc_add_notice('カート内の商品は在庫確認の期限が切れました。商品ページから再確認してください。', 'error');
            break;
        }
    }
});

/** Same API response wrapper the Claude JS accepts. */
function ahc_inline_add_to_cart() {
    ahc_inline_nonce();
    $token = ahc_inline_request('permit');
    if (!preg_match('/^[a-f0-9]{48}$/', $token)) {
        ahc_inline_error('permit_invalid', '再度在庫を確認してください。', 403);
    }
    $key = 'ahc_inline_permit_' . $token;
    $ctx = get_transient($key);
    if (!is_array($ctx) || !ahc_inline_session_check($ctx)) {
        ahc_inline_error('permit_expired', '在庫確認の期限が切れました。', 403);
    }
    if (!empty($ctx['quote']) && ahc_inline_request('accept_quote') !== '1') {
        ahc_inline_error('quote_not_accepted', '新しい価格への同意が必要です。', 400);
    }
    if (!function_exists('WC') || !WC() || !WC()->cart) {
        ahc_inline_error('permit_invalid', 'カートを利用できません。', 503);
    }
    $product_id = (int) $ctx['product_id'];
    $variation_id = (int) $ctx['variation_id'];
    $product = wc_get_product($variation_id ?: $product_id);
    if (!$product || !$product->is_purchasable() || !$product->is_in_stock()
        || (int)get_post_meta($variation_id ?: $product_id, '_ahc_inline_oos_until', true) > time()) {
        ahc_inline_error('permit_invalid', '選択商品の在庫を確認できません。', 409);
    }
    if (!ahc_inline_claim_permit($token)) {
        ahc_inline_error('permit_invalid', 'この在庫確認は既に使用されています。', 409);
    }
    $GLOBALS['ahc_inline_authorized_cart_add'] = $ctx;
    try {
        $added = WC()->cart->add_to_cart($product_id, 1, $variation_id,
                                        (array)($ctx['attrs'] ?? []));
    } finally {
        unset($GLOBALS['ahc_inline_authorized_cart_add']);
    }
    if (!$added) {
        // Cart can fail validation for reasons unrelated to the permit.
        delete_option('ahc_inline_claim_' . hash('sha256', $token));
        ahc_inline_error('permit_invalid', 'カートへの追加に失敗しました。', 409);
    }
    delete_transient($key);
    wp_send_json_success(['ok'=>true, 'cart_url'=>wc_get_cart_url()]);
}
add_action('wp_ajax_ahc_sc_add_to_cart', 'ahc_inline_add_to_cart');
add_action('wp_ajax_nopriv_ahc_sc_add_to_cart', 'ahc_inline_add_to_cart');
