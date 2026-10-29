// results-bar.js
// What floats on both indexes, all placed by where the count line is: the
// sticky bar, with `× clear all`, and the "top ↑" pill once the count line has
// scrolled off above; the "N survivors ↓" pill while it is still below
// (#1441). MANUAL §13.7.
//
// A mirror: nothing here counts anything. It copies the count spans the index
// script paints and the top `× clear all`'s visibility, and the bar's button
// clicks that one, so neither copy can disagree with the line it stands in for.
// Without IntersectionObserver both stay `hidden`.
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
  function topClear() {
    var buttons = all('.btn-clear');
    for (var i = 0; i < buttons.length; i++) {
      if (!buttons[i].closest('[data-results-bar]')) return buttons[i];
    }
    return null;
  }

  function reduceMotion() {
    return typeof window.matchMedia === 'function'
      && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  /* Scroll `target` to the top (its `scroll-margin-top` sets where it lands)
     and move focus there, so a keyboard reader carries on from it rather than
     from the pill they pressed. */
  function goTo(target) {
    target.scrollIntoView({ behavior: reduceMotion() ? 'auto' : 'smooth', block: 'start' });
    if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
    target.focus({ preventScroll: true });
  }

  function wire() {
    var bar = document.querySelector('[data-results-bar]');
    var jump = document.querySelector('[data-results-jump]');
    /* The top pill names the id it returns to; without that element it never
       shows, rather than scrolling nowhere. */
    var up = document.querySelector('[data-results-top]');
    var upTarget = up ? document.getElementById(up.getAttribute('data-results-top')) : null;
    if (!upTarget) up = null;
    var heading = document.getElementById('results');
    if (!(bar || jump || up) || !heading) return;
    if (typeof window.IntersectionObserver !== 'function') return;

    var count = findCount();
    if (!count) return;

    /* Each copy's number and word, from whichever of the two is on the page. */
    var copies = [];
    if (bar) {
      copies.push([bar.querySelector('[data-results-bar-n]'),
                   bar.querySelector('[data-results-bar-word]')]);
    }
    if (jump) {
      copies.push([jump.querySelector('[data-results-jump-n]'),
                   jump.querySelector('[data-results-jump-word]')]);
    }
    var barClear = bar ? bar.querySelector('[data-results-bar-clear]') : null;

    function sync() {
      copies.forEach(function (copy) {
        if (copy[0]) copy[0].textContent = count.n.textContent;
        if (copy[1]) copy[1].textContent = count.w.textContent;
      });
      if (barClear) {
        var top = topClear();
        /* Read off the inline `style.visibility` the index scripts write.
           Anything but an explicit `visible` is hidden, the resting state. */
        barClear.style.visibility =
          top && top.style.visibility === 'visible' ? 'visible' : 'hidden';
      }
    }

    if (barClear) {
      barClear.addEventListener('click', function () {
        var top = topClear();
        if (top) top.click();
        /* The index script repaints synchronously, so the count is current. */
        sync();
      });
    }

    if (jump) jump.addEventListener('click', function () { goTo(heading); });
    if (up) up.addEventListener('click', function () { goTo(upTarget); });

    if (typeof window.MutationObserver === 'function') {
      var watcher = new MutationObserver(sync);
      var textChanges = { childList: true, characterData: true, subtree: true };
      watcher.observe(count.n, textChanges);
      watcher.observe(count.w, textChanges);
      var top = topClear();
      if (top) watcher.observe(top, { attributes: true, attributeFilter: ['style'] });
    }

    /* Above: the count line has wholly left the top, so the bar stands in for
       it and the top pill offers the way back. Below: it is not yet wholly on
       screen, so the down pill points to it. A line peeking a few pixels over
       the bottom edge has not been seen. */
    function place(rect) {
      var above = rect.bottom <= 0;
      var below = !above && rect.bottom > window.innerHeight;
      if (above || below) sync();
      if (bar) bar.hidden = !above;
      if (up) up.hidden = !above;
      if (jump) jump.hidden = !below;
    }

    var observer = new IntersectionObserver(function (entries) {
      /* The last entry is the current state; earlier ones are history. */
      var entry = entries[entries.length - 1];
      if (entry) place(entry.boundingClientRect);
    }, { threshold: [0, 1] });
    observer.observe(heading);

    /* The observer reports only a crossing, and a jump from the foot of the
       page to the top (Home, a tap on a phone's status bar, reduced motion)
       crosses nothing, which would leave the bar up over the header. So a
       scroll re-reads the line's box, once a frame. */
    var queued = false;
    window.addEventListener('scroll', function () {
      if (queued) return;
      queued = true;
      window.requestAnimationFrame(function () {
        queued = false;
        place(heading.getBoundingClientRect());
      });
    }, { passive: true });
  }

  document.addEventListener('DOMContentLoaded', wire);
})();
