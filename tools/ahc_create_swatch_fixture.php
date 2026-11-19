<?php
/**
 * Isolated DRAFT fixtures for the swatch check (GPT 84e54b3 §4; audits 5dc4c1b, c7e70d6). Local only.
 *
 * create: for each row "supplier_product_id,colorway_original" in fixtures=<csv>, makes a draft variable
 *   product from template=<existing SP parent SKU> (size variations, prices, stock and image copied as
 *   SYNTHETIC test values - not supplier data; the template is not changed):
 *     parent SKU FX-SP-<id>, variations FX-SP-<id>-<n>, title "[FIXTURE] ... (<colorway>)",
 *     status draft, catalog visibility hidden, meta _ahc_fixture=1 and _ahc_fixture_run=<run_id>
 *     on parent and variations. Purchase is refused by mu-plugins/ahc-fixture-guard.php.
 *   Every planned SKU (parent and children) is checked for collisions and CSV duplicates first.
 *   A run manifest (manifest=<new file>) records each created post id as it is saved, so a
 *   failed run can be cleaned up with "remove" using the same manifest.
 * remove: deletes only the posts listed in manifest=<file> whose parent/child markers, run id,
 *   FX-SP- SKU, parent id and draft status all match. Dry run unless "apply".
 *
 * Run (plain key=value args; WP-CLI 2.12 does not pass --options to eval-file):
 *   wp eval-file tools/ahc_create_swatch_fixture.php create fixtures=<csv> template=SP-<id> manifest=<new file> site=<host> [apply] --path=...
 *   wp eval-file tools/ahc_create_swatch_fixture.php remove manifest=<file> site=<host> [apply] --path=...
 */
