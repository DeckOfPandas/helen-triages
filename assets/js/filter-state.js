// =============================================================================
// FILTER STATE — the index's filter query string and state shape. No DOM;
// filters.js and cocktail-index.js are the wiring (MANUAL §3).
//
// Loaded as a plain <script> before filters.js (attaching to window.HTF), and
// via require() in tests/js/filter-state.test.js.
//
// The grammar:   /food/?star=lamb&tag=soup,make-ahead
//   - One parameter per filter kind, values comma-separated. The split happens
//     before decoding, so a value containing a comma can be spelled `%2C`.
//   - A leading `-` is reserved for "exclude" and such a value is dropped.
//   - Unknown parameters are ignored.
//   - `+` decodes to a space: Jekyll's `url_encode` writes a space as `+` and
//     decodeURIComponent does not undo that.
// =============================================================================
(function (root) {
  'use strict';

  // The filter kinds this grammar knows; parseQuery always returns a key for
  // each. The list is shared by both sites: each index reads only the keys it
  // has buttons for. `ing` is the one kind both read, and each matches it
  // against what its own picker would offer, never by substring (#1050).
  var KINDS = ['star', 'tag', 'mood', 'ing'];

  var EXCLUDE_PREFIX = '-';

  // Decodes one raw token. `+` becomes `%20` before decoding, so a genuine
  // plus spelled `%2B` survives. A malformed escape yields '' and the caller
  // drops it, so a hand-mangled URL cannot take the page down.
  function decodeValue(raw) {
    try {
      return decodeURIComponent(String(raw).replace(/\+/g, '%20'));
    } catch (e) {
      return '';
    }
  }

  // location.search (with or without its leading '?') -> one array per kind,
  // values in the order they appeared, deduplicated. Arity is the caller's
  // business: the star filter is single-select and filters.js picks one.
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
        // Checked on both sides of the decode: `-soup` and `%2Dsoup` are the
        // same claim spelled two ways.
        if (rawValue.charAt(0) === EXCLUDE_PREFIX) return;
        var value = decodeValue(rawValue).trim();
        if (!value || value.charAt(0) === EXCLUDE_PREFIX) return;
        if (out[kind].indexOf(value) === -1) out[kind].push(value);
      });
    });

    return out;
  }

  // The name query is not a kind (#1024). `?q=<text>` is what the reader typed
  // into the search box, whole: a title may carry a comma, so it must not go
  // through the comma-split above. The last `q` wins; an empty one is no query.
  function parseName(search) {
    var body = String(search == null ? '' : search).replace(/^[?#]/, '');
    var name = '';
    body.split('&').forEach(function (chunk) {
      var eq = chunk.indexOf('=');
      if (eq === -1) return;
      if (decodeValue(chunk.slice(0, eq)) !== 'q') return;
      var value = decodeValue(chunk.slice(eq + 1)).trim();
      if (value) name = value;
    });
    return name;
  }

  // `?ship=<value>` is one exact `meta.ship` value, from a drink page's SHIP IT?
  // link (#1412). Not a kind: a single value, never comma-split. The last
  // `ship` wins; the caller drops a value no card carries.
  function parseShip(search) {
    var body = String(search == null ? '' : search).replace(/^[?#]/, '');
    var ship = '';
    body.split('&').forEach(function (chunk) {
      var eq = chunk.indexOf('=');
      if (eq === -1) return;
      if (decodeValue(chunk.slice(0, eq)) !== 'ship') return;
      var value = decodeValue(chunk.slice(eq + 1)).trim();
      if (value) ship = value;
    });
    return ship;
  }

  // The shortlist query is not a kind either, and has two meanings (#1093):
  //   ?shortlist=1                  this browser's own shortlist
  //   ?shortlist=negroni,aviation   a shortlist someone sent, by slug
  // A slug is [a-z0-9-] and nothing else; anything outside that is dropped,
  // because a link is untrusted input. `1` alone is the own-list flag, never a
  // slug. The last `shortlist` parameter wins.
  // -> { own: boolean, slugs: string[] }; never both.
  var SLUG_RE = /^[a-z0-9][a-z0-9-]*$/;

  function parseShortlist(search) {
    var body = String(search == null ? '' : search).replace(/^[?#]/, '');
    var out = { own: false, slugs: [] };
    body.split('&').forEach(function (chunk) {
      var eq = chunk.indexOf('=');
      if (eq === -1) return;
      if (decodeValue(chunk.slice(0, eq)) !== 'shortlist') return;
      var raw = chunk.slice(eq + 1);
      out = { own: false, slugs: [] };
      if (decodeValue(raw).trim() === '1') { out.own = true; return; }
      raw.split(',').forEach(function (rawValue) {
        var slug = decodeValue(rawValue).trim().toLowerCase();
        if (!SLUG_RE.test(slug) || slug === '1') return;
        if (out.slugs.indexOf(slug) === -1) out.slugs.push(slug);
      });
    });
    return out;
  }

  // The query string parseShortlist reads back as these slugs. Slugs failing
  // the same test are left out, so a link this writes is always one this
  // reads. '' for an empty list.
  function shortlistQuery(slugs) {
    var kept = [];
    (Array.isArray(slugs) ? slugs : []).forEach(function (s) {
      var slug = String(s).trim().toLowerCase();
      if (SLUG_RE.test(slug) && slug !== '1' && kept.indexOf(slug) === -1) kept.push(slug);
    });
    return kept.length ? 'shortlist=' + kept.join(',') : '';
  }

  // --- the state shape --------------------------------------------------------

  // Every field of the food index's filter state; the only place the list is
  // written. A field declares:
  //   empty      a factory for its cleared value (a factory, because a shared
  //              empty Set would be one Set mutated from two places)
  //   narrows    whether it counts as "something is still narrowing the list"
  //              -- see hasNarrowingFilterFor
  //   keepsView  set on the half-typed-search flags: text in a box does not
  //              leave the shortlist view, only choosing a result does (#918)
  var FIELD_SPEC = {
    // The tag buttons. Multi-select: a row needs every active tag.
    tags: { empty: function () { return new Set(); }, narrows: true },

    // Star ingredient. Single-select.
    star: { empty: function () { return null; }, narrows: true },

    // LEAVE OUT (#52). Entries from the derived ingredient index
    // (`data-all-ingredients`), not from main_ingredients, which is a partial
    // hint and unsafe to exclude by. A row is dropped if it lists any of them.
    excludedIngredients: { empty: function () { return new Set(); }, narrows: true },

    // HAS TO HAVE (#1092). A row survives only if it has every chosen entry.
    includedIngredients: { empty: function () { return new Set(); }, narrows: true },

    // Show only what is shortlisted (#546). The answer is not on the row: it
    // is a fact about this browser, so rowMatchesFilters is handed
    // `row.shortlisted`. It is a view, not a facet (#918): never true while
    // any other narrowing field is set -- see enterShortlistViewFor and
    // reconcileShortlistViewFor.
    shortlisted: { empty: function () { return false; }, narrows: true },

    // The title search, folded and lowercased by filters.js before it lands
    // here.
    nameQuery: { empty: function () { return ''; }, narrows: true },

    // Not a filter: the ingredient box has text in it and nothing has been
    // chosen yet. It is a field because clear-all clears it, so the clear
    // button must offer itself while it is set. It narrows nothing.
    isSearching: { empty: function () { return false; }, narrows: false, keepsView: true },

    // The same flag for the LEAVE OUT box (#274).
    isExcludeSearching: { empty: function () { return false; }, narrows: false, keepsView: true }
  };

  // The cocktail index's fields (#579): a second table, not a second
  // mechanism. Everything below the tables takes a spec.
  //   moods      Set; MOOD and HASSLE together, one filter under two headings
  //   chaos      string|null; null is the YOLO switch at rest, painted as
  //              `open`, which applies no filter (#478, #1440)
  //   include    Set of pool entries, AND between them
  //   exclude    Set of pool entries, exact or through a declared family
  //   nameQuery  I KNOW WHAT I WANT, folded and lowercased by the wiring
  var COCKTAIL_FIELD_SPEC = {
    moods: { empty: function () { return new Set(); }, narrows: true },
    chaos: { empty: function () { return null; }, narrows: true },

    // One exact `meta.ship`, from a card's mark (#1412); ANDed with `chaos`.
    ship: { empty: function () { return null; }, narrows: true },

    include: { empty: function () { return new Set(); }, narrows: true },
    exclude: { empty: function () { return new Set(); }, narrows: true },
    nameQuery: { empty: function () { return ''; }, narrows: true },

    // Same meaning as in FIELD_SPEC.
    shortlisted: { empty: function () { return false; }, narrows: true },

    // Half-typed searches, as isSearching in FIELD_SPEC.
    isIncludeSearching: { empty: function () { return false; }, narrows: false, keepsView: true },
    isExcludeSearching: { empty: function () { return false; }, narrows: false, keepsView: true }
  };

  // Derived, never hand-maintained.
  var FIELDS = Object.keys(FIELD_SPEC);
  var NARROWING_FIELDS = FIELDS.filter(function (f) { return FIELD_SPEC[f].narrows; });

  // A fresh, fully-cleared state. What clear-all assigns.
  function emptyStateFor(spec) {
    var state = {};
    Object.keys(spec).forEach(function (f) { state[f] = spec[f].empty(); });
    return state;
  }

  // "Does this field hold anything?", answered from the value, so a new field
  // needs no predicate. Sets are duck-typed by `size`: `instanceof Set` is
  // false across a realm boundary (a Node test's Set is not a browser frame's).
  function isFieldSet(value) {
    if (value === null || value === undefined || value === false || value === '') return false;
    if (typeof value.size === 'number') return value.size > 0;
    return true;
  }

  // The clear-all button's visibility. It must agree with what clear-all
  // clears, or the button hides while it still has work to do; both walk the
  // same spec.
  function hasAnythingToClearFor(spec, state) {
    return Object.keys(spec).some(function (f) { return isFieldSet((state || {})[f]); });
  }

  // The shortlist view (#918). enterShortlistViewFor is the state the
  // shortlist button produces when pressed on: everything cleared,
  // `shortlisted` true. The caller still empties its own text boxes and pools.
  function enterShortlistViewFor(spec) {
    var state = emptyStateFor(spec);
    if ('shortlisted' in spec) state.shortlisted = true;
    return state;
  }

  // Run at the top of every apply(), so a restored record is reconciled too:
  // if the view is on and another field is set, the view is left. Returns true
  // when it did so. `keepsView` fields are ignored.
  function reconcileShortlistViewFor(spec, state) {
    var s = state || {};
    if (!s.shortlisted) return false;
    var other = Object.keys(spec).some(function (f) {
      return f !== 'shortlisted' && !spec[f].keepsView && isFieldSet(s[f]);
    });
    if (other) s.shortlisted = false;
    return other;
  }

  // The exclusion rule (#52): set membership against the row's derived
  // ingredient entries, never substring -- excluding `peas` by substring would
  // also lose `peanut butter` and `pearl barley`. The fuzziness belongs in
  // finding the entry, never in applying it. An "(all)" value is the one
  // umbrella, matched by the caller's `familyMatch(entries, key)`; with none
  // supplied it falls through to the exact comparison and matches nothing.
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

  // HAS TO HAVE (#1092): does this row have every required ingredient? Not
  // excludesRow flipped: every value goes through familyMatch, suffix or not,
  // because this matches against `main_ingredients`, a partial hint, where
  // "chicken" has to reach "chicken breast". With no familyMatch it fails
  // closed: an empty list is visibly wrong.
  function includesRow(entries, included, familyMatch) {
    if (!included) return true;
    var list = entries || [];
    var values = typeof included.forEach === 'function' ? included : [];
    var everyMatch = true;
    values.forEach(function (value) {
      if (!everyMatch) return;
      var key = isFamilyValue(value) ? familyKey(value) : String(value).trim();
      if (!familyMatch || !familyMatch(list, key)) everyMatch = false;
    });
    return everyMatch;
  }

  // "Is this row one you asked for?" (#506). Kept apart from excludesRow so
  // the caller can count the rows dropped only for what they list.
  // The row is pre-normalised by the caller: `titleFolded` must be folded and
  // lowercased, because `state.nameQuery` is stored that way.
  function rowMatchesFilters(row, state, familyMatch) {
    var r = row || {};
    var s = state || {};

    // AND across chosen tags.
    var rowTags = r.tags || [];
    var missing = false;
    if (s.tags && typeof s.tags.forEach === 'function') {
      s.tags.forEach(function (t) { if (rowTags.indexOf(t) === -1) missing = true; });
    }
    if (missing) return false;

    // A row answers its own star and any `starAlso` (taxonomy.yml `star_also`).
    if (s.star && (r.star || '') !== s.star
        && (r.starAlso || []).indexOf(s.star) === -1) return false;

    if (s.nameQuery && String(r.titleFolded || '').indexOf(s.nameQuery) === -1) return false;

    // `row.shortlisted` is the caller's answer from HTF.shortlist, not a data-
    // attribute: the build cannot know what is in this browser's localStorage.
    if (s.shortlisted && !r.shortlisted) return false;

    if (!includesRow(r.ingredients || [], s.includedIngredients, familyMatch)) return false;

    return true;
  }

  // A different question from hasAnythingToClear, and it must stay different
  // (#248): "while an ingredient box is being typed into, is anything else
  // still narrowing the list?" It decides whether the list hides behind the
  // "searching" message, so the half-typed-search flags do not count.
  function hasNarrowingFilterFor(spec, state) {
    return Object.keys(spec).filter(function (f) { return spec[f].narrows; })
      .some(function (f) { return isFieldSet((state || {})[f]); });
  }

  // The browser fact the restore rests on (#387): the navigation type, not
  // bfcache. `jekyll serve` sends `no-store`, which disqualifies a page from
  // bfcache, so a restore built on it would work live and not locally.
  // `perf` is injected for tests.
  function arrivedByGoingBack(perf) {
    var timing = perf || (typeof performance !== 'undefined' ? performance : null);
    try {
      var nav = timing.getEntriesByType('navigation')[0];
      return !!nav && nav.type === 'back_forward';
    } catch (e) {
      return false;    // no Navigation Timing: behave as a fresh visit
    }
  }

  // --- serialising the state (#387) -------------------------------------------
  // For sessionStorage, so going back restores the list you left; not for URLs.
  // Needed because `JSON.stringify(new Set())` is `{}`: a state round-tripped
  // through raw JSON silently loses every Set field. Each field's shape is read
  // from its own `empty()` value.
  function serialiseFor(spec, state) {
    var out = {};
    Object.keys(spec).forEach(function (f) {
      var value = state ? state[f] : undefined;
      // Duck-typed rather than `instanceof Set` — see isFieldSet().
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

  // The inverse, and deliberately forgiving: stored state is untrusted input
  // (a version behind, or hand-edited), so anything missing, malformed or the
  // wrong type falls back to that field's own empty value.
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

  // One mechanism bound to one table (#579). The returned object is the whole
  // contract: a caller never sees the spec again, so no call site can keep a
  // field list of its own.
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
      enterShortlistView: function () { return enterShortlistViewFor(spec); },
      reconcileShortlistView: function (state) { return reconcileShortlistViewFor(spec, state); },
      serialise: function (state) { return serialiseFor(spec, state); },
      deserialise: function (raw) { return deserialiseFor(spec, raw); }
    };
  }

  // The food index's binding; the unprefixed exports below are bound to it.
  var food = create(FIELD_SPEC);

  var api = {
    KINDS: KINDS,
    EXCLUDE_PREFIX: EXCLUDE_PREFIX,
    parseQuery: parseQuery,
    parseName: parseName,
    parseShip: parseShip,
    parseShortlist: parseShortlist,
    shortlistQuery: shortlistQuery,
    serialise: food.serialise,
    deserialise: food.deserialise,
    FIELDS: FIELDS,
    NARROWING_FIELDS: NARROWING_FIELDS,
    emptyState: food.emptyState,
    isFieldSet: isFieldSet,
    FAMILY_SUFFIX: FAMILY_SUFFIX,
    excludesRow: excludesRow,
    includesRow: includesRow,
    // Food-shaped; the cocktail index answers its own row question in
    // cocktail-index.js against COCKTAIL_FIELDS.
    rowMatchesFilters: rowMatchesFilters,
    arrivedByGoingBack: arrivedByGoingBack,
    hasAnythingToClear: food.hasAnythingToClear,
    isEmpty: food.isEmpty,
    hasNarrowingFilter: food.hasNarrowingFilter,
    enterShortlistView: food.enterShortlistView,
    reconcileShortlistView: food.reconcileShortlistView,

    // The two tables and the factory that binds either. Exported so a test can
    // generate its per-field cases from the spec, not from a hand-written list.
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
