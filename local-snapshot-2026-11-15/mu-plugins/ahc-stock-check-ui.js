/*
 * 在庫確認（その場で判定 → カートへ）の画面側。Claude、2026-11-21。
 * 設計：docs/stock-check-inline-final-design-claude-2026-11-21.md（§2 画面、§10 サーバーとの約束）
 * サーバー側（ahc_sc_start / ahc_sc_step / ahc_sc_add_to_cart）は GPT 担当。
 * 流れの部分（createFlow）は DOM に依存しないので、node でテストできる（qa/js-tests/stock_check_ui_flow_test.js）。
 */
(function (root) {
  'use strict';

  var MSG = {
    running: '在庫を確認しています…',
    inStock: '在庫確認できました。カートに入れられます。',
    quote: function (q, l) { return '在庫確認できました。現在の販売価格は ' + q + ' です（掲載価格 ' + l + '）。'; },
    outOfStock: 'このサイズは現在在庫がありません。',
    unconfirmed: '買い付け先のサイトにつながらず、在庫を確認できませんでした。お手数ですが、時間をおいてもう一度在庫を確認してください。',
    added: 'カートに追加しました。',
    network: '通信に失敗しました。時間をおいてもう一度お試しください。',
    rateLimited: '短時間に続けて確認されました。少し待ってからもう一度お試しください。',
    nonce: '画面の有効期限が切れました。ページを再読み込みしてから、もう一度お試しください。',
    permitExpired: '確認から時間がたちました。もう一度在庫を確認してください。',
    invalid: '選択内容を確認できませんでした。カラーとサイズを選び直してください。'
  };

  /**
   * 流れ。api: {start(sel), step(checkId), addToCart(permit, acceptQuote)} はすべて Promise を返す。
   * view: {running(), result(r), error(code, message), added(r)}。
   * カート追加が成功したら added を呼ぶ（ポップアップを閉じて商品ページに留まる。オーナー確定 2026-11-21 20:15）。
   * 失敗したら error を呼ぶ（ポップアップは開いたまま）。自動の再試行はしない。
   */
  function createFlow(api, view, opts) {
    opts = opts || {};
    var now = opts.now || function () { return Date.now(); };
    var sleep = opts.sleep || function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
    var budgetMs = opts.budgetMs || 45000;
    var intervalMs = opts.intervalMs || 1000;
    var token = 0;
    var busy = false;

    function errorFrom(r) {
      var code = (r && r.code) || 'network';
      if (code === 'marked_oos') return { kind: 'result', r: { result: 'out_of_stock' } };
      return { kind: 'error', code: code, message: (r && r.message) || '' };
    }

    function run(selection) {
      if (busy) return Promise.resolve('busy');
      var my = ++token;
      busy = true;
      view.running();
      var t0 = now();
      function finish(x) { if (my === token) busy = false; return x; }
      function handle(e) {
        if (my !== token) return 'cancelled';
        if (e.kind === 'result') { view.result(e.r); return e.r.result; }
        view.error(e.code, e.message); return 'error:' + e.code;
      }
      function loop(checkId) {
        if (my !== token) return Promise.resolve('cancelled');
        if (now() - t0 > budgetMs) { view.result({ result: 'unconfirmed', reason: 'timeout' }); return Promise.resolve('unconfirmed'); }
        return api.step(checkId).then(function (s) {
          if (my !== token) return 'cancelled';
          if (!s || !s.ok) return handle(errorFrom(s));
          if (s.state === 'done') { view.result(s); return s.result; }
          return sleep(intervalMs).then(function () { return loop(checkId); });
        });
      }
      return api.start(selection).then(function (r) {
        if (my !== token) return 'cancelled';
        if (!r || !r.ok) return handle(errorFrom(r));
        return loop(r.check_id);
      }).catch(function () {
        return handle({ kind: 'error', code: 'network', message: '' });
      }).then(finish, finish);
    }

    function cancel() { token++; busy = false; }

    function addToCart(permit, acceptQuote) {
      return api.addToCart(permit, acceptQuote ? 1 : 0).then(function (r) {
        if (r && r.ok) { view.added(r); return 'added'; }
        var e = errorFrom(r); view.error(e.code, e.message); return 'error:' + e.code;
      }).catch(function () { view.error('network', ''); return 'error:network'; });
    }

    return { run: run, cancel: cancel, addToCart: addToCart, isBusy: function () { return busy; } };
  }

  function messageFor(code, serverMessage) {
    if (code === 'rate_limited') return MSG.rateLimited;
    if (code === 'nonce') return MSG.nonce;
    if (code === 'permit_expired' || code === 'permit_invalid') return MSG.permitExpired;
    if (code === 'invalid_selection') return MSG.invalid;
    if (code === 'network') return MSG.network;
    return serverMessage || MSG.unconfirmed;
  }

  /* サイズの表示：Woo のサイズに cm の対応が書いてある場合だけ「US 9 / 27cm」形式にする。推測で cm を足さない。
   * 元のサイズの値（結合・カートに使う値）は変えない。表示用の文字だけ。 */
  function sizeLabel(text) {
    var t = String(text == null ? '' : text).trim();
    var m = t.match(/^(.*?)\s*\(\s*(\d+(?:\.\d+)?)\s*cm\s*\)$/i);
    return m ? m[1] + ' / ' + m[2] + 'cm' : t;
  }

  var exported = { createFlow: createFlow, MSG: MSG, messageFor: messageFor, sizeLabel: sizeLabel };
  if (typeof module !== 'undefined' && module.exports) module.exports = exported;
  root.AHC_SC_UI = exported;

  /* ------------------------------ 画面への取り付け ------------------------------ */
  if (typeof document === 'undefined') return;
  var CFG = root.AHC_SC_CFG || {};

  function post(action, data) {
    var fd = new FormData();
    fd.append('action', action);
    fd.append('nonce', CFG.nonce || '');
    Object.keys(data).forEach(function (k) { fd.append(k, data[k]); });
    return fetch(CFG.ajaxUrl, { method: 'POST', body: fd, credentials: 'same-origin' })
      .then(function (res) { return res.json(); })
      .then(function (j) {
        // wp_send_json_success/error の形 {success, data} と、素の {ok,...} の両方を受ける
        if (j && typeof j.success === 'boolean') { var d = j.data || {}; if (typeof d.ok !== 'boolean') d.ok = j.success; return d; }
        return j;
      });
  }

  function init() {
    var box = document.querySelector('.ahc-sc');
    if (!box) return;
    var form = box.closest('form') || null;
    var openBtn = box.querySelector('.ahc-sc-open');
    var reason = box.querySelector('.ahc-sc-reason');
    var dialog = box.querySelector('.ahc-sc-dialog');
    var itemEl = box.querySelector('.ahc-sc-item');
    var statusEl = box.querySelector('.ahc-sc-status');
    var spinner = box.querySelector('.ahc-sc-spinner');
    var actions = box.querySelector('.ahc-sc-actions');
    var variable = box.dataset.variable === '1';
    var current = null; // 見つかったバリエーション（Woo の found_variation）

    function selects() { return form ? Array.prototype.slice.call(form.querySelectorAll('select[name^="attribute_"]')) : []; }
    function itemText() {
      return selects().map(function (s) {
        var o = s.options[s.selectedIndex];
        return o && s.value ? sizeLabel(o.text.replace(/\s*SOLD OUT\s*$/, '')) : '';
      }).filter(Boolean).join(' / ');
    }
    function selection() {
      var d = { product_id: box.dataset.productId, variation_id: current ? current.variation_id : 0 };
      selects().forEach(function (s) { d[s.name] = s.value; });
      return d;
    }
    function setOpenable(ok, why) { openBtn.disabled = !ok; reason.textContent = ok ? '' : why; }
    function openDialog() { if (dialog.showModal) { if (!dialog.open) dialog.showModal(); } else dialog.setAttribute('open', ''); }
    // 閉じる・キャンセル：カートには入れずに閉じる。サイズの選択はそのまま残す（フォームには触らない）。
    function closeDialog() { flow.cancel(); if (dialog.close) { if (dialog.open) dialog.close(); } else dialog.removeAttribute('open'); }
    function button(label, cls, onClick) {
      var b = document.createElement('button'); b.type = 'button'; b.className = cls; b.textContent = label;
      b.addEventListener('click', onClick); actions.appendChild(b); return b;
    }
    function clearActions() { actions.innerHTML = ''; }
    function setStatus(text, isError) { statusEl.textContent = text; statusEl.classList.toggle('is-error', !!isError); }

    // 品切れ確定：このページでもそのサイズを SOLD OUT にする（他のお客様向けの表示はサーバーの品切れの印で行う）
    function markSoldOut() {
      if (!variable || !current || !form) { setOpenable(false, 'SOLD OUT'); return; }
      var vid = current.variation_id;
      try {
        var list = JSON.parse(form.getAttribute('data-product_variations') || '[]');
        list.forEach(function (v) { if (v.variation_id === vid) { v.is_in_stock = false; v.is_purchasable = false; } });
        form.setAttribute('data-product_variations', JSON.stringify(list));
      } catch (e) { /* 一覧が無い（AJAX 読み込み）場合は下の jQuery 側だけ */ }
      if (root.jQuery) {
        var cached = root.jQuery(form).data('product_variations');
        if (Array.isArray(cached)) cached.forEach(function (v) { if (v.variation_id === vid) { v.is_in_stock = false; v.is_purchasable = false; } });
        var size = selects().filter(function (s) { return /size/i.test(s.name); })[0] || selects()[selects().length - 1];
        if (size) root.jQuery(size).trigger('change');
      }
      setOpenable(false, 'このサイズは SOLD OUT です');
    }

    var view = {
      running: function () {
        clearActions(); spinner.hidden = false; setStatus(MSG.running, false);
      },
      result: function (r) {
        spinner.hidden = true; clearActions();
        if (r.result === 'in_stock' && r.price_case === 'quote') {
          setStatus(MSG.quote(r.quote_price_text, r.listed_price_text), false);
          button('この商品をカートに入れる', 'button alt ahc-sc-cart', function () { this.disabled = true; flow.addToCart(r.permit, true); });
          button('キャンセル', 'ahc-sc-link ahc-sc-cancel', closeDialog);
        } else if (r.result === 'in_stock') {
          var priceText = r.price_text || r.listed_price_text; // GPT のステージング版は listed_price_text だけを返す
          setStatus(MSG.inStock + (priceText ? '　販売価格：' + priceText : ''), false);
          button('この商品をカートに入れる', 'button alt ahc-sc-cart', function () { this.disabled = true; flow.addToCart(r.permit, false); });
          button('キャンセル', 'ahc-sc-link ahc-sc-cancel', closeDialog);
        } else if (r.result === 'out_of_stock') {
          setStatus(MSG.outOfStock, false);
          markSoldOut();
          button('閉じる', 'ahc-sc-link', closeDialog);
        } else {
          setStatus(MSG.unconfirmed, true);
          button('閉じる', 'ahc-sc-link', closeDialog);
        }
      },
      error: function (code, message) {
        spinner.hidden = true; clearActions();
        setStatus(messageFor(code, message), true);
        button('閉じる', 'ahc-sc-link', closeDialog);
      },
      // カート追加成功：ポップアップを閉じて商品ページに留まる。ミニカートの数字を更新し、ボタンの下に一言出す。
      added: function () {
        spinner.hidden = true; clearActions(); setStatus('', false);
        closeDialog();
        reason.textContent = MSG.added;
        if (root.jQuery) root.jQuery(document.body).trigger('wc_fragment_refresh');
      }
    };
    var flow = createFlow({
      start: function (sel) { return post('ahc_sc_start', sel); },
      step: function (id) { return post('ahc_sc_step', { check_id: id }); },
      addToCart: function (permit, accept) { return post('ahc_sc_add_to_cart', { permit: permit, accept_quote: accept }); }
    }, view, { budgetMs: (CFG.budgetSeconds || 45) * 1000 });

    if (variable && root.jQuery && form) {
      var $f = root.jQuery(form);
      $f.on('found_variation', function (e, v) {
        current = v;
        if (v && v.is_in_stock && v.is_purchasable !== false) setOpenable(true, '');
        else setOpenable(false, 'このサイズは SOLD OUT です');
      });
      $f.on('reset_data hide_variation', function () { current = null; setOpenable(false, 'カラー・サイズを選択してください'); });
      // 選び直したら、開いているポップアップと途中の確認は捨てる
      $f.on('woocommerce_variation_select_change', function () { if (dialog.open) closeDialog(); });
    }
    openBtn.addEventListener('click', function () {
      if (openBtn.disabled || flow.isBusy()) return;
      itemEl.textContent = (box.dataset.productName || '') + (itemText() ? ' / ' + itemText() : '');
      openDialog();
      flow.run(selection());
    });
    dialog.addEventListener('click', function (e) { if (e.target === dialog) closeDialog(); });
    dialog.addEventListener('cancel', function () { flow.cancel(); });
    box.querySelector('.ahc-sc-close').addEventListener('click', closeDialog);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})(typeof window !== 'undefined' ? window : this);
