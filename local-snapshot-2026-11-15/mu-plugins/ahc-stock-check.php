<?php
/*
Plugin Name: AHC Stock Check (stage 1)
Description: 「在庫を確認する」受付（購入可能化計画 項目A 段階1）。ADD TO BAG を在庫確認依頼に置き換え、
依頼は非公開の投稿タイプに保存する。カート・注文・決済には進ませない。
設計：docs/stock-check-flow-design-claude-2026-11-20.md（GLM判断 959420a 反映）。
*/
if (!defined('ABSPATH')) exit;

const AHC_SC_PT = 'ahc_stock_request';

/* ---------- parameters (owner-pending values live here) ---------- */
function ahc_sc_param($key) {
    $defaults = [
        'expire_days'         => 14, // 受付 → 受付期限切れ（最後の状態変更から）
        'reply_business_days' => 3,  // 返信目安
        'retention_months'    => 6,  // 完了後の保持期間
        'rate_seconds'        => 60, // 同一IP・同一メールの連投間隔
        'message_max'         => 1000,
    ];
    $opt = get_option('ahc_sc_params', []);
    $val = (is_array($opt) && isset($opt[$key])) ? $opt[$key] : ($defaults[$key] ?? null);
    return apply_filters('ahc_sc_param', $val, $key);
}
function ahc_sc_notify_email() {
    $to = get_option('ahc_sc_notify_email', '');
    return is_email($to) ? $to : get_option('admin_email');
}

/* ---------- states ---------- */
function ahc_sc_statuses() {
    return [
        'received'       => '受付',         // 依頼を保存した直後
        'checking'       => '確認中',       // 運営が海外ショップへ在庫・価格を確認している
        'available'      => '確保可',       // 買付可能と確認。購入案内（段階2）待ち
        'unavailable'    => '確保不可',     // 在庫なし・買付不可と確認した
        'intake_expired' => '受付期限切れ', // 未完了のまま最後の状態変更から expire_days 経過
        'cancelled'      => '取消',         // 依頼者の申し出などで取り消した
        // 段階2で「購入済み」相当の終着状態を追加する。
    ];
}
function ahc_sc_open_statuses() { return ['received', 'checking', 'available']; }

/* ---------- private post type ---------- */
add_action('init', function () {
    $cap = 'manage_woocommerce';
    register_post_type(AHC_SC_PT, [
        'labels' => ['name' => '在庫確認依頼', 'singular_name' => '在庫確認依頼', 'menu_name' => '在庫確認依頼',
                     'edit_item' => '在庫確認依頼', 'search_items' => '依頼を検索', 'not_found' => '依頼はありません'],
        'public' => false, 'publicly_queryable' => false, 'exclude_from_search' => true,
        'show_in_rest' => false, 'show_in_nav_menus' => false, 'show_in_admin_bar' => false,
        'query_var' => false, 'rewrite' => false, 'has_archive' => false,
        'show_ui' => true, 'menu_icon' => 'dashicons-clipboard', 'supports' => false,
        'map_meta_cap' => false,
        'capabilities' => [
            'edit_post' => $cap, 'read_post' => $cap, 'delete_post' => $cap,
            'edit_posts' => $cap, 'edit_others_posts' => $cap, 'delete_posts' => $cap,
            'publish_posts' => $cap, 'read_private_posts' => $cap, 'create_posts' => 'do_not_allow',
            'delete_private_posts' => $cap, 'delete_others_posts' => $cap, 'edit_private_posts' => $cap,
        ],
    ]);
    if (!wp_next_scheduled('ahc_sc_daily')) wp_schedule_event(time() + 300, 'daily', 'ahc_sc_daily');
});

