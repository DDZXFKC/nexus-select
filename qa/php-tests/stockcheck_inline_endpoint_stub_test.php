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
add_filter('ahc_inline_verified_offers',function($offers,$pid,$vid,$attrs) {
  global $SIM;
  if ($SIM==='empty')return [];
  if ($SIM==='multi') return [
    ['shop'=>'fixture-high','url'=>'https://example.test/sku-high','estimated_total_jpy'=>14000],
    ['shop'=>'fixture-low','url'=>'https://example.test/sku-low','estimated_total_jpy'=>16000]
  ];
  return [['shop'=>'fixture','url'=>'https://example.test/sku',
          'estimated_total_jpy'=>15000]];
},10,4);
add_filter('ahc_inline_check_one_offer',function($prev,$offer,$pid,$vid,$attrs) {
  global $SIM;
  if ($SIM==='oos') return ['stock'=>'OUT_OF_STOCK','reason'=>'OK'];
  return ['stock'=>'IN_STOCK','reason'=>'OK','current_price'=>['amount'=>100,'currency'=>'USD']];
},10,5);
add_filter('ahc_inline_recomputed_sale_price',function($old,$current,$offer,$pid,$vid) {
  global $SIM;
  if ($SIM==='multi') return $offer['shop']==='fixture-high'?26000:24400;
  return $SIM==='quote'?25400:($SIM==='smallincrease'?25300:25000);
},10,5);
$FAIL=0;$PASS=0;
function t($label,$condition){global $FAIL,$PASS;if($condition){$PASS++;echo 'PASS '.$label."\n";}else{$FAIL++;echo 'FAIL '.$label."\n";}}
function req($fun,$data=[]) {$_POST=array_merge(['nonce'=>'valid'],$data);try{$fun();}catch(Finished $e){return $e;}throw new Exception('no json response');}
function start($pid=10,$vid=11,$attrs=['attribute_pa_size'=>'9','attribute_pa_color'=>'black']) {
  return req('ahc_inline_start',array_merge(['product_id'=>$pid,'variation_id'=>$vid],$attrs));
}
function fresh_session() { global $W,$TR; $W->session=new FakeSession();$TR=[]; }

t('ordinary Woo add-to-cart blocked',!apply_filters('woocommerce_add_to_cart_validation',true));
$GLOBALS['ahc_inline_authorized_cart_add']=['product_id'=>10,'variation_id'=>11,
  'attrs'=>['attribute_pa_size'=>'9','attribute_pa_color'=>'black'],'price'=>25000,'shop'=>'fixture'];
t('authorized context cannot add another product',
  !apply_filters('woocommerce_add_to_cart_validation',true,20,1,0,[]));
t('authorized context cannot add a different size',
  !apply_filters('woocommerce_add_to_cart_validation',true,10,1,11,
    ['attribute_pa_size'=>'10','attribute_pa_color'=>'black']));
t('authorized context cannot add extra quantity',
  !apply_filters('woocommerce_add_to_cart_validation',true,10,2,11,
    ['attribute_pa_size'=>'9','attribute_pa_color'=>'black']));
unset($GLOBALS['ahc_inline_authorized_cart_add']);
$start=start();
t('guest start sets session cookie and returns ID',$start->ok && $W->session->cookie &&
  preg_match('/^[a-f0-9]{40}$/',$start->data['check_id']));
$id=$start->data['check_id'];
$step=req('ahc_inline_step',['check_id'=>$id]);
t('step session preserved and stock confirmed',$step->ok && $step->data['result']==='in_stock');
$permit=$step->data['permit'];
$add=req('ahc_inline_add_to_cart',['permit'=>$permit,'accept_quote'=>'0']);
t('authorized item added; cart redirect returned',$add->ok && $add->data['cart_url']==='https://example.test/cart/' && count($W->cart->lines)===1);
t('cart line signed and price fixed',ahc_inline_cart_line_valid($W->cart->lines[0]) && $W->cart->lines[0]['ahc_inline_price']===25000);
do_action('woocommerce_before_calculate_totals',$W->cart);
t('Woo price recalculation uses permit price',$W->cart->lines[0]['data']->get_price()==='25000');
$again=req('ahc_inline_add_to_cart',['permit'=>$permit]);
t('replay rejected',!$again->ok && $again->data['code']==='permit_expired');

