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
//
// -----------------------------------------------------------------------------
// THE STATE SHAPE (GitHub issue #52, step one)
// -----------------------------------------------------------------------------
//
// This file also owns WHAT THE INDEX'S FILTER STATE IS, as an enumerable table
// rather than as six loose variables in filters.js's 894 lines of DOM wiring.
//
// It is here because of a bug that happened three times in two days, always
// the same shape: clearAllFilters() emptied five things and the clear-button's
// visibility predicate checked four, so the button hid while it still had work
// to do. `nameQuery` was missed once; `isSearching` was missed once; before
// that two rival copies of the predicate disagreed with each other. Every one
// was found by eye, on the page, after shipping.
//
// The fix is not "be more careful". It is that the list of fields exists ONCE,
// in FIELD_SPEC below, and BOTH the empty state and the "is anything set"
// answer are computed BY ITERATING IT. Add a field to FIELD_SPEC and it is
// cleared, and counted by the clear button, on the same line that declares it —
// there is no second place to remember. tests/js/filter-state.test.js generates
// its per-field cases from FIELDS for the same reason: a hand-written list of
// cases has exactly the omission problem it is meant to catch.
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

  // ---------------------------------------------------------------------------
  // THE STATE SHAPE
  // ---------------------------------------------------------------------------

  /* Every field the index's filter state has, and the only place the list is
     written down. A field declares two things and nothing else:

       empty   a FACTORY for this field's cleared value. A factory, not a
               value, because two of them are Sets: a shared empty Set handed
               out twice would be one Set mutated from two places.

       narrows whether this field counts as "something is still narrowing the
               list" — see hasNarrowingFilter below. It is stated per field
               because it is genuinely per field, and the two fields that say
               false each have a reason recorded here.

     There is deliberately no per-field "is it set?" predicate: isFieldSet
     below answers that generically from the value, so adding a field costs one
     line and cannot half-arrive. */
  var FIELD_SPEC = {
    // The tag buttons (MOOD, PRACTICALITIES). Multi-select: every active tag
    // must be present on a row for it to survive.
    tags: { empty: function () { return new Set(); }, narrows: true },

    // STAR INGREDIENT. Single-select — picking a second replaces the first.
    star: { empty: function () { return null; }, narrows: true },

    /* The chosen ingredient-search result. NOT narrowing, deliberately:
       filters.js's renderResultsPool() nulls it on every keystroke, so while
       the ingredient box is being typed into it is always null, and including
       it in hasNarrowingFilter would be a no-op dressed up as a rule. */
    ingredient: { empty: function () { return null; }, narrows: false },

    // The meta filters (rewrite/proofread/short/draft), local builds only.
    meta: { empty: function () { return new Set(); }, narrows: true },

    /* The title search, folded and lowercased by filters.js before it lands
       here. NARROWING since 2026-08-16: a title search is a filter like any
       other, and the rows it has left are meaningful, so hiding them behind
       the "searching" message while you pick an ingredient threw away context
       you had just asked for. A tag or a star already kept the list on screen;
       nameQuery was the odd one out, and Helen's call was that it should
       behave like the others. */
    nameQuery: { empty: function () { return ''; }, narrows: true },

    /* NOT A FILTER, and the one that keeps getting forgotten. It means "the
       ingredient box has text in it and nothing has been chosen from the
       results yet" — a half-finished search rather than an applied filter. It
       is in this table because clear-all DOES clear it (it empties the box and
       the results pool), so the clear button must offer itself while it is
       set: type "chi", get a pool of results, and without this there is no way
       to clear them but deleting the text by hand. Helen found that one.

       It does not narrow anything — it is the very state hasNarrowingFilter
       exists to ask a question ABOUT — so narrows is false. */
    isSearching: { empty: function () { return false; }, narrows: false }
  };

  // Derived, never hand-maintained: these two are why adding a field to
  // FIELD_SPEC is the whole change.
  var FIELDS = Object.keys(FIELD_SPEC);
  var NARROWING_FIELDS = FIELDS.filter(function (f) { return FIELD_SPEC[f].narrows; });

  // A fresh, fully-cleared state. What clearAllFilters() assigns.
  function emptyState() {
    var state = {};
    FIELDS.forEach(function (f) { state[f] = FIELD_SPEC[f].empty(); });
    return state;
  }

  /* "Does this field hold anything?", answered from the VALUE rather than from
     a per-field predicate, so a new field needs no predicate written for it.
     Sets are asked for their size (duck-typed rather than `instanceof Set`,
     which is false across a realm boundary — a Node test's Set is not a
     browser frame's Set); strings and booleans and null answer for themselves.
     Anything else is a value someone deliberately stored, so it counts. */
  function isFieldSet(value) {
    if (value === null || value === undefined || value === false || value === '') return false;
    if (typeof value.size === 'number') return value.size > 0;
    return true;
  }

  /* "Is there anything for the clear-all button to clear?" — purely the
     button's visibility, and it must agree with what clear-all actually
     clears, or the button hides while still having work to do. It agrees by
     construction: clear-all assigns emptyState(), and both walk FIELDS. */
  function hasAnythingToClear(state) {
    return FIELDS.some(function (f) { return isFieldSet((state || {})[f]); });
  }

  function isEmpty(state) {
    return !hasAnythingToClear(state);
  }

  /* A DIFFERENT QUESTION, and it must stay different — GitHub issue #248.
     There used to be three near-identical expressions in filters.js and the
     issue read as "unify them"; unifying them would have been wrong, because
     this one and hasAnythingToClear ask genuinely different things and
     collapsing them trades a documented difference for a silent behaviour
     change at whichever call site loses its own answer.

     This one asks: "while the ingredient box is being typed into, is anything
     ELSE still narrowing the list?" It is the one input to filters.js's
     suppressList, which decides whether the list hides behind the "searching"
     message. Hence NARROWING_FIELDS rather than FIELDS: see `ingredient` and
     `isSearching` in FIELD_SPEC for why each is excluded. */
  function hasNarrowingFilter(state) {
    return NARROWING_FIELDS.some(function (f) { return isFieldSet((state || {})[f]); });
  }

  var api = {
    KINDS: KINDS,
    EXCLUDE_PREFIX: EXCLUDE_PREFIX,
    parseQuery: parseQuery,
    FIELDS: FIELDS,
    NARROWING_FIELDS: NARROWING_FIELDS,
    emptyState: emptyState,
    isFieldSet: isFieldSet,
    hasAnythingToClear: hasAnythingToClear,
    isEmpty: isEmpty,
    hasNarrowingFilter: hasNarrowingFilter
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  } else {
    root.HTF = root.HTF || {};
    root.HTF.filterState = api;
  }
})(typeof window !== 'undefined' ? window : this);
