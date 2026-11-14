<?php
/**
 * Plugin Name: NEXUS Category Navigation Auto-Classify
 * Description: After WooCommerce has finished saving a product (admin, REST API, WP-CLI or CRUD),
 * completes the category hierarchy (gender root + group + leaf) and adds usage facets
 * (Running / Basketball / Boots) only when the model-name rule table matches clearly.
 * Unclear usage is left as Sneakers only and flagged for review; it never blocks publishing.
 *
 * 2026-11-15 rev2:
 * - Runs on woocommerce_new_product / woocommerce_update_product (after WooCommerce has written
 *   the product's categories). save_post_product fired before categories were stored for
 *   products created through the REST API / CRUD, so new products were not classified.
 * - Boots are decided by boot model words, not by the brand name (Timberland also sells non-boots).
 * - Facets this plugin added itself are removed again when the rule no longer matches.
 *   Categories set by a person are never removed.
 * - Gender is also taken from a gendered leaf/group slug (mens-sneakers -> mens).
 * - Products that cannot be classified are marked with _nx_catnav_needs_review (reason text).
 */
defined('ABSPATH') || exit;

function nx_catnav_rule_table() {
    return [
        'leaf_group' => [
            'sneakers' => 'shoes', 'running' => 'shoes', 'basketball' => 'shoes', 'boots' => 'shoes', 'sandals' => 'shoes',
            'tshirt' => 'clothing', 'ls-tshirts' => 'clothing', 'shirts' => 'clothing', 'polo' => 'clothing', 'hoodie' => 'clothing',
            'sweatshirts' => 'clothing', 'knitwear' => 'clothing', 'jacket' => 'clothing', 'pants' => 'clothing', 'jeans' => 'clothing', 'shorts' => 'clothing',
            'cap' => 'headwear', 'beanies' => 'headwear', 'hats' => 'headwear',
            'bag' => 'accessories', 'wallets' => 'accessories', 'jewelry' => 'accessories', 'socks' => 'accessories', 'belts' => 'accessories', 'eyewear' => 'accessories',
        ],
        // Usage facets: matched against the product name (model names / boot words only, never a brand alone).
        'facets' => [
            'running' => '/Novablast|Gel-Nimbus|GEL-Nimbus|Gel-Cumulus 2[78]|GEL-Cumulus 2[78]|Gel-Kayano 33|GEL-Kayano 33|GT-1000|GT-2000 15|Gel-Contend|Gel-Pulse|DynaBlast|DS Trainer|Trabuco|Vomero 18/i',
            'basketball' => '/Air Jordan|(^|\s)J Balvin.*Jordan|Jordan AJ|Jordan Son of Mars|Jordan 6 Rings|Jordan Spizike|Jordan Retro|Kobe|Ja \d|Nike Ja|\bKD ?6\b|Harden|Caitlin|A[\'\’]Two|G\.T\. Cut|Anthony Edwards|Way of Wade|Huarache 2K4|Foamposite|Ewing/i',
            'boots' => '/\bBoots?\b|6[- ]?Inch|\bChukka\b|Goadome|Field Boot|Euro Hiker|\bBotas?\b|ブーツ/iu',
        ],
        // Lifestyle icons: never auto-assigned a usage facet even if a pattern matches.
        'facet_exclude' => '/Air Force|AF1|\bDunk\b/i',
    ];
}

/**
 * Pure classification step (no WordPress calls), so it can be tested on its own.
 *
 * @param string[] $slugs          current product_cat slugs
 * @param string   $title          product name
 * @param string[] $previous_auto  facet slugs this plugin added on an earlier run
 * @return array{add:string[], remove:string[], auto:string[], review:string}
 */
