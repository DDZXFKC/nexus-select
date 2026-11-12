<?php
/*
Plugin Name: NEXUS Address Guard
Description: Prevents silent loss of shopper-typed text in the city field during
postal-code autofill on the block checkout. The autofill (okuricart) replaces
the city with the canonical city name when the postcode changes; any extra
text the shopper typed there (typically the town name, e.g. the full
"Uji-shi Gokasho" in the city field) would be discarded. This guard snapshots
the city at the moment the postcode changes and, if the autofill then trims
the city to a prefix of the snapshot, moves the trimmed remainder to the
front of address_1 (where the town belongs) instead of losing it.
Local prototype only. Does not modify okuricart or WooCommerce.
*/
add_action('wp_footer', function () {
    if (!function_exists('is_checkout') || !is_checkout()) return;
    if (function_exists('is_order_received_page') && is_order_received_page()) return;
    ?>
<script>
(function () {
  'use strict';

  function zipDigits(value) {
    return String(value || '')
      .replace(/[０-９]/g, function (ch) {
        return String.fromCharCode(ch.charCodeAt(0) - 0xFEE0);
      })
      .replace(/[^0-9]/g, '');
  }

  function bind() {
    if (!window.wp || !window.wp.data || !wp.data.select('wc/store/cart')) {
      return false;
    }

    var lastZip = { billing: null, shipping: null };
    var snap = { billing: null, shipping: null };

    wp.data.subscribe(function () {
      var customerData = wp.data.select('wc/store/cart').getCustomerData();
      if (!customerData) return;

      ['billing', 'shipping'].forEach(function (type) {
        var address = type === 'billing' ? customerData.billingAddress : customerData.shippingAddress;
        if (!address) return;

        var zip = zipDigits(address.postcode);

        if (lastZip[type] === null) {
          lastZip[type] = zip;
          return;
        }

        if (zip !== lastZip[type]) {
          // Postcode just changed. The autofill lookup is asynchronous, so
          // the city still holds the shopper's text right now: snapshot it.
          snap[type] = { city: address.city || '' };
          lastZip[type] = zip;
          return;
        }

        var s = snap[type];
        if (!s) return;

        var city = address.city || '';
        if (city && s.city && s.city.indexOf(city) === 0 && s.city.length > city.length) {
          // The autofill trimmed the city to a prefix of what the shopper
          // typed. Move the remainder (town name etc.) to address_1.
          var rest = s.city.slice(city.length).replace(/^[\s　]+/, '');
          var address1 = address.address_1 || '';
          snap[type] = null;
          if (rest && address1.indexOf(rest) !== 0) {
            var patch = { address_1: rest + address1 };
            var action = type === 'billing' ? 'setBillingAddress' : 'setShippingAddress';
            wp.data.dispatch('wc/store/cart')[action](Object.assign({}, address, patch));
          }
        } else if (city !== s.city) {
          // City changed to something unrelated to the snapshot (different
          // city, or the shopper retyped). The snapshot no longer applies.
          snap[type] = null;
        }
        // If city still equals the snapshot, the autofill patch has not
        // landed yet; keep waiting.
      });
    });

    return true;
  }

  // The wc/store/cart store registers after the checkout JS loads; poll for
  // it the same way okuricart's autofill does.
  var tries = 0;
  var timer = setInterval(function () {
    tries++;
    if (bind() || tries >= 50) {
      clearInterval(timer);
    }
  }, 200);
})();
</script>
    <?php
});
