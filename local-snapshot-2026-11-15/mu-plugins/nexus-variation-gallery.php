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
3) Color details: when a color is selected, show that color's details
   (colorway name / style code / optional note) from the product meta
   _nexus_color_details in a small box under the variations form. Uses
   the same color-change signals as the gallery filter. Products
   without the meta are unaffected.
Local prototype only. Does not modify the theme or the tracking plugin.
*/
add_action('woocommerce_single_product_summary', function () {
    global $product;
    if (!$product || !function_exists('get_post_meta')) return;
    $raw = get_post_meta($product->get_id(), '_nexus_color_details', true);
    if (!$raw) return;
    $dec = json_decode((string) $raw, true);
    if (!is_array($dec) || !$dec) return;
    echo '<div class="nexus-color-detail" id="nexus-color-detail" hidden></div>';
}, 33);
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
    /*
     * Swatch thumbnails per color value (owner-approved 2026-11-19): the
     * theme's color swatch shows the variation image of that color.
     * Only a variation's OWN image is used (get_image_id('edit') does not
     * fall back to the parent image), so a color without its own image
     * never borrows another color's photo. If one image is shared by two
     * different colors, it is not trusted for either. Reads child
     * variation objects directly instead of another
     * get_available_variations() pass (GPT audit c2d058d, items 1 and 5).
     */
    $thumbs = null;
    if ($product && $product->is_type('variable')) {
        $tattr = null;
        foreach ($product->get_variation_attributes() as $ak => $av) {
            if (stripos($ak, 'color') !== false) { $tattr = $ak; break; }
        }
        if ($tattr) {
            $by_color = [];   // color value => image id
            $by_image = [];   // image id => set of color values
            foreach ($product->get_children() as $child_id) {
                $v = wc_get_product($child_id);
                if (!$v || !$v->is_type('variation')) continue;
                // Same value the variation form uses (term slug for pa_ attributes).
                $attrs = $v->get_attributes();
                $val = isset($attrs[$tattr]) ? (string) $attrs[$tattr] : '';
                $img = (int) $v->get_image_id('edit');
                if ($val === '' || !$img) continue;
                if (!isset($by_color[$val])) $by_color[$val] = $img;
                $by_image[$img][$val] = true;
            }
            $timgs = [];
            foreach ($by_color as $val => $img) {
                if (count($by_image[$img]) > 1) continue;
                $src = wp_get_attachment_image_src($img, 'woocommerce_thumbnail');
                if ($src && !empty($src[0])) $timgs[$val] = esc_url_raw($src[0]);
            }
            if ($timgs) $thumbs = ['attr' => 'attribute_' . $tattr, 'images' => $timgs];
        }
    }
    /*
     * Color components for the data-driven swatch (GPT design 70ee059).
     * Contract (proposed, to be confirmed by GPT/Muse): product meta
     * _ahc_color_components = JSON object keyed by the variation color
     * value (pa_ term slug) -> ordered list of {"name": "...", "hex": "#RRGGBB" | null}.
     * Written by the sheet -> Woo step; the theme only reads it.
     */
    $components = null;
    if ($product && $product->is_type('variable')) {
        $craw = get_post_meta($product->get_id(), '_ahc_color_components', true);
        $cdec = $craw ? json_decode((string) $craw, true) : null;
        $ctx = json_decode((string) get_post_meta($product->get_id(), '_ahc_color_components_context', true), true);
        $kattr = null;
        foreach ($product->get_variation_attributes() as $ak => $av) {
            if (stripos($ak, 'color') !== false) { $kattr = $ak; break; }
        }
        $clean_list = function ($list) {
            $items = [];
            foreach ((array) $list as $c) {
                if (!is_array($c)) continue;
                $hex = isset($c['hex']) && is_string($c['hex']) && preg_match('/^#[0-9A-Fa-f]{6}$/', $c['hex']) ? strtoupper($c['hex']) : null;
                $items[] = ['name' => isset($c['name']) ? (string) $c['name'] : '', 'hex' => $hex];
            }
            return $items;
        };
        if (is_array($cdec) && array_key_exists('__single__', $cdec) && is_array($cdec['__single__']) && !$kattr) {
            /*
             * Single-colorway product without a color variation (GPT 84e54b3): reserved key
             * __single__. Colored only when the context status is CONFIRMED; otherwise neutral.
             * An explicit empty list (no components) is neutral too; no meta = nothing shown.
             */
            $status = is_array($ctx) && isset($ctx['swatch_status']) ? (string) $ctx['swatch_status'] : '';
            $items = $clean_list($cdec['__single__']);
            if ($status !== 'CONFIRMED') foreach ($items as &$it) { $it['hex'] = null; } unset($it);
            $components = ['single' => [
                'label' => wc_attribute_label('pa_color'),
                'colorway' => is_array($ctx) && isset($ctx['colorway_original']) ? (string) $ctx['colorway_original'] : implode('/', array_column($items, 'name')),
                'status' => $status,
                'items' => $items,
            ]];
        } elseif ($kattr && is_array($cdec) && $cdec) {
            $clean = [];
            foreach ($cdec as $val => $list) {
                if ($val === '__single__' || !is_array($list)) continue;
                $clean[(string) $val] = $clean_list($list);
            }
            if ($clean) $components = ['attr' => 'attribute_' . $kattr, 'colors' => $clean];
        }
    }
    $details = null;
    $cattr2 = null;
    if ($product && $product->is_type('variable')) {
        foreach ($product->get_variation_attributes() as $ak => $av) {
            if (stripos($ak, 'color') !== false) { $cattr2 = 'attribute_' . $ak; break; }
        }
        $raw = get_post_meta($product->get_id(), '_nexus_color_details', true);
        if ($raw) {
            $dec = json_decode((string) $raw, true);
            if (is_array($dec) && $dec) $details = $dec;
        }
    }
    ?>
