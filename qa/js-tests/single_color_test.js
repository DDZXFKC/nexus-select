// Offline test for the single-colorway block in the theme's main.js (tiny DOM mock, no browser).
// Usage: node qa/js-tests/single_color_test.js local-snapshot-2026-11-15/theme/main.js
const src = require('fs').readFileSync(process.argv[2], 'utf8');
const stripe = src.slice(src.indexOf('  function stripeBackground'), src.indexOf('  function isColorAttribute'));
const a = src.indexOf('  const singleData'), b = src.indexOf('  /*\n   * Developer audit:');
function el(tag) {
  const cls = new Set();
  return { tag, children: [], style: {}, attrs: {}, textContent: '',
    classList: { add: c => cls.add(c), has: c => cls.has(c) },
    set className(v) { v.split(' ').forEach(c => cls.add(c)); }, get className() { return [...cls].join(' '); },
    setAttribute(k, v) { this.attrs[k] = v; }, append(...c) { this.children.push(...c); } };
}
function run(data) {
  let inserted = null;
  const table = { insertAdjacentElement: (pos, node) => { inserted = { pos, node }; } };
  const forms = [{ querySelector: () => table }];
  const window = { NEXUS_COLOR_COMPONENTS: data };
  const document = { createElement: el };
  eval(stripe + src.slice(a, b));
  return inserted;
}
let fail = 0;
const check = (name, ok) => { console.log(ok ? 'PASS' : 'FAIL', name); if (!ok) fail++; };
const base = { label: 'カラー', colorway: 'Midnight Navy/Metallic Gold/Black/White', status: 'CONFIRMED',
  items: [{ name: 'Midnight Navy', hex: '#172B4D' }, { name: 'Metallic Gold', hex: '#C6A34A' },
          { name: 'Black', hex: '#171717' }, { name: 'White', hex: '#FFFFFF' }] };
let r = run({ single: base });
const [label, sw, name] = r.node.children;
check('inserted before size table', r.pos === 'beforebegin');
check('3 stripes from first 3', sw.style.background.startsWith('linear-gradient(90deg, #172B4D') && !sw.style.background.includes('#FFFFFF'));
check('all original names shown (4+)', name.textContent === base.colorway);
check('label', label.textContent === 'カラー');
check('swatch not interactive', sw.attrs['aria-hidden'] === 'true' && sw.tag === 'span');
r = run({ single: { ...base, status: 'UNKNOWN' } });
check('UNKNOWN neutral', r.node.children[1].classList.has('nexus-swatch__color--unconfirmed') && !r.node.children[1].style.background);
r = run({ single: { ...base, items: [{ name: 'Red', hex: null }] } });
check('missing hex neutral', r.node.children[1].classList.has('nexus-swatch__color--unconfirmed'));
r = run({ single: { label: 'カラー', colorway: '', status: 'UNKNOWN', items: [] } });
check('explicit empty list neutral', r.node.children[1].classList.has('nexus-swatch__color--unconfirmed'));
r = run({ single: { ...base, items: [{ name: 'White', hex: '#FFFFFF' }], colorway: 'White' } });
check('white confirmed is colored (solid border from base CSS)', r.node.children[1].style.background === '#FFFFFF' && !r.node.children[1].classList.has('nexus-swatch__color--unconfirmed'));
check('no meta -> nothing', run(null) === null);
process.exit(fail ? 1 : 0);