if (!defined('ABSPATH')) exit(1);
$host = (string) wp_parse_url(home_url(), PHP_URL_HOST);
if (!preg_match('/(\.local|\.localhost|\.test)$|^localhost$/', $host)) WP_CLI::error("Local only: $host");
$o = ['cmd' => null, 'fixtures' => null, 'template' => null, 'manifest' => null, 'site' => null, 'apply' => false];
foreach ((isset($args) ? $args : []) as $a) {
    $a = preg_replace('/^--/', '', (string) $a);
    if ($a === 'create' || $a === 'remove') $o['cmd'] = $a;
    elseif ($a === 'apply') $o['apply'] = true;
    elseif (preg_match('/^(fixtures|template|manifest|site)=(.+)$/', $a, $m)) $o[$m[1]] = $m[2];
    else WP_CLI::error("Unknown argument: $a");
}
if ($o['site'] !== $host) WP_CLI::error("site=<host> must equal $host");
if (!$o['cmd'] || !$o['manifest']) WP_CLI::error('create|remove and manifest=<file> are required');
$sku_taken = function ($sku) {
    global $wpdb;
    return (int) $wpdb->get_var($wpdb->prepare(
        "SELECT COUNT(*) FROM {$wpdb->postmeta} m JOIN {$wpdb->posts} p ON p.ID = m.post_id
         WHERE m.meta_key = '_sku' AND m.meta_value = %s AND p.post_status <> 'trash'", $sku)) > 0;
};

// ------------------------------------------------------------------ remove
if ($o['cmd'] === 'remove') {
    $man = json_decode((string) @file_get_contents($o['manifest']), true);
    if (!is_array($man) || ($man['format'] ?? '') !== 'ahc-fixture-manifest-v1' || ($man['site'] ?? '') !== $host || !is_array($man['parents'] ?? null)) {
        WP_CLI::error('Manifest invalid or for another site.');
    }
    $run = (string) $man['run_id'];
    $bad = []; $plan = [];
    foreach ($man['parents'] as $pe) {
        $id = (int) ($pe['id'] ?? 0);
        $p = $id ? wc_get_product($id) : null;
        if (!$p) { $bad[] = "parent $id missing (already removed?)"; continue; }
        if ($p->get_sku() !== $pe['sku'] || strpos($p->get_sku(), 'FX-SP-') !== 0 || $p->get_status() !== 'draft'
            || get_post_meta($id, '_ahc_fixture', true) !== '1' || get_post_meta($id, '_ahc_fixture_run', true) !== $run) {
            $bad[] = "parent $id {$pe['sku']}: marker/SKU/run/status mismatch"; continue;
        }
        $kids = array_map('intval', $p->get_children());
        $listed = array_map('intval', $pe['children'] ?? []);
        sort($kids); sort($listed);
        if ($kids !== $listed) { $bad[] = "parent $id: children differ from manifest"; continue; }
        foreach ($kids as $vid) {
            $v = wc_get_product($vid);
            if (!$v || $v->get_parent_id() !== $id || strpos($v->get_sku(), $pe['sku'] . '-') !== 0
                || get_post_meta($vid, '_ahc_fixture', true) !== '1' || get_post_meta($vid, '_ahc_fixture_run', true) !== $run) {
                $bad[] = "child $vid of $id: marker/SKU/parent mismatch"; continue 2;
            }
        }
        $plan[$id] = [$pe['sku'], $kids];
    }
    if ($bad) { foreach ($bad as $b) WP_CLI::warning($b); WP_CLI::error(count($bad) . ' check error(s). Nothing was removed.'); }
    foreach ($plan as $id => [$sku, $kids]) WP_CLI::log(($o['apply'] ? 'REMOVE ' : 'WOULD REMOVE ') . "$sku id=$id children=" . count($kids));
    if (!$o['apply']) { WP_CLI::log('DRY RUN remove parents=' . count($plan)); return; }
    foreach ($plan as $id => [$sku, $kids]) {
        foreach ($kids as $vid) wp_delete_post($vid, true);
        wp_delete_post($id, true);
        if (get_post($id)) WP_CLI::error("Delete of $id did not take effect; stopped.");
    }
    WP_CLI::log('REMOVED parents=' . count($plan) . " run=$run");
    return;
}

// ------------------------------------------------------------------ create: validate everything first
if (!$o['fixtures'] || !is_readable($o['fixtures']) || !$o['template']) WP_CLI::error('fixtures=<csv> and template=<SP-sku> are required');
if (file_exists($o['manifest'])) WP_CLI::error('manifest must be a new file');
$tid = wc_get_product_id_by_sku($o['template']);
$tpl = $tid ? wc_get_product($tid) : null;
if (!$tpl || !$tpl->is_type('variable') || strpos($tpl->get_sku(), 'SP-') !== 0) WP_CLI::error('template must be an existing SP- variable product');
foreach (array_keys($tpl->get_variation_attributes()) as $ak) if (stripos($ak, 'color') !== false) WP_CLI::error('template must not have a color variation');
$tkids = $tpl->get_children();
if (!$tkids) WP_CLI::error('template has no variations');

$fh = fopen($o['fixtures'], 'r');
if (fgetcsv($fh) !== ['supplier_product_id', 'colorway_original']) WP_CLI::error('fixtures header must be: supplier_product_id,colorway_original');
$rows = []; $errs = []; $seen = [];
while (($r = fgetcsv($fh)) !== false) {
    if (count($r) === 1 && trim((string) $r[0]) === '') continue;
    if (count($r) !== 2 || !preg_match('/^\d+$/', $r[0])) { $errs[] = 'bad row: ' . implode(',', $r); continue; }
    if (isset($seen[$r[0]])) { $errs[] = "duplicate id {$r[0]} in fixtures CSV"; continue; }
    $seen[$r[0]] = true;
    $sku = 'FX-SP-' . $r[0];
    foreach (array_merge([$sku, 'SP-' . $r[0]], array_map(function ($n) use ($sku) { return "$sku-$n"; }, range(1, count($tkids)))) as $s) {
        if ($sku_taken($s)) $errs[] = "SKU $s already exists";
    }
    $rows[] = [$r[0], $r[1], $sku];
}
fclose($fh);
if (!$rows) $errs[] = 'no fixtures';
if ($errs) { foreach ($errs as $e) WP_CLI::warning($e); WP_CLI::error(count($errs) . ' error(s). Nothing was created.'); }

$base = trim(preg_replace('/\s*\([^()]*\)\s*$/u', '', $tpl->get_name()));
if (!$o['apply']) {
    foreach ($rows as [$pid, $colorway, $sku]) WP_CLI::log("WOULD CREATE  $sku  [FIXTURE] $base ($colorway)  variations=" . count($tkids));
    WP_CLI::log('DRY RUN fixtures=' . count($rows));
    return;
}

$run = 'fx-' . gmdate('YmdHis') . '-' . wp_generate_password(6, false);
$man = ['format' => 'ahc-fixture-manifest-v1', 'site' => $host, 'run_id' => $run, 'template' => $o['template'], 'parents' => []];
$save_manifest = function () use (&$man, $o) {
    $json = wp_json_encode($man, JSON_UNESCAPED_UNICODE);
    if (file_put_contents($o['manifest'] . '.tmp', $json) !== strlen($json) || !rename($o['manifest'] . '.tmp', $o['manifest'])) {
        WP_CLI::error('Could not write the run manifest; stop and clean up with remove.');
    }
};
$save_manifest();   // exists before the first post is created
try {
    foreach ($rows as [$pid, $colorway, $sku]) {
        $p = new WC_Product_Variable();
        $p->set_name("[FIXTURE] $base ($colorway)");
        $p->set_status('draft');
        $p->set_catalog_visibility('hidden');
        $p->set_sku($sku);
        $p->set_image_id($tpl->get_image_id('edit'));
        $attrs = [];
        foreach ($tpl->get_attributes('edit') as $k => $at) $attrs[$k] = clone $at;
        $p->set_attributes($attrs);
        $new_id = $p->save();
        if (!$new_id) throw new Exception("save failed for $sku");
        update_post_meta($new_id, '_ahc_fixture', '1');
        update_post_meta($new_id, '_ahc_fixture_run', $run);
        update_post_meta($new_id, '_ahc_fixture_note', 'SYNTHETIC test fixture; prices/sizes/images copied from ' . $o['template'] . ', not supplier data');
        $man['parents'][] = ['id' => $new_id, 'sku' => $sku, 'supplier_product_id' => $pid, 'children' => []];
        $pi = count($man['parents']) - 1;
        $save_manifest();
        $n = 0;
        foreach ($tkids as $vid) {
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
            $vid_new = $v->save();
            if (!$vid_new) throw new Exception("variation save failed for $sku-$n");
            update_post_meta($vid_new, '_ahc_fixture', '1');
            update_post_meta($vid_new, '_ahc_fixture_run', $run);
            $man['parents'][$pi]['children'][] = $vid_new;
            $save_manifest();
        }
        WC_Product_Variable::sync($new_id);
        // Read back.
        $chk = wc_get_product($new_id);
        if (!$chk || $chk->get_sku() !== $sku || $chk->get_status() !== 'draft' || count($chk->get_children()) !== count($tkids)
            || get_post_meta($new_id, '_ahc_fixture', true) !== '1') {
            throw new Exception("readback failed for $sku");
        }
        WP_CLI::log("CREATED  $sku  id=$new_id  variations=$n  (draft, hidden, purchase refused)");
    }
} catch (Throwable $e) {
    WP_CLI::error('Create failed: ' . $e->getMessage() . '. Clean up with: remove manifest=' . $o['manifest'] . ' site=' . $host . ' apply');
}
WP_CLI::log("DONE fixtures=" . count($rows) . " run=$run manifest=" . $o['manifest']);