fresh_session();global $SIM;$SIM='quote';
$s=start();$step=req('ahc_inline_step',['check_id'=>$s->data['check_id']]);$token=$step->data['permit'];
t('400 yen triggers quote',$step->data['price_case']==='quote' && $step->data['quote_price_text']==='¥25,400');
$deny=req('ahc_inline_add_to_cart',['permit'=>$token,'accept_quote'=>'0']);
t('quote requires explicit consent',!$deny->ok && $deny->data['code']==='quote_not_accepted');
$yes=req('ahc_inline_add_to_cart',['permit'=>$token,'accept_quote'=>'1']);
t('accepted quote applied to cart line',$yes->ok && end($W->cart->lines)['ahc_inline_price']===25400);

fresh_session();$SIM='smallincrease';
$s=start();$step=req('ahc_inline_step',['check_id'=>$s->data['check_id']]);
t('300 yen increase keeps listed price per owner rule',
  $step->ok && $step->data['result']==='in_stock' &&
  $step->data['price_case']==='listed' && isset($step->data['permit']));

fresh_session();$SIM='multi';
$s=start();$id=$s->data['check_id'];
$step1=req('ahc_inline_step',['check_id'=>$id]);
t('supplier list stays running after first expensive offer',
  $step1->ok && $step1->data['state']==='running');
$step2=req('ahc_inline_step',['check_id'=>$id]);
t('all suppliers checked before accepting cheapest offer',
  $step2->ok && $step2->data['result']==='in_stock' &&
  $step2->data['price_case']==='listed' && isset($step2->data['permit']));
$add=req('ahc_inline_add_to_cart',['permit'=>$step2->data['permit']]);
t('selected cheaper supplier persists on cart line',
  $add->ok && end($W->cart->lines)['ahc_inline_shop']==='fixture-low');

fresh_session();$SIM='empty';
$s=start();$step=req('ahc_inline_step',['check_id'=>$s->data['check_id']]);
t('no offers fails closed as no_candidate',$step->ok && $step->data['result']==='unconfirmed' && $step->data['reason']==='no_candidate');

fresh_session();$SIM='oos';
$s=start();$step=req('ahc_inline_step',['check_id'=>$s->data['check_id']]);
t('confirmed OOS marks variation for 24 hours',
  $step->data['result']==='out_of_stock' &&
  get_post_meta(11,'_ahc_inline_oos_until')>=time()+DAY_IN_SECONDS-5);
$SIM='ok'; fresh_session(); $blocked=start();
t('other customer blocked by shared 24-hour OOS mark',
  !$blocked->ok && $blocked->data['code']==='marked_oos');
$META[11]['_ahc_inline_oos_until']=time()-1;
fresh_session(); $s=start(); $again=req('ahc_inline_step',['check_id'=>$s->data['check_id']]);
t('expired OOS mark allows fresh verification',
  $s->ok && $again->ok && $again->data['result']==='in_stock');

fresh_session();$SIM='ok';
$s=start(20,0,[]);
t('simple item start accepted',$s->ok);
$step=req('ahc_inline_step',['check_id'=>$s->data['check_id']]);
t('simple item step confirmed',$step->ok && $step->data['result']==='in_stock');
$add=req('ahc_inline_add_to_cart',['permit'=>$step->data['permit']]);
t('simple item cart addition succeeds',$add->ok && end($W->cart->lines)['variation_id']===0);

fresh_session();$bad=start(10,11,['attribute_pa_size'=>'10','attribute_pa_color'=>'black']);
t('mismatched size rejected server-side',!$bad->ok && $bad->data['code']==='invalid_selection');

fresh_session(); $SIM='ok';
$s=start(10,12,['attribute_pa_size'=>'9','attribute_pa_color'=>'black']);
t('any-attribute variation accepted with explicit selected size',$s->ok);
if ($s->ok) {
  $id=$s->data['check_id'];
  $step=req('ahc_inline_step',['check_id'=>$id]);
  $token=$step->data['permit']??'';
  $add=req('ahc_inline_add_to_cart',['permit'=>$token]);
  t('any-attribute size preserved in cart add',
    $add->ok && ($W->cart->lines[count($W->cart->lines)-1]['variation_id']??0)===12);
  $permit=get_transient('ahc_inline_permit_'.$token);
  t('any-attribute permit consumed after successful cart add',
    $permit===false);
}
echo "TOTAL $PASS PASS; $FAIL FAIL\n";
exit($FAIL?1:0);
