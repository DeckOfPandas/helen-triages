// =============================================================================
// FILTER STATE — the index's filter query string, parsed. No DOM.
//
// GitHub issue #40 made every taxonomy badge a link into the index carrying
// the filter it stands for (`_includes/recipe_badges.html`), which means the
// index's filter state now has a written-down URL form. This file owns that
// grammar and nothing else. filters.js stays the DOM half, exactly as it does
// for recipe-list.js and ingredient-search.js (HANDOVER §3).
//
// Loaded two ways from the one file, no bundler:
//   - In the browser, as a plain <script> before filters.js, attaching to
//     window.HTF (the same namespace assets.js already establishes).
//   - In Node, via require(), for tests (tests/js/filter-state.test.js).
//
// -----------------------------------------------------------------------------
// THE GRAMMAR
// -----------------------------------------------------------------------------
//
//   /food/?star=lamb&tag=soup,make-ahead
//
//   - ONE PARAMETER PER FILTER KIND, never one per value. `star` and `tag`
//     today; `ing` (the ingredient search) is the obvious third and is
//     deliberately not implemented, because nothing emits it yet.
//   - VALUES ARE COMMA-SEPARATED within a kind. Safe because no tag, star
//     ingredient or main_ingredients entry contains a comma — checked against
//     _data/food/taxonomy.yml. The split happens BEFORE decoding, so a value
//     that ever did contain one could still be spelled `%2C` and survive.
//   - A LEADING `-` IS RESERVED and means "exclude" (GitHub issue #52, not
//     built). Unambiguous because no declared tag or star BEGINS with a
//     hyphen — `make-ahead`, `no-cook` and `one-handed food` all have interior
//     ones, which are ordinary characters and are left alone. Until #52 exists
//     a `-`-prefixed value is DROPPED rather than read as a positive filter on
//     a tag literally named "-soup"; #52 turns that drop into an exclusion
//     without changing anything an existing link means.
//   - UNKNOWN PARAMETERS ARE IGNORED, and so is any value the page's own
//     filter matrix doesn't offer (that second half is filters.js's job, since
//     only it can see the buttons). Same policy cook-timer.js already applies
//     to `?protein=beef`: a query string is a suggestion, and a bad one is not
//     worth an error on a page that works perfectly well without it.
//
// `+` DECODES TO A SPACE, and this is the part that will bite. Jekyll's
// `url_encode` filter is CGI.escape underneath, which spells a space as `+`,
// not `%20` — and `decodeURIComponent` does NOT undo that, so a naive decode
// leaves `oily+fish`. Six real values are affected (`oily fish`, `root veg`,
// `carbs party`, `hot snack`, `ice cream`, `one-handed food`) and they are
// among the most clickable things on the page. `+` is turned into `%20` before
// decoding rather than into a space after it, so a genuine plus spelled `%2B`
// still comes back as a plus.
//
// toQuery() — writing this grammar back out — is deliberately ABSENT. Nothing
// updates the URL as you filter yet, and this repo has a standing rule against
// building a slot nothing fills (test_no_decoration_slot_is_orphaned, and
// HANDOVER §12's `--annotation-gutter` cautionary tale). Add it the day
// something calls it.
// =============================================================================
(function (root) {
  'use strict';

  // The filter kinds this grammar knows. parseQuery always returns a key for
  // each one, so a caller never has to guard against a missing array; a
  // parameter not named here is ignored outright.
  var KINDS = ['star', 'tag'];

  var EXCLUDE_PREFIX = '-';

  // Decodes one raw query-string token. `+` -> space (see the header), then
  // ordinary percent-decoding. A malformed escape (`%zz`) throws in
  // decodeURIComponent; that's a hand-mangled URL, so it yields '' and the
  // caller drops it, rather than taking the page down with it.
  function decodeValue(raw) {
    try {
      return decodeURIComponent(String(raw).replace(/\+/g, '%20'));
    } catch (e) {
      return '';
    }
  }

  // location.search (with or without its leading '?') -> { star: [...],
  // tag: [...] }, values in the order they appeared, deduplicated.
  //
  // Arity is the CALLER's business, not this function's: the star filter is
  // single-select in the UI today, but the grammar has no opinion about that
  // and returns everything it was given. filters.js takes the last valid one.
  function parseQuery(search) {
    var out = {};
    KINDS.forEach(function (kind) { out[kind] = []; });

    var body = String(search == null ? '' : search).replace(/^[?#]/, '');
    if (!body) return out;

    body.split('&').forEach(function (chunk) {
      var eq = chunk.indexOf('=');
      if (eq === -1) return;               // `?tag` with no value says nothing
      var kind = decodeValue(chunk.slice(0, eq));
      if (KINDS.indexOf(kind) === -1) return;

      chunk.slice(eq + 1).split(',').forEach(function (rawValue) {
        // Checked on BOTH sides of the decode: `-soup` and `%2Dsoup` are the
        // same claim spelled two ways, and a bare `-` is a value that reserves
        // the whole grammar and names nothing, so it goes too.
        if (rawValue.charAt(0) === EXCLUDE_PREFIX) return;
        var value = decodeValue(rawValue).trim();
        if (!value || value.charAt(0) === EXCLUDE_PREFIX) return;
        if (out[kind].indexOf(value) === -1) out[kind].push(value);
      });
    });

    return out;
  }

  var api = { KINDS: KINDS, EXCLUDE_PREFIX: EXCLUDE_PREFIX, parseQuery: parseQuery };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  } else {
    root.HTF = root.HTF || {};
    root.HTF.filterState = api;
  }
})(typeof window !== 'undefined' ? window : this);
