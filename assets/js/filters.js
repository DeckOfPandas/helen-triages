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

  /* The shortlisted-only button (#546) sits on the results heading, not in
     the matrix. It ships `hidden` and is revealed below. */
  var shortlistOnlyBtn = document.getElementById('shortlist-only');

  /* Hide the drafts (#1358). The button exists only on a local build, so
     this is null on the deployed index. A row is a draft if it wears the
     `.badge-draft` pill. Not a field of `state`; cocktail-index.js has the
     twin. */
  var draftsBtn = document.getElementById('drafts-toggle');
  var hideDrafts = false;

  /* A shortlist someone sent, `?shortlist=slug,slug` (#1093): opening the
     link shows the list and saves none of it. It is the shortlist view with a
     different answer to "is this row on it": `state.shortlisted` is true, so
     any filter takes the view off (#918) and update() drops this list when it
     does. Not in `state`, so the back-memory never carries a stranger's list
     into this browser's next visit. null when no shared list is showing. */
  var sharedKeys = null;
  var sharedUnmatched = [];
  var sharedNote = document.querySelector('[data-shared-shortlist]');
  // Top and bottom of the matrix (#67), kept in step through clearButtons.
  var clearButtons = [];
  if (matrix) {
    var clearBtnTop = document.createElement('button');
    clearBtnTop.type = 'button';
    clearBtnTop.className = 'btn-clear';
    clearBtnTop.textContent = '× clear all';
    matrix.insertBefore(clearBtnTop, matrix.firstChild);
    clearButtons.push(clearBtnTop);

    var clearBtnBottom = document.createElement('button');
    clearBtnBottom.type = 'button';
    clearBtnBottom.className = 'btn-clear btn-clear--bottom';
    clearBtnBottom.textContent = '× clear all';
    matrix.appendChild(clearBtnBottom);
    clearButtons.push(clearBtnBottom);
  }

  // A third, inside the empty-list line (#1093), so it hides with it.
  var emptyMessageEl = document.querySelector('.recipe-list-empty');
  if (emptyMessageEl) {
    var clearBtnEmpty = document.createElement('button');
    clearBtnEmpty.type = 'button';
    clearBtnEmpty.className = 'btn-clear btn-clear--empty';
    clearBtnEmpty.textContent = '× clear all';
    emptyMessageEl.appendChild(clearBtnEmpty);
    clearButtons.push(clearBtnEmpty);
  }

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

  /* The shortlisted-only button (#546) is outside `.controls`, so it is
     painted from state here, class and aria-pressed together. */
  function syncShortlistOnly() {
    if (!shortlistOnlyBtn) return;
    // `is-on`, the shortlist controls' state class on both sites, not the
    // matrix's `.active`. A shared list is not YOUR shortlist, so the button
    // is not on while one shows (#1093).
    var own = !!state.shortlisted && !sharedKeys;
    shortlistOnlyBtn.classList.toggle('is-on', own);
    shortlistOnlyBtn.setAttribute('aria-pressed', own ? 'true' : 'false');
  }

  /* The note over a shared list, and its "keep these" (#1342). */
  function syncSharedNote() {
    if (!sharedNote) return;
    sharedNote.hidden = !sharedKeys;
    if (!sharedKeys) return;
    var text = sharedNote.querySelector('[data-shared-shortlist-text]');
    if (text) {
      text.textContent = 'a shared shortlist (' + sharedKeys.length + ')' +
        (sharedUnmatched.length ? '; not found: ' + sharedUnmatched.join(', ') : '');
    }
    var keep = sharedNote.querySelector('[data-shared-shortlist-keep]');
    if (keep) keep.hidden = sharedKeys.length === 0;
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
    /* The shortlist view gives way to any other filter (#918): every handler
       that sets a field ends in update(), so this line is the whole rule. */
    FilterState.reconcileShortlistView(state);
    if (!state.shortlisted) { sharedKeys = null; sharedUnmatched = []; }
    syncSharedNote();
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
         `shortlisted` and `titleFolded` are built only when asked for: each is
         a lookup per row per update. `shortlisted` is the one fact not on a
         data- attribute: it is in this browser's localStorage (#546). */
      var row = {
        tags: (li.dataset.tags || '').split(',').filter(Boolean),
        star: li.dataset.star || '',
        starAlso: (li.dataset.starAlso || '').split(',').filter(Boolean),
        ingredients: (li.dataset.ingredients || '').split(',').map(function(s) { return s.trim(); }),
        shortlisted: state.shortlisted
          ? (sharedKeys
            ? sharedKeys.indexOf(li.dataset.url || '') !== -1
            : HTF.shortlist.has(li.dataset.url || ''))
          : false,
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
      // visibility, not display -- same reasoning as ingredientClear above.
      if (nameSearchClear) nameSearchClear.style.visibility = state.nameQuery ? 'visible' : 'hidden';
    }

    /* Number and word are two spans, so the digits can take the label face
       (`.results-count-number`); results-bar.js mirrors both. The fallback
       keeps a template or fixture with only the outer element painting. */
    var recipeCountEl = document.getElementById('recipe-count');
    if (recipeCountEl) {
      var survivorWord = visibleCount === 1 ? 'survivor' : 'survivors';
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
    syncShortlistOnly();
    /* Unconditional (#801): the list must disappear when the filter goes off
       and lose a recipe un-shortlisted while it is on. */
    renderShoppingList();
    updateInlineLabels();
    updateIngredientClear();
    renderExcludeActive();
    syncAriaPressed();
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

  /* The boxes and pools that are DOM, not state. Shared by clear-all and the
     shortlist button (#918), so the two cannot disagree about which exist. */
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
      update();
    };
    clearButtons.forEach(function (btn) {
      btn.addEventListener('click', clearAllFilters);
    });
  }

  /* --- The shopping list (#801) ----------------------------------------------
     The arithmetic is assets/js/food-shopping-list.js; this gathers entries
     and paints. Shown only while the shortlist view is on. It reads the
     store, not the visible rows: you shop from what you shortlisted. */
  var shoppingEl = document.getElementById('shopping-list');
  var shoppingRecipes = shoppingEl && shoppingEl.querySelector('.shopping-list-recipes');
  var shoppingAisles = shoppingEl && shoppingEl.querySelector('.shopping-list-aisles');
  var shoppingEmpty = shoppingEl && shoppingEl.querySelector('.shopping-list-empty');
  var shoppingNote = shoppingEl && shoppingEl.querySelector('.shopping-list-note');
  var setAllInput = document.getElementById('shopping-list-setall');

  /* Each recipe's ingredients and yield, emitted by food/index.html from
     _plugins/food_shopping.rb. Absent or unreadable, the shopping list
     renders nothing and every filter still works. */
  var RECIPES = (function () {
    var node = document.getElementById('recipe-ingredients');
    if (!node) return {};
    try {
      return JSON.parse(node.textContent) || {};
    } catch (e) {
      console.warn('filters.js: could not parse #recipe-ingredients — ' + e.message);
      return {};
    }
  })();

  var AISLES = (function () {
    var node = document.getElementById('recipe-aisles');
    if (!node) return [];
    try {
      var parsed = JSON.parse(node.textContent);
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      console.warn('filters.js: could not parse #recipe-aisles — ' + e.message);
      return [];
    }
  })();

  /* Measures bought whole (#1297): `half_step_measures` and
     `half_step_counts` from _data/food/scaling.yml. Absent, nothing rounds. */
  var WHOLE_MEASURES = String(
    (shoppingEl && shoppingEl.getAttribute('data-whole-measures')) || '')
    .split(',').filter(Boolean);

  // A sprig, a bunch: bought whole, used in quarters. `quarter_step_measures`.
  var QUARTER_MEASURES = String(
    (shoppingEl && shoppingEl.getAttribute('data-quarter-measures')) || '')
    .split(',').filter(Boolean);

  /* Nouns bought by count, so two recipes' lemons read "2 lemons" (#1297):
     `count_nouns`. Absent, a row keeps the recipe's spelling. */
  var COUNT_NOUNS = String(
    (shoppingEl && shoppingEl.getAttribute('data-count-nouns')) || '')
    .split(',').filter(Boolean);

  /* Things that hold what a recipe makes (a jar, a tin), so a row reads
     "2 jars of Peanut Sauce": `container_words`. */
  var CONTAINER_NOUNS = String(
    (shoppingEl && shoppingEl.getAttribute('data-container-nouns')) || '')
    .split(',').filter(Boolean);

  /* Title and href per row, read once. `dataset.titleText` is the unmarked
     title, so a name search's <mark> never reaches the list. The blob's keys
     are site-relative; the row's link already carries the base URL. */
  var hrefByUrl = {};
  var titleByUrl = (function () {
    var map = {};
    items.forEach(function (li) {
      var link = li.querySelector('.recipe-title-link');
      if (li.dataset.url && link) {
        map[li.dataset.url] = link.dataset.titleText || link.textContent;
        hrefByUrl[li.dataset.url] = link.getAttribute('href') || li.dataset.url;
      }
    });
    return map;
  })();

  /* In the order they were shortlisted (the store keeps insertion order).
     Recipes no longer on the page are dropped. */
  function shortlistedRecipes() {
    // A list someone sent is totalled as it stands (see renderShoppingList).
    return (sharedKeys || HTF.shortlist.list()).filter(function (url) {
      return Object.prototype.hasOwnProperty.call(RECIPES, url);
    });
  }

  /* --- A `serves:` recipe counts people (#815) -------------------------------
     `p` is its portion count: from `serves:`, or else `serves_estimate:`,
     which arrives flagged `e` so yieldText() can mark it `~`.

     Can this recipe be scaled? Asked of the recipe, never of the store: a
     stored number is a preference, not a capability. */
  function hasPortions(url) {
    var recipe = RECIPES[url];
    return !!(recipe && recipe.p > 0);
  }

  /* The number in the box: what was last typed, or the recipe's own count.
     null where the recipe carries none, and then there is no box. */
  function portionsFor(url) {
    if (!hasPortions(url)) return null;
    return HTF.shortlist.portions(url) || RECIPES[url].p;
  }

  /* Portions wanted over portions made; batches for a `makes:` recipe. A
     recipe with no count scales by 1 and gets no box. */
  function scaleFor(url) {
    if (isBatch(url)) return batchesFor(url);
    if (!hasPortions(url)) return 1;
    return portionsFor(url) / RECIPES[url].p;
  }

  /* --- A `makes:` recipe counts batches (#1297) ------------------------------
     The row says "batches" in words, so the box cannot be mistaken for a
     portions box. `w`, `h` and `m` are the recipe page's own figures (#1286):
     whole recipes, half offered, what one makes. Both step ½, 1, 2, 3 and
     never 1½. The count has its own store (HTF.shortlist.batches): a stored
     6 cannot say whether it meant people or batches. */
  function isBatch(url) {
    var recipe = RECIPES[url];
    return !!(recipe && recipe.w);
  }

  function halfOffered(url) {
    return isBatch(url) && !!RECIPES[url].h;
  }

  /* One batch until she says otherwise. A stored half is honoured only while
     the build still offers one: a preference is not a capability. */
  function batchesFor(url) {
    var n = HTF.shortlist.batches(url) || 1;
    return (n < 1 && !halfOffered(url)) ? 1 : n;
  }

  /* A typed or stepped figure, made into one the box can hold. The spinner
     moves in halves so that it can reach ½, which means it also lands on 1½:
     that goes on to the next whole batch in the direction it was travelling. */
  function batchCount(url, raw, previous) {
    var n = Number(raw);
    if (!isFinite(n) || n <= 0) return null;
    if (n < 1) return halfOffered(url) ? 0.5 : 1;
    if (n % 1 !== 0) return n > previous ? Math.ceil(n) : Math.floor(n);
    return n;
  }

  /* Is a word of the yield already in the title? "cookies" of Peanut Butter
     Cookies, yes. Compared in the singular both sides (`foldUnit`), so "pies"
     finds "Pie". */
  function wordInTitle(word, title) {
    var fold = HTF.shoppingList.foldUnit;
    var wanted = fold(word);
    if (!wanted) return false;
    return String(title).toLowerCase().split(/[\s,()\/&]+/).some(function (w) {
      return w !== '' && fold(w) === wanted;
    });
  }

  function batchWord(n) {
    return n > 1 ? 'batches of' : 'batch of';
  }

  /* "Sweet Potato Chocolate Brownies" before "squares" is "Brownie". The
     thing-name word is the last one before any " with ...". Only a plain
     plural is touched: `-ss` and `-us` words (Swiss, hummus) are not. */
  function singularHead(title) {
    var text = String(title);
    var cut = text.search(/\s+with\s+/i);
    var head = cut === -1 ? text : text.slice(0, cut);
    var tail = cut === -1 ? '' : text.slice(cut);
    var match = /^(.*?)([A-Za-zÀ-ɏ]+)$/.exec(head);
    if (!match || !/[^su]s$/i.test(match[2])) return text;
    var single = HTF.shoppingList.foldUnit(match[2]);
    if (!single || single === match[2].toLowerCase()) return text;
    if (/^[A-Z]/.test(match[2])) single = single.charAt(0).toUpperCase() + single.slice(1);
    return match[1] + single + tail;
  }

  /* The words of a row around the recipe's name: `word` is what the number
     counts, `pre`/`post` sit either side, `title` is the name as written.
       [2] batches of 18 [Peanut Butter Cookies]    title names the thing
       [1] batch of 24 [Guinness ... Cake] squares  it does not: said after
       [2] × [Lemon Meringue Pie]                   one whole thing: never "batch"
       [2] jars of [Peanut Sauce]                   a container holds it: "of"
       [3] [Rainbow Confetti] traybakes             one thing that is it
     A × also precedes a yield that opens with a digit ("2 × 8-inch"). */
  function rowWords(url, title, n) {
    var out = { word: '', pre: '', title: title, post: '' };
    if (!isBatch(url)) {
      out.word = n === 1 ? 'portion of' : 'portions of';
      return out;
    }
    out.word = batchWord(n);
    var made = RECIPES[url].m;
    if (!(made && made.kind === 'count' && made.stem)) return out;

    var unitLabel = HTF.shoppingList.unitLabel;
    var words = String(made.stem).split(/\s+/);
    // "dozen" is counted as itself and never changes with the number.
    var group = made.invariable ? words.shift() : '';
    var noun = words.length ? words[words.length - 1] : '';
    var named = !noun || wordInTitle(noun, title);
    // What stood before the noun, less anything the title already says
    // ("mince" of "dozen mince pies").
    var before = words.slice(0, -1).filter(function (w) {
      return !wordInTitle(w, title);
    }).join(' ');
    var lead = (group ? group + ' ' : '') + (before ? before + ' ' : '');

    if (Number(made.base) === 1) {
      var times = made.times ? '× ' : '';
      if (!named && CONTAINER_NOUNS.indexOf(HTF.shoppingList.foldUnit(noun)) !== -1) {
        out.word = times + lead + (n > 1 ? unitLabel(noun, 2) : noun) + ' of';
        return out;
      }
      if (named) {
        out.word = group || '×';
        out.pre = before ? before + ' ' : '';
        return out;
      }
      out.word = (times + group).trim();
      out.pre = before ? before + ' ' : '';
      out.title = singularHead(title);
      out.post = ' ' + (n > 1 ? unitLabel(noun, 2) : noun);
      return out;
    }

    // `makes: "3 batches (...)"` counts batches already: "batch of 3" is noise.
    if (!made.box || /^batch/i.test(String(made.stem))) return out;
    out.pre = made.box + ' ' + (group ? group + ' ' : '');
    if (!named) {
      out.title = singularHead(title);
      out.post = ' ' + words.join(' ') + String(made.rest || '');
    }
    return out;
  }

  /* The recipe's name as a link to the row's own href. `text` is the name as
     a row has reworded it ("... Brownie" before "squares"). */
  function recipeLink(url, text) {
    return '<a class="shopping-list-recipe-link" href="' +
      HTF.escapeHtml(hrefByUrl[url] || url) + '">' +
      HTF.escapeHtml(text || titleByUrl[url] || url) + '</a>';
  }

  /* Everything after the box. Its own function because the input handler
     rewrites it in place: the box cannot be re-rendered under a typing
     cursor, and several words of the row move with the number. */
  function rowInner(url, n) {
    var words = rowWords(url, titleByUrl[url] || url, n);
    return '<span class="shopping-list-count-word">' +
      HTF.escapeHtml(words.word) + '</span>' + (words.word ? ' ' : '') +
      HTF.escapeHtml(words.pre) + recipeLink(url, words.title) +
      HTF.escapeHtml(words.post);
  }

  function rowSentence(url, n) {
    return '<span>' + rowInner(url, n) + '</span>';
  }

  /* What a screen reader is told the box counts. It cannot move with the
     number, so a row that is not batches says "how many". */
  function boxLabel(url) {
    var made = RECIPES[url] && RECIPES[url].m;
    var single = made && made.kind === 'count' && Number(made.base) === 1 && made.stem;
    return single ? 'how many: ' : 'batches of ';
  }

  /* The yield in the recipe's own words and key: `k` is `serves` or `makes`,
     so a `makes:` value is never printed behind the word "serves". */
  function yieldText(url) {
    var recipe = RECIPES[url];
    if (!recipe) return '';
    // An estimate is marked `~` (#815); a stated yield is quoted as written.
    if (recipe.e) return recipe.p ? '~' + recipe.p + ' portions' : '';
    if (!recipe.y) return '';
    return (recipe.k || 'serves') + ' ' + recipe.y;
  }

  function renderShoppingList() {
    if (!shoppingEl) return;
    /* Shown over a shared list too. Opening the link still saves nothing:
       the list is totalled from the link. A number typed into a box is saved,
       as that recipe's count. */
    shoppingEl.hidden = !state.shortlisted;
    if (shoppingEl.hidden) return;

    var urls = shortlistedRecipes();
    if (shoppingEmpty) shoppingEmpty.hidden = urls.length > 0;

    /* Rebuilt whole, but never from the input handler: replacing the node
       under a typing cursor loses the caret (it calls renderTotals() alone).
       Batch rows go last, under a hairline drawn on the first one when
       portions rows sit above it, so "set all" sits over the rows it sets.
       Each group keeps shortlist order. */
    var portionRows = urls.filter(function (url) { return !isBatch(url); });
    var batchRows = urls.filter(isBatch);
    var firstBatch = portionRows.length ? batchRows[0] : null;

    if (shoppingRecipes) {
      shoppingRecipes.innerHTML = portionRows.concat(batchRows).map(function (url) {
        var title = titleByUrl[url] || url;
        var yielded = yieldText(url);
        /* No portion count, no box (hasPortions): such a recipe contributes
           its ingredients at x1 and says why it cannot be scaled.
           A `makes:` recipe reads "2 batches of 18 Peanut Butter Cookies"
           (#1297): the figure after "of" is one batch's and never moves. */
        if (isBatch(url)) {
          var batches = batchesFor(url);
          var floor = halfOffered(url) ? '0.5' : '1';
          var makes = RECIPES[url].y ? ', which makes ' + RECIPES[url].y : '';
          return (url === firstBatch
            ? '<li class="shopping-list-recipe--first-batch">' : '<li>') +
            '<input type="number" class="shopping-list-portions" min="' + floor +
            '" max="99" step="' + floor + '" inputmode="decimal" value="' + batches + '" ' +
            'data-url="' + HTF.escapeHtml(url) + '" data-batches ' +
            'title="' + HTF.escapeHtml(title + makes) + '" ' +
            'aria-label="' + HTF.escapeHtml(boxLabel(url) + title + makes) + '">' +
            rowSentence(url, batches) +
            '</li>';
        }

        if (!hasPortions(url)) {
          return '<li class="shopping-list-recipe--unscalable">' +
            '<span>' + HTF.escapeHtml(title) +
            '<span class="shopping-list-yield-missing">' +
            'no serving size — add <code>serves_estimate:</code></span>' +
            '</span></li>';
        }

        /* The yield is not printed beside the name: "7 Moules Marinière
           serves 4" reads as 7 × 4. It goes in the control's title and
           aria-label instead. */
        var relative = yielded ? ', which ' + yielded : '';
        return '<li>' +
          '<input type="number" class="shopping-list-portions" min="1" max="99" step="1" ' +
          'inputmode="numeric" value="' + portionsFor(url) + '" ' +
          'data-url="' + HTF.escapeHtml(url) + '" ' +
          'title="' + HTF.escapeHtml(title + relative) + '" ' +
          'aria-label="portions of ' + HTF.escapeHtml(title + relative) + '">' +
          rowSentence(url, portionsFor(url)) +
          '</li>';
      }).join('');
    }

    renderTotals(urls);
  }

  function renderTotals(urls) {
    if (!shoppingAisles) return;

    var shortlisted = urls || shortlistedRecipes();
    var entries = [];
    shortlisted.forEach(function (url) {
      var scale = scaleFor(url);
      ((RECIPES[url] || {}).i || []).forEach(function (ing) {
        // `recipe` and the four marks are #1297's: see `reunite` in
        // food-shopping-list.js for what each one does to the total.
        entries.push({
          amount: ing.a, name: ing.n, aisle: ing.s, scale: scale,
          recipe: url, parts: ing.pt, fruit: ing.f, count: ing.c, pointer: ing.x
        });
      });
    });

    /* A panel with boxes and no totals says so. The usual cause is
       _plugins/food_shopping.rb not having run: Jekyll loads plugins once at
       boot and does not reload them on watch. */
    if (shortlisted.length && !entries.length) {
      console.warn(
        'filters.js: every shortlisted recipe reached the page with no '
        + 'ingredients, so the shopping list has nothing to total. This is '
        + 'almost always _plugins/food_shopping.rb not having run: Jekyll '
        + 'loads plugins once at startup and does not reload them on watch, '
        + 'so restart `jekyll-local` rather than waiting for a rebuild.'
      );
      shoppingAisles.innerHTML =
        '<p class="shopping-list-empty">No ingredient data was built for '
        + 'these recipes, so there is nothing to add up. If this is the local '
        + 'server, restart it — its plugins are loaded once at startup.</p>';
      return;
    }

    var aisles = HTF.foodShoppingList.build(entries, {
      aisles: AISLES, wholeMeasures: WHOLE_MEASURES,
      quarterMeasures: QUARTER_MEASURES, countNouns: COUNT_NOUNS
    });

    /* What the numbers did not reach, as on the recipe page (#1088): a row
       is named when any line behind it had no amount to scale ("salt, to
       taste"). Bracketed, comma-joined, no full stop, in the list's order. */
    if (shoppingNote) {
      var unscaled = [];
      aisles.forEach(function (aisle) {
        aisle.items.forEach(function (row) {
          if (row.unquantified.length) unscaled.push(row.label);
        });
      });
      shoppingNote.textContent = unscaled.length
        ? '(Not scaled: ' + unscaled.join(', ') + ')' : '';
      shoppingNote.hidden = unscaled.length === 0;
    }

    /* Rebuilt whole: a few dozen rows are not worth a diffing render. */
    shoppingAisles.innerHTML = aisles.map(function (aisle) {
      return '<section class="shopping-list-aisle">' +
        '<h3 class="shopping-list-aisle-name">' + HTF.escapeHtml(aisle.label) + '</h3>' +
        '<ul class="shopping-list-items">' +
        aisle.items.map(function (row) {
          return '<li>' +
            '<span class="shopping-list-amount">' + HTF.escapeHtml(row.text) + '</span>' +
            '<span class="shopping-list-name">' + HTF.escapeHtml(row.label) + '</span>' +
            /* "(1¼ in the recipes)" (#1297): the amount is what to buy. */
            (row.aside ? '<span class="shopping-list-aside">(' +
              HTF.escapeHtml(row.aside) + ')</span>' : '') +
            /* Whose line was not scaled: each a link to its recipe. */
            (row.unscaledRecipes && row.unscaledRecipes.length
              ? '<span class="shopping-list-unscaled">(' +
                row.unscaledRecipes.map(recipeLink).join(', ') + ')</span>'
              : '') +
            '</li>';
        }).join('') +
        '</ul></section>';
    }).join('');
  }

  if (shoppingRecipes) {
    // Delegated, because the inputs are replaced on every shortlist change.
    shoppingRecipes.addEventListener('input', function (ev) {
      var input = ev.target;
      if (!input.classList || !input.classList.contains('shopping-list-portions')) return;
      var url = input.dataset.url;
      var shown;
      if (isBatch(url)) {
        var typed = Number(input.value);
        shown = HTF.shortlist.setBatches(url,
          batchCount(url, input.value, batchesFor(url))) || 1;
        // Only the spinner's 1½ is rewritten under the cursor. Typing carries
        // an `inputType` and waits for `change`: rewriting "2.2" to "2" mid-
        // figure made the next key give "25" (#1386).
        if (!ev.inputType && typed > 1 && typed % 1 !== 0) input.value = String(shown);
      } else {
        shown = HTF.shortlist.setPortions(url, input.value) || portionsFor(url);
      }
      /* The row's words move with the number and are rewritten in place. */
      var word = input.parentNode && input.parentNode.querySelector &&
        input.parentNode.querySelector('.shopping-list-count-word');
      if (word && word.parentNode) word.parentNode.innerHTML = rowInner(url, shown);
      // Totals only. Re-rendering the recipe list would replace the very input
      // being typed into and take the caret with it.
      renderTotals();
    });

    /* On `change`, a box shows what it was taken as: "0.2" where no half is
       offered is one batch, and "1.5" portions is 1. */
    shoppingRecipes.addEventListener('change', function (ev) {
      var input = ev.target;
      if (!input.classList || !input.classList.contains('shopping-list-portions')) return;
      var url = input.dataset.url;
      input.value = String(isBatch(url) ? batchesFor(url) : portionsFor(url));
    });
  }

  if (setAllInput) {
    /* Set all writes every recipe's own number and keeps no state. It ships
       empty: each recipe starts at its own yield, so no one number means "as
       written". */
    /* Number(), not parseInt: parseInt reads "1e9" as 1, and the list then
       disagreed with the box. */
    function setAllValue() {
      var n = Number(setAllInput.value);
      return isFinite(n) && n >= 1 ? Math.min(99, Math.floor(n)) : null;
    }

    setAllInput.addEventListener('input', function () {
      var n = setAllValue();
      if (n === null) return;
      /* A batch row is left alone (#1297): "6 portions" has no answer for a
         recipe that makes 18 cookies. */
      shortlistedRecipes().forEach(function (url) {
        if (!isBatch(url)) HTF.shortlist.setPortions(url, n);
      });
      renderShoppingList();
    });

    /* On `change` the box shows what was applied, or empties if nothing was. */
    setAllInput.addEventListener('change', function () {
      var n = setAllValue();
      setAllInput.value = n === null ? '' : String(n);
    });
  }

  /* --- The shortlist (#546) ---------------------------------------------------
     The button ships `hidden` and is revealed here, by the script that makes
     the filter real. It is a view, not a facet (#918): pressing it on clears
     every other filter, boxes and pools included; a filter set while it is on
     takes it off again (reconcileShortlistView, in update()). */
  if (shortlistOnlyBtn) {
    shortlistOnlyBtn.hidden = false;
    shortlistOnlyBtn.addEventListener('click', function () {
      if (sharedKeys) {
        // Over a shared list the button is not on (syncShortlistOnly), so a
        // press means what it means when off: show MY shortlist.
        sharedKeys = null;
        sharedUnmatched = [];
      } else if (state.shortlisted) {
        state.shortlisted = false;
      } else {
        state = FilterState.enterShortlistView();
        resetFilterControls();
      }
      update();
    });
  }

  /* #1358. The label names what a press will do, and `is-on` says the list is
     currently narrowed, as it does on the button above. */
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

  /* A row's own toggle changed (dispatched by shortlist.js). Unconditional,
     and `update(true)` keeps the page number: marking a row on page 3 must
     not throw you back to page 1. */
  document.addEventListener('htf:shortlist-change', function () {
    update(true);
  });

  /* Keep these (#1093): merges the shared list into this browser's shortlist
     (addAll never un-marks anything), then shows that shortlist. The change
     event repaints every row's toggle. */
  var sharedKeep = sharedNote && sharedNote.querySelector('[data-shared-shortlist-keep]');
  if (sharedKeep) {
    sharedKeep.addEventListener('click', function () {
      if (!sharedKeys) return;
      var keys = sharedKeys;
      sharedKeys = null;
      sharedUnmatched = [];
      HTF.shortlist.addAll(keys);
      document.dispatchEvent(new CustomEvent('htf:shortlist-change', {
        detail: { key: null, on: true, kept: keys.length }
      }));
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

    /* `?ing=` (#1050), from the search-for-anything box. The text goes into
       HAS TO HAVE and the pool is painted as a keystroke would paint it,
       which chooses a unique result. With several, the button whose name IS
       the word is clicked, so the choice takes the click handler's path. With
       none, the pool stays for the reader to pick from. Last value wins. */
    if (wanted.ing.length && searchBox && resultsPool) {
      var wantedIng = wanted.ing[wanted.ing.length - 1];
      searchBox.value = wantedIng;
      renderResultsPool();
      var wantedKey = fold(wantedIng.trim().toLowerCase());
      var exact = null;
      resultsPool.querySelectorAll('.btn-ingredient').forEach(function (btn) {
        if (exact) return;
        var byKey = fold(String(btn.dataset.ingredient || '').toLowerCase()) === wantedKey;
        var byLabel = fold(String(btn.textContent || '').replace(' (all)', '').trim().toLowerCase()) === wantedKey;
        if (byKey || byLabel) exact = btn;
      });
      // Not when auto-select already chose it: a click on an active button
      // removes it (#1092).
      if (exact && !exact.classList.contains('active') && typeof exact.click === 'function') {
        exact.click();
      }
    }
  })();

  // A fresh load starts shuffled, filtered or not, so no recipe is stuck at
  // the bottom. .recipe-list starts visibility:hidden in CSS so the shuffled
  // order is the first one painted. Arriving by going back restores the list
  // you left instead (#387).
  var restored = restoreIndexMemory();
  if (!restored) shuffleRecipeList();

  /* `?shortlist=1` (#1011) enters the shortlist view exactly as the button
     does, after the query-string filters and the memory, and replaces both;
     the remembered scroll goes with the remembered list. `?shortlist=a,b`
     (#1093) enters the same view and answers "is this row on it" from the
     link (`sharedKeys`); resolveSlugs writes nothing. */
  var arrivedShortlist = FilterState.parseShortlist(location.search);
  if (arrivedShortlist.own || arrivedShortlist.slugs.length) {
    state = FilterState.enterShortlistView();
    resetFilterControls();
    restored = null;
    if (arrivedShortlist.slugs.length) {
      var resolvedShared = HTF.shortlist.resolveSlugs(arrivedShortlist.slugs,
        items.map(function (li) { return li.dataset.url || ''; }));
      sharedKeys = resolvedShared.keys;
      sharedUnmatched = resolvedShared.unmatched;
    }
  }

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
