// shortlist.js
// =============================================================================
// THE SHORTLIST'S DOM HALF — every control that marks or unmarks one thing.
// =============================================================================
// GitHub issue #546. HTF.shortlist (assets/js/assets.js) is the STORE and knows
// nothing about a page; this is the wiring, and knows nothing about storage.
// Same split filters.js and filter-state.js already run on, for the same
// reason: the store is the part worth testing without a browser.
//
// FOUR PLACES, ONE SCRIPT, and the placements are Helen's (2026-09-04):
//   - the right-hand end of a recipe row on the food index
//   - the top-right corner of a drink card on the cocktail index
//   - beside `print` on a recipe page
//   - the top-right of the meta panel on a drink page
// Every one of them is `.btn-shortlist` carrying `data-shortlist-key`, so this
// file needs no per-site branch and no list of selectors to keep in step. A
// fifth placement is markup and a stylesheet rule, and nothing here.
//
// THE CONTROLS SHIP `hidden` AND THIS REVEALS THEM. `.btn-print` established
// the rule and _layouts/recipe.html states it: "a control that silently fails
// is worse than no control", so the markup assumes JavaScript did not run and
// this is the thing that proves it did. CSS cannot ask that question.
//
// THE WORD NEVER CHANGES; the mark and the colour carry the state. That is
// #494's finding, quoted in _layouts/cocktail.html: a label that swaps between
// two words has to be read as either the state or the action, and there is
// nothing on screen to say which. So the button says `shortlist` in both
// states, `_sass/*/_shortlist.scss` draws a `+` or a `✓` in front of it via
// ::before, and only the class and aria-pressed move. It also means the control
// cannot change width, which is what lets it sit in a drink card's top-right
// corner without unpinning the fixed anchors _cards.scss is built on.
//
// WHY A DOCUMENT EVENT RATHER THAN A CALLBACK REGISTRY. Both indexes filter on
// "is this shortlisted", and both already have one apply()/updateResults() that
// repaints everything from state. `htf:shortlist-change` lets each of them
// subscribe with one line and stay the only thing that decides what its own
// page looks like -- where a registry here would make this file a second place
// that knows the two indexes exist.
// =============================================================================

(function () {
  'use strict';

  var HTF = window.HTF;

  // No store, no controls. The root landing page has no site-key and so has no
  // shortlist at all -- see HTF.shortlist's own note on why that is a refusal
  // rather than a fallback to a shared list.
  if (!HTF || !HTF.shortlist || !HTF.site) return;

  var EVENT = 'htf:shortlist-change';

  function controls() {
    return Array.prototype.slice.call(
      document.querySelectorAll('.btn-shortlist[data-shortlist-key]')
    );
  }

  /* Paint one control from the store. Class for the eye, aria-pressed for
     everyone else -- a screen reader cannot see `is-on`, and this is a toggle
     button, which is exactly what aria-pressed is for. */
  function paint(btn) {
    var on = HTF.shortlist.has(btn.dataset.shortlistKey);
    btn.classList.toggle('is-on', on);
    btn.setAttribute('aria-pressed', on ? 'true' : 'false');
  }

  /* Every count on the page, from one place. The index's own "shortlisted"
     filter shows how many there are to see; nothing else does today, and a
     second reader costs this function nothing. */
  function paintCounts() {
    var n = HTF.shortlist.count();
    Array.prototype.slice.call(document.querySelectorAll('[data-shortlist-count]'))
      .forEach(function (el) { el.textContent = String(n); });
  }

  /* THE WHOLE PAGE, NOT THE BUTTON THAT WAS CLICKED. A row and a card are one
     control each today, but the drink page has one and its own index card is a
     back-navigation away in the same bfcache entry -- and the cost of repainting
     every control on a page is one class toggle per control. Painting only the
     clicked one is the optimisation that goes stale the first time two controls
     share a key. */
  function repaint() {
    controls().forEach(paint);
    paintCounts();
  }

  function wire() {
    var all = controls();

    all.forEach(function (btn) {
      paint(btn);
      // The proof that JavaScript ran. See the header.
      btn.hidden = false;
    });
    paintCounts();

    /* ONE DELEGATED LISTENER, on the document. The food index reorders its rows
       on every filter pass and the cocktail index reorders its cards, but
       neither destroys them -- so a per-button listener would in fact survive.
       This is delegation for a different reason: `.recipe-list` is paginated and
       `.drink-cards` is re-ranked, and both are cheaper to reason about if the
       handler does not care which nodes exist when it is attached. */
    document.addEventListener('click', function (ev) {
      var btn = ev.target.closest && ev.target.closest('.btn-shortlist[data-shortlist-key]');
      if (!btn) return;
      ev.preventDefault();

      var key = btn.dataset.shortlistKey;
      HTF.shortlist.toggle(key);
      repaint();

      /* `detail` carries what changed, for a listener that wants to be cleverer
         than "repaint everything". Neither index is, today: both re-run the pass
         they already re-run for every other filter, which is what keeps the
         shortlisted view from ever disagreeing with the toggles on it. */
      document.dispatchEvent(new CustomEvent(EVENT, {
        detail: { key: key, on: HTF.shortlist.has(key) }
      }));
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wire);
  } else {
    wire();
  }
})();
