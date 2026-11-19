<?php
// Offline harness for tools/ahc_color_components_to_woo.php (no WordPress).
// Run: php qa/php-tests/woo_writer_stub_test.php
define('ABSPATH', '/');
class WP_CLI { static $log = [];
  static function error($m) { throw new Exception($m); }
  static function warning($m) { self::$log[] = "W:$m"; }
  static function log($m) { self::$log[] = $m; } }
$META = [];
class P { function __construct($id) { $this->id = $id; }
  function is_type($t) { return $t === 'variable'; }
  function get_variation_attributes() { return ['pa_color' => ['c' . $this->id]]; } }
function home_url() { return 'http://ahc.local'; }
function wp_parse_url($u, $c) { return parse_url($u, $c); }
function wc_get_product_id_by_sku($s) { return in_array($s, ['SP-1', 'SP-2', 'SP-3'], true) ? (int) substr($s, 3) : 0; }
function wc_get_product($id) { return new P($id); }
function taxonomy_exists($t) { return false; }
function get_post_meta($id, $k, $s) { global $META; return $META[$id] ?? ''; }
function update_post_meta($id, $k, $v) { global $META; $META[$id] = $v; }
function wp_json_encode($v) { return json_encode($v); }
function wp_slash($v) { return $v; }
$csv = tempnam(sys_get_temp_dir(), 'w');
file_put_contents($csv, "shop_code,supplier_product_id,supplier_color_key,position,token_original,display_hex,hex_status\n"
  . "SP,1,single,1,Black,#171717,APPROVED_APPROX\nSP,1,single,2,White,#FFFFFF,APPROVED_APPROX\n"
  . "SP,2,single,1,Red,,NOT_SHOWN\n"
  . "SP,3,single,0,,,NO_COMPONENTS\n"
  . "SP,9,single,1,Black,#171717,APPROVED_APPROX\n");
$fail = 0;
function check($name, $ok) { global $fail; echo ($ok ? 'ok   ' : 'FAIL ') . "$name\n"; if (!$ok) $fail++; }
$args = [$csv, '--apply'];
include __DIR__ . '/../../tools/ahc_color_components_to_woo.php';
check('confirmed stripes', json_decode($META[1], true) === ['c1' => [['name' => 'Black', 'hex' => '#171717'], ['name' => 'White', 'hex' => '#FFFFFF']]]);
check('unconfirmed null hex', json_decode($META[2], true) === ['c2' => [['name' => 'Red', 'hex' => null]]]);
check('no components -> empty list', json_decode($META[3], true) === ['c3' => []]);
check('not found reported', in_array('NOT FOUND  SP-9', WP_CLI::$log, true));
check('stats', strpos(end(WP_CLI::$log), '"written":3') !== false && strpos(end(WP_CLI::$log), 'row_errors=0') !== false);
exit($fail ? 1 : 0);