/* ---------- helpers ---------- */
function ahc_sc_norm_email($e) { return strtolower(trim((string) $e)); }
function ahc_sc_key($email, $product_id, $color, $size) {
    return md5(ahc_sc_norm_email($email) . '|' . (int) $product_id . '|' . $color . '|' . $size);
}
function ahc_sc_next_receipt_id() {
    $day = wp_date('Ymd');
    $opt = 'ahc_sc_seq_' . $day;
    $n = (int) get_option($opt, 0) + 1;
    update_option($opt, $n, false);
    return sprintf('SC-%s-%03d', $day, $n);
}
function ahc_sc_client_ip() {
    return isset($_SERVER['REMOTE_ADDR']) ? preg_replace('/[^0-9a-fA-F:.]/', '', (string) $_SERVER['REMOTE_ADDR']) : '';
}
function ahc_sc_find_open($key) {
    $q = get_posts([
        'post_type' => AHC_SC_PT, 'post_status' => 'any', 'numberposts' => 1, 'fields' => 'ids',
        'meta_query' => [
            ['key' => '_ahc_sc_key', 'value' => $key],
            ['key' => '_ahc_sc_status', 'value' => ahc_sc_open_statuses(), 'compare' => 'IN'],
        ],
    ]);
    return $q ? (int) $q[0] : 0;
}

/**
 * Resolve the chosen product / variation to display names, from the server's own data.
 * Returns ['product'=>WC_Product,'variation_id'=>int,'color'=>string,'size'=>string,'other'=>string,'price'=>string] or WP_Error.
 */
function ahc_sc_resolve($product_id, $variation_id, array $posted_attrs) {
    $product = wc_get_product((int) $product_id);
    if (!$product || $product->get_status() !== 'publish' || !$product->is_visible()) {
        return new WP_Error('product', '商品が見つかりません。ページを再読み込みしてください。');
    }
    if (function_exists('ahc_is_fixture_product') && ahc_is_fixture_product($product)) {
        return new WP_Error('product', 'この商品は在庫確認を受け付けていません。');
    }
    $target = $product; $color = ''; $size = ''; $other = [];
    if ($product->is_type('variable')) {
        $variation = wc_get_product((int) $variation_id);
        if (!$variation || !$variation->is_type('variation') || (int) $variation->get_parent_id() !== (int) $product->get_id()) {
            return new WP_Error('variation', 'カラーとサイズを選択してください。');
        }
        $allowed = $product->get_variation_attributes();
        foreach ($variation->get_attributes() as $name => $value) {
            if ($value === '' ) { // "any" attribute: take the posted value, only if it is a real option
                $value = (string) ($posted_attrs['attribute_' . $name] ?? '');
                if ($value === '' || !in_array($value, array_map('strval', (array) ($allowed[$name] ?? [])), true)) {
                    return new WP_Error('variation', 'カラーとサイズを選択してください。');
                }
            }
            $label = $value;
            if (taxonomy_exists($name)) { $t = get_term_by('slug', $value, $name); if ($t) $label = $t->name; }
            if (stripos($name, 'color') !== false || stripos($name, 'colour') !== false) $color = $label;
            elseif (stripos($name, 'size') !== false) $size = $label;
            else $other[] = wc_attribute_label($name) . ':' . $label;
        }
        $target = $variation;
    }
    if (!$target->is_in_stock()) return new WP_Error('soldout', 'このサイズは SOLD OUT です。');
    $price = function_exists('wc_get_price_to_display') ? wc_get_price_to_display($target) : $target->get_price();
    return ['product' => $product, 'variation_id' => $product->is_type('variable') ? (int) $variation_id : 0,
            'color' => $color, 'size' => $size, 'other' => implode(' / ', $other), 'price' => (string) $price];
}

/* ---------- submit (admin-ajax, logged in or not) ---------- */
function ahc_sc_handle_nonce() { wp_send_json_success(['nonce' => wp_create_nonce('ahc_sc_submit')]); }
add_action('wp_ajax_ahc_sc_nonce', 'ahc_sc_handle_nonce');
add_action('wp_ajax_nopriv_ahc_sc_nonce', 'ahc_sc_handle_nonce');