<style>.nexus-swatch.is-disabled{opacity:.35;text-decoration:line-through;pointer-events:none}.nexus-color-detail{margin:10px 0 14px;padding:10px 12px;border:1px solid #e2e2e2;font-size:13px;line-height:1.7;color:#111}.nexus-color-detail-note{margin-top:6px}</style>
<script>
window.NEXUS_VAR_MAP = <?php echo $map ? wp_json_encode($map) : 'null'; ?>;
window.NEXUS_COLOR_MAP = <?php echo $colormap ? wp_json_encode($colormap) : 'null'; ?>;
window.NEXUS_COLOR_THUMBS = <?php echo $thumbs ? wp_json_encode($thumbs) : 'null'; ?>;
window.NEXUS_COLOR_COMPONENTS = <?php echo $components ? wp_json_encode($components, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT) : 'null'; ?>;
window.NEXUS_COLOR_DETAILS = <?php echo $details ? wp_json_encode($details) : 'null'; ?>;
window.NEXUS_COLOR_ATTR = <?php echo $cattr2 ? wp_json_encode($cattr2) : 'null'; ?>;
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
  function syncColorDetail(val) {
    var D = window.NEXUS_COLOR_DETAILS;
    var box = document.getElementById('nexus-color-detail');
    if (!box) return;
    if (!D || !val || !D[val]) {
      box.hidden = true;
      box.textContent = '';
      return;
    }
    var d = D[val];
    var parts = [];
    if (d.name) parts.push('カラー：' + d.name);
    if (d.model) parts.push('型番：' + d.model);
    box.textContent = parts.join(' ／ ');
    if (d.note) {
      var n = document.createElement('div');
      n.className = 'nexus-color-detail-note';
      n.textContent = d.note;
      box.appendChild(n);
    }
    box.hidden = parts.length === 0 && !d.note;
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
    var CA = window.NEXUS_COLOR_ATTR;
    if (CA) {
      var csel2 = $form.find('select[name="' + CA + '"]');
      if (csel2.length && csel2.val()) syncColorDetail(csel2.val());
      $form.on('change', 'select[name="' + CA + '"]', function () {
        syncColorDetail(this.value);
      });
      $form.on('click', '.nexus-swatches--colors .nexus-swatch[data-value]', function () {
        var val = this.getAttribute('data-value');
        setTimeout(function () { syncColorDetail(val); }, 30);
      });
      $form.on('found_variation', function (e, variation) {
        if (variation && variation.attributes) syncColorDetail(variation.attributes[CA]);
      });
      $form.on('reset_data', function () { syncColorDetail(''); });
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
