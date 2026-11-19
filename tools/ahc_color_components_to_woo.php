<?php
/**
 * Sheet -> Woo link for the data-driven color swatch (GPT designs 70ee059, 84e54b3).
 *
 * Input: the CSV made by collector/color_woo_export.py (one row per color component;
 * position 0 = marker row for a product without components).
 * Columns (exact header):
 *   shop_code,market,supplier_product_id,supplier_color_key,colorway_original,
 *   swatch_status,position,token_original,display_hex,hex_status
 *
 * Writes, per allowlisted Shoe Palace product (parent SKU SP-<supplier_product_id>):
 *   _ahc_color_components          {"__single__": [{"name": "...", "hex": "#RRGGBB"|null}, ...]}
 *   _ahc_color_components_context  {"schema_version":2,"shop_code","market","supplier_product_id",
 *                                   "supplier_color_key","colorway_original","swatch_status"}
 * Nothing else is touched (price, stock, images, variations, attributes are snapshotted before
 * and after and must be identical).
 *
 * Safety
 * - Local only (host .local/.localhost/.test/localhost) and --site=<host> must equal the site host.
 * - --allowlist=<file> (one supplier_product_id per line) is required; only those products are processed.
 * - Every check runs before any write. Any error -> nothing is written (no partial apply).
 * - Dry run by default. --apply writes, after saving a backup JSON (--backup=<file>, required with --apply),
 *   then reads back every written value. --rollback=<backup file> restores a backup.
 * - Only products WITHOUT a color variation are in scope (SP single colorway). MERGED/PROTO/FL/CV: refused.
 *
 * Run (WP-CLI 2.12 does not pass --options to eval-file, so pass them as plain args after the CSV):
 *   wp eval-file tools/ahc_color_components_to_woo.php <csv> site=<host> allowlist=<file> [apply backup=<file>] --path=...
 *   wp eval-file tools/ahc_color_components_to_woo.php rollback=<backup file> site=<host> --path=...
 */
if (!defined('ABSPATH')) exit(1);

defined('AHC_META') || define('AHC_META', '_ahc_color_components');
defined('AHC_CTX') || define('AHC_CTX', '_ahc_color_components_context');
defined('AHC_FIELDS') || define('AHC_FIELDS', ['shop_code', 'market', 'supplier_product_id', 'supplier_color_key', 'colorway_original',
    'swatch_status', 'position', 'token_original', 'display_hex', 'hex_status']);
defined('AHC_STATUSES') || define('AHC_STATUSES', ['CONFIRMED', 'DRAFT', 'UNKNOWN', 'HOLD']);

$host = (string) wp_parse_url(home_url(), PHP_URL_HOST);
if (!preg_match('/(\.local|\.localhost|\.test)$|^localhost$/', $host)) {
    WP_CLI::error("Refusing to run on $host: Local environment only.");
}
$opt = ['csv' => null, 'site' => null, 'allowlist' => null, 'apply' => false, 'backup' => null, 'rollback' => null];
foreach ((isset($args) && is_array($args) ? $args : []) as $a) {
    $a = preg_replace('/^--/', '', (string) $a);
    if ($a === 'apply') $opt['apply'] = true;
    elseif (preg_match('/^(site|allowlist|backup|rollback)=(.+)$/', $a, $m)) $opt[$m[1]] = $m[2];
    elseif ($opt['csv'] === null && strpos($a, '=') === false) $opt['csv'] = $a;
    else WP_CLI::error("Unknown argument: $a");
}
if ($opt['site'] !== $host) WP_CLI::error("site=<host> must equal this site's host ($host).");

/** Snapshot of everything this tool must NOT change. */
if (!function_exists('ahc_guard_snapshot')) { function ahc_guard_snapshot($pid) {
    $p = wc_get_product($pid);
    $kids = [];
    foreach ($p->get_children() as $vid) {
        $v = wc_get_product($vid);
        $kids[$vid] = [$v->get_sku(), $v->get_regular_price('edit'), $v->get_sale_price('edit'), $v->get_stock_status('edit'),
            $v->get_stock_quantity('edit'), $v->get_image_id('edit'), $v->get_attributes('edit')];
    }
    $attrs = [];
    foreach ($p->get_attributes('edit') as $k => $at) $attrs[$k] = is_object($at) ? $at->get_data() : $at;
    return md5(serialize([$p->get_sku(), $p->get_name(), $p->get_status(), $p->get_image_id('edit'),
        $p->get_gallery_image_ids('edit'), $attrs, $kids]));
} }

