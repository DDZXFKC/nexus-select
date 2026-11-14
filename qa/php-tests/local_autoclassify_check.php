<?php
/**
 * Integration check on the Local site (NOT production): proves that a product created and updated
 * through WooCommerce's CRUD layer (the same path as the REST API / WP-CLI / a sourcing importer)
 * is classified by nexus-catnav-autoclassify.php.
 *
 * It creates ONE temporary DRAFT product (never public), checks it, and permanently deletes it.
 * Run (MySQL socket required, see qa/README.md):
 *   wp eval-file qa/php-tests/local_autoclassify_check.php --path="<Local site>/app/public"
 */
if (!defined('ABSPATH')) exit(1);
$host = wp_parse_url(home_url(), PHP_URL_HOST);
if (!preg_match('/(\.local|\.localhost|\.test)$|^localhost$/', (string) $host)) {
    WP_CLI::error("Refusing to run on $host: Local environment only.");
}
$term = function ($slug) { $t = get_term_by('slug', $slug, 'product_cat'); return $t ? (int) $t->term_id : 0; };
$slugs = function ($id) { clean_object_term_cache($id, 'product'); $s = wp_get_post_terms($id, 'product_cat', ['fields' => 'slugs']); sort($s); return $s; };
$fail = 0;
$check = function ($name, $ok, $detail) use (&$fail) { if ($ok) WP_CLI::log("PASS  $name"); else { $fail++; WP_CLI::warning("FAIL  $name :: $detail"); } };

if (!$term('mens-sneakers') || !$term('mens-running')) WP_CLI::error('mens-sneakers / mens-running category not found');

$p = new WC_Product_Simple();
$p->set_name('AHC QA TEMP Plain Sneaker');
$p->set_status('draft');
$p->set_regular_price('1');
$p->set_category_ids([$term('mens-sneakers')]);
$id = $p->save();
try {
    $s = $slugs($id);
    $check('new product: root + group completed', in_array('mens', $s, true) && in_array('mens-shoes', $s, true), implode(',', $s));
    $check('new product: no facet for a plain sneaker', !in_array('mens-running', $s, true), implode(',', $s));

    $p = wc_get_product($id);
    $p->set_name('AHC QA TEMP ASICS Novablast 5');
    $p->save();
    $s = $slugs($id);
    $check('update: running facet added', in_array('mens-running', $s, true), implode(',', $s));

    $p = wc_get_product($id);
    $p->set_name('AHC QA TEMP Plain Sneaker');
    $p->save();
    $s = $slugs($id);
    $check('update: auto facet removed when no longer matching', !in_array('mens-running', $s, true) && in_array('mens-sneakers', $s, true), implode(',', $s));
} finally {
    wp_delete_post($id, true);
    WP_CLI::log("Temporary draft product $id deleted.");
}
$fail ? WP_CLI::error("$fail check(s) failed") : WP_CLI::success('autoclassify works for products saved through WooCommerce CRUD / REST');
