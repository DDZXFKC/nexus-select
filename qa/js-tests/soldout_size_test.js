// Offline test for soldOut() in the theme's main.js. Usage: node qa/js-tests/soldout_size_test.js local-snapshot-2026-11-15/theme/main.js
const src = require('fs').readFileSync(process.argv[2], 'utf8');
const a = src.indexOf('  function soldOut'), b = src.indexOf('  function updateButtons');
eval(src.slice(a, b));
function mk(vars, others = []) {
  const form = { getAttribute: () => vars === null ? null : JSON.stringify(vars),
    querySelectorAll: () => others };
  return { name: 'attribute_pa_size', closest: () => form };
}
let fail = 0; const check = (n, ok) => { console.log(ok ? 'PASS' : 'FAIL', n); if (!ok) fail++; };
const vars = [
  { attributes: { attribute_pa_size: '9' }, is_in_stock: true },
  { attributes: { attribute_pa_size: '10' }, is_in_stock: false },
];
const sel = mk(vars);
check('in-stock size not sold out', soldOut(sel, '9') === false);
check('OOS size sold out', soldOut(sel, '10') === true);
check('unknown size not asserted', soldOut(sel, '11') === false);
check('no inline data (AJAX) not asserted', soldOut(mk(null), '10') === false);
const color = { name: 'attribute_pa_color', value: 'red' };
const two = [
  { attributes: { attribute_pa_size: '10', attribute_pa_color: 'red' }, is_in_stock: false },
  { attributes: { attribute_pa_size: '10', attribute_pa_color: 'blue' }, is_in_stock: true },
];
check('sold out only for the selected color', soldOut(mk(two, [color]), '10') === true);
check('available when no color chosen yet', soldOut(mk(two, []), '10') === false);
process.exit(fail ? 1 : 0);
