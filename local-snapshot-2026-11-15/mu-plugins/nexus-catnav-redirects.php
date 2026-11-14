<?php
/**
 * Plugin Name: NEXUS Category Navigation Redirects
 * Description: Redirects pre-2026-11-15 two-level product category URLs to the new three-level hierarchy. Slugs are unchanged; only the path gains the group segment.
 */
defined('ABSPATH') || exit;

add_action('template_redirect', function () {
    if (is_admin()) return;
    $path = isset($_SERVER['REQUEST_URI']) ? wp_parse_url(sanitize_text_field(wp_unslash($_SERVER['REQUEST_URI'])), PHP_URL_PATH) : '';
    if (!$path) return;
    // /product-category/{gender}/{leaf}/ -> /product-category/{gender}/{group}/{leaf}/
    if (!preg_match('#^/product-category/(mens|womens|kids)/([a-z0-9\-]+)/?$#', $path, $m)) return;
    $gender = $m[1];
    $leafSlug = $m[2];
    if (strpos($leafSlug, $gender . '-') !== 0) return;
    $leafKey = substr($leafSlug, strlen($gender) + 1);
    $groups = [
        'sneakers' => 'shoes', 'running' => 'shoes', 'basketball' => 'shoes', 'boots' => 'shoes', 'sandals' => 'shoes',
        'tshirt' => 'clothing', 'ls-tshirts' => 'clothing', 'shirts' => 'clothing', 'polo' => 'clothing', 'hoodie' => 'clothing',
        'sweatshirts' => 'clothing', 'knitwear' => 'clothing', 'jacket' => 'clothing', 'pants' => 'clothing', 'jeans' => 'clothing', 'shorts' => 'clothing',
        'cap' => 'headwear', 'beanies' => 'headwear', 'hats' => 'headwear',
        'bag' => 'accessories', 'wallets' => 'accessories', 'jewelry' => 'accessories', 'socks' => 'accessories', 'belts' => 'accessories', 'eyewear' => 'accessories',
    ];
    if (!isset($groups[$leafKey])) return;
    $term = get_term_by('slug', $leafSlug, 'product_cat');
    if (!$term || is_wp_error($term)) return;
    $parent = get_term($term->parent, 'product_cat');
    if (!$parent || is_wp_error($parent) || $parent->slug !== $gender . '-' . $groups[$leafKey]) return; // already migrated check
    $target = get_term_link($term);
    if (is_wp_error($target)) return;
    wp_safe_redirect($target, 301);
    exit;
}, 1);
