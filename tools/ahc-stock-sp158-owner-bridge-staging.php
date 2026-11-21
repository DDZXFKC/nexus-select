<?php
/**
 * AFTER HOURS CLUB / Shoe Palace 158 verified identities + owner price rule.
 * STAGING ONLY; load with ahc-stock-inline-endpoints-staging.php and
 * ahc-stock-sp-live-adapter-staging.php. Do not load earlier SP offer or
 * pricing modules simultaneously.
 *
 * Evidence CSV is not a stock or current-price feed. Merchant availability
 * and price MUST be refreshed by the live adapter on every inquiry.
 */
defined('ABSPATH') || exit;

function ahc_sp158_valid_url($url) {
    if (!is_string($url) || !function_exists('wp_parse_url')) return false;
    $parts = wp_parse_url($url);
    return is_array($parts) && ($parts['scheme'] ?? '') === 'https'
        && ($parts['host'] ?? '') === 'www.shoepalace.com'
        && !isset($parts['user']) && !isset($parts['pass'])
        && !isset($parts['port']) && !isset($parts['query']) && !isset($parts['fragment'])
        && preg_match('~^/products/[A-Za-z0-9_-]+/?$~D', $parts['path'] ?? '') === 1;
}

/** Strictly validate the complete, unmodified, owner-reviewed 1713-row export. */
function ahc_sp158_evidence($path) {
    static $cache = [];
    $resolved = is_string($path) ? realpath($path) : false;
    if (!$resolved || !is_file($resolved) || !is_readable($resolved)
        || filesize($resolved) > 2000000) return null;
    $fingerprint = $resolved . ':' . filesize($resolved) . ':' . filemtime($resolved);
    if (array_key_exists($fingerprint, $cache)) return $cache[$fingerprint];
    $stream = fopen($resolved, 'rb');
    if (!$stream) return null;
    $required = ['product_id','parent_sku','variation_id','woo_variation_sku',
        'supplier_product_id','shopify_product_id_live','shopify_variant_id_live',
        'shopify_variant_sku_live','source_url','available_live','price_cents_live',
        'fetched_utc','status','reason'];
    $map = []; $parents = []; $merchantVariants = []; $valid = true; $count = 0;
    try {
        $headers = fgetcsv($stream, 0, ',', '"', '\\');
        if (!is_array($headers) || $headers !== $required) $valid = false;
        while ($valid && ($cells = fgetcsv($stream, 0, ',', '"', '\\')) !== false) {
            if (count($cells) !== count($headers)) { $valid=false; break; }
            $r = array_combine($headers, $cells);
            $pid = $r['product_id']; $vid = $r['variation_id'];
            $supplier = $r['supplier_product_id'];
            $merchantVariant = $r['shopify_variant_id_live'];
            $sku = $r['woo_variation_sku'];
            if ($r['status'] !== 'PASS' || $r['reason'] !== 'EXACT_PARENT_ID_AND_VARIANT_SKU'
                || !ctype_digit($pid) || !ctype_digit($vid) || !ctype_digit($supplier)
                || !ctype_digit($merchantVariant)
                || $r['parent_sku'] !== 'SP-' . $supplier
                || $r['shopify_product_id_live'] !== $supplier
                || !$sku || $r['shopify_variant_sku_live'] !== $sku
                || !ctype_digit($r['price_cents_live'])
                || !in_array($r['available_live'], ['0','1'], true)
                || !$r['fetched_utc'] || !ahc_sp158_valid_url($r['source_url'])) {
                $valid=false; break;
            }
            $key = $pid . ':' . $vid;
            $mkey = $supplier . ':' . $merchantVariant;
            if (isset($map[$key]) || isset($merchantVariants[$mkey])) {
                $valid=false; break;
            }
            if (isset($parents[$pid]) &&
                ($parents[$pid]['supplier'] !== $supplier ||
                 $parents[$pid]['url'] !== $r['source_url'])) {
                $valid=false; break;
            }
            $parents[$pid] = ['supplier'=>$supplier,'url'=>$r['source_url']];
            $merchantVariants[$mkey] = true;
            $map[$key] = $r;
            $count++;
            if ($count > 1713) { $valid=false; break; }
        }
    } finally { fclose($stream); }
    // Partial uploads are never accepted as a fully verified 158-product feed.
    $cache[$fingerprint] = ($valid && $count === 1713 && count($parents) === 158)
        ? $map : null;
    return $cache[$fingerprint];
}

/** Exact arithmetic, from the owner's final provided formula.
 * Source USD cents × 158 × 1.02 + 2200 + 1500 + 60,
 * then / 0.785 and round UP to next JPY 100.
 */
