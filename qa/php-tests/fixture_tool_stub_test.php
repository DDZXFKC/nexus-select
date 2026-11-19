<?php
// Offline checks for tools/ahc_create_swatch_fixture.php (validation and remove guards) and the
// fixture guard mu-plugin. Run: php qa/php-tests/fixture_tool_stub_test.php
define('ABSPATH', '/');
class WP_CLI { static $log = []; static function error($m) { throw new RuntimeException($m); }
  static function warning($m) { self::$log[] = "W:$m"; } static function log($m) { self::$log[] = $m; } }
$SKUS = ['SP-1' => 10, 'FX-SP-7-2' => 99]; $META = []; $POSTS = [];
class P { function __construct($id) { $this->id = $id; }
  function is_type($t) { return $t === 'variable'; } function get_variation_attributes() { return ['pa_size' => ['9', '10']]; }
  function get_children() { global $POSTS; return $POSTS[$this->id]['kids'] ?? [11, 12]; }
  function get_sku() { global $POSTS; return $POSTS[$this->id]['sku'] ?? 'SP-1'; }
  function get_status() { global $POSTS; return $POSTS[$this->id]['status'] ?? 'publish'; }
  function get_parent_id() { global $POSTS; return $POSTS[$this->id]['parent'] ?? 0; }
  function get_id() { return $this->id; } function get_name() { return 'Shoe (Black)'; } }
class WPDB { public $posts = 'p', $postmeta = 'm'; function prepare($q, $v) { return $v; }
  function get_var($sku) { global $SKUS; return isset($SKUS[$sku]) ? 1 : 0; } }
$wpdb = new WPDB();
function home_url() { return 'http://ahc.local'; } function wp_parse_url($u, $c) { return parse_url($u, $c); }
function wc_get_product_id_by_sku($s) { global $SKUS; return $SKUS[$s] ?? 0; }
function wc_get_product($id) { global $POSTS; return ($id === 10 || isset($POSTS[$id])) ? new P($id) : null; }
function get_post_meta($id, $k, $s) { global $META; return $META[$id][$k] ?? ''; }
function wp_json_encode($v, $f = 0) { return json_encode($v, $f); }
$DELETED = []; function wp_delete_post($id, $f) { global $DELETED, $POSTS; $DELETED[] = $id; unset($POSTS[$id]); }
function get_post($id) { global $POSTS; return $POSTS[$id] ?? null; }
$tmp = sys_get_temp_dir() . '/fx_' . getmypid(); @mkdir($tmp);
function runf($argv) { $args = $argv; WP_CLI::$log = [];
  try { include __DIR__ . '/../../tools/ahc_create_swatch_fixture.php'; return 'OK'; } catch (RuntimeException $e) { return 'ERR ' . $e->getMessage(); } }
