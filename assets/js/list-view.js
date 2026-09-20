// =============================================================================
// LIST VIEW — pure ordering/paging logic, no DOM.
//
// `recipe-list.js` UNTIL 2026-09-20 (#759), AND IT WAS NEVER ABOUT RECIPES.
// The old name recorded where these three helpers were born, not who uses
// them: #694 brought the COCKTAIL index to the same `paginate`, so the two
// indexes cannot drift about what "page 3 of 7" means, and `shuffle` and
// `titleMatchTier` are as site-neutral. A cocktails developer was reading a
// `<script src=".../recipe-list.js">` on a page with no recipes on it.
//
// THE HEADER ITSELF WAS THE ARGUMENT FOR RENAMING. It had said, since #694,
// that the file is not about recipes -- which removed most of the cost of the
// wrong name for anyone who read the paragraph, and none of it for anyone who
// did not. #759: "a name that needs a paragraph of explanation is a name that
// will mislead someone who does not read the paragraph."
//
// `list-view.js` rather than `pagination.js`, because paging is one of the
// three things here. It sits beside `filter-state.js` and
// `ingredient-search.js` in the same pure, no-DOM, directly-testable family.
//
// NOT TO BE CONFUSED WITH `.recipe-list`, which is a CSS class on the FOOD
// index's `<ul>` and keeps its name: that one really is a list of recipes.
//
// Extracted out of filters.js for the same reason ingredient-search.js was:
// testable directly with Node (see tests/js/list-view.test.js) instead of
// only checked by hand against a live page. Each caller still owns everything
// DOM-shaped -- filters.js reads `items` off the page and sets
// `li.style.display`; cocktail-index.js toggles `card.hidden` instead, and the
// difference between those two is exactly the kind of thing that belongs in the
// caller rather than here.
//
// Loaded two ways from the one file, no bundler:
//   - In the browser, as a plain <script> before the index script that uses it
//     (filters.js on food, cocktail-index.js on cocktails), attaching to
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

  // Which of the three title-search tiers a title falls into, for a given
  // (already folded+lowercased) query — GitHub issues #63/#78. Helen's
  // rule: a title starting with the query outranks one where the query
  // merely starts some OTHER word in it, which in turn outranks one where
  // the query is only a mid-word substring somewhere. Returns 1/2/3 for
  // those three tiers, or 0 for no match at all (the caller is expected to
  // already know which titles matched; 0 only matters if it doesn't).
  // `fold` is injected rather than required here, so this file stays free
  // of a hard dependency on ingredient-search.js the way shuffle/paginate
  // above are — filters.js already has a `fold` in scope to pass in.
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
    root.HTF.recipeList = api;
  }
})(typeof window !== 'undefined' ? window : this);
