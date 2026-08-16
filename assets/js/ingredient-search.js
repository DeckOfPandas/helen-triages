// =============================================================================
// INGREDIENT SEARCH — pure matching/ranking logic, no DOM.
//
// Extracted out of filters.js so it can be tested directly with Node's
// built-in test runner (see tests/js/ingredient-search.test.js) instead of
// only being verified by hand against a live page. filters.js still owns
// everything DOM-shaped: reading ingredients off the page, click handlers,
// turning a search() result into <button> elements.
//
// Loaded two ways from the one file, no bundler:
//   - In the browser, as a plain <script> before filters.js, attaching to
//     window.HTF (the same namespace assets.js already establishes).
//   - In Node, via require(), for tests.
// =============================================================================
(function (root) {
  'use strict';

  // Strip diacritics and normalise hyphens to spaces, for MATCHING ONLY.
  // Nobody types "comté" into a search box, so folding both sides lets
  // `comte`, `comté` and `mte` all find the same ingredient. Same idea for
  // hyphens -- "five-spice" is one compound ingredient name, but a query
  // typed as "five spice" (a space, the natural way to type two words)
  // should match it exactly as if the hyphen were a space. Display is
  // never folded -- buttons render the ingredient's real text, hyphens
  // and accents intact.
  function fold(str) {
    return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/-/g, ' ');
  }

  // Splits on hyphens as well as whitespace so "five-spice" tokenises as
  // ["five", "spice"] for matching, the same as a query typed "five spice"
  // -- see fold() above for why hyphens are treated as word boundaries.
  function getWords(str) {
    return str.toLowerCase().trim().split(/[\s-]+/).filter(Boolean);
  }

  // Builds a matcher bound to one vocabulary (the parsed contents of
  // _data/ingredient_words.yml). Everything below is a closure over the
  // word lists so they're only ever parsed once.
  function create(vocabulary) {
    var FAMILY_BUTTON_MIN_CHARS = vocabulary.search.family_button_min_chars;
    var singularMap = vocabulary.singulars || {};
    var synonymMap = vocabulary.synonyms || {};

    function normaliseIngredientWord(word) {
      return singularMap[word] || word;
    }

    // Synonym keys are folded once at startup so a folded query still finds
    // them. When a query exactly matches a key, any ingredient containing
    // any of the listed words is treated as a candidate, and the key earns
    // a forced (all) button.
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

    // Preparation-state words ("chopped", "crispy") describe what was done
    // to an ingredient, not what it is — recipe files keep them, but the
    // search UI strips them so "chopped pistachios" and "pistachios" are
    // treated as the one ingredient. See _data/ingredient_words.yml for the
    // full reasoning per word.
    var modifierSet = new Set((vocabulary.modifiers || []).map(function (w) {
      return fold(String(w).toLowerCase());
    }));

    // Colour/variety words that head 2+ entries but aren't a real family —
    // "red (all)" would lump together red wine, red onion and red Thai
    // curry paste. See _data/ingredient_words.yml.
    var neverFamilySet = new Set((vocabulary.never_family || []).map(function (w) {
      return fold(String(w).toLowerCase());
    }));

    // Specific entries excluded from counting towards their own head word's
    // family — "cherry tomatoes" isn't a cherry. See _data/ingredient_words.yml.
    var familyExceptionSet = new Set((vocabulary.family_exceptions || []).map(function (w) {
      return fold(String(w).toLowerCase());
    }));

    // Connector words ("and", "or", "of", "with") that never count as a
    // match target, wherever they fall in the phrase.
    var stopwordSet = new Set((vocabulary.stopwords || []).map(function (w) {
      return fold(String(w).toLowerCase());
    }));

    // Whole-phrase rewrites, in three forms — a name renames ("five-spice
    // powder" -> "five-spice"), a list SPLITS ("beef or venison stock" ->
    // beef stock + venison stock), an empty list DROPS. Folded keys, so
    // "Five-Spice Powder" still matches. Normalised to a list here so there
    // is one shape downstream and the YAML can keep writing a bare name where
    // a bare name reads better. See _data/food/ingredient_words.yml for what
    // is in it and, more importantly, for why it is a named list and not a
    // rule.
    var aliasMap = {};
    Object.keys(vocabulary.aliases || {}).forEach(function (key) {
      var becomes = vocabulary.aliases[key];
      aliasMap[fold(key.toLowerCase())] =
        Array.isArray(becomes) ? becomes.map(String) : [String(becomes)];
    });

    // Returns an ARRAY, always — an unaliased entry is itself, alone, which
    // is what keeps this a no-op on every entry the list doesn't name. Both
    // vocabularies are handed to it, so a phrase that appears in
    // main_ingredients as well as in `item:` text is rewritten in the include
    // picker too; the YAML names the four that currently do.
    // hasOwnProperty rather than a truthiness test: an empty list is a real
    // answer here (drop the entry), not a missing one.
    function applyAlias(ing) {
      var key = fold(ing.toLowerCase());
      return Object.prototype.hasOwnProperty.call(aliasMap, key) ? aliasMap[key] : [ing];
    }

    // Button label overrides, keyed by the match key they relabel — kept
    // separate from `aliases` because matching still has to run against the
    // real match key, not the pretty name. See _data/ingredient_words.yml.
    var displayNameMap = {};
    Object.keys(vocabulary.display_names || {}).forEach(function (key) {
      displayNameMap[fold(key.toLowerCase())] = vocabulary.display_names[key];
    });

    function getDisplayLabel(ing) {
      return displayNameMap[fold(ing.toLowerCase())] || ing;
    }

    function stripModifiers(ing) {
      var words = ing.split(/\s+/);
      while (words.length > 1 && modifierSet.has(fold(words[0].toLowerCase()))) {
        words.shift();
      }
      return words.join(' ');
    }

    // --- GitHub issue #273: what the DERIVED vocabulary needs extra ---------
    //
    // The exclude picker's vocabulary is derived from `item:` free text, not
    // from the curated main_ingredients, so it arrives carrying quantities
    // ("1 tsp salt"), portion phrasings ("a good pinch of salt") and method
    // notes ("herbs to taste"). All three name a real ingredient with
    // something in front of or behind it; none of them is a different
    // ingredient. Three strips below. The entries that name TWO ingredients
    // at once ("beef or venison stock") or none at all need naming rather
    // than stripping, and are handled by `aliases` above — same mechanism as
    // "five-spice powder", widened to take a list. See
    // _data/food/ingredient_words.yml for the word lists and for why each one
    // is literal phrases rather than a rule.
    //
    // Every one of these is a no-op on a clean entry, which is what lets
    // buildMasterList stay the single door both vocabularies go through.

    // A quantity token is digits and/or vulgar fractions and the characters
    // that join them, and NOTHING else: "1", "¼–½", "4–5.5" qualify;
    // "3-bone" and "70%" do not, because a letter or a percent sign means
    // the token is part of the name. Deliberately conservative — see the
    // `quantity_units` comment in the YAML.
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
          // Every consecutive unit word after the number, so "3 fl oz" goes
          // in one pass. Never the last word standing: an entry always keeps
          // something, even if the whole of it looked like a measurement.
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

    // The one normalisation pipeline. Order is trailing-first so a strip at
    // the end can never be confused by one at the front, then front-to-back:
    // quantity, measure phrase, modifier — widest context to narrowest.
    function normaliseEntry(ing) {
      return stripModifiers(stripMeasurePhrase(stripLeadingQuantity(stripTrailingPhrase(ing))));
    }

    function getMatchWords(ing) {
      return getWords(ing).filter(function (word) {
        return !stopwordSet.has(fold(word));
      });
    }

    // Takes the raw ingredient strings as they appear on the page (one per
    // recipe, splitting already done by the caller), returns the
    // deduplicated, normalised, alphabetically sorted master list. Both
    // vocabularies come through here — main_ingredients for the include
    // picker, the derived `item:` index for the exclude picker — and
    // normaliseEntry is a no-op on the curated first one.
    //
    // A plain .sort() is case-sensitive — every capital letter sorts before
    // every lowercase one, so "Chinese five spice" would jump ahead of
    // "chai", "cheddar" and "cheese" instead of sitting between "chestnuts"
    // and "chives" where it belongs.
    //
    // One raw string can yield more than one entry, or none — an alias may be
    // a split or a drop as well as a rename, so applyAlias returns a list and
    // this flattens it. It runs AFTER the strips because its keys are the
    // post-strip forms: "chopped almonds or whatever you prefer" is keyed as
    // "almonds or whatever you prefer".
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

    // The core of the search box. Returns:
    //   { familyButtons: ["cheese"], results: [{ing, isPrefixMatch, hasWordMatch}, ...] }
    // familyButtons are word stems that earn a "word (all)" button.
    // results are already deduplicated and in final render order.
    function search(rawQuery, masterIngredientsList) {
      var query = fold(rawQuery.trim().toLowerCase());
      if (!query) return { familyButtons: [], results: [] };

      var enableFamilyButtons = query.length >= FAMILY_BUTTON_MIN_CHARS;
      var queryWords = query.split(/\s+/).filter(Boolean);
      var multiWord = queryWords.length > 1;

      // Count how many DISTINCT ingredient entries share each FIRST word. A
      // word shared as the head of 2+ entries is a "family" and earns an
      // umbrella (all) button — "chicken" heads chicken breast/leg/thigh.
      // Only the first word counts, not every word in the phrase — "chop"
      // is the SECOND word of both "lamb chops" and "pork chops", cuts of
      // lamb and of pork respectively, not members of a "chop" family.
      // family_exceptions are skipped entirely: "cherry tomatoes" doesn't
      // count towards "cherry"'s family.
      var wordToEntries = {};
      masterIngredientsList.forEach(function (ing) {
        if (familyExceptionSet.has(fold(ing.toLowerCase()))) return;
        var normWords = getMatchWords(ing).map(normaliseIngredientWord).map(fold);
        var entryKey = normWords.join(' ');
        var headWord = normWords[0];
        if (!wordToEntries[headWord]) wordToEntries[headWord] = new Set();
        wordToEntries[headWord].add(entryKey);
      });

      // Whether the query is a genuine prefix of ANY head word at all,
      // anywhere in the corpus — used below to decide whether structural
      // family detection needs to fall back to a looser, substring check.
      var anyHeadwordPrefixed = Object.keys(wordToEntries).some(function (hw) {
        return hw.indexOf(query) === 0;
      });

      var renderedKeys = new Set();

      if (multiWord) {
        var multiMatches = [];
        masterIngredientsList.forEach(function (ing) {
          var ingWords = getMatchWords(ing);
          var ingKey = ingWords.map(normaliseIngredientWord).join(' ');
          var allMatch = queryWords.every(function (qw) {
            return ingWords.some(function (iw) { return iw.indexOf(qw) !== -1; });
          });
          if (!allMatch) return;
          // Same "start of the string" rule as the single-word path.
          var isPrefixMatch = fold(ing.toLowerCase()).indexOf(query) === 0;
          // Same "any word" rule as the single-word path's hasWordMatch,
          // applied per query word: does every word you typed start some
          // word in this entry (not necessarily the same one, not
          // necessarily in order)?
          var hasWordMatch = queryWords.every(function (qw) {
            return ingWords.some(function (iw) { return iw.indexOf(qw) === 0; });
          });
          multiMatches.push({ ing: ing, ingKey: ingKey, isPrefixMatch: isPrefixMatch, hasWordMatch: hasWordMatch });
        });
        // Three-band order, same as the single-word path below: entries
        // starting with the query outrank everything else; within the
        // rest, a genuine word match outranks one included only because a
        // query word happened to sit mid-word somewhere in the phrase.
        var multiPrefix = multiMatches.filter(function (c) { return c.isPrefixMatch; });
        var multiRestMatched = multiMatches.filter(function (c) { return !c.isPrefixMatch && c.hasWordMatch; });
        var multiRestOther = multiMatches.filter(function (c) { return !c.isPrefixMatch && !c.hasWordMatch; });
        var multiResults = [];
        multiPrefix.concat(multiRestMatched, multiRestOther).forEach(function (c) {
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

      // A curated family (declared in _data/ingredient_words.yml
      // `synonyms`) is ENGAGED once the query is a recognisable prefix of
      // its name — "chees" is clearly heading towards "cheese". A curated
      // family has a known, finite membership list, so its members are
      // surfaced inline rather than gated behind the (all) button, which
      // stays as a one-click way to select the whole family as a filter.
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
        var normWords = ingWords.map(normaliseIngredientWord).map(fold);
        var normKey = normWords.join(' ');

        // Checks each word's normalised form as well as its raw text. Most
        // plurals in `singulars` are a plain "+s"/"+es", so the singular is
        // already a literal prefix of the plural and matches without this.
        // A handful are genuinely irregular ("cherries"→cherry) — the
        // ending changes rather than just extending, so "cherries" never
        // contains "cherry" as a raw substring at all.
        var matchedAnyWord = ingWords.some(function (word, idx) {
          return fold(word).indexOf(query) !== -1 || normWords[idx].indexOf(query) !== -1;
        });

        // Membership check mirrors how the (all) button itself filters
        // recipes elsewhere — a substring match against the whole
        // ingredient text — so "cream cheese" and "goat's cheese" are
        // recognised as cheeses even though "cheese" is only one word.
        var foldedIng = fold(ing.toLowerCase());
        var isFamilyMember = false;
        engagedFamilyWords.forEach(function (syn) {
          if (foldedIng.indexOf(syn) !== -1) isFamilyMember = true;
        });

        if (!matchedAnyWord && !isFamilyMember) return;

        // "Start of the string", not "start of any word" — "chocolate
        // chips" matching on "chips" would put it ahead of things that
        // actually start with the query. Also checks the normalised first
        // word, so "cherries" ranks as a prefix match for "cherry".
        var isPrefixMatch = foldedIng.indexOf(query) === 0 || normWords[0].indexOf(query) === 0;

        // For the tint (a real word match, not just family membership):
        // does ANY word — not just the first — start with the query?
        // Deliberately looser than isPrefixMatch, which only ever looks at
        // the start of the whole string. "cream cheese" isn't ranked as a
        // top match for "chees" (it doesn't start with "chees"), but it's
        // still worth marking as a real textual hit rather than a
        // family-only one like "cheddar".
        var hasWordMatch = ingWords.some(function (word, idx) {
          return fold(word).indexOf(query) === 0 || normWords[idx].indexOf(query) === 0;
        });

        candidates.push({ ing: ing, normKey: normKey, isPrefixMatch: isPrefixMatch, hasWordMatch: hasWordMatch });

        // Check for STRUCTURAL family membership — a FIRST word with no
        // curated synonym list that nonetheless heads 2+ distinct entries.
        // Normally only as a PREFIX of the head word — not contained
        // anywhere in it: "chi" sits inside "pistachios" with no relation
        // to what was typed. Excludes never_family — "red", "white",
        // "mixed" genuinely head 2+ entries, but those entries are
        // unrelated foods that merely share a colour or variety word.
        //
        // GitHub issue #56: "hic" should still collapse chicken breast/
        // thigh/stock into "chicken (all)", even though "hic" isn't a
        // prefix of "chicken" — it's buried mid-word. Falls back to a
        // substring check on the head word, but ONLY when the query
        // doesn't prefix ANY head word anywhere in the corpus — a real
        // prefix relationship ("chi" → "chicken") always wins outright and
        // never gets diluted by this looser fallback.
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

      // Render order, three bands: entries starting with the query outrank
      // everything else, full stop. Within the rest, a genuine word match
      // ("cream cheese") outranks a family-only member ("cheddar") —
      // deliberately NOT promoted as far as the prefix tier, or "chocolate
      // chips" (word-matched for "chi" via "chips") would rank alongside
      // "chicken breast" again. Alphabetical within each band —
      // masterIngredientsList is already sorted, and filtering preserves
      // that order.
      var prefixMatches = candidates.filter(function (c) { return c.isPrefixMatch; });
      var restMatched = candidates.filter(function (c) { return !c.isPrefixMatch && c.hasWordMatch; });
      var restFamilyOnly = candidates.filter(function (c) { return !c.isPrefixMatch && !c.hasWordMatch; });

      var results = [];
      prefixMatches.concat(restMatched, restFamilyOnly).forEach(function (c) {
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
      buildMasterList: buildMasterList,
      search: search
    };
  }

  var api = { fold: fold, getWords: getWords, create: create };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  } else {
    root.HTF = root.HTF || {};
    root.HTF.ingredientSearch = api;
  }
})(typeof window !== 'undefined' ? window : this);
