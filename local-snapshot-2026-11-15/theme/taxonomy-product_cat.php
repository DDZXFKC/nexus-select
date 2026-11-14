<?php
/**
 * Product category archive with gender category tree sidebar.
 * AFTER HOURS CLUB category navigation (2026-11-15).
 * Falls back to the standard WooCommerce archive for non-gender roots.
 */
defined('ABSPATH') || exit;

$nx_current = get_queried_object();
if (!$nx_current || !isset($nx_current->term_id)) {
    get_header('shop');
    woocommerce_content();
    get_footer('shop');
    return;
}

// Find the root term of the current category.
$nx_root = $nx_current;
$nx_guard = 0;
while ($nx_root->parent && $nx_guard < 10) {
    $nx_parent = get_term($nx_root->parent, 'product_cat');
    if (!$nx_parent || is_wp_error($nx_parent)) break;
    $nx_root = $nx_parent;
    $nx_guard++;
}
if (!in_array($nx_root->slug, ['mens', 'womens', 'kids'], true)) {
    get_header('shop');
    woocommerce_content();
    get_footer('shop');
    return;
}

$nx_ancestors = get_ancestors($nx_current->term_id, 'product_cat', 'taxonomy');
$nx_current_id = (int) $nx_current->term_id;

// Build the term tree once. A term is visible when it has products itself
// or any visible descendant. With the store convention (products assigned
// to root + group + leaf), group counts already include their products.
$nx_by_id = [];
$nx_children = [];
$nx_all = get_terms(['taxonomy' => 'product_cat', 'hide_empty' => false, 'orderby' => 'term_id', 'order' => 'ASC']);
foreach ($nx_all as $nx_t) {
    $nx_by_id[(int) $nx_t->term_id] = $nx_t;
    $nx_children[(int) $nx_t->parent][] = $nx_t;
}
$nx_visible = [];
$nx_mark_visible = function ($term_id) use (&$nx_mark_visible, &$nx_children, &$nx_by_id, &$nx_visible) {
    $nx_any = false;
    foreach (($nx_children[$term_id] ?? []) as $nx_kid) {
        if ($nx_mark_visible((int) $nx_kid->term_id)) $nx_any = true;
    }
    $nx_visible[$term_id] = ((int) ($nx_by_id[$term_id]->count ?? 0) > 0) || $nx_any;
    return $nx_visible[$term_id];
};
$nx_mark_visible((int) $nx_root->term_id);

$nx_render_level = function ($parent_id, $depth, $parent_term = null) use (&$nx_render_level, &$nx_children, &$nx_visible, $nx_current_id, $nx_ancestors) {
    $nx_kids = $nx_children[$parent_id] ?? [];
    if (!$nx_kids) return;
    echo '<ul class="nx-catnav__list nx-catnav__list--depth-' . (int) $depth . '">';
    // Owner-confirmed structure (2026-11-15): no "All Shoes" style child links.
    // The group name itself (e.g. SHOES) is the link to the group's full listing.
    foreach ($nx_kids as $nx_t) {
        $nx_tid = (int) $nx_t->term_id;
        if (empty($nx_visible[$nx_tid])) continue;
        $nx_link = get_term_link($nx_t);
        if (is_wp_error($nx_link)) continue;
        $nx_is_current = ($nx_tid === $nx_current_id);
        $nx_is_ancestor = in_array($nx_tid, $nx_ancestors, true);
        $nx_has_kids = false;
        foreach (($nx_children[$nx_tid] ?? []) as $nx_gc) {
            if (!empty($nx_visible[(int) $nx_gc->term_id])) { $nx_has_kids = true; break; }
        }
        $nx_classes = 'nx-catnav__item';
        if ($nx_is_current) $nx_classes .= ' is-current';
        if ($nx_is_ancestor) $nx_classes .= ' is-ancestor';
        echo '<li class="' . esc_attr($nx_classes) . '">';
        if ($nx_has_kids) {
            $nx_open = ($nx_is_current || $nx_is_ancestor || $depth === 0) ? ' open' : '';
            echo '<details class="nx-catnav__branch"' . $nx_open . '>';
            echo '<summary class="nx-catnav__summary"><a class="nx-catnav__link" href="' . esc_url($nx_link) . '"' . ($nx_is_current ? ' aria-current="page"' : '') . '>' . esc_html($nx_t->name) . '</a></summary>';
            $nx_render_level($nx_tid, $depth + 1, $nx_t);
            echo '</details>';
        } else {
            echo '<a class="nx-catnav__link" href="' . esc_url($nx_link) . '"' . ($nx_is_current ? ' aria-current="page"' : '') . '>' . esc_html($nx_t->name) . '</a>';
        }
        echo '</li>';
    }
    echo '</ul>';
};

global $wp_query;
$nx_found = isset($wp_query) ? (int) $wp_query->found_posts : 0;

get_header('shop');
?>
<div class="nx-archive">
  <aside class="nx-archive__side">
    <details class="nx-catnav" open>
      <summary class="nx-catnav__title"><?php echo esc_html($nx_root->name); ?></summary>
      <nav class="nx-catnav__nav" aria-label="<?php echo esc_attr($nx_root->name); ?> categories">
        <?php
        $nx_root_link = get_term_link($nx_root);
        if (!is_wp_error($nx_root_link)) {
            $nx_all_label = 'ALL ' . $nx_root->name . ' ITEMS';
            if ($nx_root->slug === 'kids') $nx_all_label = 'ALL KIDS ITEMS';
            echo '<ul class="nx-catnav__list nx-catnav__list--depth-0"><li class="nx-catnav__item' . ($nx_current_id === (int) $nx_root->term_id ? ' is-current' : '') . '"><a class="nx-catnav__link nx-catnav__link--all" href="' . esc_url($nx_root_link) . '"' . ($nx_current_id === (int) $nx_root->term_id ? ' aria-current="page"' : '') . '>' . esc_html($nx_all_label) . '</a></li></ul>';
        }
        $nx_render_level((int) $nx_root->term_id, 0);
        ?>
      </nav>
    </details>
  </aside>
  <div class="nx-archive__main">
    <h1 class="nx-archive__heading"><?php echo esc_html($nx_current->name); ?></h1>
    <?php if ($nx_found < 1) : ?>
      <p class="nx-archive__empty">NO ITEMS</p>
    <?php else : ?>
      <?php woocommerce_content(); ?>
    <?php endif; ?>
  </div>
</div>
<?php
get_footer('shop');
