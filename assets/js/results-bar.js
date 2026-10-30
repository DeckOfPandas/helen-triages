// results-bar.js
// The results pill at the foot of the screen on both indexes
// (_includes/results-pill.html, #1448). One face at a time, read off where the
// filter panel and the count line are: "top ↑" while the panel is above the
// screen; "N survivors ↓" while the count line is below it; and, while any
// filter is on, "N survivors" with no arrow in between. The × beside it shows
// whenever there is something to clear. MANUAL §13.7.
//
// A mirror: nothing here counts or clears. It copies the count spans the index
// script paints, and the × is the index script's own clear-all, whose
// visibility that script sets; this reads it.
//
// Wired on DOMContentLoaded and loaded after the index script, which adopts
// the × in its own DOMContentLoaded handler; listeners fire in registration
// order (tests/test_site_config.py holds the script order).

(function () {
  'use strict';

  var COUNT_IDS = [
    ['recipe-count-n', 'recipe-count-word'],
    ['drink-count-n', 'drink-count-word']
  ];

  /* The count spans this page actually has. null on a page with neither. */
  function findCount() {
    for (var i = 0; i < COUNT_IDS.length; i++) {
      var n = document.getElementById(COUNT_IDS[i][0]);
      var w = document.getElementById(COUNT_IDS[i][1]);
      if (n && w) return { n: n, w: w };
    }
    return null;
  }

  function all(root, selector) {
    return Array.prototype.slice.call(root.querySelectorAll(selector));
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
    var pill = document.querySelector('[data-results-pill]');
    var heading = document.getElementById('results');
    var panel = document.querySelector('[data-filter-panel]');
    if (!pill || !heading || !panel) return;
    if (typeof window.requestAnimationFrame !== 'function') return;

    var count = findCount();
    if (!count) return;

    var plain = pill.querySelector('[data-results-pill-count]');
    var down = pill.querySelector('[data-results-pill-down]');
    var up = pill.querySelector('[data-results-pill-up]');
    var clear = pill.querySelector('[data-results-pill-clear]');
    /* "top" names the id it returns to; without that element it is never
       offered, rather than scrolling nowhere. */
    var upTarget = up ? document.getElementById(up.getAttribute('data-results-pill-up')) : null;

    function sync() {
      all(pill, '[data-results-pill-n]').forEach(function (el) { el.textContent = count.n.textContent; });
      all(pill, '[data-results-pill-word]').forEach(function (el) { el.textContent = count.w.textContent; });
    }

    /* Read off the inline `style.visibility` the index script writes on the
       ×. Anything but an explicit `visible` is nothing to clear. */
    function anyFilter() {
      return !!clear && clear.style.visibility === 'visible';
    }

    function place() {
      var panelBox = panel.getBoundingClientRect();
      var lineBox = heading.getBoundingClientRect();
      var above = panelBox.bottom <= 0 && !!upTarget;
      /* Not yet wholly on screen: a line peeking a few pixels over the bottom
         edge has not been seen. */
      var below = !above && lineBox.bottom > window.innerHeight;
      var on = anyFilter();
      sync();
      if (up) up.hidden = !above;
      if (down) down.hidden = !below;
      if (plain) plain.hidden = above || below;
      pill.classList.toggle('results-pill--clear', on);
      pill.hidden = !(above || below || on);
    }

    if (down) down.addEventListener('click', function () { goTo(heading); });
    if (up && upTarget) up.addEventListener('click', function () { goTo(upTarget); });
    /* The index script's own listener clears and repaints synchronously;
       this one, registered after it, re-places the pill on the result. */
    if (clear) clear.addEventListener('click', place);

    if (typeof window.MutationObserver === 'function') {
      var watcher = new MutationObserver(place);
      var textChanges = { childList: true, characterData: true, subtree: true };
      watcher.observe(count.n, textChanges);
      watcher.observe(count.w, textChanges);
      if (clear) watcher.observe(clear, { attributes: true, attributeFilter: ['style'] });
    }

    /* Where the panel and the line are changes on scroll, on resize, and when
       a filter changes the panel's height; once a frame covers all three. */
    var queued = false;
    function soon() {
      if (queued) return;
      queued = true;
      window.requestAnimationFrame(function () {
        queued = false;
        place();
      });
    }
    window.addEventListener('scroll', soon, { passive: true });
    window.addEventListener('resize', soon);
    window.addEventListener('load', soon);
    place();
  }

  document.addEventListener('DOMContentLoaded', wire);
})();
