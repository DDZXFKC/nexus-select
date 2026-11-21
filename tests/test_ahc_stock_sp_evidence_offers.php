<?php
/** CLI isolated tests for Shoe Palace verified-offer source. No WordPress required. */
define('ABSPATH', '/');
$GLOBALS['pricing_estimate'] = null;
$GLOBALS['verified_currency'] = null;
class ProductMock {
    private $type; private $sku; private $parent;
    function __construct($type,$sku,$parent=0){$this->type=$type;$this->sku=$sku;$this->parent=$parent;}
    function is_type($t){return $t===$this->type;}
    function get_parent_id(){return $this->parent;}
    function get_sku(){return $this->sku;}
}
function wc_get_product($id) {
    if ($id===100) return new ProductMock('variable','SP-123');
    if ($id===101) return new ProductMock('variation','21141139',100);
    return false;
}
function wp_parse_url($s){return parse_url($s);}
function add_filter(...$args){}
function apply_filters($name,$default,$meta) {
    if ($name==='ahc_sp_verified_landed_estimate_jpy') return $GLOBALS['pricing_estimate'];
    if ($name==='ahc_sp_verified_store_currency') return $GLOBALS['verified_currency'];
    throw new RuntimeException('unexpected filter');
}
require __DIR__.'/../tools/ahc-stock-sp-evidence-offers-staging.php';
function same($a,$b,$msg){if($a!==$b)throw new RuntimeException($msg.' '.var_export($a,true));}
function runOffers() {return ahc_sp_offers_from_evidence([],100,101,[]);}
function writeFixture($rows) {
    $path=tempnam(sys_get_temp_dir(),'ahcsp');
    $f=fopen($path,'wb');
    $columns=['product_id','variation_id','shop_code','supplier_product_id','source_url',
              'merchant_variant_id','status','merchant_variant_sku','woo_variation_sku',
              'sku_evidence','sku_verified_at_utc'];
    fputcsv($f,$columns);
    foreach($rows as $row) fputcsv($f,$row);
    fclose($f);
    return $path;
}
function witness() {
    return ['100','101','SP','123','https://www.shoepalace.com/products/test-shoe',
            '900','verified','21141139','21141139','shopify SKU observed','2026-11-21T10:03:00Z'];
}
$path=writeFixture([witness()]);
define('AHC_SP_EVIDENCE_CSV',$path);
try {
    same(runOffers(),[],'default deny with missing costs');
    $GLOBALS['pricing_estimate']=13000;
    same(runOffers(),[],'currency missing denies offer');
    $GLOBALS['verified_currency']='USD';
    $a=runOffers();same(count($a),1,'verified offer created');
    same($a[0]['merchant_variant_id'],'900','variant ID retained');
    same($a[0]['estimated_total_jpy'],13000,'estimated price kept');
    $GLOBALS['pricing_estimate']='13000';same(runOffers(),[],'string cost blocked');
    $GLOBALS['pricing_estimate']=13000;
    $bad=witness();$bad[7]='WRONG';
    file_put_contents($path,file_get_contents(writeFixture([$bad])));same(runOffers(),[],'bad supplier sku blocked');
    file_put_contents($path,file_get_contents(writeFixture([witness(),witness()])));
    same(runOffers(),[],'duplicate evidence blocked');
    $bad=witness();$bad[4]='https://www.shoepalace.com.evil.test/products/test';
    file_put_contents($path,file_get_contents(writeFixture([$bad])));same(runOffers(),[],'evil host blocked');
    $bad=witness();$bad[6]='pending';
    file_put_contents($path,file_get_contents(writeFixture([$bad])));same(runOffers(),[],'unverified row blocked');
    $bad=witness();$bad[5]='';
    file_put_contents($path,file_get_contents(writeFixture([$bad])));same(runOffers(),[],'missing variant ID blocked');
    file_put_contents($path,file_get_contents(writeFixture([witness()])));
    same(ahc_sp_offers_from_evidence([],100,999,[]),[],'wrong woo variation blocked');
    echo "10 scenarios PASS\n";
} finally {unlink($path);}
