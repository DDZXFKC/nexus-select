<?php
/**
 * Sheet -> Woo link for the data-driven color swatch (GPT designs 70ee059, 84e54b3; review 5dc4c1b).
 *
 * Input CSV (collector/color_woo_export.py), exact header:
 *   shop_code,market,supplier_product_id,supplier_color_key,colorway_original,
 *   swatch_status,position,token_original,display_hex,hex_status
 * One row per color component; position 0 = marker row for a product without components.
 *
 * Writes, per allowlisted Shoe Palace product (parent SKU SP-<supplier_product_id>):
 *   _ahc_color_components          {"__single__": [{"name": "...", "hex": "#RRGGBB"|null}, ...]}
 *   _ahc_color_components_context  {"schema_version":2,"shop_code","market","supplier_product_id",
 *                                   "supplier_color_key","colorway_original","swatch_status"}
 * Nothing else is touched; a guard snapshot (parent + variations: SKU, name, status, prices incl.
 * effective price, stock, images, gallery, attributes) must be identical after the write.
 *
 * Required arguments (WP-CLI 2.12 does not pass --options to eval-file, so plain key=value):
 *   site=<host>        must equal this site's host (Local hosts only)
 *   allowlist=<file>   supplier_product_ids to process (one per line)
 *   mapping=<file>     verified CSV "supplier_product_id,market,parent_sku" from Local evidence
 *                      (read-only check by Muse). The CSV market must equal the mapping market.
 *                      parent_sku is SP-<id> (real product) or FX-SP-<id> (isolated draft fixture
 *                      made by tools/ahc_create_swatch_fixture.php; must be draft with _ahc_fixture=1).
 * Options:
 *   apply backup=<new file>   write (default is dry run). The backup is created exclusively.
 *   allow_published=1         allow writing to published posts (default: drafts only)
 *   rollback=<backup file>    restore a backup (all posts pre-checked first, compare-and-swap)
 *
 * Every check runs before any write. Any error -> nothing is written (no partial apply).
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
$opt = ['csv' => null, 'site' => null, 'allowlist' => null, 'mapping' => null, 'apply' => false, 'backup' => null,
    'rollback' => null, 'allow_published' => false];
foreach ((isset($args) && is_array($args) ? $args : []) as $a) {
    $a = preg_replace('/^--/', '', (string) $a);
    if ($a === 'apply') $opt['apply'] = true;
    elseif ($a === 'allow_published=1') $opt['allow_published'] = true;
    elseif (preg_match('/^(site|allowlist|mapping|backup|rollback)=(.+)$/', $a, $m)) $opt[$m[1]] = $m[2];
    elseif ($opt['csv'] === null && strpos($a, '=') === false) $opt['csv'] = $a;
    else WP_CLI::error("Unknown argument: $a");
}
if ($opt['site'] !== $host) WP_CLI::error("site=<host> must equal this site's host ($host).");
$site_id = ['host' => $host, 'home' => home_url(), 'blog_id' => function_exists('get_current_blog_id') ? get_current_blog_id() : 1];

if (!function_exists('ahc_guard_snapshot')) {
    /** Snapshot of everything this tool must NOT change. */
    function ahc_guard_snapshot($pid) {
        $p = wc_get_product($pid);
        $kids = [];
        foreach ($p->get_children() as $vid) {
            $v = wc_get_product($vid);
            $kids[$vid] = [$v->get_sku(), $v->get_price('edit'), $v->get_regular_price('edit'), $v->get_sale_price('edit'),
                $v->get_stock_status('edit'), $v->get_stock_quantity('edit'), $v->get_image_id('edit'), $v->get_attributes('edit')];
        }
        $attrs = [];
        foreach ($p->get_attributes('edit') as $k => $at) $attrs[$k] = is_object($at) ? $at->get_data() : $at;
        return md5(serialize([$p->get_sku(), $p->get_name(), $p->get_status(), $p->get_price('edit'), $p->get_regular_price('edit'),
            $p->get_sale_price('edit'), $p->get_stock_status('edit'), $p->get_stock_quantity('edit'), $p->get_image_id('edit'),
            $p->get_gallery_image_ids('edit'), $attrs, $kids]));
    }
    function ahc_current($post_id) {
        $cur = [];
        foreach ([AHC_META, AHC_CTX] as $k) $cur[$k] = metadata_exists('post', $post_id, $k) ? (string) get_post_meta($post_id, $k, true) : null;
        return $cur;
    }
    function ahc_set($post_id, $vals) {
        foreach ([AHC_META, AHC_CTX] as $k) {
            if ($vals[$k] === null) delete_post_meta($post_id, $k);
            else update_post_meta($post_id, $k, wp_slash($vals[$k]));
        }
    }
    function ahc_norm($t) {
        if (class_exists('Normalizer')) $t = Normalizer::normalize((string) $t, Normalizer::FORM_KC);
        return trim(preg_replace('/\s+/u', ' ', mb_strtolower((string) $t)));
    }
}

