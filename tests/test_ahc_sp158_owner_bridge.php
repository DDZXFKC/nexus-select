<?php
/** PHP CLI: offline integration with real 1713-row verified SP CSV. */
define('ABSPATH','/');
define('AHC_SP158_VERIFIED_CSV', dirname(__DIR__) .
    '/data/xserver-export/sp158-live-sku-match-2026-11-22.csv');
$GLOBALS['hooks'] = [];
function add_filter($name,$fn,$priority=10,$args=1) { $GLOBALS['hooks'][$name][]=$fn; }
// Fixture simulates separate, already-reviewed route-cost coverage.
// No production filter returns true without a private approval manifest.
function apply_filters($name,$prev,...$args) {
    return $name === 'ahc_sp158_live_cost_coverage_verified' ? true : $prev;
}
function wp_parse_url($url) { return parse_url($url); }
class SP158FakeProduct {
    private $type; private $sku; private $parent;
    public function __construct($type,$sku,$parent=0) {
        $this->type=$type;$this->sku=$sku;$this->parent=$parent;
    }
    public function is_type($type) { return $this->type===$type; }
    public function get_sku() { return $this->sku; }
    public function get_parent_id() { return $this->parent; }
}
function wc_get_product($id) { return $GLOBALS['products'][$id] ?? false; }
require __DIR__.'/../tools/ahc-stock-sp158-owner-bridge-staging.php';
function check($description,$value) {
    if (!$value) throw new RuntimeException($description);
    echo 'PASS '.$description."\n";
}
$map = ahc_sp158_evidence(AHC_SP158_VERIFIED_CSV);
check('entire evidence file loaded',is_array($map) && count($map)===1713);
$parents=[];$merchant=[];$stock=0;$sum=0;
foreach ($map as $row) {
    $parents[$row['product_id']]=true;
    $merchant[$row['supplier_product_id'].':'.$row['shopify_variant_id_live']]=true;
    $stock += ($row['available_live']==='1')?1:0;
    $sum += (int)$row['price_cents_live'];
}
check('158 products and 1713 unique Shopify variants',
    count($parents)===158 && count($merchant)===1713);
check('supplier snapshot integrity', $stock===804 && $sum===23508531);
$first=reset($map);
$pid=(int)$first['product_id'];$vid=(int)$first['variation_id'];
$GLOBALS['products']=[
    $pid=>new SP158FakeProduct('variable',$first['parent_sku']),
    $vid=>new SP158FakeProduct('variation',$first['woo_variation_sku'],$pid)
];
$offers=ahc_sp158_owner_offers([],$pid,$vid,[]);
check('real row creates exact supplier offer',count($offers)===1 &&
    $offers[0]['supplier_product_id']===$first['supplier_product_id'] &&
    $offers[0]['merchant_variant_id']===$first['shopify_variant_id_live'] &&
    $offers[0]['merchant_variant_sku']===$first['woo_variation_sku']);
check('snapshot OOS never prevents live inquiry',
    $first['available_live']==='0' ? count($offers)===1 : true);
check('no inferred Woo identity',
    ahc_sp158_owner_offers([],$pid,$vid+400000,[])===[]);
$GLOBALS['products'][$vid]=new SP158FakeProduct('variation','WRONG-SKU',$pid);
check('changed Woo SKU denied',
    ahc_sp158_owner_offers([],$pid,$vid,[])===[]);
$GLOBALS['products'][$vid]=new SP158FakeProduct('variation',$first['woo_variation_sku'],$pid);
check('owner 100 USD price exactly 25400 JPY',
    ahc_sp158_sale_price_from_cents(10000)===25400);
check('owner 125.99 USD price exactly 30700 JPY',
    ahc_sp158_sale_price_from_cents(12599)===30700);
check('invalid supplier price denied',
    ahc_sp158_sale_price_from_cents(0)===null &&
    ahc_sp158_sale_price_from_cents(-1)===null);
$live=['amount'=>'100.00','currency'=>'USD'];
check('current price overrides historical snapshot',
    ahc_sp158_owner_price(null,$live,$offers[0],$pid,$vid)===25400);
$live['currency']='EUR';
check('incorrect currency denied',
    ahc_sp158_owner_price(null,$live,$offers[0],$pid,$vid)===null);
$live=['amount'=>'100.00','currency'=>'USD'];
$bad=$offers[0];$bad['merchant_variant_id']='0';
check('price rejects supplier variant mismatch',
    ahc_sp158_owner_price(null,$live,$bad,$pid,$vid)===null);
check('missing evidence rejects price',
    ahc_sp158_owner_price(null,$live,$offers[0],$pid,$vid+123456)===null);
check('prior SP price cannot override verified owner formula',
    ahc_sp158_owner_price(33333,$live,$offers[0],$pid,$vid)===25400);
check('merchant URL confined to official product handles',
    !ahc_sp158_valid_url('https://www.shoepalace.com.evil.test/products/foo') &&
    !ahc_sp158_valid_url('https://www.shoepalace.com/products/foo?redirect=evil'));

/** Strict validation of corrupted copies (never touch authoritative file). */
function tampered($modify) {
    $lines=file(AHC_SP158_VERIFIED_CSV);
    $modify($lines);
    $file=tempnam(sys_get_temp_dir(),'sp158-fixture-');
    file_put_contents($file,implode('',$lines));
    return $file;
}
$partial=tampered(function (&$lines) {array_pop($lines);});
check('partial CSV rejected',ahc_sp158_evidence($partial)===null);
unlink($partial);
$duplicate=tampered(function (&$lines) {$lines[count($lines)-1]=$lines[1];});
check('duplicate row rejected',ahc_sp158_evidence($duplicate)===null);
unlink($duplicate);
$wrong=tampered(function (&$lines) {
    $parts=str_getcsv($lines[1]);$parts[7]='FORGED-SKU';
    $lines[1]=implode(',',array_map(fn($v)=>$v,$parts))."\n";
});
check('supplier SKU tamper rejected',ahc_sp158_evidence($wrong)===null);
unlink($wrong);
echo "20 scenarios PASS\n";
