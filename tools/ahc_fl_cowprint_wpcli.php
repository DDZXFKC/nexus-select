<?php
/**
 * WP-CLI one-shot image replacement for Nike Air Force 1 '07 Cow Print.
 * Exact Woo SKU FL-O0442200 / manufacturer style IO0442-200.
 *
 * This file is NEVER auto-loaded. It must be required explicitly by WP-CLI.
 * Dry-run:
 *   wp --require=tools/ahc_fl_cowprint_wpcli.php ahc images cowprint --source-dir=/private/staged
 * Commit:
 *   wp --require=tools/ahc_fl_cowprint_wpcli.php ahc images cowprint --source-dir=/private/staged --execute
 *
 * No unrelated Woo product, SKU, order, or variation attribute is changed.
 * Requires AHC_IMAGE_BACKUP_DIR (private, outside webroot) for --execute.
 */
if (!defined('WP_CLI') || !WP_CLI || !class_exists('WP_CLI')) return;
WP_CLI::add_command('ahc images cowprint', function ($positional, $assoc) {
    $style = 'IO0442-200';
    $woo_sku = 'FL-O0442200';
    $ids = ['O0442200_01','O0442200_03','O0442200_04'];
    $expected = [
        'O0442200_01'=>'5e71bbd25b84e123708e537b41aedd9403aff1cc09d0660f3dfa1b6a794a7ba4',
        'O0442200_03'=>'db096d01e1d94f2a78f5c22906c626cb90dcbca8520789d51a61e84031a838c5',
        'O0442200_04'=>'eb2304bbe0321e23cebbb4a6fab02d530b52ae945acc5dd1d5529c31e7e2b814',
    ];
    if (!function_exists('wc_get_product_id_by_sku') || !function_exists('wc_get_product')) {
        WP_CLI::error('WooCommerce is not loaded'); return;
    }
    $product_id = (int) wc_get_product_id_by_sku($woo_sku);
    $product = $product_id ? wc_get_product($product_id) : false;
    if (!$product || (string)$product->get_sku() !== $woo_sku ||
        !($product->is_type('variable') || $product->is_type('simple')) ||
        stripos($product->get_name(), 'Air Force') === false ||
        stripos($product->get_name(), 'Cow') === false) {
        WP_CLI::error('Exact product identity not confirmed. No changes made.'); return;
    }

    if (get_post_meta($product_id,'_ahc_cowprint_20261122_repaired',true)) {
        WP_CLI::error('Already repaired; do not import duplicate media or overwrite the prior rollback record');
        return;
    }
    $source_dir = isset($assoc['source-dir']) ? realpath($assoc['source-dir']) : false;
    if (!$source_dir || !is_dir($source_dir)) {
        WP_CLI::error('Missing non-public input folder. No changes.'); return;
    }
    $images = [];
    foreach ($ids as $stem) {
        $path = $source_dir . '/' . $stem . '-white-square.png';
        $content_sha = is_file($path) && is_readable($path) ? hash_file('sha256',$path) : '';
        if (!hash_equals($expected[$stem], (string)$content_sha)) {
            WP_CLI::error('Unverified image source for '.$stem.'. No changes.'); return;
        }
        $size = getimagesize($path);
        if (!$size || $size[0] !== $size[1] || $size['mime'] !== 'image/png') {
            WP_CLI::error('Image must be a valid square PNG: '.$stem); return;
        }
        $images[] = ['stem'=>$stem,'path'=>$path,'width'=>$size[0],'sha256'=>$content_sha];
    }

    $old_main = (int)$product->get_image_id();
    $old_gallery = array_map('intval', $product->get_gallery_image_ids());
    $old_all = array_unique(array_merge([$old_main],$old_gallery));
    $old_variations = [];
    if ($product->is_type('variable')) {
        foreach ($product->get_children() as $vid) {
            $variation = wc_get_product($vid);
            if (!$variation || !$variation->is_type('variation') ||
                (int)$variation->get_parent_id()!==$product_id) {
                WP_CLI::error('Variation ownership invalid; abort without changing gallery'); return;
            }
            $old_variations[(string)$vid] = (int)$variation->get_image_id();
        }
    }
    $backup = [
        'product_id'=>$product_id,'product_sku'=>$woo_sku,'manufacturer_style'=>$style,
        'previous_featured_id'=>$old_main,'previous_gallery_ids'=>$old_gallery,
        'previous_variation_image_ids'=>$old_variations,
        'source_images'=>$images,'created_at'=>gmdate('c')
    ];
    WP_CLI::log('Validated exact product ID '.$product_id.', '.count($images).' verified white-square PNG images.');
    WP_CLI::log('Original feature: '.$old_main.', original gallery entries: '.count($old_gallery));
    WP_CLI::log('Source dimensions: '.implode(', ', array_map(
        static function($v){return $v['stem'].' '.$v['width'].'px';}, $images)));
    if (!isset($assoc['execute'])) {
        WP_CLI::log('DRY RUN: neither WordPress media nor images changed.');
        return;
    }
    $dir = getenv('AHC_IMAGE_BACKUP_DIR');
    $dir = is_string($dir) ? realpath($dir) : false;
    if (!$dir || !is_dir($dir) || !is_writable($dir)
        || strpos($dir, realpath(ABSPATH . '/wp-content') ?: ABSPATH . '/wp-content')===0) {
        WP_CLI::error('Private backup directory outside wp-content required. No changes.'); return;
    }
    $backup_file = $dir.'/ahc-fl-cowprint-'.$product_id.'-'.gmdate('YmdHis').'.json';
    if (file_put_contents($backup_file,wp_json_encode($backup,JSON_PRETTY_PRINT))===false) {
        WP_CLI::error('Failed to save rollback file; no changes.'); return;
    }
    chmod($backup_file,0600);
    require_once ABSPATH.'wp-admin/includes/file.php';
    require_once ABSPATH.'wp-admin/includes/image.php';
    require_once ABSPATH.'wp-admin/includes/media.php';
    $new_ids=[];
    foreach ($images as $source) {
        $temp = wp_tempnam($source['stem'].'.png');
        if (!$temp || !copy($source['path'],$temp)) {
            WP_CLI::error('Temporary media copy failed; original product unchanged'); return;
        }
        $file=[
            // Keep the _01/_03/_04 suffix as the LAST part of each filename.
            // The live color-gallery filter groups files by the common stem
            // and a terminal _number; '-white-square' would break that logic.
            'name'=>'ahccow-20261122-'.$source['stem'].'.png',
            'tmp_name'=>$temp,
            'type'=>'image/png',
            'size'=>filesize($temp),
            'error'=>0,
        ];
        $attachment=media_handle_sideload($file,$product_id,
            'Foot Locker original '.$source['stem'].' / '.$style);
        if (is_wp_error($attachment)) {
            @unlink($temp);
            WP_CLI::error('Media upload failed; original gallery unchanged: '.$attachment->get_error_message());
            return;
        }
        update_post_meta($attachment,'_wp_attachment_image_alt',
            "Nike Air Force 1 '07 Cow Print ".$style.' '.$source['stem']);
        $new_ids[]=(int)$attachment;
    }
    // Change Woo gallery only when all three new attachments are present.
    $product->set_image_id($new_ids[0]);
    $product->set_gallery_image_ids(array_slice($new_ids,1));
    $product->save();
    $modified=[];
    foreach ($old_variations as $vid=>$old_thumb) {
        // Protect variation-specific imagery which was not part of the
        // formerly damaged main/gallery set.
        if ($old_thumb===0 || in_array($old_thumb,$old_all,true)) {
            $variation=wc_get_product((int)$vid);
            $variation->set_image_id($new_ids[0]);
            $variation->save();
            $modified[]=(int)$vid;
        }
    }
    update_post_meta($product_id,'_ahc_cowprint_20261122_repaired',implode(',', $new_ids));
    $backup['new_attachment_ids']=$new_ids;
    $backup['updated_variation_ids']=$modified;
    file_put_contents($backup_file, wp_json_encode($backup,JSON_PRETTY_PRINT));
    WP_CLI::success('Image replacement complete. IDs: '.implode(',',$new_ids).
        '. Keep private rollback backup: '.$backup_file);
});