function ahc_sc_handle_submit() {
    $p = wp_unslash($_POST);
    if (!wp_verify_nonce((string) ($p['nonce'] ?? ''), 'ahc_sc_submit')) {
        wp_send_json_error(['message' => '画面の有効期限が切れました。もう一度「送信する」を押してください。', 'code' => 'nonce'], 403);
    }
    if (!empty($p['website'])) { // honeypot: answer like success, save nothing
        wp_send_json_success(['receipt_id' => '', 'message' => '受け付けました。']);
    }
    $name   = trim(sanitize_text_field((string) ($p['name'] ?? '')));
    $email  = ahc_sc_norm_email(sanitize_email((string) ($p['email'] ?? '')));
    $email2 = ahc_sc_norm_email(sanitize_email((string) ($p['email_confirm'] ?? '')));
    $msg    = trim(sanitize_textarea_field((string) ($p['message'] ?? '')));
    if ($name === '' || mb_strlen($name) > 100) wp_send_json_error(['message' => 'お名前を入力してください。', 'code' => 'name'], 400);
    if (!is_email($email)) wp_send_json_error(['message' => 'メールアドレスを正しく入力してください。', 'code' => 'email'], 400);
    if ($email !== $email2) wp_send_json_error(['message' => '確認用のメールアドレスが一致しません。', 'code' => 'email_confirm'], 400);
    if (mb_strlen($msg) > (int) ahc_sc_param('message_max')) {
        wp_send_json_error(['message' => 'メッセージは' . (int) ahc_sc_param('message_max') . '文字以内で入力してください。', 'code' => 'message'], 400);
    }
    $wait = (int) ahc_sc_param('rate_seconds');
    $ipk = 'ahc_sc_ip_' . md5(ahc_sc_client_ip()); $emk = 'ahc_sc_em_' . md5($email);
    if (get_transient($ipk) || get_transient($emk)) {
        wp_send_json_error(['message' => '短時間に続けて送信されました。1分ほど置いてからお試しください。', 'code' => 'rate'], 429);
    }
    $attrs = [];
    foreach ($p as $k => $v) if (strpos((string) $k, 'attribute_') === 0) $attrs[$k] = sanitize_title((string) $v);
    $r = ahc_sc_resolve((int) ($p['product_id'] ?? 0), (int) ($p['variation_id'] ?? 0), $attrs);
    if (is_wp_error($r)) wp_send_json_error(['message' => $r->get_error_message(), 'code' => $r->get_error_code()], 400);

    set_transient($ipk, 1, $wait); set_transient($emk, 1, $wait);
    $key = ahc_sc_key($email, $r['product']->get_id(), $r['color'], $r['size'] . '|' . $r['other']);
    if (ahc_sc_find_open($key)) {
        // Do not echo the existing receipt ID: anyone could type someone else's address.
        wp_send_json_success(['duplicate' => true, 'receipt_id' => '',
            'message' => 'このメールアドレスで、同じ商品・カラー・サイズのご依頼をすでに受け付けています。受付時にお送りしたメールをご確認ください。']);
    }
    $rid = ahc_sc_next_receipt_id();
    $now = time();
    $post_id = wp_insert_post(['post_type' => AHC_SC_PT, 'post_status' => 'private', 'post_title' => $rid], true);
    if (is_wp_error($post_id) || !$post_id) wp_send_json_error(['message' => '受付に失敗しました。時間を置いてお試しください。', 'code' => 'save'], 500);
    $meta = [
        '_ahc_sc_receipt' => $rid, '_ahc_sc_status' => 'received', '_ahc_sc_status_at' => $now, '_ahc_sc_updated_at' => $now,
        '_ahc_sc_received_at' => $now, '_ahc_sc_key' => $key, '_ahc_sc_name' => $name, '_ahc_sc_email' => $email,
        '_ahc_sc_message' => $msg, '_ahc_sc_product_id' => $r['product']->get_id(), '_ahc_sc_variation_id' => $r['variation_id'],
        '_ahc_sc_product_name' => $r['product']->get_name(), '_ahc_sc_color' => $r['color'], '_ahc_sc_size' => $r['size'],
        '_ahc_sc_other' => $r['other'], '_ahc_sc_price' => $r['price'], '_ahc_sc_currency' => get_woocommerce_currency(), '_ahc_sc_memo' => '',
    ];
    foreach ($meta as $k => $v) update_post_meta($post_id, $k, $v);
    $sent = ahc_sc_send_mails($post_id);
    update_post_meta($post_id, '_ahc_sc_mail_log', $sent);
    wp_send_json_success(['duplicate' => false, 'receipt_id' => $rid,
        'message' => '在庫確認のご依頼を受け付けました。受付ID：' . $rid . '（受付メールをお送りしました。届かない場合もこの受付IDでお問い合わせいただけます）']);
}
add_action('wp_ajax_ahc_sc_submit', 'ahc_sc_handle_submit');
add_action('wp_ajax_nopriv_ahc_sc_submit', 'ahc_sc_handle_submit');

