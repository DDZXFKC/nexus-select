<?php if (!defined('ABSPATH')) exit; ?>
<?php get_header(); ?>
<section class="nx-search">
  <h1 class="nx-search__title">検索結果</h1>
  <?php $nx_q = get_search_query(); ?>
  <form class="nx-search__form" role="search" method="get" action="<?php echo esc_url(home_url('/')); ?>"><label class="screen-reader-text" for="nx-search-input">商品を検索</label><input id="nx-search-input" name="s" type="search" placeholder="キーワードを入力" value="<?php echo esc_attr($nx_q); ?>" required><input type="hidden" name="post_type" value="product"><button type="submit">検索</button></form>
  <?php if (trim((string) $nx_q) === '') : ?>
    <p class="nx-search__note">検索キーワードを入力してください。</p>
  <?php elseif (have_posts()) : ?>
    <p class="nx-search__note">「<?php echo esc_html($nx_q); ?>」の検索結果</p>
    <ul class="nx-search__list">
    <?php while (have_posts()) : the_post(); ?>
      <li class="nx-search__item">
        <a class="nx-search__link" href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
        <p class="nx-search__excerpt"><?php echo esc_html(wp_trim_words(wp_strip_all_tags(get_the_excerpt()), 36, '…')); ?></p>
      </li>
    <?php endwhile; ?>
    </ul>
    <?php the_posts_pagination(['mid_size' => 1]); ?>
  <?php else : ?>
    <p class="nx-search__note">「<?php echo esc_html($nx_q); ?>」に該当する商品・ページが見つかりませんでした。</p>
  <?php endif; ?>
</section>
<?php get_footer(); ?>
