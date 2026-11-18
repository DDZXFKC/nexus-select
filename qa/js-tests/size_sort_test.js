// Offline test for sizeSortKey in the theme's main.js (no browser needed).
// Usage: node qa/js-tests/size_sort_test.js local-snapshot-2026-11-15/theme/main.js
const src = require('fs').readFileSync(process.argv[2], 'utf8');
const a = src.indexOf('const LETTER_SIZES'), b = src.indexOf('  function getOptions');
eval(src.slice(a, b).replace('const LETTER_SIZES', 'var LETTER_SIZES'));
const cases = [
  ['US 10.5C (16cm)', [0, 10.5]], ['US 1.5Y (20cm)', [1, 1.5]], ['3Y （21.5cm）', [1, 3]],
  ['10C (16 cm)', [0, 10]], ['US 9', [2, 9]], ['XL', [3, 5]], ['ＸＬ', [3, 5]],
  ['10C (approx cm)', null], ['10C (16cm) extra', null], ['10C (16cm', null], ['10C 16cm)', null],
  ['9 (Wide)', null], ['M 9 / W 10.5', null], ['10C/11C', null], ['10C (abc16cm)', null],
];
let fail = 0;
for (const [label, expected] of cases) {
  const got = sizeSortKey(label);
  const pass = JSON.stringify(got) === JSON.stringify(expected);
  if (!pass) fail++;
  console.log(pass ? 'PASS' : 'FAIL', JSON.stringify(label), JSON.stringify(got));
}
const order = l => l.map(x => [x, sizeSortKey(x)]).sort((p, q) => p[1][0] - q[1][0] || p[1][1] - q[1][1]).map(x => x[0]);
const clifton = ['US 1.5Y (20cm)', 'US 10.5C (16cm)', 'US 11.5C (17cm)', 'US 11C (16.5cm)', 'US 12.5C (18.5cm)', 'US 12C (18cm)',
  'US 13.5C (19cm)', 'US 13C (19cm)', 'US 1Y (19.5cm)', 'US 2.5Y (21cm)', 'US 2Y (20.5cm)', 'US 3Y (21.5cm)'];
const want = ['US 10.5C (16cm)', 'US 11C (16.5cm)', 'US 11.5C (17cm)', 'US 12C (18cm)', 'US 12.5C (18.5cm)', 'US 13C (19cm)',
  'US 13.5C (19cm)', 'US 1Y (19.5cm)', 'US 1.5Y (20cm)', 'US 2Y (20.5cm)', 'US 2.5Y (21cm)', 'US 3Y (21.5cm)'];
const okOrder = JSON.stringify(order(clifton)) === JSON.stringify(want);
if (!okOrder) fail++;
console.log(okOrder ? 'PASS' : 'FAIL', 'Clifton 10 Preschool order');
console.log(fail ? `${fail} FAILED` : 'ALL PASS');
process.exit(fail ? 1 : 0);
