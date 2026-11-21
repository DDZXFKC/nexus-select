<?php
/** Isolated API integration test (NO WordPress or external merchant requests). */
define('ABSPATH', '/');
define('DAY_IN_SECONDS', 86400);
define('HOUR_IN_SECONDS', 3600);
define('MINUTE_IN_SECONDS', 60);
$HOOKS=[]; $TR=[]; $META=[]; $OPTIONS=[]; $PRODUCTS=[]; $NOTICES=[]; $CALLS=[]; $SIM='ok';
function add_filter($h,$fn,$priority=10,$args=1) { global $HOOKS; $HOOKS[$h][]=['fn'=>$fn,'priority'=>$priority]; }
function add_action($h,$fn,$priority=10,$args=1) { add_filter($h,$fn,$priority,$args); }
function apply_filters($h,$value,...$args) {
    global $HOOKS; $callbacks=$HOOKS[$h]??[];
    usort($callbacks,fn($a,$b)=>$a['priority']<=>$b['priority']);
    foreach($callbacks as $cb) $value=($cb['fn'])($value,...$args);
    return $value;
}
function do_action($h,...$args) {
    global $HOOKS; $callbacks=$HOOKS[$h]??[];
    usort($callbacks,fn($a,$b)=>$a['priority']<=>$b['priority']);
    foreach($callbacks as $cb) ($cb['fn'])(...$args);
}
class Finished extends Exception { public $ok,$data,$status; }
function wp_send_json_success($d) { $e=new Finished(); $e->ok=true; $e->data=$d; throw $e; }
function wp_send_json_error($d,$status=400) { $e=new Finished(); $e->ok=false; $e->data=$d; $e->status=$status; throw $e; }
function check_ajax_referer($action,$field,$die=true) { return ($action==='ahc_sc_inline' && ($_POST[$field]??'')==='valid')?1:false; }
function sanitize_text_field($v) { return trim((string)$v); }
function sanitize_key($v) { return preg_replace('/[^a-z0-9_\-]/','',strtolower((string)$v)); }
function wp_unslash($v) { return $v; }
function absint($v) { return abs((int)$v); }
function get_post_meta($id,$k,$single=true) { global $META; return $META[$id][$k]??''; }
function update_post_meta($id,$k,$v) { global $META; $META[$id][$k]=$v; }
function get_transient($k) { global $TR; return $TR[$k]??false; }
function set_transient($k,$v,$ttl) { global $TR; $TR[$k]=$v; }
function delete_transient($k) { global $TR; unset($TR[$k]); }
function add_option($key,$v,$deprecated='',$autol=false) { global $OPTIONS; if(array_key_exists($key,$OPTIONS))return false; $OPTIONS[$key]=$v;return true; }
function delete_option($key) { global $OPTIONS; unset($OPTIONS[$key]); }
function wp_next_scheduled($event) { return true; }
function wp_schedule_event($timestamp,$frequency,$event) {}
function wp_salt($name) { return 'secret-test-site-salt'; }
function wc_add_notice($text,$type='error') { global $NOTICES; $NOTICES[]=$text; }
function wc_get_cart_url() { return 'https://example.test/cart/'; }
class FakeSession {
  public $cookie=false; public $id='';
  function set_customer_session_cookie($bool) {$this->cookie=$bool; $this->id='guest-persisted-1234';}
  function get_customer_id() { return $this->id; }
}
class FakeProduct {
  public $id,$type,$parent,$status='publish',$price='25000',$attrs=[];
  function __construct($id,$type,$parent=0,$attrs=[]) {$this->id=$id;$this->type=$type;$this->parent=$parent;$this->attrs=$attrs;}
  function get_id(){return $this->id;}
  function get_sku(){return $this->id===10?'SP-123':($this->id===11?'SKU5':'');}
  function get_status(){return $this->status;}
  function is_visible(){return true;}
  function is_type($type){return $this->type===$type;}
  function get_parent_id(){return $this->parent;}
  function get_variation_attributes(){return $this->attrs;}
  function get_price(){return $this->price;}
  function is_purchasable(){return true;}
  function is_in_stock(){return true;}
  function set_price($p){$this->price=(string)$p;}
}
class FakeCart {
  public $lines=[];
  function add_to_cart($pid,$qty,$vid,$attrs) {
    if (!apply_filters('woocommerce_add_to_cart_validation',true,$pid,$qty,$vid,$attrs))return false;
    $extra=apply_filters('woocommerce_add_cart_item_data',[],$pid,$vid,$qty);
    if (!isset($extra['ahc_inline_sig']))return false;
    $this->lines[]=array_merge(['product_id'=>$pid,'variation_id'=>$vid,
       'data'=>wc_get_product($vid?:$pid)],$extra);
    return 'key';
  }
  function get_cart(){return $this->lines;}
}
class FakeWC {public $session,$cart;function __construct(){$this->session=new FakeSession();$this->cart=new FakeCart();}}
$W=new FakeWC();
function WC(){global $W;return $W;}
function wc_get_product($id){global $PRODUCTS;return $PRODUCTS[$id]??null;}
$PRODUCTS[10]=new FakeProduct(10,'variable');
$PRODUCTS[11]=new FakeProduct(11,'variation',10,['attribute_pa_size'=>'9','attribute_pa_color'=>'black']);
$PRODUCTS[12]=new FakeProduct(12,'variation',10,['attribute_pa_size'=>'','attribute_pa_color'=>'black']);
$PRODUCTS[20]=new FakeProduct(20,'simple');
require __DIR__.'/../../tools/ahc-stock-inline-endpoints-staging.php';