function ahc_sc_item_line($id) {
    $parts = [get_post_meta($id, '_ahc_sc_product_name', true)];
    foreach (['_ahc_sc_color' => 'カラー', '_ahc_sc_size' => 'サイズ'] as $k => $l) { $v = get_post_meta($id, $k, true); if ($v !== '') $parts[] = $l . '：' . $v; }
    $o = get_post_meta($id, '_ahc_sc_other', true); if ($o !== '') $parts[] = $o;
    return implode(' / ', $parts);
}
function ahc_sc_send_mails($id) {
    $rid = get_post_meta($id, '_ahc_sc_receipt', true);
    $price = wp_strip_all_tags(wc_price((float) get_post_meta($id, '_ahc_sc_price', true)));
    $site = wp_specialchars_decode(get_bloginfo('name'), ENT_QUOTES);
    $body = get_post_meta($id, '_ahc_sc_name', true) . " 様\n\n"
        . "在庫確認のご依頼を受け付けました。\n\n受付ID：{$rid}\n商品：" . ahc_sc_item_line($id) . "\n表示価格：{$price}\n\n"
        . "在庫確認は無料です。この時点では注文・決済は発生しません。\n"
        . "在庫確認は商品の確保を保証するものではありません。海外ショップの在庫・価格は変動するため、確認の結果ご用意できない場合があります。\n"
        . "通常" . (int) ahc_sc_param('reply_business_days') . "営業日以内に、このメールアドレスへご返信します。\n"
        . "受付から" . (int) ahc_sc_param('expire_days') . "日を過ぎても進展のない依頼は、自動で受付期限切れとなります。\n\n{$site}\n";
    $a = wp_mail(get_post_meta($id, '_ahc_sc_email', true), "【{$site}】在庫確認のご依頼を受け付けました（{$rid}）", $body);
    $admin = "新しい在庫確認依頼\n\n受付ID：{$rid}\n商品：" . ahc_sc_item_line($id) . "\n表示価格：{$price}\n管理画面：" . admin_url('post.php?post=' . (int) $id . '&action=edit') . "\n";
    $b = wp_mail(ahc_sc_notify_email(), "【在庫確認】新着 {$rid}", $admin, ['Reply-To: ' . get_post_meta($id, '_ahc_sc_email', true)]);
    return ['requester' => (bool) $a, 'notify' => (bool) $b, 'at' => time()];
}

/* ---------- daily: auto-expire and retention ---------- */
function ahc_sc_run_daily($now = null) {
    $now = $now ?: time();
    $done = ['expired' => 0, 'deleted' => 0];
    $expire_before = $now - (int) ahc_sc_param('expire_days') * DAY_IN_SECONDS;
    foreach (get_posts(['post_type' => AHC_SC_PT, 'post_status' => 'any', 'numberposts' => -1, 'fields' => 'ids', 'meta_query' => [
        ['key' => '_ahc_sc_status', 'value' => ahc_sc_open_statuses(), 'compare' => 'IN'],
        ['key' => '_ahc_sc_status_at', 'value' => $expire_before, 'compare' => '<', 'type' => 'NUMERIC']]]) as $id) {
        update_post_meta($id, '_ahc_sc_status', 'intake_expired');
        update_post_meta($id, '_ahc_sc_status_at', $now); update_post_meta($id, '_ahc_sc_updated_at', $now);
        $done['expired']++;
    }
    $keep_after = strtotime('-' . (int) ahc_sc_param('retention_months') . ' months', $now);
    foreach (get_posts(['post_type' => AHC_SC_PT, 'post_status' => 'any', 'numberposts' => -1, 'fields' => 'ids', 'meta_query' => [
        ['key' => '_ahc_sc_status', 'value' => ahc_sc_open_statuses(), 'compare' => 'NOT IN'],
        ['key' => '_ahc_sc_status_at', 'value' => $keep_after, 'compare' => '<', 'type' => 'NUMERIC']]]) as $id) {
        wp_delete_post($id, true);
        $done['deleted']++;
    }
    return $done;
}
add_action('ahc_sc_daily', 'ahc_sc_run_daily');

