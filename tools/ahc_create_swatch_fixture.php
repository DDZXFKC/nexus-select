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
 *   The run manifest (manifest=<new file>, created exclusively) lists the run id and every PLANNED
 *   SKU before anything is saved; markers (_ahc_fixture, _ahc_fixture_run) are set on each object
 *   before save(). NOTE: a Woo save is not a DB transaction (post insert and meta writes are separate),
 *   so an interruption between them CAN leave an unmarked post. That case is not auto-deleted: take a
 *   full DB snapshot before create and restore it if the run is interrupted (GPT 7bf74dd).
 * remove: finds every post of any status (trash included) carrying this run's marker, checks each one
 *   (type, fixture marker, run id, planned FX-SP- SKU, child's actual parent = its planned parent,
 *   parent draft) and deletes children then parents, verifying each deletion. Any empty SKU, unplanned
 *   SKU, top-level child or type mismatch stops the whole remove (restore the DB snapshot instead).
 *   Idempotent: an interrupted remove can simply be run again. Dry run unless "apply".
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

// ------------------------------------------------------------------ remove (discover by run id, idempotent)
if ($o['cmd'] === 'remove') {
    $man = json_decode((string) @file_get_contents($o['manifest']), true);
    $run = is_array($man) ? (string) ($man['run_id'] ?? '') : '';
    if (!is_array($man) || ($man['format'] ?? '') !== 'ahc-fixture-manifest-v2' || ($man['site'] ?? '') !== $host
        || !preg_match('/^fx-\d{14}-[A-Za-z0-9]{6}$/', $run) || !is_array($man['planned'] ?? null)) {
        WP_CLI::error('Manifest invalid, empty run id, or for another site.');
    }
    $parent_skus = []; $child_skus = [];
    foreach ($man['planned'] as $pl) {
        $ps = (string) ($pl['sku'] ?? '');
        if (!preg_match('/^FX-SP-\d+$/', $ps) || isset($parent_skus[$ps])) WP_CLI::error("Manifest: bad or duplicate planned SKU $ps");
        $parent_skus[$ps] = true;
        foreach ((array) ($pl['child_skus'] ?? []) as $cs) {
            if (strpos((string) $cs, $ps . '-') !== 0 || isset($child_skus[$cs])) WP_CLI::error("Manifest: bad or duplicate child SKU $cs");
            $child_skus[$cs] = $ps;
        }
    }
    $all_status = array_merge(array_keys(get_post_stati()), ['trash', 'auto-draft', 'inherit']);
    $found = get_posts(['post_type' => ['product', 'product_variation'], 'post_status' => array_values(array_unique($all_status)),
        'numberposts' => -1, 'fields' => 'ids', 'meta_query' => [['key' => '_ahc_fixture_run', 'value' => $run]]]);
    $bad = []; $parents = []; $children = []; $parent_id_by_sku = [];
    foreach ($found as $id) {
        $p = wc_get_product($id);
        if (!$p) { $bad[] = "$id: not a product"; continue; }
        if (get_post_meta($id, '_ahc_fixture', true) !== '1') { $bad[] = "$id: missing fixture marker"; continue; }
        $sku = $p->get_sku();
        if ($sku === '') { $bad[] = "$id: empty SKU (not auto-deleted; restore the DB snapshot)"; continue; }
        if (isset($parent_skus[$sku])) {
            if (!$p->is_type('variable') || $p->get_parent_id() !== 0 || $p->get_status() !== 'draft') { $bad[] = "$id $sku: parent is not a draft top-level variable product"; continue; }
            foreach ($p->get_children() as $vid) {
                if (get_post_meta($vid, '_ahc_fixture_run', true) !== $run) $bad[] = "$id $sku: has a child $vid that is not from this run";
            }
            $parents[$id] = $sku;
            $parent_id_by_sku[$sku] = $id;
        } elseif (isset($child_skus[$sku])) {
            if (!$p->is_type('variation') || $p->get_parent_id() === 0) { $bad[] = "$id $sku: child is not a variation with a parent"; continue; }
            $children[$id] = $sku;
        } else {
            $bad[] = "$id: SKU $sku is not planned in this manifest";
        }
    }
    foreach ($children as $id => $sku) {
        $par = wc_get_product($id)->get_parent_id();
        $want = $child_skus[$sku];
        if (!isset($parent_id_by_sku[$want])) {
            // planned parent already deleted (resumed remove): the actual parent must be gone too
            if (get_post($par)) $bad[] = "child $id $sku: parent $par is not its planned parent $want";
        } elseif ($par !== $parent_id_by_sku[$want]) {
            $bad[] = "child $id $sku: actual parent $par != planned parent $want ({$parent_id_by_sku[$want]})";
        }
    }
    if ($bad) { foreach ($bad as $x) WP_CLI::warning($x); WP_CLI::error(count($bad) . ' check error(s). Nothing was removed.'); }
    foreach ($children as $id => $sku) WP_CLI::log(($o['apply'] ? 'REMOVE ' : 'WOULD REMOVE ') . "child $id $sku");
    foreach ($parents as $id => $sku) WP_CLI::log(($o['apply'] ? 'REMOVE ' : 'WOULD REMOVE ') . "parent $id $sku");
    if (!$o['apply']) { WP_CLI::log('DRY RUN remove parents=' . count($parents) . ' children=' . count($children) . " run=$run"); return; }
    foreach (array_merge(array_keys($children), array_keys($parents)) as $id) {
        wp_delete_post($id, true);
        if (get_post($id)) WP_CLI::error("Delete of $id did not take effect; stopped. Re-run the same remove to continue.");
    }
    WP_CLI::log('REMOVED parents=' . count($parents) . ' children=' . count($children) . " run=$run");
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

$run = 'fx-' . gmdate('YmdHis') . '-' . wp_generate_password(6, false, false);
$planned = [];
foreach ($rows as [$pid, $colorway, $sku]) {
    $planned[] = ['supplier_product_id' => $pid, 'sku' => $sku,
        'child_skus' => array_map(function ($n) use ($sku) { return "$sku-$n"; }, range(1, count($tkids)))];
}
$man = ['format' => 'ahc-fixture-manifest-v2', 'site' => $host, 'run_id' => $run, 'template' => $o['template'],
    'planned' => $planned, 'created' => []];
$json = wp_json_encode($man, JSON_UNESCAPED_UNICODE);
$mh = @fopen($o['manifest'], 'x');   // exclusive: never reuse or overwrite a manifest
if (!$mh || fwrite($mh, $json) !== strlen($json) || !fflush($mh)) WP_CLI::error('Could not create the manifest exclusively. Nothing was created.');
fclose($mh);
if (file_get_contents($o['manifest']) !== $json) WP_CLI::error('Manifest readback failed. Nothing was created.');
$save_manifest = function () use (&$man, $o, $run) {
    $json = wp_json_encode($man, JSON_UNESCAPED_UNICODE);
    $tmp = $o['manifest'] . '.' . $run . '.tmp';
    if (file_put_contents($tmp, $json) !== strlen($json) || !rename($tmp, $o['manifest'])) {
        throw new Exception('could not update the manifest');
    }
};
try {
    foreach ($rows as $ri => [$pid, $colorway, $sku]) {
        $p = new WC_Product_Variable();
        $p->set_name("[FIXTURE] $base ($colorway)");
        $p->set_status('draft');
        $p->set_catalog_visibility('hidden');
        $p->set_sku($sku);
        $p->set_image_id($tpl->get_image_id('edit'));
        $attrs = [];
        foreach ($tpl->get_attributes('edit') as $k => $at) $attrs[$k] = clone $at;
        $p->set_attributes($attrs);
        // Markers are part of the same save: an interrupted run never leaves an unmarked post.
        $p->update_meta_data('_ahc_fixture', '1');
        $p->update_meta_data('_ahc_fixture_run', $run);
        $p->update_meta_data('_ahc_fixture_note', 'SYNTHETIC test fixture; prices/sizes/images copied from ' . $o['template'] . ', not supplier data');
        $new_id = $p->save();
        if (!$new_id) throw new Exception("save failed for $sku");
        $man['created'][] = ['id' => $new_id, 'sku' => $sku, 'children' => []];
        $ci = count($man['created']) - 1;
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
            $v->update_meta_data('_ahc_fixture', '1');
            $v->update_meta_data('_ahc_fixture_run', $run);
            $vid_new = $v->save();
            if (!$vid_new) throw new Exception("variation save failed for $sku-$n");
            $man['created'][$ci]['children'][] = $vid_new;
            $save_manifest();
        }
        WC_Product_Variable::sync($new_id);
        $chk = wc_get_product($new_id);
        if (!$chk || $chk->get_sku() !== $sku || $chk->get_status() !== 'draft' || count($chk->get_children()) !== count($tkids)
            || get_post_meta($new_id, '_ahc_fixture', true) !== '1' || get_post_meta($new_id, '_ahc_fixture_run', true) !== $run) {
            throw new Exception("readback failed for $sku");
        }
        foreach ($chk->get_children() as $vid) {
            if (get_post_meta($vid, '_ahc_fixture', true) !== '1' || get_post_meta($vid, '_ahc_fixture_run', true) !== $run) throw new Exception("child marker readback failed for $sku");
        }
        WP_CLI::log("CREATED  $sku  id=$new_id  variations=$n  (draft, hidden, purchase refused)");
    }
} catch (Throwable $e) {
    WP_CLI::error('Create failed: ' . $e->getMessage() . '. Check what to clean up with (dry run): remove manifest=' . $o['manifest'] . ' site=' . $host);
}
WP_CLI::log("DONE fixtures=" . count($rows) . " run=$run manifest=" . $o['manifest']);
