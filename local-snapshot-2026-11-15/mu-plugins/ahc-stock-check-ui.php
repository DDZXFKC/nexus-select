<?php
/*
Plugin Name: AHC Stock Check UI（その場で判定 → カートへ）
Description: 商品ページの「在庫を確認する」ボタン・ポップアップ・スピナー・結果表示・カートへ進むボタン。
入力欄は置かない（オーナー決定 2026-11-21 12:40）。判定とカート許可はサーバー側（ahc-stock-check.php、GPT 担当）。
設計：docs/stock-check-inline-final-design-claude-2026-11-21.md
*/
if (!defined('ABSPATH')) exit;

function ahc_scui_is_product_page() { return function_exists('is_product') && is_product(); }

/* 商品ページ：WooCommerce の「カートに追加」ボタンを「在庫を確認する」に置き換える。
 * カートには、在庫確認で出た購入許可を通してだけ入る（サーバー側の門は GPT 担当）。 */
add_action('wp', function () {
    if (!ahc_scui_is_product_page()) return;
    remove_action('woocommerce_single_variation', 'woocommerce_single_variation_add_to_cart_button', 20);
    add_action('woocommerce_single_variation', function () { echo ahc_scui_block(true); }, 20);
    remove_action('woocommerce_simple_add_to_cart', 'woocommerce_simple_add_to_cart', 30);
    add_action('woocommerce_simple_add_to_cart', function () {
        global $product;
        if ($product && $product->is_in_stock()) echo '<div class="cart">', ahc_scui_block(false), '</div>';
    }, 30);
    add_action('woocommerce_single_product_summary', function () {
        echo '<p class="ahc-sc-origin">海外お取り寄せ / 国内送料無料</p>';
    }, 11);
});

function ahc_scui_block($variable) {
    global $product;
    if (!$product) return '';
    $pid = (int) $product->get_id();
    $icons = [
        'buy'   => '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 7h12l-1 13H7L6 7z M9 7a3 3 0 0 1 6 0" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>',
        'check' => '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12l5 5L20 6" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>',
        'ship'  => '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 7h11v9H3z M14 10h4l3 3v3h-7 M7 19a1.5 1.5 0 1 0 0-.1 M17 19a1.5 1.5 0 1 0 0-.1" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>',
    ];
    ob_start(); ?>
<div class="ahc-sc" data-product-id="<?php echo $pid; ?>" data-product-name="<?php echo esc_attr($product->get_name()); ?>" data-variable="<?php echo $variable ? '1' : '0'; ?>">
  <button type="button" class="button alt ahc-sc-open"<?php echo $variable ? ' disabled' : ''; ?>>在庫を確認する</button>
  <p class="ahc-sc-reason" aria-live="polite"><?php echo $variable ? 'カラー・サイズを選択してください' : ''; ?></p>
  <p class="ahc-sc-free">在庫確認は無料です。この時点では注文・決済は発生しません。</p>
  <ul class="ahc-sc-guide">
    <li><?php echo $icons['buy']; ?>ご注文後に海外ショップから買い付け</li>
    <li><?php echo $icons['check']; ?>検品後にお届け</li>
    <li><?php echo $icons['ship']; ?>国内送料無料・配送状況の確認が可能</li>
  </ul>
  <dialog class="ahc-sc-dialog" aria-labelledby="ahc-sc-title-<?php echo $pid; ?>">
    <div class="ahc-sc-panel">
      <p class="ahc-sc-title" id="ahc-sc-title-<?php echo $pid; ?>">在庫を確認する</p>
      <p class="ahc-sc-item"></p>
      <div class="ahc-sc-status-row" role="status" aria-live="polite">
        <span class="ahc-sc-spinner" hidden aria-hidden="true"></span>
        <p class="ahc-sc-status"></p>
      </div>
      <div class="ahc-sc-actions"></div>
      <div class="ahc-sc-terms">
        <p>海外ショップからの買い付けのため、次の場合は販売価格が掲載価格と変わることがあります。</p>
        <ul>
          <li>掲載時の買い付け先に在庫がなく、別の買い付け先で買う場合</li>
          <li>前提にしていたクーポンが失効・条件変更した場合</li>
          <li>買い付け先のセールが終了した場合</li>
          <li>為替が大きく円安に動いた場合</li>
          <li>買い付け先が値上げした場合</li>
        </ul>
      </div>
      <button type="button" class="ahc-sc-close" aria-label="閉じる">×</button>
    </div>
  </dialog>
</div>
<?php
    return ob_get_clean();
}