/* ---------- admin: list columns, status/memo box ---------- */
add_filter('manage_' . AHC_SC_PT . '_posts_columns', function () {
    return ['cb' => '<input type="checkbox" />', 'title' => '受付ID', 'ahc_item' => '商品 / カラー / サイズ', 'ahc_email' => 'メール',
            'ahc_status' => '状態', 'ahc_received' => '受付日時', 'ahc_updated' => '更新日時', 'ahc_memo' => '対応メモ'];
});
add_action('manage_' . AHC_SC_PT . '_posts_custom_column', function ($col, $id) {
    $st = ahc_sc_statuses();
    switch ($col) {
        case 'ahc_item': echo esc_html(ahc_sc_item_line($id)); break;
        case 'ahc_email': echo esc_html(get_post_meta($id, '_ahc_sc_email', true)); break;
        case 'ahc_status': echo esc_html($st[get_post_meta($id, '_ahc_sc_status', true)] ?? ''); break;
        case 'ahc_received': echo esc_html(wp_date('Y-m-d H:i', (int) get_post_meta($id, '_ahc_sc_received_at', true))); break;
        case 'ahc_updated': echo esc_html(wp_date('Y-m-d H:i', (int) get_post_meta($id, '_ahc_sc_updated_at', true))); break;
        case 'ahc_memo': echo esc_html(wp_trim_words(get_post_meta($id, '_ahc_sc_memo', true), 20)); break;
    }
}, 10, 2);
add_action('add_meta_boxes_' . AHC_SC_PT, function ($post) {
    add_meta_box('ahc_sc_box', '依頼内容と対応', function ($post) {
        $id = $post->ID; $st = ahc_sc_statuses(); $cur = get_post_meta($id, '_ahc_sc_status', true);
        wp_nonce_field('ahc_sc_admin_save', 'ahc_sc_admin_nonce');
        $rows = ['受付ID' => get_post_meta($id, '_ahc_sc_receipt', true), '商品' => ahc_sc_item_line($id),
                 '表示価格' => wp_strip_all_tags(wc_price((float) get_post_meta($id, '_ahc_sc_price', true))),
                 'お名前' => get_post_meta($id, '_ahc_sc_name', true), 'メール' => get_post_meta($id, '_ahc_sc_email', true),
                 'メッセージ' => get_post_meta($id, '_ahc_sc_message', true),
                 '受付日時' => wp_date('Y-m-d H:i', (int) get_post_meta($id, '_ahc_sc_received_at', true)),
                 '更新日時' => wp_date('Y-m-d H:i', (int) get_post_meta($id, '_ahc_sc_updated_at', true))];
        echo '<table class="form-table">';
        foreach ($rows as $l => $v) echo '<tr><th>' . esc_html($l) . '</th><td>' . nl2br(esc_html($v)) . '</td></tr>';
        echo '<tr><th>状態</th><td><select name="ahc_sc_status">';
        foreach ($st as $k => $l) echo '<option value="' . esc_attr($k) . '"' . selected($cur, $k, false) . '>' . esc_html($l) . '</option>';
        echo '</select><p class="description">受付→確認中→確保可／確保不可。未完了（受付・確認中・確保可）のまま' . (int) ahc_sc_param('expire_days') . '日状態が変わらないと自動で受付期限切れ。確保可でも購入案内（段階2）ができるまでは、確認中のまま手動メールで状況を伝える運用。</p></td></tr>';
        echo '<tr><th>対応メモ</th><td><textarea name="ahc_sc_memo" rows="4" style="width:100%">' . esc_textarea(get_post_meta($id, '_ahc_sc_memo', true)) . '</textarea></td></tr></table>';
    }, AHC_SC_PT, 'normal', 'high');
});
add_action('save_post_' . AHC_SC_PT, function ($post_id) {
    if (!isset($_POST['ahc_sc_admin_nonce']) || !wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['ahc_sc_admin_nonce'])), 'ahc_sc_admin_save')) return;
    if ((defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) || !current_user_can('manage_woocommerce')) return;
    $now = time(); $changed = false;
    $new = sanitize_key(wp_unslash($_POST['ahc_sc_status'] ?? ''));
    if (isset(ahc_sc_statuses()[$new]) && $new !== get_post_meta($post_id, '_ahc_sc_status', true)) {
        update_post_meta($post_id, '_ahc_sc_status', $new); update_post_meta($post_id, '_ahc_sc_status_at', $now); $changed = true;
    }
    $memo = sanitize_textarea_field(wp_unslash($_POST['ahc_sc_memo'] ?? ''));
    if ($memo !== get_post_meta($post_id, '_ahc_sc_memo', true)) { update_post_meta($post_id, '_ahc_sc_memo', $memo); $changed = true; }
    if ($changed) update_post_meta($post_id, '_ahc_sc_updated_at', $now);
});

