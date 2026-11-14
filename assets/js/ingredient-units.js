/* The IMPERIAL / METRIC switch under INGREDIENTS (MANUAL §8.2), only on a
   recipe written in ounces, pounds, fluid ounces or pints. Imperial, as
   written, is the default and nothing is remembered. Metric is the shopping
   list's conversion, applied by recipe-scale.js, so it holds at any scale.

   It shares a row, and its look, with the tick boxes' switch
   (ingredient-ticks.js, _ingredient-switches.scss): whichever script runs
   first makes `.ingredient-switches`. Built here, not in the layout, so a
   reader without the script never sees it. */
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
  button.className = 'ingredient-switch ingredient-units';
  button.setAttribute('role', 'switch');
  button.setAttribute('aria-label', 'metric');
  [['off', 'imperial'], ['track', null], ['on', 'metric']].forEach(function (pair) {
    var part = document.createElement('span');
    part.className = 'ingredient-switch-' + pair[0];
    if (pair[1]) part.textContent = pair[1];
    else part.setAttribute('aria-hidden', 'true');
    button.appendChild(part);
  });

  var metric = false;

  function set(value) {
    metric = value;
    button.setAttribute('aria-checked', metric ? 'true' : 'false');
    scale.setMetric(metric);
  }

  button.addEventListener('click', function () { set(!metric); });

  set(false);
  row.appendChild(button);
})();
