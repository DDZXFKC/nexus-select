<?php
// Offline test for mu-plugins/ahc-stock-check.php (stage 1). Run: php qa/php-tests/stock_check_stub_test.php
define('ABSPATH', '/'); define('DAY_IN_SECONDS', 86400);
$H = []; $OPT = []; $META = []; $POSTS = []; $TR = []; $MAIL = []; $NEXT = 100; $PT = null; $NOTICES = [];
function add_action($h, $f, $p = 10, $n = 1) { global $H; $H[$h][] = $f; }
function add_filter($h, $f, $p = 10, $n = 1) { global $H; $H[$h][] = $f; }
function apply_filters($h, $v) { return $v; }
function remove_action() {}
function get_option($k, $d = false) { global $OPT; return $OPT[$k] ?? $d; }
function update_option($k, $v) { global $OPT; $OPT[$k] = $v; }
function is_email($e) { return (bool) filter_var($e, FILTER_VALIDATE_EMAIL); }
function register_post_type($n, $a) { global $PT; $PT = $a; }
function wp_next_scheduled() { return true; }
function wp_date($f, $t = null) { return date($f, $t ?? time()); }
function get_transient($k) { global $TR; return $TR[$k] ?? false; }
function set_transient($k, $v) { global $TR; $TR[$k] = $v; }
function wp_unslash($v) { return $v; }
function sanitize_text_field($v) { return trim(strip_tags($v)); }
function sanitize_textarea_field($v) { return trim(strip_tags($v)); }
function sanitize_email($v) { return trim($v); }
function sanitize_title($v) { return strtolower($v); }
function sanitize_key($v) { return strtolower(preg_replace('/[^a-z0-9_\-]/i', '', $v)); }
function wp_verify_nonce($n, $a) { return $n === 'good'; }
function wp_create_nonce() { return 'good'; }
class Done extends Exception { public $ok; public $data; public $code; }
function wp_send_json_success($d) { $e = new Done(); $e->ok = true; $e->data = $d; throw $e; }
function wp_send_json_error($d, $c = 400) { $e = new Done(); $e->ok = false; $e->data = $d; $e->code = $c; throw $e; }
class WP_Error { function __construct($c, $m) { $this->c = $c; $this->m = $m; } function get_error_message() { return $this->m; } function get_error_code() { return $this->c; } }
function is_wp_error($x) { return $x instanceof WP_Error; }
function taxonomy_exists() { return false; }
function wc_attribute_label($n) { return $n; }
function get_woocommerce_currency() { return 'JPY'; }
function wc_price($p) { return '¥' . number_format($p); }
function wp_strip_all_tags($s) { return $s; }
function wp_specialchars_decode($s) { return $s; }
function get_bloginfo() { return 'AFTER HOURS CLUB'; }
function admin_url($p = '') { return '/wp-admin/' . $p; }
function wp_mail($to, $s, $b, $h = []) { global $MAIL; $MAIL[] = compact('to', 's', 'b', 'h'); return true; }
function wc_add_notice($m) { global $NOTICES; $NOTICES[] = $m; }
function wp_insert_post($a) { global $NEXT, $POSTS; $id = $NEXT++; $POSTS[$id] = $a; return $id; }
function update_post_meta($id, $k, $v) { global $META; $META[$id][$k] = $v; }
function get_post_meta($id, $k, $s = true) { global $META; return $META[$id][$k] ?? ''; }
function wp_delete_post($id) { global $POSTS, $META; unset($POSTS[$id], $META[$id]); }
function get_posts($a) {
    global $POSTS, $META; $out = [];
    foreach ($POSTS as $id => $p) {
        $ok = true;
        foreach ($a['meta_query'] as $m) {
            $v = $META[$id][$m['key']] ?? null; $c = $m['compare'] ?? '=';
            if ($c === '=' && $v !== $m['value']) $ok = false;
            if ($c === 'IN' && !in_array($v, $m['value'], true)) $ok = false;
            if ($c === 'NOT IN' && in_array($v, $m['value'], true)) $ok = false;
            if ($c === '<' && !($v < $m['value'])) $ok = false;
        }
        if ($ok) $out[] = $id;
    }
    return $out;
}
class Prod {
    public $id, $type, $stock, $parent, $attrs, $status = 'publish';
    function __construct($id, $type, $stock = true, $parent = 0, $attrs = []) { $this->id = $id; $this->type = $type; $this->stock = $stock; $this->parent = $parent; $this->attrs = $attrs; }
    function get_status() { return $this->status; } function is_visible() { return true; } function get_id() { return $this->id; }
    function is_type($t) { return $this->type === $t; } function get_parent_id() { return $this->parent; }
    function get_attributes() { return $this->attrs; } function is_in_stock() { return $this->stock; }
    function get_variation_attributes() { return ['pa_color' => ['black'], 'pa_size' => ['9', '10']]; }
    function get_price() { return '25000'; } function get_name() { return 'Test Shoe'; }
}
$PRODUCTS = [10 => new Prod(10, 'variable'), 11 => new Prod(11, 'variation', true, 10, ['pa_color' => 'black', 'pa_size' => '9']),
             12 => new Prod(12, 'variation', false, 10, ['pa_color' => 'black', 'pa_size' => '10']),
             13 => new Prod(13, 'variation', true, 99, ['pa_color' => 'black', 'pa_size' => '9'])];
