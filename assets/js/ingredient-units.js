/* The IMPERIAL / METRIC switch under INGREDIENTS (MANUAL §8.2), only on a
   recipe written in ounces, pounds, fluid ounces or pints. Imperial, as
   written, is the default and nothing is remembered. Metric is the shopping
   list's conversion, applied by recipe-scale.js, so it holds at any scale.

   It shares a row with the tick boxes' button (ingredient-ticks.js): whichever
   script runs first makes `.ingredient-switches`. Built here, not in the
   layout, so a reader without the script never sees it. */
(function () {
  'use strict';

  var HTF = window.HTF;
  var scale = HTF && HTF.recipeScale;
  var article = document.querySelector('article.recipe');
  var section = article && article.querySelector('.recipe-section-ingredients');
  if (!scale || !scale.imperial || !section) return;

  var row = section.querySelector('.ingredient-switches');
  if (!row) {
    row = document.createElement('div');
    row.className = 'ingredient-switches';
    section.appendChild(row);
  }

  var button = document.createElement('button');
  button.type = 'button';
  button.className = 'ingredient-units';
  button.setAttribute('role', 'switch');
  button.setAttribute('aria-label', 'metric');
  ['imperial', null, 'metric'].forEach(function (text) {
    var part = document.createElement('span');
    if (text) {
      part.className = 'ingredient-units-word ingredient-units-' + text;
      part.textContent = text;
    } else {
      part.className = 'ingredient-units-track';
      part.setAttribute('aria-hidden', 'true');
    }
    button.appendChild(part);
  });

  var metric = false;

  function set(value) {
    metric = value;
    button.setAttribute('aria-checked', metric ? 'true' : 'false');
    button.classList.toggle('is-metric', metric);
    scale.setMetric(metric);
  }

  button.addEventListener('click', function () { set(!metric); });

  set(false);
  row.appendChild(button);
})();
