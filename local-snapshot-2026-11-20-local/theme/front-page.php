<?php if (!defined('ABSPATH')) exit; ?>
<?php get_header(); ?>
<?php
/* PC-only editorial homepage. Mobile/tablet markup below is unchanged. */
$nexus_pc_shop = function_exists('wc_get_page_permalink') ? wc_get_page_permalink('shop') : home_url('/shop/');
$nexus_pc_shop = $nexus_pc_shop ?: home_url('/shop/');
$nexus_pc_men = get_term_by('slug', 'mens', 'product_cat');
$nexus_pc_women = get_term_by('slug', 'womens', 'product_cat');
$nexus_pc_men_link = $nexus_pc_men && !is_wp_error($nexus_pc_men) ? get_term_link($nexus_pc_men) : $nexus_pc_shop;
$nexus_pc_women_link = $nexus_pc_women && !is_wp_error($nexus_pc_women) ? get_term_link($nexus_pc_women) : $nexus_pc_shop;
$nexus_pc_hero = absint(get_theme_mod('nexus_pc_hero_image', 0));
$nexus_pc_video = absint(get_theme_mod('nexus_pc_hero_video', 0));
$nexus_pc_video_url = $nexus_pc_video && get_post_mime_type($nexus_pc_video)==='video/mp4' ? wp_get_attachment_url($nexus_pc_video) : '';
$nexus_pc_poster_url = $nexus_pc_hero ? wp_get_attachment_image_url($nexus_pc_hero, 'full') : '';
$nexus_pc_men_img = absint(get_theme_mod('nexus_pc_men_image', 0));
$nexus_pc_women_img = absint(get_theme_mod('nexus_pc_women_image', 0));
?>
<div class="nexus-pc-home" id="nexus-pc-home">
  <section class="nexus-pc-hero" aria-label="SELECTED WORLD">
    <?php if ($nexus_pc_hero) : ?>
      <?php echo wp_get_attachment_image($nexus_pc_hero, 'full', false, ['class'=>'nexus-pc-hero__image','loading'=>'eager','fetchpriority'=>'high','alt'=>'AFTER HOURS CLUB editorial collection']); ?>
    <?php endif; ?>
    <?php if ($nexus_pc_video_url): ?>
      <video class="nexus-pc-hero__image nx-pc-film" hidden muted loop playsinline preload="none" data-src="<?php echo esc_url($nexus_pc_video_url); ?>" <?php if ($nexus_pc_poster_url): ?>poster="<?php echo esc_url($nexus_pc_poster_url); ?>"<?php endif; ?> aria-hidden="true"></video>
      <button type="button" class="nx-pc-film-toggle" hidden style="position:absolute;bottom:16px;right:16px;z-index:2;background:#fff;color:#111;padding:10px 16px;border:1px solid #111" aria-label="動画を再生">PLAY</button>
    <?php endif; ?>
    <div class="nexus-pc-hero__content">
      <p class="nexus-pc-hero__eyebrow">AFTER HOURS CLUB</p>
      <h1>SELECTED<br>WORLD</h1>
      <p class="nexus-pc-hero__sub">GLOBAL FASHION SELECT SHOP</p>
      <span class="nexus-pc-hero__rule" aria-hidden="true"></span>
      <p class="nexus-pc-hero__jp">世界から、まだ知らない一着を。</p>
      <a class="nexus-pc-hero__cta" href="<?php echo esc_url($nexus_pc_shop); ?>">SHOP NOW <span aria-hidden="true">→</span></a>
    </div>
  </section>
  <script>
  (function(){
    const root=document.querySelector('.nexus-pc-hero'),v=root?.querySelector('.nx-pc-film'),b=root?.querySelector('.nx-pc-film-toggle');
    if(!v||!b)return;
    const desktop=matchMedia('(min-width: 1025px)'),reduced=matchMedia('(prefers-reduced-motion: reduce)');
    let visible=false,manualPause=false,failed=false;
    function sync(){b.textContent=v.paused?'PLAY':'PAUSE';b.setAttribute('aria-label',v.paused?'動画を再生':'動画を停止');}
    function play(){if(failed||!desktop.matches)return;if(!v.getAttribute('src'))v.src=v.dataset.src;v.muted=true;v.play().catch(sync);}
    function update(){b.hidden=!desktop.matches||failed;if(!desktop.matches){v.pause();v.hidden=true;return;}if(!visible||document.hidden||reduced.matches||manualPause||navigator.connection?.saveData||failed){v.pause();return;}play();}
    b.addEventListener('click',()=>{if(v.paused){manualPause=false;play();}else{manualPause=true;v.pause();}});
    v.addEventListener('playing',()=>{if(!desktop.matches||document.hidden||!visible){v.pause();v.hidden=true;return;}v.hidden=false;sync();});
    v.addEventListener('pause',sync);
    v.addEventListener('error',()=>{failed=true;v.hidden=true;b.hidden=true;});
    if('IntersectionObserver' in window)new IntersectionObserver(e=>{visible=e[0].isIntersecting&&e[0].intersectionRatio>=0.25;update();},{threshold:0.25}).observe(root);else visible=true;
    [desktop,reduced].forEach(m=>{if(m.addEventListener)m.addEventListener('change',update);else m.addListener(update);});
    document.addEventListener('visibilitychange',update);update();sync();
  })();
  </script>
  <div class="nexus-pc-benefits" aria-label="サービスの特徴">
    <div><span aria-hidden="true">✈</span> 海外限定アイテムをセレクト</div>
    <div><span aria-hidden="true">◇</span> 安心の購入サポート</div>
    <div><span aria-hidden="true">▣</span> 追跡で配送状況を確認</div>
  </div>
  <section class="nexus-pc-arrivals" aria-labelledby="nexus-pc-arrivals-title">
    <div class="nexus-pc-section-heading">
      <h2 id="nexus-pc-arrivals-title">NEW ARRIVALS</h2>
      <a href="<?php echo esc_url($nexus_pc_shop); ?>">VIEW ALL <span aria-hidden="true">→</span></a>
    </div>
    <?php
    if (function_exists('wc_get_products')) {
      $nexus_pc_ids = array_map('absint', wc_get_products(['status'=>'publish','limit'=>6,'orderby'=>'date','order'=>'DESC','return'=>'ids']));
      if ($nexus_pc_ids) {
        echo do_shortcode('[products ids="'.esc_attr(implode(',', $nexus_pc_ids)).'" columns="6" orderby="post__in"]');
      }
    }
    ?>
  </section>
  <section class="nexus-pc-categories" aria-label="コレクション">
    <a class="nexus-pc-category nexus-pc-category--men" href="<?php echo esc_url($nexus_pc_men_link); ?>">
      <?php if ($nexus_pc_men_img) echo wp_get_attachment_image($nexus_pc_men_img, 'large', false, ['loading'=>'lazy','alt'=>'MEN collection']); ?>
      <span class="nexus-pc-category__text"><strong>MEN</strong><small>COLLECTION <span aria-hidden="true">→</span></small></span>
    </a>
    <a class="nexus-pc-category nexus-pc-category--women" href="<?php echo esc_url($nexus_pc_women_link); ?>">
      <?php if ($nexus_pc_women_img) echo wp_get_attachment_image($nexus_pc_women_img, 'large', false, ['loading'=>'lazy','alt'=>'WOMEN collection']); ?>
      <span class="nexus-pc-category__text"><strong>WOMEN</strong><small>COLLECTION <span aria-hidden="true">→</span></small></span>
    </a>
  </section>
  <section class="nexus-pc-brand-index" id="nexus-pc-brands" aria-labelledby="nexus-pc-brand-title">
    <h2 id="nexus-pc-brand-title">SHOP BY BRAND</h2>
    <?php $nexus_pc_brands = taxonomy_exists('pa_brand') ? get_terms(['taxonomy'=>'pa_brand','hide_empty'=>true,'orderby'=>'count','order'=>'DESC','number'=>8]) : []; ?>
    <?php $nexus_brand_logos = ['nike'=>'nike.svg','asics'=>'asics.svg','jordan'=>'jordan.svg','patta'=>'patta.svg','adidas'=>'adidas.svg','new-balance'=>'newbalance.svg','carhartt-wip'=>'carhartt.svg','vans'=>'vans.svg','li-ning'=>'lining.svg','timberland'=>'timberland.svg','on'=>'on.svg','ewing-athletics'=>'ewing.png']; ?>
    <?php if (!is_wp_error($nexus_pc_brands) && $nexus_pc_brands) : ?>
      <nav class="nexus-pc-brand-index__links" aria-label="ブランド別商品一覧">
        <?php foreach ($nexus_pc_brands as $nexus_pc_brand) : ?>
          <a href="<?php echo esc_url(get_term_link($nexus_pc_brand)); ?>"><?php if (!empty($nexus_brand_logos[$nexus_pc_brand->slug])) : ?><img class="nx-brand-logo" src="<?php echo esc_url(get_template_directory_uri() . '/assets/brands/' . $nexus_brand_logos[$nexus_pc_brand->slug]); ?>" alt="<?php echo esc_attr($nexus_pc_brand->name); ?>" loading="lazy"><?php else : ?><?php echo esc_html($nexus_pc_brand->name); ?><?php endif; ?></a>
        <?php endforeach; ?>
      </nav>
    <?php endif; ?>
  </section>
