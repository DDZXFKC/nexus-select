<?php
/**
 * Sheet -> Woo link for the data-driven color swatch (GPT design 70ee059).
 *
 * Reads one CSV (a non-secret export of the 2 tables, one row per color
 * component) and stores, per Woo product, the post meta _ahc_color_components
 * that the theme renders as 1-3 vertical stripes:
 *   { "<pa_color value of that product>": [ {"name": "...", "hex": "#RRGGBB" | null}, ... ] }
 *
 * Rules
 * - Local sites only (.local/.localhost/.test/localhost). Shoe Palace only (shop_code SP as in the sheet; legacy shoe-palace also accepted).
 * - Dry run by default. Writes only with --apply.
 * - Woo product is found by its parent SKU "SP-<supplier_product_id>" (existing Shoe Palace prep format).
 *   Products not found, or with no / several color values, are skipped and reported (never guessed).
 * - Component order = position. All components are stored; the theme shows the first 3.
 * - hex is written only when hex_status is APPROVED_APPROX and the value is #RRGGBB; otherwise null
 *   (the theme then shows the neutral "unconfirmed" circle). DRAFT colors never reach the storefront.
 * - Only the meta key _ahc_color_components is touched. Price, stock, SKU, images, terms: unchanged.
 *
 * CSV columns (header required):
 *   shop_code,supplier_product_id,supplier_color_key,position,token_original,display_hex,hex_status
 * Make this CSV from the sheet with collector/color_woo_export.py (it blanks hex for HOLD/UNKNOWN
 * products and stops if the sheet's swatch_status differs from the recompute).
 *
 * Run:
 *   wp eval-file tools/ahc_color_components_to_woo.php <csv> [--apply] [--only-confirmed] --path="<Local site>/app/public"
 *   --only-confirmed: skip products whose first 3 colors are not all approved (they keep the current swatch).
 */
if (!defined('ABSPATH')) exit(1);
$host = wp_parse_url(home_url(), PHP_URL_HOST);
if (!preg_match('/(\.local|\.localhost|\.test)$|^localhost$/', (string) $host)) {
    WP_CLI::error("Refusing to run on $host: Local environment only.");
}
$args = isset($args) && is_array($args) ? $args : [];
$csv = null; $apply = false;
foreach ($args as $a) {
    if ($a === '--apply') $apply = true; elseif ($a === '--only-confirmed') continue; elseif ($csv === null) $csv = $a;
}
if (!$csv || !is_readable($csv)) WP_CLI::error('CSV path required and must be readable.');

$fh = fopen($csv, 'r');
$header = fgetcsv($fh);
$need = ['shop_code', 'supplier_product_id', 'supplier_color_key', 'position', 'token_original', 'display_hex', 'hex_status'];
if (!$header || array_diff($need, $header)) WP_CLI::error('CSV header must contain: ' . implode(',', $need));
$idx = array_flip($header);

$groups = [];   // supplier_product_id => position => component
$errors = 0;
while (($row = fgetcsv($fh)) !== false) {
    if (count($row) === 1 && trim((string) $row[0]) === '') continue;
    $shop = trim($row[$idx['shop_code']]);
    if ($shop !== 'SP' && $shop !== 'shoe-palace') { $errors++; WP_CLI::warning("skip non-Shoe Palace row: $shop"); continue; }
    $pid = trim($row[$idx['supplier_product_id']]);
    $key = trim($row[$idx['supplier_color_key']]);
    $pos = (int) $row[$idx['position']];
    if ($pid === '' || $pos < 1) { $errors++; WP_CLI::warning('skip row without product id / position'); continue; }
    if ($key !== 'single') { $errors++; WP_CLI::warning("skip $pid: supplier_color_key '$key' (multi-color products are not in scope yet)"); continue; }
    if (isset($groups[$pid][$pos])) { $errors++; WP_CLI::warning("duplicate position $pos for $pid"); $groups[$pid]['__bad'] = true; continue; }
    $hex = trim($row[$idx['display_hex']]);
    $ok = trim($row[$idx['hex_status']]) === 'APPROVED_APPROX' && preg_match('/^#[0-9A-Fa-f]{6}$/', $hex);
    $groups[$pid][$pos] = ['name' => trim($row[$idx['token_original']]), 'hex' => $ok ? strtoupper($hex) : null];
}
fclose($fh);

$stats = ['written' => 0, 'unchanged' => 0, 'would_write' => 0, 'not_found' => 0, 'color_value_unclear' => 0, 'bad_group' => 0, 'shown_fully_colored' => 0, 'shown_unconfirmed' => 0];
$only_confirmed = in_array('--only-confirmed', $args, true);
foreach ($groups as $pid => $comps) {
    if (!empty($comps['__bad'])) { $stats['bad_group']++; continue; }
    ksort($comps);
    if (array_keys($comps) !== range(1, count($comps))) { $stats['bad_group']++; WP_CLI::warning("$pid: positions are not 1..n"); continue; }
    $post_id = wc_get_product_id_by_sku('SP-' . $pid);
    $product = $post_id ? wc_get_product($post_id) : null;
    if (!$product || !$product->is_type('variable')) { $stats['not_found']++; WP_CLI::log("NOT FOUND  SP-$pid"); continue; }
    $attr = null;
    foreach ($product->get_variation_attributes() as $ak => $values) {
        if (stripos($ak, 'color') !== false) { $attr = $values; break; }
    }
    $values = $attr ? array_values(array_unique(array_map('strval', (array) $attr))) : [];
    if (count($values) !== 1) { $stats['color_value_unclear']++; WP_CLI::log("COLOR VALUE UNCLEAR  SP-$pid (" . count($values) . ' values)'); continue; }
    $value = $values[0];
    // pa_ attributes: the variation form uses the term slug.
    if (taxonomy_exists('pa_color') && ($t = get_term_by('name', $value, 'pa_color'))) $value = $t->slug;
    $first = array_slice(array_values($comps), 0, 3);
    $full = $first && !in_array(null, array_column($first, 'hex'), true);
    $stats[$full ? 'shown_fully_colored' : 'shown_unconfirmed']++;
    // --only-confirmed: write only products whose first min(3, n) colors are all approved,
    // so no storefront swatch falls back to the "unconfirmed" circle.
    if ($only_confirmed && !$full) continue;
    $json = wp_json_encode([$value => array_values($comps)]);
    $old = (string) get_post_meta($post_id, '_ahc_color_components', true);
    if ($old === $json) { $stats['unchanged']++; continue; }
    if ($apply) { update_post_meta($post_id, '_ahc_color_components', wp_slash($json)); $stats['written']++; }
    else { $stats['would_write']++; WP_CLI::log("WOULD WRITE  SP-$pid  $json"); }
}
WP_CLI::log(($apply ? 'APPLIED' : 'DRY RUN') . ' ' . wp_json_encode($stats) . " row_errors=$errors");
