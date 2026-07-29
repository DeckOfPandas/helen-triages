document.addEventListener('DOMContentLoaded', function () {
  var activeTags = new Set();
  var activeStar = null;
  var activeIngredient = null;
  var activeMetaFilters = new Set();
  var nameQuery = ''; // 'rewrite' and/or 'proofread'
  var isSearching = false;

  var allIngredientsSet = new Set();
  var items = document.querySelectorAll('.recipe-list li');

  items.forEach(function(li) {
    var rawIng = li.dataset.ingredients || '';
    rawIng.split(',').map(function(s) { return s.trim(); }).filter(Boolean).forEach(function(ing) {
      allIngredientsSet.add(ing);
    });
  });
  var masterIngredientsList = Array.from(allIngredientsSet).sort();

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


  function makeIngredientButton(key, label) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn-tag btn-ingredient';
    if (key === activeIngredient) btn.classList.add('active');
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

  // Count how many DISTINCT ingredient entries each normalised word appears in.
  // A word shared by 2+ entries is a "family" and earns an umbrella "(all)" button.
  //
  // Entries are counted by their NORMALISED key, not their raw text. Two entries
  // that differ only by pluralisation are the same entry as far as the reader is
  // concerned, and should not conjure a family between them: "peach" and
  // "peaches" both normalise to "peach", so they count once and no spurious
  // "peach (all)" button appears. Genuine families — "cheese" spanning "blue
  // cheese", "cheddar cheese", "cream cheese" — have distinct normalised keys
  // and are unaffected.
  var wordToEntries = {};
  masterIngredientsList.forEach(function(ing) {
    var normWords = getWords(ing).map(normaliseIngredientWord).map(fold);
    var entryKey = normWords.join(' ');
    var seenInThisEntry = new Set();
    normWords.forEach(function(w) {
      if (seenInThisEntry.has(w)) return;
      seenInThisEntry.add(w);
      if (!wordToEntries[w]) wordToEntries[w] = new Set();
      wordToEntries[w].add(entryKey);
    });
  });

  if (multiWord) {
    masterIngredientsList.forEach(function(ing) {
      var ingWords = getWords(ing);
      var ingKey = ingWords.map(normaliseIngredientWord).join(' ');
      var allMatch = queryWords.every(function(qw) {
        return ingWords.some(function(iw) { return iw.indexOf(qw) !== -1; });
      });
      if (allMatch && !renderedKeys.has(ingKey)) {
        renderedKeys.add(ingKey);
        resultsPool.appendChild(makeIngredientButton(ing, ing));
      }
    });
  } else {
    // --- Single-word query ---
    //
    // Rules:
    // 1. Collect all matching ingredients.
    // 2. For any word shared by 2+ entries, emit a "word (all)" umbrella button.
    // 3. Suppress an entry if another matching entry's normalised word set is a
    //    strict subset of its own — i.e. it's a plural/variant of a shorter form
    //    that is also in the results. e.g. "chicken legs" is suppressed when
    //    "chicken leg" is present, because {chicken, leg} ⊂ {chicken, legs}.
    // 4. Always suppress entries that are pure members of an (all) family AND
    //    have no additional distinguishing words beyond the family word itself
    //    — i.e. single-word entries like bare "chicken" when "chicken (all)" exists.

    // Step 1: collect all matching entries with their normalised word sets.
    var candidates = []; // { ing, normWords, normKey }
    var familyWords = new Set(); // words that earn an (all) button

    // TYPING NARROWS, NEVER WIDENS.
    //
    // The synonym families in _data/ingredient_words.yml are deliberately NOT
    // used to expand these suggestions. They used to be: an exact query match
    // swapped substring matching for the whole curated family, so "chees"
    // offered seven buttons and "cheese" offered twenty-one. One keystroke
    // exploded the result set, which is the opposite of what a search box
    // should do.
    //
    // The family is now reachable only through its "(all)" button, which the
    // click handler expands using the same synonym list. Naming a declared
    // family always earns that button, whether or not the word happens to
    // appear literally in any ingredient.
    if (getSynonymWords(query)) familyWords.add(query);

    masterIngredientsList.forEach(function(ing) {
      var ingWords = getWords(ing);
      var normWords = ingWords.map(normaliseIngredientWord).map(fold);

      var matchedAnyWord = ingWords.some(function(word) {
        return fold(word).indexOf(query) !== -1;
      });
      if (!matchedAnyWord) return;

      var normKey = normWords.join(' ');
      candidates.push({ ing: ing, normWords: normWords, normKey: normKey });

      // Check each matched word for family membership (only for queries at or
      // above FAMILY_BUTTON_MIN_CHARS — see _data/ingredient_words.yml)
      if (enableFamilyButtons) {
        ingWords.forEach(function(word, idx) {
          if (fold(word).indexOf(query) === -1) return;
          var normWord = normWords[idx];
          var entries = wordToEntries[normWord];
          if (entries && entries.size > 1) {
            familyWords.add(normWord);
          }
        });
      }
    });

    // Step 2: build normalised word sets for subset check.
    // For each candidate, compute its Set of normalised words.
    var candidateSets = candidates.map(function(c) {
      return new Set(c.normWords);
    });

    // Step 3 & 4: decide which candidates to suppress.
    // Suppress candidate i if:
    //   (a) candidate i's normalised word set is a strict superset of another
    //       candidate j's word set — i.e. i is a plural/variant of a shorter
    //       form j that is also in the results.
    //       e.g. "chicken legs" {chicken,leg} is suppressed when "chicken leg"
    //       {chicken,leg} is present (same after normalisation), OR
    //       more generally when j's words are all contained in i's words and
    //       j is shorter.
    //   (b) candidate i is a single-word entry whose word is a family word
    //       (bare "chicken" suppressed in favour of "chicken (all)")
    // Two-pass suppression:
    // Pass 1 — rule (b): suppress bare single-word family members.
    // Pass 2 — rule (a): suppress entries that are strict supersets of a
    //           non-suppressed entry (catches plurals and redundant variants).
    //           Must be a second pass so we don't use suppressed entries as
    //           suppressors (e.g. bare "chicken" must not cause "chicken leg"
    //           to be suppressed).
    var suppress = candidates.map(function(c) {
      return c.normWords.length === 1 && familyWords.has(c.normWords[0]);
    });

    candidates.forEach(function(c, i) {
      if (suppress[i]) return; // already suppressed
      for (var j = 0; j < candidates.length; j++) {
        if (i === j || suppress[j]) continue; // skip self and suppressed candidates
        var otherSet = candidateSets[j];
        var thisSet = candidateSets[i];
        if (otherSet.size >= thisSet.size) continue; // j must be strictly smaller than i
        var jSubsetOfI = true;
        otherSet.forEach(function(w) { if (!thisSet.has(w)) jSubsetOfI = false; });
        if (jSubsetOfI) { suppress[i] = true; break; }
      }
    });

    // Step 5: render — (all) buttons first, then survivors in original order.
    var renderedAllKeys = new Set();
    familyWords.forEach(function(fw) {
      var label = fw + ' (all)';
      if (!renderedAllKeys.has(fw)) {
        renderedAllKeys.add(fw);
        resultsPool.appendChild(makeIngredientButton(label, label));
      }
    });

    candidates.forEach(function(c, i) {
      if (suppress[i]) return;
      if (!renderedKeys.has(c.normKey)) {
        renderedKeys.add(c.normKey);
        resultsPool.appendChild(makeIngredientButton(c.ing, c.ing));
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
