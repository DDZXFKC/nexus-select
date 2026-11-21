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
    if (!$pid || !$vid) ahc_inline_error('invalid_selection', 'サイズを選択してください。');
    $parent = wc_get_product($pid);
    $variation = wc_get_product($vid);
    if (!$parent || !$parent->is_visible() || !$parent->is_type('variable')
        || !$variation || !$variation->is_type('variation')
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
        'variation_id' => $variation->get_id(),
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
                   'listed_price_text'=>wc_price($r['listed']),
                   'quote_price_text'=>$quoted?wc_price($r['best']['price']):null];
    } elseif ($r['cursor'] >= count($r['offers']) && $r['checks']
              && count(array_filter($r['checks'], function($x){
                   return $x['stock']==='OUT_OF_STOCK';
              })) === count($r['offers'])) {
        $result = ['ok'=>true,'state'=>'done','result'=>'out_of_stock'];
        update_post_meta($r['variation_id'],'_ahc_inline_oos_until',time()+24*3600);
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

/*
 * ahc_sc_add_to_cart is intentionally NOT exposed until the Woo standard and
 * Store API cart gates, session-bound single-use permits, quoted price
 * persistence, and checkout validation have been tested together. Installing
 * this file alone does NOT unlock purchasing.
 */
