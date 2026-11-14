<?php
/**
 * AHC QA: read-only data export for the quality inspection system.
 *
 * Run with WP-CLI (MySQL socket must be specified, see qa/README.md):
 *   wp eval-file qa/export/ahc_export.php /path/to/output.json --path="<Local site>/app/public"
 *
 * This script only READS. It never writes to the database.
 * It exports products, variations, categories and image metadata.
 * It does NOT export customers, orders, addresses, emails or any user data.
 */
if (!defined('ABSPATH')) { fwrite(STDERR, "Run via wp eval-file\n"); exit(1); }

$out = isset($args[0]) ? $args[0] : '';
if ($out === '') { WP_CLI::error('Output path is required: wp eval-file ahc_export.php /path/to/output.json'); }

$uploads = wp_get_upload_dir();
$image_cache = [];
$image_info = function ($id) use (&$image_cache, $uploads) {
    $id = (int) $id;
    if (!$id) return null;
    if (isset($image_cache[$id])) return $id;
    $file = get_attached_file($id);
    $meta = wp_get_attachment_metadata($id);
    $sizes = [];
    if (is_array($meta) && !empty($meta['sizes']) && $file) {
        $dir = dirname($file);
        foreach ($meta['sizes'] as $name => $s) {
            $p = $dir . '/' . $s['file'];
            $sizes[$name] = ['file' => $p, 'exists' => file_exists($p), 'width' => (int) $s['width'], 'height' => (int) $s['height']];
        }
    }
    $image_cache[$id] = [
        'id' => $id,
        'url' => wp_get_attachment_url($id),
        'file' => $file ?: '',
        'exists' => $file ? file_exists($file) : false,
        'mime' => get_post_mime_type($id),
        'width' => is_array($meta) && isset($meta['width']) ? (int) $meta['width'] : 0,
        'height' => is_array($meta) && isset($meta['height']) ? (int) $meta['height'] : 0,
        'sizes' => $sizes,
    ];
    return $id;
};

$terms = get_terms(['taxonomy' => 'product_cat', 'hide_empty' => false]);
$categories = [];
foreach ($terms as $t) {
    $link = get_term_link($t);
    $categories[] = [
        'id' => (int) $t->term_id,
        'name' => $t->name,
        'slug' => $t->slug,
        'parent' => (int) $t->parent,
        'count' => (int) $t->count,
        'link' => is_wp_error($link) ? '' : $link,
    ];
}

$ids = wc_get_products(['status' => 'publish', 'limit' => -1, 'return' => 'ids', 'type' => array_keys(wc_get_product_types())]);
$products = [];
foreach ($ids as $pid) {
    $p = wc_get_product($pid);
    if (!$p) continue;
    $brands = [];
    if (taxonomy_exists('pa_brand')) {
        $bt = wp_get_post_terms($pid, 'pa_brand', ['fields' => 'names']);
        if (!is_wp_error($bt)) $brands = array_values($bt);
    }
    $img = $image_info($p->get_image_id());
    $gallery = [];
    foreach ($p->get_gallery_image_ids() as $gid) { $g = $image_info($gid); if ($g) $gallery[] = $g; }
    $variations = [];
    if ($p->is_type('variable')) {
        foreach ($p->get_children() as $vid) {
            $v = wc_get_product($vid);
            if (!$v) continue;
            $variations[] = [
                'id' => (int) $vid,
                'status' => $v->get_status(),
                'sku' => $v->get_sku(),
                'price' => $v->get_price(),
                'regular_price' => $v->get_regular_price(),
                'sale_price' => $v->get_sale_price(),
                'attributes' => $v->get_attributes(),
                'stock_status' => $v->get_stock_status(),
                'purchasable' => $v->is_purchasable(),
                'image_id' => $image_info($v->get_image_id()),
            ];
        }
    }
    $attrs = [];
    foreach ($p->get_attributes() as $name => $a) {
        $attrs[$name] = is_object($a) && method_exists($a, 'is_taxonomy') && $a->is_taxonomy()
            ? wc_get_product_terms($pid, $name, ['fields' => 'names'])
            : (is_object($a) && method_exists($a, 'get_options') ? $a->get_options() : $a);
    }
    $products[] = [
        'id' => (int) $pid,
        'name' => $p->get_name(),
        'slug' => $p->get_slug(),
        'type' => $p->get_type(),
        'status' => $p->get_status(),
        'visibility' => $p->get_catalog_visibility(),
        'sku' => $p->get_sku(),
        'price' => $p->get_price(),
        'regular_price' => $p->get_regular_price(),
        'sale_price' => $p->get_sale_price(),
        'description_length' => mb_strlen(wp_strip_all_tags($p->get_description())),
        'short_description_length' => mb_strlen(wp_strip_all_tags($p->get_short_description())),
        'category_ids' => array_map('intval', $p->get_category_ids()),
        'brands' => $brands,
        'attributes' => $attrs,
        'image_id' => $img,
        'gallery_ids' => $gallery,
        'permalink' => get_permalink($pid),
        'stock_status' => $p->get_stock_status(),
        'purchasable' => $p->is_purchasable(),
        'variations' => $variations,
    ];
}

$data = [
    'exported_at' => gmdate('c'),
    'site' => [
        'blogname' => get_option('blogname'),
        'blogdescription' => get_option('blogdescription'),
        'home_url' => home_url('/'),
        'currency' => get_woocommerce_currency(),
        'theme' => get_stylesheet(),
        'theme_mods' => [
            'nexus_pc_hero_image' => (int) get_theme_mod('nexus_pc_hero_image', 0),
            'nexus_pc_hero_video' => (int) get_theme_mod('nexus_pc_hero_video', 0),
        ],
    ],
    'categories' => $categories,
    'products' => $products,
    'images' => array_values($image_cache),
];

$json = wp_json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
if (file_put_contents($out, $json) === false) { WP_CLI::error("Could not write $out"); }
WP_CLI::success(sprintf('Exported %d products, %d categories, %d images to %s', count($products), count($categories), count($image_cache), $out));
