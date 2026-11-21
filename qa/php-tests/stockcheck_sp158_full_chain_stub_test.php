<?php
/** Offline full Woo AJAX → SP158 evidence → mocked merchant → owner pricing → cart. */
define('ABSPATH','/');
define('AHC_SP158_VERIFIED_CSV', dirname(__DIR__,2) .
    '/data/xserver-export/sp158-live-sku-match-2026-11-22.csv');
define('DAY_IN_SECONDS',86400);define('HOUR_IN_SECONDS',3600);define('MINUTE_IN_SECONDS',60);
$HOOKS=[];$TRANSIENTS=[];$META=[];$OPTIONS=[];$PRODUCTS=[];$HTTP=[];
function add_filter($name,$fn,$priority=10,$args=1) {
    $GLOBALS['HOOKS'][$name][]=['callback'=>$fn,'priority'=>$priority];
}
function add_action($name,$fn,$priority=10,$args=1){add_filter($name,$fn,$priority,$args);}
function apply_filters($name,$result,...$args) {
    $callbacks=$GLOBALS['HOOKS'][$name]??[];
    usort($callbacks,fn($a,$b)=>$a['priority']<=>$b['priority']);
    foreach($callbacks as $item)$result=($item['callback'])($result,...$args);
    return $result;
}
function wp_parse_url($url){return parse_url($url);}
function check_ajax_referer($action,$key,$die=true){return ($action==='ahc_sc_inline' && ($_POST[$key]??'')==='valid')?1:false;}
function sanitize_text_field($x){return trim((string)$x);}
function sanitize_key($x){return preg_replace('/[^a-z0-9_-]/','',strtolower((string)$x));}
function wp_unslash($x){return $x;}
function absint($x){return abs((int)$x);}
function get_transient($key){return $GLOBALS['TRANSIENTS'][$key]??false;}
function set_transient($key,$val,$ttl){$GLOBALS['TRANSIENTS'][$key]=$val;}
function delete_transient($key){unset($GLOBALS['TRANSIENTS'][$key]);}
function get_post_meta($id,$key,$single=true){return $GLOBALS['META'][$id][$key]??null;}
function update_post_meta($id,$key,$v){$GLOBALS['META'][$id][$key]=$v;}
function add_option($key,$value,$deprecated='',$autoload=false) {
    if(isset($GLOBALS['OPTIONS'][$key]))return false;
    $GLOBALS['OPTIONS'][$key]=$value;return true;
}
function delete_option($key){unset($GLOBALS['OPTIONS'][$key]);}
function wp_next_scheduled($name){return true;}
function wp_schedule_event($at,$cadence,$name){}
function wp_salt($name){return 'local-test-only';}
function wc_add_notice($msg,$kind='error'){}
function wc_get_cart_url(){return 'https://example.test/cart';}
class JSONResponse extends Exception { public $ok,$payload; }
function wp_send_json_success($payload){$e=new JSONResponse();$e->ok=true;$e->payload=$payload;throw $e;}
function wp_send_json_error($payload,$status=400){$e=new JSONResponse();$e->ok=false;$e->payload=$payload;throw $e;}
class Product {
    public $id,$type,$sku,$parent,$attrs,$price;
    function __construct($id,$type,$sku,$parent=0,$attrs=[],$price='25000') {
        $this->id=$id;$this->type=$type;$this->sku=$sku;$this->parent=$parent;$this->attrs=$attrs;$this->price=$price;
    }
    function get_id(){return $this->id;}
    function get_sku(){return $this->sku;}
    function is_type($type){return $this->type===$type;}
    function get_parent_id(){return $this->parent;}
    function get_status(){return 'publish';}
    function is_visible(){return true;}
    function get_price(){return $this->price;}
    function get_variation_attributes(){return $this->attrs;}
    function is_purchasable(){return true;}
    function is_in_stock(){return true;}
    function set_price($v){$this->price=(string)$v;}
}
function wc_get_product($id){return $GLOBALS['PRODUCTS'][$id]??false;}
class Session {
    public $id='';
    function get_customer_id(){return $this->id;}
    function set_customer_session_cookie($enabled){$this->id='buyer-unique-session';}
}
class Cart {
    public $lines=[];
    function add_to_cart($pid,$quantity,$vid,$attrs){
        if(!apply_filters('woocommerce_add_to_cart_validation',true,$pid,$quantity,$vid,$attrs))return false;
        $data=apply_filters('woocommerce_add_cart_item_data',[],$pid,$vid,$quantity);
        if(empty($data['ahc_inline_sig']))return false;
        $this->lines[]=array_merge($data,['product_id'=>$pid,'variation_id'=>$vid,
                                            'data'=>wc_get_product($vid)]);
        return 'line';
    }
    function get_cart(){return $this->lines;}
}
class WCEnv { public $session,$cart;
    function __construct(){$this->session=new Session();$this->cart=new Cart();}
}
$GLOBALS['WCENV']=new WCEnv();
function WC(){return $GLOBALS['WCENV'];}
function wp_safe_remote_get($url,$opts) {
    $GLOBALS['HTTP'][]=['url'=>$url,'options'=>$opts];
    return $GLOBALS['MERCHANT'];
}
function is_wp_error($r){return false;}
function wp_remote_retrieve_response_code($r){return $r['status'];}
function wp_remote_retrieve_body($r){return $r['body'];}
require __DIR__.'/../../tools/ahc-stock-inline-endpoints-staging.php';
require __DIR__.'/../../tools/ahc-stock-sp158-owner-bridge-staging.php';
require __DIR__.'/../../tools/ahc-stock-sp-live-adapter-staging.php';