</div>
<div class="nexus-pc-home__original">


<?php
$nx_poster = absint(get_theme_mod('nexus_mobile_poster',0));
$nx_poster_url = $nx_poster ? wp_get_attachment_image_url($nx_poster,'large') : '';
/* Mobile hero slideshow: Ken Burns (slow pan + zoom) with quiet crossfade.
   Owner spec 2026-11-14, design consulted with GPT (9s interval / 2.4s fade / 11.4s motion,
   landscape pan +4% -> -4%, zoom 1.12 -> 1.20, portrait zoom only).
   To add or remove a slide, edit this ID list. 'pan' is 'landscape' or 'portrait'. */
$nx_hero_slide_defs = [
  ['id' => 18943, 'pan' => 'portrait'],
  ['id' => 18944, 'pan' => 'portrait'],
  ['id' => 18945, 'pan' => 'portrait'],
];
$nx_hero_slides = [];
foreach ($nx_hero_slide_defs as $nx_def) {
  $nx_url = wp_get_attachment_image_url($nx_def['id'], 'full');
  if ($nx_url) $nx_hero_slides[] = ['url' => $nx_url, 'pan' => $nx_def['pan']];
}
?>
<section class="nx-mobile-campaign" aria-labelledby="nx-mobile-title">
  <div class="nx-mobile-film"<?php echo count($nx_hero_slides) > 1 ? ' data-nx-slideshow' : ''; ?>>
    <?php if ($nx_hero_slides): ?>
      <div class="nx-film-layer" aria-hidden="true">
      <?php foreach ($nx_hero_slides as $nx_i => $nx_slide): ?>
        <img class="nx-film-image nx-film-image--<?php echo esc_attr($nx_slide['pan']); ?><?php echo $nx_i === 0 ? ' is-active' : ''; ?>" src="<?php echo esc_url($nx_slide['url']); ?>" alt=""<?php echo $nx_i === 0 ? ' fetchpriority="high"' : ' loading="lazy"'; ?>>
      <?php endforeach; ?>
      </div>
    <?php elseif ($nx_poster_url): ?>
      <img src="<?php echo esc_url($nx_poster_url); ?>" alt="AFTER HOURS CLUB campaign" fetchpriority="high" width="720" height="1280">
    <?php endif; ?>
  </div>
  <div class="nx-mobile-copy">
    <p>BEYOND BORDERS</p>
    <h1 id="nx-mobile-title">ENJOY FASHION.<br>ENJOY LIFE.</h1>
    <p>好きな服で、毎日をもっと楽しく。</p>
    <a href="<?php echo esc_url($nexus_pc_shop); ?>">SHOP NOW</a>
  </div>
