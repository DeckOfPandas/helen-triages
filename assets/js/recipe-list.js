// =============================================================================
// RECIPE LIST — pure ordering/paging logic, no DOM.
//
// Extracted out of filters.js for the same reason ingredient-search.js was:
// testable directly with Node (see tests/js/recipe-list.test.js) instead of
// only checked by hand against a live page. filters.js still owns everything
// DOM-shaped -- reading `items` off the page, re-appending them in shuffled
// order, setting `li.style.display`. The category-code bar's is-lit logic
// stayed in filters.js on purpose: it reads badge classes off actual DOM
// elements, so there's no DOM-free version of it worth extracting.
//
// Loaded two ways from the one file, no bundler:
//   - In the browser, as a plain <script> before filters.js, attaching to
//     window.HTF (the same namespace assets.js already establishes).
//   - In Node, via require(), for tests.
// =============================================================================
(function (root) {
  'use strict';

  // Fisher-Yates. Returns a new array rather than shuffling in place, so the
  // caller decides when and how to apply the new order to the DOM -- this
  // function never touches anything beyond the array it's handed.
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

  // Given how many items matched the active filters, which page was asked
  // for, the page size, and whether "(see all)" is in effect, works out
  // what's actually current and which slice of the matched list that covers.
  //
  // requestedPage isn't necessarily valid -- a filter can narrow the results
  // so the page you were on no longer exists -- so this always returns a
  // legal currentPage rather than trusting the caller's number. showAll
  // collapses the slice to everything, which is also why there's no separate
  // showAll branch at the call site: start/end already cover it.
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

  var api = { shuffle: shuffle, paginate: paginate };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  } else {
    root.HTF = root.HTF || {};
    root.HTF.recipeList = api;
  }
})(typeof window !== 'undefined' ? window : this);
