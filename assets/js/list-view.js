// =============================================================================
// LIST VIEW — pure ordering/paging logic, no DOM, shared by both indexes
// (filters.js on food, cocktail-index.js on cocktails) so they cannot drift
// about what "page 3 of 7" means. Each caller owns everything DOM-shaped.
// Not to be confused with `.recipe-list`, a CSS class on the food index.
//
// Loaded two ways, no bundler: a plain <script> before the index script,
// attaching to window.HTF; and require() in Node (tests/js/list-view.test.js).
// =============================================================================
(function (root) {
  'use strict';

  // Fisher-Yates. Returns a new array; the caller applies the order to the DOM.
  function shuffle(array) {
    var result = array.slice();
    for (var i = result.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = result[i];
      result[i] = result[j];
      result[j] = tmp;
    }
    return result;
  }

  // requestedPage need not be valid (a filter can narrow the results out
  // from under it), so a legal currentPage is returned. showAll makes the
  // slice everything, so callers need no separate branch.
  function paginate(totalItems, requestedPage, pageSize, showAll) {
    var totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
    var currentPage = Math.min(Math.max(requestedPage, 1), totalPages);
    return {
      currentPage: currentPage,
      totalPages: totalPages,
      start: showAll ? 0 : (currentPage - 1) * pageSize,
      end: showAll ? totalItems : currentPage * pageSize
    };
  }

  // Title-search tier for an already folded, lowercased query (#63, #78):
  // 1 the title starts with it, 2 another word starts with it, 3 it is only
  // a mid-word substring, 0 no match. `fold` is injected so this file needs
  // no ingredient-search.js.
  function titleMatchTier(title, query, fold) {
    if (!query) return 0;
    var folded = fold(title.toLowerCase());
    var words = folded.split(/\s+/).filter(Boolean);
    if (words.length && words[0].indexOf(query) === 0) return 1;
    if (words.some(function (w) { return w.indexOf(query) === 0; })) return 2;
    if (folded.indexOf(query) !== -1) return 3;
    return 0;
  }

  var api = { shuffle: shuffle, paginate: paginate, titleMatchTier: titleMatchTier };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  } else {
    root.HTF = root.HTF || {};
    root.HTF.listView = api;
  }
})(typeof window !== 'undefined' ? window : this);
