// filter-fold.js
// =============================================================================
// THE PHONE FOLD -- a chip section folds to its label at phone width. #1219,
// Helen, 2026-10-10, from a candidates page: "The mobile view is simplest:
// sections fold." _sass/shared/_filter-fold.scss has the measurements and
// the reasons; this is the wiring.
// =============================================================================
// ONE SCRIPT, BOTH SITES. It reads data-attributes and no class of either
// index: `[data-fold]` is a section, `[data-fold-head]` its label row,
// `[data-fold-body]` its chips, `[data-fold-count]` the chosen-chip count and
// `[data-fold-mark]` the + / - button. The count and the mark ship `hidden`
// and are revealed here, so without JavaScript nothing can fold and nothing
// is offered.
//
// THE STYLESHEET DECIDES WHETHER FOLDING IS ON. `.is-folded` has a rule only
// at phone width, and the mark is `display: none` above it. A tap on the row
// is acted on only while the mark is displayed, which asks the stylesheet
// rather than restating its breakpoint here.
//
// WHICH START OPEN. The first section, and any section the URL's fragment
// names: a tag on a recipe page links to `#filter-mood` so the reader lands on
// the lit chip (#1059), and a folded section would hide it.
//
// THE COUNT IS READ, NEVER KEPT: the number of chips in the section whose
// `aria-pressed` is "true", which both index scripts keep in step with their
// own chosen class. It is repainted after any click in the section and, where
// MutationObserver exists, whenever a chip's `aria-pressed` changes -- which
// is what catches `x clear all` and a filter set from the URL.
//
// THE MARK'S ACCESSIBLE NAME IS THE SECTION'S OWN LABEL, and `aria-expanded`
// says which way it is. No words of this script's are read out.
//
// ON DOMContentLoaded, AND LOADED AFTER THE INDEX SCRIPT, as results-bar.js
// is: filters.js applies a filter carried in the URL inside its own handler,
// and listeners fire in registration order, so the first count painted here
// already includes it.
// =============================================================================

(function () {
  'use strict';

  function all(root, selector) {
    return Array.prototype.slice.call(root.querySelectorAll(selector));
  }

  function wireSection(section, index, target) {
    var head = section.querySelector('[data-fold-head]');
    var body = section.querySelector('[data-fold-body]');
    var mark = section.querySelector('[data-fold-mark]');
    var count = section.querySelector('[data-fold-count]');
    if (!head || !body || !mark) return;

    /* Folding is on exactly while the stylesheet shows the mark. A browser
       that cannot answer is treated as a phone: the class is inert on a wide
       screen anyway. */
    function folding() {
      if (typeof window.getComputedStyle !== 'function') return true;
      return window.getComputedStyle(mark).display !== 'none';
    }

    function paint() {
      var folded = section.classList.contains('is-folded');
      mark.textContent = folded ? '+' : '−';
      mark.setAttribute('aria-expanded', folded ? 'false' : 'true');
      if (count) {
        var chosen = all(body, '[aria-pressed="true"]').length;
        count.textContent = chosen ? String(chosen) : '';
        count.hidden = !chosen;
      }
    }

    var label = head.querySelector('[data-fold-label]');
    if (label) mark.setAttribute('aria-label', label.textContent.replace(/\s+/g, ' ').trim());

    var open = index === 0 || (target && section.getAttribute('id') === target);
    if (!open) section.classList.add('is-folded');
    mark.hidden = false;

    head.addEventListener('click', function (event) {
      if (!folding()) return;
      /* Another button in the row -- the section's own `x clear` -- keeps its
         own job. */
      var button = event.target && event.target.closest ? event.target.closest('button') : null;
      if (button && button !== mark) return;
      section.classList.toggle('is-folded');
      paint();
    });

    body.addEventListener('click', function () { setTimeout(paint, 0); });
    if (typeof window.MutationObserver === 'function') {
      new window.MutationObserver(paint).observe(
        body, { attributes: true, attributeFilter: ['aria-pressed'], subtree: true });
    }

    paint();
  }

  function wire() {
    var target = '';
    try { target = decodeURIComponent((window.location && window.location.hash || '').replace(/^#/, '')); }
    catch (e) { target = ''; }
    all(document, '[data-fold]').forEach(function (section, index) {
      wireSection(section, index, target);
    });
  }

  document.addEventListener('DOMContentLoaded', wire);
})();