$fail = 0; function check($n, $ok) { global $fail; echo ($ok ? 'PASS ' : 'FAIL ') . "$n\n"; if (!$ok) $fail++; }
$H = "supplier_product_id,colorway_original\n";
file_put_contents("$tmp/ok.csv", $H . "5,Chestnut\n6,\n");
check('dry run lists, creates nothing', runf(['create', "fixtures=$tmp/ok.csv", 'template=SP-1', "manifest=$tmp/m0.json", 'site=ahc.local']) === 'OK' && !file_exists("$tmp/m0.json") && strpos(end(WP_CLI::$log), 'fixtures=2') !== false);
file_put_contents("$tmp/dup.csv", $H . "5,A\n5,B\n");
check('stop: duplicate id in CSV', strpos(runf(['create', "fixtures=$tmp/dup.csv", 'template=SP-1', "manifest=$tmp/m1.json", 'site=ahc.local']), 'ERR') === 0);
file_put_contents("$tmp/col.csv", $H . "7,A\n");
check('stop: child SKU collision', strpos(runf(['create', "fixtures=$tmp/col.csv", 'template=SP-1', "manifest=$tmp/m2.json", 'site=ahc.local']), 'ERR') === 0);
file_put_contents("$tmp/real.csv", $H . "1,A\n");
check('stop: real SP SKU exists', strpos(runf(['create', "fixtures=$tmp/real.csv", 'template=SP-1', "manifest=$tmp/m3.json", 'site=ahc.local']), 'ERR') === 0);
check('stop: wrong site', strpos(runf(['create', "fixtures=$tmp/ok.csv", 'template=SP-1', "manifest=$tmp/m4.json", 'site=prod.com']), 'ERR') === 0);
// remove
$POSTS = [200 => ['sku' => 'FX-SP-5', 'status' => 'draft', 'kids' => [201]], 201 => ['sku' => 'FX-SP-5-1', 'parent' => 200], 300 => ['sku' => 'FX-SP-6', 'status' => 'draft', 'kids' => [301]], 301 => ['sku' => 'FX-SP-6-1', 'parent' => 300]];
$META = [200 => ['_ahc_fixture' => '1', '_ahc_fixture_run' => 'r1'], 201 => ['_ahc_fixture' => '1', '_ahc_fixture_run' => 'r1'], 300 => ['_ahc_fixture' => '1', '_ahc_fixture_run' => 'r1'], 301 => ['_ahc_fixture' => '1', '_ahc_fixture_run' => 'r1']];
$man = ['format' => 'ahc-fixture-manifest-v1', 'site' => 'ahc.local', 'run_id' => 'r1', 'parents' => [['id' => 200, 'sku' => 'FX-SP-5', 'children' => [201]], ['id' => 300, 'sku' => 'FX-SP-6', 'children' => [301]]]];
file_put_contents("$tmp/man.json", json_encode($man));
check('remove dry run deletes nothing', runf(['remove', "manifest=$tmp/man.json", 'site=ahc.local']) === 'OK' && $DELETED === []);
$META[301]['_ahc_fixture_run'] = 'other';
check('remove refuses on marker/run mismatch (nothing deleted)', strpos(runf(['remove', "manifest=$tmp/man.json", 'site=ahc.local', 'apply']), 'ERR') === 0 && $DELETED === []);
$META[301]['_ahc_fixture_run'] = 'r1'; $POSTS[300]['status'] = 'publish';
check('remove refuses non-draft', strpos(runf(['remove', "manifest=$tmp/man.json", 'site=ahc.local', 'apply']), 'ERR') === 0 && $DELETED === []);
$POSTS[300]['status'] = 'draft';
check('remove apply deletes only manifest posts', runf(['remove', "manifest=$tmp/man.json", 'site=ahc.local', 'apply']) === 'OK' && $DELETED === [201, 200, 301, 300]);
// guard plugin
$FILTERS = []; function add_filter($h, $f, $p = 10, $n = 1) { global $FILTERS; $FILTERS[$h] = $f; } function add_action($h, $f) {}
function wc_add_notice($m, $t) {}
$META = [500 => ['_ahc_fixture' => '1']]; $POSTS = [500 => ['sku' => 'FX-SP-9'], 501 => ['sku' => 'FX-SP-9-1', 'parent' => 500], 600 => ['sku' => 'SP-3']];
include __DIR__ . '/../../local-snapshot-2026-11-15/mu-plugins/ahc-fixture-guard.php';
check('guard: fixture parent not purchasable', $FILTERS['woocommerce_is_purchasable'](true, new P(500)) === false);
check('guard: fixture variation not purchasable', $FILTERS['woocommerce_variation_is_purchasable'](true, new P(501)) === false);
check('guard: real product unaffected', $FILTERS['woocommerce_is_purchasable'](true, new P(600)) === true);
check('guard: add to cart refused', $FILTERS['woocommerce_add_to_cart_validation'](true, 500, 1, 501) === false);
exit($fail ? 1 : 0);