function ahc_sp158_sale_price_from_cents($cents) {
    if (!is_int($cents) || $cents <= 0 || $cents > 100000000) return null;
    // cost in 1/10000 JPY: cents * (158*102) + 3760*10000.
    $cost10000 = $cents * 16116 + 37600000;
    // Sale price / 100 = ceil(cost10000 / 785000).
    $sale = intdiv($cost10000 + 784999, 785000) * 100;
    return $sale > 0 && $sale <= 100000000 ? $sale : null;
}

function ahc_sp158_owner_offers($offers, $product_id, $variation_id, $attrs) {
    if (!is_array($offers)) return [];
    if (!defined('AHC_SP158_VERIFIED_CSV')) return $offers;
    if (!is_int($product_id) || !is_int($variation_id)
        || $product_id <= 0 || $variation_id <= 0
        || !function_exists('wc_get_product')) return $offers;
    $rows = ahc_sp158_evidence(AHC_SP158_VERIFIED_CSV);
    if (!is_array($rows)) return $offers;
    $row = $rows[$product_id . ':' . $variation_id] ?? null;
    if (!$row) return $offers;
    $parent = wc_get_product($product_id);
    $variation = wc_get_product($variation_id);
    if (!$parent || !$variation || !$parent->is_type('variable')
        || !$variation->is_type('variation')
        || (int)$variation->get_parent_id() !== $product_id
        || (string)$parent->get_sku() !== $row['parent_sku']
        || (string)$variation->get_sku() !== $row['woo_variation_sku']) return $offers;
    // Snapshot availability is intentionally ignored. Sorting estimates
    // are NOT sale quotes and never grant purchase authorization.
    $estimate = ahc_sp158_sale_price_from_cents((int)$row['price_cents_live']);
    if ($estimate === null) return $offers;
    $offers[] = [
        'shop'=>'SP', 'url'=>$row['source_url'],
        'supplier_product_id'=>$row['supplier_product_id'],
        'merchant_variant_id'=>$row['shopify_variant_id_live'],
        'merchant_variant_sku'=>$row['shopify_variant_sku_live'],
        'identity_verified'=>true, 'verified_currency'=>'USD',
        'estimated_total_jpy'=>$estimate
    ];
    return $offers;
}
add_filter('ahc_inline_verified_offers', 'ahc_sp158_owner_offers', 25, 4);

function ahc_sp158_owner_price($previous, $current_price, $offer, $product_id, $variation_id) {
    if ($previous !== null || !is_array($offer) || ($offer['shop'] ?? '') !== 'SP') return $previous;
    if (!is_array($current_price) || ($current_price['currency'] ?? '') !== 'USD'
        || !is_string($current_price['amount'] ?? null)
        || !preg_match('/^[0-9]{1,6}\.[0-9]{2}$/D', $current_price['amount'])
        || !is_int($product_id) || !is_int($variation_id)
        || !defined('AHC_SP158_VERIFIED_CSV')) return null;
    $rows = ahc_sp158_evidence(AHC_SP158_VERIFIED_CSV);
    $row = is_array($rows) ? ($rows[$product_id . ':' . $variation_id] ?? null) : null;
    if (!$row || ($offer['identity_verified'] ?? false) !== true
        || ($offer['verified_currency'] ?? '') !== 'USD'
        || ($offer['supplier_product_id'] ?? '') !== $row['supplier_product_id']
        || (string)($offer['merchant_variant_id'] ?? '') !== $row['shopify_variant_id_live']
        || ($offer['merchant_variant_sku'] ?? '') !== $row['shopify_variant_sku_live']
        || ($offer['url'] ?? '') !== $row['source_url']) return null;
    // The .js product endpoint has no checkout destination, sales tax,
    // domestic-shipping charge or import-fee evidence. The owner's exact
    // formula is authoritative, but it must not be treated as proof that
    // those costs are already covered for this particular purchase route.
    $cost_context = [
        'shop'=>'SP',
        'product_id'=>$product_id,
        'variation_id'=>$variation_id,
        'supplier_product_id'=>$row['supplier_product_id'],
        'merchant_variant_id'=>$row['shopify_variant_id_live'],
        'merchant_variant_sku'=>$row['shopify_variant_sku_live'],
        'source_url'=>$row['source_url'],
        'source_price_usd'=>$current_price['amount'],
        'currency'=>'USD',
    ];
    if (apply_filters('ahc_sp158_live_cost_coverage_verified', false,
            $cost_context) !== true) return null;
    $cents = (int)str_replace('.', '', $current_price['amount']);
    return ahc_sp158_sale_price_from_cents($cents);
}
add_filter('ahc_inline_recomputed_sale_price', 'ahc_sp158_owner_price', 25, 5);
