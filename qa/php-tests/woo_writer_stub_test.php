<?php
// Offline harness for tools/ahc_color_components_to_woo.php (no WordPress; stub functions).
// Run: php qa/php-tests/woo_writer_stub_test.php
define('ABSPATH', '/');
class WP_CLI {
    static $log = [];
    static function error($m) { throw new RuntimeException($m); }
    static function warning($m) { self::$log[] = "W:$m"; }
    static function log($m) { self::$log[] = $m; }
}
$META = []; $SKU = []; $COLORVAR = [];
class P {
    function __construct($id) { $this->id = $id; }
    function is_type($t) { return $t === 'variable'; }
    function get_variation_attributes() { global $COLORVAR; return isset($COLORVAR[$this->id]) ? ['pa_color' => ['a', 'b'], 'pa_size' => ['9']] : ['pa_size' => ['9', '10']]; }
    function get_children() { return []; }
    function __call($n, $a) { return $n === 'get_attributes' ? [] : ($n === 'get_gallery_image_ids' ? [] : "v-$n"); }
}
class WPDB {
    public $posts = 'wp_posts', $postmeta = 'wp_postmeta';
    function prepare($q, $v) { return $v; }
    function get_col($sku) { global $SKU; return array_keys(array_filter($SKU, function ($s) use ($sku) { return $s === $sku; })); }
}
$wpdb = new WPDB();
function home_url() { return 'http://ahc.local'; }
function wp_parse_url($u, $c) { return parse_url($u, $c); }
function wc_get_product($id) { return new P($id); }
function metadata_exists($t, $id, $k) { global $META; return isset($META[$id][$k]); }
function get_post_meta($id, $k, $s) { global $META; return $META[$id][$k] ?? ''; }
function update_post_meta($id, $k, $v) { global $META; $META[$id][$k] = $v; }
function delete_post_meta($id, $k) { global $META; unset($META[$id][$k]); }
function wp_json_encode($v, $f = 0) { return json_encode($v, $f); }
function wp_slash($v) { return $v; }
function wc_delete_product_transients() {}

$H = "shop_code,market,supplier_product_id,supplier_color_key,colorway_original,swatch_status,position,token_original,display_hex,hex_status\n";
$GOOD = $H
    . "SP,US,1,single,Black/White,CONFIRMED,1,Black,#171717,APPROVED_APPROX\n"
    . "SP,US,1,single,Black/White,CONFIRMED,2,White,#FFFFFF,APPROVED_APPROX\n"
    . "SP,US,2,single,Red,UNKNOWN,1,Red,,NOT_SHOWN\n"
    . "SP,US,3,single,,UNKNOWN,0,,,NO_COMPONENTS\n"
    . "SP,US,9,single,Black,CONFIRMED,1,Black,#171717,APPROVED_APPROX\n";
$tmp = sys_get_temp_dir() . '/ahcw_' . getmypid();
@mkdir($tmp);
function runw($csv, $allow, $extra = []) {
    global $tmp;
    file_put_contents("$tmp/in.csv", $csv);
    file_put_contents("$tmp/allow.txt", implode("\n", $allow) . "\n");
    WP_CLI::$log = [];
    $args = array_merge(["$tmp/in.csv", 'site=ahc.local', "allowlist=$tmp/allow.txt"], $extra);
    try { include __DIR__ . '/../../tools/ahc_color_components_to_woo.php'; return 'OK'; }
    catch (RuntimeException $e) { return 'ERR ' . $e->getMessage(); }
}
$fail = 0;
function check($name, $ok) { global $fail; echo ($ok ? 'PASS ' : 'FAIL ') . "$name\n"; if (!$ok) $fail++; }
function reset_site() { global $META, $SKU, $COLORVAR; $META = []; $SKU = [101 => 'SP-1', 102 => 'SP-2', 103 => 'SP-3']; $COLORVAR = []; }

reset_site();
check('dry run writes nothing', runw($GOOD, [1, 2, 3]) === 'OK' && $META === [] && strpos(end(WP_CLI::$log), '"would_write":3') !== false);
@unlink("$tmp/b1.json");
check('apply', runw($GOOD, [1, 2, 3], ['apply', "backup=$tmp/b1.json"]) === 'OK');
check('confirmed -> __single__ stripes', json_decode($META[101]['_ahc_color_components'], true) === ['__single__' => [['name' => 'Black', 'hex' => '#171717'], ['name' => 'White', 'hex' => '#FFFFFF']]]);
check('context schema 2', json_decode($META[101]['_ahc_color_components_context'], true)['schema_version'] === 2
    && json_decode($META[101]['_ahc_color_components_context'], true)['colorway_original'] === 'Black/White');