// ------------------------------------------------------------------ rollback
if ($opt['rollback'] !== null) {
    $bk = json_decode((string) file_get_contents($opt['rollback']), true);
    if (!is_array($bk) || ($bk['site'] ?? '') !== $host || !isset($bk['posts'])) WP_CLI::error('Backup file invalid or for another site.');
    foreach ($bk['posts'] as $pid => $old) {
        foreach ([AHC_META, AHC_CTX] as $k) {
            if ($old[$k] === null) delete_post_meta((int) $pid, $k);
            else update_post_meta((int) $pid, $k, wp_slash($old[$k]));
        }
    }
    $bad = 0;
    foreach ($bk['posts'] as $pid => $old) foreach ([AHC_META, AHC_CTX] as $k) {
        $now = metadata_exists('post', (int) $pid, $k) ? (string) get_post_meta((int) $pid, $k, true) : null;
        if ($now !== $old[$k]) $bad++;
    }
    WP_CLI::log('ROLLBACK ' . wp_json_encode(['posts' => count($bk['posts']), 'readback_mismatch' => $bad]));
    if ($bad) WP_CLI::error('Rollback readback mismatch.');
    return;
}

// ------------------------------------------------------------------ read + validate (no writes)
if (!$opt['csv'] || !is_readable($opt['csv'])) WP_CLI::error('CSV path required and must be readable.');
if (!$opt['allowlist'] || !is_readable($opt['allowlist'])) WP_CLI::error('allowlist=<file> is required.');
if ($opt['apply'] && !$opt['backup']) WP_CLI::error('apply requires backup=<file>.');
if ($opt['backup'] && file_exists($opt['backup'])) WP_CLI::error('Backup file already exists; choose a new path.');
$allow = array_values(array_filter(array_map('trim', file($opt['allowlist'])), 'strlen'));
if (!$allow || count($allow) !== count(array_unique($allow))) WP_CLI::error('Allowlist is empty or has duplicates.');
foreach ($allow as $x) if (!preg_match('/^\d+$/', $x)) WP_CLI::error("Allowlist id is not numeric: $x");
$allow = array_flip($allow);

$errors = [];
$err = function ($m) use (&$errors) { $errors[] = $m; };
$fh = fopen($opt['csv'], 'r');
$header = fgetcsv($fh);
if ($header !== AHC_FIELDS) WP_CLI::error('CSV header must be exactly: ' . implode(',', AHC_FIELDS));
$groups = [];
$line = 1;
while (($row = fgetcsv($fh)) !== false) {
    $line++;
    if (count($row) === 1 && trim((string) $row[0]) === '') continue;
    if (count($row) !== count(AHC_FIELDS)) { $err("line $line: column count " . count($row)); continue; }
    $r = array_combine(AHC_FIELDS, array_map('trim', $row));
    if (!isset($allow[$r['supplier_product_id']])) continue;
    $pid = $r['supplier_product_id'];
    if ($r['shop_code'] !== 'SP') { $err("line $line: shop_code {$r['shop_code']} not in scope"); continue; }
    if ($r['supplier_color_key'] !== 'single') { $err("line $line: supplier_color_key {$r['supplier_color_key']} not in scope"); continue; }
    if (!preg_match('/^\d+$/', $r['position'])) { $err("line $line: position '{$r['position']}' is not an integer"); continue; }
    if (!in_array($r['swatch_status'], AHC_STATUSES, true)) { $err("line $line: swatch_status {$r['swatch_status']}"); continue; }
    if ($r['market'] === '') { $err("line $line: market empty"); continue; }
    $pos = (int) $r['position'];
    $hex = $r['display_hex'];
    if ($hex !== '') {
        if (!preg_match('/^#[0-9A-Fa-f]{6}$/', $hex)) { $err("line $line: bad hex $hex"); continue; }
        if ($r['swatch_status'] !== 'CONFIRMED' || $r['hex_status'] !== 'APPROVED_APPROX') { $err("line $line: hex given for non-CONFIRMED/non-approved"); continue; }
    }
    $g = &$groups[$pid];
    if (!isset($g)) $g = ['ctx' => [$r['market'], $r['colorway_original'], $r['swatch_status']], 'marker' => 0, 'comps' => []];
    if ($g['ctx'] !== [$r['market'], $r['colorway_original'], $r['swatch_status']]) $err("$pid: market/colorway/status differ between rows (or several markets for one SKU)");
    if ($pos === 0) {
        if ($r['hex_status'] !== 'NO_COMPONENTS' || $r['token_original'] !== '' || $hex !== '') $err("$pid: malformed marker row");
        $g['marker']++;
    } else {
        if (isset($g['comps'][$pos])) $err("$pid: duplicate position $pos");
        $g['comps'][$pos] = ['name' => $r['token_original'], 'hex' => $hex === '' ? null : strtoupper($hex)];
    }
    unset($g);
}
fclose($fh);