// ------------------------------------------------------------------ rollback (all checks first, CAS)
if ($opt['rollback'] !== null) {
    $raw = @file_get_contents($opt['rollback']);
    $bk = $raw === false ? null : json_decode($raw, true);
    $bad = [];
    if (!is_array($bk) || ($bk['format'] ?? '') !== 'ahc-swatch-backup-v2' || ($bk['site'] ?? null) !== $site_id || !is_array($bk['posts'] ?? null)) {
        WP_CLI::error('Backup file invalid, wrong format, or for another site.');
    }
    $is_val = function ($v) { return is_array($v) && array_keys($v) === [AHC_META, AHC_CTX]
        && (is_string($v[AHC_META]) || $v[AHC_META] === null) && (is_string($v[AHC_CTX]) || $v[AHC_CTX] === null); };
    foreach ($bk['posts'] as $post_id => $e) {
        if (!preg_match('/^\d+$/', (string) $post_id) || !is_array($e) || !isset($e['sku'], $e['old'], $e['new']) || !$is_val($e['old']) || !$is_val($e['new'])) {
            $bad[] = "$post_id: malformed entry"; continue;
        }
        $p = wc_get_product((int) $post_id);
        if (!$p || $p->get_sku() !== $e['sku']) { $bad[] = "$post_id: SKU differs from backup ({$e['sku']})"; continue; }
        $cur = ahc_current((int) $post_id);
        // CAS: current must be what this tool wrote, or already the old value (not written / already restored).
        if ($cur !== $e['new'] && $cur !== $e['old']) $bad[] = "$post_id {$e['sku']}: changed since the write; not restoring";
    }
    if ($bad) { foreach ($bad as $b) WP_CLI::warning($b); WP_CLI::error(count($bad) . ' rollback check error(s). Nothing was restored.'); }
    $restored = 0; $mismatch = 0;
    foreach ($bk['posts'] as $post_id => $e) {
        if (ahc_current((int) $post_id) === $e['old']) continue;
        ahc_set((int) $post_id, $e['old']);
        $restored++;
    }
    foreach ($bk['posts'] as $post_id => $e) if (ahc_current((int) $post_id) !== $e['old']) $mismatch++;
    WP_CLI::log('ROLLBACK ' . wp_json_encode(['posts' => count($bk['posts']), 'restored' => $restored, 'readback_mismatch' => $mismatch]));
    if ($mismatch) WP_CLI::error('Rollback readback mismatch; re-run the same rollback (it is idempotent).');
    return;
}

// ------------------------------------------------------------------ read + validate (no writes)
foreach (['csv', 'allowlist', 'mapping'] as $k) if (!$opt[$k] || !is_readable($opt[$k])) WP_CLI::error("$k file is required and must be readable.");
if ($opt['apply'] && !$opt['backup']) WP_CLI::error('apply requires backup=<new file>.');
$allow = array_values(array_filter(array_map('trim', file($opt['allowlist'])), 'strlen'));
if (!$allow || count($allow) !== count(array_unique($allow))) WP_CLI::error('Allowlist is empty or has duplicates.');
foreach ($allow as $x) if (!preg_match('/^\d+$/', $x)) WP_CLI::error("Allowlist id is not numeric: $x");
$allow = array_flip($allow);

