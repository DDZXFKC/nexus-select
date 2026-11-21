<?php
/**
 * 商品画像の枠・背景の監査（読み取り専用）。オーナー決定ルール：正方形・白背景・1画面1画像。
 *
 * 実行（XServer、WordPress のルートで）:
 *   wp eval-file /path/to/audit_product_images.php out=$HOME/ahc-image-audit.csv
 * 任意: statuses=publish,private,draft（既定 publish）  limit=50（試し実行）
 *
 * 書き込みは out= に指定した CSV だけ。商品・画像・データベースは一切変更しない。
 *
 * 判定（verdict）:
 *   OK        正方形で、背景が白または透過（サイトの白地にそのまま載る）
 *   PAD       背景は白または透過だが正方形ではない → 白い正方形キャンバスに置くだけで直る（取り込みルールどおり、切り抜き不要）
 *   CUTOUT    背景が白でも透過でもない（ベージュ・グレー・写真背景など）→ 切り抜き、または白背景の公式画像への差し替えが必要
 *   MISSING   画像ファイルがサーバーに無い・読めない
 *   NO_IMAGE  商品にメイン画像が設定されていない
 */

const AHC_IMG_WHITE_MIN = 245;      // 各色がこれ以上なら「白」とみなす（0-255）
const AHC_IMG_TRANSPARENT_MIN = 120; // GD の alpha（0=不透明, 127=完全透明）がこれ以上なら「透過」
const AHC_IMG_BG_SHARE = 0.90;      // 縁の画素のうちこの割合以上が白/透過なら、その背景とみなす
const AHC_IMG_SQUARE_TOL = 0.01;    // 縦横差が長辺の1%以内なら正方形

/** 画像リソースの縁を調べて背景を分類する。テスト用に WordPress から独立させてある。 */
function ahc_img_audit_classify($im) {
    $w = imagesx($im); $h = imagesy($im);
    $pts = [];
    $n = 100; // 各辺のサンプル数
    for ($i = 0; $i < $n; $i++) {
        $x = (int) floor($i * ($w - 1) / max(1, $n - 1));
        $y = (int) floor($i * ($h - 1) / max(1, $n - 1));
        $pts[] = [$x, 0]; $pts[] = [$x, $h - 1]; $pts[] = [0, $y]; $pts[] = [$w - 1, $y];
    }
    $white = 0; $trans = 0; $rs = []; $gs = []; $bs = [];
    foreach ($pts as [$x, $y]) {
        $c = imagecolorsforindex($im, imagecolorat($im, $x, $y));
        if ($c['alpha'] >= AHC_IMG_TRANSPARENT_MIN) { $trans++; continue; }
        if ($c['red'] >= AHC_IMG_WHITE_MIN && $c['green'] >= AHC_IMG_WHITE_MIN && $c['blue'] >= AHC_IMG_WHITE_MIN) $white++;
        $rs[] = $c['red']; $gs[] = $c['green']; $bs[] = $c['blue'];
    }
    $total = count($pts);
    $med = function ($a) { if (!$a) return 255; sort($a); return $a[intdiv(count($a), 2)]; };
    $hex = sprintf('#%02X%02X%02X', $med($rs), $med($gs), $med($bs));
    $tp = $trans / $total; $wp = $white / $total;
    if ($tp >= AHC_IMG_BG_SHARE) $bg = 'TRANSPARENT';
    elseif ($tp + $wp >= AHC_IMG_BG_SHARE) $bg = $tp > 0 ? 'WHITE_OR_TRANSPARENT' : 'WHITE';
    else $bg = 'OTHER';
    $square = abs($w - $h) <= AHC_IMG_SQUARE_TOL * max($w, $h);
    if ($bg === 'OTHER') $verdict = 'CUTOUT';
    elseif (!$square) $verdict = 'PAD';
    else $verdict = 'OK';
    return ['w' => $w, 'h' => $h, 'square' => $square, 'bg' => $bg, 'white_pct' => round($wp * 100, 1),
            'transparent_pct' => round($tp * 100, 1), 'border_hex' => $hex, 'verdict' => $verdict];
}

