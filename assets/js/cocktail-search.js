// =============================================================================
// COCKTAIL SEARCH — pure pool/ranking/matching logic for the drinks index.
// No DOM. GitHub issue #579; what it fixes is #549.
//
// Extracted out of cocktail-index.js for the reason back-link.js already makes
// the case for (HANDOVER §3): every rule below was hand-rolled inside 428 lines
// of DOM wiring, where the only way to ask it a question was to open a browser
// and type. "Does a chip named `gin` exclude a drink whose only gin-shaped
// ingredient is ginger syrup?" is a question a pure function can be asked.
// It could not be, and the answer was yes, for twelve drinks.
//
// cocktail-index.js still owns everything DOM-shaped: reading the attributes,
// building chips, toggling [hidden], reordering the list.
//
// Loaded two ways from the one file, no bundler:
//   - In the browser, as a plain <script> after ingredient-search.js and before
//     cocktail-index.js, attaching to window.HTF.
//   - In Node, via require(), for tests (tests/js/cocktail-search.test.js).
//
// -----------------------------------------------------------------------------
// WHAT IS SHARED WITH FOOD, AND WHAT IS DELIBERATELY NOT
// -----------------------------------------------------------------------------
//
// SHARED, from HTF.ingredientSearch: `fold` and `getWords` (text normalisation,
// which has no site in it at all) and `orderByBand` (the three-band ordering
// rule). Nothing else.
//
// NOT SHARED, on purpose: IS.create()'s whole matcher. It carries modifier
// stripping, quantity and measure-phrase stripping, singulars and aliases --
// all of which exist because food's exclude picker reads raw `item:` prose
// written for a cook ("a knob of butter", "about 200 g raw king prawns").
// Since #558 this pool is `generic + card name + suggestion`, a curated
// vocabulary, so every one of those strips would be a no-op dressed up as
// reuse. Measured 2026-08-29: zero singular/plural pairs in the 240 terms.
//
// AND NOT SHARED, because the data says so: food's family DERIVATION. An (all)
// button forms on the food site where entries share a head word after
// normalisation. _data/cocktails/ingredients.yml states the reason it cannot
// work here, and it is right -- "aged Demerara rum" and "moderately aged
// Jamaican rum" have nothing textually in common. So the family is DECLARED, in
// `family_of`, and what IS shared with food is the CONSUMPTION of a declared
// family, which is exactly what `synonyms` in ingredient_words.yml already is.
//
// -----------------------------------------------------------------------------
// FUZZY TO FIND, FUZZY TO INCLUDE, EXACT TO EXCLUDE
// -----------------------------------------------------------------------------
//
// Food's rule, adopted here, and the asymmetry is not an inconsistency -- it is
// the cost of being wrong in each direction. Over-including shows you a drink
// you may not have wanted: visible, and the card says why it is there.
// Over-EXCLUDING hides a drink you would have had: invisible, and you never
// learn it existed.
//
// This replaces a single raw substring test used for BOTH directions against
// the whole concatenated attribute -- the thing filter-state.js's excludesRow()
// exists to forbid ("excluding peas would silently lose the peanut butter
// cookies and the pearl barley casserole"). Measured over 114 drinks, 26 of the
// 240 pool terms over-matched:
//
//     gin          hid 12 drinks whose only gin-shaped thing was GINGER
//     water        hid 13 whose only water was HONEY water
//     apple juice  matched 15 drinks that have PINEapple juice
//
// The breadth that loses is smaller than it looks, and that is why no
// structural head-word umbrella had to be invented to replace it: the pool
// already offers the entry a person would actually pick. `lime juice` matches
// 56 of the 57 drinks `lime`-as-substring caught; `sugar syrup` 35 of 40. Where
// an umbrella IS genuinely needed it is a spirit -- no pool entry is literally
// "rum", and the declared family covers 63 drinks -- which is the case
// `family_of` was written for.
// =============================================================================
(function (root) {
  'use strict';

  var IS = (typeof module !== 'undefined' && module.exports)
    ? require('./ingredient-search.js')
    : root.HTF.ingredientSearch;

  var fold = IS.fold;
  var getWords = IS.getWords;

  // The same spelling filter-state.js uses, and for the same reason: the suffix
  // is the umbrella's name on its own face, so it has to read identically
  // wherever it is written down. Not imported from there, because this module
  // has no other business with that one and a dependency for one string is a
  // dependency to maintain.
  var FAMILY_SUFFIX = ' (all)';

  /* The build-time attribute -> its entries. `|`-separated and `|`-terminated,
     the same self-delimiting shape food/index.html uses for
     data-all-ingredients, chosen there because a comma is the commonest
     character in the values and this one appears in none of them.

     Splitting ONCE, here, is also what makes the seam unreachable: the old
     substring test ran against the joined string, where a query could match
     across the boundary between two ingredients and nothing on the card
     corresponded to what had matched. */
  function splitEntries(attrValue) {
    return String(attrValue == null ? '' : attrValue)
      .split('|')
      .map(function (s) { return s.trim(); })
      .filter(Boolean);
  }

  /* Folding that CANNOT change a string's length, so an offset into the folded
     form is an offset into the original. fold() is length-preserving for every
     character in this collection (a precomposed accent decomposes to two and
     loses one; a hyphen becomes a space) but that is a fact about today's data
     rather than a promise, and nameHighlight() below hands its answer to
     `slice`. Anything that would change length simply does not fold: the worst
     case is a character that fails to match, never a highlight in the wrong
     place. */
  function foldByCharacter(str) {
    var out = '';
    for (var i = 0; i < str.length; i++) {
      var ch = str.charAt(i).toLowerCase();
      var folded = fold(ch);
      out += (folded.length === 1 ? folded : ch);
    }
    return out;
  }

  function normalise(str) {
    return fold(String(str == null ? '' : str).toLowerCase()).trim();
  }

  function isFamilyValue(value) {
    return typeof value === 'string' &&
      value.length > FAMILY_SUFFIX.length &&
      value.slice(-FAMILY_SUFFIX.length) === FAMILY_SUFFIX;
  }

  function familyKey(value) {
    return normalise(value.slice(0, -FAMILY_SUFFIX.length));
  }

  function create(vocabulary) {
    var voc = vocabulary || {};
    var cfg = voc.search || {};

    /* Three numbers, and none of them is written down in this file. They live
       in _data/cocktails/ingredients.yml beside the vocabulary they govern,
       the same rule food's `family_button_min_chars` follows and
       test_the_cocktail_search_config_is_not_hardcoded enforces. #549 point 4
       is the minimum query length, and it is a DATA question -- how much
       typing before a pool of candidates is more help than noise -- not a
       question about this algorithm. */
    var MIN_QUERY_CHARS = cfg.min_query_chars;
    var FAMILY_BUTTON_MIN_CHARS = cfg.family_button_min_chars;
    var POOL_CAP = cfg.pool_cap;

    var families = (voc.families || []).map(String);
    var familyOfGeneric = voc.family_of || {};
    var cardNames = voc.card_names || {};

    /* One map, entry -> the families it belongs to, built once. A CARD NAME
       resolves through the generic it abbreviates, which matters because the
       pool contains both: a drink whose rum shows as "Demerara rum" on the card
       must still answer to "rum (all)".

       A LIST, not a single value, because a card name may legitimately stand
       for two generics -- #501's declared collapse, where both Jamaicans read
       "Jamaican rum" on the strength of the funk being the shared trait. They
       happen to share a family too; nothing guarantees the next collapse will,
       and a silently-picked first answer is how that would be discovered. */
    var familyIndex = Object.create(null);

    function addFamily(entry, family) {
      var key = normalise(entry);
      if (!key || !family) return;
      if (!familyIndex[key]) familyIndex[key] = [];
      if (familyIndex[key].indexOf(family) === -1) familyIndex[key].push(family);
    }

    Object.keys(familyOfGeneric).forEach(function (generic) {
      var family = familyOfGeneric[generic];
      addFamily(generic, family);
      if (Object.prototype.hasOwnProperty.call(cardNames, generic)) {
        addFamily(cardNames[generic], family);
      }
    });

    function familiesOf(entry) {
      return (familyIndex[normalise(entry)] || []).slice();
    }

    function entryHasFamily(entries, family) {
      return (entries || []).some(function (entry) {
        return familiesOf(entry).indexOf(family) !== -1;
      });
    }

    // ------------------------------------------------------------------------
    // THE POOL
    // ------------------------------------------------------------------------

    /* Every distinct entry across the collection, gathered from the attributes
       rather than from a second copy of the vocabulary -- the same reasoning
       filters.js applies to `masterIngredientsList`. The template has already
       downcased, so a plain case-insensitive sort is all this needs; the
       comparison is spelled out anyway, because "the values happen to arrive
       lowercase" is a fact about the template and not about this function. */
    function buildPool(attrValues) {
      var seen = Object.create(null);
      (attrValues || []).forEach(function (value) {
        splitEntries(value).forEach(function (entry) { seen[entry] = true; });
      });
      return Object.keys(seen).sort(function (a, b) {
        return a.toLowerCase().localeCompare(b.toLowerCase());
      });
    }

    // ------------------------------------------------------------------------
    // THE SEARCH
    // ------------------------------------------------------------------------

    /* Returns { familyButtons, results, hidden }.

       `hidden` is a COUNT, not a silence. A pool that quietly stops at eight
       looks like a complete answer and the one you wanted may be the ninth --
       the same rule the rest of this repo holds itself to. Family buttons are
       not counted against the cap: they are a different offer, and capping an
       umbrella to make room for the things it stands over is backwards. */
    function search(rawQuery, pool, chosen) {
      var typed = String(rawQuery == null ? '' : rawQuery).trim();
      var empty = { familyButtons: [], results: [], hidden: 0 };
      if (typed.length < MIN_QUERY_CHARS) return empty;

      var query = normalise(typed);
      if (!query) return empty;

      var taken = (chosen || []).map(normalise);
      var candidates = [];

      (pool || []).forEach(function (entry) {
        var folded = normalise(entry);
        if (folded.indexOf(query) === -1) return;
        if (taken.indexOf(folded) !== -1) return;
        var words = getWords(folded);
        candidates.push({
          entry: entry,
          isPrefixMatch: folded.indexOf(query) === 0,
          hasWordMatch: words.some(function (w) { return w.indexOf(query) === 0; })
        });
      });

      // Shared with food rather than re-derived — see orderByBand's own note in
      // assets/js/ingredient-search.js for what is shared and what is not.
      var ordered = IS.orderByBand(candidates);

      /* A family earns a button when the query is heading towards its NAME and
         it has at least one member in the pool. The membership half is not
         decoration: `families` is a spec, and offering "aquavit (all)" on a
         collection holding no aquavit is an umbrella over nothing. Same shape
         as the index's own rule that a mood with no drinks renders no button. */
      var familyButtons = [];
      if (typed.length >= FAMILY_BUTTON_MIN_CHARS) {
        families.forEach(function (family) {
          if (normalise(family).indexOf(query) !== 0) return;
          var present = (pool || []).some(function (entry) {
            return familiesOf(entry).indexOf(family) !== -1;
          });
          if (present) familyButtons.push(family);
        });
      }

      return {
        familyButtons: familyButtons,
        results: ordered.slice(0, POOL_CAP),
        hidden: Math.max(0, ordered.length - POOL_CAP)
      };
    }

    // ------------------------------------------------------------------------
    // THE TWO MATCHING RULES
    // ------------------------------------------------------------------------

    /* EXACT, or a declared family. See this file's header for why exclusion is
       the strict direction: its errors are the invisible ones.

       A whole-entry comparison, never a substring, and never against the joined
       attribute -- which is what let "gin" reach "ginger syrup" and what let a
       query match across the seam between two ingredients. */
    function matchesExclude(entries, chip) {
      if (!chip) return false;
      if (isFamilyValue(chip)) return entryHasFamily(entries, chipFamily(chip));
      var wanted = normalise(chip);
      return (entries || []).some(function (entry) { return normalise(entry) === wanted; });
    }

    /* Every word of the chip must PREFIX some word of the entry. Prefix rather
       than "contained in", which is the looser rule filters.js uses on the food
       side: contained-in is what makes "apple juice" match PINEapple juice, and
       there are fifteen of those. Prefix keeps the case this looseness is for
       -- a "lime" chip finding the lime juice, 56 drinks -- and drops the case
       nobody wants.

       Still deliberately loose in one respect: a "gin" chip does reach ginger
       syrup here. That is the cheap direction (you are shown a drink and the
       card says why), and "gin (all)" is the precise answer sitting right
       beside it in the pool. */
    function matchesInclude(entries, chip) {
      if (!chip) return false;
      if (isFamilyValue(chip)) return entryHasFamily(entries, chipFamily(chip));
      var chipWords = getWords(normalise(chip));
      if (!chipWords.length) return false;
      return (entries || []).some(function (entry) {
        var entryWords = getWords(normalise(entry));
        return chipWords.every(function (cw) {
          return entryWords.some(function (ew) { return ew.indexOf(cw) === 0; });
        });
      });
    }

    function chipFamily(chip) {
      var wanted = familyKey(chip);
      var hit = null;
      families.forEach(function (family) {
        if (normalise(family) === wanted) hit = family;
      });
      return hit;
    }

    /* Does this ONE ingredient answer any of the chosen include chips? The card
       lights a matched ingredient with it, so it must use the same rule the
       filter used -- a card that survived for a reason it cannot show is the
       one thing HANDOVER §9.13 says a card must never be. */
    function entryIsHit(entries, chips) {
      return (chips || []).some(function (chip) {
        return matchesInclude(entries, chip);
      });
    }

    // ------------------------------------------------------------------------
    // I KNOW WHAT I WANT
    // ------------------------------------------------------------------------

    /* SUBSTRING, unlike the ingredient fields, and that is not an oversight:
       those match a vocabulary where "rum" starting a word is the meaningful
       test, whereas a drink name is something you already hold and are part-way
       through typing. "negr" should find the Negroni.

       What it was missing is folding. Three drink names carry an accent --
       Jägerita, Vieux Carré, Champs Elysées -- and not one of them was
       reachable from an ASCII keyboard. */
    function matchesName(title, query) {
      var wanted = foldByCharacter(String(query == null ? '' : query).trim());
      if (!wanted) return true;
      return foldByCharacter(String(title == null ? '' : title)).indexOf(wanted) !== -1;
    }

    /* Where the match sits in the ORIGINAL title, for the highlight (#564).
       Offsets into the original rather than the folded form, so the marked-up
       title keeps its accents -- the same rule filters.js's
       updateTitleHighlights() follows: fold to compare, never to display. */
    function nameHighlight(title, query) {
      var wanted = foldByCharacter(String(query == null ? '' : query).trim());
      if (!wanted) return null;
      var at = foldByCharacter(String(title == null ? '' : title)).indexOf(wanted);
      if (at === -1) return null;
      return { start: at, end: at + wanted.length };
    }

    return {
      buildPool: buildPool,
      familiesOf: familiesOf,
      search: search,
      matchesInclude: matchesInclude,
      matchesExclude: matchesExclude,
      entryIsHit: entryIsHit,
      matchesName: matchesName,
      nameHighlight: nameHighlight
    };
  }

  var api = {
    FAMILY_SUFFIX: FAMILY_SUFFIX,
    splitEntries: splitEntries,
    isFamilyValue: isFamilyValue,
    create: create
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  } else {
    root.HTF = root.HTF || {};
    root.HTF.cocktailSearch = api;
  }
})(typeof window !== 'undefined' ? window : this);
