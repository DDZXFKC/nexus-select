<?php
/**
 * AFTER HOURS CLUB Shoe Palace 158 stock check — staging deployment loader.
 *
 * Copy this file to wp-content/mu-plugins/ahc-sp158-staging-loader.php.
 * Place the four modules in:
 * wp-content/mu-plugins/ahc-sp158/
 *
 * Site operator must define AHC_SP158_STAGING_ENABLED=true and
 * AHC_SP158_VERIFIED_CSV=/absolute/private/path/to/reviewed.csv.
 * Without both values the loader is inert.
 *
 * Never load ahc-stock-inline-cart-gate-staging.php or the previous
 * ahc-stock-sp-evidence-offers-staging.php / pricing-staging.php together.
 */
defined('ABSPATH') || exit;
if (!defined('AHC_SP158_STAGING_ENABLED') || AHC_SP158_STAGING_ENABLED !== true
    || !defined('AHC_SP158_VERIFIED_CSV')
    || !is_string(AHC_SP158_VERIFIED_CSV)) return;

$ahc_sp158_dir = __DIR__ . '/ahc-sp158';
$ahc_sp158_files = [
    $ahc_sp158_dir . '/ahc-stock-inline-endpoints-staging.php',
    $ahc_sp158_dir . '/ahc-stock-sp158-owner-bridge-staging.php',
    $ahc_sp158_dir . '/ahc-stock-sp158-cost-coverage-provider.php',
    $ahc_sp158_dir . '/ahc-stock-sp-live-adapter-staging.php',
];
foreach ($ahc_sp158_files as $ahc_sp158_file) {
    if (!is_readable($ahc_sp158_file)) return;
}
if (!is_readable(AHC_SP158_VERIFIED_CSV)) return;
// If another MU-plugin has already registered this Ajax route, do not
// register a duplicate endpoint. Investigate deployment order instead.
if (function_exists('has_action') &&
    (has_action('wp_ajax_ahc_sc_add_to_cart') ||
     has_action('wp_ajax_nopriv_ahc_sc_add_to_cart'))) return;
foreach ($ahc_sp158_files as $ahc_sp158_file) require_once $ahc_sp158_file;
unset($ahc_sp158_dir,$ahc_sp158_files,$ahc_sp158_file);
