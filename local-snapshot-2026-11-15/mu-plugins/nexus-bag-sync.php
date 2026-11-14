<?php
/*
Plugin Name: NEXUS Bag Count Sync
Description: Keeps the header cart counts (PC topbar number, mobile home bag
number, v08 header "BAG (n)") in sync with the WooCommerce Blocks cart store,
so quantity changes and removals on the cart page update the header without a
page reload. The theme renders the counts server-side only; the block cart
updates itself via the Store API and never touches the header. Local prototype
only. Added 2026-11-13 for the pre-launch re-check (site acceptance follow-up).
*/
add_action('wp_footer', function () {
    if (is_admin()) return;
    ?>
<script>
(function () {
  function setBag(n) {
    document.querySelectorAll('.nexus-pc-topbar__count').forEach(function (el) {
      el.textContent = n;
    });
    document.querySelectorAll('.nx-home-bag span').forEach(function (el) {
      el.textContent = n;
    });
    document.querySelectorAll('.nexus-v08-header a').forEach(function (a) {
      if (/^BAG \(\d+\)$/.test(a.textContent.trim())) {
        a.textContent = 'BAG (' + n + ')';
      }
    });
  }
  function fromStore() {
    if (!window.wp || !wp.data || !wp.data.select) return;
    var sel = wp.data.select('wc/store/cart');
    if (!sel || !sel.getCartData) return;
    var d = sel.getCartData();
    if (d && typeof d.itemsCount === 'number') setBag(d.itemsCount);
  }
  function init() {
    if (window.wp && wp.data && wp.data.subscribe) {
      try {
        wp.data.subscribe(fromStore);
      } catch (e) { /* store not registered on this page */ }
      fromStore();
    }
    if (window.jQuery) {
      jQuery(document.body).on('added_to_cart removed_from_cart updated_cart_totals', function () {
        setTimeout(fromStore, 300);
      });
    }
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
</script>
    <?php
});
