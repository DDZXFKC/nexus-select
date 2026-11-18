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
    const label = String(text).trim().toUpperCase();
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
   * Tight crop for image swatches (owner feedback 2026-11-19: the product
   * looked small with a large white margin). Finds the product's bounding
   * box on the white background and zooms so the product fills the
   * existing circle. Circle size/shape unchanged. If the image cannot be
   * read (e.g. cross-origin), a fixed zoom is used instead.
   */
  const SWATCH_FILL = 0.92;

  function productBox(img) {
    const size = 80;
    const canvas = document.createElement('canvas');
    const ratio = img.naturalWidth / img.naturalHeight || 1;
    canvas.width = ratio >= 1 ? size : Math.round(size * ratio);
    canvas.height = ratio >= 1 ? Math.round(size / ratio) : size;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
    let x0 = canvas.width, y0 = canvas.height, x1 = -1, y1 = -1;
    for (let y = 0; y < canvas.height; y++) {
      for (let x = 0; x < canvas.width; x++) {
        const i = (y * canvas.width + x) * 4;
        const alpha = data[i + 3];
        const light = Math.min(data[i], data[i + 1], data[i + 2]);
        if (alpha > 16 && light < 235) {
          if (x < x0) x0 = x;
          if (y < y0) y0 = y;
          if (x > x1) x1 = x;
          if (y > y1) y1 = y;
        }
      }
    }
    if (x1 < x0 || y1 < y0) return null;
    return {
      x: x0 / canvas.width, y: y0 / canvas.height,
      w: (x1 - x0 + 1) / canvas.width, h: (y1 - y0 + 1) / canvas.height,
      ratio
    };
  }

  function applyBox(visual, box) {
    const size = visual.clientWidth || 36;
    const width = (SWATCH_FILL * size) / Math.max(box.w, box.h / box.ratio);
    const height = width / box.ratio;
    const left = size / 2 - (box.x + box.w / 2) * width;
    const top = size / 2 - (box.y + box.h / 2) * height;
    visual.style.backgroundSize = width.toFixed(1) + 'px ' + height.toFixed(1) + 'px';
    visual.style.backgroundPosition = left.toFixed(1) + 'px ' + top.toFixed(1) + 'px';
  }

  function fitSwatchImage(visual, url) {
    const img = new Image();
    img.decoding = 'async';
    img.onload = () => {
      let box = null;
      try {
        box = productBox(img);
      } catch (e) {
        box = null;
      }
      if (box) {
        applyBox(visual, box);
      } else {
        visual.classList.add('nexus-swatch__color--zoom');
      }
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

      if (thumb) {
        visual.classList.add('nexus-swatch__color--image');
        visual.style.backgroundImage = 'url("' + String(thumb).replace(/"/g, '%22') + '")';
        fitSwatchImage(visual, String(thumb));
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

      const unavailable =
        option.disabled ||
        !allowedByMap(select, option.value);

      button.disabled = unavailable;
      button.classList.toggle('is-disabled', unavailable);
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
   * Developer audit:
   * Use NEXUSStage2.getUnresolvedColors()
   * in the browser console after visiting product pages.
   */
  window.NEXUSStage2 = {
    getUnresolvedColors: () =>
      Array.from(unresolvedColors).sort()
  };

});
