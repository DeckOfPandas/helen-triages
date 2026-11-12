/* The recipe page's tick boxes (#1504): a TICK BOXES OFF / ON button under
   INGREDIENTS puts a box beside every ingredient line, to tick off as it goes
   in. Off by default and never remembered, like cocktails' make it; a page
   that is not ticking prints and reads exactly as before. The button is built
   here, not in the layout: it does nothing without this script, so a reader
   without it never sees it.

   A box is the first child of its <li>; recipe-scale.js steps over
   `.ingredient-tick` when it looks for a line's own text. Tapping anywhere on a
   line ticks it, except a link, which still goes where it says. */
(function () {
  'use strict';

  var article = document.querySelector('article.recipe');
  var section = article && article.querySelector('.recipe-section-ingredients');
  var rows = article ? article.querySelectorAll('.ingredients li.ingredient') : [];
  if (!section || !rows.length) return;

  var bar = document.createElement('div');
  bar.className = 'ingredient-ticks';
  var button = document.createElement('button');
  button.type = 'button';
  button.className = 'ingredient-ticks-pill';
  bar.appendChild(button);

  var on = false;

  function boxFor(row) {
    var box = row.querySelector('input.ingredient-tick');
    if (box) return box;
    var copy = row.cloneNode(true);
    Array.prototype.forEach.call(copy.querySelectorAll('.ingredient-annotation'), function (n) {
      n.parentNode.removeChild(n);
    });
    box = document.createElement('input');
    box.type = 'checkbox';
    box.className = 'ingredient-tick';
    box.setAttribute('aria-label', copy.textContent.replace(/\s+/g, ' ').trim());
    box.addEventListener('change', function () {
      row.classList.toggle('is-ticked', box.checked);
    });
    row.insertBefore(box, row.firstChild);
    row.addEventListener('click', function (event) {
      if (!on || event.target === box || event.target.closest('a')) return;
      box.checked = !box.checked;
      row.classList.toggle('is-ticked', box.checked);
    });
    return box;
  }

  function set(value) {
    on = value;
    if (on) Array.prototype.forEach.call(rows, boxFor);
    article.classList.toggle('is-ticking', on);
    button.textContent = on ? 'tick boxes on' : 'tick boxes off';
    // The words carry the state, so there is no aria-pressed to say it twice.
    button.classList.toggle('is-on', on);
  }

  button.addEventListener('click', function () { set(!on); });

  set(false);
  section.appendChild(bar);
})();
