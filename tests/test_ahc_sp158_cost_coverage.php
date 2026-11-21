<?php
/** Strict offline test: 1713 official SKU evidence + PRIVATE cost approval. */
define('ABSPATH','/');
define('AHC_SP158_VERIFIED_CSV',dirname(__DIR__).'/data/xserver-export/sp158-live-sku-match-2026-11-22.csv');
$GLOBALS['hooks']=[];
function wp_parse_url($u){return parse_url($u);}
function add_filter($name,$fn,$priority=10,$args=1){
    $GLOBALS['hooks'][$name][]=['fn'=>$fn,'priority'=>$priority];
}
function apply_filters($name,$previous,...$arguments){
    $hooks=$GLOBALS['hooks'][$name]??[];
    usort($hooks,fn($a,$b)=>$a['priority']<=>$b['priority']);
    foreach($hooks as $hook)$previous=($hook['fn'])($previous,...$arguments);
    return $previous;
}
require dirname(__DIR__).'/tools/ahc-stock-sp158-owner-bridge-staging.php';
require dirname(__DIR__).'/tools/ahc-stock-sp158-cost-coverage-provider.php';
function ok($n,$v){if(!$v)throw new RuntimeException($n);echo "PASS ".$n."\n";}
$rows=ahc_sp158_evidence(AHC_SP158_VERIFIED_CSV);
$row=reset($rows);
$keys=['source_domestic_shipping','source_sales_tax',
    'international_shipping','japan_domestic_shipping','customs_duty',
    'import_consumption_tax','partner_fee','packaging',
    'payment_processing','other_mandatory_fees'];
$fees=[];
foreach($keys as $key){
    $fees[$key]=[
        'status'=>'reviewed_covered_or_not_applicable',
        'evidence_ref'=>'FIXTURE-ONLY:'.$key,
        'explanation'=>'Test-only artificial coverage; never suitable for production'
    ];
}
$pid=$row['product_id'];$vid=$row['variation_id'];
$entry=[
    'product_id'=>$pid,'variation_id'=>$vid,
    'supplier_product_id'=>$row['supplier_product_id'],
    'merchant_variant_id'=>$row['shopify_variant_id_live'],
    'merchant_variant_sku'=>$row['woo_variation_sku'],
    'source_url'=>$row['source_url'],'reviewed_price_usd'=>'100.00',
    'formula_coverage_approved'=>true,
    'route_ref'=>'TEST-ONLY:NOT-A-REAL-ROUTE',
    'fee_coverage'=>$fees
];
$document=[
    'schema'=>'ahc.sp158.cost-coverage.v1',
    'approved_for'=>'AFTER HOURS CLUB',
    'shop'=>'SP','owner_formula'=>'USDx158x1.02+2200+1500+60/div0.785-ceil100',
    'source_currency'=>'USD','ahc_channel_divisor_confirmed'=>true,
    'approver_ref'=>'TEST-ONLY-NOT-OWNER-APPROVAL',
    'approvals'=>[$pid.':'.$vid=>$entry],
];
$file=tempnam(sys_get_temp_dir(),'ahc-sp158-cost-');
file_put_contents($file,json_encode($document, JSON_THROW_ON_ERROR));
define('AHC_SP158_COST_COVERAGE_FILE',$file);
define('AHC_SP158_COST_COVERAGE_SHA256',hash_file('sha256',$file));
$context=[
    'shop'=>'SP','product_id'=>(int)$pid,'variation_id'=>(int)$vid,
    'supplier_product_id'=>$row['supplier_product_id'],
    'merchant_variant_id'=>$row['shopify_variant_id_live'],
    'merchant_variant_sku'=>$row['woo_variation_sku'],
    'source_url'=>$row['source_url'],'source_price_usd'=>'100.00',
    'currency'=>'USD'
];
function verified($ctx){return apply_filters('ahc_sp158_live_cost_coverage_verified',false,$ctx);}
try{
    ok('scoped owner price formula remains exact',ahc_sp158_sale_price_from_cents(10000)===25400);
    ok('test-only all-fee manifest accepted for matching evidence',verified($context)===true);
    $wrong=$context;$wrong['merchant_variant_id']='1';
    ok('wrong Shopify variant rejects cost',verified($wrong)===false);
    $wrong=$context;$wrong['source_price_usd']='100.01';
    ok('changed live price rejects old cost review',verified($wrong)===false);
    $wrong=$context;$wrong['source_url'].='?foo=1';
    ok('invalid merchant URL rejects cost',verified($wrong)===false);
    $wrong=$context;$wrong['merchant_variant_sku']='fake';
    ok('wrong variant SKU rejects cost',verified($wrong)===false);
    $wrong=$context;$wrong['product_id']=80000000;
    ok('missing SKU review rejects cost',verified($wrong)===false);
    $wrong=$context;$wrong['shop']='OTHER';
    ok('other shop cannot inherit approval',verified($wrong)===false);
    $offer=['shop'=>'SP','identity_verified'=>true,'verified_currency'=>'USD',
        'supplier_product_id'=>$row['supplier_product_id'],
        'merchant_variant_id'=>$row['shopify_variant_id_live'],
        'merchant_variant_sku'=>$row['woo_variation_sku'],
        'url'=>$row['source_url']];
    $live=['amount'=>'100.00','currency'=>'USD'];
    ok('approved covered exact live price yields 25400',
        ahc_sp158_owner_price(null,$live,$offer,(int)$pid,(int)$vid)===25400);
    $live['amount']='100.01';
    ok('recomputed current supplier price cannot inherit stale cost approval',
        ahc_sp158_owner_price(null,$live,$offer,(int)$pid,(int)$vid)===null);
    $live['amount']='100.00';$live['currency']='EUR';
    ok('unverified currency rejected',ahc_sp158_owner_price(null,$live,$offer,(int)$pid,(int)$vid)===null);
    $live['currency']='USD';
    $bad=$offer;$bad['merchant_variant_id']='123';
    ok('wrong merchant identity rejected',ahc_sp158_owner_price(null,$live,$bad,(int)$pid,(int)$vid)===null);
    ok('no coverage supplied for another SKU',
        ahc_sp158_owner_price(null,$live,$offer,(int)$pid,(int)$vid+1)===null);
    // A JSON change invalidates the pinned SHA even if it remains parseable.
    file_put_contents($file, json_encode(array_merge($document,['approver_ref'=>'FORGED']),JSON_THROW_ON_ERROR));
    ok('any unapproved manifest edit is rejected',verified($context)===false);
    ok('changed manifest prevents even an old exact live price permit',
        ahc_sp158_owner_price(null,$live,$offer,(int)$pid,(int)$vid)===null);
    ok('prior unreviewed SP price cannot bypass missing cost coverage',
        ahc_sp158_owner_price(33333,$live,$offer,(int)$pid,(int)$vid)===null);
    echo "16 scoped cost coverage cases PASS\n";
} finally {
    unlink($file);
}