/* ---------- no cart in stage 1 ---------- */
function ahc_sc_cart_allowed() { return (bool) apply_filters('ahc_stock_check_allow_cart', false); }
add_filter('woocommerce_add_to_cart_validation', function ($ok) {
    if (ahc_sc_cart_allowed()) return $ok;
    wc_add_notice('現在は「在庫を確認する」からのご依頼のみ受け付けています。', 'error');
    return false;
}, 98, 1);
add_action('woocommerce_store_api_validate_add_to_cart', function () {
    if (ahc_sc_cart_allowed()) return;
    $ex = '\\Automattic\\WooCommerce\\StoreApi\\Exceptions\\RouteException';
    if (class_exists($ex)) throw new $ex('ahc_stock_check_only', '現在は「在庫を確認する」からのご依頼のみ受け付けています。', 400);
    throw new Exception('現在は「在庫を確認する」からのご依頼のみ受け付けています。');
}, 98, 0);
add_filter('woocommerce_loop_add_to_cart_link', function ($html, $product) {
    if (ahc_sc_cart_allowed() || !$product) return $html;
    return '<a href="' . esc_url($product->get_permalink()) . '" class="button">在庫を確認する</a>';
}, 20, 2);

/* ---------- product page ---------- */
add_action('wp', function () {
    if (ahc_sc_cart_allowed() || !function_exists('is_product') || !is_product()) return;
    remove_action('woocommerce_single_variation', 'woocommerce_single_variation_add_to_cart_button', 20);
    add_action('woocommerce_single_variation', function () { ahc_sc_render_block(true); }, 20);
    remove_action('woocommerce_simple_add_to_cart', 'woocommerce_simple_add_to_cart', 30);
    add_action('woocommerce_simple_add_to_cart', function () {
        global $product;
        if ($product && $product->is_in_stock()) echo '<div class="cart">', ahc_sc_render_block(false, true), '</div>';
    }, 30);
    add_action('woocommerce_single_product_summary', function () {
        echo '<p class="ahc-sc-origin">海外お取り寄せ / 国内送料無料</p>';
    }, 11);
});

