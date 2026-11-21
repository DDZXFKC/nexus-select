<?php
/** Standalone PHP CLI tests: php tests/test_ahc_stock_sp_pricing.php */
define('ABSPATH', '/');
function add_filter(...$args) {}
$GLOBALS['cost_inputs'] = null;
function apply_filters($name, $default, ...$args) {
    if ($name !== 'ahc_sp_verified_live_cost_inputs') throw new RuntimeException('unexpected hook');
    return $GLOBALS['cost_inputs'];
}
require dirname(__DIR__) . '/tools/ahc-stock-sp-pricing-staging.php';
function expectEq($actual,$expected,$label) {
    if ($actual!==$expected) throw new RuntimeException($label.' got '.var_export($actual,true).' expected '.var_export($expected,true));
}
function baseInput() {
    $costs=[
        'local_sales_tax'=>100,'local_delivery'=>200,
        'international_shipping'=>1500,'domestic_shipping'=>600,
        'customs_duty'=>300,'import_consumption_tax'=>1000,
        'partner_fee'=>2000,'packaging'=>100,'other_fees'=>0
    ];
    return [
        'approved'=>true,'shop'=>'SP',
        'supplier_product_id'=>'123','merchant_variant_id'=>'900',
        'merchant_variant_sku'=>'SKU5','source_price_usd'=>'125.99',
        'source_ref'=>'live-sp-fixture:2026','observed_at'=>time(),
        'fx_jpy_per_usd_x10000'=>1500000,'fx_observed_at'=>time(),
        'costs_jpy'=>$costs,
        'verified_zero_reasons'=>['other_fees'=>'reviewed explicitly zero for this route'],
        'required_profit_jpy'=>3000,'payment_fee_bps'=>325,
        'payment_fixed_jpy'=>0,'round_up_jpy'=>100,
        'pricing_policy_ref'=>'owner-approved-test-fixture-only'
    ];
}
function price() {
    return ahc_sp_pricing_jpy(['amount'=>'125.99','currency'=>'USD'],[
        'shop'=>'SP','identity_verified'=>true,
        'supplier_product_id'=>'123','merchant_variant_id'=>'900',
        'merchant_variant_sku'=>'SKU5'
    ],100,101);
}
$GLOBALS['cost_inputs']=baseInput();
// Purchase 18,899 + costs 5,800 + profit 3,000 => 27,699 / .9675 -> round 28,700
expectEq(price(),28700,'exact conversion and rounding');
foreach (['local_sales_tax','international_shipping','customs_duty','import_consumption_tax','partner_fee','domestic_shipping','other_fees'] as $field) {
    $GLOBALS['cost_inputs']=baseInput();
    unset($GLOBALS['cost_inputs']['costs_jpy'][$field]);
    expectEq(price(),null,'missing cost '.$field);
}
$GLOBALS['cost_inputs']=baseInput();unset($GLOBALS['cost_inputs']['verified_zero_reasons']['other_fees']);
expectEq(price(),null,'unjustified zero');
$GLOBALS['cost_inputs']=baseInput();$GLOBALS['cost_inputs']['payment_fee_bps']=null;
expectEq(price(),null,'unknown payment fee');
$GLOBALS['cost_inputs']=baseInput();$GLOBALS['cost_inputs']['approved']=false;
expectEq(price(),null,'unapproved input');
$GLOBALS['cost_inputs']=baseInput();$GLOBALS['cost_inputs']['merchant_variant_id']='901';
expectEq(price(),null,'wrong supplier variant');
$GLOBALS['cost_inputs']=baseInput();$GLOBALS['cost_inputs']['source_price_usd']='125.98';
expectEq(price(),null,'outdated price');
$GLOBALS['cost_inputs']=baseInput();$GLOBALS['cost_inputs']['observed_at']=time()-400;
expectEq(price(),null,'stale source');
$GLOBALS['cost_inputs']=baseInput();$GLOBALS['cost_inputs']['fx_observed_at']=time()-4000;
expectEq(price(),null,'stale exchange rate');
$GLOBALS['cost_inputs']=baseInput();$GLOBALS['cost_inputs']['costs_jpy']['local_sales_tax']='0';
expectEq(price(),null,'string cost');
$GLOBALS['cost_inputs']=baseInput();$GLOBALS['cost_inputs']['payment_fee_bps']=10000;
expectEq(price(),null,'invalid card fee');
$GLOBALS['cost_inputs']=baseInput();$GLOBALS['cost_inputs']['round_up_jpy']=0;
expectEq(price(),null,'rounding unset');
echo "19 cases PASS\n";
