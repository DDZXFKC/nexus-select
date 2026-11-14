<?php
/**
 * Plugin Name: kaitsuke tweaks
 * Description: Small presentation tweaks for the kaitsuke-shop theme.
 */
add_filter('woocommerce_dropdown_variation_attribute_options_args', function ($args) {
    $args['show_option_none'] = 'SELECT A SIZE';
    return $args;
});

/*
 * Product image whole-shoe fix (added 2026-11-08).
 *
 * The 'woocommerce_thumbnail' size is generated as a 300x300 hard crop,
 * which cuts off the toe and heel of wide product photos wherever that
 * size is used (shop grid, related products, cart, ...).
 * 1) Serve the proportional 'medium' size in its place. It is already
 *    generated for every attachment and is never cropped.
 * 2) Register future 'woocommerce_thumbnail' generations as uncropped.
 * 3) CSS safety net so loop/block product images are never cover-cropped.
 */
add_filter('image_downsize', function ($downsize, $id, $size) {
    if (! is_string($size) || 'woocommerce_thumbnail' !== $size) {
        return $downsize;
    }
    $candidates = array('medium', 'medium_large');
    foreach ($candidates as $candidate) {
        $intermediate = image_get_intermediate_size($id, $candidate);
        if ($intermediate && ! empty($intermediate['url'])) {
            return array($intermediate['url'], $intermediate['width'], $intermediate['height'], true);
        }
    }
    $meta = wp_get_attachment_metadata($id);
    if ($meta && ! empty($meta['file']) && ! empty($meta['width']) && ! empty($meta['height'])) {
        $uploads = wp_upload_dir();
        return array($uploads['baseurl'] . '/' . $meta['file'], (int) $meta['width'], (int) $meta['height'], false);
    }
    return $downsize;
}, 10, 3);

add_filter('woocommerce_get_image_size_thumbnail', function ($size) {
    if (is_array($size)) {
        $size['crop'] = false;
    }
    return $size;
});

add_action('wp_head', function () {
    echo '<style id="kaitsuke-whole-shoe">.woocommerce ul.products li.product a img,.wc-block-components-product-image img{object-fit:contain;background:#fff}</style>';
}, 20);
