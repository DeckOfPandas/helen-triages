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

  function create(vocabulary, bottleData) {
    var voc = vocabulary || {};
    var cfg = voc.search || {};
    var bottles = bottleData || {};

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
    var familyAliases = voc.family_aliases || {};
    var familyLabels = voc.family_labels || {};

    /* What the (all) button SAYS, which is not always the family's key --
       `family_labels` in the vocabulary. Helen, 2026-08-29: "I think that chip
       should be 'whisk(e)y (all)', even though it's clunky, to avoid ever
       having to split or claim they combine."

       A LABEL RATHER THAN A RENAME, and the reason is mechanical: a
       `<family>_characters` list is keyed off the family's name (see
       test_a_declared_character_vocabulary_is_enforced, which strips that
       suffix), so renaming the family would drag `whisk(e)y_characters` along
       with it. Same separation `card_names` already draws for generics --
       matching runs on the key, the button shows the name. */
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

    /* ONE CHIP PER CATEGORY, CARRYING THE CARD'S NAME FOR IT — Helen's ruling,
       2026-08-29, looking at `aged rum` and `moderately aged rum` offered as two
       separate chips: "we have no 'aged rum' in our dictionary."

       She was right and it was worse than one pair. FIFTEEN generics in the
       collection also had their card name in the pool as a chip of its own, and
       ELEVEN of those fifteen pairs selected exactly the same drinks -- two
       buttons, one answer, and no way to tell from either which was which.

       The card name wins, so the picker speaks the language the cards speak.
       The generic stays SEARCHABLE (`cardNameTerms` below), so typing
       "moderately" still finds the `aged rum` chip; it just never appears as a
       second button. Food's `display_names` is the same idea and its comment is
       the one to read: "matching still has to run against the real match key,
       not the pretty name."

       THE COLLAPSING PAIRS COME FREE AND ARE THE BEST PART. `sugar syrup 1:1`
       and `sugar syrup 2:1` share the card name `sugar syrup`, so they become
       one chip covering 35 drinks rather than two covering 4 and 31 -- which is
       §9.10.1's own ruling arriving in the picker: "a ratio is a MAKING fact,
       not a CHOOSING fact". Same for the two honey waters and the two
       Jamaicans. `card_names_may_collide` already declares each of these three
       as deliberate. */
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

    /* What a chip actually selects. A plain entry covers only itself -- the
       exact rule this module's header argues for -- and a card-name chip covers
       every generic it stands for. Nothing here is a substring test. */
    function coveredBy(chipValue) {
      var key = normalise(chipValue);
      return chipCovers[key] || [key];
    }

    /* Which chip a term ends up under, as a comparable key. A generic and the
       card name that abbreviates it are the SAME chip, so asking "are these
       two names the same option?" has to be asked here rather than of the
       strings -- `moderately aged Jamaican rum` and `Jamaican rum` are one
       answer, not two. */
    function chipKeyOf(term) {
      return normalise(chipForTerm[normalise(term)] || term);
    }

    /* ---------------------------------------------------------------------
       DECLARED VOCABULARY versus TRANSCRIBED TEXT
       ---------------------------------------------------------------------
       A generic or a card name is a name Helen chose. A suggestion is free text
       typed while transcribing a recipe, and it is the only one of the three
       that arrives carrying sentences. The two rules below apply to the second
       kind and must never touch the first.

       THIS IS NOT DEFENSIVENESS, IT IS ONE MEASURED CASE: `coconut rum` is a
       declared generic AND a declared alias of the bottle `Malibu`. Without
       this boundary the `coconut rum` chip would resolve to `Malibu`, putting a
       brand back into the picker and reversing #501's ruling that no brand
       appears on a card. It is the only collision of the 173 against the 97,
       and it would have been a silent regression.

       Derived from the file's own shape, exactly as test_cocktails.py's
       _declared_generics does: every list-valued key is a generic vocabulary
       except `families` and the `<family>_characters` lists. A group added to
       the YAML is covered by the line that adds it. */
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

    /* THE SPELLING TO SHOW A READER, for a term that arrived downcased.
       `data-ing` is lowercased at build time -- the card wants it that way and
       the filtering compares folded strings -- so every searchable term is
       lower case by the time this module sees it. That is invisible while
       nothing renders a term, and #603's annotation renders one: the bracket
       would read `cachaça (sagatiba)` for a bottle the collection spells
       Sagatiba, and `(havana club 3)` for one it spells Havana Club 3.

       Both source files carry the real spelling, so neither is guessed: the
       vocabulary for a generic or a card name, bottles.yml for a bottle. An
       unknown string is returned as it came, which is the only honest answer
       and is what a drink's own suggestion text gets. */
    function canonicalSpelling(term) {
      var key = normalise(term);
      return declaredVocabulary[key] || bottleCanonical[key] || term;
    }

    /* THE SPELLING THAT EXPLAINS THE MATCH, which is not always the canonical
       one -- and a bracket that cannot explain itself is the whole of #603.

       `Wray and Nephew` is an ALIAS of the bottle `Wray & Nephew`. Someone
       typing "and" matches the alias; canonicalising the answer prints
       `Jamaican overproof rum (Wray & Nephew)`, where neither the chip nor the
       bracket contains a single letter of what they typed. That is the exact
       complaint #603 was raised about, arriving through the fix for it.

       So: the canonical name when it carries the query, and otherwise the
       spelling that actually did -- preferring the alias AS WRITTEN in
       bottles.yml over the downcased attribute, because one is a name someone
       chose and the other is a build artefact. */
    function displaySpelling(term, query) {
      var canonical = canonicalSpelling(term);
      if (!query || normalise(canonical).indexOf(query) !== -1) return canonical;
      return bottleAliasSpelling[normalise(term)] || term;
    }

    /* A BOTTLE KEEPS ONE IDENTITY — Helen: "'wray and nephew' and 'wray &
       nephew' should both collapse onto the latter." bottles.yml has said so
       since #529 ("ALIASES ARE HOW A BOTTLE KEEPS ONE IDENTITY... add the
       spelling, do not add a second bottle") and the search had never read it,
       which HANDOVER §9.10.1 names as the known excess: "suggestions go in raw
       rather than resolved through bottles.yml's aliases, so `Havana 3` and
       `Havana Club 3` can both appear." 97 names and aliases over 38 bottles. */
    /* Every alias AS WRITTEN, keyed by its folded form. bottleCanonical answers
       "which bottle is this", which is the right answer almost everywhere and
       the wrong one for a bracket: `Wray & Nephew` is the bottle, and it is not
       what someone typing "and" matched -- they matched the alias
       "Wray and Nephew". See displaySpelling. */
    var bottleAliasSpelling = Object.create(null);

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

    /* WHICH CATEGORY A BOTTLE IS, keyed by every spelling it answers to. The
       same file, one field further in, and it is what lets an ingredient
       offering two categories say which of them a bottle actually names --
       see buildPool. A bottle's category is bottle-invariant (#529: "Appleton
       12 is a moderately-aged Jamaican in every drink that pours it"), which
       is why reading it here does NOT reopen #441's ruling against a shared
       table for `character`. */
    var bottleGenericOf = Object.create(null);
    Object.keys(bottles.bottles || {}).forEach(function (name) {
      var generic = (bottles.bottles[name] || {}).generic;
      if (!generic) return;
      bottleGenericOf[normalise(name)] = generic;
      ((bottles.bottles[name] || {}).aliases || []).forEach(function (alias) {
        bottleGenericOf[normalise(alias)] = generic;
      });
    });

    /* The bottle file's OWN list of suggestion strings that are not a usable
       bottle name -- ten of them, each carrying the reason it is unresolved and
       what shape it wants instead. Declared there rather than detected here,
       because "two bottles in one string, in two categories" is a judgement
       about the drinks and not a fact about the characters. #585 is the backlog
       of working them off. */
    var unresolvedSuggestion = Object.create(null);
    Object.keys(bottles.unresolved_suggestions || {}).forEach(function (s) {
      unresolvedSuggestion[normalise(s)] = true;
    });

    /* PROSE IS NOT A BOTTLE NAME — Helen met four of these one at a time, so
       the shape is a rule rather than a list of the four. Both halves are
       declared in _data/cocktails/ingredients.yml's `search:` block, where the
       measurement behind them is recorded: applied to all 87 real suggestions
       it flags 17, every one genuinely prose, and catches no bottle name.

       WHOLE WORDS, NOT LETTERS. `orgeat`, `orange juice` and `Cointreau` all
       contain "or"; none is a disjunction. */
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

    /* One term as it arrives on a card -> the chip it should become, or null to
       not offer it at all. Declared vocabulary passes through untouched: a
       generic is a name Helen chose, and `ginger and lemongrass cordial` must
       survive any rule aimed at transcription. */
    function resolveTerm(term) {
      if (isDeclared(term)) return term;
      if (isProse(term)) return null;
      var key = normalise(term);
      if (unresolvedSuggestion[key]) return null;
      return bottleCanonical[key] || term;
    }

    /* THE SAME QUESTION ASKED OF A TERM THAT WILL NEVER BE A BUTTON, and the
       one place the two answers differ is deliberate.

       BECOMING A CHIP needs a usable bottle name, so resolveTerm above drops
       everything `unresolved_suggestions` names. BEING A WAY IN only needs to
       be a NAME: `Portobello` and `Luxardo` are in that list because a brand
       is not a bottle (#529), and typing either of them to reach `gin` and
       `maraschino liqueur` is a feature Helen has praised -- §9.3.3 cites it.
       Dropping those from the search to satisfy a rule about buttons would
       take out the thing band 3 exists for.

       PROSE IS DIFFERENT AND GOES, on both paths. "Havana 7, Appleton 8" is
       not a name at all, so it can neither be a button nor explain one: under
       #603's annotation it prints a bracket that is two bottles, on two
       different chips, with nothing saying which belongs to which. 14 hidden
       terms read as prose today.

       THE CANONICAL NAME JOINS THE TERMS, it does not replace them -- the same
       bargain the loose branch already strikes below, and for the same reason:
       `ED3` is an alias whose canonical name contains none of its letters, so
       collapsing rather than adding would delete a way in that works today. */
    function resolveHiddenTerm(term) {
      if (isDeclared(term)) return term;
      if (isProse(term)) return null;
      return bottleCanonical[normalise(term)] || term;
    }

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
    /* Returns CHIPS, not strings: { value, terms }. `value` is what the button
       says and what gets stored as a filter; `terms` is everything that finds
       it -- the card name, every generic it stands for, and any bottle that
       sits beside it.

       TAKES ONE GROUP PER INGREDIENT, not one per card, and that is what makes
       the rule below expressible at all: a `suggestion` is a bottle FOR the
       generic written next to it, and only the per-ingredient `data-ing`
       attribute knows which generic that is. A card-level list has already
       thrown the pairing away.

       A BOTTLE IS NOT OFFERED WHEN ITS CATEGORY IS — Helen's ruling,
       2026-08-29, on `falernum` and `john d taylor's velvet falernum` sitting
       side by side: "the first chip being 'falernum (all)' would at least stop
       me worrying that the two sets were disjoint."

       They are not disjoint, and that was measured rather than argued: the
       falernum bottle matches 1 drink and the category matches 14, and the 1 is
       inside the 14. Across all 15 bottle/category pairs in the collection, 14
       are strictly nested -- the exception is a data bug, not a design case.
       So the two chips were never alternatives, and a picker that lays them out
       as though they were is asking a question with no answer.

       The bottle stays SEARCHABLE as a hidden term of its category, so typing
       "velvet" or "el dorado" still gets you there; what goes is the second
       button. Same shape as #501's ruling one layer up: the card shows the
       category, and the bottle is the drink page's business. */
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

        /* The bottles beside this ingredient, as searchable names: the way in
           survives, the second button does not. Routed through
           resolveHiddenTerm now -- prose is not a name and cannot explain a
           chip, and a bottle's canonical spelling joins its own. */
        var hidden = [];
        loose.forEach(function (raw) {
          var resolved = resolveHiddenTerm(raw);
          if (resolved === null) return;
          if (hidden.indexOf(raw) === -1) hidden.push(raw);
          if (hidden.indexOf(resolved) === -1) hidden.push(resolved);
        });

        /* A BOTTLE BELONGS TO THE OPTION IT NAMES, NOT TO EVERY OPTION ON THE
           POUR. An ingredient may offer two categories -- a disjunctive
           `generic` means "either would do" (#441) -- and then name a bottle
           for each. Nothing in the drink says which goes with which; the two
           lists simply sit in the same order, and order is not a statement.

           Attaching all of them to all of them is what put `Jamaican rum` in
           front of Helen when she typed "havana" (#603). The proof that this
           is a CODE fault rather than a data one is Kamaniwanalaya, whose
           suggestions were rewritten into a proper list on 2026-08-30 and
           whose every bottle resolves cleanly: typing "chairman" still offered
           both `aged rum` and `Jamaican rum`, though Chairman's Reserve is
           declared `moderately aged rum` and nothing else.

           So the pairing is recovered from bottles.yml, which states each
           bottle's own category, rather than from position. Three ingredients
           in the collection have this shape today.

           DELIBERATELY NARROW, and the case it must not break is #534's: an
           ingredient offering ONE category may suggest a bottle from another
           on purpose -- a cherry brandy suggesting Cherry Heering, which is a
           liqueur -- so a bottle is only ever filtered AWAY from an option
           when it demonstrably names a different option on the same pour. */
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
          // A disjunction, or a suggestion the bottle file calls unresolved,
          // never becomes a chip at all; an aliased bottle becomes its
          // canonical self. See resolveTerm above.
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

      /* FOUR BANDS, NOT FOOD'S THREE — Helen, 2026-08-29: "it's surprising to
         me that 've' returns 'falernum' before any vermouth. I think here it
         should be prefix matching of first word, prefix matching of any word,
         then prefix matching of any word in the bottle name as is this one,
         then substring."

             1  the chip's own name starts with the query      "ve" -> vermouth
             2  a word in the chip's own name starts with it   "ve" -> sweet vermouth
             3  a word in a name it does NOT show starts with it
                                                               "ve" -> falernum,
                                                               via velvet falernum
             4  the query is only a substring of its own name  "li" -> galliano

         The rule underneath is that VISIBLE BEATS HIDDEN at equal strength, and
         any real word beats a mere substring. Band 3 exists at all because
         Helen chose to stop offering a bottle its own chip when its category is
         offered -- the bottle became a way IN to the category rather than a
         button, and a way in that outranked the thing you actually typed.

         A chip is ranked by its BEST term. That is also what keeps the generic
         searchable after the card name took the button: "moderately" band-1
         matches `moderately aged rum` and surfaces the `aged rum` chip. */
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
            /* WHICH TERM ACTUALLY MATCHED, which is a different question from
               which chip won -- and on band 3 it is the only place the answer
               exists. A chip found through a name it does not display can say
               nothing about why it is on screen unless it is handed the term,
               and #603 is what happens then: typing "mu" returns
               `clear blended rum` (matched inside "clear blended MUlti-region
               rum") and "sa" returns `cachaça` (matched on the bottle
               Sagatiba). Both are band 3 working exactly as designed.

               Carried on every band, not only band 3, because a consumer
               asking "is this the chip's own name?" should compare rather
               than infer -- on bands 1, 2 and 4, `via` is the chip's own
               value. */
            via: displaySpelling(term, query),
            /* WHAT KIND of name found it, because the three hidden kinds are
               three different arguments and #603 collects one of each:

                 own      the chip's own name -- bands 1, 2 and 4
                 generic  a category name the card name abbreviates away
                          ("mu" -> `clear blended rum`, via "clear blended
                          MUlti-region rum")
                 bottle   a suggestion sitting beside the generic. This is the
                          kind band 3 was BUILT for -- "velvet" -> `falernum`

               THERE IS NO `prose` KIND, and there was one for an hour. A
               suggestion that is not a bottle name at all -- "Havana 7,
               Appleton 8" -- used to reach the search as a hidden term and
               would have printed as a chip's own explanation. resolveHiddenTerm
               drops those from the pool now, so a prose string cannot be
               matched, and a fourth value here would be a classification
               nothing can produce. */
            viaKind: (normalise(term) === normalise(value)) ? 'own'
              : isDeclared(term) ? 'generic' : 'bottle',
            /* WHEN THE NAME THAT FOUND IT SHOULD REPLACE THE CHIP'S OWN RATHER
               THAN SIT IN A BRACKET AFTER IT — Helen, 2026-08-31, on
               `clear blended rum (clear blended multi-region rum)`: "should be
               returned without its display name given that name is a bit of a
               hack. I don't know if this is a one-off or a principle."

               It is a principle, and measured: 15 of the 27 card names are
               STRICT ABBREVIATIONS of their generic -- every word of the card
               name appears in the generic, which adds a qualifier. So the
               bracket in all fifteen repeats the chip to itself and appends the
               bit it dropped: `aged rum (moderately aged rum)`,
               `Demerara rum (aged Demerara rum)`, `gin (London dry gin)`.

               A bracket is for a name that is genuinely OTHER -- Sagatiba,
               Beefeater, El Dorado 3 -- where the two strings say different
               things and both are worth reading. Where the longer one simply
               contains the shorter, printing both is printing one twice, and
               the longer is the one that answers the question.

               THE CHIP'S VALUE IS UNTOUCHED. This is what a candidate is
               LABELLED; what gets stored, compared against a card and cleared
               is still the card name, because that is what the index filters
               by. */
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

          /* A HIDDEN TERM MUST BE MATCHED ON A REAL WORD, never on a substring
             and never on a connector.

             Helen, 2026-08-29: "'el' returns both 'aged rum' and 'jamaican
             rum', which is counterintuitive." Neither LABEL contains "el"; the
             match was mid-word inside the generics those chips stand for,
             "moderat(el)y aged rum" and "caram(el)-forward Jamaican rum". So
             band 3 is out for anything the chip does not display: a card can
             always print its reason, and a chip cannot print a term it hides.

             BAND 2 STAYS, AND HAS TO. It is what makes typing a bottle name
             find its category -- "velvet" reaching `falernum`, which is the
             whole point of not offering the bottle its own button. A first pass
             banned band 2 as well; it took "velvet" with it.

             What band 2 must NOT do is match a connector. Sweeping all 676
             two-letter queries found `an` returning `Smith & Cross`, because
             its alias is spelled "Smith AND Cross" -- a word that is in the
             name without being any of what the name means. The prose list
             already names those words for a different job, and it is the same
             set of words for the same reason. */
          var band;
          if (normalise(term) === normalise(value)) {
            // What the chip SHOWS: food's three bands, with substring last.
            band = scored.isPrefixMatch ? 1 : (scored.hasWordMatch ? 2 : 4);
          } else {
            /* A name the chip does NOT show. It must be matched on a real word
               -- never a substring, which is how "el" surfaced `aged rum` out
               of "moderat(el)y", and never a connector, which is how "an"
               surfaced `Smith & Cross` out of "Smith AND Cross". The prose list
               already names those words for a different job and it is the same
               set for the same reason. */
            /* A MULTI-WORD QUERY MATCHES A HIDDEN NAME FROM ITS START, and
               that is not an exception to the rule above -- it is the same
               rule. Helen, 2026-08-31: "I do want to be able to type 'el d'
               and see el dorado."

               `hasWordMatch` asks whether one WORD begins with the whole
               query, so it can never be true of a query containing a space:
               "el d" prefixes no single word of "el dorado 12", and typing the
               bottle's real name found nothing at all. What band 3 exists to
               refuse is a match that begins in the MIDDLE of a word -- "el"
               inside "moderat(el)y" -- and a match at the start of the whole
               string cannot be one of those, because position 0 is a word
               boundary by definition.

               So the test is "does this name begin with what you typed", which
               is band 1's own test applied to a name the chip does not show.
               It cannot readmit the connector case either: `an` is not a
               prefix of "Smith & Cross". */
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

      /* Shared with food rather than re-derived — see orderByBand's own note in
         assets/js/ingredient-search.js. What is shared is the discipline (lower
         band first, input order preserved inside a band, which is what makes
         "alphabetical within a band" free); the bands themselves are this
         site's four, computed above. */
      var ordered = IS.orderByBand(candidates, function (c) { return c.band; });

      /* A family earns a button when the query is heading towards its NAME and
         it has at least one member in the pool. The membership half is not
         decoration: `families` is a spec, and offering "aquavit (all)" on a
         collection holding no aquavit is an umbrella over nothing. Same shape
         as the index's own rule that a mood with no drinks renders no button. */
      var familyButtons = [];
      if (typed.length >= FAMILY_BUTTON_MIN_CHARS) {
        families.forEach(function (family) {
          /* REACHED BY ANY OF ITS NAMES, but always LABELLED with its canonical
             one -- `family_aliases` in the vocabulary. A family nobody spells
             the way it is stored is a family nobody can reach: `whiskey` found
             nothing at all, and `agave` is named after the plant because it
             holds mezcal too, so nobody types it.

             One button, never one per spelling. `scotch` offering a second
             umbrella called "scotch (all)" would be an umbrella lying about its
             own width -- the family holds bourbon and rye. Saying `whisky` on
             the button is what makes that visible instead. */
          var label = labelForFamily(family);

          /* ALREADY CHOSEN, SO NOT OFFERED AGAIN. The chosen chips are drawn
             first and the search's results after them; pool candidates were
             filtered against `chosen` and family buttons were NOT, so an
             umbrella you had already picked came straight back round as an
             offer and rendered twice -- Helen, with the screenshot: "If I click
             'whiskey (all)', I see the same button again." Same class of
             omission as #390's dropped flag: the answer was computed and one of
             the two consumers ignored it. */
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
      /* Whole-entry membership against everything this chip stands for. For a
         plain entry that is the entry itself; for a card-name chip it is every
         generic wearing that name, which is how one `sugar syrup` chip reaches
         both ratios without a substring rule anywhere near it. */
      var wanted = coveredBy(chip);
      return (entries || []).some(function (entry) {
        return wanted.indexOf(normalise(entry)) !== -1;
      });
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

    /* An (all) chip back to the family it stands for. Resolved through EVERY
       name the family answers to, not just its key, because the chip carries
       the display label -- `whisk(e)y (all)` has to find `whisky`. Sharing
       namesForFamily with the button builder is what stops a label that can be
       offered but not applied. */
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
