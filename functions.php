<?php
if (!defined('ABSPATH')) exit;
add_action('after_setup_theme', function(){
 add_theme_support('title-tag'); add_theme_support('post-thumbnails'); add_theme_support('woocommerce'); add_theme_support('html5',['search-form','gallery','caption']);
 register_nav_menus(['primary'=>__('Primary Menu','nexus-select')]);
});
add_action('wp_enqueue_scripts', function(){wp_enqueue_style('nexus-style',get_stylesheet_uri(),[],wp_get_theme()->get('Version'));wp_enqueue_script('nexus-main',get_template_directory_uri().'/main.js',[],wp_get_theme()->get('Version'),true);});
add_filter('woocommerce_show_page_title','__return_false');
add_action('woocommerce_before_single_product',function(){if(function_exists('woocommerce_breadcrumb')) woocommerce_breadcrumb(['delimiter'=>' / ','wrap_before'=>'<nav class="nexus-breadcrumb">','wrap_after'=>'</nav>']);},5);
remove_action('woocommerce_before_main_content','woocommerce_breadcrumb',20);
add_action('woocommerce_single_product_summary',function(){echo '<p class="nexus-notice">海外から買い付ける商品は、在庫・価格・配送予定が変わる場合があります。ご注文前に各商品条件をご確認ください。</p>';},35);
// A guide is only shown when a verified, product-specific guide has been entered by the store operator.
add_action('woocommerce_single_product_summary',function(){
 $id=get_the_ID();$guide=get_post_meta($id,'_nexus_size_guide_html',true);
 if(!$guide)return;
 echo '<details class="nexus-size-guide"><summary>SIZE GUIDE</summary><div>'.wp_kses_post($guide).'</div></details>';
},36);
add_action('add_meta_boxes_product',function(){add_meta_box('nexus_size_guide',__('Verified size guide','nexus-select'),function($post){
 wp_nonce_field('nexus_guide_save','nexus_guide_nonce');
 echo '<p>ブランド・商品区分・モデルに適合する公式サイズ表だけを入力してください。未入力なら非表示です。</p>';
 wp_editor(get_post_meta($post->ID,'_nexus_size_guide_html',true),'nexus_guide_editor',['textarea_name'=>'nexus_guide_html','textarea_rows'=>7,'media_buttons'=>false]);
 },'product','normal');});
add_action('save_post_product',function($post_id){
 if(!isset($_POST['nexus_guide_nonce'])||!wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['nexus_guide_nonce'])),'nexus_guide_save'))return;
 if(defined('DOING_AUTOSAVE')&&DOING_AUTOSAVE)return;
 if(!current_user_can('edit_post',$post_id))return;
 if(isset($_POST['nexus_guide_html']))update_post_meta($post_id,'_nexus_size_guide_html',wp_kses_post(wp_unslash($_POST['nexus_guide_html'])));
});

add_action('wp', function () {
    if (!function_exists('is_product') || !is_product()) {
        return;
    }
    remove_action(
        'woocommerce_before_single_product_summary',
        'woocommerce_show_product_images',
        20
    );
    add_action(
        'woocommerce_before_single_product_summary',
        function () {
            wc_get_template('single-product/product-image.php');
        },
        20
    );
});

/* PC homepage editorial images. IDs point to licensed images in Media Library. */
add_action('customize_register', function($wp_customize) {
    $wp_customize->add_section('nexus_pc_editorial', [
        'title' => 'NEXUS SELECT — PCホーム画像',
        'priority' => 35,
        'description' => '使用権を確認した画像だけを設定してください。スマホホームには影響しません。',
    ]);
    foreach ([
        'nexus_pc_hero_image' => 'PCヒーロー（横長・モデル写真）',
        'nexus_pc_men_image' => 'PC MENコレクション写真',
        'nexus_pc_women_image' => 'PC WOMENコレクション写真',
    ] as $setting => $label) {
        $wp_customize->add_setting($setting, ['default'=>0,'sanitize_callback'=>'absint']);
        $wp_customize->add_control(new WP_Customize_Media_Control($wp_customize, $setting, [
            'label'=>$label, 'section'=>'nexus_pc_editorial', 'mime_type'=>'image'
        ]));
    }
});

// Ensure KIDS is an independent WooCommerce product category.
// Admin-only, idempotent; does not alter any existing product assignments.
add_action('admin_init', function () {
    if (!current_user_can('manage_woocommerce') || !taxonomy_exists('product_cat')) return;
    if (term_exists('kids', 'product_cat')) return;
    $result = wp_insert_term('KIDS', 'product_cat', ['slug' => 'kids']);
    if (is_wp_error($result)) {
        error_log('NEXUS SELECT: Unable to create KIDS category: ' . $result->get_error_message());
    }
});


/* Mobile campaign media, separate from desktop settings. */
add_action('customize_register', function($c){
 $c->add_section('nexus_mobile_campaign',['title'=>'NEXUS SELECT — モバイルホーム','priority'=>36]);
 foreach(['poster'=>'動画ポスター','video'=>'キャンペーン動画 MP4','mens'=>'MEN 写真','womens'=>'WOMEN 写真','kids'=>'KIDS 写真'] as $key=>$label){
  $id='nexus_mobile_'.$key;
  $c->add_setting($id,['default'=>0,'sanitize_callback'=>'absint']);
  $c->add_control(new WP_Customize_Media_Control($c,$id,['label'=>$label,'section'=>'nexus_mobile_campaign','mime_type'=>$key==='video'?'video':'image']));
 }
});
