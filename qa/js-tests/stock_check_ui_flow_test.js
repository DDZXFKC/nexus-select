// node qa/js-tests/stock_check_ui_flow_test.js
const { createFlow, messageFor, MSG, sizeLabel } = require('../../local-snapshot-2026-11-15/mu-plugins/ahc-stock-check-ui.js');
let fail = 0; const check = (n, ok) => { console.log((ok ? 'PASS ' : 'FAIL ') + n); if (!ok) fail++; };
function mkView() { const log = []; return { log, running: () => log.push(['running']), result: r => log.push(['result', r]), error: (c, m) => log.push(['error', c, m]), added: r => log.push(['added', r]) }; }
function api(steps, startRes = { ok: true, check_id: 'c1' }, cart = { ok: true, cart_url: '/cart/' }) {
  const calls = { start: 0, step: 0, cart: [], cancel: [] };
  return { calls, start: () => { calls.start++; return Promise.resolve(startRes); },
    step: () => { const s = steps[Math.min(calls.step, steps.length - 1)]; calls.step++; return s instanceof Error ? Promise.reject(s) : Promise.resolve(s); },
    addToCart: (p, a) => { calls.cart.push([p, a]); return Promise.resolve(cart); },
    cancel: (id, permit) => { calls.cancel.push([id, permit]); return Promise.resolve({ok:true}); } };
}
const fast = t => ({ sleep: () => Promise.resolve(), now: () => t.v, budgetMs: 45000 });
(async () => {
  // 1 in stock listed after two running steps
  let t = { v: 0 }, v = mkView(), a = api([{ ok: true, state: 'running' }, { ok: true, state: 'running' }, { ok: true, state: 'done', result: 'in_stock', price_case: 'listed', price_text: '¥31,100', permit: 'P1' }]);
  let f = createFlow(a, v, fast(t));
  let r = await f.run({});
  check('in_stock: spinner first, then result', v.log[0][0] === 'running' && v.log[1][0] === 'result' && r === 'in_stock');
  check('in_stock: polled 3 steps', a.calls.step === 3);
  check('not busy after done', !f.isBusy());
  await f.addToCart('P1', false);
  check('cart: permit sent, quote not accepted, added (stay on product page, no redirect)', a.calls.cart[0][0] === 'P1' && a.calls.cart[0][1] === 0 && v.log.at(-1)[0] === 'added' && !v.log.some(x => x[0] === 'go'));
  // 2 quote: accept flag passes 1
  v = mkView(); a = api([{ ok: true, state: 'done', result: 'in_stock', price_case: 'quote', quote_price_text: '¥32,000', listed_price_text: '¥31,100', permit: 'P2' }]);
  f = createFlow(a, v, fast(t)); await f.run({}); await f.addToCart('P2', true);
  check('quote: result kept and accept=1 sent', v.log[1][1].price_case === 'quote' && a.calls.cart[0][1] === 1);
  check('quote message format', MSG.quote('¥32,000', '¥31,100').includes('¥32,000') && MSG.quote('¥32,000', '¥31,100').includes('掲載価格 ¥31,100'));
  // 3 out of stock
  v = mkView(); a = api([{ ok: true, state: 'done', result: 'out_of_stock' }]); f = createFlow(a, v, fast(t));
  check('out_of_stock result', (await f.run({})) === 'out_of_stock');
  // 4 stale legacy mark must not masquerade as a fresh live stock result.
  v = mkView(); a = api([], { ok: false, code: 'marked_oos' }); f = createFlow(a, v, fast(t));
  r = await f.run({});
  check('legacy marked_oos cannot claim a live sold-out result',
    r === 'error:marked_oos' && a.calls.step === 0 &&
    v.log.at(-1)[0] === 'error');
  // Separate user-initiated checks can immediately move OOS -> available.
  v = mkView(); a = api([{ ok: true, state: 'done', result: 'out_of_stock' }]);
  f = createFlow(a, v, fast(t));
  check('fresh OOS inquiry displays sold-out promptly', (await f.run({})) === 'out_of_stock');
  v = mkView(); a = api([{ ok: true, state: 'done', result: 'in_stock', price_case: 'listed', permit:'NEW' }]);
  f = createFlow(a, v, fast(t));
  check('fresh in-stock inquiry immediately exposes buyable permit',
    (await f.run({})) === 'in_stock' &&
    v.log.at(-1)[1].permit === 'NEW' && a.calls.step === 1);
  // 5 unconfirmed
  v = mkView(); a = api([{ ok: true, state: 'done', result: 'unconfirmed', reason: 'unreachable' }]); f = createFlow(a, v, fast(t));
  check('unconfirmed result', (await f.run({})) === 'unconfirmed');
  // 6 timeout: keeps running past budget -> unconfirmed timeout, never out_of_stock
  t = { v: 0 }; v = mkView(); const steps = [{ ok: true, state: 'running' }];
  a = api(steps); f = createFlow(a, v, { sleep: () => { t.v += 10000; return Promise.resolve(); }, now: () => t.v, budgetMs: 45000 });
  r = await f.run({});
  check('timeout after budget -> unconfirmed/timeout', r === 'unconfirmed' && v.log.at(-1)[1].reason === 'timeout' && a.calls.step <= 6);
  // 7 network error -> error network (not sold out)
  v = mkView(); a = api([new Error('net')]); f = createFlow(a, v, fast({ v: 0 }));
  r = await f.run({});
  check('network failure -> error network', r === 'error:network' && v.log.at(-1)[1] === 'network');
  // 8 rate limited / nonce messages
  v = mkView(); a = api([], { ok: false, code: 'rate_limited' }); f = createFlow(a, v, fast({ v: 0 }));
  check('rate_limited start -> error', (await f.run({})) === 'error:rate_limited');
  check('messages for codes', messageFor('rate_limited') === MSG.rateLimited && messageFor('nonce') === MSG.nonce && messageFor('permit_invalid') === MSG.permitExpired && messageFor('x', 'srv') === 'srv');
  // 9 cancel during running -> no result shown
  let resolveStep; v = mkView();
  a = { start: () => Promise.resolve({ ok: true, check_id: 'c' }), step: () => new Promise(res => { resolveStep = res; }), addToCart: () => Promise.resolve({}) };
  f = createFlow(a, v, fast({ v: 0 }));
  const p = f.run({}); await new Promise(r => setTimeout(r, 0)); f.cancel();
  resolveStep({ ok: true, state: 'done', result: 'in_stock', permit: 'X' });
  check('cancelled run shows nothing after cancel', (await p) === 'cancelled' && v.log.length === 1);
  // 9b cancelled popup explicitly invalidates its non-expiring server permit
  v = mkView(); a = api([{ok: true, state: 'done', result: 'in_stock', permit: 'CANCELME'}]);
  f = createFlow(a, v, fast({v:0}));
  await f.run({}); f.cancel(); await new Promise(res => setTimeout(res, 0));
  check('cancelled stock popup explicitly revokes selected permit',
    a.calls.cancel.length === 1 && a.calls.cancel[0][0] === 'c1' &&
    a.calls.cancel[0][1] === 'CANCELME' && !f.isBusy());

  // 9c successful cart add consumes permit without sending cancel
  v = mkView(); a = api([{ok: true, state: 'done', result: 'in_stock', permit: 'SOLD'}]);
  f = createFlow(a, v, fast({v:0}));
  await f.run({}); await f.addToCart('SOLD', false); f.cancel();
  await new Promise(res => setTimeout(res, 0));
  check('cart success does not revoke already-used permit',
    a.calls.cancel.length === 0);

  // 9d start response arrived after cancel: revoke late server check ID
  let resolveStart, lateRevokes=[];
  v=mkView();a={start:()=>new Promise(resolve=>{resolveStart=resolve;}),
    step:()=>Promise.resolve({ok:true,state:'done',result:'out_of_stock'}),
    cancel:(id,permit)=>{lateRevokes.push([id,permit]);return Promise.resolve({ok:true});}};
  f=createFlow(a,v,fast({v:0}));
  let pendingStart=f.run({});f.cancel();
  resolveStart({ok:true,check_id:'LATESTART'});
  await pendingStart;await new Promise(res=>setTimeout(res,0));
  check('cancel before start response revokes orphan check record',
    lateRevokes.length===1 && lateRevokes[0][0]==='LATESTART');

  // 9e step completes after cancellation: revoke the just-issued permit
  let resolveLateStep;lateRevokes=[];
  v=mkView();a={start:()=>Promise.resolve({ok:true,check_id:'LATESTEP'}),
    step:()=>new Promise(resolve=>{resolveLateStep=resolve;}),
    cancel:(id,permit)=>{lateRevokes.push([id,permit]);return Promise.resolve({ok:true});}};
  f=createFlow(a,v,fast({v:0}));
  let pendingStep=f.run({});
  await new Promise(res=>setTimeout(res,0));
  f.cancel();
  resolveLateStep({ok:true,state:'done',result:'in_stock',permit:'LATETOKEN'});
  await pendingStep;await new Promise(res=>setTimeout(res,0));
  check('cancelled late stock success revokes its newly-issued permit',
    lateRevokes.some(p=>p[0]==='LATESTEP' && p[1]==='LATETOKEN') &&
    !v.log.some(item=>item[0]==='result'));

  // 10 double click while busy -> second run ignored
  v = mkView(); let rs; a = { start: () => new Promise(res => { rs = res; }), step: () => Promise.resolve({ ok: true, state: 'done', result: 'out_of_stock' }), addToCart: () => Promise.resolve({}) };
  f = createFlow(a, v, fast({ v: 0 })); const p1 = f.run({}); const second = await f.run({}); rs({ ok: true, check_id: 'c' }); await p1;
  check('second run while busy ignored', second === 'busy' && v.log.filter(x => x[0] === 'running').length === 1);
  // 10b duplicate add clicks cannot issue duplicate AJAX requests
  let finishAdd, addCount = 0;
  v = mkView(); a = {
    addToCart: () => { addCount++; return new Promise(resolve => { finishAdd=resolve; }); }
  };
  f = createFlow(a, v, fast({v:0}));
  const pending = f.addToCart('P',false);
  const duplicate = await f.addToCart('P',false);
  check('double add-to-cart while request is pending is ignored',
    duplicate === 'busy' && f.isAdding() && addCount === 1);
  finishAdd({ok: true}); await pending;

  // 11 add to cart failure -> error, no redirect
  v = mkView(); a = api([], undefined, { ok: false, code: 'permit_expired' }); f = createFlow(a, v, fast({ v: 0 }));
  await f.addToCart('P', false);
  check('add failure -> error shown (popup stays open), not added', v.log.at(-1)[0] === 'error' && v.log.at(-1)[1] === 'permit_expired' && !v.log.some(x => x[0] === 'added'));
  // 11b add network failure -> error network, no automatic retry
  v = mkView(); let n = 0; a = { start: () => Promise.resolve({}), step: () => Promise.resolve({}), addToCart: () => { n++; return Promise.reject(new Error('x')); } };
  f = createFlow(a, v, fast({ v: 0 })); await f.addToCart('P', false);
  check('add network failure -> error, called once (no auto retry)', v.log.at(-1)[1] === 'network' && n === 1);
  // 11c unconfirmed -> no further step calls after the result (no auto retry / no holding)
  v = mkView(); a = api([{ ok: true, state: 'done', result: 'unconfirmed', reason: 'unreachable' }]); f = createFlow(a, v, fast({ v: 0 }));
  await f.run({}); await new Promise(r => setTimeout(r, 5));
  check('unconfirmed -> stops, one step only, not busy', a.calls.step === 1 && !f.isBusy());
  check('unconfirmed message tells it could not connect and asks to retry later', /つながらず/.test(MSG.unconfirmed) && /時間をおいて/.test(MSG.unconfirmed));
  // 11d size label: cm shown only when Woo label has it
  check('size label US 3Y (23cm) -> US 3Y / 23cm', sizeLabel('US 3Y (23cm)') === 'US 3Y / 23cm');
  check('size label US 9 unchanged (no guessed cm)', sizeLabel('US 9') === 'US 9' && sizeLabel('US 14.0') === 'US 14.0');
  // 11e buttons: cart label + cancel under it
  const js = require('fs').readFileSync(__dirname + '/../../local-snapshot-2026-11-15/mu-plugins/ahc-stock-check-ui.js', 'utf8');
  check('cart button label and cancel present', (js.match(/この商品をカートに入れる/g) || []).length === 2 && (js.match(/'キャンセル'/g) || []).length === 2 && !/location\.href/.test(js));
  check('live UI can change in both directions without modifying Woo variation cache',
    /showLiveAvailability\('in_stock'\)/.test(js) &&
    /showLiveAvailability\('out_of_stock'\)/.test(js) &&
    !/function markSoldOut\(/.test(js) &&
    !/v\.is_in_stock\s*=\s*false/.test(js) &&
    /もう一度在庫確認できます/.test(js));

  // 12 no email/name fields in UI markup (owner 12:40)
  const php = require('fs').readFileSync(__dirname + '/../../local-snapshot-2026-11-15/mu-plugins/ahc-stock-check-ui.php', 'utf8');
  check('popup has no input/textarea fields', !/<input|<textarea/.test(php.slice(php.indexOf('<dialog'), php.indexOf('</dialog>'))));
  check('stock UI server markup does not install shared 24h OOS filter',
    !php.includes('_ahc_inline_oos_until') &&
    !php.includes("add_filter('woocommerce_available_variation'"));

  check('in-stock wording', MSG.inStock === '在庫確認できました。カートに入れられます。');
  process.exit(fail ? 1 : 0);
})();
