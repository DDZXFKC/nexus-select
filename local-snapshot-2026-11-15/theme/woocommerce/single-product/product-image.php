<?php
if(!defined('ABSPATH'))exit;
global $product;
if(!$product)return;
$ids=[];
if($product->get_image_id())$ids[]=$product->get_image_id();
$ids=array_merge($ids,$product->get_gallery_image_ids());
echo '<div class="woocommerce-product-gallery nexus-gallery" aria-label="Product images">';
if(!$ids){echo wc_placeholder_img('woocommerce_single');}
foreach(array_unique($ids) as $id){
 $full=wp_get_attachment_image_url($id,'full');
 if(!$full)continue;
 echo '<a href="'.esc_url($full).'" target="_blank" rel="noopener">'.wp_get_attachment_image($id,'large',false,['loading'=>$id===$ids[0]?'eager':'lazy','decoding'=>'async']).'</a>';
}
echo '</div><p class="nexus-gallery-note">画像をクリックすると拡大表示できます。</p>'; 
