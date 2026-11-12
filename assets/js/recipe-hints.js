/* The stock and spice hints on a recipe's ingredient lines (MANUAL §8.2), in
   the cocktails' ship-key pattern (ship-key.js): a small ringed i after the
   line opens a modal box saying how much, closed by its ×, Escape or a click
   on the backdrop. The words are HTF.foodHints'; this file finds the lines,
   builds the one box, and fills it from the line that opened it.

   A hint reads the line's amount as it is when opened, so it follows the
   scaler and the metric switch. Built here, not in the layout, so a browser
   without the script or without `showModal` shows no button. */
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

  var dialog = document.createElement('dialog');
  if (typeof dialog.showModal !== 'function') return;
  dialog.className = 'ingredient-hint';
  dialog.id = 'ingredient-hint';
  dialog.setAttribute('aria-labelledby', 'ingredient-hint-title');

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  var body = el('div', 'ingredient-hint-body');
  var form = el('form', 'ingredient-hint-close-form');
  form.method = 'dialog';
  var close = el('button', 'ingredient-hint-close', '×');
  close.setAttribute('aria-label', 'close');
  form.appendChild(close);
  var title = el('h2', 'ingredient-hint-title');
  title.id = 'ingredient-hint-title';
  var content = el('div', 'ingredient-hint-content');
  body.appendChild(form);
  body.appendChild(title);
  body.appendChild(content);
  dialog.appendChild(body);

  dialog.addEventListener('click', function (event) {
    if (event.target === dialog) dialog.close();
  });

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
      '.ingredient-amount, .ingredient-annotation, .ingredient-hint-open, input'
    ), function (n) { n.parentNode.removeChild(n); });
    return copy.textContent.replace(/\s+/g, ' ').trim();
  }

  function hintFor(row) {
    var amount = amountOf(row);
    var item = itemOf(row);
    return HTF.foodHints.stockHint(amount, item, data) ||
      HTF.foodHints.spiceHint(amount, item, data);
  }

  function fill(row, hint) {
    title.textContent = (amountOf(row) + ' ' + itemOf(row)).trim();
    content.textContent = '';
    content.appendChild(el('p', 'ingredient-hint-lead', hint.title));
    if (hint.rows.length) {
      var list = el('dl', 'ingredient-hint-list');
      hint.rows.forEach(function (r) {
        var line = el('div', 'ingredient-hint-row');
        line.appendChild(el('dt', null, r.amount));
        line.appendChild(el('dd', null, r.what));
        list.appendChild(line);
      });
      content.appendChild(list);
    }
    hint.lines.forEach(function (text) {
      content.appendChild(el('p', 'ingredient-hint-line', text));
    });
  }

  var wired = 0;
  Array.prototype.forEach.call(article.querySelectorAll('.ingredients li.ingredient'), function (row) {
    if (!hintFor(row)) return;
    wired += 1;
    // The i is drawn by CSS, so no text read off the line ever carries it.
    var button = el('button', 'ingredient-hint-open');
    button.type = 'button';
    button.setAttribute('aria-haspopup', 'dialog');
    button.setAttribute('aria-controls', 'ingredient-hint');
    button.setAttribute('aria-label', 'how much');
    button.addEventListener('click', function (event) {
      // A tap here opens the box and never ticks the line (ingredient-ticks.js).
      event.stopPropagation();
      var hint = hintFor(row);
      if (!hint) return;
      fill(row, hint);
      dialog.showModal();
    });
    row.insertBefore(button, row.querySelector('.ingredient-annotation'));
  });

  if (wired) document.body.appendChild(dialog);
})();