/* 在庫確認で全店品切れが確定したサイズ（_ahc_inline_oos_until が未来）は、他のお客様にも SOLD OUT と見せる。
 * WooCommerce の在庫データは書き換えない（設計 §4）。印はサーバー側（GPT）の ahc_sc_step が付ける。 */
add_filter('woocommerce_available_variation', function ($data, $product, $variation) {
    if ($variation && (int) get_post_meta($variation->get_id(), '_ahc_inline_oos_until', true) > time()) {
        $data['is_in_stock'] = false;
        $data['is_purchasable'] = false;
        $data['availability_html'] = '<p class="stock out-of-stock">SOLD OUT</p>';
    }
    return $data;
}, 20, 3);

add_action('wp_enqueue_scripts', function () {
    if (!ahc_scui_is_product_page()) return;
    $base = defined('WPMU_PLUGIN_URL') ? WPMU_PLUGIN_URL : content_url('mu-plugins');
    $file = __DIR__ . '/ahc-stock-check-ui.js';
    wp_enqueue_script('ahc-sc-ui', $base . '/ahc-stock-check-ui.js', ['jquery'], file_exists($file) ? (string) filemtime($file) : '1', true);
    wp_add_inline_script('ahc-sc-ui', 'window.AHC_SC_CFG = ' . wp_json_encode([
        'ajaxUrl'       => admin_url('admin-ajax.php'),
        'nonce'         => wp_create_nonce('ahc_sc_inline'),
        'budgetSeconds' => (int) apply_filters('ahc_sc_inline_budget_seconds', 45),
    ]) . ';', 'before');
});

add_action('wp_head', function () {
    if (!ahc_scui_is_product_page()) return; ?>
<style>
.ahc-sc-origin{font-size:12px;letter-spacing:.06em;margin:4px 0 14px}
.ahc-sc .ahc-sc-open{width:100%;min-height:51px;letter-spacing:.09em}
.ahc-sc .ahc-sc-open:disabled{opacity:.4;cursor:not-allowed}
.ahc-sc-reason{font-size:12px;color:#666;margin:6px 0 0;min-height:1em}
.ahc-sc-free{font-size:12px;margin:8px 0 12px}
.ahc-sc-guide{list-style:none;margin:0 0 16px;padding:0;font-size:12px}
.ahc-sc-guide li{display:flex;align-items:center;gap:8px;padding:4px 0}
.ahc-sc-guide svg{width:18px;height:18px;flex:none}
.ahc-sc-dialog{border:0;padding:0;width:min(520px,92vw);max-height:90vh;overflow:auto;background:#fff;color:#111}
.ahc-sc-dialog::backdrop{background:rgba(0,0,0,.45)}
.ahc-sc-panel{position:relative;padding:24px 20px 20px}
.ahc-sc-title{font-size:14px;letter-spacing:.08em;font-weight:600;margin:0 0 6px}
.ahc-sc-item{font-size:13px;margin:0 0 16px}
.ahc-sc-status-row{display:flex;align-items:flex-start;gap:10px;min-height:28px;margin:0 0 14px}
.ahc-sc-status{font-size:14px;line-height:1.6;margin:0}
.ahc-sc-status.is-error{color:#b00020}
.ahc-sc-spinner{flex:none;width:22px;height:22px;border:2px solid #ddd;border-top-color:#111;border-radius:50%;animation:ahc-sc-spin .8s linear infinite}
.ahc-sc-spinner[hidden]{display:none}
@keyframes ahc-sc-spin{to{transform:rotate(360deg)}}
@media (prefers-reduced-motion:reduce){.ahc-sc-spinner{animation-duration:2.4s}}
.ahc-sc-actions{display:flex;flex-direction:column;gap:10px;margin:0 0 16px}
.ahc-sc-actions .ahc-sc-cart{width:100%;min-height:51px;letter-spacing:.09em}
.ahc-sc-link{background:none;border:0;text-decoration:underline;font-size:12px;cursor:pointer;align-self:center}
.ahc-sc-terms{font-size:12px;background:#f6f6f6;padding:10px 12px}
.ahc-sc-terms p{margin:0 0 4px}
.ahc-sc-terms ul{margin:0;padding-left:1.2em}
.ahc-sc-close{position:absolute;top:6px;right:8px;background:none;border:0;font-size:22px;line-height:1;cursor:pointer;padding:6px}
</style>
<?php });
