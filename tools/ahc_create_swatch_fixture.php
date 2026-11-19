<?php
/**
 * Create isolated DRAFT fixtures for the swatch check (GPT 84e54b3 §4, review 5dc4c1b). Local only.
 *
 * For each line "supplier_product_id,colorway_original" in fixtures=<csv> (header required), creates a
 * draft variable product cloned from template=<existing SP parent SKU> (its size variations, prices, stock
 * and image are copied as values; the template is not changed):
 *   parent SKU  FX-SP-<supplier_product_id>     (never a real SKU; refused if any post already uses it)
 *   variations  FX-SP-<supplier_product_id>-<n>
 *   title       "[FIXTURE] <template title without its last (...)> (<colorway_original>)"
 *   status draft, catalog visibility hidden, meta _ahc_fixture=1 -> not visible or purchasable.
 * Dry run by default; "apply" creates. "remove" deletes only posts that carry _ahc_fixture=1 and an FX-SP- SKU.
 * Run: wp eval-file tools/ahc_create_swatch_fixture.php fixtures=<csv> template=SP-<id> site=<host> [apply|remove] --path=...
 */
if (!defined('ABSPATH')) exit(1);
$host = (string) wp_parse_url(home_url(), PHP_URL_HOST);
if (!preg_match('/(\.local|\.localhost|\.test)$|^localhost$/', $host)) WP_CLI::error("Local only: $host");
$o = ['fixtures' => null, 'template' => null, 'site' => null, 'mode' => 'dry'];
foreach ((isset($args) ? $args : []) as $a) {
    $a = preg_replace('/^--/', '', (string) $a);
    if ($a === 'apply' || $a === 'remove') $o['mode'] = $a;
    elseif (preg_match('/^(fixtures|template|site)=(.+)$/', $a, $m)) $o[$m[1]] = $m[2];
    else WP_CLI::error("Unknown argument: $a");
}
if ($o['site'] !== $host) WP_CLI::error("site=<host> must equal $host");

if ($o['mode'] === 'remove') {
    $ids = get_posts(['post_type' => 'product', 'post_status' => 'any', 'numberposts' => -1, 'fields' => 'ids',
        'meta_query' => [['key' => '_ahc_fixture', 'value' => '1']]]);
    $n = 0;
    foreach ($ids as $id) {
        $p = wc_get_product($id);
        if (!$p || strpos($p->get_sku(), 'FX-SP-') !== 0 || $p->get_status() !== 'draft') { WP_CLI::warning("skip $id (not an FX draft)"); continue; }
        foreach ($p->get_children() as $vid) wp_delete_post($vid, true);
        wp_delete_post($id, true);
        $n++;
    }
    WP_CLI::log("REMOVED fixtures=$n");
    return;
}

if (!$o['fixtures'] || !is_readable($o['fixtures']) || !$o['template']) WP_CLI::error('fixtures=<csv> and template=<SP-sku> are required');
$tid = wc_get_product_id_by_sku($o['template']);
$tpl = $tid ? wc_get_product($tid) : null;
if (!$tpl || !$tpl->is_type('variable') || strpos($tpl->get_sku(), 'SP-') !== 0) WP_CLI::error('template must be an existing SP- variable product');
foreach (array_keys($tpl->get_variation_attributes()) as $ak) if (stripos($ak, 'color') !== false) WP_CLI::error('template must not have a color variation');

$fh = fopen($o['fixtures'], 'r');
if (fgetcsv($fh) !== ['supplier_product_id', 'colorway_original']) WP_CLI::error('fixtures header must be: supplier_product_id,colorway_original');
$rows = [];
while (($r = fgetcsv($fh)) !== false) {
    if (count($r) === 1 && trim((string) $r[0]) === '') continue;
    if (count($r) !== 2 || !preg_match('/^\d+$/', $r[0])) WP_CLI::error('bad fixtures row: ' . implode(',', $r));
    $sku = 'FX-SP-' . $r[0];
    if (wc_get_product_id_by_sku($sku) || wc_get_product_id_by_sku('SP-' . $r[0])) WP_CLI::error("$sku or SP-{$r[0]} already exists; not creating");
    $rows[] = [$r[0], $r[1], $sku];
}
fclose($fh);
$base = trim(preg_replace('/\s*\([^()]*\)\s*$/u', '', $tpl->get_name()));
foreach ($rows as [$pid, $colorway, $sku]) {
    $title = "[FIXTURE] $base ($colorway)";
    if ($o['mode'] !== 'apply') { WP_CLI::log("WOULD CREATE  $sku  $title  variations=" . count($tpl->get_children())); continue; }
    $p = new WC_Product_Variable();
    $p->set_name($title);
    $p->set_status('draft');
    $p->set_catalog_visibility('hidden');
    $p->set_sku($sku);
    $p->set_image_id($tpl->get_image_id('edit'));
    $attrs = [];
    foreach ($tpl->get_attributes('edit') as $k => $at) $attrs[$k] = clone $at;
    $p->set_attributes($attrs);
    $new_id = $p->save();
    update_post_meta($new_id, '_ahc_fixture', '1');
    $n = 0;
    foreach ($tpl->get_children() as $vid) {
        $tv = wc_get_product($vid);
        $v = new WC_Product_Variation();
        $v->set_parent_id($new_id);
        $v->set_attributes($tv->get_attributes('edit'));
        $v->set_regular_price($tv->get_regular_price('edit'));
        $v->set_sale_price($tv->get_sale_price('edit'));
        $v->set_manage_stock($tv->get_manage_stock('edit'));
        $v->set_stock_quantity($tv->get_stock_quantity('edit'));
        $v->set_stock_status($tv->get_stock_status('edit'));
        $v->set_image_id($tv->get_image_id('edit'));
        $v->set_sku($sku . '-' . (++$n));
        $v->set_status('publish');   // variation status; the parent stays draft
        $v->save();
        update_post_meta($v->get_id(), '_ahc_fixture', '1');
    }
    WC_Product_Variable::sync($new_id);
    WP_CLI::log("CREATED  $sku  id=$new_id  variations=$n  (draft, hidden)");
}
WP_CLI::log('DONE mode=' . $o['mode'] . ' fixtures=' . count($rows));
