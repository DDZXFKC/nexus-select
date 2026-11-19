<?php
/**
 * READ-ONLY probe (Local): how do color variations map back to supplier products?
 * For every variable product that has a color variation attribute, prints per color value:
 * the variation SKUs and every variation/parent meta key that looks like a source reference.
 * Writes nothing. Output: one JSON line per product.
 * Run: wp eval-file tools/probe_color_variation_sources.php [--limit=20] --path="<Local>/app/public"
 */
if (!defined('ABSPATH')) exit(1);
$host = wp_parse_url(home_url(), PHP_URL_HOST);
if (!preg_match('/(\.local|\.localhost|\.test)$|^localhost$/', (string) $host)) WP_CLI::error("Local only: $host");
$limit = 20;
foreach ((isset($args) ? $args : []) as $a) if (preg_match('/^--limit=(\d+)$/', $a, $m)) $limit = (int) $m[1];
$ids = get_posts(['post_type' => 'product', 'post_status' => ['publish', 'draft'], 'numberposts' => -1, 'fields' => 'ids']);
$n = 0;
$keyre = '/sku|source|supplier|origin|shop|sp_|_sp|product_id|url|handle|color/i';
foreach ($ids as $pid) {
    $p = wc_get_product($pid);
    if (!$p || !$p->is_type('variable')) continue;
    $cattr = null;
    foreach (array_keys($p->get_variation_attributes()) as $ak) if (stripos($ak, 'color') !== false) { $cattr = $ak; break; }
    if (!$cattr) continue;
    $pmeta = [];
    foreach (get_post_meta($pid) as $k => $v) if (preg_match($keyre, $k)) $pmeta[$k] = mb_substr((string) $v[0], 0, 120);
    $colors = [];
    foreach ($p->get_children() as $vid) {
        $v = wc_get_product($vid);
        if (!$v) continue;
        $val = (string) $v->get_attribute($cattr);
        $vm = [];
        foreach (get_post_meta($vid) as $k => $vv) if (preg_match($keyre, $k) && $k !== '_sku') $vm[$k] = mb_substr((string) $vv[0], 0, 120);
        $colors[$val][] = ['sku' => $v->get_sku(), 'meta' => $vm];
    }
    foreach ($colors as $val => $list) $colors[$val] = array_slice($list, 0, 2) + ['__variations' => count($list)];
    WP_CLI::log(wp_json_encode(['id' => $pid, 'sku' => $p->get_sku(), 'title' => $p->get_name(), 'attr' => $cattr,
        'parent_meta' => $pmeta, 'colors' => $colors], JSON_UNESCAPED_UNICODE));
    if (++$n >= $limit) break;
}
WP_CLI::log("products_with_color_attr_printed=$n");