function ahc_sc_render_block($variable, $return = false) {
    global $product;
    if (!$product) return '';
    $icons = [
        'buy'   => '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 7h12l-1 13H7L6 7z M9 7a3 3 0 0 1 6 0" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>',
        'check' => '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12l5 5L20 6" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>',
        'ship'  => '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 7h11v9H3z M14 10h4l3 3v3h-7 M7 19a1.5 1.5 0 1 0 0-.1 M17 19a1.5 1.5 0 1 0 0-.1" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>',
    ];
    $privacy = function_exists('get_privacy_policy_url') ? get_privacy_policy_url() : '';
    ob_start(); ?>
<div class="ahc-sc" data-product-id="<?php echo (int) $product->get_id(); ?>" data-variable="<?php echo $variable ? '1' : '0'; ?>">
  <?php if ($variable) : ?><input type="hidden" name="variation_id" class="variation_id" value="0"><?php endif; ?>
  <button type="button" class="button alt ahc-sc-open"<?php echo $variable ? ' disabled' : ''; ?>>在庫を確認する</button>
  <p class="ahc-sc-reason" aria-live="polite"><?php echo $variable ? 'カラー・サイズを選択してください' : ''; ?></p>
  <p class="ahc-sc-free">在庫確認は無料です。この時点では注文・決済は発生しません。</p>
  <ul class="ahc-sc-guide">
    <li><?php echo $icons['buy']; ?>ご注文後に海外ショップから買い付け</li>
    <li><?php echo $icons['check']; ?>検品後にお届け</li>
    <li><?php echo $icons['ship']; ?>国内送料無料・配送状況の確認が可能</li>
  </ul>
  <div class="ahc-sc-form" hidden>
    <p class="ahc-sc-item"></p>
    <label>お名前<input type="text" class="ahc-sc-name" maxlength="100" autocomplete="name" required></label>
    <label>メールアドレス<input type="email" class="ahc-sc-email" autocomplete="email" required></label>
    <label>メールアドレス（確認）<input type="email" class="ahc-sc-email2" autocomplete="off" required></label>
    <label>メッセージ（任意）<textarea class="ahc-sc-message" rows="3" maxlength="<?php echo (int) ahc_sc_param('message_max'); ?>" placeholder="ほかのサイズもご希望の場合などはこちらへ"></textarea></label>
    <div class="ahc-sc-hp" aria-hidden="true"><label>Website<input type="text" class="ahc-sc-website" tabindex="-1" autocomplete="off"></label></div>
    <p class="ahc-sc-note">通常<?php echo (int) ahc_sc_param('reply_business_days'); ?>営業日以内にメールでご返信します。在庫確認は商品の確保を保証するものではありません。
      <?php if ($privacy) : ?>入力内容は在庫確認のご連絡のために利用します（<a href="<?php echo esc_url($privacy); ?>" target="_blank" rel="noopener">プライバシーポリシー</a>）。<?php endif; ?></p>
    <button type="button" class="button alt ahc-sc-send">送信する</button>
    <p class="ahc-sc-result" role="status" aria-live="polite"></p>
  </div>
</div>
<?php
    $html = ob_get_clean();
    if ($return) return $html;
    echo $html;
    return '';
}

