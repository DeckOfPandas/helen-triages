document.addEventListener('DOMContentLoaded', function () {
  var FilterState = HTF.filterState;

  /* One state object; its fields, its cleared value and both "is anything
     set" answers come from assets/js/filter-state.js. Read FIELD_SPEC there
     before adding a filter kind. clearAllFilters() reassigns it wholesale, so
     every reader must go through this variable (#52). */
  var state = FilterState.emptyState();

  /* Display text per chosen HAS TO HAVE key (#1092). Not in `state`: a
     filter's identity is the match key ("five-spice"), or two spellings of
     one ingredient would count as two. The label ("Chinese five-spice
     powder") is carried through go-back memory beside it. */
  var ingredientLabels = {};

  var PAGE_SIZE = 20;
  var currentPage = 1;
  var showAll = false;

  // An array, not a live NodeList: shuffleRecipeList() reorders it, so every
  // later pass walks the order currently on screen.
  var items = Array.from(document.querySelectorAll('.recipe-list li'));

  // The unmarked title text, read once: updateTitleHighlights() rebuilds from
  // it, never from the link's current (possibly wrapped) content.
  var titleLinks = Array.from(document.querySelectorAll('.recipe-title-link'));
  titleLinks.forEach(function (a) { a.dataset.titleText = a.textContent; });

  var matrix = document.querySelector('.controls');
  var recipeList = document.querySelector('.recipe-list');

  /* Hide the drafts (#1358). The button exists only on a local build, so
     this is null on the deployed index. A row is a draft if it wears the
     `.badge-draft` pill. Not a field of `state`; cocktail-index.js has the
     twin. */
  var draftsBtn = document.getElementById('drafts-toggle');
  var hideDrafts = false;

  /* Only the untried (DECISIONS §4): local builds only, like the drafts
     button, and composing with every filter. A row is untried if it carries
     `data-untried`. */
  var untriedBtn = document.getElementById('untried-toggle');
  var onlyUntried = false;

  // The one clear-all is the results pill's × (_includes/results-pill.html,
  // #1448): this script sets its visibility and wires its click, and
  // results-bar.js shows it whenever that visibility says there is something
  // to clear. A list, so the code below that walks it is unchanged.
  var clearButtons = [];
  var pillClear = document.querySelector('[data-results-pill-clear]');
  if (matrix && pillClear) clearButtons.push(pillClear);

  var searchBox = document.getElementById('ingredient-search-box');
  var resultsPool = document.getElementById('ingredient-results-pool');
  var ingredientClear = document.getElementById('ingredient-search-clear');
  var nameSearchBox = document.getElementById('name-search-box');
  var nameSearchClear = document.getElementById('name-search-clear');

  // LEAVE OUT, the dislike navigator (#52): a plain, always-visible section.
  var excludeBox = document.getElementById('exclude-search-box');
  var excludeClear = document.getElementById('exclude-search-clear');
  var excludePool = document.getElementById('exclude-results-pool');
  var excludeActive = document.getElementById('exclude-active');

  // --- Ingredient vocabulary: _data/food/ingredient_words.yml, emitted as JSON
  // by food/index.html. No ingredient words are written in this file.
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

  // Matching and ranking live in ingredient-search.js (pure, tested with
  // Node); this file only wires them to the page.
  var IS = HTF.ingredientSearch.create(VOCABULARY);
  var fold = HTF.ingredientSearch.fold;
  var getWords = HTF.ingredientSearch.getWords;

  /* Two predicates, and they are different questions (#248); do not merge
     them. hasNarrowingFilter(): is anything other than a half-typed
     ingredient search narrowing the list? It alone feeds suppressList.
     hasAnythingToClear(): the clear-all button's visibility, which must agree
     with what clearAllFilters() clears. Which fields each counts is on
     FIELD_SPEC in filter-state.js. */
  function hasNarrowingFilter() {
    return FilterState.hasNarrowingFilter(state);
  }

  function hasAnythingToClear() {
    return FilterState.hasAnythingToClear(state);
  }

  // DOM half of HTF.listView.shuffle: appendChild on an attached node moves it.
  function shuffleRecipeList() {
    if (!recipeList) return;
    items = HTF.listView.shuffle(items);
    items.forEach(function(li) { recipeList.appendChild(li); });
  }

  // --- Index memory (#387) ----------------------------------------------------
  // Going back to the index restores the list you left: order, filters, page,
  // scroll. Any other arrival shuffles (MANUAL §13.7). It rests on the
  // navigation type plus sessionStorage, not on bfcache, which a browser may
  // decline (a `no-store` response disqualifies the page).
  var MEMORY_KEY = 'htf-index-memory-v1';

  // Rows carry no id; the title link's href is unique and stable. By class,
  // never "the first <a>": badge links share the row (#40).
  function rowKey(li) {
    var a = li.querySelector('.recipe-title-link');
    return a ? a.getAttribute('href') : '';
  }

  var arrivedByGoingBack = FilterState.arrivedByGoingBack;

  /* Saved on pagehide, which fires on the way into bfcache too and, unlike
     `unload`, does not disqualify the page from it. Storage failures are
     swallowed in HTF.indexMemory (#686), shared with the drinks index. */
  function saveIndexMemory() {
    if (!recipeList) return;
    HTF.indexMemory.save(MEMORY_KEY, {
      order: items.map(rowKey),
      filters: FilterState.serialise(state),
      // Display text per chosen key: see ingredientLabels.
      ingredientLabels: ingredientLabels,
      page: currentPage,
      showAll: showAll,
      scrollY: window.scrollY || 0
    });
  }

  /* Returns the saved record, or null for "carry on as a fresh load": not a
     back navigation, nothing stored, or a record that does not fit. Stored
     state is untrusted input. */
  function restoreIndexMemory() {
    if (!recipeList || !arrivedByGoingBack()) return null;

    var saved = HTF.indexMemory.restore(MEMORY_KEY);
    if (!saved || !Array.isArray(saved.order)) return null;

    // Saved order first, then any row the record did not know: a recipe added
    // since belongs at the end, never silently dropped.
    var byKey = {};
    items.forEach(function (li) { byKey[rowKey(li)] = li; });
    var ordered = [];
    saved.order.forEach(function (key) {
      if (byKey[key]) { ordered.push(byKey[key]); delete byKey[key]; }
    });
    items.forEach(function (li) { if (byKey[rowKey(li)]) ordered.push(li); });
    items = ordered;
    items.forEach(function (li) { recipeList.appendChild(li); });

    state = FilterState.deserialise(saved.filters);

    /* Half-finished searches are not restored: a pool of candidates nobody
       picked is not a filter. Chosen results are, below. */
    state.isSearching = false;
    state.isExcludeSearching = false;

    if (nameSearchBox) nameSearchBox.value = state.nameQuery || '';
    if (excludeBox) excludeBox.value = '';
    // Cleared, not filled: with several entries chosen there is no one label
    // to echo. The chosen chips are rebuilt below.
    if (searchBox) searchBox.value = '';

    /* One active button per chosen ingredient, as choosing it leaves things;
       the end state is reproduced, no search is replayed. */
    ingredientLabels = (saved.ingredientLabels && typeof saved.ingredientLabels === 'object')
      ? saved.ingredientLabels : {};
    if (state.includedIngredients.size && resultsPool) {
      resultsPool.innerHTML = '';
      state.includedIngredients.forEach(function (key) {
        resultsPool.appendChild(makeIngredientButton(key, ingredientLabels[key] || key, true));
      });
      ensureActiveIngredientShapes();
    }

    currentPage = (typeof saved.page === 'number' && saved.page > 0) ? saved.page : 1;
    showAll = !!saved.showAll;
    return saved;
  }

  // While a title search is active, matching rows are grouped into the tiers
  // of HTF.listView.titleMatchTier (#63, #78) and each tier is shuffled, so no
  // recipe is stuck at the bottom of its tier. Runs on every keystroke.
  function reorderForTitleSearch() {
    if (!recipeList) return;
    var byTier = { 0: [], 1: [], 2: [], 3: [] };
    items.forEach(function(li) {
      // By class, never "the first <a>" (see rowKey).
      var title = (li.querySelector('.recipe-title-link') || {}).textContent || '';
      var tier = HTF.listView.titleMatchTier(title, state.nameQuery, fold);
      byTier[tier].push(li);
    });
    items = [].concat(
      HTF.listView.shuffle(byTier[1]),
      HTF.listView.shuffle(byTier[2]),
      HTF.listView.shuffle(byTier[3]),
      byTier[0]
    );
    items.forEach(function(li) { recipeList.appendChild(li); });
  }

  var rawIngredientStrings = [];
  items.forEach(function(li) {
    var rawIng = li.dataset.ingredients || '';
    rawIng.split(',').map(function(s) { return s.trim(); }).filter(Boolean).forEach(function(ing) {
      rawIngredientStrings.push(ing);
    });
  });
  var masterIngredientsList = IS.buildMasterList(rawIngredientStrings);

  // --- The derived ingredient index, for exclusions (#52) ---------------------
  // A second vocabulary, over data-all-ingredients (every ingredient_groups
  // item) and not data-ingredients (main_ingredients): the latter is a partial
  // hint, fine to include on and dangerous to exclude by. Each row's entries
  // go through buildMasterList as the corpus-wide list does, so the entry the
  // picker offers ("roasted peanuts") is the form the row is compared in.
  var rowExcludeEntries = new Map();
  var allDerivedEntries = [];
  items.forEach(function (li) {
    var entries = (li.dataset.allIngredients || '')
      .split('|')
      .map(function (s) { return s.trim(); })
      .filter(Boolean);
    entries.forEach(function (e) { allDerivedEntries.push(e); });
    rowExcludeEntries.set(li, IS.buildMasterList(entries));
  });
  var excludeMasterList = IS.buildMasterList(allDerivedEntries);

  var FAMILY_SUFFIX = FilterState.FAMILY_SUFFIX;

  /* IS.entriesMatchKey reads the vocabulary, so it lives on the instance. It
     is the matcher handed to FilterState.excludesRow and rowMatchesFilters. */
  var entriesMatchKey = IS.entriesMatchKey;

  /* The rule is FilterState.excludesRow: set membership, never substring, so
     "peas" does not take the peanut butter with it. This is the DOM half:
     which entries the row has. */
  function rowIsExcluded(li) {
    if (!state.excludedIngredients.size) return false;
    return FilterState.excludesRow(
      rowExcludeEntries.get(li) || [], state.excludedIngredients, entriesMatchKey
    );
  }

  function makeIngredientButton(key, label, wordMatch) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn-tag btn-ingredient';
    if (state.includedIngredients.has(key)) btn.classList.add('active');
    if (wordMatch) btn.classList.add('btn-ingredient--word-match');
    btn.dataset.ingredient = key;
    btn.textContent = label;
    if (state.includedIngredients.has(key)) markIngredientChosen(btn);
    return btn;
  }

  /* A chosen HAS TO HAVE chip carries its own x, in a span of its own so
     nothing reading the chip's label picks it up; aria-hidden, and the
     accessible name says what a click does. Still one button. */
  function markIngredientChosen(btn) {
    if (btn.querySelector('.btn-ingredient-x')) return;
    btn.setAttribute('aria-label', 'stop requiring ' + btn.textContent.trim());
    var x = document.createElement('span');
    x.className = 'btn-ingredient-x';
    x.setAttribute('aria-hidden', 'true');
    x.textContent = ' \u00d7';
    btn.appendChild(x);
  }

  function unmarkIngredientChosen(btn) {
    var x = btn.querySelector('.btn-ingredient-x');
    if (x) x.remove();
    btn.removeAttribute('aria-label');
  }

  // Only ACTIVE ingredient buttons get a .tag-shape slot (the tape shape the
  // other active filters wear): a shape on every search result would be noise.
  // Added here, not at creation, because a button can become active after it
  // is built. Several can be active at once (#1092).
  function ensureActiveIngredientShapes() {
    if (!matrix) return;
    var any = false;
    matrix.querySelectorAll('.btn-ingredient.active').forEach(function (activeBtn) {
      any = true;
      if (!activeBtn.querySelector('.tag-shape')) {
        var shape = document.createElement('span');
        shape.className = 'tag-shape';
        shape.setAttribute('aria-hidden', 'true');
        activeBtn.insertBefore(shape, activeBtn.firstChild);
      }
    });
    if (any && window.HTF && HTF.tagShapes) HTF.tagShapes();
  }

  function updateIngredientClear() {
    if (ingredientClear) {
      // visibility, not display: toggling display adds and removes it from
      // the flex row, and the input's width jumps.
      ingredientClear.style.visibility =
        (state.includedIngredients.size || (searchBox && searchBox.value.trim())) ? 'visible' : 'hidden';
    }
  }

  // Wraps the part of each title that matches state.nameQuery in
  // mark.title-hit. Rebuilt from the stashed original text every time.
  // Folded one character at a time, so an index into it is an index into the
  // original and the highlight lands on the letters that matched. A character
  // whose fold would change length is kept as it is (#1386).
  function foldInPlace(str) {
    var out = '';
    for (var i = 0; i < str.length; i++) {
      var ch = str.charAt(i).toLowerCase();
      var folded = HTF.ingredientSearch.fold(ch);
      out += folded.length === 1 ? folded : ch;
    }
    return out;
  }

  function updateTitleHighlights() {
    titleLinks.forEach(function (a) {
      var original = a.dataset.titleText;
      if (!state.nameQuery) {
        a.textContent = original;
        return;
      }
      // Composed first: a decomposed é is two characters and its accent alone
      // folds to nothing. NFC looks the same on screen.
      original = original.normalize('NFC');
      var idx = foldInPlace(original).indexOf(state.nameQuery);
      if (idx === -1) {
        a.textContent = original;
        return;
      }
      var before = original.slice(0, idx);
      var hit = original.slice(idx, idx + state.nameQuery.length);
      var after = original.slice(idx + state.nameQuery.length);
      a.innerHTML = HTF.escapeHtml(before) +
        '<mark class="title-hit"><span class="tag-shape" aria-hidden="true"></span>' + HTF.escapeHtml(hit) + '</mark>' +
        HTF.escapeHtml(after);
    });
    if (state.nameQuery && window.HTF && HTF.tagShapes) HTF.tagShapes();
  }






function renderResultsPool() {
  if (!searchBox || !resultsPool) return;
  var query = fold(searchBox.value.trim().toLowerCase());
  resultsPool.innerHTML = '';
  state.isSearching = !!query;

  /* Chosen entries stay visible, and clickable to remove, whatever is typed
     (#1092): typing never clears a requirement. */
  state.includedIngredients.forEach(function (key) {
    resultsPool.appendChild(makeIngredientButton(key, ingredientLabels[key] || key, true));
  });

  if (!query) {
    ensureActiveIngredientShapes();
    update();
    return;
  }
  var result = IS.search(query, masterIngredientsList);

  result.familyButtons.forEach(function(fw) {
    var label = fw + ' (all)';
    // Already shown above as a chosen entry -- never offered twice.
    if (state.includedIngredients.has(label)) return;
    // A family only forms when its word starts with the query: a word match.
    resultsPool.appendChild(makeIngredientButton(label, label, true));
  });
  result.results.forEach(function(r) {
    // No bare "chicken" beside "chicken (all)" (#51); a multi-word entry
    // like "chicken breast" still shows.
    if (result.familyButtons.indexOf(fold(r.ing.trim().toLowerCase())) !== -1) return;
    // Already shown above as a chosen entry -- never offered twice.
    if (state.includedIngredients.has(r.ing)) return;
    resultsPool.appendChild(makeIngredientButton(r.ing, r.label || r.ing, r.hasWordMatch));
  });

  // Auto-select on a unique match, where unique means among what is not
  // already chosen.
  var freshButtons = Array.prototype.filter.call(
    resultsPool.querySelectorAll('.btn-ingredient'),
    function (b) { return !b.classList.contains('active'); }
  );
  if (freshButtons.length === 1) {
    var onlyBtn = freshButtons[0];
    var onlyKey = onlyBtn.dataset.ingredient;
    state.includedIngredients.add(onlyKey);
    ingredientLabels[onlyKey] = onlyBtn.textContent;
    onlyBtn.classList.add('active');
    markIngredientChosen(onlyBtn);
    state.isSearching = false;
  }
  ensureActiveIngredientShapes();
  update();
  updateIngredientClear();
}


  


  



  // --- LEAVE OUT, the dislike navigator (#52) --------------------------------

  /* `wordMatch` is a word-PREFIX match, as on makeIngredientButton (#390):
     "pas" marks "anchovy paste" and not "antipasti vegetables", which is in
     the list on a substring match, nor the family members the vocabulary
     brought along. */
  function makeExcludeButton(value, label, wordMatch) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn-tag btn-exclude';
    if (wordMatch) btn.classList.add('btn-exclude--word-match');
    btn.dataset.exclude = value;
    btn.textContent = label;
    return btn;
  }

  /* The name and the × are separate elements so the stylesheet can strike
     only .btn-exclude-label. Still one button; the × is not a second control. */
  function makeActiveExcludeButton(value) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn-tag btn-exclude btn-exclude--active';
    btn.dataset.exclude = value;
    btn.setAttribute('aria-label', 'stop leaving out ' + value);

    var label = document.createElement('span');
    label.className = 'btn-exclude-label';
    label.textContent = value;
    btn.appendChild(label);

    btn.appendChild(document.createTextNode(' ×'));
    return btn;
  }

  /* Fuzzy to find, exact to filter: "pea" offers peas, peanut butter and
     pearl barley, and the one picked is matched as a whole entry
     (rowIsExcluded). */
  function renderExcludePool() {
    if (!excludeBox || !excludePool) return;
    var query = fold(excludeBox.value.trim().toLowerCase());
    excludePool.innerHTML = '';
    if (excludeClear) excludeClear.style.visibility = query ? 'visible' : 'hidden';
    // Set in step with the pool, so the clear button appears as soon as a
    // half-finished search puts results on screen (#274).
    state.isExcludeSearching = !!query;
    if (!query) {
      update();
      return;
    }

    var result = IS.search(query, excludeMasterList);
    result.familyButtons.forEach(function (fw) {
      var label = fw + FAMILY_SUFFIX;
      // A family is a word match by construction, as in renderResultsPool.
      excludePool.appendChild(makeExcludeButton(label, label, true));
    });
    result.results.forEach(function (r) {
      // No bare "chicken" beside "chicken (all)" (#51).
      if (result.familyButtons.indexOf(fold(r.ing.trim().toLowerCase())) !== -1) return;
      excludePool.appendChild(makeExcludeButton(r.ing, r.label || r.ing, r.hasWordMatch));
    });
    update();
  }

  /* What is being left out, painted from state and not at click time:
     clear-all reassigns the state object and never touches this markup. The
     line reads "hiding peas" (#1088): about the ingredient, with no count and
     no claim about what a recipe is free of. */
  function renderExcludeActive() {
    if (!excludeActive) return;
    excludeActive.innerHTML = '';
    if (!state.excludedIngredients.size) return;

    /* No visible "leaving out" label (#363); each pill's aria-label keeps the
       words, because a screen reader gets no strikethrough. */
    var names = [];
    state.excludedIngredients.forEach(function (value) {
      // The line drops the "(all)" that the pill keeps as the control's name.
      names.push(value.replace(FAMILY_SUFFIX, ''));
      excludeActive.appendChild(makeActiveExcludeButton(value));
    });

    // The class keeps its name though the line no longer counts: it is the
    // hook food/_search.scss styles.
    var count = document.createElement('span');
    count.className = 'exclude-count';
    count.textContent = 'hiding ' + names.join(' and ');
    excludeActive.appendChild(count);
  }

  // Multi-select: cooking for someone who hates peas AND coriander.
  function toggleExcluded(value) {
    if (!value) return;
    if (state.excludedIngredients.has(value)) {
      state.excludedIngredients.delete(value);
    } else {
      state.excludedIngredients.add(value);
      // Emptied on a pick, ready for the next thing to leave out.
      if (excludeBox) excludeBox.value = '';
      if (excludePool) excludePool.innerHTML = '';
      if (excludeClear) excludeClear.style.visibility = 'hidden';
      state.isExcludeSearching = false;
    }
    update();
  }


  if (excludeBox) {
    excludeBox.addEventListener('input', renderExcludePool);
  }

  if (excludeClear) {
    excludeClear.addEventListener('click', function () {
      // Clears the SEARCH, not the exclusions -- those come off one at a time
      // by their own pills, or all at once with clear all.
      if (excludeBox) excludeBox.value = '';
      if (excludePool) excludePool.innerHTML = '';
      excludeClear.style.visibility = 'hidden';
      state.isExcludeSearching = false;
      if (excludeBox) excludeBox.focus();
      update();
    });
  }

  if (searchBox) {
    searchBox.addEventListener('input', renderResultsPool);
  }

  if (ingredientClear) {
    ingredientClear.addEventListener('click', function() {
      // Clears the SEARCH, not the choices (#1092): an empty box repaints
      // exactly the chosen chips.
      if (searchBox) searchBox.value = '';
      renderResultsPool();
    });
  }

  // aria-pressed is synced from .active here, in one place, so the visual and
  // the announced state cannot disagree.
  function syncAriaPressed() {
    if (!matrix) return;
    matrix.querySelectorAll('.btn-star, .btn-tag').forEach(function(btn) {
      btn.setAttribute('aria-pressed', btn.classList.contains('active') ? 'true' : 'false');
    });
  }

  // .active is painted from state, never at a toggle site: a row badge (#40)
  // and a query string change state with no button to reach for.
  // .btn-ingredient is skipped: it also wears .btn-tag, but its state is
  // state.includedIngredients, kept where the button is built and clicked.
  function syncFilterButtons() {
    if (!matrix) return;
    matrix.querySelectorAll('.btn-tag').forEach(function(btn) {
      if (btn.classList.contains('btn-ingredient')) return;
      btn.classList.toggle('active', state.tags.has(btn.dataset.tag));
    });
    matrix.querySelectorAll('.btn-star').forEach(function(btn) {
      btn.classList.toggle('active', state.star === btn.dataset.star);
    });
  }

  // The toggles change state and call update(); a badge click is the same
  // action. Button classes are syncFilterButtons()' job.
  function toggleTag(value) {
    if (!value) return;
    if (state.tags.has(value)) state.tags.delete(value);
    else state.tags.add(value);
    update();
  }

  // Single-select, unlike tags: picking a second star replaces the first
  // rather than adding to it, and picking the active one again clears it.
  function toggleStar(value) {
    if (!value) return;
    state.star = (state.star === value) ? null : value;
    update();
  }

  function update(preservePage) {
    if (!preservePage) { currentPage = 1; showAll = false; }
    var visibleCount = 0;
    var totalPages = 1;
    var suppressList = state.isSearching && !hasNarrowingFilter();
    if (recipeList) recipeList.style.display = suppressList ? 'none' : '';

    updateTitleHighlights();

    // Matching runs even while the list is suppressed, so the count reflects
    // the filters in effect (#60). Only row visibility and paging are gated.
    var matchingLis = [];

    items.forEach(function(li) {
      /* The row as FilterState.rowMatchesFilters needs it (#506).
         `titleFolded` is built only when asked for: a lookup per row per
         update. */
      var row = {
        tags: (li.dataset.tags || '').split(',').filter(Boolean),
        star: li.dataset.star || '',
        starAlso: (li.dataset.starAlso || '').split(',').filter(Boolean),
        ingredients: (li.dataset.ingredients || '').split(',').map(function(s) { return s.trim(); }),
        titleFolded: state.nameQuery
          ? HTF.ingredientSearch.fold(
            ((li.querySelector('.recipe-title-link') || {}).textContent || '').toLowerCase())
          : ''
      };

      var visible = FilterState.rowMatchesFilters(row, state, entriesMatchKey);

      /* Last: above is what you asked for, this is what you can't serve. */
      if (visible && rowIsExcluded(li)) visible = false;

      /* The local-only drafts switch, #1358. */
      if (visible && hideDrafts && li.querySelector('.badge-draft')) visible = false;
      if (visible && onlyUntried && !li.hasAttribute('data-untried')) visible = false;

      if (visible) matchingLis.push(li);
      else if (!suppressList) li.style.display = 'none';
    });

    visibleCount = matchingLis.length;

    if (!suppressList) {
      // paginate() returns a legal currentPage when a filter has narrowed the
      // results out from under the one asked for, so it is adopted back.
      var pageInfo = HTF.listView.paginate(visibleCount, currentPage, PAGE_SIZE, showAll);
      currentPage = pageInfo.currentPage;
      totalPages = pageInfo.totalPages;

      matchingLis.forEach(function(li, idx) {
        li.style.display = (idx >= pageInfo.start && idx < pageInfo.end) ? '' : 'none';
      });
    }

    // Matched on the badge's own data-tag/data-star, not its text, which
    // could not tell a MOOD badge from a STAR one. Meta and draft badges
    // carry neither and never match.
    document.querySelectorAll('.recipe-list .badge').forEach(function(badge) {
      var badgeTag = badge.dataset.tag;
      var badgeStar = badge.dataset.star;
      badge.classList.remove('badge--matched');
      if ((badgeTag && state.tags.has(badgeTag)) || (badgeStar && state.star === badgeStar)) {
        badge.classList.add('badge--matched');
      }
    });

    // A pill lights up if it matches ANY chosen entry (#1092): a visual aid,
    // not the AND requirement, which is FilterState.includesRow's.
    var activeKeys2 = [];
    state.includedIngredients.forEach(function (k) {
      activeKeys2.push(String(k).replace(' (all)', '').trim());
    });
    document.querySelectorAll('.recipe-list .ingredient-pill').forEach(function(pill) {
      pill.classList.remove('ingredient-pill--matched');
      if (!activeKeys2.length) {
        // Strip a shape left from a previous match: .ingredient-pill has no
        // .tag-shape colour of its own, so an orphan would show faintly.
        var stale = pill.querySelector('.tag-shape');
        if (stale) stale.remove();
        return;
      }
      var pillText = pill.textContent.trim().toLowerCase();
      var pillWords = null;
      var matches = activeKeys2.some(function (activeKey2) {
        var activeSynonyms2 = IS.getSynonymWords(activeKey2);
        if (activeSynonyms2) {
          return activeSynonyms2.some(function(syn) { return pillText.indexOf(syn) !== -1; });
        }
        if (!pillWords) pillWords = getWords(pillText).map(IS.normaliseIngredientWord);
        var activeWords = getWords(activeKey2).map(IS.normaliseIngredientWord);
        return activeWords.every(function(aw) {
          return pillWords.some(function(pw) { return pw.indexOf(aw) !== -1; });
        });
      });
      if (matches) {
        pill.classList.add('ingredient-pill--matched');
        if (!pill.querySelector('.tag-shape')) {
          var shape = document.createElement('span');
          shape.className = 'tag-shape';
          shape.setAttribute('aria-hidden', 'true');
          pill.insertBefore(shape, pill.firstChild);
        }
      }
    });
    if (activeKeys2.length && window.HTF && HTF.tagShapes) HTF.tagShapes();

    // Null-guarded: a throw here would silently skip everything below it.
    var emptyMessage = document.querySelector('.recipe-list-empty');
    if (emptyMessage) {
      emptyMessage.style.display = (!suppressList && visibleCount === 0) ? 'block' : 'none';
    }

    var searchingMessage = document.querySelector('.recipe-list-searching');
    if (searchingMessage) searchingMessage.style.display = suppressList ? 'block' : 'none';

    if (clearButtons.length) {
      var clearVisibility = hasAnythingToClear() ? 'visible' : 'hidden';
      clearButtons.forEach(function (btn) { btn.style.visibility = clearVisibility; });
    }
    // visibility, not display -- same reasoning as ingredientClear above.
    if (matrix && nameSearchClear) nameSearchClear.style.visibility = state.nameQuery ? 'visible' : 'hidden';

    /* Number and word are two spans, so the digits can take the label face
       (`.results-count-number`); results-bar.js mirrors both. The fallback
       keeps a template or fixture with only the outer element painting.
       "recipes" until something narrows the list, then "survivors" (Helen's
       ruling, DECISIONS §13): the joke needs a filter to land. */
    var recipeCountEl = document.getElementById('recipe-count');
    if (recipeCountEl) {
      var countNoun = hasAnythingToClear() ? 'survivor' : 'recipe';
      var survivorWord = visibleCount === 1 ? countNoun : countNoun + 's';
      var recipeCountN = document.getElementById('recipe-count-n');
      var recipeCountWord = document.getElementById('recipe-count-word');
      if (recipeCountN && recipeCountWord) {
        recipeCountN.textContent = visibleCount;
        recipeCountWord.textContent = survivorWord;
      } else {
        recipeCountEl.textContent = visibleCount + ' ' + survivorWord;
      }
    }

    // Hidden entirely under showAll: nothing left in it to do.
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

    // Order matters between these two: syncAriaPressed() reads the .active
    // class syncFilterButtons() has just painted.
    syncFilterButtons();
    updateInlineLabels();
    updateIngredientClear();
    renderExcludeActive();
    syncAriaPressed();
    syncAddressBar();
  }

  /* The address bar says what is chosen (#1462 C3), so a reload or a copied
     link shows the same list; arrival reads it back in applyQueryString.
     Off until startup has read the query it arrived with, which every
     update() before then would otherwise overwrite. `?into=` (the list being
     filled, shortlist-picker.js) is carried through untouched. */
  var addressBarLive = false;
  var arrivedInto = (/[?&]into=([a-z0-9]+)/.exec(location.search) || [])[1] || '';
  function setList(set) {
    var list = [];
    set.forEach(function (v) { list.push(v); });
    return list;
  }
  function syncAddressBar() {
    if (!addressBarLive) return;
    FilterState.replaceQuery(FilterState.buildQuery([
      ['star', state.star ? [state.star] : []],
      ['tag', setList(state.tags)],
      ['ing', setList(state.includedIngredients)],
      ['out', setList(state.excludedIngredients)],
      ['q', [nameSearchBox ? nameSearchBox.value : '']],
      ['into', arrivedInto ? [arrivedInto] : []]
    ]));
  }

  function updateInlineLabels() {
    var starRow = document.querySelector('.category.category--star');
    if (starRow && starRow.querySelector('.btn-clear-inline')) {
      starRow.querySelector('.btn-clear-inline').style.display = state.star ? 'inline-block' : 'none';
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
      // A chosen HAS TO HAVE chip holds spans now (its x, its tape slot), and
      // a click on one of those is a click on the chip.
      var ingredientBtn = target.closest && target.closest('.btn-ingredient');
      if (ingredientBtn) target = ingredientBtn;

      /* The exclude section is claimed whole, first: its buttons wear
         .btn-tag for looks and would otherwise toggle a MOOD tag called
         "peas". */
      if (target.closest && target.closest('.search--exclude')) {
        if (target.classList.contains('btn-exclude')) toggleExcluded(target.dataset.exclude);
        return;
      }

      if (target.classList.contains('btn-tag') && !target.classList.contains('btn-ingredient')) {
        toggleTag(target.dataset.tag);
        return;
      }

      if (target.classList.contains('btn-star')) {
        toggleStar(target.dataset.star);
        return;
      }

      if (target.classList.contains('btn-clear-inline')) {
        var row = target.closest('.category');
        if (row) {
          if (row.classList.contains('category--star')) {
            state.star = null;
          } else {
            row.querySelectorAll('.btn-tag').forEach(function(b) {
              state.tags.delete(b.dataset.tag);
            });
          }
          update();
        }
        return;
      }

      if (target.classList.contains('btn-ingredient')) {
        var ing = target.dataset.ingredient;
        if (state.includedIngredients.has(ing)) {
          // Remove just this one requirement (#1092).
          state.includedIngredients.delete(ing);
          delete ingredientLabels[ing];
          target.classList.remove('active');
          unmarkIngredientChosen(target);
          var staleShape = target.querySelector('.tag-shape');
          if (staleShape) staleShape.remove();
        } else {
          // Another requirement: AND, not replace (#1092).
          state.includedIngredients.add(ing);
          // The label the button SHOWS, not its match key, recorded now: the
          // box may hold a different search by the time it is next needed.
          ingredientLabels[ing] = target.textContent.replace(' (all)', '').trim();
          /* Choosing one clears the search, as LEAVE OUT does: with an empty
             box renderResultsPool() draws the chosen chips and nothing else. */
          if (searchBox) searchBox.value = '';
          renderResultsPool();
          updateIngredientClear();
          return;
        }
        state.isSearching = !!(searchBox && searchBox.value.trim());
        update();
        return;
      }
    });
  }

  // A badge on a recipe row does exactly what its filter's own button does
  // (#40). Delegated: there are hundreds of badges, and paging hides rows, it
  // does not remove them. preventDefault() because the href is a real link
  // (_includes/recipe_badges.html) and following it would reload the index.
  // A modified or non-primary click is left alone, so it opens the link in a
  // new tab as any link does.
  if (recipeList) {
    recipeList.addEventListener('click', function(e) {
      if (!e.target || !e.target.closest) return;
      if (e.button || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
      // closest(): a badge holds a .tag-shape span, so a click can land on a
      // descendant.
      var badge = e.target.closest('.badge[data-tag], .badge[data-star]');
      if (!badge || !recipeList.contains(badge)) return;
      e.preventDefault();
      if (badge.dataset.star) toggleStar(badge.dataset.star);
      else toggleTag(badge.dataset.tag);
    });
  }

  if (nameSearchBox) {
    nameSearchBox.addEventListener('input', function() {
      state.nameQuery = HTF.ingredientSearch.fold(nameSearchBox.value.trim().toLowerCase());
      // A cleared query reshuffles, so rows do not stay in the last search's
      // tiers.
      if (state.nameQuery) {
        reorderForTitleSearch();
      } else {
        shuffleRecipeList();
      }
      update();
    });
  }

  if (nameSearchClear) {
    nameSearchClear.addEventListener('click', function() {
      state.nameQuery = '';
      nameSearchBox.value = '';
      nameSearchClear.style.visibility = 'hidden';
      shuffleRecipeList();
      update();
    });
  }

  /* The boxes and pools that are DOM, not state, which clear-all empties. */
  function resetFilterControls() {
    if (searchBox) searchBox.value = '';
    if (nameSearchBox) nameSearchBox.value = '';
    if (nameSearchClear) nameSearchClear.style.visibility = 'hidden';
    if (resultsPool) resultsPool.innerHTML = '';
    // The exclude picker's half-typed search; the exclusions are state.
    if (excludeBox) excludeBox.value = '';
    if (excludePool) excludePool.innerHTML = '';
    if (excludeClear) excludeClear.style.visibility = 'hidden';
  }

  if (clearButtons.length) {
    var clearAllFilters = function() {
      // One assignment (#52): emptyState() walks the FIELD_SPEC that
      // hasAnythingToClear() walks, so the two cannot drift.
      state = FilterState.emptyState();
      resetFilterControls();
      // Reshuffles only on this deliberate action, never on an incidental
      // return to zero filters, which would reorder the page under the reader.
      shuffleRecipeList();
      // update() empties the address bar's query with the filters.
      update();
    };
    clearButtons.forEach(function (btn) {
      btn.addEventListener('click', clearAllFilters);
    });
  }

  /* #1358. The label names what a press will do, and `is-on` says the list is
     currently narrowed. */
  if (draftsBtn) {
    draftsBtn.hidden = false;
    draftsBtn.addEventListener('click', function () {
      hideDrafts = !hideDrafts;
      draftsBtn.textContent = hideDrafts ? 'show drafts' : 'hide drafts';
      draftsBtn.classList.toggle('is-on', hideDrafts);
      draftsBtn.setAttribute('aria-pressed', hideDrafts ? 'true' : 'false');
      update();
    });
  }

  /* A filter's label, not an action's: `is-on` and aria-pressed carry the
     state, as on a filter chip. */
  if (untriedBtn) {
    untriedBtn.hidden = false;
    untriedBtn.addEventListener('click', function () {
      onlyUntried = !onlyUntried;
      untriedBtn.classList.toggle('is-on', onlyUntried);
      untriedBtn.setAttribute('aria-pressed', onlyUntried ? 'true' : 'false');
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

  // `/food/?star=lamb&tag=soup` arrives filtered (#40). The grammar is
  // filter-state.js's; the validation is here, where the offered buttons are.
  // Values are compared against each button's dataset, never built into an
  // attribute selector: text off a URL would need escaping. A value matching
  // no button is dropped in silence, so a stale link lands on a working index.
  (function applyQueryString() {
    if (!matrix) return;
    var wanted = FilterState.parseQuery(location.search);

    function isOffered(selector, datasetKey, value) {
      var found = false;
      matrix.querySelectorAll(selector).forEach(function(btn) {
        if (btn.classList.contains('btn-ingredient')) return;
        if (btn.dataset[datasetKey] === value) found = true;
      });
      return found;
    }

    wanted.tag.forEach(function(value) {
      if (isOffered('.btn-tag', 'tag', value)) state.tags.add(value);
    });

    // Single-select: the last star NAMED IN THE URL wins, so this iterates
    // the parsed list, not the buttons.
    wanted.star.forEach(function(value) {
      if (isOffered('.btn-star', 'star', value)) state.star = value;
    });

    /* `?ing=` (#1050, #1462 C3), from the search-for-anything box or the
       address bar. Each value in turn goes into HAS TO HAVE and the pool is
       painted as a keystroke would paint it, which chooses a unique result.
       With several, the button whose name IS the word is clicked, so the
       choice takes the click handler's path. With none, the pool stays for
       the reader to pick from, until the next value replaces the text. */
    if (wanted.ing.length && searchBox && resultsPool) {
      wanted.ing.forEach(function (wantedIng) {
        // A family chip is searched by its word: "(all)" is the button's, not
        // the reader's.
        searchBox.value = FilterState.isFamilyValue(wantedIng)
          ? FilterState.familyKey(wantedIng) : wantedIng;
        renderResultsPool();
        var wantedKey = fold(wantedIng.trim().toLowerCase());
        var buttons = Array.prototype.slice.call(resultsPool.querySelectorAll('.btn-ingredient'));
        // The button's own key first, so "garlic (all)" is never taken for
        // a bare "garlic" whose label reads the same.
        var exact = buttons.filter(function (btn) {
          return fold(String(btn.dataset.ingredient || '').toLowerCase()) === wantedKey;
        })[0] || buttons.filter(function (btn) {
          return fold(String(btn.textContent || '').replace(' (all)', '').trim().toLowerCase()) === wantedKey;
        })[0] || null;
        // Not when auto-select already chose it: a click on an active button
        // removes it (#1092).
        if (exact && !exact.classList.contains('active') && typeof exact.click === 'function') {
          exact.click();
        }
      });
    }

    /* `?out=` (#1462 C3): LEAVE OUT, an entry the picker offers or a family
       it would offer, compared whole. Anything else is dropped. */
    wanted.out.forEach(function (value) {
      var offered = excludeMasterList.indexOf(value) !== -1;
      if (!offered && FilterState.isFamilyValue(value)) {
        var key = FilterState.familyKey(value);
        offered = IS.search(key, excludeMasterList).familyButtons.indexOf(fold(key.toLowerCase())) !== -1;
      }
      if (offered) state.excludedIngredients.add(value);
    });
  })();

  // A fresh load starts shuffled, filtered or not, so no recipe is stuck at
  // the bottom. .recipe-list starts visibility:hidden in CSS so the shuffled
  // order is the first one painted. Arriving by going back restores the list
  // you left instead (#387).
  var restored = restoreIndexMemory();
  if (!restored) shuffleRecipeList();

  /* `?q=` (#1024), from the search box: exactly what typing into the name
     box does. After the memory and the shuffle, because a name just typed is
     a fresh instruction. */
  var arrivedName = FilterState.parseName(location.search);
  if (arrivedName && nameSearchBox) {
    nameSearchBox.value = arrivedName;
    state.nameQuery = HTF.ingredientSearch.fold(arrivedName.toLowerCase());
    reorderForTitleSearch();
    restored = null;
  }

  addressBarLive = true;
  update(!!restored);          // preserve the restored page number
  if (recipeList) recipeList.style.visibility = 'visible';

  // After the reveal, so the page has its real height to scroll within.
  if (restored && typeof restored.scrollY === 'number') {
    window.scrollTo(0, restored.scrollY);
  }

  /* Arriving at a fragment (`#results`, `#filter-star`, ...; #1050, #1057):
     the browser jumped once against the unrevealed, unfiltered page, so the
     scroll is repeated after the reveal. Not on a back navigation, where the
     remembered scroll is the truer answer. */
  if (!restored && location.hash && location.hash.length > 1) {
    var target = document.getElementById(location.hash.slice(1));
    if (target && typeof target.scrollIntoView === 'function') {
      target.scrollIntoView({ block: 'start' });
    }
  }

  window.addEventListener('pagehide', saveIndexMemory);
});
