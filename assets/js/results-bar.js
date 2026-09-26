// results-bar.js
// =============================================================================
// THE STICKY RESULTS BAR -- "N survivors" and `× clear all`, following the
// reader down the page. Helen, 2026-09-26, from the "N survivors" candidates
// page: both treatments, the mono number and this bar, on BOTH indexes.
// =============================================================================
// PURE DOM WIRING, AND A MIRROR: nothing here counts anything. The bar copies
// the count spans the index script paints (`#recipe-count-n` /
// `#recipe-count-word` on food, `#drink-count-n` / `#drink-count-word` on
// cocktails) and the top `× clear all`'s visibility, and its own button clicks
// that one. So it can never disagree with the line it stands in for, and it
// only offers clearing when there is something to clear -- the index script's
// predicate decides that, not a second one here.
//
// WHEN IT SHOWS. Only while IntersectionObserver reports `#results` NOT
// intersecting AND above the viewport (`boundingClientRect.top < 0`). Below
// the fold or in view, the bar stays hidden -- which is also what keeps it off
// the header and the filter panel, since both sit above the heading. No
// IntersectionObserver, no bar: the markup ships `hidden` and a browser
// without the API keeps the page it would have had anyway.
//
// HOW IT KEEPS UP. A MutationObserver on the two count spans and on the top
// button's `style` attribute (the index scripts write `style.visibility`),
// plus a resync every time the observer fires and after the bar's own click.
// Without MutationObserver it still shows the right numbers whenever it
// appears; it just would not follow a change made while it was already up.
//
// ON DOMContentLoaded, DELIBERATELY, AND LOADED AFTER THE INDEX SCRIPT.
// filters.js builds its clear-all buttons inside its own DOMContentLoaded
// handler, so a bar that looked for them at parse time would find nothing.
// Listeners fire in registration order, which is what the script order in each
// index template guarantees (tests/test_site_config.py holds it).
//
// ONE SCRIPT, BOTH SITES. It finds `[data-results-bar]` and does not care
// which index it is on; the pairs of count ids below are the only place the
// two differ.
// =============================================================================

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

  /* THE TOP `× clear all` -- the first `.btn-clear` in document order that is
     not the bar's own. Both index scripts insert theirs as the panel's first
     child, ahead of the bottom copy and the one inside "Blank canvas.", so the
     first is the top one. Looked up each time rather than once: it is built by
     a script, and the lookup costs nothing. */
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
        /* `visibility`, the same property the index scripts set on their own
           buttons, read off the same inline style they write it to. Anything
           but an explicit `visible` is hidden -- before the first apply() the
           inline value is empty and the stylesheet's resting state is hidden. */
        barClear.style.visibility =
          top && top.style.visibility === 'visible' ? 'visible' : 'hidden';
      }
    }

    if (barClear) {
      barClear.addEventListener('click', function () {
        var top = topClear(bar);
        if (top) top.click();
        /* apply() is synchronous on both indexes, so the count is already
           repainted by the time click() returns. */
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
