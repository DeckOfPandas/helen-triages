document.addEventListener('DOMContentLoaded', function () {
  var activeTags = new Set();
  var activeStar = null;
  var activeIngredient = null;
  var activeMetaFilters = new Set();
  var nameQuery = ''; // 'rewrite' and/or 'proofread'
  var isSearching = false;

  var PAGE_SIZE = 20;
  var currentPage = 1;
  var showAll = false;

  // An array, not a live NodeList: shuffleRecipeList() reorders it in place
  // and re-appends in that order, so every later pass over `items` — matching,
  // pagination, the code bars — walks in whatever order is currently on
  // screen rather than the page's original load-time order.
  var items = Array.from(document.querySelectorAll('.recipe-list li'));

  // Original, unmarked-up title text per link, read once. updateTitleHighlights()
  // always rebuilds from this rather than the link's current (possibly already
  // wrapped) textContent, so re-running it on every keystroke never compounds.
  var titleLinks = Array.from(document.querySelectorAll('.recipe-title-link'));
  titleLinks.forEach(function (a) { a.dataset.titleText = a.textContent; });

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

  // The shuffle itself is pure -- assets/js/recipe-list.js, tested directly
  // with Node. This is the DOM half: re-appending in the new order.
  // appendChild on a node already in the document MOVES it rather than
  // duplicating it, so this reorders the real DOM, not a detached copy.
  function shuffleRecipeList() {
    if (!recipeList) return;
    items = HTF.recipeList.shuffle(items);
    items.forEach(function(li) { recipeList.appendChild(li); });
  }

  // Whether a row's ingredient line is ACTUALLY truncated by its line-clamp,
  // not just short. CSS has no selector for "this box's content overflowed
  // it" — mask-image can't conditionally apply itself — so this measures
  // scrollHeight against clientHeight directly and flags the ones that really
  // are cut off. Hidden rows (display:none, offsetParent null) are skipped:
  // they measure 0/0 either way, and get measured again once a filter or
  // page change makes them visible, because this runs at the end of update().
  function updateIngredientClamp() {
    document.querySelectorAll('.recipe-list .ingredient-list').forEach(function(el) {
      if (el.offsetParent === null) return;
      el.classList.toggle('is-clamped', el.scrollHeight > el.clientHeight + 1);
    });
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

  // The tape-shape treatment other active filters get (STAR/MOOD/
  // PRACTICALITIES) needs a .tag-shape slot in the markup, same as
  // _includes/filter_group.html adds for those. Ingredient buttons are all
  // built by makeIngredientButton() above with no slot at all, deliberately
  // — a shape on every one of an unbounded swarm of search results would be
  // exactly the "count is unbounded" noise .btn-ingredient--word-match's own
  // comment already argues against. Only the ONE active button (Helen:
  // "apply the same tag styling to active ingredient search tags") gets a
  // slot, added here rather than at creation time since which button ends
  // up active isn't always known yet when it's built (renderResultsPool's
  // narrow-to-one-match case sets .active on an already-built button).
  function ensureActiveIngredientShape() {
    if (!matrix) return;
    var activeBtn = matrix.querySelector('.btn-ingredient.active');
    if (!activeBtn) return;
    if (!activeBtn.querySelector('.tag-shape')) {
      var shape = document.createElement('span');
      shape.className = 'tag-shape';
      shape.setAttribute('aria-hidden', 'true');
      activeBtn.insertBefore(shape, activeBtn.firstChild);
    }
    if (window.HTF && HTF.tagShapes) HTF.tagShapes();
  }

  function updateIngredientClear() {
    if (ingredientClear) {
      // visibility, not display -- see the button's own comment in
      // food/index.html. Toggling display added/removed it from the flex
      // row entirely, so the input's rendered width jumped the instant it
      // appeared instead of the clear link calmly sitting in space that
      // was already there (Helen: "the clear link appears cutting off the
      // field rather than to the right of it").
      ingredientClear.style.visibility = (activeIngredient || (searchBox && searchBox.value.trim())) ? 'visible' : 'hidden';
    }
  }

  function escapeHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  // Wraps the substring of each recipe title that matches nameQuery in a
  // .title-hit span, same "same tag styling" idea as the ingredient pills
  // above -- Helen's stretch goal: "could the part of the title hit gain
  // the orange background and scratchy, capitalised lettering." Only the
  // MATCHED substring gets the treatment, not the whole title, so this
  // rebuilds from the original text (stashed once, above) every time
  // rather than patching whatever's currently in the DOM.
  function updateTitleHighlights() {
    titleLinks.forEach(function (a) {
      var original = a.dataset.titleText;
      if (!nameQuery) {
        a.textContent = original;
        return;
      }
      var idx = original.toLowerCase().indexOf(nameQuery);
      if (idx === -1) {
        a.textContent = original;
        return;
      }
      var before = original.slice(0, idx);
      var hit = original.slice(idx, idx + nameQuery.length);
      var after = original.slice(idx + nameQuery.length);
      a.innerHTML = escapeHtml(before) +
        '<mark class="title-hit"><span class="tag-shape" aria-hidden="true"></span>' + escapeHtml(hit) + '</mark>' +
        escapeHtml(after);
    });
    if (nameQuery && window.HTF && HTF.tagShapes) HTF.tagShapes();
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
  ensureActiveIngredientShape();
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

  function update(preservePage) {
    if (!preservePage) { currentPage = 1; showAll = false; }
    var visibleCount = 0;
    var totalPages = 1;
    var suppressList = isSearching && !hasActiveFilters();
    if (recipeList) recipeList.style.display = suppressList ? 'none' : '';

    updateTitleHighlights();

    if (!suppressList) {
      var matchingLis = [];

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

        if (visible) matchingLis.push(li);
        else li.style.display = 'none';
      });

      visibleCount = matchingLis.length;

      // The maths is pure -- assets/js/recipe-list.js -- and returns a
      // legal currentPage even if the one we asked for no longer exists
      // (a filter can narrow the results out from under whatever page you
      // were on), so it's adopted back rather than just read.
      var pageInfo = HTF.recipeList.paginate(visibleCount, currentPage, PAGE_SIZE, showAll);
      currentPage = pageInfo.currentPage;
      totalPages = pageInfo.totalPages;

      matchingLis.forEach(function(li, idx) {
        li.style.display = (idx >= pageInfo.start && idx < pageInfo.end) ? '' : 'none';
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
      if (!activeKey2) {
        // Strip any shape left from a previous match -- .ingredient-pill
        // has no default .tag-shape colour of its own (unlike .badge/
        // .btn-tag), so an orphaned slot here would render at whatever
        // colour this pill's own text is, a faint stray shape behind
        // ordinary unmatched text.
        var stale = pill.querySelector('.tag-shape');
        if (stale) stale.remove();
        return;
      }
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
      if (matches) {
        pill.classList.add('ingredient--matched');
        if (!pill.querySelector('.tag-shape')) {
          var shape = document.createElement('span');
          shape.className = 'tag-shape';
          shape.setAttribute('aria-hidden', 'true');
          pill.insertBefore(shape, pill.firstChild);
        }
      }
    });
    if (activeKey2 && window.HTF && HTF.tagShapes) HTF.tagShapes();

    var emptyMessage = document.querySelector('.recipe-list-empty');
    emptyMessage.style.display = (!suppressList && visibleCount === 0) ? 'block' : 'none';

    var searchingMessage = document.querySelector('.recipe-list-searching');
    if (searchingMessage) searchingMessage.style.display = suppressList ? 'block' : 'none';

    if (clearButton) {
      clearButton.style.visibility = (activeTags.size > 0 || activeStar || activeIngredient || activeMetaFilters.size > 0) ? 'visible' : 'hidden';
      // visibility, not display -- same reasoning as ingredientClear above.
      if (nameSearchClear) nameSearchClear.style.visibility = nameQuery ? 'visible' : 'hidden';
    }

    var recipeCountEl = document.getElementById('recipe-count');
    if (recipeCountEl && !suppressList) {
      recipeCountEl.textContent = visibleCount + (visibleCount === 1 ? ' survivor' : ' survivors');
    }

    // Hidden entirely once showAll is set, not just its prev/next disabled --
    // there's nothing left in it to do once every matching row is on screen.
    var pagination = document.querySelector('.recipe-pagination');
    if (pagination) {
      pagination.style.display = (!suppressList && totalPages > 1 && !showAll) ? 'grid' : 'none';
      var pagePrevBtn = document.getElementById('recipe-page-prev');
      var pageNextBtn = document.getElementById('recipe-page-next');
      var pageStatusEl = document.getElementById('recipe-page-status');
      if (pagePrevBtn) pagePrevBtn.disabled = currentPage <= 1;
      if (pageNextBtn) pageNextBtn.disabled = currentPage >= totalPages;
      if (pageStatusEl) pageStatusEl.textContent = 'page ' + currentPage + ' of ' + totalPages;
    }

    updateInlineLabels();
    updateIngredientClear();
    syncAriaPressed();
    updateIngredientClamp();
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
          var staleShape = target.querySelector('.tag-shape');
          if (staleShape) staleShape.remove();
        } else {
          activeIngredient = ing;
          isSearching = false;
          var rawKey = target.dataset.ingredient;
          if (searchBox) searchBox.value = rawKey.replace(' (all)', '').trim();
          resultsPool.innerHTML = '';
          resultsPool.appendChild(target);
          matrix.querySelectorAll('.btn-ingredient').forEach(function(b) { b.classList.remove('active'); });
          target.classList.add('active');
          ensureActiveIngredientShape();
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
      nameSearchClear.style.visibility = 'hidden';
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
      if (nameSearchClear) nameSearchClear.style.visibility = 'hidden';
      if (resultsPool) resultsPool.innerHTML = '';
      if (matrix) {
        matrix.querySelectorAll('.btn-tag, .btn-star, .btn-meta').forEach(function(btn) {
          btn.classList.remove('active');
        });
      }
      // Reshuffles only here, on the deliberate "clear everything at once"
      // action — not on every incidental path back to zero active filters
      // (e.g. toggling the last individual tag off), which reads as an
      // unrelated action reordering the page underneath you.
      shuffleRecipeList();
      update();
    });
  }

  var pagePrevBtn = document.getElementById('recipe-page-prev');
  var pageNextBtn = document.getElementById('recipe-page-next');
  if (pagePrevBtn) {
    pagePrevBtn.addEventListener('click', function() {
      currentPage -= 1;
      update(true);
      if (recipeList) recipeList.scrollIntoView({ block: 'start' });
    });
  }
  if (pageNextBtn) {
    pageNextBtn.addEventListener('click', function() {
      currentPage += 1;
      update(true);
      if (recipeList) recipeList.scrollIntoView({ block: 'start' });
    });
  }

  var seeAllBtn = document.getElementById('recipe-page-see-all');
  if (seeAllBtn) {
    seeAllBtn.addEventListener('click', function() {
      showAll = true;
      update(true);
    });
  }

  // Line-clamp changes from 1 line to 2 at the 600px breakpoint, so a resize
  // can flip whether a row is genuinely overflowing. Debounced: resize fires
  // continuously while dragging, and re-measuring every .ingredient-list on
  // every one of those events is wasted work for a value that only matters
  // once the drag settles.
  var resizeTimer = null;
  window.addEventListener('resize', function() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(updateIngredientClamp, 120);
  });

  // A fresh page load starts at "no filters active" too — the same state
  // "clear all" produces — so it gets the same shuffle for the same reason.
  // .recipe-list starts visibility:hidden in CSS specifically so this can run
  // before anything is shown — revealing it only now means the shuffled order
  // is what paints, not the server-rendered alphabetical order flashing first.
  shuffleRecipeList();
  update();
  if (recipeList) recipeList.style.visibility = 'visible';
});
