<?php if (!defined('ABSPATH')) exit; ?>
</main>
<footer class="nexus-v08-footer">
  <div class="nexus-v08-footer__inner">
    <div class="nexus-v08-footer__brand">
      <p class="nexus-v08-footer__title"><?php bloginfo('name'); ?></p>
      <p class="nexus-v08-footer__text">日本で買えないスニーカーと服を、世界から。</p>
    </div>
    <nav class="nexus-v08-footer__nav" aria-label="Footer">
      <div>
        <h3>SHOP</h3>
        <a href="<?php echo esc_url(home_url('/shop/')); ?>">すべての商品</a>
        <a href="<?php echo esc_url(home_url('/')); ?>#brands">ブランド</a>
        <?php
        $nexus_request_page = get_post(16);

        if (
            $nexus_request_page instanceof WP_Post &&
            $nexus_request_page->post_type === 'page' &&
            $nexus_request_page->post_status === 'publish'
        ) :
        ?>
        <a href="<?php echo esc_url(get_permalink(16)); ?>">買付リクエスト</a>
        <?php endif; ?>
      </div>
      <div>
        <h3>SUPPORT</h3>
        <a href="<?php echo esc_url(home_url('/tokushoho/')); ?>">特定商取引法に基づく表記</a>
        <a href="<?php echo esc_url(home_url('/privacy-policy/')); ?>">プライバシーポリシー</a>
        <a href="<?php echo esc_url(home_url('/contact/')); ?>">お問い合わせ</a>
      </div>
    </nav>
  </div>
  <p class="nexus-v08-footer__copy">© <?php echo esc_html(date_i18n('Y')); ?> <?php bloginfo('name'); ?></p>
</footer>
<?php wp_footer(); ?>
</body>
</html>