$mapping = [];
$mh = fopen($opt['mapping'], 'r');
if (fgetcsv($mh) !== ['supplier_product_id', 'market', 'parent_sku']) WP_CLI::error('mapping header must be exactly: supplier_product_id,market,parent_sku');
while (($m = fgetcsv($mh)) !== false) {
    if (count($m) === 1 && trim((string) $m[0]) === '') continue;
    if (count($m) !== 3 || isset($mapping[$m[0]])) WP_CLI::error('mapping: malformed or duplicate row for ' . ($m[0] ?? '?'));
    $mapping[$m[0]] = ['market' => $m[1], 'sku' => $m[2]];
}
fclose($mh);

$errors = [];
$err = function ($m) use (&$errors) { $errors[] = $m; };
$fh = fopen($opt['csv'], 'r');
if (fgetcsv($fh) !== AHC_FIELDS) WP_CLI::error('CSV header must be exactly: ' . implode(',', AHC_FIELDS));
$groups = [];
$line = 1;
while (($row = fgetcsv($fh)) !== false) {
    $line++;
    if (count($row) === 1 && trim((string) $row[0]) === '') continue;
    if (count($row) !== count(AHC_FIELDS)) { $err("line $line: column count " . count($row)); continue; }
    $r = array_combine(AHC_FIELDS, $row);   // values kept as-is (originals are not trimmed)
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
    } elseif ($r['hex_status'] === 'APPROVED_APPROX') { $err("line $line: APPROVED_APPROX without hex"); continue; }
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
    [$market, $colorway, $status] = $g['ctx'];
    if (!isset($mapping[$pid])) { $err("$pid: no verified market mapping"); continue; }
    // Real product SP-<pid>, or an isolated draft fixture FX-SP-<pid> (tools/ahc_create_swatch_fixture.php).
    $sku = $mapping[$pid]['sku'];
    $is_fixture = $sku === 'FX-SP-' . $pid;
    if ($sku !== 'SP-' . $pid && !$is_fixture) { $err("$pid: mapping parent_sku $sku must be SP-$pid or FX-SP-$pid"); continue; }
    if ($mapping[$pid]['market'] !== $market) $err("$pid: CSV market $market != verified Local market {$mapping[$pid]['market']}");
    if ($g['marker'] > 1) $err("$pid: duplicate marker row");
    if ($g['marker'] && $g['comps']) $err("$pid: marker row mixed with components");
    ksort($g['comps']);
    if ($g['comps'] && array_keys($g['comps']) !== range(1, count($g['comps']))) $err("$pid: positions are not 1..n");
    if ($status === 'CONFIRMED') {
        if (!$g['comps']) $err("$pid: CONFIRMED without components");
        foreach (array_slice(array_values($g['comps']), 0, 3) as $i => $c) if ($c['hex'] === null) $err("$pid: CONFIRMED but color " . ($i + 1) . ' has no hex');
    }
    if ($g['comps'] && $status !== 'HOLD') {
        $orig = array_values(array_filter(explode('/', $colorway), function ($t) { return trim($t) !== ''; }));
        $names = array_map(function ($c) { return $c['name']; }, array_values($g['comps']));
        if (array_map('ahc_norm', $orig) !== array_map('ahc_norm', $names)) $err("$pid: colorway_original does not match the components");
    }
    $ids = $wpdb->get_col($wpdb->prepare(
        "SELECT p.ID FROM {$wpdb->posts} p JOIN {$wpdb->postmeta} m ON m.post_id = p.ID
         WHERE m.meta_key = '_sku' AND m.meta_value = %s AND p.post_type IN ('product','product_variation') AND p.post_status <> 'trash'", $sku));
    if (count($ids) !== 1) { $err("$sku: found " . count($ids) . ' posts (need exactly 1)'); continue; }
    $post_id = (int) $ids[0];
    $product = wc_get_product($post_id);
    if (!$product || !$product->is_type('variable')) { $err("$sku: not a variable product"); continue; }
    if ($is_fixture && (get_post_meta($post_id, '_ahc_fixture', true) !== '1' || $product->get_status() !== 'draft')) { $err("$sku: not a draft fixture"); continue; }
    if (!$opt['allow_published'] && $product->get_status() !== 'draft') { $err("$sku: status {$product->get_status()} (only drafts without allow_published=1)"); continue; }
    if (isset($seen_post[$post_id])) { $err("$sku: parent already used by {$seen_post[$post_id]}"); continue; }
    $seen_post[$post_id] = $pid;
    foreach (array_keys($product->get_variation_attributes()) as $ak) {
        if (stripos($ak, 'color') !== false) { $err("$sku: has a color variation ($ak) - out of scope"); continue 2; }
    }
    $new = [
        AHC_META => wp_json_encode(['__single__' => array_values($g['comps'])], JSON_UNESCAPED_UNICODE),
        AHC_CTX => wp_json_encode(['schema_version' => 2, 'shop_code' => 'SP', 'market' => $market, 'supplier_product_id' => $pid,
            'supplier_color_key' => 'single', 'colorway_original' => $colorway, 'swatch_status' => $status], JSON_UNESCAPED_UNICODE),
    ];
    $plan[$post_id] = ['sku' => $sku, 'old' => ahc_current($post_id), 'new' => $new];
}

if ($errors) {
    foreach (array_slice($errors, 0, 50) as $e) WP_CLI::warning($e);
    WP_CLI::error(count($errors) . ' validation error(s). Nothing was written.');
}

// ------------------------------------------------------------------ dry run / apply
$stats = ['planned' => count($plan), 'unchanged' => 0, 'would_write' => 0, 'written' => 0];
foreach ($plan as $post_id => $p) {
    if ($p['old'] === $p['new']) { $stats['unchanged']++; unset($plan[$post_id]); continue; }
    $stats['would_write']++;
    WP_CLI::log("PLAN  {$p['sku']}  {$p['new'][AHC_META]}  {$p['new'][AHC_CTX]}");
}
if (!$opt['apply']) { WP_CLI::log('DRY RUN ' . wp_json_encode($stats)); return; }
if (!$plan) { WP_CLI::log('APPLIED ' . wp_json_encode($stats) . ' (nothing to write, no backup created)'); return; }

// Backup: exclusive create, full write, then read back and compare before any write.
$backup = ['format' => 'ahc-swatch-backup-v2', 'site' => $site_id, 'created_at' => gmdate('c'), 'posts' => []];
foreach ($plan as $post_id => $p) $backup['posts'][(string) $post_id] = ['sku' => $p['sku'], 'old' => $p['old'], 'new' => $p['new']];
$json = wp_json_encode($backup, JSON_UNESCAPED_UNICODE);
$bh = @fopen($opt['backup'], 'x');
if (!$bh) WP_CLI::error('Could not create backup exclusively (exists or not writable). Nothing was written.');
$ok = fwrite($bh, $json) === strlen($json) && fflush($bh);
fclose($bh);
if (!$ok || file_get_contents($opt['backup']) !== $json) WP_CLI::error('Backup write could not be verified. Nothing was written.');

$guard = [];
foreach ($plan as $post_id => $p) $guard[$post_id] = ahc_guard_snapshot($post_id);
foreach ($plan as $post_id => $p) {
    // CAS: nothing else may have changed the meta since validation.
    if (ahc_current($post_id) !== $p['old']) WP_CLI::error("{$p['sku']} changed during the run. Stopped after {$stats['written']} write(s); run rollback=" . $opt['backup']);
    ahc_set($post_id, $p['new']);
    $stats['written']++;
}
if (function_exists('wc_delete_product_transients')) foreach ($plan as $post_id => $p) wc_delete_product_transients($post_id);
$bad_read = 0; $bad_guard = 0;
foreach ($plan as $post_id => $p) {
    if (ahc_current($post_id) !== $p['new']) $bad_read++;
    if (ahc_guard_snapshot($post_id) !== $guard[$post_id]) $bad_guard++;
}
$stats['readback_mismatch'] = $bad_read;
$stats['other_fields_changed'] = $bad_guard;
WP_CLI::log('APPLIED ' . wp_json_encode($stats) . ' backup=' . $opt['backup']);
if ($bad_read || $bad_guard) WP_CLI::error('Readback/guard mismatch: run rollback=' . $opt['backup']);
