/* NEXUS SELECT — Stage 2
 * WooCommerce variation buttons and color swatches
 */

document.addEventListener('DOMContentLoaded', () => {

  /* Existing mobile navigation */
  const menuButton = document.querySelector('.nexus-menu-toggle');
  const nav = document.querySelector('.site-nav');

  if (menuButton && nav) {
    menuButton.addEventListener('click', () => {
      const open = nav.classList.toggle('is-open');
      menuButton.setAttribute('aria-expanded', String(open));
    });
  }

  /* -------------------------------------------------------
     Color palette

     Exact brand-specific colors can be added to EXACT_COLORS.
     Generic colors are handled by BASIC_COLORS.
     Unknown colors are never silently assigned a guessed color.
     ------------------------------------------------------- */

  // Display-only approximations, NOT verified manufacturer color codes.
  // Audit: docs/pa-color-audit-2026-11-11.md (used terms only).
  const EXACT_COLORS = {
    'palomino': '#A67C52',
    'university red': '#B5122A',
    'phantom': '#E7E2D9',
    'light smoke grey': '#B7B8B8',
    'bleached aqua': '#A6D9D6',
    'birch': '#D8C7A8',
    'blush': '#E8B8B4',
    'bold berry': '#842C55',
    'carbon': '#35393B',
    'cashmere': '#C9B79D',
    'cinnamon': '#A96543',
    'clay canyon': '#B66E51',
    'cocoa powder': '#705042',
    'cold moss': '#606A4B',
    'coral reef': '#F18B78',
    'cotton candy': '#F5B9D5',
    'dahlia': '#B74786',
    'dark concord': '#44316C',
    'deep forest': '#213F32',
    'deep royal': '#214BA0',
    'denim': '#476A8C',
    'desert ochre': '#B47738',
    'energy aqua': '#3EC9C9',
    'fawn': '#BDA17D',
    'fir': '#365747',
    'flash crimson': '#D91F3D',
    'foggy teal': '#5D9898',
    'fresh air': '#B9DFE6',
    'gravel': '#797C78',
    'hardware pearl': '#E3DFD4',
    'hyper crimson': '#D51C45',
    'hyper royal': '#2458BC',
    'infrared 23': '#EF354B',
    'ivory': '#F3EBDD',
    'lemon spark': '#F4E45B',
    'light lemon twist': '#F2EF9D',
    'light sapphire': '#80A7D8',
    'lime': '#A8CE42',
    'lt crimson': '#D85268',
    'lt violet ore': '#A89AC8',
    'midnight': '#20283D',
    'morpho': '#377BB7',
    'moss': '#667A4A',
    'mosstone': '#777F62',
    'multi': '#8A7896',
    'oatmeal': '#D9CCB4',
    'off noir': '#28262C',
    'old rose': '#B9828B',
    'old royal': '#31549A',
    'oxblood': '#542735',
    'platinum': '#D3D3CF',
    'pure aqua': '#55C9D4',
    'pure platinum': '#D5D8D9',
    'rainy lake': '#6E9CB2',
    'rose dust': '#C89DA4',
    'sage frost': '#B4C8B6',
    'sky': '#82C5E7',
    'teal': '#287F82',
    'volt': '#C8ED36',
    'wheat': '#D4B17A',
    'yamabuki': '#E6AE35'
  };

  const BASIC_COLORS = {
    'black': '#171717',
    'white': '#FFFFFF',
    'grey': '#999999',
    'gray': '#999999',
    'red': '#C62828',
    'blue': '#2864A0',
    'navy': '#172B4D',
    'green': '#40734C',
    'olive': '#73784B',
    'yellow': '#E6C53B',
    'orange': '#D97732',
    'purple': '#80559C',
    'pink': '#E5A0B5',
    'brown': '#795548',
    'beige': '#D8C6A6',
    'cream': '#F1E8D4',
    'sail': '#EEE9DF',
    'tan': '#C49A6C',
    'gold': '#C6A34A',
    'silver': '#BFC2C5',
    'gum': '#B98753',
    'burgundy': '#6B2535',
    'maroon': '#713642',
    'khaki': '#B4A482',
    'anthracite': '#383B3F'
  };

  const UNKNOWN_COLOR = '#D9D9D9';
  const unresolvedColors = new Set();

  function normalizeColorName(value) {
    return String(value || '')
      .normalize('NFKC')
      .toLowerCase()
      .trim()
      .replace(/[-_]+/g, ' ')
      .replace(/\s+/g, ' ');
  }

  function colorForPart(part) {
    const key = normalizeColorName(part);

    if (Object.prototype.hasOwnProperty.call(EXACT_COLORS, key)) {
      return EXACT_COLORS[key];
    }

    if (Object.prototype.hasOwnProperty.call(BASIC_COLORS, key)) {
      return BASIC_COLORS[key];
    }

    /*
     * Conservative generic matching:
     * Only recognize an explicit basic-color word.
     * Do not infer unknown proprietary names.
     */
    const words = key.split(/\s+/);

    for (const word of words) {
      if (Object.prototype.hasOwnProperty.call(BASIC_COLORS, word)) {
        return BASIC_COLORS[word];
      }
    }

    unresolvedColors.add(part.trim());
    return UNKNOWN_COLOR;
  }

  function swatchColors(label) {
    const parts = String(label)
      .split('/')
      .map(part => part.trim())
      .filter(Boolean);

    if (!parts.length) {
      return [UNKNOWN_COLOR];
    }

    /*
     * For 5+ color names, display the first four.
     * Keep the complete name in accessibility attributes.
     * Such cases should be reviewed for manual mapping.
     */
    if (parts.length > 4) {
      unresolvedColors.add(label);
    }

    return parts.slice(0, 4).map(colorForPart);
  }

  function colorBackground(colors) {
    if (colors.length === 1) {
      return colors[0];
    }

    const segment = 100 / colors.length;
    const stops = [];

    colors.forEach((color, index) => {
      const start = (index * segment).toFixed(4);
      const end = ((index + 1) * segment).toFixed(4);

      stops.push(`${color} ${start}% ${end}%`);
    });

    return `conic-gradient(from -90deg, ${stops.join(', ')})`;
  }

  /* Equal vertical stripes, left to right (1 = 100%, 2 = 50/50, 3 = thirds). */
  function stripeBackground(hexes) {
    if (hexes.length === 1) return hexes[0];
    const step = 100 / hexes.length;
    const stops = hexes.map((hex, i) =>
      `${hex} ${(i * step).toFixed(4)}% ${((i + 1) * step).toFixed(4)}%`);
    return `linear-gradient(90deg, ${stops.join(', ')})`;
  }

  function isColorAttribute(select) {
    return select.name === 'attribute_pa_color';
  }

  function isSizeAttribute(select) {
    return select.name === 'attribute_pa_size';
  }

  /*
   * Size sort key (owner-approved 2026-11-19, docs/variation-ui-investigation-claude-2026-11-19.md).
   * Kids C sizes, then Y sizes, then plain numbers (adult US), each ascending.
   * Apparel letter sizes XXS..4XL in their natural order.
   * If any label cannot be parsed, the original WooCommerce order is kept.
   */
  const LETTER_SIZES = ['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', '2XL', 'XXXL', '3XL', '4XL'];

  function sizeSortKey(text) {
    // Kids labels carry the JP length, e.g. "10.5C (17.5cm)" (owner rule
    // 2026-11-16: US + cm). Ignore only a trailing "(<number>cm)" when sorting.
    const label = String(text).normalize('NFKC').trim().toUpperCase()
      .replace(/\s*\(\s*\d+(?:\.\d+)?\s*CM\s*\)\s*$/, '').trim();
    const kids = label.match(/^(?:US\s*)?(\d+(?:\.\d+)?)\s*([CY])$/);
    if (kids) {
      return [kids[2] === 'C' ? 0 : 1, Number(kids[1])];
    }
    const plain = label.match(/^(?:US\s*)?(\d+(?:\.\d+)?)$/);
    if (plain) {
      return [2, Number(plain[1])];
    }
    const letter = LETTER_SIZES.indexOf(label);
    if (letter !== -1) {
      return [3, letter];
    }
    return null;
  }

  function getOptions(select) {
    const options = Array.from(select.options)
      .filter(option => option.value !== '');

    if (!isSizeAttribute(select)) {
      return options;
    }

    const keys = new Map(
      options.map(option => [option, sizeSortKey(option.textContent)])
    );

    if (
      options.length > 1 &&
      options.every(option => keys.get(option) !== null)
    ) {
      return options.sort((a, b) => {
        const ka = keys.get(a);
        const kb = keys.get(b);
        return ka[0] - kb[0] || ka[1] - kb[1];
      });
    }

    return options;
  }

  /*
   * Image swatch window (owner decision 2026-11-19, docs/variation-ui-swatch-decision-maou-2026-11-19.md):
   * the circle must be filled ONLY by the product's colors, never by the
   * photo's white background. Fully automatic for every product.
   *  1. Background = near-white/transparent pixels connected to the image
   *     edge (flood fill), so white parts INSIDE a white shoe still count
   *     as product.
   *  2. Find the largest square made only of product pixels (preferring
   *     squares near the product's center) and zoom so the circle sits
   *     inside that square. A circle inside an all-product square never
   *     shows background.
   *  3. If no usable square is found, keep a fixed center zoom (fallback).
   * Circle size/shape unchanged.
   */
  const SWATCH_SAMPLE = 120;     // analysis resolution (px, longer side)
  const SWATCH_MIN_SIDE = 0.06;  // smallest acceptable square (share of width)
  const SWATCH_INSET = 0.9;      // circle diameter vs square side (edge safety)

  function productWindow(img) {
    const ratio = img.naturalWidth / img.naturalHeight || 1;
    const w = ratio >= 1 ? SWATCH_SAMPLE : Math.max(1, Math.round(SWATCH_SAMPLE * ratio));
    const h = ratio >= 1 ? Math.max(1, Math.round(SWATCH_SAMPLE / ratio)) : SWATCH_SAMPLE;
    const canvas = document.createElement('canvas');
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    ctx.drawImage(img, 0, 0, w, h);
    const data = ctx.getImageData(0, 0, w, h).data;

    const isLight = i => data[i * 4 + 3] <= 16 ||
      Math.min(data[i * 4], data[i * 4 + 1], data[i * 4 + 2]) >= 235;

    // 1. Flood-fill background from the border.
    const background = new Uint8Array(w * h);
    const queue = [];
    const push = i => {
      if (!background[i] && isLight(i)) {
        background[i] = 1;
        queue.push(i);
      }
    };
    for (let x = 0; x < w; x++) { push(x); push((h - 1) * w + x); }
    for (let y = 0; y < h; y++) { push(y * w); push(y * w + w - 1); }
    while (queue.length) {
      const i = queue.pop();
      const x = i % w;
      const y = (i - x) / w;
      if (x > 0) push(i - 1);
      if (x < w - 1) push(i + 1);
      if (y > 0) push(i - w);
      if (y < h - 1) push(i + w);
    }

    // Product center (for tie-breaking).
    let sx = 0, sy = 0, n = 0;
    for (let i = 0; i < w * h; i++) {
      if (!background[i]) { sx += i % w; sy += Math.floor(i / w); n++; }
    }
    if (!n) return null;
    const cx = sx / n, cy = sy / n;

    // 2. Largest all-product square (dynamic programming).
    const side = new Uint16Array(w * h);
    let best = 0, bx = 0, by = 0, bestDist = Infinity;
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const i = y * w + x;
        if (background[i]) continue;
        const s = (x && y) ? 1 + Math.min(side[i - 1], side[i - w], side[i - w - 1]) : 1;
        side[i] = s;
        const mx = x - s / 2 + 0.5, my = y - s / 2 + 0.5;
        const dist = (mx - cx) ** 2 + (my - cy) ** 2;
        if (s > best || (s === best && dist < bestDist)) {
          best = s; bx = x - s + 1; by = y - s + 1; bestDist = dist;
        }
      }
    }
    if (best < SWATCH_MIN_SIDE * w) return null;
    return { x: bx / w, y: by / h, side: best / w, ratio };
  }

  function applyWindow(visual, win) {
    const size = visual.clientWidth || 36;
    // Displayed image width so that the square spans size / SWATCH_INSET.
    const width = size / (SWATCH_INSET * win.side);
    const height = width / win.ratio;
    const centerX = (win.x + win.side / 2) * width;
    const centerY = win.y * height + (win.side * width) / 2;
    visual.style.backgroundSize = width.toFixed(1) + 'px ' + height.toFixed(1) + 'px';
    visual.style.backgroundPosition =
      (size / 2 - centerX).toFixed(1) + 'px ' + (size / 2 - centerY).toFixed(1) + 'px';
  }

  function fitSwatchImage(visual, url, label) {
    const img = new Image();
    img.decoding = 'async';
    img.onload = () => {
      let win = null;
      try {
        win = productWindow(img);
      } catch (e) {
        win = null;
      }
      if (win) {
        visual.classList.add('nexus-swatch__color--image');
        visual.style.backgroundImage = 'url("' + url.replace(/"/g, '%22') + '")';
        applyWindow(visual, win);
      } else {
        /*
         * No background-free window could be found (or the image could not
         * be read). A center zoom cannot guarantee "no white background"
         * (GPT acceptance def2cb9), so fall back to the color-name circle.
         */
        visual.classList.remove('nexus-swatch__color--image');
        visual.style.backgroundImage = '';
        visual.style.background = colorBackground(swatchColors(label));
      }
    };
    img.onerror = () => {
      visual.style.background = colorBackground(swatchColors(label));
    };
    img.src = url;
  }

  function createButton(select, option) {
    const button = document.createElement('button');
    const label = option.textContent.trim();

    button.type = 'button';
    button.className = 'nexus-swatch';
    button.dataset.value = option.value;
    button.setAttribute('aria-label', label);
    button.setAttribute('title', label);

    if (isColorAttribute(select)) {
      button.classList.add('nexus-swatch--color');

      const visual = document.createElement('span');
      visual.className = 'nexus-swatch__color';
      visual.setAttribute('aria-hidden', 'true');
      /*
       * Owner decision 2026-11-19: the swatch is the product image of that
       * color, cropped to the circle. Thumbnails come from the
       * nexus-variation-gallery mu-plugin (window.NEXUS_COLOR_THUMBS).
       * Without a thumbnail, fall back to the existing color-name palette.
       */
      const thumbs = window.NEXUS_COLOR_THUMBS;
      const thumb = thumbs && thumbs.attr === select.name &&
        thumbs.images && thumbs.images[option.value];

      /*
       * Data-driven swatch (GPT design 70ee059, owner-approved): when the
       * product carries color components, the circle is split into equal
       * vertical stripes, left to right, using the first min(3, n)
       * components' display colors. Products with component data use ONLY
       * this method (no photo crop mixed in). If any of the first min(3, n)
       * colors is not yet resolved, a neutral "unconfirmed" circle is shown;
       * unknown colors are never painted gray or guessed.
       */
      const comps = window.NEXUS_COLOR_COMPONENTS;
      const usesComponents = comps && comps.attr === select.name && comps.colors;

      if (usesComponents) {
        const list = comps.colors[option.value];
        const shown = Array.isArray(list) ? list.slice(0, 3) : [];
        const hexes = shown.map(c => c && /^#[0-9A-Fa-f]{6}$/.test(c.hex || '') ? c.hex : null);
        if (shown.length && hexes.every(Boolean)) {
          visual.style.background = stripeBackground(hexes);
        } else {
          visual.classList.add('nexus-swatch__color--unconfirmed');
        }
      } else if (thumb) {
        // The image is shown only after its background-free window is
        // measured, so the uncropped photo (white background) never flashes.
        fitSwatchImage(visual, String(thumb), label);
      } else {
        visual.style.background = colorBackground(
          swatchColors(label)
        );
      }

      button.appendChild(visual);

    } else {
      if (isSizeAttribute(select)) {
        button.classList.add('nexus-swatch--size');
      }

      button.textContent = label;
    }

    button.addEventListener('click', () => {
      if (button.disabled) return;

      /*
       * Keep the original WooCommerce select authoritative.
       */
      select.value = option.value;

      /*
       * Native change bubbles into WooCommerce's
       * existing jQuery variation listeners.
       */
      select.dispatchEvent(
        new Event('change', { bubbles: true })
      );

      updateButtons(select);
    });

    return button;
  }

  function allowedByMap(select, value) {
    const map = window.NEXUS_VAR_MAP;
    const form = select.closest('form.variations_form');

    if (!map || !form || !map[select.name]) {
      return true;
    }

    const otherSelects = Array.from(
      form.querySelectorAll('select[name^="attribute_"]')
    ).filter(other =>
      other !== select && other.value
    );

    if (!otherSelects.length) {
      return true;
    }

    return otherSelects.every(other => {
      const compatible =
        map[other.name] &&
        map[other.name][other.value] &&
        map[other.name][other.value][select.name];

      /*
       * If the map does not contain the required relation,
       * do not guess that it is available.
       */
      return Array.isArray(compatible) &&
        compatible.includes(value);
    });
  }

  /*
   * SOLD OUT (owner decision 2026-11-20): a value is sold out when every
   * variation that matches it (and the other selected values) is out of
   * stock in WooCommerce's own variation data. Unknown data (AJAX-loaded
   * forms with no inline variations) never asserts SOLD OUT.
   */
  function soldOut(select, value) {
    const form = select.closest('form.variations_form');
    let vars = null;
    try {
      vars = JSON.parse(form && form.getAttribute('data-product_variations') || 'null');
    } catch (e) {
      vars = null;
    }
    if (!Array.isArray(vars) || !vars.length) return false;
    const others = Array.from(
      form.querySelectorAll('select[name^="attribute_"]')
    ).filter(other => other !== select && other.value);
    const matching = vars.filter(v => {
      const a = v && v.attributes || {};
      if (a[select.name] && a[select.name] !== value) return false;
      return others.every(o => !a[o.name] || a[o.name] === o.value);
    });
    return matching.length > 0 && matching.every(v => v.is_in_stock === false);
  }

  function updateButtons(select) {
    const wrapper = select.nextElementSibling;

    if (
      !wrapper ||
      !wrapper.classList.contains('nexus-swatches')
    ) {
      return;
    }

    const options = getOptions(select);
    const buttons = Array.from(
      wrapper.querySelectorAll('.nexus-swatch')
    );

    /*
     * Color names are not printed inside the swatches, so show the
     * selected color's name next to the attribute label (mobile has no
     * tooltip). Owner-approved 2026-11-19.
     */
    if (isColorAttribute(select)) {
      const row = select.closest('tr');
      const labelCell = row && row.querySelector('th.label, td.label');
      if (labelCell) {
        let name = labelCell.querySelector('.nexus-selected-value');
        if (!name) {
          name = document.createElement('span');
          name.className = 'nexus-selected-value';
          name.setAttribute('aria-live', 'polite');
          labelCell.appendChild(name);
        }
        const chosen = options.find(item => item.value === select.value);
        name.textContent = chosen ? chosen.textContent.trim() : '';
      }
    }

    /*
     * Rebuild only when WooCommerce changes the option set.
     * Normal selection changes update existing buttons.
     */
    const currentValues = buttons.map(
      button => button.dataset.value
    );

    const nextValues = options.map(option => option.value);

    const needsRebuild =
      currentValues.length !== nextValues.length ||
      currentValues.some(
        (value, index) => value !== nextValues[index]
      );

    if (needsRebuild) {
      wrapper.replaceChildren(
        ...options.map(option => createButton(select, option))
      );

      return updateButtons(select);
    }

    buttons.forEach(button => {
      const option = options.find(
        item => item.value === button.dataset.value
      );

      if (!option) return;

      const selected = select.value === option.value;

      const isSoldOut = soldOut(select, option.value);
      const unavailable =
        option.disabled ||
        !allowedByMap(select, option.value) ||
        isSoldOut;

      button.disabled = unavailable;
      button.classList.toggle('is-disabled', unavailable);
      button.classList.toggle('is-soldout', isSoldOut);
      const baseLabel = option.textContent.trim();
      const label = isSoldOut ? `${baseLabel} SOLD OUT` : baseLabel;
      button.setAttribute('aria-label', label);
      button.setAttribute('title', label);
      button.setAttribute('aria-pressed', String(selected));
      button.classList.toggle('is-selected', selected);
    });
  }

  const forms = document.querySelectorAll(
    'form.variations_form'
  );

  forms.forEach(form => {
    const selects = Array.from(
      form.querySelectorAll('select[name^="attribute_"]')
    );

    selects.forEach(select => {
      const row = select.closest('tr');

      if (!row || !select.options.length) {
        return;
      }

      const wrapper = document.createElement('div');
      wrapper.className = 'nexus-swatches';

      if (isColorAttribute(select)) {
        wrapper.classList.add('nexus-swatches--colors');
      } else if (isSizeAttribute(select)) {
        wrapper.classList.add('nexus-swatches--sizes');
      }

      wrapper.setAttribute('role', 'group');
      wrapper.setAttribute(
        'aria-label',
        row.querySelector('label')?.textContent.trim() ||
        select.name
      );

      select.insertAdjacentElement('afterend', wrapper);
      select.classList.add('nexus-native-select');

      select.addEventListener('change', () => {
        selects.forEach(updateButtons);
      });

      updateButtons(select);
    });

    if (window.jQuery) {
      window.jQuery(form).on(
        'woocommerce_update_variation_values ' +
        'reset_data found_variation ' +
        'woocommerce_variation_select_change',
        () => {
          selects.forEach(updateButtons);
        }
      );
    }
  });

  /*
   * Single-colorway product without a color variation (GPT 84e54b3):
   * a non-interactive circle + the original colorway text above the size
   * row. It never touches the selects, so size selection, price and stock
   * behave exactly as before. Colored only for CONFIRMED with all of the
   * first min(3, n) colors approved; otherwise the neutral circle.
   */
  const singleData = window.NEXUS_COLOR_COMPONENTS &&
    window.NEXUS_COLOR_COMPONENTS.single;

  const singleItems = singleData && Array.isArray(singleData.items) ?
    singleData.items : [];

  /*
   * No color components (explicit empty list): nothing is known about the
   * color, so no circle and no empty "color" row is shown (GPT 458ba6b).
   */
  if (singleData && singleItems.length && forms.length) {
    const table = forms[0].querySelector('table.variations');
    const items = singleItems;
    const shown = items.slice(0, 3);
    const hexes = shown.map(c =>
      c && /^#[0-9A-Fa-f]{6}$/.test(c.hex || '') ? c.hex : null);
    const colored = singleData.status === 'CONFIRMED' &&
      shown.length > 0 && hexes.every(Boolean);

    const block = document.createElement('div');
    block.className = 'nexus-single-color';

    const label = document.createElement('span');
    label.className = 'nexus-single-color__label';
    label.textContent = singleData.label || '';

    const visual = document.createElement('span');
    visual.className = 'nexus-swatch__color nexus-single-color__swatch';
    visual.setAttribute('aria-hidden', 'true');
    if (colored) {
      visual.style.background = stripeBackground(hexes);
    } else {
      visual.classList.add('nexus-swatch__color--unconfirmed');
    }

    const name = document.createElement('span');
    name.className = 'nexus-single-color__name';
    name.textContent = singleData.colorway ||
      items.map(c => c && c.name).filter(Boolean).join('/');

    block.append(label, visual, name);

    if (table) {
      table.insertAdjacentElement('beforebegin', block);
    } else {
      forms[0].insertAdjacentElement('afterbegin', block);
    }
  }

  /*
   * Developer audit:
   * Use NEXUSStage2.getUnresolvedColors()
   * in the browser console after visiting product pages.
   */
  window.NEXUSStage2 = {
    getUnresolvedColors: () =>
      Array.from(unresolvedColors).sort()
  };

});
