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

  const EXACT_COLORS = {
    'palomino': '#A67C52',
    'university red': '#B5122A',
    'phantom': '#E7E2D9',
    'light smoke grey': '#B7B8B8'
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

  function getOptions(select) {
    const options = Array.from(select.options)
      .filter(option => option.value !== '');

    if (!isSizeAttribute(select)) {
      return options;
    }

    const parseSize = option => {
      const match = option.textContent.trim()
        .match(/^(?:US\s*)?(\d+(?:\.\d+)?)$/i);

      return match ? Number(match[1]) : null;
    };

    if (
      options.length > 1 &&
      options.every(option => parseSize(option) !== null)
    ) {
      return options.sort(
        (a, b) => parseSize(a) - parseSize(b)
      );
    }

    return options;
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
      visual.style.background = colorBackground(
        swatchColors(label)
      );

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
