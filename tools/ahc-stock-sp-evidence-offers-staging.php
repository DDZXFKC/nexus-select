<?php
/**
 * AFTER HOURS CLUB — STAGING ONLY. Verified Shoe Palace offer resolver.
 *
 * The owner-reviewed CSV contains identity evidence, NOT real-time stock or
 * complete landed costs. The other filter must explicitly supply a positive
 * verified estimate. By default this provider emits zero offers.
 *
 * Configure AHC_SP_EVIDENCE_CSV outside the public web root on staging.
 */
defined('ABSPATH') || exit;

function ahc_sp_offer_verified_url($url) {
    if (!is_string($url) || !$url) return false;
    $p = wp_parse_url($url);
    return is_array($p) && ($p['scheme'] ?? '') === 'https'
        && ($p['host'] ?? '') === 'www.shoepalace.com'
        && !isset($p['user']) && !isset($p['pass'])
        && !isset($p['query']) && !isset($p['fragment']) && !isset($p['port'])
        && preg_match('~^/products/[a-zA-Z0-9_-]+/?$~D', $p['path'] ?? '') === 1;
}
function ahc_sp_offers_from_evidence($offers, $product_id, $variation_id, $attrs) {
    // Never override an upstream provider and never publish guessed candidates.
    if (!is_array($offers)) return [];
    if (!defined('AHC_SP_EVIDENCE_CSV') || !is_string(AHC_SP_EVIDENCE_CSV)) return $offers;
    if (!is_int($product_id) || !is_int($variation_id) || $product_id <= 0 || $variation_id <= 0) return $offers;
    if (!function_exists('wc_get_product')) return $offers;
    $parent = wc_get_product($product_id);
    $variation = wc_get_product($variation_id);
    if (!$parent || !$variation || !$parent->is_type('variable') ||
        !$variation->is_type('variation') || (int)$variation->get_parent_id() !== $product_id) return $offers;
    if (!preg_match('/^SP-([0-9]+)$/D', (string)$parent->get_sku(), $match)) return $offers;
    $supplier_product_id = $match[1];
    $sku = (string)$variation->get_sku();
    if ($sku === '') return $offers;
    // Avoid accepting evidence from an untrusted directory or partial file.
    $file = realpath(AHC_SP_EVIDENCE_CSV);
    if (!$file || !is_file($file) || !is_readable($file) || filesize($file) > 2000000) return $offers;
    $handle = fopen($file, 'rb');
    if (!$handle) return $offers;
    $rows = [];
    $valid = true;
    try {
        $headers = fgetcsv($handle, 0, ',', '"', '\\');
        $must = ['product_id','variation_id','shop_code','supplier_product_id',
                 'source_url','merchant_variant_id','status','merchant_variant_sku',
                 'woo_variation_sku','sku_evidence','sku_verified_at_utc'];
        if (!is_array($headers) || count($headers) !== count(array_unique($headers))
            || array_diff($must, $headers)) $valid = false;
        if ($valid) {
            while (($cells = fgetcsv($handle, 0, ',', '"', '\\')) !== false) {
                if (count($cells) !== count($headers)) { $valid = false; break; }
                $row = array_combine($headers, $cells);
                if (($row['product_id'] ?? '') !== (string)$product_id ||
                    ($row['variation_id'] ?? '') !== (string)$variation_id) continue;
                $rows[] = $row;
                if (count($rows) > 1) break;
            }
        }
    } finally { fclose($handle); }
    if (!$valid || count($rows) !== 1) return $offers;
    $row = $rows[0];
    if ($row['shop_code'] !== 'SP' || $row['status'] !== 'verified' ||
        $row['supplier_product_id'] !== $supplier_product_id ||
        $row['woo_variation_sku'] !== $sku || $row['merchant_variant_sku'] !== $sku ||
        !ctype_digit((string)$row['merchant_variant_id']) ||
        !$row['sku_evidence'] || !$row['sku_verified_at_utc'] ||
        !ahc_sp_offer_verified_url($row['source_url'])) return $offers;
    // Pricing is independently reviewed; never substitute historic prices.
    $estimate = apply_filters('ahc_sp_verified_landed_estimate_jpy', null, [
        'product_id' => $product_id, 'variation_id' => $variation_id,
        'supplier_product_id' => $supplier_product_id,
        'merchant_variant_id' => $row['merchant_variant_id'],
        'merchant_variant_sku' => $sku, 'source_url' => $row['source_url']
    ]);
    if (!is_int($estimate) || $estimate <= 0) return $offers;
    // Shopify .js does not carry a currency; do not assert USD from URL.
    $currency = apply_filters('ahc_sp_verified_store_currency', null,
        $row['source_url'], $supplier_product_id);
    if ($currency !== 'USD') return $offers;
    $offers[] = [
        'shop'=>'SP', 'url'=>$row['source_url'],
        'supplier_product_id'=>$supplier_product_id,
        'merchant_variant_id'=>$row['merchant_variant_id'],
        'merchant_variant_sku'=>$sku, 'identity_verified'=>true,
        'verified_currency'=>$currency, 'estimated_total_jpy'=>$estimate
    ];
    return $offers;
}
add_filter('ahc_inline_verified_offers', 'ahc_sp_offers_from_evidence', 20, 4);