function wc_get_product($id) { global $PRODUCTS; return $PRODUCTS[$id] ?? null; }
include __DIR__ . '/../../local-snapshot-2026-11-15/mu-plugins/ahc-stock-check.php';
foreach ($H['init'] as $f) $f();

$fail = 0; function check($n, $ok) { global $fail; echo ($ok ? 'PASS ' : 'FAIL ') . "$n\n"; if (!$ok) $fail++; }
function submit($over = []) {
    $_POST = array_merge(['nonce' => 'good', 'name' => '山田', 'email' => 'A@Example.com', 'email_confirm' => 'a@example.com',
        'message' => '', 'website' => '', 'product_id' => 10, 'variation_id' => 11, 'attribute_pa_color' => 'black', 'attribute_pa_size' => '9'], $over);
    try { ahc_sc_handle_submit(); } catch (Done $d) { return $d; }
    return null;
}
function clear_rate() { global $TR; $TR = []; }

// 6, 7: private post type
check('post type not public/queryable/REST/search', $PT['public'] === false && $PT['publicly_queryable'] === false && $PT['show_in_rest'] === false && $PT['exclude_from_search'] === true && $PT['query_var'] === false && $PT['rewrite'] === false);
check('all caps are manage_woocommerce, create disabled', $PT['capabilities']['edit_posts'] === 'manage_woocommerce' && $PT['capabilities']['read_post'] === 'manage_woocommerce' && $PT['capabilities']['create_posts'] === 'do_not_allow');
// 5: nonce / honeypot / validation
$r = submit(['nonce' => 'bad']); check('bad nonce refused (403)', !$r->ok && $r->code === 403 && $r->data['code'] === 'nonce');
$r = submit(['website' => 'http://spam']); check('honeypot: success reply, nothing saved', $r->ok && !$POSTS);
$r = submit(['email_confirm' => 'b@example.com']); check('email confirm mismatch refused', !$r->ok && $r->data['code'] === 'email_confirm');
$r = submit(['message' => str_repeat('あ', 1001)]); check('message over 1000 refused', !$r->ok && $r->data['code'] === 'message');
$r = submit(['name' => '']); check('empty name refused', !$r->ok && $r->data['code'] === 'name');
// 2 (server side): sold out / wrong variation
$r = submit(['variation_id' => 12, 'attribute_pa_size' => '10']); check('SOLD OUT size refused', !$r->ok && $r->data['code'] === 'soldout');
$r = submit(['variation_id' => 13]); check('variation of another product refused', !$r->ok && $r->data['code'] === 'variation');
check('nothing saved by refused requests', !$POSTS);
// 1, 8: save + receipt ID + mails
$r = submit(); $id = array_key_last($POSTS);
check('accepted with receipt ID SC-YYYYMMDD-001', $r->ok && preg_match('/^SC-\d{8}-001$/', $r->data['receipt_id']));
check('saved private, status received, email normalised', $POSTS[$id]['post_status'] === 'private' && $META[$id]['_ahc_sc_status'] === 'received' && $META[$id]['_ahc_sc_email'] === 'a@example.com');
check('server-side names and price stored', $META[$id]['_ahc_sc_color'] === 'black' && $META[$id]['_ahc_sc_size'] === '9' && $META[$id]['_ahc_sc_price'] === '25000');
check('requester + notify mails sent', count($MAIL) === 2 && $MAIL[0]['to'] === 'a@example.com' && strpos($MAIL[0]['b'], 'この時点では注文・決済は発生しません') !== false && strpos($MAIL[0]['b'], '確保を保証するものではありません') !== false);
check('notify has Reply-To requester', $MAIL[1]['h'] === ['Reply-To: a@example.com']);
// 5: rate limit
$r = submit(['email' => 'c@example.com', 'email_confirm' => 'c@example.com']); check('second submit within 60s refused (429)', !$r->ok && $r->code === 429);
// 3: duplicate while open, ID not echoed; allowed after completion
clear_rate(); $n = count($POSTS);
$r = submit(['email' => 'a@EXAMPLE.com', 'email_confirm' => 'A@example.com']); check('duplicate (case-insensitive) not created, ID not shown', $r->ok && $r->data['duplicate'] === true && $r->data['receipt_id'] === '' && count($POSTS) === $n);
$META[$id]['_ahc_sc_status'] = 'available'; clear_rate();
$r = submit(); check('available still blocks duplicate', $r->data['duplicate'] === true);
$META[$id]['_ahc_sc_status'] = 'unavailable'; clear_rate();
$r = submit(); check('after completion a new request is allowed (-002)', $r->ok && !$r->data['duplicate'] && substr($r->data['receipt_id'], -3) === '002');
// 4: expiry and retention
$id2 = array_key_last($POSTS); $now = time();
$META[$id2]['_ahc_sc_status_at'] = $now - 15 * 86400;
$d = ahc_sc_run_daily($now); check('open request idle 15 days -> intake_expired', $META[$id2]['_ahc_sc_status'] === 'intake_expired' && $d['expired'] === 1);
$META[$id]['_ahc_sc_status_at'] = $now - 13 * 86400; $META[$id]['_ahc_sc_status'] = 'checking';
ahc_sc_run_daily($now); check('idle 13 days stays open', $META[$id]['_ahc_sc_status'] === 'checking');
$META[$id2]['_ahc_sc_status_at'] = strtotime('-7 months', $now);
$d = ahc_sc_run_daily($now); check('completed > 6 months deleted', !isset($POSTS[$id2]) && $d['deleted'] === 1);
$OPT['ahc_sc_params'] = ['expire_days' => 1]; $META[$id]['_ahc_sc_status_at'] = $now - 2 * 86400;
ahc_sc_run_daily($now); check('expire days is a parameter (1 day for testing)', $META[$id]['_ahc_sc_status'] === 'intake_expired');
// cart blocked in stage 1
$ok = true; foreach ($H['woocommerce_add_to_cart_validation'] as $f) $ok = $f(true);
check('add to cart refused with notice', $ok === false && $NOTICES);
$OPT['ahc_sc_params'] = [];
clear_rate(); $n0 = count($POSTS); $r = submit(['email' => 'noconf@example.com', 'email_confirm' => '']); check('owner 2026-11-21: email confirm field not required', $r->ok && count($POSTS) === $n0 + 1); clear_rate();
exit($fail ? 1 : 0);