add_action('wp_head', function () {
    if (!function_exists('is_product') || !is_product() || ahc_sc_cart_allowed()) return; ?>
<style>
.ahc-sc-origin{font-size:12px;letter-spacing:.06em;margin:4px 0 14px}
.ahc-sc .ahc-sc-open,.ahc-sc .ahc-sc-send{width:100%;min-height:51px;letter-spacing:.09em}
.ahc-sc .ahc-sc-open:disabled{opacity:.4;cursor:not-allowed}
.ahc-sc-reason{font-size:12px;color:#666;margin:6px 0 0;min-height:1em}
.ahc-sc-free{font-size:12px;margin:8px 0 12px}
.ahc-sc-guide{list-style:none;margin:0 0 16px;padding:0;font-size:12px}
.ahc-sc-guide li{display:flex;align-items:center;gap:8px;padding:4px 0}
.ahc-sc-guide svg{width:18px;height:18px;flex:none}
.ahc-sc-form{border-top:1px solid #ddd;padding-top:14px}
.ahc-sc-form label{display:block;font-size:12px;margin-bottom:10px}
.ahc-sc-form input,.ahc-sc-form textarea{display:block;width:100%;margin-top:4px;padding:10px;border:1px solid #aaa;border-radius:0;font-size:16px}
.ahc-sc-hp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}
.ahc-sc-note{font-size:11px;color:#555}
.ahc-sc-result{font-size:13px;margin-top:10px}
.ahc-sc-result.is-error{color:#b00020}
</style>
<?php });

add_action('wp_footer', function () {
    if (!function_exists('is_product') || !is_product() || ahc_sc_cart_allowed()) return; ?>
<script>
(function () {
  var box = document.querySelector('.ahc-sc');
  if (!box) return;
  var ajax = <?php echo wp_json_encode(admin_url('admin-ajax.php')); ?>;
  var form = box.closest('form') || document;
  var openBtn = box.querySelector('.ahc-sc-open'), reason = box.querySelector('.ahc-sc-reason');
  var panel = box.querySelector('.ahc-sc-form'), result = box.querySelector('.ahc-sc-result');
  var variable = box.dataset.variable === '1', current = null, nonce = '';
  function q(s) { return box.querySelector(s); }
  function selects() { return Array.prototype.slice.call(form.querySelectorAll ? form.querySelectorAll('select[name^="attribute_"]') : []); }
  function itemText() {
    return selects().map(function (s) {
      var o = s.options[s.selectedIndex]; return o && s.value ? o.text.replace(/\s*SOLD OUT\s*$/, '') : '';
    }).filter(Boolean).join(' / ');
  }
  function setState(ok, why) {
    openBtn.disabled = !ok; reason.textContent = ok ? '' : why;
    if (!ok) { panel.hidden = true; }
  }
  if (variable && window.jQuery) {
    var $f = jQuery(box).closest('form.variations_form');
    $f.on('found_variation', function (e, v) {
      current = v;
      if (v && v.is_in_stock && v.is_purchasable !== false) setState(true, '');
      else setState(false, 'このサイズは SOLD OUT です');
    });
    $f.on('reset_data hide_variation', function () { current = null; setState(false, 'カラー・サイズを選択してください'); });
  }
  openBtn.addEventListener('click', function () {
    if (openBtn.disabled) return;
    q('.ahc-sc-item').textContent = itemText();
    panel.hidden = false; result.textContent = ''; result.classList.remove('is-error');
    fetch(ajax + '?action=ahc_sc_nonce', { credentials: 'same-origin' }).then(function (r) { return r.json(); })
      .then(function (j) { if (j && j.success) nonce = j.data.nonce; }).catch(function () {});
    q('.ahc-sc-name').focus();
  });
  q('.ahc-sc-send').addEventListener('click', function () {
    var send = this, fd = new FormData();
    fd.append('action', 'ahc_sc_submit'); fd.append('nonce', nonce);
    fd.append('product_id', box.dataset.productId);
    fd.append('variation_id', current ? current.variation_id : 0);
    selects().forEach(function (s) { fd.append(s.name, s.value); });
    fd.append('name', q('.ahc-sc-name').value); fd.append('email', q('.ahc-sc-email').value);
    fd.append('email_confirm', q('.ahc-sc-email2').value); fd.append('message', q('.ahc-sc-message').value);
    fd.append('website', q('.ahc-sc-website').value);
    send.disabled = true; result.classList.remove('is-error'); result.textContent = '送信しています…';
    fetch(ajax, { method: 'POST', body: fd, credentials: 'same-origin' }).then(function (r) { return r.json(); })
      .then(function (j) {
        var d = (j && j.data) || {};
        result.textContent = d.message || '送信に失敗しました。時間を置いてお試しください。';
        if (!j || !j.success) { result.classList.add('is-error'); send.disabled = false;
          if (d.code === 'nonce') fetch(ajax + '?action=ahc_sc_nonce', { credentials: 'same-origin' }).then(function (r) { return r.json(); }).then(function (k) { if (k && k.success) nonce = k.data.nonce; });
          return; }
        Array.prototype.forEach.call(panel.querySelectorAll('input,textarea'), function (el) { el.disabled = true; });
      })
      .catch(function () { result.classList.add('is-error'); result.textContent = '送信に失敗しました。時間を置いてお試しください。'; send.disabled = false; });
  });
})();
</script>
<?php });
