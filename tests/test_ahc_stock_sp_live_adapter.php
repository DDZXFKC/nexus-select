<?php
/** Standalone PHP CLI tests: php tests/test_ahc_stock_sp_live_adapter.php */
define('ABSPATH', '/');
$GLOBALS['calls'] = 0;
class AHCSPFakeProduct {
    private $type; private $sku; private $parent;
    function __construct($type,$sku,$parent=0){$this->type=$type;$this->sku=$sku;$this->parent=$parent;}
    function is_type($type){return $this->type===$type;}
    function get_sku(){return $this->sku;}
    function get_parent_id(){return $this->parent;}
}
function add_filter(...$args){}
function wc_get_product($id) {
    if ($id===100) return new AHCSPFakeProduct('variable','SP-123');
    if ($id===101) return new AHCSPFakeProduct('variation','SKU5',100);
    return false;
}
function wp_parse_url($url){return parse_url($url);}
function wp_safe_remote_get($url,$opts) {
    $GLOBALS['calls']++;
    $GLOBALS['requested_url']=$url;
    $GLOBALS['request_options']=$opts;
    return $GLOBALS['response'];
}
function is_wp_error($response){return false;}
function wp_remote_retrieve_response_code($response){return $response['status'];}
function wp_remote_retrieve_body($response){return $response['body'];}
require __DIR__ . '/../tools/ahc-stock-sp-live-adapter-staging.php';
function offer() {return [
    'shop'=>'SP','url'=>'https://www.shoepalace.com/products/test-shoe',
    'supplier_product_id'=>'123','merchant_variant_id'=>'900',
    'merchant_variant_sku'=>'SKU5','identity_verified'=>true,
    'verified_currency'=>'USD'
];}
function check($offer){return ahc_sp_live_check_offer(null,$offer,100,101,[]);}
function eq($actual,$expected,$description) {
    if ($actual!==$expected) throw new RuntimeException($description.' expected '.var_export($expected,true).' got '.var_export($actual,true));
}
function fixture($available,$price,$sku='SKU5') {
    $GLOBALS['response']=['status'=>200,'body'=>json_encode([
        'id'=>123,'variants'=>[['id'=>900,'sku'=>$sku,'available'=>$available,'price'=>$price]]
    ])];
}
fixture(true,12599);
$r=check(offer());
eq($r['stock'],'IN_STOCK','valid live variant');
eq($r['current_price']['amount'],'125.99','Shopify cents');
eq($GLOBALS['requested_url'],'https://www.shoepalace.com/products/test-shoe.js','endpoint');
eq($GLOBALS['request_options']['redirection'],0,'never redirect');
fixture(false,12599);eq(check(offer())['stock'],'OUT_OF_STOCK','out of stock');
fixture(true,12599,'WRONG');eq(check(offer())['stock'],'UNCONFIRMED','wrong SKU');
fixture(true,null);eq(check(offer())['stock'],'UNCONFIRMED','unknown price');
$before=$GLOBALS['calls'];
$o=offer();$o['url']='https://www.shoepalace.com.evil.invalid/products/test';
eq(check($o)['stock'],'UNCONFIRMED','unsafe host');eq($GLOBALS['calls'],$before,'must not request unsafe host');
$o=offer();$o['verified_currency']='';eq(check($o)['reason'],'currency_unverified','no verified currency');
$o=offer();$o['identity_verified']=false;eq(check($o)['stock'],'UNCONFIRMED','unverified identity');
$GLOBALS['response']=['status'=>429,'body'=>''];eq(check(offer())['stock'],'UNCONFIRMED','rate-limited');
echo "8 scenarios PASS\n";
