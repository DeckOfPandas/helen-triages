// back-link.js
// =============================================================================
// THE BACK ARROW ON A RECIPE OR COCKTAIL PAGE — GitHub issue #387.
// =============================================================================
// _includes/back-to-index.html renders `.back-to-index` as an ordinary link to
// this site's index. That link is correct on its own and this file is not
// required for it to work. All this does is upgrade it, in the one case where
// the upgrade is provably right: you got here FROM that index, so going back
// through history returns the page you actually left.
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
// EVERY UNCERTAIN CASE FALLS THROUGH TO THE PLAIN LINK, deliberately. No
// referrer (typed the URL, opened a bookmark, followed a link from another
// site, or a browser that suppresses it), a referrer from somewhere else, a
// cross-origin referrer, an unparseable one -- in all of those, this file does
// nothing at all and the href does its job. The failure mode of guessing wrong
// here is "back went somewhere you did not expect", which is worse than a
// refresh; the failure mode of standing down is a refresh, which is what you
// would have got anyway.
// =============================================================================

(function () {
  var link = document.querySelector('.back-to-index');
  if (!link) return;

  var referrer = document.referrer;
  if (!referrer) return;

  var from, to;
  try {
    from = new URL(referrer);
    to = new URL(link.getAttribute('href'), window.location.href);
  } catch (e) {
    return;                       // not parseable; the plain link stands
  }

  // Same site, and the previous page is the very index this link points at.
  // Compared on pathname alone: the index carries no query string of its own
  // today, and a future `?tag=soup` on it should still count as "came from the
  // index" rather than disqualifying the shortcut.
  if (from.origin !== window.location.origin) return;
  if (from.pathname !== to.pathname) return;

  link.addEventListener('click', function (event) {
    // Let the browser handle anything that is not a plain left click -- a
    // middle click, or ctrl/cmd-click to open in a new tab, must still follow
    // the real href rather than being swallowed into a history call that would
    // do nothing in a new tab.
    if (event.defaultPrevented) return;
    if (event.button !== 0) return;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;

    event.preventDefault();
    window.history.back();
  });
})();
