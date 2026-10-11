// results-bar.js
// The sticky results bar: "N survivors" and `× clear all`, following the
// reader down the page, on both indexes.
//
// A mirror: nothing here counts anything. It copies the count spans the index
// script paints and the top `× clear all`'s visibility, and its own button
// clicks that one, so it cannot disagree with the line it stands in for.
//
// Shown only while `#results` is not intersecting AND above the viewport.
// Without IntersectionObserver the markup stays `hidden`.
//
// Wired on DOMContentLoaded and loaded after the index script: filters.js
// builds its clear-all buttons in its own DOMContentLoaded handler, and
// listeners fire in registration order (tests/test_site_config.py holds the
// script order).

(function () {
  'use strict';

  var COUNT_IDS = [
    ['recipe-count-n', 'recipe-count-word'],
    ['drink-count-n', 'drink-count-word']
  ];

  function all(selector) {
    return Array.prototype.slice.call(document.querySelectorAll(selector));
  }

  /* The count spans this page actually has. null on a page with neither. */
  function findCount() {
    for (var i = 0; i < COUNT_IDS.length; i++) {
      var n = document.getElementById(COUNT_IDS[i][0]);
      var w = document.getElementById(COUNT_IDS[i][1]);
      if (n && w) return { n: n, w: w };
    }
    return null;
  }

  /* The top `× clear all`: the first `.btn-clear` in document order that is
     not the bar's own. Looked up each time, because a script builds it. */
  function topClear(bar) {
    var buttons = all('.btn-clear');
    for (var i = 0; i < buttons.length; i++) {
      if (!buttons[i].closest('[data-results-bar]')) return buttons[i];
    }
    return null;
  }

  function wire() {
    var bar = document.querySelector('[data-results-bar]');
    var heading = document.getElementById('results');
    if (!bar || !heading) return;
    if (typeof window.IntersectionObserver !== 'function') return;

    var count = findCount();
    if (!count) return;

    var barN = bar.querySelector('[data-results-bar-n]');
    var barWord = bar.querySelector('[data-results-bar-word]');
    var barClear = bar.querySelector('[data-results-bar-clear]');

    function sync() {
      if (barN) barN.textContent = count.n.textContent;
      if (barWord) barWord.textContent = count.w.textContent;
      if (barClear) {
        var top = topClear(bar);
        /* Read off the inline `style.visibility` the index scripts write.
           Anything but an explicit `visible` is hidden, the resting state. */
        barClear.style.visibility =
          top && top.style.visibility === 'visible' ? 'visible' : 'hidden';
      }
    }

    if (barClear) {
      barClear.addEventListener('click', function () {
        var top = topClear(bar);
        if (top) top.click();
        /* The index script repaints synchronously, so the count is current. */
        sync();
      });
    }

    if (typeof window.MutationObserver === 'function') {
      var watcher = new MutationObserver(sync);
      var textChanges = { childList: true, characterData: true, subtree: true };
      watcher.observe(count.n, textChanges);
      watcher.observe(count.w, textChanges);
      var top = topClear(bar);
      if (top) watcher.observe(top, { attributes: true, attributeFilter: ['style'] });
    }

    var observer = new IntersectionObserver(function (entries) {
      /* The last entry is the current state; earlier ones are history. */
      var entry = entries[entries.length - 1];
      if (!entry) return;
      var above = !entry.isIntersecting && entry.boundingClientRect.top < 0;
      if (above) sync();
      bar.hidden = !above;
    });
    observer.observe(heading);
  }

  document.addEventListener('DOMContentLoaded', wire);
})();