function nx_catnav_classify(array $slugs, $title, array $previous_auto = []) {
    $rules = nx_catnav_rule_table();
    // Gender comes from the root, or from a gendered group/leaf slug such as "mens-sneakers".
    $genders = [];
    foreach (['mens', 'womens', 'kids'] as $g) {
        foreach ($slugs as $s) {
            if ($s === $g || strpos($s, $g . '-') === 0) { $genders[] = $g; break; }
        }
    }
    if (!$genders) {
        return ['add' => [], 'remove' => [], 'auto' => [], 'review' => 'gender-missing'];
    }
    $add = [];
    $auto = [];
    $review = '';
    // Facets the plugin added before but which no longer match may be removed again (only those).
    $remove_candidates = array_values(array_intersect($previous_auto, $slugs));
    foreach ($genders as $g) {
        $has_leaf = false;
        foreach ($slugs as $s) {
            if (strpos($s, $g . '-') !== 0) continue;
            $leaf = substr($s, strlen($g) + 1);
            if (isset($rules['leaf_group'][$leaf])) {
                $has_leaf = true;
                $add[] = $g . '-' . $rules['leaf_group'][$leaf];
            }
        }
        if (!$has_leaf) $review = 'leaf-missing';
        if (in_array($g . '-sneakers', $slugs, true) || in_array($g . '-boots', $slugs, true)) {
            if (!preg_match($rules['facet_exclude'], $title)) {
                foreach ($rules['facets'] as $facet => $pattern) {
                    if (preg_match($pattern, $title)) {
                        $auto[] = $g . '-' . $facet;
                        $add[] = $g . '-' . $facet;
                        $add[] = $g . '-shoes';
                        break;
                    }
                }
            }
        }
        $add[] = $g; // gender root stays assigned (header menu counts rely on it)
    }
    $auto = array_values(array_unique($auto));
    // Keep a previously auto-added facet if it still matches; otherwise remove it.
    $remove = array_values(array_diff($remove_candidates, $auto));
    // A product must keep at least one leaf: never remove the last one.
    $remaining = array_diff(array_merge($slugs, $add), $remove);
    foreach ($genders as $g) {
        $left = array_filter($remaining, function ($s) use ($g, $rules) {
            return strpos($s, $g . '-') === 0 && isset($rules['leaf_group'][substr($s, strlen($g) + 1)]);
        });
        if (!$left) {
            $remove = array_values(array_filter($remove, function ($s) use ($g) { return strpos($s, $g . '-') !== 0; }));
        }
    }
    return [
        'add' => array_values(array_unique(array_diff($add, $slugs))),
        'remove' => $remove,
        // Remember facets added now plus earlier auto facets that are still kept.
        'auto' => array_values(array_unique(array_merge($auto, array_diff(array_intersect($previous_auto, $slugs), $remove)))),
        'review' => $review,
    ];
}

function nx_catnav_autoclassify($product_id) {
    static $nx_running = false;
    if ($nx_running) return;
    if (wp_is_post_revision($product_id) || get_post_type($product_id) !== 'product') return;
    $slugs = wp_get_post_terms($product_id, 'product_cat', ['fields' => 'slugs']);
    if (is_wp_error($slugs)) return;
    $previous = get_post_meta($product_id, '_nx_catnav_auto', true);
    $previous = is_array($previous) ? $previous : [];
    $r = nx_catnav_classify((array) $slugs, get_the_title($product_id), $previous);

    $nx_running = true;
    if ($r['add']) {
        $ids = [];
        foreach ($r['add'] as $s) {
            $t = get_term_by('slug', $s, 'product_cat');
            if ($t && !is_wp_error($t)) $ids[] = (int) $t->term_id;
        }
        if ($ids) wp_set_object_terms($product_id, $ids, 'product_cat', true);
    }
    if ($r['remove']) {
        $ids = [];
        foreach ($r['remove'] as $s) {
            $t = get_term_by('slug', $s, 'product_cat');
            if ($t && !is_wp_error($t)) $ids[] = (int) $t->term_id;
        }
        if ($ids) wp_remove_object_terms($product_id, $ids, 'product_cat');
    }
    $nx_running = false;

    if ($r['auto']) update_post_meta($product_id, '_nx_catnav_auto', $r['auto']);
    else delete_post_meta($product_id, '_nx_catnav_auto');
    if ($r['review']) update_post_meta($product_id, '_nx_catnav_needs_review', $r['review']);
    else delete_post_meta($product_id, '_nx_catnav_needs_review');
    if (($r['add'] || $r['remove']) && function_exists('wc_delete_product_transients')) wc_delete_product_transients($product_id);
}

// Fired by WooCommerce's product data store AFTER categories are written: admin edit, quick edit,
// REST API, WP-CLI (wc product create/update) and $product->save() all pass through these.
add_action('woocommerce_new_product', 'nx_catnav_autoclassify', 20, 1);
add_action('woocommerce_update_product', 'nx_catnav_autoclassify', 20, 1);
