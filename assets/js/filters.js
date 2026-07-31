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

  // The actual matching/ranking algorithm lives in ingredient-search.js —
  // pure, no DOM, testable directly with Node. This file only wires it to
  // the page: read ingredients off the DOM, call IS.search(), turn the
  // result into buttons.
  var IS = HTF.ingredientSearch.create(VOCABULARY);
  var fold = HTF.ingredientSearch.fold;
  var getWords = HTF.ingredientSearch.getWords;

  function hasActiveFilters() {
    return activeTags.size > 0 || activeStar !== null || activeMetaFilters.size > 0;
  }

  var rawIngredientStrings = [];
  items.forEach(function(li) {
    var rawIng = li.dataset.ingredients || '';
    rawIng.split(',').map(function(s) { return s.trim(); }).filter(Boolean).forEach(function(ing) {
      rawIngredientStrings.push(ing);
    });
  });
  var masterIngredientsList = IS.buildMasterList(rawIngredientStrings);

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
  var result = IS.search(query, masterIngredientsList);

  result.familyButtons.forEach(function(fw) {
    var label = fw + ' (all)';
    // Always a word match by construction — a family only ever forms
    // (curated or structural) when its word already starts with the
    // query, so this is never in doubt for an (all) button.
    resultsPool.appendChild(makeIngredientButton(label, label, true));
  });
  result.results.forEach(function(r) {
    resultsPool.appendChild(makeIngredientButton(r.ing, r.ing, r.hasWordMatch));
  });

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
          var activeSynonyms = IS.getSynonymWords(activeKey);
          if (activeSynonyms) {
            // Synonym (all): match any ingredient containing any synonym word
            for (var i = 0; i < ingList.length; i++) {
              var ingLower2 = ingList[i].toLowerCase();
              if (activeSynonyms.some(function(syn) { return ingLower2.indexOf(syn) !== -1; })) {
                hasMatch = true; break;
              }
            }
          } else {
            var activeWords = getWords(activeKey).map(IS.normaliseIngredientWord);
            for (var i = 0; i < ingList.length; i++) {
              var ingWords2 = getWords(ingList[i]).map(IS.normaliseIngredientWord);
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
    var activeSynonyms2 = activeKey2 ? IS.getSynonymWords(activeKey2) : null;
    var activeWords = (!activeSynonyms2 && activeKey2)
      ? getWords(activeKey2).map(IS.normaliseIngredientWord)
      : [];
    document.querySelectorAll('.recipe-list .ingredient-pill').forEach(function(pill) {
      pill.classList.remove('ingredient--matched');
      if (!activeKey2) return;
      var pillText = pill.textContent.trim().toLowerCase();
      var matches;
      if (activeSynonyms2) {
        matches = activeSynonyms2.some(function(syn) { return pillText.indexOf(syn) !== -1; });
      } else {
        var pillWords = getWords(pillText).map(IS.normaliseIngredientWord);
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
