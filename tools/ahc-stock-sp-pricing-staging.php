<?php
/**
 * AHC staging-only sale price calculation. Does not authorize purchase.
 * Every cost input must be supplied by a trusted server-side provider for
 * the exact live supplier variant and price. No default/assumed zero costs.
 */
defined('ABSPATH') || exit;

function ahc_sp_pricing_jpy($previous, $current_price, $offer, $product_id, $variation_id) {
    if ($previous !== null || !is_array($offer) || ($offer['shop'] ?? '') !== 'SP') return $previous;
    if (!is_array($current_price) || !is_array($offer) ||
        ($offer['shop'] ?? '') !== 'SP' ||
        ($current_price['currency'] ?? '') !== 'USD' ||
        !is_string($current_price['amount'] ?? null) ||
        !preg_match('/^[0-9]{1,6}\.[0-9]{2}$/D', $current_price['amount']) ||
        !is_int($product_id) || !is_int($variation_id) || $product_id <= 0 || $variation_id <= 0) return null;
    $cents = (int)str_replace('.', '', $current_price['amount']);
    if ($cents <= 0) return null;
    if (($offer['identity_verified'] ?? false) !== true ||
        !ctype_digit((string)($offer['merchant_variant_id'] ?? '')) ||
        !ctype_digit((string)($offer['supplier_product_id'] ?? '')) ||
        !is_string($offer['merchant_variant_sku'] ?? null) ||
        $offer['merchant_variant_sku'] === '') return null;

    /*
     * The provider must verify source, validity, purchase route, USD/JPY rate,
     * all tax/fee components and the owner's margin/rounding policy.
     * An explicit zero requires its own documented, reviewed reason.
     */
    $input = apply_filters('ahc_sp_verified_live_cost_inputs', null,
        $current_price, $offer, $product_id, $variation_id);
    if (!is_array($input) || ($input['approved'] ?? false) !== true ||
        ($input['shop'] ?? '') !== 'SP' ||
        (string)($input['supplier_product_id'] ?? '') !== (string)$offer['supplier_product_id'] ||
        (string)($input['merchant_variant_id'] ?? '') !== (string)$offer['merchant_variant_id'] ||
        (string)($input['merchant_variant_sku'] ?? '') !== $offer['merchant_variant_sku'] ||
        ($input['source_price_usd'] ?? null) !== $current_price['amount'] ||
        !is_string($input['source_ref'] ?? null) || $input['source_ref'] === '' ||
        !is_int($input['observed_at'] ?? null) ||
        abs(time() - $input['observed_at']) > 300) return null;

    $fx = $input['fx_jpy_per_usd_x10000'] ?? null;
    $fx_at = $input['fx_observed_at'] ?? null;
    if (!is_int($fx) || $fx <= 0 || $fx > 10000000 ||
        !is_int($fx_at) || abs(time() - $fx_at) > 3600) return null;

    $required = ['local_sales_tax', 'local_delivery', 'international_shipping',
        'domestic_shipping', 'customs_duty', 'import_consumption_tax',
        'partner_fee', 'packaging', 'other_fees'];
    $costs = $input['costs_jpy'] ?? null;
    $zero_reasons = $input['verified_zero_reasons'] ?? null;
    if (!is_array($costs) || !is_array($zero_reasons) ||
        count($costs) !== count($required) ||
        array_diff($required, array_keys($costs)) ||
        array_diff(array_keys($costs), $required)) return null;

    // Use positive integer scaled FX: cents * (JPY per USD * 10000) / 1,000,000.
    // Hard caps prevent integer overflow even for unexpected remote input.
    if ($cents > 100000000 || $cents > intdiv(PHP_INT_MAX, $fx)) return null;
    $purchase_jpy = intdiv($cents * $fx + 999999, 1000000);
    $landed = $purchase_jpy;
    foreach ($required as $name) {
        $cost = $costs[$name];
        if (!is_int($cost) || $cost < 0 || $cost > 10000000) return null;
        if ($cost === 0 && (!isset($zero_reasons[$name]) ||
            !is_string($zero_reasons[$name]) ||
            trim($zero_reasons[$name]) === '')) return null;
        $landed += $cost;
    }

    // Owner's sheet uses a source-price card uplift (2% in the
    // reviewed snapshot) and a revenue divisor, not a separately
    // invented fixed-profit + payment-fee gross-up formula.
    // Supply the channel-adjusted divisor from reviewed, current
    // server-side settings. Never silently apply a BUYMA divisor to AHC.
    $card_bps = $input['source_card_uplift_bps'] ?? null;
    $divisor = $input['channel_price_divisor_million'] ?? null;
    $round_up = $input['round_up_jpy'] ?? null;
    $policy = $input['pricing_policy_ref'] ?? null;
    if (($input['channel'] ?? '') !== 'AHC' ||
        ($input['channel_fee_verified'] ?? false) !== true ||
        !is_int($card_bps) || $card_bps < 0 || $card_bps > 10000 ||
        !is_int($divisor) || $divisor < 100000 || $divisor > 1000000 ||
        !is_int($round_up) || $round_up < 1 || $round_up > 10000 ||
        !is_string($policy) || $policy === '') return null;
    // Calculate the source price uplift at 1/10000 JPY precision,
    // then divide by the verified channel divisor and round upwards.
    // Arithmetic remains integer-only, with strict overflow guards.
    $factor = 10000 + $card_bps;
    if ($cents > intdiv(PHP_INT_MAX, $fx * $factor)) return null;
    $purchase_x10000 = intdiv($cents * $fx * $factor + 999999, 1000000);
    if ($landed < $purchase_jpy || $landed - $purchase_jpy > 100000000) return null;
    $total_x10000 = $purchase_x10000 + ($landed - $purchase_jpy) * 10000;
    if ($total_x10000 <= 0 || $total_x10000 > 9000000000000) return null;
    $denom = $divisor * 10000 * $round_up;
    if ($denom <= 0) return null;
    $price = intdiv($total_x10000 * 1000000 + $denom - 1, $denom) * $round_up;
    return ($price > 0 && $price <= 100000000) ? $price : null;
}
add_filter('ahc_inline_recomputed_sale_price', 'ahc_sp_pricing_jpy', 20, 5);