/* Integrated provider fixture — no external requests, no site writes. */
function wp_parse_url($s){return parse_url($s);}
function is_wp_error($r){return false;}
function wp_safe_remote_get($url,$opts) {
    global $SCENARIO,$HTTP_CALLS;
    $HTTP_CALLS++;
    if ($url!=='https://www.shoepalace.com/products/test-shoe.js')
        throw new RuntimeException('Unexpected supplier URL '.$url);
    if (($opts['redirection']??1)!==0) throw new RuntimeException('Redirects must be disabled');
    if ($SCENARIO==='http429') return ['status'=>429,'body'=>''];
    $available=$SCENARIO==='oos'?false:true;
    $sku=$SCENARIO==='wrongsku'?'WRONG':'SKU5';
    return ['status'=>200,'body'=>json_encode([
       'id'=>123,'variants'=>[['id'=>900,'sku'=>$sku,'available'=>$available,'price'=>12599]]
    ])];
}
function wp_remote_retrieve_response_code($r){return $r['status'];}
function wp_remote_retrieve_body($r){return $r['body'];}
$csv=tempnam(sys_get_temp_dir(),'ahc-sp-fixture');
$f=fopen($csv,'wb');
$headers=['product_id','variation_id','shop_code','supplier_product_id',
          'source_url','merchant_variant_id','status','merchant_variant_sku',
          'woo_variation_sku','sku_evidence','sku_verified_at_utc'];
fputcsv($f,$headers);
fputcsv($f,['10','11','SP','123','https://www.shoepalace.com/products/test-shoe',
    '900','verified','SKU5','SKU5','independent Shopify variant SKU','2026-11-21T09:00:00Z']);