$plan = [];
$seen_post = [];
global $wpdb;
foreach ($allow as $pid => $_) {
    if (!isset($groups[$pid])) { $err("$pid: allowlisted but not in CSV"); continue; }
    $g = $groups[$pid];
    if ($g['marker'] > 1) $err("$pid: duplicate marker row");
    if ($g['marker'] && $g['comps']) $err("$pid: marker row mixed with components");
    ksort($g['comps']);
    if ($g['comps'] && array_keys($g['comps']) !== range(1, count($g['comps']))) $err("$pid: positions are not 1..n");
    [$market, $colorway, $status] = $g['ctx'];
    if ($g['comps'] && $status !== 'HOLD') {
        $orig = array_values(array_filter(array_map('trim', explode('/', $colorway)), 'strlen'));
        $names = array_map(function ($c) { return $c['name']; }, array_values($g['comps']));
        // Same normalization as color_fullrun.norm(): NFKC, casefold, collapse whitespace.
        $nz = function ($t) { if (class_exists('Normalizer')) $t = Normalizer::normalize($t, Normalizer::FORM_KC);
            return trim(preg_replace('/\s+/u', ' ', mb_strtolower((string) $t))); };
        if (array_map($nz, $orig) !== array_map($nz, $names)) $err("$pid: colorway_original does not match the components");
    }
    $sku = 'SP-' . $pid;
    $ids = $wpdb->get_col($wpdb->prepare(
        "SELECT p.ID FROM {$wpdb->posts} p JOIN {$wpdb->postmeta} m ON m.post_id = p.ID
         WHERE m.meta_key = '_sku' AND m.meta_value = %s AND p.post_type IN ('product','product_variation') AND p.post_status <> 'trash'", $sku));
    if (count($ids) !== 1) { $err("$sku: found " . count($ids) . ' posts (need exactly 1)'); continue; }
    $post_id = (int) $ids[0];
    $product = wc_get_product($post_id);
    if (!$product || !$product->is_type('variable')) { $err("$sku: not a variable product"); continue; }
    if (isset($seen_post[$post_id])) { $err("$sku: parent already used by {$seen_post[$post_id]}"); continue; }
    $seen_post[$post_id] = $pid;
    foreach (array_keys($product->get_variation_attributes()) as $ak) {
        if (stripos($ak, 'color') !== false) { $err("$sku: has a color variation ($ak) - out of scope"); continue 2; }
    }
    $meta = wp_json_encode(['__single__' => array_values($g['comps'])], JSON_UNESCAPED_UNICODE);
    $ctx = wp_json_encode(['schema_version' => 2, 'shop_code' => 'SP', 'market' => $market, 'supplier_product_id' => $pid,
        'supplier_color_key' => 'single', 'colorway_original' => $colorway, 'swatch_status' => $status], JSON_UNESCAPED_UNICODE);
    $plan[$post_id] = ['sku' => $sku, 'meta' => $meta, 'ctx' => $ctx];
}

if ($errors) {
    foreach (array_slice($errors, 0, 50) as $e) WP_CLI::warning($e);
    WP_CLI::error(count($errors) . ' validation error(s). Nothing was written.');
}

// ------------------------------------------------------------------ dry run / apply
$stats = ['planned' => count($plan), 'unchanged' => 0, 'would_write' => 0, 'written' => 0];
$old = [];
foreach ($plan as $post_id => $p) {
    $cur = [];
    foreach ([AHC_META, AHC_CTX] as $k) $cur[$k] = metadata_exists('post', $post_id, $k) ? (string) get_post_meta($post_id, $k, true) : null;
    $old[$post_id] = $cur;
    if ($cur[AHC_META] === $p['meta'] && $cur[AHC_CTX] === $p['ctx']) { $stats['unchanged']++; unset($plan[$post_id]); continue; }
    $stats['would_write']++;
    WP_CLI::log("PLAN  {$p['sku']}  {$p['meta']}  {$p['ctx']}");
}
if (!$opt['apply']) { WP_CLI::log('DRY RUN ' . wp_json_encode($stats)); return; }

$backup = ['site' => $host, 'created_at' => gmdate('c'), 'posts' => array_intersect_key($old, $plan)];
if (file_put_contents($opt['backup'], wp_json_encode($backup, JSON_UNESCAPED_UNICODE)) === false) WP_CLI::error('Could not write backup.');
$guard = [];
foreach ($plan as $post_id => $p) $guard[$post_id] = ahc_guard_snapshot($post_id);
foreach ($plan as $post_id => $p) {
    update_post_meta($post_id, AHC_META, wp_slash($p['meta']));
    update_post_meta($post_id, AHC_CTX, wp_slash($p['ctx']));
    $stats['written']++;
}
wc_delete_product_transients();
$bad_read = 0; $bad_guard = 0;
foreach ($plan as $post_id => $p) {
    if ((string) get_post_meta($post_id, AHC_META, true) !== $p['meta'] || (string) get_post_meta($post_id, AHC_CTX, true) !== $p['ctx']) $bad_read++;
    if (ahc_guard_snapshot($post_id) !== $guard[$post_id]) $bad_guard++;
}
$stats['readback_mismatch'] = $bad_read;
$stats['other_fields_changed'] = $bad_guard;
WP_CLI::log('APPLIED ' . wp_json_encode($stats) . ' backup=' . $opt['backup']);
if ($bad_read || $bad_guard) WP_CLI::error('Readback/guard mismatch: run rollback=' . $opt['backup']);