/** ファイルを読み、分類する。読めなければ MISSING。 */
function ahc_img_audit_file($path) {
    if (!$path || !is_readable($path)) return ['verdict' => 'MISSING', 'note' => 'file not found'];
    $data = @file_get_contents($path);
    $im = $data === false ? false : @imagecreatefromstring($data);
    if (!$im) return ['verdict' => 'MISSING', 'note' => 'unreadable image'];
    $r = ahc_img_audit_classify($im);
    imagedestroy($im);
    return $r;
}

if (!defined('ABSPATH') || defined('AHC_IMG_AUDIT_TEST')) return; // 単体テストでは関数だけ読み込む

// wp eval-file は位置引数をこのファイルのスコープの $args に入れる（key=value 形式で渡す）
$opt = [];
foreach ((isset($args) ? (array) $args : []) as $a) { if (strpos($a, '=') !== false) { [$k, $v] = explode('=', $a, 2); $opt[$k] = $v; } }
$out = $opt['out'] ?? '';
if ($out === '') { fwrite(STDERR, "out=<CSVの出力先> を指定してください（例：out=\$HOME/ahc-image-audit.csv）\n"); return; }
$abspath_real = realpath(ABSPATH);
$out_dir = realpath(dirname($out));
if ($out_dir && $abspath_real && strpos($out_dir, $abspath_real) === 0) { fwrite(STDERR, "公開ディレクトリ（WordPress のルート配下）には出力しません。ホームディレクトリなどを指定してください。\n"); return; }
$statuses = array_filter(explode(',', $opt['statuses'] ?? 'publish'));
$limit = isset($opt['limit']) ? (int) $opt['limit'] : -1;
@ini_set('memory_limit', '1024M');

$ids = get_posts(['post_type' => 'product', 'post_status' => $statuses, 'numberposts' => $limit, 'fields' => 'ids', 'orderby' => 'ID', 'order' => 'ASC']);
$fh = fopen($out, 'w');
if (!$fh) { fwrite(STDERR, "CSV を開けません: $out\n"); return; }
fputcsv($fh, ['product_id', 'status', 'sku', 'name', 'role', 'attachment_id', 'file', 'mime', 'w', 'h', 'square', 'bg', 'white_pct', 'transparent_pct', 'border_hex', 'verdict', 'note', 'product_url']);
$cache = []; $count = []; $prod_bad = [];
foreach ($ids as $pid) {
    $p = wc_get_product($pid);
    if (!$p) continue;
    $rows = [];
    $main = (int) $p->get_image_id();
    if (!$main) $rows[] = ['main', 0];
    else $rows[] = ['main', $main];
    foreach ($p->get_gallery_image_ids() as $g) $rows[] = ['gallery', (int) $g];
    if ($p->is_type('variable')) {
        foreach ($p->get_children() as $vid) { $v = wc_get_product($vid); if ($v && $v->get_image_id() && $v->get_image_id() != $main) $rows[] = ['variation', (int) $v->get_image_id()]; }
    }
    $seen = [];
    foreach ($rows as [$role, $aid]) {
        if ($aid && isset($seen[$aid])) continue;
        $seen[$aid] = 1;
        if (!$aid) { $r = ['verdict' => 'NO_IMAGE', 'note' => 'no main image']; $file = ''; $mime = ''; }
        else {
            $file = get_attached_file($aid);
            $mime = get_post_mime_type($aid);
            if (!isset($cache[$aid])) $cache[$aid] = ahc_img_audit_file($file);
            $r = $cache[$aid];
        }
        $count[$r['verdict']] = ($count[$r['verdict']] ?? 0) + 1;
        if ($r['verdict'] !== 'OK') $prod_bad[$pid] = 1;
        fputcsv($fh, [$pid, get_post_status($pid), $p->get_sku(), $p->get_name(), $role, $aid, $file ? basename($file) : '', $mime,
            $r['w'] ?? '', $r['h'] ?? '', isset($r['square']) ? ($r['square'] ? 1 : 0) : '', $r['bg'] ?? '', $r['white_pct'] ?? '',
            $r['transparent_pct'] ?? '', $r['border_hex'] ?? '', $r['verdict'], $r['note'] ?? '', get_permalink($pid)]);
    }
}
fclose($fh);
ksort($count);
echo 'products=' . count($ids) . ' products_with_issue=' . count($prod_bad) . ' images_checked=' . count($cache) . "\n";
foreach ($count as $k => $v) echo "$k=$v\n";
echo "csv=$out\n";