</section>
<script>
(function(){
  var film=document.querySelector('.nx-mobile-film[data-nx-slideshow]');
  if(!film)return;
  var slides=Array.prototype.slice.call(film.querySelectorAll('.nx-film-image'));
  if(slides.length<2)return;
  var reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
  var mobile=window.matchMedia('(max-width: 1024px)');
  if(reduced.matches)return;
  var INTERVAL=9000, FADE=2400;
  var current=0, nextTimer=null, running=false, visible=false;
  function isImageReady(img){
    if(!img)return Promise.resolve(false);
    if(img.complete&&img.naturalWidth>0){
      if(typeof img.decode==='function'){return img.decode().then(function(){return true;},function(){return true;});}
      return Promise.resolve(true);
    }
    return new Promise(function(resolve){
      var done=false;
      function finish(ok){if(done)return;done=true;resolve(ok);}
      img.addEventListener('load',function(){finish(true);},{once:true});
      img.addEventListener('error',function(){finish(false);},{once:true});
      setTimeout(function(){finish(img.complete&&img.naturalWidth>0);},5000);
    });
  }
  function clearTimers(){if(nextTimer){clearTimeout(nextTimer);nextTimer=null;}}
  function scheduleNext(delay){clearTimers();if(!running)return;nextTimer=setTimeout(step,delay);}
  function activate(i){
    var prev=slides[current];
    slides.forEach(function(s,k){if(k!==i)s.classList.remove('is-active');});
    if(prev&&prev!==slides[i]){prev.classList.add('is-leaving');setTimeout(function(){prev.classList.remove('is-leaving');},FADE+150);}
    slides[i].classList.add('is-active');
    current=i;
  }
  function step(){
    if(!running)return;
    var next=(current+1)%slides.length;
    isImageReady(slides[next]).then(function(ok){
      if(!running)return;
      if(ok){activate(next);scheduleNext(INTERVAL);}
      else{scheduleNext(1500);}
    });
  }
  function resetSlides(){
    slides.forEach(function(s,k){s.classList.toggle('is-active',k===0);s.classList.remove('is-leaving');});
    current=0;
  }
  function start(){if(running||reduced.matches||!mobile.matches)return;running=true;scheduleNext(INTERVAL);}
  function stop(){running=false;clearTimers();}
  if('IntersectionObserver' in window){
    new IntersectionObserver(function(entries){visible=entries[0].isIntersecting;if(visible&&!document.hidden)start();else stop();},{threshold:0.25}).observe(film);
  }else{visible=true;start();}
  document.addEventListener('visibilitychange',function(){if(document.hidden)stop();else if(visible)start();});
  [reduced,mobile].forEach(function(m){
    if(m.addEventListener)m.addEventListener('change',function(){
      if(reduced.matches){stop();resetSlides();}
      else if(!mobile.matches){stop();}
      else if(visible&&!document.hidden){start();}
    });
    else if(m.addListener)m.addListener(function(){if(reduced.matches){stop();resetSlides();}});
  });
})();
</script>