function expect($what,$truth){if(!$truth)throw new RuntimeException($what);echo 'PASS '.$what."\n";}
function request($function,$data=[]){
    $_POST=array_merge(['nonce'=>'valid'],$data);
    try {$function();}catch(JSONResponse $e){return $e;}
    throw new RuntimeException('missing JSON response');
}
$rows=ahc_sp158_evidence(AHC_SP158_VERIFIED_CSV);
$row=reset($rows);$pid=(int)$row['product_id'];$vid=(int)$row['variation_id'];
$attrs=['attribute_pa_size'=>'9'];
$GLOBALS['PRODUCTS'][$pid]=new Product($pid,'variable',$row['parent_sku']);
$GLOBALS['PRODUCTS'][$vid]=new Product($vid,'variation',$row['woo_variation_sku'],$pid,$attrs,'25000');
function merchant($stock, $cents=12599) {
    global $row;
    $GLOBALS['MERCHANT']=['status'=>200,'body'=>json_encode([
        'id'=>(int)$row['supplier_product_id'],
        'variants'=>[['id'=>(int)$row['shopify_variant_id_live'],
            'sku'=>$row['shopify_variant_sku_live'],'available'=>$stock,'price'=>$cents]]
    ])];
}
function start_check(){
    global $pid,$vid,$attrs;
    return request('ahc_inline_start',array_merge(['product_id'=>$pid,'variation_id'=>$vid],$attrs));
}
merchant(true);
expect('direct cart blocked',
    !apply_filters('woocommerce_add_to_cart_validation',true,$pid,1,$vid,$attrs));
$started=start_check();
expect('genuine Woo selection starts authenticated guest check',$started->ok);
$step=request('ahc_inline_step',['check_id'=>$started->payload['check_id']]);
expect('live store price used instead of 2026-11-21 snapshot',
    $step->ok && $step->payload['result']==='in_stock' &&
    $step->payload['price_case']==='quote' &&
    $step->payload['quote_price_text']==='¥30,700');
expect('supplier contacted only once at official .js URL',
    count($GLOBALS['HTTP'])===1 &&
    $GLOBALS['HTTP'][0]['url']===$row['source_url'].'.js' &&
    $GLOBALS['HTTP'][0]['options']['redirection']===0);
$deny=request('ahc_inline_add_to_cart',['permit'=>$step->payload['permit']]);
expect('higher price needs explicit consent',!$deny->ok &&
    $deny->payload['code']==='quote_not_accepted');
$add=request('ahc_inline_add_to_cart',['permit'=>$step->payload['permit'],'accept_quote'=>'1']);
expect('signed quote is bound to correct variation and price',
    $add->ok && count(WC()->cart->lines)===1 &&
    end(WC()->cart->lines)['variation_id']===$vid &&
    end(WC()->cart->lines)['ahc_inline_price']===30700);
$again=request('ahc_inline_add_to_cart',['permit'=>$step->payload['permit'],'accept_quote'=>'1']);
expect('one-use permit cannot be replayed',!$again->ok);
$GLOBALS['TRANSIENTS']=[];$GLOBALS['WCENV']->session=new Session();$GLOBALS['HTTP']=[];
merchant(false);
$started=start_check();
$step=request('ahc_inline_step',['check_id'=>$started->payload['check_id']]);
expect('real supplier sold-out result never authorizes purchase',
    $step->ok && $step->payload['result']==='out_of_stock' &&
    empty($step->payload['permit']));
$GLOBALS['META'][$vid]['_ahc_inline_oos_until']=time()+86400;
$GLOBALS['TRANSIENTS']=[];$GLOBALS['WCENV']->session=new Session();$GLOBALS['HTTP']=[];
// USD 99.00 yields an owner-formula increase below JPY 400; listed price stays.
merchant(true,9900);
$started=start_check();
$step=request('ahc_inline_step',['check_id'=>$started->payload['check_id']]);
expect('restock immediately overrides even leftover legacy 24h mark',
    $started->ok && $step->ok && $step->payload['result']==='in_stock' &&
    $step->payload['price_case']==='listed');
echo "9 full-chain scenarios PASS\n";
