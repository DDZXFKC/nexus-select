<?php
/**
 * AFTER HOURS CLUB — SP158 production route cost coverage gate.
 *
 * Explicitly separate the owner's fixed pricing arithmetic from proof that
 * it covers THIS supplier purchase route. Shopify /products/<handle>.js
 * does not disclose delivery ZIP, checkout shipping, sales tax, customs,
 * import VAT or AHC payment provider fees.
 *
 * Optional private JSON file: define AHC_SP158_COST_COVERAGE_FILE to an
 * absolute path OUTSIDE webroot. Nothing in this file is a price quote.
 * No file, missing fields, non-matching selected SKU/price or unreviewed
 * expense => false; the purchase check stays "unconfirmed".
 *
 * The file is independently managed by the store operator and must not be
 * supplied from POST, theme HTML, customer cookies, or public GitHub.
 */
defined('ABSPATH') || exit;

function ahc_sp158_route_cost_coverage($verified, $context) {
    if (!is_array($context) || ($context['shop'] ?? '') !== 'SP'
        || !defined('AHC_SP158_COST_COVERAGE_FILE')
        || !is_string(AHC_SP158_COST_COVERAGE_FILE)) return false;
    $file = realpath(AHC_SP158_COST_COVERAGE_FILE);
    if (!$file || !is_file($file) || !is_readable($file)
        || filesize($file) > 2000000 || filesize($file) < 8) return false;

    // An SHA-256 pin is required to prevent an accidentally overwritten
    // file from silently changing the merchant/fee approvals.
    if (!defined('AHC_SP158_COST_COVERAGE_SHA256')
        || !is_string(AHC_SP158_COST_COVERAGE_SHA256)
        || !preg_match('/^[a-f0-9]{64}$/D', AHC_SP158_COST_COVERAGE_SHA256)
        || !hash_equals(AHC_SP158_COST_COVERAGE_SHA256, hash_file('sha256', $file))) return false;

    $data = json_decode(file_get_contents($file), true);
    if (!is_array($data) || ($data['schema'] ?? null) !== 'ahc.sp158.cost-coverage.v1'
        || ($data['approved_for'] ?? null) !== 'AFTER HOURS CLUB'
        || ($data['shop'] ?? null) !== 'SP'
        || ($data['owner_formula'] ?? null) !== 'USDx158x1.02+2200+1500+60/div0.785-ceil100'
        || ($data['source_currency'] ?? null) !== 'USD'
        || ($data['ahc_channel_divisor_confirmed'] ?? null) !== true
        || !is_string($data['approver_ref'] ?? null) || trim($data['approver_ref']) === ''
        || !is_array($data['approvals'] ?? null)) return false;

    $pid = (string)($context['product_id'] ?? '');
    $vid = (string)($context['variation_id'] ?? '');
    $sid = (string)($context['supplier_product_id'] ?? '');
    $variant = (string)($context['merchant_variant_id'] ?? '');
    $sku = (string)($context['merchant_variant_sku'] ?? '');
    $url = $context['source_url'] ?? null;
    $amount = $context['source_price_usd'] ?? null;
    if (!ctype_digit($pid) || !ctype_digit($vid) ||
        !ctype_digit($sid) || !ctype_digit($variant)
        || $sku === '' || !is_string($amount)
        || !preg_match('/^[0-9]{1,6}\.[0-9]{2}$/D', $amount)
        || !function_exists('ahc_sp158_valid_url') || !ahc_sp158_valid_url($url)) return false;

    $target = $pid . ':' . $vid;
    $entry = $data['approvals'][$target] ?? null;
    if (!is_array($entry) || ($entry['product_id'] ?? '') !== $pid
        || ($entry['variation_id'] ?? '') !== $vid
        || ($entry['supplier_product_id'] ?? '') !== $sid
        || ($entry['merchant_variant_id'] ?? '') !== $variant
        || ($entry['merchant_variant_sku'] ?? '') !== $sku
        || ($entry['source_url'] ?? '') !== $url
        || ($entry['reviewed_price_usd'] ?? '') !== $amount
        || ($entry['formula_coverage_approved'] ?? null) !== true
        || !is_string($entry['route_ref'] ?? null) || trim($entry['route_ref']) === '') return false;

    // Fees that may exist even with complete stock + product price.
    // Each must have its actual checkout/route evidence, AND a reviewed
    // reason why the fixed owner formula already covers it or it is zero.
    $required = ['source_domestic_shipping','source_sales_tax',
        'international_shipping','japan_domestic_shipping',
        'customs_duty','import_consumption_tax','partner_fee',
        'packaging','payment_processing','other_mandatory_fees'];
    $coverage = $entry['fee_coverage'] ?? null;
    if (!is_array($coverage) || count($coverage) !== count($required)
        || array_diff($required, array_keys($coverage))
        || array_diff(array_keys($coverage), $required)) return false;

    foreach ($required as $name) {
        $fee = $coverage[$name];
        if (!is_array($fee) || ($fee['status'] ?? null) !== 'reviewed_covered_or_not_applicable'
            || !is_string($fee['evidence_ref'] ?? null)
            || trim($fee['evidence_ref']) === ''
            || !is_string($fee['explanation'] ?? null)
            || trim($fee['explanation']) === '') return false;
    }
    return true;
}
add_filter('ahc_sp158_live_cost_coverage_verified',
    'ahc_sp158_route_cost_coverage', 20, 2);
