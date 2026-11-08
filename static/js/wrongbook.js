/* Wrong-book page: render stored LaTeX and support deleting entries. */
(function () {
  'use strict';

  var M = window.M14;

  function renderAll() {
    document.querySelectorAll('[data-tex]').forEach(function (el) {
      M.renderTex(el, el.getAttribute('data-tex'));
    });
  }

  document.addEventListener('click', async function (e) {
    var btn = e.target.closest('.del');
    if (!btn) { return; }
    var qid = btn.getAttribute('data-qid');
    if (!window.confirm('確定刪除這筆記錄？')) { return; }
    try {
      await M.api('/api/wrongbook/' + encodeURIComponent(qid), { method: 'DELETE' });
      var card = btn.closest('.card');
      if (card) { card.remove(); }
      if (!document.querySelector('.card')) {
        location.reload();
      }
    } catch (err) {
      alert(err.message || '刪除失敗');
    }
  });

  renderAll();
})();