<?php
$nexus_new_ids = [];
$nexus_featured_ids = [];

if (class_exists('WooCommerce')) {
    /*
     * NEW ARRIVALS
     * Latest 8 published products.
     */
    $nexus_new_ids = wc_get_products([
        'status'  => 'publish',
        'limit'   => 8,
        'orderby' => 'date',
        'order'   => 'DESC',
        'return'  => 'ids',
    ]);

    $nexus_new_ids = array_map('absint', $nexus_new_ids);

    /*
     * FEATURED DROPS
     * Exclude every product already shown in NEW ARRIVALS.
     */
    $nexus_featured_ids = wc_get_products([
        'status'   => 'publish',
        'limit'    => 8,
        'featured' => true,
        'exclude'  => $nexus_new_ids,
        'orderby'  => 'date',
        'order'    => 'DESC',
        'return'   => 'ids',
    ]);

    $nexus_featured_ids = array_map('absint', $nexus_featured_ids);
}
?>

<section class="nexus-v08-section">
  <div class="nexus-v08-section__head">
    <h2>NEW ARRIVALS</h2>
    <a href="<?php echo esc_url(home_url('/shop/')); ?>">VIEW ALL</a>
  </div>
  <?php
  if (!empty($nexus_new_ids)) {
      echo do_shortcode(
          '[products ids="' .
          esc_attr(implode(',', $nexus_new_ids)) .
          '" columns="2" orderby="post__in"]'
      );
  }
  ?>
