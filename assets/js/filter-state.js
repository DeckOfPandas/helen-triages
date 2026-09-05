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
  //
  // `mood` JOINED THEM ON 2026-09-05, when the drink page's mood chips became
  // links to a pre-filtered index -- Helen: "let's wire the chips up to show a
  // filtered index page please, echoing what we do on the food site, which
  // feels lovely." That is food's badge behaviour exactly (see
  // _includes/recipe_badges.html), and this list is the one place the grammar
  // is written down for both sites.
  //
  // THE LIST IS SHARED AND THAT COSTS NOTHING. `star` and `tag` mean nothing on
  // the cocktails index and `mood` means nothing on food's; each index reads
  // only the keys it has buttons for, and a parsed key nobody asks about is an
  // empty array. Splitting this per site would be two grammars to keep in step
  // for no gain -- and this file's own header already argues that the query
  // grammar is one thing.
  var KINDS = ['star', 'tag', 'mood'];

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

    /* THE DISLIKE NAVIGATOR — GitHub issue #52's actual goal, in Helen's
       words: "I have invited someone for dinner and they hate peas, so I want
       to see all recipes that do NOT contain peas as an ingredient."

       A Set of entries from the DERIVED ingredient index (food/index.html's
       `data-all-ingredients`, built from every ingredient_groups item on the
       row, incidentals included) — not from main_ingredients, which is a
       deliberately partial hint and so is safe to include ON but dangerous to
       exclude BY. Multi-select, like tags: a row is dropped if it lists ANY of
       these.

       Narrowing, and this is the one field where that is worth saying out
       loud: an exclusion is a filter with no button of its own lit up
       anywhere in the matrix, so if it did not count towards
       hasAnythingToClear the clear-all button would hide while a filter was
       still silently removing rows — the issue-#52 bug all over again, in the
       feature issue #52 was actually about. Declaring it here is the entire
       change: emptyState(), hasAnythingToClear(), hasNarrowingFilter() and
       the generated per-field cases in tests/js/filter-state.test.js all pick
       it up by iteration. */
    excludedIngredients: { empty: function () { return new Set(); }, narrows: true },

    /* The chosen ingredient-search result. NOT narrowing, deliberately:
       filters.js's renderResultsPool() nulls it on every keystroke, so while
       the ingredient box is being typed into it is always null, and including
       it in hasNarrowingFilter would be a no-op dressed up as a rule. */
    ingredient: { empty: function () { return null; }, narrows: false },

    // The meta filters (rewrite/proofread/short/draft), local builds only.
    meta: { empty: function () { return new Set(); }, narrows: true },

    /* SHOW ONLY WHAT IS SHORTLISTED — GitHub issue #546. A boolean, and the
       first one in this table that is a real filter rather than a
       half-finished-search flag.

       THE ANSWER IS NOT ON THE ROW, which is what makes this field different
       from every other one here. `tags`, `star` and `meta` are all matched
       against something the build wrote into the markup; whether a recipe is
       shortlisted is a fact about THIS BROWSER, held in localStorage by
       HTF.shortlist. rowMatchesFilters stays pure by being handed the answer
       (`row.shortlisted`) rather than reaching for the store itself — the same
       arrangement `familyMatch` already has for the ingredient index.

       NARROWING, and clear-all DOES clear it. Both follow from it being an
       ordinary filter: it hides rows, so the "searching" message must not
       replace a shortlisted view; and `clear all` means "show me everything
       again", which would be a lie if one filter survived it. */
    shortlisted: { empty: function () { return false; }, narrows: true },

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
    isSearching: { empty: function () { return false; }, narrows: false },

    /* isSearching's sibling for the LEAVE OUT box (#exclude-search-box, GitHub
       issue #52) — "the exclude box has text in it and nothing has been
       chosen from its results yet". GitHub issue #274: this field simply did
       not exist, so typing "pea" into the exclude box set no state at all,
       hasAnythingToClear() correctly answered "nothing is set", and the clear
       button stayed hidden beside a pool of results you had no other way to
       dismiss but deleting the text by hand — the exact isSearching bug,
       recurring because the exclude box's half-finished search had no field
       of its own to be forgotten from. Same shape as isSearching for the same
       reasons: clear-all DOES clear it (empties the box and its results pool,
       see clearAllFilters()), so it must count towards hasAnythingToClear; it
       does not narrow anything, so narrows is false. */
    isExcludeSearching: { empty: function () { return false; }, narrows: false }
  };

  /* THE COCKTAIL INDEX'S FIELDS — GitHub issue #579.
     ---------------------------------------------------------------------------
     A SECOND TABLE, NOT A SECOND MECHANISM, and the distinction is the whole
     decision. Everything below the tables -- emptyState, hasAnythingToClear,
     serialise, the generated per-field test cases -- is written once and takes
     a spec. The tables are separate because the two indexes genuinely ask
     different questions: there is no cocktail equivalent of a star ingredient,
     and no food equivalent of chaos.

     WHY THIS IS WORTH DOING AT ALL, rather than leaving cocktail-index.js its
     five loose variables: issue #541 asks for a clear-all button on this page,
     "very much like food site". Food's clear-all is the exact feature that
     produced the bug three times in two days -- clearAllFilters() emptied N
     things and the button's visibility predicate checked N-1, so it hid while
     it still had work to do. Building #541 on five loose variables and six
     hand-written showClear() calls is that bug's own conditions, reassembled.

     What each field is, and what the page does with it:

       moods      Set, MOOD and HASSLE together. One filter with two headings --
                  a drink matching either is matched the same way -- and the
                  headings only differ in which CLEAR link owns them.
       chaos      string|null. `good` narrows; `open` is a visible STATE that
                  applies no filter at all, which is the #478 fix rather than an
                  oversight (the button for "I'll try anything" used to be the
                  one button guaranteed to hide all 55 of the best drinks). It
                  is still CLEARABLE while set, because the button is lit.
       include    Set of pool entries, AND between them: adding an ingredient
                  means "and this one too", which is how a cupboard works.
       exclude    Set of pool entries, matched EXACTLY or through a declared
                  family -- see assets/js/cocktail-search.js for why exclusion
                  is the strict direction.
       nameQuery  I KNOW WHAT I WANT, folded and lowercased by the wiring. */
  var COCKTAIL_FIELD_SPEC = {
    moods: { empty: function () { return new Set(); }, narrows: true },
    chaos: { empty: function () { return null; }, narrows: true },
    include: { empty: function () { return new Set(); }, narrows: true },
    exclude: { empty: function () { return new Set(); }, narrows: true },
    nameQuery: { empty: function () { return ''; }, narrows: true },

    /* The same field the food table declares, and it means the same thing on
       both sites — see FIELD_SPEC's own note for why the answer arrives on the
       row rather than being looked up here. The two tables stay separate
       because the two indexes ask genuinely different questions; this is one of
       the few they both ask. */
    shortlisted: { empty: function () { return false; }, narrows: true },

    /* isSearching's two siblings, and they are here for the reason its own
       entry above gives: clear-all DOES empty these boxes and their candidate
       pools, so the clear button must offer itself while one is set. Typing
       "gi" into HAS TO HAVE and picking nothing leaves a pool of chips on
       screen with no other way to dismiss them but deleting the text by hand.
       That is issue #274 on the food side, and it is cheaper to declare the
       field than to rediscover it here. */
    isIncludeSearching: { empty: function () { return false; }, narrows: false },
    isExcludeSearching: { empty: function () { return false; }, narrows: false }
  };

  // Derived, never hand-maintained: these two are why adding a field to a spec
  // is the whole change.
  var FIELDS = Object.keys(FIELD_SPEC);
  var NARROWING_FIELDS = FIELDS.filter(function (f) { return FIELD_SPEC[f].narrows; });

  /* Every function below takes the SPEC it is working from, and `create(spec)`
     at the foot of the file binds one to a table. The food-shaped names this
     module has always exported (emptyState, hasAnythingToClear, ...) are that
     binding over FIELD_SPEC, so filters.js and every existing test are
     untouched by the parameterisation. */

  // A fresh, fully-cleared state. What clearAllFilters() assigns.
  function emptyStateFor(spec) {
    var state = {};
    Object.keys(spec).forEach(function (f) { state[f] = spec[f].empty(); });
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
  function hasAnythingToClearFor(spec, state) {
    return Object.keys(spec).some(function (f) { return isFieldSet((state || {})[f]); });
  }

  /* ---------------------------------------------------------------------------
     THE EXCLUSION RULE — GitHub issue #52
     ---------------------------------------------------------------------------

     "Does this row list anything the cook has ruled out?", answered against the
     row's DERIVED ingredient entries (food/index.html's data-all-ingredients,
     put through HTF.ingredientSearch.buildMasterList by filters.js so both
     sides of the comparison have had the same normalisation).

     SET MEMBERSHIP, NOT SUBSTRING, and this is the whole rule. The real
     collection holds `peas`, `peanut butter`, `smooth peanut butter`,
     `roasted peanuts` and `organic pearl barley`. A "contains" test for the
     short things people type takes all five out at once; excluding peas would
     silently lose the peanut butter cookies and the pearl barley casserole.
     The picker hands back a REAL ENTRY, chosen from a list where all five were
     offered side by side, so the row test compares whole entries and nothing
     else. The fuzziness belongs in FINDING the entry, never in applying it.

     A "(all)" family button (the picker offers "chicken (all)" over chicken
     breast/thighs/stock) is the one umbrella, and it says so on its face.
     Matching a family needs the ingredient vocabulary — singulars, synonyms,
     modifier stripping — which this module deliberately does not have and is
     not going to grow, so the caller passes `familyMatch(entries, key)` in.
     With no familyMatch supplied, an "(all)" value falls through to the same
     exact comparison as everything else and simply matches nothing: no
     vocabulary, no umbrella, and never a silent substring rule sneaking in
     through the back door. */
  var FAMILY_SUFFIX = ' (all)';

  function isFamilyValue(value) {
    return typeof value === 'string' &&
      value.length > FAMILY_SUFFIX.length &&
      value.slice(-FAMILY_SUFFIX.length) === FAMILY_SUFFIX;
  }

  function familyKey(value) {
    return value.slice(0, -FAMILY_SUFFIX.length).trim();
  }

  function excludesRow(entries, excluded, familyMatch) {
    if (!excluded) return false;
    var list = entries || [];
    var values = typeof excluded.forEach === 'function' ? excluded : [];
    var hit = false;
    values.forEach(function (value) {
      if (hit) return;
      if (familyMatch && isFamilyValue(value)) {
        if (familyMatch(list, familyKey(value))) hit = true;
      } else if (list.indexOf(value) !== -1) {
        hit = true;
      }
    });
    return hit;
  }

  /* THE OTHER HALF OF THE ROW QUESTION — "is this row one you asked for?" —
     issue #506, and it is deliberately NOT merged with excludesRow above.
     ---------------------------------------------------------------------
     filters.js runs them in this order and says why: everything here decides
     whether a row is one you asked for, and excludesRow decides whether it is
     one you cannot serve. Keeping them apart is what makes the excluded COUNT
     meaningful -- the panel reports how many rows survived every other filter
     and were dropped only for what they list, which a single merged predicate
     could not tell you.

     WHY IT MOVED. It was 40 lines inside filters.js's update(), the one module
     in HANDOVER 3's table with no tests at all, reading five data- attributes
     off a live <li>. Every rule below is a decision with a handful of inputs
     and no need of a DOM, which is back-link.js's argument exactly.

     THE ROW IS PRE-NORMALISED BY THE CALLER, the same contract excludesRow
     already states for `entries`: `titleFolded` has been through
     ingredientSearch.fold on a lowercased title, because `state.nameQuery` is
     stored folded and a comparison between one folded and one raw string is a
     silent miss. filters.js computes it only when there IS a name query, so an
     empty `titleFolded` on a row means "not asked", never "no title".

     WITHOUT A `familyMatch` AN INGREDIENT FILTER SELECTS NOTHING, where the
     same omission on the exclude side excludes nothing. Both are "the umbrella
     cannot be applied", and each fails in the direction that shows: an empty
     list is visibly wrong, where a silently unenforced exclusion would hand
     back the very thing you ruled out. */
  function rowMatchesFilters(row, state, familyMatch) {
    var r = row || {};
    var s = state || {};

    // AND across chosen tags: two tags means both, which is how a shelf works.
    var rowTags = r.tags || [];
    var missing = false;
    if (s.tags && typeof s.tags.forEach === 'function') {
      s.tags.forEach(function (t) { if (rowTags.indexOf(t) === -1) missing = true; });
    }
    if (missing) return false;

    if (s.star && (r.star || '') !== s.star) return false;

    if (s.nameQuery && String(r.titleFolded || '').indexOf(s.nameQuery) === -1) return false;

    /* ONE META FILTER, AND `draft` IS IT -- issue #562 removed the other four
       (`rewrite`, `proofread`, `no-short`, `has-short`) and their attributes
       with them. `draft` needs none of the care they did: every row either is
       a draft or is not, where "does this have a short method" had no answer
       at all for a magic-bag row and needed three values to say so. */
    if (s.meta && typeof s.meta.has === 'function' &&
        s.meta.has('draft') && !r.isDraft) return false;

    /* SHORTLISTED — #546. `row.shortlisted` is the caller's answer from
       HTF.shortlist, not a data- attribute: the build cannot know what is in
       this browser's localStorage. Asked here rather than in filters.js so that
       it composes with everything above it by construction — shortlisted AND
       make-ahead is one predicate, not two places that have to agree. */
    if (s.shortlisted && !r.shortlisted) return false;

    if (s.ingredient) {
      var key = String(s.ingredient).replace(FAMILY_SUFFIX, '').trim();
      if (!familyMatch || !familyMatch(r.ingredients || [], key)) return false;
    }

    return true;
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
  function hasNarrowingFilterFor(spec, state) {
    return Object.keys(spec).filter(function (f) { return spec[f].narrows; })
      .some(function (f) { return isFieldSet((state || {})[f]); });
  }

  /* THE ONE BROWSER FACT THE RESTORE RESTS ON — #387, and shared by both
     indexes since #595 rather than written twice.

     BFCACHE IS NOT THE MECHANISM, and building on it was the first attempt.
     `jekyll serve` sends `Cache-Control: ... no-store ...` (measured with
     curl -I, not assumed) and no-store disqualifies a page from bfcache in
     Chrome and Firefox -- so on the machine this site is developed on it can
     NEVER apply, and a feature resting on it would work on the deployed site
     and not on :4001. That is issue #235's trap running backwards: the page
     Helen looks at all day disagreeing with the live one.

     The navigation TYPE is a fact rather than a favour. It says whether this
     load was a back/forward navigation whether or not bfcache was involved,
     and paired with sessionStorage it needs nothing from the browser's
     goodwill. `performance` is injected so this can be asked a question
     without one. */
  function arrivedByGoingBack(perf) {
    var timing = perf || (typeof performance !== 'undefined' ? performance : null);
    try {
      var nav = timing.getEntriesByType('navigation')[0];
      return !!nav && nav.type === 'back_forward';
    } catch (e) {
      return false;    // no Navigation Timing: behave as a fresh visit
    }
  }

  // ---------------------------------------------------------------------------
  // SERIALISING THE STATE — GitHub issue #387
  // ---------------------------------------------------------------------------
  // For sessionStorage, so that returning to the index by going BACK restores
  // the list you left rather than a fresh one. NOT for URLs: `toQuery()` above
  // is still deliberately absent, because the thing that would have called it
  // wants the shuffle ORDER too, which is not a filter and has no business in a
  // filter grammar.
  //
  // WHY THIS IS NEEDED AT ALL, since it looks like something JSON already does:
  // three of the eight fields are Sets, and `JSON.stringify(new Set())` is
  // `{}` — not an error, not an empty array, just silently nothing. A state
  // round-tripped through raw JSON comes back with its tags, its exclusions and
  // its meta filters quietly emptied, and the symptom is "some of my filters
  // came back and some didn't", which is a horrible thing to debug.
  //
  // DERIVED FROM FIELD_SPEC, like everything else here: a field added to that
  // table is serialised, restored and defaulted with no change to this code.
  // Each field's shape is read from its own `empty()` value rather than from a
  // list of names — the same reasoning isFieldSet() already uses.
  function serialiseFor(spec, state) {
    var out = {};
    Object.keys(spec).forEach(function (f) {
      var value = state ? state[f] : undefined;
      // Duck-typed rather than `instanceof Set` — see isFieldSet() for why that
      // is false across a realm boundary.
      if (value && typeof value.forEach === 'function' && typeof value.size === 'number') {
        var list = [];
        value.forEach(function (v) { list.push(v); });
        out[f] = list;
      } else {
        out[f] = value === undefined ? null : value;
      }
    });
    return out;
  }

  /* The inverse, and deliberately forgiving: anything missing, malformed or the
     wrong type falls back to that field's own empty value. Stored state is
     UNTRUSTED INPUT — it can be a version behind, hand-edited in devtools, or
     left from a build where a field meant something else — and the cost of a
     bad restore is an index that looks wrong with no way to tell why, while the
     cost of falling back is one unfiltered page. */
  function deserialiseFor(spec, raw) {
    var state = emptyStateFor(spec);
    if (!raw || typeof raw !== 'object') return state;
    Object.keys(spec).forEach(function (f) {
      if (!(f in raw)) return;
      var blank = spec[f].empty();
      var value = raw[f];
      if (blank instanceof Set) {
        if (Array.isArray(value)) state[f] = new Set(value);
      } else if (typeof blank === 'string') {
        if (typeof value === 'string') state[f] = value;
      } else if (typeof blank === 'boolean') {
        state[f] = !!value;
      } else if (typeof value === 'string' || value === null) {
        state[f] = value;
      }
    });
    return state;
  }

  /* ONE MECHANISM BOUND TO ONE TABLE — GitHub issue #579.

     Everything a caller wants, derived from the spec it is handed and from
     nothing else. Two indexes, two tables, and no second copy of the reasoning
     that keeps a clear-all button honest.

     The returned object is the whole contract: a caller never sees the spec
     again, which is what stops a call site quietly reaching past the mechanism
     to a field list of its own -- the exact move that produced the food bug
     this file was written for. */
  function create(spec) {
    var fields = Object.keys(spec);
    return {
      FIELDS: fields,
      NARROWING_FIELDS: fields.filter(function (f) { return spec[f].narrows; }),
      emptyState: function () { return emptyStateFor(spec); },
      isFieldSet: isFieldSet,
      hasAnythingToClear: function (state) { return hasAnythingToClearFor(spec, state); },
      isEmpty: function (state) { return !hasAnythingToClearFor(spec, state); },
      hasNarrowingFilter: function (state) { return hasNarrowingFilterFor(spec, state); },
      serialise: function (state) { return serialiseFor(spec, state); },
      deserialise: function (raw) { return deserialiseFor(spec, raw); }
    };
  }

  // The food index's binding, exported under the names this module has always
  // used, so filters.js is untouched by any of the above.
  var food = create(FIELD_SPEC);

  var api = {
    KINDS: KINDS,
    EXCLUDE_PREFIX: EXCLUDE_PREFIX,
    parseQuery: parseQuery,
    serialise: food.serialise,
    deserialise: food.deserialise,
    FIELDS: FIELDS,
    NARROWING_FIELDS: NARROWING_FIELDS,
    emptyState: food.emptyState,
    isFieldSet: isFieldSet,
    FAMILY_SUFFIX: FAMILY_SUFFIX,
    excludesRow: excludesRow,
    // The pair, and food-shaped: tags, star, name, meta and the one ingredient
    // key are the food index's questions. The cocktail index asks a different
    // five and answers them in cocktail-index.js against COCKTAIL_FIELDS.
    rowMatchesFilters: rowMatchesFilters,
    arrivedByGoingBack: arrivedByGoingBack,
    hasAnythingToClear: food.hasAnythingToClear,
    isEmpty: food.isEmpty,
    hasNarrowingFilter: food.hasNarrowingFilter,

    // The two tables, and the factory that binds either. FOOD_FIELDS is the
    // same object the food-shaped exports above are bound to, exported so a
    // test can generate its per-field cases from whichever spec it is checking
    // rather than from a hand-written list -- which is the omission problem
    // this whole file exists to remove.
    create: create,
    FOOD_FIELDS: FIELD_SPEC,
    COCKTAIL_FIELDS: COCKTAIL_FIELD_SPEC
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  } else {
    root.HTF = root.HTF || {};
    root.HTF.filterState = api;
  }
})(typeof window !== 'undefined' ? window : this);
