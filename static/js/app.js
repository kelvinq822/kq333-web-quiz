/* Shared helpers: KaTeX rendering, fetch wrapper, small utilities. */
(function () {
  'use strict';

  var hasKatex = typeof window.katex !== 'undefined';

  function renderTex(el, tex) {
    if (!el) { return; }
    if (!hasKatex) { el.textContent = tex; return; }
    try {
      window.katex.render(tex, el, { throwOnError: false, displayMode: false, trust: false });
    } catch (err) {
      el.textContent = tex;
    }
  }

  function isPlain(tex) {
    return tex === '以上皆非';
  }

  function renderChoice(el, tex) {
    if (isPlain(tex)) {
      el.textContent = tex;
      el.classList.add('plain');
      return;
    }
    renderTex(el, tex);
  }

  async function api(path, options) {
    var opts = options || {};
    var res = await fetch(path, {
      method: opts.method || 'GET',
      headers: opts.body ? { 'Content-Type': 'application/json' } : undefined,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
      credentials: 'same-origin'
    });
    var data = null;
    try { data = await res.json(); } catch (e) { data = null; }
    if (!res.ok) {
      var msg = (data && data.message) || ('HTTP ' + res.status);
      var err = new Error(msg);
      err.status = res.status;
      err.data = data;
      throw err;
    }
    return data;
  }

  function setText(id, value) {
    var el = document.getElementById(id);
    if (el) { el.textContent = value; }
  }

  function vibrate(ms) {
    if (navigator.vibrate) { try { navigator.vibrate(ms); } catch (e) {} }
  }

  window.M14 = {
    renderTex: renderTex,
    renderChoice: renderChoice,
    isPlain: isPlain,
    api: api,
    setText: setText,
    vibrate: vibrate,
    hasKatex: hasKatex
  };
})();
