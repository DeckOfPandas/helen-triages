// =============================================================================
// COCKTAIL SEARCH — pool, ranking and matching for the drinks index. No DOM;
// cocktail-index.js owns the wiring (#579, MANUAL §3).
//
// Loaded as a plain <script> after ingredient-search.js (attaching to
// window.HTF), and via require() in tests/js/cocktail-search.test.js.
//
// Shares only `fold`, `getWords` and `orderByBand` with food. Food's matcher
// strips cook's prose, which this curated vocabulary has none of; food derives
// families from a shared head word, which cannot work here ("aged Demerara rum"
// and "moderately aged Jamaican rum"), so a family is declared in `family_of`.
//
// Fuzzy to find, fuzzy to include, exact to exclude. Over-including shows a
// drink and the card says why; over-excluding hides one invisibly. Never a
// substring test against the joined attribute: `gin` would hide ginger syrup.
// =============================================================================
(function (root) {
  'use strict';

  var IS = (typeof module !== 'undefined' && module.exports)
    ? require('./ingredient-search.js')
    : root.HTF.ingredientSearch;

  var fold = IS.fold;
  var getWords = IS.getWords;

  // Must stay identical to filter-state.js's FAMILY_SUFFIX.
  var FAMILY_SUFFIX = ' (all)';

  // The build-time attribute -> its entries: `|`-separated and `|`-terminated.
  // Matching runs on these entries, never on the joined string, where a query
  // could match across the seam between two ingredients.
  function splitEntries(attrValue) {
    return String(attrValue == null ? '' : attrValue)
      .split('|')
      .map(function (s) { return s.trim(); })
      .filter(Boolean);
  }

  // Folding that cannot change a string's length, so an offset into the folded
  // form is an offset into the original: nameHighlight() hands it to `slice`.
  // A character whose fold would change length is left unfolded.
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

  function create(vocabulary, bottleData) {
    var voc = vocabulary || {};
    var cfg = voc.search || {};
    var bottles = bottleData || {};

    // Both numbers live in _data/cocktails/ingredients.yml's `search:` block;
    // do not write either down here.
    var MIN_QUERY_CHARS = cfg.min_query_chars;
    var FAMILY_BUTTON_MIN_CHARS = cfg.family_button_min_chars;

    var families = (voc.families || []).map(String);
    var familyOfGeneric = voc.family_of || {};
    var cardNames = voc.card_names || {};
    var familyAliases = voc.family_aliases || {};
    var familyLabels = voc.family_labels || {};

    // What the (all) button says, e.g. `whisk(e)y`. A label, not a rename:
    // the `<family>_characters` lists are keyed off the family's name.
    function labelForFamily(family) {
      return familyLabels[family] || family;
    }

    // Every spelling a family answers to: its key, its display label, and any
    // declared alias. One list, used both to find the family and to resolve a
    // chip back to it, so the two can never disagree about what counts.
    function namesForFamily(family) {
      var names = [family, labelForFamily(family)];
      Object.keys(familyAliases).forEach(function (alias) {
        if (familyAliases[alias] === family) names.push(alias);
      });
      return names;
    }

    // One chip per category, carrying the card's name for it. The generic
    // stays a searchable term of that chip and never becomes a second button;
    // generics sharing a card name (`sugar syrup` for both ratios) are one
    // chip. Matching runs on the generic, the button shows the card name.
    var chipForTerm = Object.create(null);   // folded term -> the chip it belongs to
    var chipCovers = Object.create(null);    // folded chip -> [folded terms it selects]

    function cover(chipValue, term) {
      var chipKey = normalise(chipValue);
      var termKey = normalise(term);
      if (!chipKey || !termKey) return;
      if (!chipCovers[chipKey]) chipCovers[chipKey] = [];
      if (chipCovers[chipKey].indexOf(termKey) === -1) chipCovers[chipKey].push(termKey);
      chipForTerm[termKey] = chipValue;
    }

    Object.keys(cardNames).forEach(function (generic) {
      var card = cardNames[generic];
      cover(card, generic);
      cover(card, card);
    });

    // What a chip selects: a plain entry covers only itself, a card-name chip
    // every generic it stands for. Never a substring test.
    function coveredBy(chipValue) {
      var key = normalise(chipValue);
      return chipCovers[key] || [key];
    }

    // Which chip a term ends up under, as a comparable key: a generic and the
    // card name that abbreviates it are the same chip.
    function chipKeyOf(term) {
      return normalise(chipForTerm[normalise(term)] || term);
    }

    // Declared vocabulary (generics and card names) versus transcribed
    // suggestions. The prose and bottle rules below apply only to suggestions:
    // `coconut rum` is a generic and also an alias of the bottle Malibu, and
    // must not resolve to the brand (#501). Every list-valued key is a generic
    // vocabulary except `families` and the `<family>_characters` lists.
    var declaredVocabulary = Object.create(null);
    Object.keys(voc).forEach(function (key) {
      if (key === 'families' || /_characters$/.test(key)) return;
      if (!Array.isArray(voc[key])) return;
      // The VALUE, not `true`: this doubles as the map from a downcased
      // attribute back to the spelling Helen wrote -- see canonicalSpelling.
      voc[key].forEach(function (value) { declaredVocabulary[normalise(value)] = value; });
    });
    Object.keys(cardNames).forEach(function (generic) {
      declaredVocabulary[normalise(generic)] = generic;
      declaredVocabulary[normalise(cardNames[generic])] = cardNames[generic];
    });

    function isDeclared(term) {
      return !!declaredVocabulary[normalise(term)];
    }

    // The spelling to show a reader. `data-ing` is lowercased at build time,
    // so a term is recovered from the vocabulary or bottles.yml; an unknown
    // string is returned as it came.
    function canonicalSpelling(term) {
      var key = normalise(term);
      return declaredVocabulary[key] || bottleCanonical[key] || term;
    }

    // The spelling that explains the match (#603): the canonical name when it
    // contains the query, otherwise the alias as bottles.yml writes it.
    // Typing "and" matches the alias `Wray and Nephew`; printing
    // `Wray & Nephew` would show none of what was typed.
    function displaySpelling(term, query) {
      var canonical = canonicalSpelling(term);
      if (!query || normalise(canonical).indexOf(query) !== -1) return canonical;
      return bottleAliasSpelling[normalise(term)] || term;
    }

    // Every alias as written, keyed by its folded form -- see displaySpelling.
    var bottleAliasSpelling = Object.create(null);

    // A bottle keeps one identity: every alias in bottles.yml resolves to the
    // bottle's name (#529).
    var bottleCanonical = Object.create(null);
    Object.keys(bottles.bottles || {}).forEach(function (name) {
      // A bottle whose NAME is also declared vocabulary is not a bottle here --
      // #314 permits three brands as generics precisely because nothing
      // generalises them, and their chip is the descriptive card name.
      if (isDeclared(name)) return;
      bottleCanonical[normalise(name)] = name;
      cover(name, name);
      ((bottles.bottles[name] || {}).aliases || []).forEach(function (alias) {
        if (isDeclared(alias)) return;
        bottleCanonical[normalise(alias)] = name;
        bottleAliasSpelling[normalise(alias)] = alias;
        // So the chip SELECTS the drink that named the alias, not merely finds
        // it: a drink listing `wray and nephew` must answer to `Wray & Nephew`
        // in the exclude direction too, where there is no fuzzy reach to save it.
        cover(name, alias);
      });
    });

    // Which category a bottle is, keyed by every spelling it answers to. It
    // lets an ingredient offering two categories say which one a bottle names
    // -- see buildPool.
    var bottleGenericOf = Object.create(null);
    Object.keys(bottles.bottles || {}).forEach(function (name) {
      var generic = (bottles.bottles[name] || {}).generic;
      if (!generic) return;
      bottleGenericOf[normalise(name)] = generic;
      ((bottles.bottles[name] || {}).aliases || []).forEach(function (alias) {
        bottleGenericOf[normalise(alias)] = generic;
      });
    });

    // bottles.yml's own list of suggestion strings that are not a usable
    // bottle name. Declared there, not detected here (#585).
    var unresolvedSuggestion = Object.create(null);
    Object.keys(bottles.unresolved_suggestions || {}).forEach(function (s) {
      unresolvedSuggestion[normalise(s)] = true;
    });

    // Prose is not a bottle name. Both lists are declared in the vocabulary's
    // `search:` block. Whole words, not letters: `orgeat` contains "or" and is
    // not a disjunction.
    var proseWords = (cfg.prose_words || []).map(function (w) {
      return String(w).toLowerCase();
    });
    var proseMarks = (cfg.prose_marks || []).map(String);

    function isProse(term) {
      var text = String(term == null ? '' : term);
      if (proseMarks.some(function (m) { return text.indexOf(m) !== -1; })) return true;
      var seen = getWords(fold(text.toLowerCase()));
      return proseWords.some(function (w) { return seen.indexOf(w) !== -1; });
    }

    // One term as it arrives on a card -> the chip it should become, or null to
    // not offer it at all. Declared vocabulary passes through untouched:
    // `ginger and lemongrass cordial` must survive any rule aimed at prose.
    function resolveTerm(term) {
      if (isDeclared(term)) return term;
      if (isProse(term)) return null;
      var key = normalise(term);
      if (unresolvedSuggestion[key]) return null;
      return bottleCanonical[key] || term;
    }

    // The same question for a term that is only a way in, never a button. It
    // deliberately keeps what `unresolved_suggestions` names: a brand such as
    // `Luxardo` is not a bottle (#529) but typing it must still reach its
    // category. Prose goes on both paths. The caller adds the canonical name
    // beside the raw term, not in place of it: `ED3` shares no letter with
    // `El Dorado 3`.
    function resolveHiddenTerm(term) {
      if (isDeclared(term)) return term;
      if (isProse(term)) return null;
      return bottleCanonical[normalise(term)] || term;
    }

    // Entry -> the families it belongs to. A card name resolves through the
    // generic it abbreviates. A list, because a card name may stand for two
    // generics (#501) and nothing guarantees they share a family.
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

    // --- the pool -------------------------------------------------------------

    // Returns chips, { value, terms }: `value` is what the button says and
    // what is stored as a filter; `terms` is everything that finds it.
    //
    // Takes one group per ingredient (its `data-ing`), not one per card: a
    // suggestion is a bottle for the generic written beside it, and only the
    // per-ingredient attribute keeps that pairing.
    //
    // A bottle is not offered as a chip when its category is. It stays a
    // hidden term of the category, so typing "velvet" still reaches `falernum`.
    function buildPool(ingredientGroups) {
      var byValue = Object.create(null);

      function add(chipValue, terms) {
        var key = normalise(chipValue);
        if (!byValue[key]) byValue[key] = { value: chipValue, terms: [] };
        terms.forEach(function (t) {
          if (t && byValue[key].terms.indexOf(t) === -1) byValue[key].terms.push(t);
        });
      }

      (ingredientGroups || []).forEach(function (group) {
        var raws = splitEntries(group);
        // The declared half of this ingredient: its generics and their card
        // names. Everything else in the group is a bottle someone typed.
        var declared = raws.filter(isDeclared);
        var loose = raws.filter(function (r) { return !isDeclared(r); });

        var hidden = [];
        loose.forEach(function (raw) {
          var resolved = resolveHiddenTerm(raw);
          if (resolved === null) return;
          if (hidden.indexOf(raw) === -1) hidden.push(raw);
          if (hidden.indexOf(resolved) === -1) hidden.push(resolved);
        });

        // An ingredient may offer two categories (a disjunctive `generic`,
        // #441) and name a bottle for each. A bottle belongs to the option
        // bottles.yml says it is, not to every option (#603). Deliberately
        // narrow: an ingredient offering one category may suggest a bottle
        // from another on purpose (#534), so a bottle is filtered away from an
        // option only when it names a different option on the same ingredient.
        var groupChips = Object.create(null);
        declared.forEach(function (raw) { groupChips[chipKeyOf(raw)] = true; });
        var offersSeveral = Object.keys(groupChips).length > 1;

        function belongsWith(term, raw) {
          if (!offersSeveral) return true;
          var generic = bottleGenericOf[normalise(term)];
          if (!generic) return true;                    // not a bottle we know
          var key = chipKeyOf(generic);
          if (!groupChips[key]) return true;            // names no option here
          return key === chipKeyOf(raw);
        }

        declared.forEach(function (raw) {
          var chipValue = chipForTerm[normalise(raw)] || raw;
          var mine = hidden.filter(function (term) { return belongsWith(term, raw); });
          add(chipValue, [raw].concat(coveredBy(chipValue), mine));
        });

        if (declared.length) return;

        // No category on this ingredient, so a bottle is all there is to offer.
        loose.forEach(function (raw) {
          var entry = resolveTerm(raw);
          if (entry === null) return;
          var chipValue = chipForTerm[normalise(entry)] || entry;
          // The RAW term stays searchable, so collapsing a spelling never loses
          // a way in: typing "wray and nephew" still finds `Wray & Nephew`.
          add(chipValue, [raw, entry].concat(coveredBy(chipValue)));
        });
      });
      return Object.keys(byValue).map(function (k) { return byValue[k]; })
        .sort(function (a, b) {
          return a.value.toLowerCase().localeCompare(b.value.toLowerCase());
        });
    }

    // --- the search -----------------------------------------------------------

    // Returns { familyButtons, results }. Every candidate is returned, by
    // Helen's ruling: no cap and no "+N more".
    function search(rawQuery, pool, chosen) {
      var typed = String(rawQuery == null ? '' : rawQuery).trim();
      var empty = { familyButtons: [], results: [] };
      if (typed.length < MIN_QUERY_CHARS) return empty;

      var query = normalise(typed);
      if (!query) return empty;

      var taken = (chosen || []).map(normalise);
      var candidates = [];

      // Four bands (food has three); a chip is ranked by its best term:
      //   1  the chip's own name starts with the query      "ve" -> vermouth
      //   2  a word in the chip's own name starts with it   "ve" -> sweet vermouth
      //   3  a word in a name it does not show starts with it
      //                                      "ve" -> falernum, via velvet falernum
      //   4  the query is only a substring of its own name  "li" -> galliano
      // Visible beats hidden at equal strength; a real word beats a substring.
      (pool || []).forEach(function (chip) {
        var value = chip && chip.value !== undefined ? chip.value : chip;
        var terms = (chip && chip.terms) ? chip.terms : [value];
        if (taken.indexOf(normalise(value)) !== -1) return;

        var best = null;
        var bestBand = Infinity;
        terms.forEach(function (term) {
          var folded = normalise(term);
          if (folded.indexOf(query) === -1) return;
          var words = getWords(folded);
          var scored = {
            entry: value,
            // Which term matched, in the spelling that carries the query. On
            // band 3 it is the only way the chip can say why it is on screen
            // (#603); on the other bands it is the chip's own value.
            via: displaySpelling(term, query),
            // What kind of name found it: `own` (the chip's name), `generic`
            // (a category name its card name abbreviates) or `bottle` (a
            // suggestion beside the generic).
            viaKind: (normalise(term) === normalise(value)) ? 'own'
              : isDeclared(term) ? 'generic' : 'bottle',
            // True when the matched generic contains every word of the card
            // name: the label then shows the generic alone, since a bracket
            // would repeat the chip (`aged rum (moderately aged rum)`). A
            // bottle always gets a bracket. The chip's stored value is
            // untouched; this only changes how a candidate is labelled.
            viaReplacesName: (function () {
              if (normalise(term) === normalise(value)) return false;
              if (!isDeclared(term)) return false;
              var termWords = getWords(normalise(term));
              return getWords(normalise(value)).every(function (w) {
                return termWords.indexOf(w) !== -1;
              });
            })(),
            isPrefixMatch: folded.indexOf(query) === 0,
            hasWordMatch: words.some(function (w) { return w.indexOf(query) === 0; })
          };

          var band;
          if (normalise(term) === normalise(value)) {
            // What the chip SHOWS: food's three bands, with substring last.
            band = scored.isPrefixMatch ? 1 : (scored.hasWordMatch ? 2 : 4);
          } else {
            // A name the chip does not show must match at the start of a word
            // or of the whole name, never mid-word: "el" inside "moderately"
            // would surface `aged rum`, which cannot print its reason. The
            // whole-name test is what lets "el d" reach `El Dorado`. A word
            // match that lands only on prose words ("or", "with") does not
            // count; `and` is deliberately not a prose word.
            if (!scored.hasWordMatch && !scored.isPrefixMatch) return;
            if (scored.hasWordMatch) {
              var onlyConnector = words.every(function (w) {
                return w.indexOf(query) !== 0 || proseWords.indexOf(w) !== -1;
              });
              if (onlyConnector) return;
            }
            band = 3;
          }

          if (band < bestBand) { bestBand = band; best = scored; }
        });
        if (best) { best.band = bestBand; candidates.push(best); }
      });

      // Lower band first, pool order (alphabetical) kept inside a band.
      var ordered = IS.orderByBand(candidates, function (c) { return c.band; });

      // A family earns a button when the query prefixes one of its names and
      // it has at least one member in the pool.
      var familyButtons = [];
      if (typed.length >= FAMILY_BUTTON_MIN_CHARS) {
        families.forEach(function (family) {
          // Reached by any of its names, labelled with one: a single button
          // per family, never one per spelling.
          var label = labelForFamily(family);

          // An umbrella already chosen is not offered again.
          if (taken.indexOf(normalise(label + FAMILY_SUFFIX)) !== -1) return;

          if (!namesForFamily(family).some(function (n) {
            return normalise(n).indexOf(query) === 0;
          })) return;

          var present = (pool || []).some(function (chip) {
            var terms = (chip && chip.terms) ? chip.terms : [chip];
            return terms.some(function (t) { return familiesOf(t).indexOf(family) !== -1; });
          });
          if (present) familyButtons.push(label);
        });
      }

      // An umbrella suppresses its own bare word (#51): `gin (all)` takes out
      // `gin` and leaves `sloe gin`. The cost is that the bare name cannot be
      // picked alone while the umbrella is on offer.
      // familyButtons holds bare labels (the index appends the suffix), so
      // there is no suffix to strip here.
      var umbrellaNames = familyButtons.map(normalise);
      var offered = ordered.filter(function (candidate) {
        return umbrellaNames.indexOf(normalise(candidate.entry)) === -1;
      });

      return {
        familyButtons: familyButtons,
        results: offered
      };
    }

    // --- the two matching rules -----------------------------------------------

    // Exact, or a declared family: whole-entry membership against everything
    // the chip covers. Never a substring, never against the joined attribute.
    function matchesExclude(entries, chip) {
      if (!chip) return false;
      if (isFamilyValue(chip)) return entryHasFamily(entries, chipFamily(chip));
      var wanted = coveredBy(chip);
      return (entries || []).some(function (entry) {
        return wanted.indexOf(normalise(entry)) !== -1;
      });
    }

    // Every word of the chip must prefix some word of the entry. Prefix, not
    // "contained in", which would make "apple juice" match pineapple juice.
    // Still loose on purpose: a `gin` chip reaches ginger syrup here, and
    // `gin (all)` is the precise answer.
    function matchesInclude(entries, chip) {
      if (!chip) return false;
      if (isFamilyValue(chip)) return entryHasFamily(entries, chipFamily(chip));
      // Everything exclude would take, plus the fuzzy reach below. A card-name
      // chip must never select FEWER drinks than the same chip would exclude.
      if (matchesExclude(entries, chip)) return true;
      var chipWords = getWords(normalise(chip));
      if (!chipWords.length) return false;
      return (entries || []).some(function (entry) {
        var entryWords = getWords(normalise(entry));
        return chipWords.every(function (cw) {
          return entryWords.some(function (ew) { return ew.indexOf(cw) === 0; });
        });
      });
    }

    // An (all) chip back to its family, through every name the family answers
    // to: the chip carries the display label, so `whisk(e)y (all)` has to
    // find `whisky`.
    function chipFamily(chip) {
      var wanted = familyKey(chip);
      var hit = null;
      families.forEach(function (family) {
        if (hit) return;
        if (namesForFamily(family).some(function (n) { return normalise(n) === wanted; })) {
          hit = family;
        }
      });
      return hit;
    }

    // Does this one ingredient answer any chosen include chip? The card lights
    // a matched ingredient with it, so it must use the rule the filter used.
    function entryIsHit(entries, chips) {
      return (chips || []).some(function (chip) {
        return matchesInclude(entries, chip);
      });
    }

    // --- I know what I want ---------------------------------------------------

    // Substring, unlike the ingredient fields: "negr" should find the Negroni.
    // Folded, so an accented name is reachable from an ASCII keyboard.
    function matchesName(title, query) {
      var wanted = foldByCharacter(String(query == null ? '' : query).trim());
      if (!wanted) return true;
      return foldByCharacter(String(title == null ? '' : title)).indexOf(wanted) !== -1;
    }

    // Where the match sits in the original title, for the highlight (#564):
    // fold to compare, never to display.
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
