/* Quiz flow: one question per screen, auto-advance after grading. */
(function () {
  'use strict';

  var M = window.M14;
  var stmtEl = document.getElementById('stmt');
  var optionsEl = document.getElementById('options');
  var submitBtn = document.getElementById('submit');
  var feedbackEl = document.getElementById('feedback');

  var question = window.__INITIAL_QUESTION__ || null;
  var selected = -1;
  var locked = false;
  var shownAt = Date.now();
  var prefetched = null;

  function fetchQuestion() {
    return M.api('/api/question').then(function (q) {
      return q;
    });
  }

  function renderQuestion(q) {
    if (!q) {
      stmtEl.textContent = '暫時無法出題，請重新整理。';
      return;
    }
    question = q;
    selected = -1;
    locked = false;
    prefetched = null;
    shownAt = Date.now();
    feedbackEl.textContent = '';
    feedbackEl.className = 'feedback';
    submitBtn.disabled = true;
    submitBtn.textContent = '提交';

    M.renderTex(stmtEl, q.stmt_tex);
    optionsEl.innerHTML = '';
    q.choices.forEach(function (tex, i) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'option';
      btn.dataset.index = String(i);
      var letter = document.createElement('span');
      letter.className = 'letter';
      letter.textContent = 'ABCD'[i];
      var body = document.createElement('span');
      body.className = 'body';
      btn.appendChild(letter);
      btn.appendChild(body);
      M.renderChoice(body, tex);
      btn.addEventListener('click', function () { select(i); });
      optionsEl.appendChild(btn);
    });
  }

  function select(i) {
    if (locked) { return; }
    selected = i;
    Array.prototype.forEach.call(optionsEl.children, function (el, idx) {
      el.classList.toggle('selected', idx === i);
    });
    submitBtn.disabled = false;
    M.vibrate(10);
  }

  function paint(result) {
    Array.prototype.forEach.call(optionsEl.children, function (el, idx) {
      el.disabled = true;
      el.classList.remove('selected');
      if (idx === result.correct_index) { el.classList.add('correct'); }
      if (idx === result.your_index && !result.ok) { el.classList.add('wrong'); }
      if (idx !== result.correct_index && idx !== result.your_index) { el.classList.add('dim'); }
    });
  }

  function feedbackText(result) {
    if (result.too_fast) { return '答得太快，不計分'; }
    if (result.ok) { return '✅ 正確 +' + result.points; }
    if (result.reveal_tex) { return '❌ 以上皆非　正確答案已顯示於下方'; }
    return '❌ 答錯了';
  }

  function showReveal(result) {
    if (!result.reveal_tex) { return; }
    var box = document.createElement('div');
    box.className = 'reveal-box';
    var label = document.createElement('span');
    label.textContent = '正確答案：';
    var tex = document.createElement('span');
    M.renderTex(tex, result.reveal_tex);
    box.appendChild(label);
    box.appendChild(tex);
    feedbackEl.appendChild(box);
  }

  async function submit() {
    if (locked || selected < 0 || !question) { return; }
    locked = true;
    submitBtn.disabled = true;
    var ms = Date.now() - shownAt;
    try {
      var result = await M.api('/api/answer', {
        method: 'POST',
        body: { qid: question.qid, choice: selected, ms: ms }
      });
      paint(result);
      feedbackEl.className = 'feedback ' + (result.ok ? 'good' : 'bad');
      feedbackEl.textContent = feedbackText(result);
      showReveal(result);
      M.setText('score', result.score);
      M.setText('streak', result.streak);
      M.setText('today', result.day_attempts);
      M.vibrate(result.ok ? 30 : [20, 40, 20]);
      prefetched = result.next || null;
      setTimeout(next, 900);
    } catch (err) {
      locked = false;
      submitBtn.disabled = false;
      feedbackEl.className = 'feedback bad';
      feedbackEl.textContent = err.message || '提交失敗，請重試';
    }
  }

  function next() {
    if (prefetched) {
      var q = prefetched;
      renderQuestion(q);
      return;
    }
    fetchQuestion().then(renderQuestion).catch(function (err) {
      stmtEl.textContent = '載入失敗：' + err.message;
    });
  }

  submitBtn.addEventListener('click', submit);

  document.addEventListener('keydown', function (e) {
    if (e.key >= '1' && e.key <= '4') {
      select(parseInt(e.key, 10) - 1);
    } else if (e.key === 'Enter') {
      if (locked) { return; }
      submit();
    }
  });

  if (question) {
    renderQuestion(question);
  } else {
    next();
  }
})();
