<?php
// Offline test for tools/audit_product_images.php. Run: php qa/php-tests/image_audit_test.php
$dir = sys_get_temp_dir() . '/ahc-img-audit-test'; @mkdir($dir);
function mk($path, $w, $h, $bg, $alpha = false, $fmt = 'png') {
    $im = imagecreatetruecolor($w, $h);
    if ($alpha) { imagesavealpha($im, true); imagealphablending($im, false); $c = imagecolorallocatealpha($im, 0, 0, 0, 127); }
    else $c = imagecolorallocate($im, ...$bg);
    imagefilledrectangle($im, 0, 0, $w - 1, $h - 1, $c);
    $shoe = imagecolorallocate($im, 30, 30, 30); // 中央に「商品」
    imagefilledrectangle($im, (int) ($w * .3), (int) ($h * .3), (int) ($w * .7), (int) ($h * .7), $shoe);
    $fmt === 'jpg' ? imagejpeg($im, $path, 90) : imagepng($im, $path);
}
mk("$dir/sq_white.jpg", 800, 800, [255, 255, 255], false, 'jpg');
mk("$dir/land_beige.jpg", 1200, 800, [233, 223, 205], false, 'jpg');
mk("$dir/land_white.png", 1200, 800, [255, 255, 255]);
mk("$dir/land_trans.png", 1200, 800, null, true);
mk("$dir/sq_trans.png", 900, 900, null, true);
mk("$dir/sq_beige.jpg", 800, 800, [233, 223, 205], false, 'jpg');
mk("$dir/sq_offwhite.jpg", 800, 800, [250, 250, 248], false, 'jpg');
mk("$dir/sq_lightgrey.jpg", 800, 800, [235, 235, 235], false, 'jpg');

// --- part 1: classifier on files
define('AHC_IMG_AUDIT_TEST', 1); define('ABSPATH', '/nonexistent-wp/');
require __DIR__ . '/../../tools/audit_product_images.php';
$fail = 0; function check($n, $ok) { global $fail; echo ($ok ? 'PASS ' : 'FAIL ') . "$n\n"; if (!$ok) $fail++; }
$v = fn($f) => ahc_img_audit_file("$dir/$f");
check('square white jpg -> OK', $v('sq_white.jpg')['verdict'] === 'OK');
$r = $v('land_beige.jpg');
check('landscape beige -> CUTOUT (bg OTHER, not square)', $r['verdict'] === 'CUTOUT' && $r['bg'] === 'OTHER' && !$r['square'] && $r['w'] === 1200);
check('beige border colour reported', in_array(substr($r['border_hex'], 0, 3), ['#E9', '#E8', '#EA'], true));
check('landscape white png -> PAD', $v('land_white.png')['verdict'] === 'PAD');
$r = $v('land_trans.png');
check('landscape transparent png -> PAD (bg TRANSPARENT)', $r['verdict'] === 'PAD' && $r['bg'] === 'TRANSPARENT');
check('square transparent png -> OK', $v('sq_trans.png')['verdict'] === 'OK');
check('square beige -> CUTOUT', $v('sq_beige.jpg')['verdict'] === 'CUTOUT');
check('square off-white (250,250,248) -> OK', $v('sq_offwhite.jpg')['verdict'] === 'OK');
check('square light grey (235) -> CUTOUT', $v('sq_lightgrey.jpg')['verdict'] === 'CUTOUT');
check('missing file -> MISSING', $v('nope.jpg')['verdict'] === 'MISSING');
file_put_contents("$dir/broken.jpg", 'not an image');
check('broken file -> MISSING', $v('broken.jpg')['verdict'] === 'MISSING');

// --- part 2: whole script with stubbed WordPress (separate process so ABSPATH etc. are clean)
$stub = <<<'PHP'
<?php
define('ABSPATH', '/nonexistent-wp/');
$D = getenv('IMGDIR');
class P { function __construct($id, $type, $main, $gal, $children = [], $sku = '') { foreach (get_defined_vars() as $k => $v) $this->$k = $v; }
  function get_image_id() { return $this->main; } function get_gallery_image_ids() { return $this->gal; } function is_type($t) { return $this->type === $t; }
  function get_children() { return $this->children; } function get_sku() { return $this->sku; } function get_name() { return 'Product ' . $this->id; } }
$PRODUCTS = [1 => new P(1, 'simple', 11, [12], [], 'SP-1'), 2 => new P(2, 'variable', 13, [], [21, 22], 'SP-2'), 3 => new P(3, 'simple', 0, []), 21 => new P(21, 'variation', 14, []), 22 => new P(22, 'variation', 13, [])];
$FILES = [11 => 'sq_white.jpg', 12 => 'land_beige.jpg', 13 => 'land_trans.png', 14 => 'nope.jpg'];
function get_posts($a) { $GLOBALS['Q'] = $a; return [1, 2, 3]; }
function wc_get_product($id) { return $GLOBALS['PRODUCTS'][$id] ?? null; }
function get_attached_file($id) { return getenv('IMGDIR') . '/' . $GLOBALS['FILES'][$id]; }
function get_post_mime_type($id) { return 'image/x'; }
function get_post_status($id) { return 'publish'; }
function get_permalink($id) { return "https://example.test/p/$id"; }
$args = ['out=' . $D . '/out.csv', 'statuses=publish,private'];
include getenv('SCRIPT');
echo "STATUSES=" . implode(',', $GLOBALS['Q']['post_status']) . "\n";
PHP;
file_put_contents("$dir/run.php", $stub);
$cmd = 'IMGDIR=' . escapeshellarg($dir) . ' SCRIPT=' . escapeshellarg(realpath(__DIR__ . '/../../tools/audit_product_images.php')) . ' php ' . escapeshellarg("$dir/run.php");
$o = shell_exec($cmd);
$rows = array_map('str_getcsv', file("$dir/out.csv", FILE_IGNORE_NEW_LINES));
$hdr = array_shift($rows);
$by = []; foreach ($rows as $r) { $a = array_combine($hdr, $r); $by[$a['product_id'] . ':' . $a['role'] . ':' . $a['attachment_id']] = $a; }
check('summary counts printed', strpos($o, 'products=3') !== false && strpos($o, 'products_with_issue=3') !== false);
check('statuses argument passed', strpos($o, 'STATUSES=publish,private') !== false);
check('main square white OK', ($by['1:main:11']['verdict'] ?? '') === 'OK');
check('gallery beige CUTOUT', ($by['1:gallery:12']['verdict'] ?? '') === 'CUTOUT');
check('variable main transparent landscape PAD', ($by['2:main:13']['verdict'] ?? '') === 'PAD');
check('variation image missing file MISSING', ($by['2:variation:14']['verdict'] ?? '') === 'MISSING');
check('variation reusing main image not duplicated', !isset($by['2:variation:13']));
check('product without main image NO_IMAGE', ($by['3:main:0']['verdict'] ?? '') === 'NO_IMAGE');
check('product url column present', ($by['1:main:11']['product_url'] ?? '') === 'https://example.test/p/1');
// refuses to write into the WordPress root
$stub2 = str_replace("define('ABSPATH', '/nonexistent-wp/');", "define('ABSPATH', getenv('IMGDIR') . '/');", $stub);
file_put_contents("$dir/run2.php", $stub2); @unlink("$dir/out.csv");
$o2 = shell_exec(str_replace('run.php', 'run2.php', $cmd) . ' 2>&1');
check('refuses output inside WordPress root', strpos($o2, '公開ディレクトリ') !== false && !file_exists("$dir/out.csv"));
exit($fail ? 1 : 0);
