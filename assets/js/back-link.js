// back-link.js
// =============================================================================
// THE BACK ARROW ON A RECIPE OR COCKTAIL PAGE — GitHub issue #387.
// =============================================================================
// _includes/back-to-index.html renders `.back-to-index` as an ordinary link to
// this site's index. That link is correct on its own and this file is not
// required for it to work. All this does is upgrade it, in the one case where
// the upgrade is provably right: you got here FROM that index, IN THIS TAB, so
// going back through history returns the page you actually left.
//
// WHY THAT MATTERS MORE THAN IT SOUNDS. Following the plain link re-renders the
// index, and with no filters set the index reshuffles on every load
// (HANDOVER 13.7) -- so you would land on a correctly filtered list in a
// different order, having lost your place. history.back() restores the page
// from the browser's cache with its DOM intact: same filters, same page number,
// same shuffled order, same scroll position. Nothing is serialised, nothing is
// rebuilt, and nothing can drift out of step with the index's real state,
// because there is no second copy of that state.
//
// EVERY UNCERTAIN CASE FALLS THROUGH TO THE PLAIN LINK, deliberately. The
// failure mode of guessing wrong is "the arrow did nothing", or "back went
// somewhere I did not expect", both worse than a refresh; the failure mode of
// standing down is a refresh, which is what you would have got anyway.
//
// THE DECISION IS A PURE FUNCTION, and the DOM wiring is the rest of the file.
// HANDOVER §3: once a module gets non-trivial, the algorithm splits from the
// wiring so Node can test it directly. This one earned that immediately -- see
// the new-tab case below, which was WRONG in the first version and is invisible
// to any check that does not model a tab's history length.
// =============================================================================

(function (root) {
  'use strict';

  /**
   * Should the arrow go back through history rather than follow its href?
   *
   * Everything it needs is passed in, so a test can pose a situation a browser
   * would otherwise have to be driven into.
   *
   * @param {object} ctx
   * @param {string} ctx.referrer      document.referrer ('' when absent)
   * @param {string} ctx.linkHref      the arrow's resolved absolute URL
   * @param {string} ctx.origin        window.location.origin
   * @param {number} ctx.historyLength window.history.length
   * @returns {boolean}
   */
  function shouldGoBackToIndex(ctx) {
    // No referrer: typed the URL, opened a bookmark, came from another site, or
    // a browser that withholds it. Nothing to be confident about.
    if (!ctx.referrer) return false;

    // A TAB WITH NO HISTORY CANNOT GO BACK, and this is the case that makes the
    // referrer check insufficient on its own. Opening a recipe in a NEW TAB
    // (cmd/ctrl-click, middle-click, "open link in new tab") still sets the
    // referrer to the index -- those links carry no rel="noreferrer" -- so the
    // referrer alone says "you came from the index" quite truthfully, while the
    // new tab's session history holds exactly one entry and history.back() is a
    // silent no-op. The arrow would do NOTHING, which is the worst outcome
    // available: not a wrong page, no page at all, and no clue why.
    //
    // Helen asked precisely this ("both directly and then opening in a new
    // tab") and the first version of this file failed it.
    if (!(ctx.historyLength > 1)) return false;

    var from, to;
    try {
      from = new URL(ctx.referrer);
      to = new URL(ctx.linkHref);
    } catch (e) {
      return false;               // not parseable; the plain link stands
    }

    if (from.origin !== ctx.origin) return false;

    // Compared on pathname alone: the index carries no query string of its own
    // today, and a future `?tag=soup` on it should still count as "came from
    // the index" rather than disqualifying the shortcut.
    //
    // This also, correctly, declines the cross-recipe case. Index -> recipe A
    // -> recipe B by a link in A's method: on B the referrer is A, not the
    // index, so the arrow follows its href. Going back from B would land on A,
    // which is not what an arrow pointing at the index should do.
    return from.pathname === to.pathname;
  }

  // --- Exported the same way every other split module here is ------------------
  // Node requires it to test the decision; the browser gets it on window.HTF and
  // runs the wiring below. Same shape as recipe-list.js and ingredient-search.js
  // (HANDOVER §3), so there is one convention rather than three.
  var api = { shouldGoBackToIndex: shouldGoBackToIndex };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
    return;
  }
  root.HTF = root.HTF || {};
  root.HTF.backLink = api;

  // --- DOM wiring --------------------------------------------------------------

  if (typeof document === 'undefined') return;

  var link = document.querySelector('.back-to-index');
  if (!link) return;

  var resolved;
  try {
    resolved = new URL(link.getAttribute('href'), window.location.href).href;
  } catch (e) {
    return;
  }

  if (!shouldGoBackToIndex({
    referrer: document.referrer,
    linkHref: resolved,
    origin: window.location.origin,
    historyLength: window.history.length
  })) return;

  link.addEventListener('click', function (event) {
    // Let the browser handle anything that is not a plain left click -- a
    // middle click, or ctrl/cmd-click to open in a new tab, must still follow
    // the real href rather than being swallowed into a history call that would
    // do nothing in the new tab it just opened.
    if (event.defaultPrevented) return;
    if (event.button !== 0) return;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;

    event.preventDefault();
    window.history.back();
  });

})(typeof window !== 'undefined' ? window : this);
