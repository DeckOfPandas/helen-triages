document.addEventListener('DOMContentLoaded', function () {
  var activeTags = new Set();
  var activeStar = null;
  var activeIngredient = null;
  var activeMetaFilters = new Set();
  var nameQuery = ''; // 'rewrite' and/or 'proofread'
  var isSearching = false;

  var items = document.querySelectorAll('.recipe-list li');

  var matrix = document.querySelector('.controls');
  var recipeList = document.querySelector('.recipe-list');
  var clearButton = null;
  if (matrix) {
    var clearBtn = document.createElement('button');
    clearBtn.type = 'button';
    clearBtn.className = 'btn-clear';
    clearBtn.textContent = '× clear all';
    matrix.insertBefore(clearBtn, matrix.firstChild);
    clearButton = clearBtn;
  }

  var searchBox = document.getElementById('ingredient-search-box');
  var resultsPool = document.getElementById('ingredient-results-pool');
  var ingredientClear = document.getElementById('ingredient-search-clear');
  var nameSearchBox = document.getElementById('name-search-box');
  var nameSearchClear = document.getElementById('name-search-clear');

  // ---------------------------------------------------------------------------
  // Ingredient vocabulary — read from _data/ingredient_words.yml, emitted as
  // JSON by index.html. Nothing about ingredient words is written down in this
  // file; to change search behaviour, edit the YAML.
  // ---------------------------------------------------------------------------
  var VOCABULARY = (function () {
    var fallback = { search: { family_button_min_chars: 3 }, singulars: {}, synonyms: {} };
    var node = document.getElementById('ingredient-vocabulary');
    if (!node) {
      console.warn(
        'filters.js: no #ingredient-vocabulary block found. index.html should ' +
        'emit _data/ingredient_words.yml as JSON before loading this script. ' +
        'Ingredient search will run without singulars or synonyms.'
      );
      return fallback;
    }
    try {
      var parsed = JSON.parse(node.textContent);
      parsed.search = parsed.search || fallback.search;
      parsed.singulars = parsed.singulars || {};
      parsed.synonyms = parsed.synonyms || {};
      parsed.modifiers = parsed.modifiers || [];
      parsed.never_family = parsed.never_family || [];
      parsed.family_exceptions = parsed.family_exceptions || [];
      parsed.stopwords = parsed.stopwords || [];
      return parsed;
    } catch (e) {
      console.warn('filters.js: could not parse #ingredient-vocabulary — ' + e.message);
      return fallback;
    }
  })();

  // The minimum query length before "(all)" family buttons appear.
  // DO NOT replace this with a literal. The value is defined once, in
  // _data/ingredient_words.yml, precisely so that it cannot drift.
  var FAMILY_BUTTON_MIN_CHARS = VOCABULARY.search.family_button_min_chars;

  var singularMap = VOCABULARY.singulars;

  function normaliseIngredientWord(word) {
    return singularMap[word] || word;
  }

  // synonymMap: maps a query word to a set of ingredient words that count as
  // matches. When the query exactly equals a key, any ingredient containing any
  // of the listed words is treated as a candidate, and the key earns a forced
  // (all) button.
  var synonymMap = VOCABULARY.synonyms;

  // Strip diacritics for MATCHING ONLY. Nobody types "comté" into a search box,
  // so folding both sides lets `comte`, `comté` and `mte` all find the same
  // ingredient. Display is never folded — buttons render the ingredient's real
  // text, accents intact.
  function fold(str) {
    return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }

  // Synonym keys are folded once at startup so a folded query still finds them.
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

  function hasActiveFilters() {
    return activeTags.size > 0 || activeStar !== null || activeMetaFilters.size > 0;
  }

  function getWords(str) {
    return str.toLowerCase().trim().split(/\s+/).filter(Boolean);
  }

  // Preparation-state words ("chopped", "crispy") describe what was done to
  // an ingredient, not what it is — recipe files keep them (they're accurate
  // instructions), but the search UI strips them so "chopped pistachios" and
  // "pistachios" are treated as the one ingredient rather than two. Deliberately
  // NOT a general "strip adjectives" list: "ground almonds" vs "flaked almonds",
  // "whole milk" vs milk, and "smoked haddock" are genuinely different products,
  // so only words with no product distinction riding on them belong in
  // _data/ingredient_words.yml's `modifiers` list.
  var modifierSet = new Set((VOCABULARY.modifiers || []).map(function(w) {
    return fold(String(w).toLowerCase());
  }));

  // Colour/variety words ("red", "white", "mixed") that head 2+ entries but
  // are never themselves a standalone ingredient — "red" isn't stripped like
  // a modifier (red onion is genuinely different from onion), it just never
  // earns an "(all)" button, because the entries sharing it ("red wine",
  // "red onion", "red Thai curry paste") aren't a real family, only a
  // coincidence. See _data/ingredient_words.yml for the reasoning per word.
  var neverFamilySet = new Set((VOCABULARY.never_family || []).map(function(w) {
    return fold(String(w).toLowerCase());
  }));

  // Specific entries excluded from counting towards their own head word's
  // family — "cherry tomatoes" isn't a cherry, "tomato ketchup" isn't a type
  // of tomato. Unlike never_family, the WORD can still head a family if a
  // genuine member justifies one ("tomato" still forms from "tomatoes" and
  // "tomato purée" once ketchup is excluded) — this only removes the
  // impostor from the count, not the whole word from ever grouping.
  var familyExceptionSet = new Set((VOCABULARY.family_exceptions || []).map(function(w) {
    return fold(String(w).toLowerCase());
  }));

  function stripModifiers(ing) {
    var words = ing.split(/\s+/);
    while (words.length > 1 && modifierSet.has(fold(words[0].toLowerCase()))) {
      words.shift();
    }
    return words.join(' ');
  }

  // Connector words ("and", "or", "of", "with") that never count as a match
  // target, wherever they fall in the phrase — "chicken thighs AND
  // drumsticks" meant typing "a" matched on "and". Unlike stripModifiers
  // above, this only affects internal matching: getWords(ing) is used for
  // computation, never for the displayed label (that's always the original
  // `ing` string), so removing a connector here never breaks the sentence
  // the way stripping it from the front would.
  var stopwordSet = new Set((VOCABULARY.stopwords || []).map(function(w) {
    return fold(String(w).toLowerCase());
  }));

  function getMatchWords(ing) {
    return getWords(ing).filter(function(word) {
      return !stopwordSet.has(fold(word));
    });
  }

  // Built here, not at the top of the file, because stripping modifiers needs
  // VOCABULARY and fold() to already exist.
  var allIngredientsSet = new Set();
  items.forEach(function(li) {
    var rawIng = li.dataset.ingredients || '';
    rawIng.split(',').map(function(s) { return s.trim(); }).filter(Boolean).forEach(function(ing) {
      allIngredientsSet.add(stripModifiers(ing));
    });
  });
  // A plain .sort() is case-sensitive — every capital letter sorts before
  // every lowercase one, so "Chinese five spice" would jump ahead of "chai",
  // "cheddar" and "cheese" instead of sitting between "chestnuts" and
  // "chives" where it belongs.
  var masterIngredientsList = Array.from(allIngredientsSet).sort(function(a, b) {
    return a.toLowerCase().localeCompare(b.toLowerCase());
  });

  function makeIngredientButton(key, label, wordMatch) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn-tag btn-ingredient';
    if (key === activeIngredient) btn.classList.add('active');
    if (wordMatch) btn.classList.add('btn-ingredient--word-match');
    btn.dataset.ingredient = key;
    btn.textContent = label;
    return btn;
  }

  function updateIngredientClear() {
    if (ingredientClear) {
      ingredientClear.style.display = (activeIngredient || (searchBox && searchBox.value.trim())) ? 'inline-block' : 'none';
    }
  }






function renderResultsPool() {
  if (!searchBox || !resultsPool) return;
  var query = fold(searchBox.value.trim().toLowerCase());
  resultsPool.innerHTML = '';
  activeIngredient = null;
  isSearching = !!query;
  if (!query) {
    update();
    return;
  }
  var enableFamilyButtons = query.length >= FAMILY_BUTTON_MIN_CHARS;
  var renderedKeys = new Set();
  var queryWords = query.split(/\s+/).filter(Boolean);
  var multiWord = queryWords.length > 1;

  // Count how many DISTINCT ingredient entries share each FIRST word. A word
  // shared as the head of 2+ entries is a "family" and earns an umbrella
  // "(all)" button — "chicken" heads chicken breast/leg/thigh/mince/stock.
  //
  // Only the first word counts, not every word in the phrase. "chop" is the
  // SECOND word of both "lamb chops" and "pork chops" — those are cuts of
  // lamb and of pork respectively, not members of a "chop" family, so a
  // "chop (all)" button that lumps them together is nonsense: nobody thinks
  // "what can I cook with some kind of chop". Likewise "paste" trails a
  // dozen unrelated things (curry paste, anchovy paste, tamarind paste) that
  // share nothing but their form.
  //
  // Entries are counted by their NORMALISED key, not their raw text, so
  // "peach" and "peaches" (same entry after normalisation) count once and
  // don't conjure a spurious "peach (all)" from nothing.
  //
  // _data/ingredient_words.yml's `family_exceptions` are skipped entirely —
  // "cherry tomatoes" doesn't count towards "cherry"'s family, the same way
  // "tomato ketchup" doesn't count towards "tomato"'s.
  var wordToEntries = {};
  masterIngredientsList.forEach(function(ing) {
    if (familyExceptionSet.has(fold(ing.toLowerCase()))) return;
    var normWords = getMatchWords(ing).map(normaliseIngredientWord).map(fold);
    var entryKey = normWords.join(' ');
    var headWord = normWords[0];
    if (!wordToEntries[headWord]) wordToEntries[headWord] = new Set();
    wordToEntries[headWord].add(entryKey);
  });

  if (multiWord) {
    var multiMatches = [];
    masterIngredientsList.forEach(function(ing) {
      var ingWords = getMatchWords(ing);
      var ingKey = ingWords.map(normaliseIngredientWord).join(' ');
      var allMatch = queryWords.every(function(qw) {
        return ingWords.some(function(iw) { return iw.indexOf(qw) !== -1; });
      });
      if (!allMatch) return;
      // Same "start of the string" rule as the single-word path.
      var isPrefixMatch = fold(ing.toLowerCase()).indexOf(query) === 0;
      // Same "any word" rule as the single-word path's hasWordMatch, applied
      // per query word: does every word you typed start some word in this
      // entry (not necessarily the same one, not necessarily in order)?
      var hasWordMatch = queryWords.every(function(qw) {
        return ingWords.some(function(iw) { return iw.indexOf(qw) === 0; });
      });
      multiMatches.push({ ing: ing, ingKey: ingKey, isPrefixMatch: isPrefixMatch, hasWordMatch: hasWordMatch });
    });
    // Same three-band order as the single-word path — see the comment
    // there for why word-matches are ranked above, but not as high as,
    // strict prefix matches.
    var multiPrefix = multiMatches.filter(function(c) { return c.isPrefixMatch; });
    var multiRestMatched = multiMatches.filter(function(c) { return !c.isPrefixMatch && c.hasWordMatch; });
    var multiRestOther = multiMatches.filter(function(c) { return !c.isPrefixMatch && !c.hasWordMatch; });
    multiPrefix.concat(multiRestMatched, multiRestOther).forEach(function(c) {
      if (!renderedKeys.has(c.ingKey)) {
        renderedKeys.add(c.ingKey);
        resultsPool.appendChild(makeIngredientButton(c.ing, c.ing, c.hasWordMatch));
      }
    });
  } else {
    // --- Single-word query ---
    //
    // Rules:
    // 1. Collect all matching ingredients, whether via a literal substring
    //    match or membership of an engaged curated family (see below).
    // 2. A word heading 2+ distinct entries earns a "word (all)" umbrella
    //    button (see the wordToEntries build above).
    // No suppression step — see Step 2 below for why one used to exist here
    // and doesn't any more.

    // Step 1: collect all matching entries with their normalised word sets.
    var candidates = []; // { ing, normKey, isPrefixMatch }
    var familyWords = new Set(); // words that earn an (all) button
    var engagedFamilyWords = new Set(); // folded synonym words for families the query is heading towards

    // A curated family (declared in _data/ingredient_words.yml `synonyms`) is
    // ENGAGED once the query is a recognisable prefix of its name — "chees" is
    // clearly heading towards "cheese". A curated family has a known, finite
    // membership list, so its members are surfaced inline rather than gated
    // behind the "(all)" button, which stays as a one-click way to select the
    // whole family as a single filter.
    //
    // This replaces the old "typing narrows, never widens" rule, which existed
    // to stop one keystroke exploding into twenty buttons — but it also meant
    // even typing "cheese" in full only ever showed entries literally
    // containing the word "cheese", never cheddar, feta or gouda. Reversed at
    // Helen's request: a curated family is a known list, not an open-ended
    // one, so widening to it is safe.
    if (enableFamilyButtons) {
      Object.keys(foldedSynonymMap).forEach(function (key) {
        if (key.indexOf(query) === 0) {
          familyWords.add(key);
          foldedSynonymMap[key].forEach(function (w) { engagedFamilyWords.add(w); });
        }
      });
    }

    masterIngredientsList.forEach(function(ing) {
      var ingWords = getMatchWords(ing);
      var normWords = ingWords.map(normaliseIngredientWord).map(fold);
      var normKey = normWords.join(' ');

      // Checks each word's normalised form as well as its raw text. Most
      // plurals in _data/ingredient_words.yml's `singulars` are a plain
      // "+s"/"+es", so the singular is already a literal prefix of the
      // plural and matches without this. A handful are genuinely irregular
      // ("cherries"→cherry, "leaves"→leaf) — the ending changes rather than
      // just extending, so "cherries" never contains "cherry" as a raw
      // substring at all, and typing "cherry" found nothing despite the
      // singular being correctly declared.
      var matchedAnyWord = ingWords.some(function(word, idx) {
        return fold(word).indexOf(query) !== -1 || normWords[idx].indexOf(query) !== -1;
      });

      // Membership check mirrors how the (all) button itself filters recipes
      // in update() — a substring match against the whole ingredient text —
      // so "cream cheese" and "goat's cheese" are recognised as cheeses even
      // though "cheese" is only one of their two words.
      var foldedIng = fold(ing.toLowerCase());
      var isFamilyMember = false;
      engagedFamilyWords.forEach(function(syn) {
        if (foldedIng.indexOf(syn) !== -1) isFamilyMember = true;
      });

      if (!matchedAnyWord && !isFamilyMember) return;

      // "Start of the string", not "start of any word" — "chocolate chips"
      // matching on "chips" put it ahead of things that actually start with
      // the query, which reads as arbitrary rather than relevant. Also
      // checks the normalised first word, so "cherries" ranks as a prefix
      // match for "cherry" rather than falling to the bottom tier for
      // reasons that have nothing to do with relevance.
      var isPrefixMatch = foldedIng.indexOf(query) === 0 || normWords[0].indexOf(query) === 0;

      // For the background tint (see .btn-ingredient--word-match): does ANY
      // word — not just the first — start with the query? Deliberately
      // looser than isPrefixMatch above, which only ever looks at the start
      // of the whole string. "cream cheese" isn't ranked as a top match for
      // "chees" (it doesn't start with "chees"), but it's still worth
      // marking as a real textual hit rather than a family-only one like
      // "cheddar", which doesn't contain "chees" anywhere at all.
      var hasWordMatch = ingWords.some(function(word, idx) {
        return fold(word).indexOf(query) === 0 || normWords[idx].indexOf(query) === 0;
      });

      candidates.push({ ing: ing, normKey: normKey, isPrefixMatch: isPrefixMatch, hasWordMatch: hasWordMatch });

      // Check for STRUCTURAL family membership — a FIRST word with no curated
      // synonym list that nonetheless heads 2+ distinct entries (only for
      // queries at or above FAMILY_BUTTON_MIN_CHARS — see
      // _data/ingredient_words.yml). Curated families are handled above.
      //
      // Only the head word, and only as a PREFIX of it — not contained
      // anywhere in it. "chi" sits inside "pistachios" (pis-TA-CHI-os) with
      // no relation to what was typed, and earned a nonsensical "pistachios
      // (all)" button; checking every word, not just the first, is what
      // produced "chop (all)" from "lamb chops"/"pork chops".
      //
      // Excludes _data/ingredient_words.yml's `never_family` list — "red",
      // "white", "mixed" and the like genuinely head 2+ entries, but those
      // entries are unrelated foods that merely share a colour or variety
      // word ("red wine", "red onion"), not a real family.
      //
      // Checks the normalised first word too, same reasoning as
      // matchedAnyWord above — "berries" should be able to head a "berry"
      // family the same way "chicken" heads one, not be silently excluded
      // because the plural is irregular.
      if (enableFamilyButtons && (fold(ingWords[0]).indexOf(query) === 0 || normWords[0].indexOf(query) === 0)) {
        var headWord = normWords[0];
        if (!neverFamilySet.has(headWord)) {
          var entries = wordToEntries[headWord];
          if (entries && entries.size > 1) {
            familyWords.add(headWord);
          }
        }
      }
    });

    // Step 2: render — (all) buttons first, then every candidate, in original
    // order.
    //
    // There used to be a Step 3 here that suppressed a candidate whenever
    // some other candidate's word set was a strict subset of it — meant to
    // catch "chicken legs" as a redundant variant of "chicken leg". Checked
    // against the real data: every one of the 31 cases it actually fired on
    // turned out to hide a genuinely different product behind a
    // similar-sounding one — "red wine" hid "red wine vinegar", "brown
    // sugar" hid both "dark brown sugar" and "soft brown sugar", "tomato
    // purée" hid "sundried tomato purée". Its one stated justification
    // ("chicken legs"/"chicken leg") is handled elsewhere anyway — identical
    // entries after normalisation are deduplicated below by normKey, before
    // this step would even run. No confirmed benefit, multiple confirmed
    // harms — removed rather than patched further.
    var renderedAllKeys = new Set();
    familyWords.forEach(function(fw) {
      var label = fw + ' (all)';
      if (!renderedAllKeys.has(fw)) {
        renderedAllKeys.add(fw);
        // Always a word match by construction — a family only ever forms
        // (curated or structural) when its word already starts with the
        // query, so this is never in doubt for an (all) button.
        resultsPool.appendChild(makeIngredientButton(label, label, true));
      }
    });

    // Render order, three bands: entries starting with the query outrank
    // everything else, full stop — family membership affects whether an
    // entry is INCLUDED (matchedAnyWord / isFamilyMember above), not where
    // it ranks. Within the rest, a genuine word match ("cream cheese",
    // matched on its own text) outranks a family-only member ("cheddar",
    // included purely because the curated list says it's a cheese) —
    // deliberately NOT promoted as far as the prefix tier, or "chocolate
    // chips" (tinted for "chi" via "chips") would rank alongside "chicken
    // breast" again, the exact confusion the prefix-tier rule exists to
    // avoid. Alphabetical within each band — masterIngredientsList is
    // already sorted, and filtering preserves that order.
    var prefixMatches = candidates.filter(function(c) { return c.isPrefixMatch; });
    var restMatched = candidates.filter(function(c) { return !c.isPrefixMatch && c.hasWordMatch; });
    var restFamilyOnly = candidates.filter(function(c) { return !c.isPrefixMatch && !c.hasWordMatch; });

    prefixMatches.concat(restMatched, restFamilyOnly).forEach(function(c) {
      if (!renderedKeys.has(c.normKey)) {
        renderedKeys.add(c.normKey);
        resultsPool.appendChild(makeIngredientButton(c.ing, c.ing, c.hasWordMatch));
      }
    });
  }

  var buttons = resultsPool.querySelectorAll('.btn-ingredient');
  if (buttons.length === 1) {
    var onlyBtn = buttons[0];
    activeIngredient = onlyBtn.dataset.ingredient;
    onlyBtn.classList.add('active');
    isSearching = false;
  }
  update();
  updateIngredientClear();
}


  


  



  if (searchBox) {
    searchBox.addEventListener('input', renderResultsPool);
  }

  if (ingredientClear) {
    ingredientClear.addEventListener('click', function() {
      activeIngredient = null;
      isSearching = false;
      if (searchBox) searchBox.value = '';
      if (resultsPool) resultsPool.innerHTML = '';
      update();
    });
  }

  // Keep aria-pressed in step with the .active class.
  //
  // .active is toggled in fifteen places; aria-pressed is set in one. Syncing
  // from update() rather than at each toggle site means there is a single place
  // to be right, and no way for the visual state and the announced state to
  // disagree.
  function syncAriaPressed() {
    matrix.querySelectorAll('.btn-star, .btn-tag, .btn-meta').forEach(function(btn) {
      btn.setAttribute('aria-pressed', btn.classList.contains('active') ? 'true' : 'false');
    });
  }

  function update() {
    var visibleCount = 0;
    var suppressList = isSearching && !hasActiveFilters();
    if (recipeList) recipeList.style.display = suppressList ? 'none' : '';

    if (!suppressList) {
      items.forEach(function(li) {
        var tags = (li.dataset.tags || '').split(',').filter(Boolean);
        var star = li.dataset.star || '';
        var ingList = (li.dataset.ingredients || '').split(',').map(function(s) { return s.trim(); });
        var visible = true;

        activeTags.forEach(function(t) {
          if (tags.indexOf(t) === -1) visible = false;
        });

        if (activeStar && star !== activeStar) visible = false;

        if (nameQuery) {
          var title = (li.querySelector('a') || {}).textContent || '';
          if (title.toLowerCase().indexOf(nameQuery) === -1) visible = false;
        }

        if (activeMetaFilters.has('rewrite') && li.dataset.metaRewrite !== 'true') visible = false;
        if (activeMetaFilters.has('proofread') && li.dataset.metaProofread !== 'true') visible = false;
        if (activeMetaFilters.has('no-short') && li.dataset.metaShort === 'true') visible = false;
        if (activeMetaFilters.has('has-short') && li.dataset.metaShort !== 'true') visible = false;

        if (activeIngredient) {
          var hasMatch = false;
          var activeKey = activeIngredient.replace(' (all)', '').trim();
          var activeSynonyms = getSynonymWords(activeKey);
          if (activeSynonyms) {
            // Synonym (all): match any ingredient containing any synonym word
            for (var i = 0; i < ingList.length; i++) {
              var ingLower2 = ingList[i].toLowerCase();
              if (activeSynonyms.some(function(syn) { return ingLower2.indexOf(syn) !== -1; })) {
                hasMatch = true; break;
              }
            }
          } else {
            var activeWords = getWords(activeKey).map(normaliseIngredientWord);
            for (var i = 0; i < ingList.length; i++) {
              var ingWords2 = getWords(ingList[i]).map(normaliseIngredientWord);
              var allMatch = activeWords.every(function(aw) {
                return ingWords2.some(function(iw) { return iw.indexOf(aw) !== -1; });
              });
              if (allMatch) { hasMatch = true; break; }
            }
          }
          if (!hasMatch) visible = false;
        }

        li.style.display = visible ? '' : 'none';
        if (visible) visibleCount++;
      });
    }

    document.querySelectorAll('.recipe-list .badge').forEach(function(badge) {
      var text = badge.textContent.trim();
      badge.classList.remove('badge--matched', 'badge-ingredient-hit');
      if (activeTags.has(text) || activeStar === text) {
        badge.classList.add('badge--matched');
      }
    });

    // Highlight matching ingredient pills
    var activeKey2 = activeIngredient ? activeIngredient.replace(' (all)', '').trim() : '';
    var activeSynonyms2 = activeKey2 ? getSynonymWords(activeKey2) : null;
    var activeWords = (!activeSynonyms2 && activeKey2)
      ? getWords(activeKey2).map(normaliseIngredientWord)
      : [];
    document.querySelectorAll('.recipe-list .ingredient-pill').forEach(function(pill) {
      pill.classList.remove('ingredient--matched');
      if (!activeKey2) return;
      var pillText = pill.textContent.trim().toLowerCase();
      var matches;
      if (activeSynonyms2) {
        matches = activeSynonyms2.some(function(syn) { return pillText.indexOf(syn) !== -1; });
      } else {
        var pillWords = getWords(pillText).map(normaliseIngredientWord);
        matches = activeWords.every(function(aw) {
          return pillWords.some(function(pw) { return pw.indexOf(aw) !== -1; });
        });
      }
      if (matches) pill.classList.add('ingredient--matched');
    });

    var emptyMessage = document.querySelector('.recipe-list-empty');
    emptyMessage.style.display = (!suppressList && visibleCount === 0) ? 'block' : 'none';

    var searchingMessage = document.querySelector('.recipe-list-searching');
    if (searchingMessage) searchingMessage.style.display = suppressList ? 'block' : 'none';

    if (clearButton) {
      clearButton.style.visibility = (activeTags.size > 0 || activeStar || activeIngredient || activeMetaFilters.size > 0) ? 'visible' : 'hidden';
      if (nameSearchClear) nameSearchClear.style.display = nameQuery ? 'inline' : 'none';
    }

    updateInlineLabels();
    updateIngredientClear();
    syncAriaPressed();
  }

  function updateInlineLabels() {
    var starRow = document.querySelector('.category.category--star');
    if (starRow && starRow.querySelector('.btn-clear-inline')) {
      starRow.querySelector('.btn-clear-inline').style.display = activeStar ? 'inline-block' : 'none';
    }

    document.querySelectorAll('.category').forEach(function(row) {
      if (row.classList.contains('category--star') || row.classList.contains('search')) return;
      var trigger = row.querySelector('.btn-clear-inline');
      if (trigger) {
        trigger.style.display = row.querySelector('.btn-tag.active') !== null ? 'inline-block' : 'none';
      }
    });
  }

  if (matrix) {
    matrix.addEventListener('click', function(e) {
      var target = e.target;

      if (target.classList.contains('btn-tag') && !target.classList.contains('btn-ingredient')) {
        var tag = target.dataset.tag;
        if (activeTags.has(tag)) {
          activeTags.delete(tag);
          target.classList.remove('active');
        } else {
          activeTags.add(tag);
          target.classList.add('active');
        }
        update();
        return;
      }

      if (target.classList.contains('btn-star')) {
        var starValue = target.dataset.star;
        if (activeStar === starValue) {
          activeStar = null;
          target.classList.remove('active');
        } else {
          activeStar = starValue;
          matrix.querySelectorAll('.btn-star').forEach(function(b) { b.classList.remove('active'); });
          target.classList.add('active');
        }
        update();
        return;
      }

      if (target.classList.contains('btn-meta')) {
        var metaKey = target.dataset.meta;
        if (activeMetaFilters.has(metaKey)) {
          activeMetaFilters.delete(metaKey);
          target.classList.remove('active');
        } else {
          activeMetaFilters.add(metaKey);
          target.classList.add('active');
        }
        update();
        return;
      }

      if (target.classList.contains('btn-clear-inline')) {
        var row = target.closest('.category');
        if (row) {
          if (row.classList.contains('category--star')) {
            activeStar = null;
            matrix.querySelectorAll('.btn-star').forEach(function(b) { b.classList.remove('active'); });
          } else {
            row.querySelectorAll('.btn-tag').forEach(function(b) {
              activeTags.delete(b.dataset.tag);
              b.classList.remove('active');
            });
          }
          update();
        }
        return;
      }

      if (target.classList.contains('btn-ingredient')) {
        var ing = target.dataset.ingredient;
        if (activeIngredient === ing) {
          activeIngredient = null;
          isSearching = true;
          target.classList.remove('active');
        } else {
          activeIngredient = ing;
          isSearching = false;
          var rawKey = target.dataset.ingredient;
          if (searchBox) searchBox.value = rawKey.replace(' (all)', '').trim();
          resultsPool.innerHTML = '';
          resultsPool.appendChild(target);
          matrix.querySelectorAll('.btn-ingredient').forEach(function(b) { b.classList.remove('active'); });
          target.classList.add('active');
        }
        update();
        return;
      }
    });
  }

  if (nameSearchBox) {
    nameSearchBox.addEventListener('input', function() {
      nameQuery = nameSearchBox.value.trim().toLowerCase();
      update();
    });
  }

  if (nameSearchClear) {
    nameSearchClear.addEventListener('click', function() {
      nameQuery = '';
      nameSearchBox.value = '';
      nameSearchClear.style.display = 'none';
      update();
    });
  }

  if (clearButton) {
    clearButton.addEventListener('click', function() {
      activeTags.clear();
      activeStar = null;
      activeIngredient = null;
      activeMetaFilters.clear();
      nameQuery = '';
      isSearching = false;
      if (searchBox) searchBox.value = '';
      if (nameSearchBox) nameSearchBox.value = '';
      if (nameSearchClear) nameSearchClear.style.display = 'none';
      if (resultsPool) resultsPool.innerHTML = '';
      if (matrix) {
        matrix.querySelectorAll('.btn-tag, .btn-star, .btn-meta').forEach(function(btn) {
          btn.classList.remove('active');
        });
      }
      update();
    });
  }

  update();
});