</section>

<section class="nexus-v08-section">
  <div class="nexus-v08-section__head">
    <h2>FEATURED DROPS</h2>
    <a href="<?php echo esc_url(home_url('/shop/')); ?>">VIEW ALL</a>
  </div>
  <?php
  if (!empty($nexus_featured_ids)) {
      echo do_shortcode(
          '[products ids="' .
          esc_attr(implode(',', $nexus_featured_ids)) .
          '" columns="2" orderby="post__in"]'
      );
  }
  ?>
</section>

<section class="nx-mobile-collections" aria-label="コレクション">
<?php foreach (['mens'=>"MEN'S",'womens'=>"WOMEN'S",'kids'=>'KIDS'] as $slug=>$label):
 $term=get_term_by('slug',$slug,'product_cat');
 if (!$term || is_wp_error($term)) continue;
 // Empty category is hidden (owner rule); the card appears automatically once a product is published.
 if (!nexus_term_has_products($term)) continue;
 $url=get_term_link($term); if(is_wp_error($url))continue;
 $image=absint(get_theme_mod('nexus_mobile_'.$slug,0));
?>
<a href="<?php echo esc_url($url); ?>">
 <?php if($image) echo wp_get_attachment_image($image,'large',false,['loading'=>'lazy','alt'=>'']); ?>
 <strong><?php echo esc_html($label); ?> COLLECTION</strong><span>SHOP NOW</span>
</a>
<?php endforeach; ?>
</section>

<section class="nexus-v08-section" id="brands">
  <div class="nexus-v08-section__head">
    <h2>SHOP BY BRAND</h2>
  </div>
  <?php
  $nexus_brands = get_terms([
    'taxonomy' => 'pa_brand',
    'hide_empty' => true,
    'orderby' => 'count',
    'order' => 'DESC',
  ]);
  if (!is_wp_error($nexus_brands) && !empty($nexus_brands)) :
  ?>
  <div class="nexus-v08-brands">
    <?php foreach ($nexus_brands as $nexus_brand) : ?>
      <a class="nexus-v08-brand" href="<?php echo esc_url(get_term_link($nexus_brand)); ?>">
        <?php $nx_brand_logo_file = $nexus_brand_logos[$nexus_brand->slug] ?? ''; if ($nx_brand_logo_file) : ?><img class="nx-brand-logo" src="<?php echo esc_url(get_template_directory_uri() . '/assets/brands/' . $nx_brand_logo_file); ?>" alt="<?php echo esc_attr($nexus_brand->name); ?>" loading="lazy"><?php else : ?><span><?php echo esc_html($nexus_brand->name); ?></span><?php endif; ?>
        <small><?php echo esc_html(number_format_i18n($nexus_brand->count)); ?></small>
      </a>
    <?php endforeach; ?>
  </div>
  <?php endif; ?>
</section>

<section class="nexus-v08-guide">
  <h2>HOW IT WORKS</h2>
  <p>掲載商品は通常購入できます。掲載のない商品は「買付リクエスト」から相談できます。海外から取り寄せるため、到着まで約2〜3週間かかります。</p>
  <?php if (get_post(16) && 'publish' === get_post_status(16)) : ?>
  <a class="nexus-v08-button nexus-v08-button--ghost" href="<?php echo esc_url(get_permalink(16)); ?>">買付リクエスト</a>
  <?php endif; ?>
</section>


</div>
<?php get_footer(); ?>
