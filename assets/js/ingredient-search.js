// =============================================================================
// INGREDIENT SEARCH — pure matching and ranking for the food pickers. No DOM;
// filters.js owns the wiring (MANUAL §3).
//
// Loaded as a plain <script> before filters.js (attaching to window.HTF), and
// via require() in tests/js/ingredient-search.test.js.
// =============================================================================
(function (root) {
  'use strict';

  // Strip diacritics and turn hyphens into spaces, for matching only: `comte`
  // finds comté and "five spice" finds five-spice. Display is never folded.
  function fold(str) {
    return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/-/g, ' ');
  }

  // Splits on hyphens as well as whitespace, to agree with fold().
  function getWords(str) {
    return str.toLowerCase().trim().split(/[\s-]+/).filter(Boolean);
  }

  // The three-band rule:
  //   1  the entry starts with the query        "lime juice" for "li"
  //   2  some word in the entry starts with it  "apricot liqueur" for "li"
  //   3  the entry is in the list for some other reason
  // Band 3 is never promoted into band 1, or "chocolate chips" ranks beside
  // "chicken breast" for "chi".
  // A candidate is any object carrying `isPrefixMatch` and `hasWordMatch`.
  function bandOf(candidate) {
    if (candidate.isPrefixMatch) return 1;
    if (candidate.hasWordMatch) return 2;
    return 3;
  }

  // Lower band first, input order preserved inside a band. The stability is
  // load-bearing: "alphabetical within a band" holds only because the input
  // is already sorted. Shared with cocktail-search.js (#579), which passes
  // its own four-band function; the default is bandOf.
  function orderByBand(candidates, bandFor) {
    var band = bandFor || bandOf;
    var buckets = [];
    candidates.forEach(function (c) {
      var n = band(c);
      while (buckets.length < n) buckets.push([]);
      buckets[n - 1].push(c);
    });
    return buckets.reduce(function (all, b) { return all.concat(b); }, []);
  }

  // Builds a matcher bound to one vocabulary (the parsed contents of
  // _data/food/ingredient_words.yml, which holds the reasoning for each list).
  function create(vocabulary) {
    var FAMILY_BUTTON_MIN_CHARS = vocabulary.search.family_button_min_chars;
    var singularMap = vocabulary.singulars || {};
    var synonymMap = vocabulary.synonyms || {};

    function normaliseIngredientWord(word) {
      return singularMap[word] || word;
    }

    // Synonym keys and words, folded once so a folded query still finds them.
    var foldedSynonymMap = (function () {
      var out = {};
      Object.keys(synonymMap).forEach(function (key) {
        out[fold(key.toLowerCase())] = synonymMap[key].map(function (w) {
          return fold(String(w).toLowerCase());
        });
      });
      return out;
    })();

    function getSynonymWords(query) {
      return foldedSynonymMap[query] || null;
    }

    // Does any entry in `list` match the picked ingredient key `key`? A
    // curated synonym family matches on containment of any of its words
    // (`cheese` has to reach comté); anything else matches when every word of
    // the key prefixes some word of the entry. Prefix, not containment, or
    // `salt` matches unsalted butter (#619); a family only containment reaches
    // (`nuts` -> walnuts) is declared in the vocabulary's `synonyms`. Include
    // and the exclude "(all)" umbrella both ask this one function.
    function entriesMatchKey(list, key) {
      var synonyms = getSynonymWords(key);
      if (synonyms) {
        return (list || []).some(function (entry) {
          var lower = String(entry).toLowerCase();
          return synonyms.some(function (syn) { return lower.indexOf(syn) !== -1; });
        });
      }
      var keyWords = getWords(key).map(normaliseIngredientWord);
      return (list || []).some(function (entry) {
        var entryWords = getWords(entry).map(normaliseIngredientWord);
        return keyWords.every(function (kw) {
          // Prefix, not containment (#619).
          return entryWords.some(function (ew) { return ew.indexOf(kw) === 0; });
        });
      });
    }

    // Preparation-state words ("chopped", "crispy"), stripped so "chopped
    // pistachios" and "pistachios" are one ingredient.
    var modifierSet = new Set((vocabulary.modifiers || []).map(function (w) {
      return fold(String(w).toLowerCase());
    }));

    // Colour/variety words that head 2+ entries but aren't a real family —
    // "red (all)" would lump together red wine and red onion.
    var neverFamilySet = new Set((vocabulary.never_family || []).map(function (w) {
      return fold(String(w).toLowerCase());
    }));

    // Specific entries excluded from counting towards their own head word's
    // family — "cherry tomatoes" isn't a cherry.
    var familyExceptionSet = new Set((vocabulary.family_exceptions || []).map(function (w) {
      return fold(String(w).toLowerCase());
    }));

    // Connector words ("and", "or", "of", "with") that never count as a
    // match target, wherever they fall in the phrase.
    var stopwordSet = new Set((vocabulary.stopwords || []).map(function (w) {
      return fold(String(w).toLowerCase());
    }));

    // Whole-phrase rewrites, in three forms: a name renames ("five-spice
    // powder" -> "five-spice"), a list splits ("beef or venison stock" ->
    // beef stock + venison stock), an empty list drops. Keys are folded;
    // values are normalised to a list.
    var aliasMap = {};
    Object.keys(vocabulary.aliases || {}).forEach(function (key) {
      var becomes = vocabulary.aliases[key];
      aliasMap[fold(key.toLowerCase())] =
        Array.isArray(becomes) ? becomes.map(String) : [String(becomes)];
    });

    // Always returns an array; an unaliased entry is itself, alone.
    // hasOwnProperty, not a truthiness test: an empty list is a real answer
    // (drop the entry), not a missing one.
    function applyAlias(ing) {
      var key = fold(ing.toLowerCase());
      return Object.prototype.hasOwnProperty.call(aliasMap, key) ? aliasMap[key] : [ing];
    }

    // Button label overrides, keyed by the match key they relabel. Separate
    // from `aliases` because matching still runs against the real match key.
    var displayNameMap = {};
    Object.keys(vocabulary.display_names || {}).forEach(function (key) {
      displayNameMap[fold(key.toLowerCase())] = vocabulary.display_names[key];
    });

    function getDisplayLabel(ing) {
      return displayNameMap[fold(ing.toLowerCase())] || ing;
    }

    // A modifier that is half of a coordinated pair is not stripped (#366):
    // taking "fresh" off "fresh or frozen cranberries" leaves the fragment
    // "or frozen cranberries". The phrase stays whole; splitting it is a job
    // for `aliases`.
    var COORDINATOR = /^(?:or|and)$/i;

    function stripModifiers(ing) {
      var words = ing.split(/\s+/);
      while (words.length > 1
             && modifierSet.has(fold(words[0].toLowerCase()))
             && !COORDINATOR.test(words[1])) {
        words.shift();
      }
      return words.join(' ');
    }

    // --- what the derived vocabulary needs extra (#273) -----------------------
    // The exclude picker's vocabulary comes from `item:` free text, so it
    // carries quantities ("1 tsp salt"), portion phrasings ("a good pinch of
    // salt") and method notes ("herbs to taste"). Three strips below; each is
    // a no-op on a clean entry, which lets buildMasterList be the single door
    // for both vocabularies.

    // A quantity token is digits, vulgar fractions and the characters that
    // join them, and nothing else: "1", "¼–½", "4–5.5" qualify; "3-bone" and
    // "70%" do not, because a letter or a percent sign is part of the name.
    var QUANTITY_TOKEN = /^[0-9¼-¾⅐-⅞./–—-]+$/;
    var HAS_A_NUMBER = /[0-9¼-¾⅐-⅞]/;

    var quantityUnitSet = new Set((vocabulary.quantity_units || []).map(function (w) {
      return String(w).toLowerCase();
    }));

    function stripLeadingQuantity(ing) {
      var words = ing.split(/\s+/);
      var stripped = true;
      while (stripped) {
        stripped = false;
        if (words.length > 1 && QUANTITY_TOKEN.test(words[0]) && HAS_A_NUMBER.test(words[0])) {
          var rest = words.slice(1);
          // Every consecutive unit word after the number ("3 fl oz"), but
          // never the last word: an entry always keeps something.
          while (rest.length > 1 && quantityUnitSet.has(rest[0].toLowerCase())) {
            rest.shift();
          }
          words = rest;
          stripped = true;
        }
      }
      return words.join(' ');
    }

    // Longest first, so "a large handful of" wins over any shorter phrase it
    // happens to contain rather than leaving half of itself behind.
    function byLengthDescending(a, b) { return b.length - a.length; }

    var measurePhrases = (vocabulary.measure_phrases || []).map(function (p) {
      return String(p).toLowerCase();
    }).sort(byLengthDescending);

    function stripMeasurePhrase(ing) {
      var lower = ing.toLowerCase();
      for (var i = 0; i < measurePhrases.length; i++) {
        var prefix = measurePhrases[i] + ' ';
        if (lower.indexOf(prefix) === 0 && ing.length > prefix.length) {
          return ing.slice(prefix.length).trim();
        }
      }
      return ing;
    }

    var trailingPhrases = (vocabulary.trailing_phrases || []).map(function (p) {
      return String(p).toLowerCase();
    }).sort(byLengthDescending);

    function stripTrailingPhrase(ing) {
      var lower = ing.toLowerCase();
      for (var i = 0; i < trailingPhrases.length; i++) {
        var suffix = ' ' + trailingPhrases[i];
        if (lower.length > suffix.length &&
            lower.lastIndexOf(suffix) === lower.length - suffix.length) {
          return ing.slice(0, ing.length - suffix.length).trim();
        }
      }
      return ing;
    }

    // The one normalisation pipeline: trailing phrase first, then quantity,
    // measure phrase, modifier.
    function normaliseEntry(ing) {
      return stripModifiers(stripMeasurePhrase(stripLeadingQuantity(stripTrailingPhrase(ing))));
    }

    function getMatchWords(ing) {
      return getWords(ing).filter(function (word) {
        return !stopwordSet.has(fold(word));
      });
    }

    // An entry's words as search() compares them: stopwords out, each word to
    // its singular, folded. Joined, they are the key search() deduplicates on,
    // which is what makes "cherries" and "cherry" one button.
    function matchKeyWords(ing) {
      return getMatchWords(ing).map(normaliseIngredientWord).map(fold);
    }

    // Which picker entry a string is (#1289). Exported for page-search.js,
    // whose dropdown hands a word to this picker through `?ing=` and so must
    // treat "sweet potato" and "sweet potatoes" as one entry.
    function entryKey(ing) {
      return matchKeyWords(ing).join(' ');
    }

    // Raw ingredient strings -> the deduplicated, normalised master list,
    // sorted case-insensitively. Both vocabularies come through here:
    // main_ingredients for the include picker, the derived `item:` index for
    // the exclude picker. Aliases apply after the strips, because alias keys
    // are the post-strip forms; one raw string can yield several entries or
    // none.
    function buildMasterList(rawIngredientStrings) {
      var set = new Set();
      rawIngredientStrings.forEach(function (ing) {
        applyAlias(normaliseEntry(ing)).forEach(function (entry) {
          set.add(entry);
        });
      });
      return Array.from(set).sort(function (a, b) {
        return a.toLowerCase().localeCompare(b.toLowerCase());
      });
    }

    // Returns { familyButtons: ["cheese"], results: [{ing, label,
    // isPrefixMatch, hasWordMatch}, ...] }. familyButtons are word stems that
    // earn a "word (all)" button; results are deduplicated and in render order.
    function search(rawQuery, masterIngredientsList) {
      var query = fold(rawQuery.trim().toLowerCase());
      if (!query) return { familyButtons: [], results: [] };

      var enableFamilyButtons = query.length >= FAMILY_BUTTON_MIN_CHARS;
      var queryWords = query.split(/\s+/).filter(Boolean);
      var multiWord = queryWords.length > 1;

      // The distinct entries sharing each first word. A word heading 2+
      // entries is a family and earns an (all) button — "chicken" heads
      // chicken breast/leg/thigh. Only the first word counts: "lamb chops"
      // and "pork chops" are not a "chop" family.
      var wordToEntries = {};
      masterIngredientsList.forEach(function (ing) {
        if (familyExceptionSet.has(fold(ing.toLowerCase()))) return;
        var normWords = matchKeyWords(ing);
        var headWord = normWords[0];
        if (!wordToEntries[headWord]) wordToEntries[headWord] = new Set();
        wordToEntries[headWord].add(normWords.join(' '));
      });

      // Whether the query prefixes any head word at all — see the substring
      // fallback below.
      var anyHeadwordPrefixed = Object.keys(wordToEntries).some(function (hw) {
        return hw.indexOf(query) === 0;
      });

      var renderedKeys = new Set();

      // The query is folded, so the entry's words are too, and the dedupe key
      // is the single-word path's: "creme fraiche" finds crème fraîche once.
      if (multiWord) {
        var multiMatches = [];
        masterIngredientsList.forEach(function (ing) {
          var ingWords = getMatchWords(ing).map(fold);
          var ingKey = entryKey(ing);
          var allMatch = queryWords.every(function (qw) {
            return ingWords.some(function (iw) { return iw.indexOf(qw) !== -1; });
          });
          if (!allMatch) return;
          var isPrefixMatch = fold(ing.toLowerCase()).indexOf(query) === 0;
          // Every query word starts some word of the entry, in any order.
          var hasWordMatch = queryWords.every(function (qw) {
            return ingWords.some(function (iw) { return iw.indexOf(qw) === 0; });
          });
          multiMatches.push({ ing: ing, ingKey: ingKey, isPrefixMatch: isPrefixMatch, hasWordMatch: hasWordMatch });
        });
        var multiResults = [];
        orderByBand(multiMatches).forEach(function (c) {
          if (!renderedKeys.has(c.ingKey)) {
            renderedKeys.add(c.ingKey);
            multiResults.push({ ing: c.ing, label: getDisplayLabel(c.ing), isPrefixMatch: c.isPrefixMatch, hasWordMatch: c.hasWordMatch });
          }
        });
        return { familyButtons: [], results: multiResults };
      }

      // --- Single-word query ---
      var candidates = [];
      var familyWords = new Set();
      var engagedFamilyWords = new Set();

      // A curated family (the vocabulary's `synonyms`) is engaged once the
      // query prefixes its name — "chees" for "cheese". Its members are then
      // listed inline as well as behind the (all) button.
      if (enableFamilyButtons) {
        Object.keys(foldedSynonymMap).forEach(function (key) {
          if (key.indexOf(query) === 0) {
            familyWords.add(key);
            foldedSynonymMap[key].forEach(function (w) { engagedFamilyWords.add(w); });
          }
        });
      }

      masterIngredientsList.forEach(function (ing) {
        var ingWords = getMatchWords(ing);
        var normWords = matchKeyWords(ing);
        var normKey = normWords.join(' ');

        // The normalised form as well as the raw text: an irregular plural
        // ("cherries") never contains its singular ("cherry") as a substring.
        var matchedAnyWord = ingWords.some(function (word, idx) {
          return fold(word).indexOf(query) !== -1 || normWords[idx].indexOf(query) !== -1;
        });

        // Containment against the whole entry, the same rule entriesMatchKey
        // applies to a synonym family, so "cream cheese" is a cheese.
        var foldedIng = fold(ing.toLowerCase());
        var isFamilyMember = false;
        engagedFamilyWords.forEach(function (syn) {
          if (foldedIng.indexOf(syn) !== -1) isFamilyMember = true;
        });

        if (!matchedAnyWord && !isFamilyMember) return;

        // Start of the string, not of any word. Also checks the normalised
        // first word, so "cherries" is a prefix match for "cherry".
        var isPrefixMatch = foldedIng.indexOf(query) === 0 || normWords[0].indexOf(query) === 0;

        // Does any word start with the query? Marks a real textual hit
        // ("cream cheese" for "chees") apart from a family-only one
        // ("cheddar").
        var hasWordMatch = ingWords.some(function (word, idx) {
          return fold(word).indexOf(query) === 0 || normWords[idx].indexOf(query) === 0;
        });

        candidates.push({ ing: ing, normKey: normKey, isPrefixMatch: isPrefixMatch, hasWordMatch: hasWordMatch });

        // Structural family: a first word heading 2+ distinct entries, minus
        // never_family. The query must prefix the head word ("chi" sits
        // inside "pistachios" by coincidence). The substring fallback ("hic"
        // -> "chicken (all)", #56) applies only when the query prefixes no
        // head word anywhere, so a real prefix always wins.
        var headIsPrefixMatch = fold(ingWords[0]).indexOf(query) === 0 || normWords[0].indexOf(query) === 0;
        var headIsSubstringFallback = !headIsPrefixMatch && !anyHeadwordPrefixed && normWords[0].indexOf(query) !== -1;
        if (enableFamilyButtons && (headIsPrefixMatch || headIsSubstringFallback)) {
          var headWord = normWords[0];
          if (!neverFamilySet.has(headWord)) {
            var entries = wordToEntries[headWord];
            if (entries && entries.size > 1) {
              familyWords.add(headWord);
            }
          }
        }
      });

      // Here band 3 is a family-only member ("cheddar" for "chees").
      var results = [];
      orderByBand(candidates).forEach(function (c) {
        if (!renderedKeys.has(c.normKey)) {
          renderedKeys.add(c.normKey);
          results.push({ ing: c.ing, label: getDisplayLabel(c.ing), isPrefixMatch: c.isPrefixMatch, hasWordMatch: c.hasWordMatch });
        }
      });

      return { familyButtons: Array.from(familyWords), results: results };
    }

    return {
      normaliseIngredientWord: normaliseIngredientWord,
      getSynonymWords: getSynonymWords,
      entriesMatchKey: entriesMatchKey,
      buildMasterList: buildMasterList,
      entryKey: entryKey,
      search: search
    };
  }

  var api = {
    fold: fold,
    getWords: getWords,
    bandOf: bandOf,
    orderByBand: orderByBand,
    create: create
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  } else {
    root.HTF = root.HTF || {};
    root.HTF.ingredientSearch = api;
  }
})(typeof window !== 'undefined' ? window : this);
