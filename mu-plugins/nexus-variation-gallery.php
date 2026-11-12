<?php
/*
Plugin Name: NEXUS Variation UX Sync (prototype)
Description: Two small storefront helpers for variable products with 2 attributes
(Color x Size), built for the NEXUS SELECT prototype:
1) Gallery filter: when a color is selected, the theme's stacked gallery
   shows only that color's images. Selecting a variation never scrolls
   the page (the scroll-to-image behaviour was removed on 2026-11-13 at
   the owner's direction; the shopper's position and focus are kept).
2) Linked options: disable swatch buttons that have no variation for the
   currently selected value of the other attribute (e.g. sizes that do not
   exist for the chosen color), and clear a selection that becomes invalid.
Local prototype only. Does not modify the theme or the tracking plugin.
*/
add_action('wp_footer', function () {
    if (!function_exists('is_product') || !is_product()) return;
    global $product;
    $map = null;
    if ($product && $product->is_type('variable')) {
        $vars = $product->get_available_variations();
        $tmp = [];
        $two = true;
        foreach ($vars as $v) {
            $attrs = $v['attributes'];
            $keys = array_keys($attrs);
            if (count($keys) !== 2) { $two = false; break; }
            $k1 = $keys[0]; $k2 = $keys[1];
            $tmp[$k1][$attrs[$k1]][$k2][] = $attrs[$k2];
            $tmp[$k2][$attrs[$k2]][$k1][] = $attrs[$k1];
        }
        if ($two && $tmp) $map = $tmp;
    }
    $colormap = null;
    if ($product && $product->is_type('variable')) {
        $cvars = $product->get_available_variations();
        $cattr = null;
        foreach ($product->get_variation_attributes() as $ak => $av) {
            if (stripos($ak, 'color') !== false) { $cattr = $ak; break; }
        }
        if ($cattr) {
            $imgs = [];
            foreach ($cvars as $cv) {
                $val = $cv['attributes']['attribute_' . $cattr] ?? '';
                $src = $cv['image']['full_src'] ?? '';
                if ($val !== '' && $src && !isset($imgs[$val])) $imgs[$val] = $src;
            }
            if (count($imgs) > 1) $colormap = ['attr' => 'attribute_' . $cattr, 'images' => $imgs];
        }
    }
    ?>
<style>.nexus-swatch.is-disabled{opacity:.35;text-decoration:line-through;pointer-events:none}</style>
<script>
window.NEXUS_VAR_MAP = <?php echo $map ? wp_json_encode($map) : 'null'; ?>;
window.NEXUS_COLOR_MAP = <?php echo $colormap ? wp_json_encode($colormap) : 'null'; ?>;
(function () {
  function stemOf(url) {
    if (!url) return '';
    var base = url.split('/').pop().split('?')[0];
    base = base.replace(/\.[a-zA-Z0-9]+$/, '');
    var m = base.match(/^(.*)_\d+$/);
    return m ? m[1] : base;
  }
  function filterGallery(colorValue) {
    var CM = window.NEXUS_COLOR_MAP;
    var gallery = document.querySelector('.nexus-gallery');
    if (!gallery) return;
    var links = gallery.querySelectorAll('a');
    if (!CM || !colorValue || !CM.images[colorValue]) {
      Array.prototype.forEach.call(links, function (a) { a.style.display = ''; });
      return;
    }
    var stem = stemOf(CM.images[colorValue]);
    if (!stem) return;
    function baseOf(a) {
      var urls = [a.getAttribute('href') || ''];
      var img = a.querySelector('img');
      if (img) {
        urls.push(img.getAttribute('src') || '');
        urls.push(img.getAttribute('data-src') || '');
        urls.push(img.getAttribute('data-large_image') || '');
      }
      for (var i = 0; i < urls.length; i++) {
        var b = urls[i].split('/').pop().split('?')[0];
        if (b) return b;
      }
      return '';
    }
    function hit(a) {
      var base = baseOf(a);
      return base.indexOf(stem + '_') === 0 || base.indexOf(stem + '.') === 0;
    }
    var matched = 0;
    Array.prototype.forEach.call(links, function (a) { if (hit(a)) matched++; });
    if (!matched) return;
    Array.prototype.forEach.call(links, function (a) {
      a.style.display = hit(a) ? '' : 'none';
    });
    gallery.scrollLeft = 0;
  }
  function syncLinked() {
    var MAP = window.NEXUS_VAR_MAP;

    if (!MAP || !window.jQuery) return;

    var form = document.querySelector('form.variations_form');
    if (!form) return;

    var selects = Array.prototype.slice.call(
      form.querySelectorAll('select[name^="attribute_"]')
    );

    selects.forEach(function (sel) {
      var name = sel.getAttribute('name');

      if (!MAP[name]) return;

      var wrap = sel.nextElementSibling;

      if (
        !wrap ||
        !wrap.classList.contains('nexus-swatches')
      ) {
        return;
      }

      var allowed = null;

      selects.forEach(function (other) {
        if (other === sel || !other.value) return;

        var otherName = other.getAttribute('name');

        var compat = (
          MAP[otherName] &&
          MAP[otherName][other.value] &&
          MAP[otherName][other.value][name]
        ) || [];

        allowed = (allowed === null)
          ? compat.slice()
          : allowed.filter(function (value) {
              return compat.indexOf(value) > -1;
            });
      });

      var buttons = wrap.querySelectorAll(
        '.nexus-swatch[data-value]'
      );

      Array.prototype.forEach.call(buttons, function (button) {
        var value = button.dataset.value;

        var option = Array.prototype.find.call(
          sel.options,
          function (item) {
            return item.value === value;
          }
        );

        if (!option) return;

        var disabledByCombination =
          allowed !== null &&
          allowed.indexOf(value) === -1;

        var disabled =
          option.disabled || disabledByCombination;

        button.disabled = disabled;
        button.classList.toggle('is-disabled', disabled);
        button.setAttribute(
          'aria-pressed',
          String(sel.value === value)
        );
      });

      /*
       * Clear an invalid current selection.
       * WooCommerce remains responsible for recalculating
       * the variation, price, SKU and add-to-cart state.
       */
      if (
        sel.value &&
        allowed !== null &&
        allowed.indexOf(sel.value) === -1
      ) {
        sel.value = '';
        jQuery(sel).trigger('change');
      }
    });
  }
  function bind() {
    if (!window.jQuery) return;
    var $form = jQuery('form.variations_form');
    if (!$form.length) return;
    $form.on('found_variation', function (e, variation) {
      var CM = window.NEXUS_COLOR_MAP;
      if (CM && variation && variation.attributes) filterGallery(variation.attributes[CM.attr]);
      setTimeout(syncLinked, 60);
    });
    $form.on('woocommerce_variation_select_change reset_data hide_variation', function () {
      setTimeout(syncLinked, 60);
    });
    $form.on('reset_data', function () { filterGallery(''); });
    var CM2 = window.NEXUS_COLOR_MAP;
    if (CM2) {
      var csel0 = $form.find('select[name="' + CM2.attr + '"]');
      if (csel0.length && csel0.val()) filterGallery(csel0.val());
      $form.on('change', 'select[name="' + CM2.attr + '"]', function () {
        filterGallery(this.value);
      });
      $form.on('click', '.nexus-swatches--colors .nexus-swatch[data-value]', function () {
        var val = this.getAttribute('data-value');
        setTimeout(function () { filterGallery(val); }, 30);
      });
    }
    setTimeout(syncLinked, 300);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bind);
  } else {
    bind();
  }
})();
</script>
    <?php
});
