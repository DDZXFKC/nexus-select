<?php
defined('ABSPATH') || exit;
get_header('shop');
while (have_posts()) : the_post();
    global $product;
    do_action('woocommerce_before_single_product');
    if (post_password_required()) {
        echo get_the_password_form();
        continue;
    }
    ?>
    <div id="product-<?php the_ID(); ?>" <?php wc_product_class('nexus-product', $product); ?>>
        <div class="nexus-product-layout">
            <div class="nexus-product-visual">
                <?php do_action('woocommerce_before_single_product_summary'); ?>
            </div>
            <div class="nexus-product-info">
                <div class="summary entry-summary">
                    <?php do_action('woocommerce_single_product_summary'); ?>
                </div>
            </div>
        </div>
        <div class="nexus-product-bottom">
            <?php do_action('woocommerce_after_single_product_summary'); ?>
        </div>
    </div>
    <?php
    do_action('woocommerce_after_single_product');
endwhile;
get_footer('shop');
