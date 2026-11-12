/* The tap-to-open hints on a recipe's ingredient lines (MANUAL §8.2): a small
   ⓘ after a stock line or a ground spice, opening the hint beneath it. The
   words are HTF.foodHints'; this file finds the lines and draws them.

   The hint is worked out from the amount as it reads when opened, so it
   follows the scaler and the metric switch, and an open hint is redrawn when
   that amount changes. Built here, not in the layout, so a reader without the
   script sees no button. A tap on the button never ticks the line. */
(function () {
  'use strict';

  var HTF = window.HTF;
  var article = document.querySelector('article.recipe');
  var source = document.getElementById('ingredient-hints-data');
  if (!HTF || !HTF.foodHints || !article || !source) return;

  var data;
  try {
    data = JSON.parse(source.textContent);
  } catch (e) {
    return;
  }

  function amountOf(row) {
    var span = row.querySelector('.ingredient-amount-number');
    if (!span) return '';
    var out = '';
    Array.prototype.forEach.call(span.childNodes, function (node) {
      if (node.nodeType === 3) out += node.nodeValue;
    });
    return out.trim();
  }

  function itemOf(row) {
    var copy = row.cloneNode(true);
    Array.prototype.forEach.call(copy.querySelectorAll(
      '.ingredient-amount, .ingredient-annotation, .ingredient-hint-toggle, .ingredient-hint, input'
    ), function (n) { n.parentNode.removeChild(n); });
    return copy.textContent.replace(/\s+/g, ' ').trim();
  }

  function hintFor(row) {
    var amount = amountOf(row);
    var item = itemOf(row);
    return HTF.foodHints.stockHint(amount, item, data) ||
      HTF.foodHints.spiceHint(amount, item, data);
  }

  var count = 0;

  function wire(row) {
    if (!hintFor(row)) return;
    count += 1;
    var id = 'ingredient-hint-' + count;

    var button = document.createElement('button');
    button.type = 'button';
    button.className = 'ingredient-hint-toggle';
    button.setAttribute('aria-expanded', 'false');
    button.setAttribute('aria-controls', id);
    button.setAttribute('aria-label', 'how much');

    var panel = document.createElement('span');
    panel.className = 'ingredient-hint';
    panel.id = id;
    panel.hidden = true;

    function draw() {
      var hint = hintFor(row);
      panel.textContent = '';
      if (!hint) return;
      var title = document.createElement('span');
      title.className = 'ingredient-hint-title';
      title.textContent = hint.title;
      panel.appendChild(title);
      hint.lines.forEach(function (line) {
        var part = document.createElement('span');
        part.className = 'ingredient-hint-line';
        part.textContent = line;
        panel.appendChild(part);
      });
    }

    button.addEventListener('click', function (event) {
      event.stopPropagation();
      var open = panel.hidden;
      if (open) draw();
      panel.hidden = !open;
      button.setAttribute('aria-expanded', open ? 'true' : 'false');
    });

    panel.addEventListener('click', function (event) { event.stopPropagation(); });

    var note = row.querySelector('.ingredient-annotation');
    row.insertBefore(button, note);
    row.appendChild(panel);

    var span = row.querySelector('.ingredient-amount-number');
    if (span && window.MutationObserver) {
      new MutationObserver(function () {
        if (!panel.hidden) draw();
      }).observe(span, { childList: true, characterData: true, subtree: true });
    }
  }

  Array.prototype.forEach.call(article.querySelectorAll('.ingredients li.ingredient'), wire);
})();
