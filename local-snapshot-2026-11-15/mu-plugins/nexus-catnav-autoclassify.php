<?php
/**
 * Plugin Name: NEXUS Category Navigation Auto-Classify
 * Description: On product save, completes the category hierarchy (gender root + group + leaf)
 * and adds usage facets (Running / Basketball / Boots / Sandals & Slides) only when the
 * model-name rule table matches clearly. Unclear usage is left as Sneakers only
 * (needs-check) and never blocks publishing. Same rule table as the 2026-11-15 migration.
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
        // Usage facets: matched against the product title (model names only).
        'facets' => [
            'running' => '/Novablast|Gel-Nimbus|GEL-Nimbus|Gel-Cumulus 2[78]|GEL-Cumulus 2[78]|Gel-Kayano 33|GEL-Kayano 33|GT-1000|GT-2000 15|Gel-Contend|Gel-Pulse|DynaBlast|DS Trainer|Trabuco|Vomero 18/i',
            'basketball' => '/Air Jordan|(^|\s)J Balvin.*Jordan|Jordan AJ|Jordan Son of Mars|Jordan 6 Rings|Jordan Spizike|Jordan Retro|Kobe|Ja \d|Nike Ja|\bKD ?6\b|Harden|Caitlin|A[\'\’]Two|G\.T\. Cut|Anthony Edwards|Way of Wade|Huarache 2K4|Foamposite|Ewing/i',
            'boots' => '/Timberland|Goadome/i',
        ],
        // Lifestyle icons: never auto-assigned a usage facet even if a pattern matches.
        'facet_exclude' => '/Air Force|AF1/i',
    ];
}

add_action('save_post_product', function ($post_id, $post, $update) {
    if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) return;
    if (wp_is_post_revision($post_id)) return;
    static $nx_running = false;
    if ($nx_running) return;
    $rules = nx_catnav_rule_table();
    $slugs = wp_get_post_terms($post_id, 'product_cat', ['fields' => 'slugs']);
    if (!$slugs || is_wp_error($slugs)) return;
    $genders = array_values(array_intersect(['mens', 'womens', 'kids'], $slugs));
    if (!$genders) return; // gender is a required classification: leave to the operator
    $add = [];
    foreach ($genders as $g) {
        foreach ($slugs as $s) {
            if (strpos($s, $g . '-') !== 0) continue;
            $leaf = substr($s, strlen($g) + 1);
            if (isset($rules['leaf_group'][$leaf])) $add[] = $g . '-' . $rules['leaf_group'][$leaf];
        }
        // Usage facets apply to shoe products of this gender.
        if (in_array($g . '-' . 'sneakers', $slugs, true)) {
            $title = get_the_title($post_id);
            if (!preg_match($rules['facet_exclude'], $title)) {
                foreach ($rules['facets'] as $facet => $pattern) {
                    if (preg_match($pattern, $title)) { $add[] = $g . '-' . $facet; $add[] = $g . '-shoes'; break; }
                }
            }
        }
        $add[] = $g; // gender root stays assigned
    }
    $add = array_values(array_unique(array_diff($add, $slugs)));
    if (!$add) return;
    $term_ids = [];
    foreach ($add as $s) {
        $t = get_term_by('slug', $s, 'product_cat');
        if ($t && !is_wp_error($t)) $term_ids[] = (int) $t->term_id;
    }
    if (!$term_ids) return;
    $nx_running = true;
    wp_set_object_terms($post_id, $term_ids, 'product_cat', true);
    $nx_running = false;
}, 20, 3);
