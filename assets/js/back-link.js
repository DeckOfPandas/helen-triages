// back-link.js
// The back arrow on a recipe or cocktail page (#387).
//
// _includes/back-to-index.html renders `.back-to-index` as an ordinary link
// to the index, which works without this file. This upgrades it in one case:
// you came FROM that index IN THIS TAB, so history.back() returns the page
// you left, with its filters, page, shuffled order and scroll, where the
// plain link would re-render and reshuffle it (MANUAL §13.7).
//
// Every uncertain case falls through to the plain link: a refresh is a
// better failure than an arrow that does nothing. The decision is a pure
// function so Node can test it (MANUAL §3); the DOM wiring is the rest.

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

    // A tab with no history cannot go back. A recipe opened in a NEW TAB
    // still has the index as its referrer, but its history holds one entry
    // and history.back() is a silent no-op: the arrow would do nothing.
    if (!(ctx.historyLength > 1)) return false;

    var from, to;
    try {
      from = new URL(ctx.referrer);
      to = new URL(ctx.linkHref);
    } catch (e) {
      return false;               // not parseable; the plain link stands
    }

    if (from.origin !== ctx.origin) return false;

    // Pathname alone, so a query string on the index still counts as "came
    // from the index". This also declines index -> recipe A -> recipe B: on B
    // the referrer is A, and going back would land on A, not the index.
    return from.pathname === to.pathname;
  }

  // Node requires it to test the decision; the browser gets window.HTF.
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
    // Only a plain left click: a middle click or ctrl/cmd-click must still
    // follow the real href into its new tab.
    if (event.defaultPrevented) return;
    if (event.button !== 0) return;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;

    event.preventDefault();
    window.history.back();
  });

})(typeof window !== 'undefined' ? window : this);