check('unknown -> null hex', json_decode($META[102]['_ahc_color_components'], true) === ['__single__' => [['name' => 'Red', 'hex' => null]]]);
check('no components -> explicit empty list', json_decode($META[103]['_ahc_color_components'], true) === ['__single__' => []]);
check('readback 0, guard 0', strpos(end(WP_CLI::$log), '"readback_mismatch":0,"other_fields_changed":0') !== false);
@unlink("$tmp/b2.json");
check('rerun is a no-op', runw($GOOD, [1, 2, 3], ['apply', "backup=$tmp/b2.json"]) === 'OK' && strpos(end(WP_CLI::$log), '"unchanged":3') !== false);
check('rollback restores', runw('', [], ["rollback=$tmp/b1.json"]) !== null && !isset($META[101]['_ahc_color_components']) && !isset($META[103]['_ahc_color_components_context']));

// Negative cases: each must stop with nothing written.
$neg = [
    'not in Local (sku missing)' => [$GOOD, [9]],
    'allowlisted but absent from CSV' => [$GOOD, [1, 7]],
    'position not integer' => [$H . "SP,US,1,single,Black,CONFIRMED,1.0,Black,#171717,APPROVED_APPROX\n", [1]],
    'column count' => [$H . "SP,US,1,single,Black,CONFIRMED,1,Black,#171717\n", [1]],
    'duplicate marker' => [$H . "SP,US,3,single,,UNKNOWN,0,,,NO_COMPONENTS\nSP,US,3,single,,UNKNOWN,0,,,NO_COMPONENTS\n", [3]],
    'marker mixed' => [$H . "SP,US,3,single,Red,UNKNOWN,0,,,NO_COMPONENTS\nSP,US,3,single,Red,UNKNOWN,1,Red,,NOT_SHOWN\n", [3]],
    'non-single key' => [$H . "SP,US,1,c2,Black,CONFIRMED,1,Black,#171717,APPROVED_APPROX\n", [1]],
    'status differs between rows' => [$H . "SP,US,1,single,Black/White,CONFIRMED,1,Black,#171717,APPROVED_APPROX\nSP,US,1,single,Black/White,UNKNOWN,2,White,,NOT_SHOWN\n", [1]],
    'two markets' => [$H . "SP,US,1,single,Black/White,UNKNOWN,1,Black,,NOT_SHOWN\nSP,JP,1,single,Black/White,UNKNOWN,2,White,,NOT_SHOWN\n", [1]],
    'colorway mismatch' => [$H . "SP,US,1,single,Black/Red,UNKNOWN,1,Black,,NOT_SHOWN\nSP,US,1,single,Black/Red,UNKNOWN,2,White,,NOT_SHOWN\n", [1]],
    'other shop' => [$H . "FL,US,1,single,Black,CONFIRMED,1,Black,#171717,APPROVED_APPROX\n", [1]],
    'bad hex' => [$H . "SP,US,1,single,Black,CONFIRMED,1,Black,#17171,APPROVED_APPROX\n", [1]],
    'hex on DRAFT' => [$H . "SP,US,1,single,Black,DRAFT,1,Black,#171717,APPROVED_APPROX\n", [1]],
    'bad status' => [$H . "SP,US,1,single,Black,OK,1,Black,,NOT_SHOWN\n", [1]],
    'gap in positions' => [$H . "SP,US,1,single,Black/White,UNKNOWN,1,Black,,NOT_SHOWN\nSP,US,1,single,Black/White,UNKNOWN,3,White,,NOT_SHOWN\n", [1]],
];
foreach ($neg as $name => [$csv, $allow]) { reset_site(); $r = runw($csv, $allow); check("stop: $name", strpos($r, 'ERR') === 0 && $META === []); }
reset_site(); $SKU[104] = 'SP-1';
check('stop: duplicate SKU', strpos(runw($GOOD, [1]), 'ERR') === 0 && $META === []);
reset_site(); $COLORVAR[101] = true;
check('stop: has color variation (MERGED-like)', strpos(runw($GOOD, [1]), 'ERR') === 0 && $META === []);
reset_site();
check('stop: wrong site', strpos((function () use ($GOOD, $tmp) { file_put_contents("$tmp/in.csv", $GOOD); file_put_contents("$tmp/allow.txt", "1\n");
    $args = ["$tmp/in.csv", 'site=prod.example.com', "allowlist=$tmp/allow.txt"];
    try { include __DIR__ . '/../../tools/ahc_color_components_to_woo.php'; return 'OK'; } catch (RuntimeException $e) { return 'ERR'; } })(), 'ERR') === 0);
reset_site();
check('stop: no allowlist', strpos((function () use ($GOOD, $tmp) { file_put_contents("$tmp/in.csv", $GOOD);
    $args = ["$tmp/in.csv", 'site=ahc.local'];
    try { include __DIR__ . '/../../tools/ahc_color_components_to_woo.php'; return 'OK'; } catch (RuntimeException $e) { return 'ERR'; } })(), 'ERR') === 0);
exit($fail ? 1 : 0);