fclose($f);
define('AHC_SP_EVIDENCE_CSV',$csv);
require dirname(__DIR__,2).'/tools/ahc-stock-sp-evidence-offers-staging.php';
require dirname(__DIR__,2).'/tools/ahc-stock-sp-live-adapter-staging.php';
require dirname(__DIR__,2).'/tools/ahc-stock-sp-pricing-staging.php';
$SCENARIO='success';$HTTP_CALLS=0;$PRICING_ALLOWED=false;
add_filter('ahc_sp_verified_landed_estimate_jpy',fn($old,$r)=>15000,10,2);
add_filter('ahc_sp_verified_store_currency',fn($old,$url,$pid)=>'USD',10,3);
add_filter('ahc_sp_verified_live_cost_inputs',function($old,$current,$offer,$pid,$vid) {
  global $PRICING_ALLOWED;
  if (!$PRICING_ALLOWED) return null;
  $costs=['local_sales_tax'=>0,'local_delivery'=>0,
      'international_shipping'=>2200,'domestic_shipping'=>0,'customs_duty'=>0,
      'import_consumption_tax'=>0,'partner_fee'=>1500,'packaging'=>60,'other_fees'=>0];
  $zero=[];
  foreach($costs as $name=>$cost) if($cost===0) $zero[$name]='fixture verified zero';
  return ['approved'=>true,'shop'=>'SP','supplier_product_id'=>'123',
      'merchant_variant_id'=>'900','merchant_variant_sku'=>'SKU5',
      'source_price_usd'=>$current['amount'],'source_ref'=>'fixture-current',
      'observed_at'=>time(),'fx_jpy_per_usd_x10000'=>1500000,
      'fx_observed_at'=>time(),'costs_jpy'=>$costs,'verified_zero_reasons'=>$zero,
      'channel'=>'AHC','channel_fee_verified'=>true,'source_card_uplift_bps'=>200,
      'channel_price_divisor_million'=>785000,'round_up_jpy'=>100,
      'pricing_policy_ref'=>'approved-fixture-policy'];
},10,6);
$PASS=0;$FAIL=0;
function t2($label,$truth){global $PASS,$FAIL;if($truth){$PASS++;echo "PASS $label\n";}else{$FAIL++;echo "FAIL $label\n";}}
function req2($name,$post=[]){
  $_POST=array_merge(['nonce'=>'valid'],$post);
  try{$name();}catch(Finished $e){return $e;}
  throw new RuntimeException("No response from $name");
}
function begin(){
  return req2('ahc_inline_start',[
    'product_id'=>'10','variation_id'=>'11',
    'attribute_pa_size'=>'9','attribute_pa_color'=>'black'
  ]);
}
function resetCase(){
  global $TR,$W,$META;$TR=[];$META=[];$W->session=new FakeSession();$W->cart=new FakeCart();
}
try {
  // Direct purchase cannot skip stock checking.
  t2('direct Woo cart rejects anonymous visitor',
    !apply_filters('woocommerce_add_to_cart_validation',true,10,1,11,
      ['attribute_pa_size'=>'9','attribute_pa_color'=>'black']));
  resetCase();$PRICING_ALLOWED=false;
  $start=begin();$id=$start->data['check_id'];
  $step=req2('ahc_inline_step',['check_id'=>$id]);
  t2('missing approved cost input prevents purchase',
    $step->data['result']==='unconfirmed' && !isset($step->data['permit']));
  resetCase();$PRICING_ALLOWED=true;$SCENARIO='success';
  $start=begin();$id=$start->data['check_id'];
  $step=req2('ahc_inline_step',['check_id'=>$id]);
  t2('entire source chain returns verified price quote',
    $step->data['result']==='in_stock' && $step->data['price_case']==='quote' &&
    $step->data['quote_price_text']==='¥29,400');
  $token=$step->data['permit']??'';
  $deny=req2('ahc_inline_add_to_cart',['permit'=>$token,'accept_quote'=>'0']);
  t2('new price requires consent',!$deny->ok);
  $add=req2('ahc_inline_add_to_cart',['permit'=>$token,'accept_quote'=>'1']);
  t2('consented verified item enters cart',
    $add->ok && count($W->cart->lines)===1 &&
    $W->cart->lines[0]['ahc_inline_price']===29400 &&
    $W->cart->lines[0]['ahc_inline_shop']==='SP');
  resetCase();$SCENARIO='oos';$start=begin();
  $step=req2('ahc_inline_step',['check_id'=>$start->data['check_id']]);
  t2('live out-of-stock returns no permit and writes no shared marker',
    $step->data['result']==='out_of_stock' && !isset($step->data['permit']) &&
    !array_key_exists('_ahc_inline_oos_until',$META[11]??[]));
  // An old persisted marker from the superseded implementation must never
  // prevent a new live inquiry, even in another Woo guest session.
  resetCase();$META[11]['_ahc_inline_oos_until']=time()+86400;
  $SCENARIO='success';$start=begin();
  $step=req2('ahc_inline_step',['check_id'=>$start->data['check_id']]);
  t2('immediate supplier restock can authorize a new live purchase',
    $start->ok && $step->data['result']==='in_stock' &&
    isset($step->data['permit']));
  resetCase();
  resetCase();$SCENARIO='wrongsku';$start=begin();
  $step=req2('ahc_inline_step',['check_id'=>$start->data['check_id']]);
  t2('live supplier sku discrepancy prevents checkout',
    $step->data['result']==='unconfirmed' && !isset($step->data['permit']));
  resetCase();$SCENARIO='http429';$start=begin();
  $step=req2('ahc_inline_step',['check_id'=>$start->data['check_id']]);
  t2('supplier rate-limit prevents checkout',
    $step->data['result']==='unconfirmed' && !isset($step->data['permit']));
  echo "TOTAL $PASS PASS; $FAIL FAIL\n";
} finally {unlink($csv);}
exit($FAIL?1:0);
