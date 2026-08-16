document.addEventListener('DOMContentLoaded', function () {
  var FilterState = HTF.filterState;

  /* ONE state object, not six loose variables — GitHub issue #52, step one.
     Its fields, its cleared value and both "is anything set" answers all come
     from assets/js/filter-state.js, which is where the reasoning for each
     field now lives and where tests/js/filter-state.test.js can reach it.
     Read FIELD_SPEC there before adding a filter kind here.

     Reassigned wholesale by clearAllFilters(), never rebuilt field by field:
     that is the whole point. Every reader below goes through this one
     variable, so a reassignment reaches all of them.

       state.tags        Set, the MOOD/PRACTICALITIES tag buttons
       state.star        string|null, single-select STAR INGREDIENT
       state.ingredient  string|null, the chosen ingredient-search result
       state.meta        Set, the local-only meta filters
       state.excludedIngredients
                         Set, the "they hate peas" exclusions (issue #52).
                         Entries of the DERIVED ingredient index
                         (data-all-ingredients), matched as whole entries, not
                         as substrings -- see rowIsExcluded() below.
       state.nameQuery   the title search — folded (accents stripped,
                         HTF.ingredientSearch.fold) and lowercased, the same
                         treatment ingredient-search.js gives its own query.
                         GitHub issue #45: typing "creme brulee" found nothing
                         against a title that actually reads "Crème Brûlée".
                         Every match against a title (here and in
                         updateTitleHighlights() below) folds that title's text
                         the same way before comparing, so an accented title
                         still matches an unaccented query and vice versa; the
                         title itself is never folded for display.
       state.isSearching NOT A FILTER — "the ingredient box has text and
                         nothing is chosen yet". Clearable, so it counts
                         towards the clear button; not narrowing, so it does
                         not count towards suppressList.
       state.isExcludeSearching
                         isSearching's sibling for the LEAVE OUT box
                         (#exclude-search-box, issue #52). GitHub issue #274:
                         this had no field at all, so a half-finished exclude
                         search set no state, and the clear button stayed
                         hidden beside a pool of results with no other way to
                         dismiss them. Same treatment as isSearching. */
  var state = FilterState.emptyState();

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
  // Two buttons, same action -- issue #67. The top one is the original,
  // pinned top-right of the matrix; the bottom one repeats it after the last
  // filter section so clearing doesn't mean scrolling back up past five
  // sections. Both stay in sync (visibility, click) via clearButtons below.
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

  var searchBox = document.getElementById('ingredient-search-box');
  var resultsPool = document.getElementById('ingredient-results-pool');
  var ingredientClear = document.getElementById('ingredient-search-clear');
  var nameSearchBox = document.getElementById('name-search-box');
  var nameSearchClear = document.getElementById('name-search-clear');

  // The dislike navigator (GitHub issue #52) -- see food/index.html's own
  // comment on the section for why it starts hidden.
  var excludeReveal = document.getElementById('exclude-reveal');
  var excludePanel = document.getElementById('exclude-panel');
  var excludeBox = document.getElementById('exclude-search-box');
  var excludeClear = document.getElementById('exclude-search-clear');
  var excludePool = document.getElementById('exclude-results-pool');
  var excludeActive = document.getElementById('exclude-active');

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

  /* TWO PREDICATES, NOT ONE, AND THEY ARE NOT THE SAME QUESTION -- GitHub
     issue #248. There used to be three near-identical expressions scattered
     through this file and the issue read as "unify them". Unifying them would
     have been wrong: two of the three ask genuinely different things, and
     collapsing them would have traded a documented difference for a silent
     behaviour change in whichever call site lost its own answer.

     What they actually ask:

       hasNarrowingFilter()  "while the ingredient box is being typed into, is
                             anything ELSE still narrowing the list?" -- the
                             one input to suppressList, which decides whether
                             the list hides behind the "searching" message.

       hasAnythingToClear()  "is there anything for the clear-all button to
                             clear?" -- purely the button's visibility, and it
                             must agree with what clearAllFilters() actually
                             clears, or the button hides while still having
                             work to do.

     BOTH ARE NOW ANSWERED BY assets/js/filter-state.js, by walking its field
     table rather than by a hand-written run of `||`s -- GitHub issue #52,
     step one. The run of `||`s is what kept going wrong: it disagreed with
     clearAllFilters() about nameQuery, then about isSearching, and each time
     the clear button hid while it still had work to do. Both wrappers stay,
     because both call sites want the sentence rather than the mechanism, and
     because they are the proof that the two questions are still two.

     Which fields each one counts, and why each excluded field is excluded, is
     recorded on the fields themselves in FIELD_SPEC. Do not re-derive either
     answer here. */
  function hasNarrowingFilter() {
    return FilterState.hasNarrowingFilter(state);
  }

  function hasAnythingToClear() {
    return FilterState.hasAnythingToClear(state);
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

  // GitHub issues #63/#78: while a title search is active, matching rows
  // are grouped into three tiers (title starts with the query > some other
  // word in the title starts with it > query is only a mid-word substring
  // somewhere) — see HTF.recipeList.titleMatchTier's own comment for the
  // exact rule. Each tier is independently shuffled, same "fair shot" idea
  // as shuffleRecipeList() above, so no recipe is permanently stuck at the
  // bottom of a tier it shares with dozens of others. Runs on every
  // keystroke, same as the matching itself — the ranking is only ever
  // correct for the query that's currently typed.
  function reorderForTitleSearch() {
    if (!recipeList) return;
    var byTier = { 0: [], 1: [], 2: [], 3: [] };
    items.forEach(function(li) {
      // .recipe-title-link, not the first <a> in the row. It used to be
      // querySelector('a'), which worked only by accident: the title link
      // happened to be the first link in the <li>. GitHub issue #40 put
      // badge links in the same <li>, at which point "the first <a>" is
      // still the title today and stops being it the moment anything is
      // added above it. Named, so it cannot drift.
      var title = (li.querySelector('.recipe-title-link') || {}).textContent || '';
      var tier = HTF.recipeList.titleMatchTier(title, state.nameQuery, fold);
      byTier[tier].push(li);
    });
    items = [].concat(
      HTF.recipeList.shuffle(byTier[1]),
      HTF.recipeList.shuffle(byTier[2]),
      HTF.recipeList.shuffle(byTier[3]),
      byTier[0]
    );
    items.forEach(function(li) { recipeList.appendChild(li); });
  }

  // Whether a row's ingredient line is ACTUALLY truncated by its line-clamp,
  // not just short. CSS has no selector for "this box's content overflowed
  // it" — mask-image can't conditionally apply itself — so this measures
  // scrollHeight against clientHeight directly and flags the ones that really
  // are cut off. Hidden rows (display:none, offsetParent null) are skipped:
  // they measure 0/0 either way, and get measured again once a filter or
  // page change makes them visible, because this runs at the end of update().
  //
  // GitHub issue #93: Helen saw the fade on rows that read as fully visible,
  // not just genuinely clamped ones -- "each recipe row", not "some". A
  // -webkit-box + -webkit-line-clamp box's scrollHeight vs. clientHeight
  // comparison is a known source of exactly this kind of false positive:
  // sub-pixel line-height rounding can put scrollHeight a pixel or two above
  // clientHeight even when nothing is actually cut off, especially at
  // fractional device pixel ratios. +1 wasn't enough headroom; +3 is more
  // forgiving of that rounding while still catching genuine overflow, which
  // is never a near-miss (a whole clamped line is comfortably taller than a
  // few px). Not fully verifiable without a browser -- please check locally.
  function updateIngredientClamp() {
    document.querySelectorAll('.recipe-list .ingredient-list').forEach(function(el) {
      if (el.offsetParent === null) return;
      el.classList.toggle('is-clamped', el.scrollHeight > el.clientHeight + 3);
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

  // ---------------------------------------------------------------------------
  // THE DERIVED INGREDIENT INDEX — GitHub issue #52's exclusions
  // ---------------------------------------------------------------------------
  //
  // A SECOND vocabulary, over data-all-ingredients (every ingredient_groups
  // item on the row, incidentals included) rather than over data-ingredients
  // (main_ingredients). They are not interchangeable and the difference is the
  // whole reason this feature is built on the derived list: main_ingredients is
  // a deliberately partial hint, which is fine to include ON and dangerous to
  // exclude BY. Nine rows list an olive oil in ingredient_groups and none of
  // them names it in main_ingredients; coriander is 3 against 8, mushrooms 3
  // against 4. "No olives, please" answered from main_ingredients hands back
  // nine recipes containing the thing.
  //
  // Each row's own entries go through buildMasterList too, not just the
  // corpus-wide list. That is what makes exact membership WORK: the picker
  // offers "roasted peanuts" (buildMasterList strips the leading modifier from
  // "chopped roasted peanuts"), so a row compared in its raw form would never
  // match the entry the user was actually shown. One function, applied to both
  // sides, and the two cannot drift.
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

  /* Does any entry in `list` match the picked ingredient key `key`, by the
     rules ingredient search already uses — a curated synonym family matches on
     containment of any of its words, anything else matches when every word of
     the key prefixes some word of the entry?

     Extracted rather than written twice: the ingredient INCLUDE filter in
     update() and the "(all)" family case of the EXCLUDE filter are the same
     question asked of two different lists, and two copies of a matching rule
     this fiddly is how "chicken (all)" ends up meaning one thing when you
     filter for it and another when you filter it out. */
  function entriesMatchKey(list, key) {
    var synonyms = IS.getSynonymWords(key);
    if (synonyms) {
      return list.some(function (entry) {
        var lower = entry.toLowerCase();
        return synonyms.some(function (syn) { return lower.indexOf(syn) !== -1; });
      });
    }
    var keyWords = getWords(key).map(IS.normaliseIngredientWord);
    return list.some(function (entry) {
      var entryWords = getWords(entry).map(IS.normaliseIngredientWord);
      return keyWords.every(function (kw) {
        return entryWords.some(function (ew) { return ew.indexOf(kw) !== -1; });
      });
    });
  }

  /* The RULE itself — set membership, never substring — is
     FilterState.excludesRow, next to the state it acts on and where
     tests/js/filter-state.test.js can reach it without a DOM. Read its comment
     before changing anything here: it is the line that stops "peas" taking the
     peanut butter and the pearl barley with it.

     This wrapper is the DOM half and nothing else: which entries this row has,
     and the one thing the rule cannot know on its own — how to match a "(all)"
     family button, which needs the ingredient vocabulary. */
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
    if (key === state.ingredient) btn.classList.add('active');
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
      ingredientClear.style.visibility = (state.ingredient || (searchBox && searchBox.value.trim())) ? 'visible' : 'hidden';
    }
  }

  function escapeHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  // Wraps the substring of each recipe title that matches state.nameQuery in a
  // .title-hit span, same "same tag styling" idea as the ingredient pills
  // above -- Helen's stretch goal: "could the part of the title hit gain
  // the orange background and scratchy, capitalised lettering." Only the
  // MATCHED substring gets the treatment, not the whole title, so this
  // rebuilds from the original text (stashed once, above) every time
  // rather than patching whatever's currently in the DOM.
  function updateTitleHighlights() {
    titleLinks.forEach(function (a) {
      var original = a.dataset.titleText;
      if (!state.nameQuery) {
        a.textContent = original;
        return;
      }
      var idx = HTF.ingredientSearch.fold(original.toLowerCase()).indexOf(state.nameQuery);
      if (idx === -1) {
        a.textContent = original;
        return;
      }
      var before = original.slice(0, idx);
      var hit = original.slice(idx, idx + state.nameQuery.length);
      var after = original.slice(idx + state.nameQuery.length);
      a.innerHTML = escapeHtml(before) +
        '<mark class="title-hit"><span class="tag-shape" aria-hidden="true"></span>' + escapeHtml(hit) + '</mark>' +
        escapeHtml(after);
    });
    if (state.nameQuery && window.HTF && HTF.tagShapes) HTF.tagShapes();
  }






function renderResultsPool() {
  if (!searchBox || !resultsPool) return;
  var query = fold(searchBox.value.trim().toLowerCase());
  resultsPool.innerHTML = '';
  state.ingredient = null;
  state.isSearching = !!query;
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
    // GitHub issue #51: if "chicken (all)" is already offered, don't also
    // show a bare "chicken" row right next to it — Helen: "I am always
    // suspicious of searches like this, so if I read 'chicken (all)' next
    // to 'chicken' I'd look at both". Only suppresses an exact bare-word
    // entry, never a real multi-word one like "chicken breast".
    if (result.familyButtons.indexOf(fold(r.ing.trim().toLowerCase())) !== -1) return;
    resultsPool.appendChild(makeIngredientButton(r.ing, r.label || r.ing, r.hasWordMatch));
  });

  var buttons = resultsPool.querySelectorAll('.btn-ingredient');
  if (buttons.length === 1) {
    var onlyBtn = buttons[0];
    state.ingredient = onlyBtn.dataset.ingredient;
    onlyBtn.classList.add('active');
    state.isSearching = false;
  }
  ensureActiveIngredientShape();
  update();
  updateIngredientClear();
}


  


  



  // ---------------------------------------------------------------------------
  // THE DISLIKE NAVIGATOR — GitHub issue #52
  // ---------------------------------------------------------------------------

  function makeExcludeButton(value, label) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn-tag btn-exclude';
    btn.dataset.exclude = value;
    btn.textContent = label;
    return btn;
  }

  /* THE ACTIVE PILL, NOT makeExcludeButton -- it used to be one text node
     ("peas ×") so .btn-exclude--active's line-through ran through the × as
     well as the ingredient, which reads as "this control is disabled" rather
     than "this ingredient is out". The name and the × are now separate
     elements so _search.scss can strike only .btn-exclude-label; the × stays
     plain. Still one clickable <button> throughout -- the × is not a second
     control, same as before -- and the aria-label is unchanged. */
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

  /* The picker's own search is FUZZY, and that is correct. It runs
     HTF.ingredientSearch — folding, modifier-stripping, singulars, the lot —
     over the derived vocabulary, so typing "pea" offers peas, peanut butter
     AND pearl barley. All three are real entries in this collection; you pick
     the one you meant, and what you picked is then matched as a whole entry
     (rowIsExcluded above). Fuzzy to FIND, exact to FILTER. */
  function renderExcludePool() {
    if (!excludeBox || !excludePool) return;
    var query = fold(excludeBox.value.trim().toLowerCase());
    excludePool.innerHTML = '';
    if (excludeClear) excludeClear.style.visibility = query ? 'visible' : 'hidden';
    // isSearching's sibling for this box (GitHub issue #274) -- see its entry
    // in FIELD_SPEC. Set here, in step with the pool it describes, rather
    // than left for toggleExcluded/excludeClear alone to unset, so the clear
    // button appears the instant a half-finished search puts a pool on
    // screen and not only once something is picked out of it.
    state.isExcludeSearching = !!query;
    if (!query) {
      update();
      return;
    }

    var result = IS.search(query, excludeMasterList);
    result.familyButtons.forEach(function (fw) {
      var label = fw + FAMILY_SUFFIX;
      excludePool.appendChild(makeExcludeButton(label, label));
    });
    result.results.forEach(function (r) {
      // Same "don't offer 'chicken' next to 'chicken (all)'" suppression
      // renderResultsPool() applies, and for the same reason (issue #51):
      // two adjacent buttons that look like the same answer make you check
      // both.
      if (result.familyButtons.indexOf(fold(r.ing.trim().toLowerCase())) !== -1) return;
      excludePool.appendChild(makeExcludeButton(r.ing, r.label || r.ing));
    });
    update();
  }

  /* WHAT IS BEING LEFT OUT, painted from state rather than at each place state
     changes — the argument syncFilterButtons() already makes one layer up.
     Clear-all reassigns the whole state object and never touches this markup,
     so anything painted at click time would survive a clear that emptied the
     state underneath it.

     THE COPY IS ABOUT WHAT IS LISTED, never about what a recipe is free of.
     This index is derived from what each recipe happens to write down, so
     "hiding 1 recipe that lists peas" is a true statement about the data and
     "1 pea-free recipe" is not a claim this page is in any position to make.
     Helen will settle the fuller wording once she has seen it working — do not
     grow this into a paragraph of caveats in the meantime. */
  function renderExcludeActive(excludedCount) {
    if (!excludeActive) return;
    excludeActive.innerHTML = '';
    if (!state.excludedIngredients.size) return;

    var label = document.createElement('span');
    label.className = 'exclude-active-label';
    label.textContent = 'leaving out';
    excludeActive.appendChild(label);

    var names = [];
    state.excludedIngredients.forEach(function (value) {
      // The sentence reads about the ingredient, so the "(all)" that qualifies
      // the BUTTON comes off here -- "recipes that list chicken (all)" is not
      // a sentence. The pill keeps it, because there it is the control's name.
      names.push(value.replace(FAMILY_SUFFIX, ''));
      excludeActive.appendChild(makeActiveExcludeButton(value));
    });

    var count = document.createElement('span');
    count.className = 'exclude-count';
    var listed = names.join(' or ');
    if (excludedCount === 0) {
      /* Says nothing about the collection, deliberately. excludedCount counts
         rows this exclusion removed FROM THE CURRENT RESULTS, so zero can mean
         "nothing lists peas" or it can mean "the tag filter had already taken
         the one that does" -- and "no recipe lists peas" would be a flat
         untruth in the second case. */
      count.textContent = 'hiding nothing from the recipes left';
    } else if (excludedCount === 1) {
      count.textContent = 'hiding 1 recipe that lists ' + listed;
    } else {
      count.textContent = 'hiding ' + excludedCount + ' recipes that list ' + listed;
    }
    excludeActive.appendChild(count);
  }

  // Multi-select, like the tag buttons and unlike the star: you can be cooking
  // for someone who hates peas AND coriander, and a second pick that replaced
  // the first would be useless for the one job this feature has.
  function toggleExcluded(value) {
    if (!value) return;
    if (state.excludedIngredients.has(value)) {
      state.excludedIngredients.delete(value);
    } else {
      state.excludedIngredients.add(value);
      // Emptied on a pick rather than left standing: the next thing you want
      // is to name the NEXT thing they hate, and the entry you just chose is
      // now shown in the active list below anyway.
      if (excludeBox) excludeBox.value = '';
      if (excludePool) excludePool.innerHTML = '';
      if (excludeClear) excludeClear.style.visibility = 'hidden';
      // isSearching's sibling -- a result was just chosen, so the box is no
      // longer mid-search (renderResultsPool's own auto-select does the same
      // for state.isSearching).
      state.isExcludeSearching = false;
    }
    update();
  }

  // #exclude-dismiss follows #exclude-search-clear's own idiom -- visibility,
  // not display, so its space is reserved beside the reveal button rather
  // than the row jumping width the instant the panel opens (see
  // #ingredient-search-box's comment in _search.scss for why that mattered
  // enough to fix once already).
  /* ONE CONTROL, WHOSE LABEL REPORTS THE STATE. There was a second button, a
     "x hide" beside this one, until Helen's 2026-08-16 pass: "remove the hide
     link -- when the section is shown, update the link text". Two controls for
     one binary meant one of them was always the wrong thing to look at, and
     the closed state offered a dismiss for a panel that was not there.

     The label is the disclosure's own state, which is also why aria-expanded
     is not doing this work alone: a sighted reader gets the same information
     the attribute gives a screen reader, from the same element. */
  var EXCLUDE_LABEL_CLOSED = "I know what I don't want";
  var EXCLUDE_LABEL_OPEN = '(hide leave out)';

  function setExcludeRevealed(open) {
    if (!excludeReveal || !excludePanel) return;
    excludeReveal.setAttribute('aria-expanded', open ? 'true' : 'false');
    excludePanel.hidden = !open;
    excludeReveal.textContent = open ? EXCLUDE_LABEL_OPEN : EXCLUDE_LABEL_CLOSED;
  }

  if (excludeReveal && excludePanel) {
    excludeReveal.addEventListener('click', function () {
      setExcludeRevealed(excludeReveal.getAttribute('aria-expanded') !== 'true');
      // Focus follows the disclosure, so a keyboard user lands in the box
      // they just asked for rather than tabbing back through the panel.
      if (excludePanel.hidden === false && excludeBox) excludeBox.focus();
    });
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
      // isSearching's sibling -- see ingredientClear's own handler below.
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
      state.ingredient = null;
      state.isSearching = false;
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
    if (!matrix) return;
    matrix.querySelectorAll('.btn-star, .btn-tag, .btn-meta').forEach(function(btn) {
      btn.setAttribute('aria-pressed', btn.classList.contains('active') ? 'true' : 'false');
    });
  }

  // Paint .active on the filter buttons FROM STATE, rather than at each of
  // the places state changes. Exactly the argument syncAriaPressed's own
  // comment above makes, one layer down: .active used to be toggled inline at
  // every toggle site, which was survivable while the only way to change a
  // filter was to click its own button. Issue #40 adds a second way in (a
  // badge on a recipe row), and a query string at load is a third -- and
  // neither of those has a `target` button to reach for at all. One place to
  // be right; the toggles below just change state and call update().
  //
  // .btn-ingredient is excluded deliberately: those buttons also carry
  // .btn-tag, but their selected state is state.ingredient's, not
  // state.tags', and it is maintained where they are built and clicked.
  function syncFilterButtons() {
    if (!matrix) return;
    matrix.querySelectorAll('.btn-tag').forEach(function(btn) {
      if (btn.classList.contains('btn-ingredient')) return;
      btn.classList.toggle('active', state.tags.has(btn.dataset.tag));
    });
    matrix.querySelectorAll('.btn-star').forEach(function(btn) {
      btn.classList.toggle('active', state.star === btn.dataset.star);
    });
    matrix.querySelectorAll('.btn-meta').forEach(function(btn) {
      btn.classList.toggle('active', state.meta.has(btn.dataset.meta));
    });
  }

  // The three toggles, lifted out of the matrix click handler so a badge
  // click (and, later, issue #52's exclusion) can be the SAME action rather
  // than a second implementation of it. Note what they do not do: touch a
  // button's classes. That is syncFilterButtons()' job now.
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

  function toggleMeta(value) {
    if (!value) return;
    if (state.meta.has(value)) state.meta.delete(value);
    else state.meta.add(value);
    update();
  }

  function update(preservePage) {
    if (!preservePage) { currentPage = 1; showAll = false; }
    var visibleCount = 0;
    var totalPages = 1;
    var suppressList = state.isSearching && !hasNarrowingFilter();
    if (recipeList) recipeList.style.display = suppressList ? 'none' : '';

    updateTitleHighlights();

    // Matching runs regardless of suppressList, so the "N survivors" count
    // below always reflects the filters actually in effect (title search,
    // tags, star, meta) rather than freezing at a stale number. GitHub
    // issue #60: Helen typed a title search (ten rows), then an ingredient
    // search that matched nothing -- the list correctly emptied, but the
    // count stayed stuck at "10 survivors" because this whole block, count
    // included, used to be skipped outright while suppressList was true.
    // Only the actual <li> visibility/pagination stays gated by
    // suppressList below -- whether the list itself should keep showing
    // rows while you're still picking an ingredient search result is a
    // separate, open design question Helen hasn't resolved yet.
    var matchingLis = [];
    var excludedCount = 0;

    items.forEach(function(li) {
      var tags = (li.dataset.tags || '').split(',').filter(Boolean);
      var star = li.dataset.star || '';
      var ingList = (li.dataset.ingredients || '').split(',').map(function(s) { return s.trim(); });
      var visible = true;

      state.tags.forEach(function(t) {
        if (tags.indexOf(t) === -1) visible = false;
      });

      if (state.star && star !== state.star) visible = false;

      if (state.nameQuery) {
        // Named class, not querySelector('a') -- see reorderForTitleSearch()
        // above for why that stopped being safe with issue #40's badge links.
        var title = (li.querySelector('.recipe-title-link') || {}).textContent || '';
        if (HTF.ingredientSearch.fold(title.toLowerCase()).indexOf(state.nameQuery) === -1) visible = false;
      }

      if (state.meta.has('rewrite') && li.dataset.metaRewrite !== 'true') visible = false;
      if (state.meta.has('proofread') && li.dataset.metaProofread !== 'true') visible = false;
      if (state.meta.has('no-short') && li.dataset.metaShort === 'true') visible = false;
      if (state.meta.has('has-short') && li.dataset.metaShort !== 'true') visible = false;
      if (state.meta.has('draft') && li.dataset.metaDraft !== 'true') visible = false;

      if (state.ingredient) {
        // The two branches this used to spell out inline (a curated synonym
        // family by containment, anything else by per-word prefix) are
        // entriesMatchKey() now -- same rule, one copy, shared with the
        // exclusion filter below so an "(all)" button cannot come to mean one
        // thing when you filter FOR it and another when you filter it OUT.
        if (!entriesMatchKey(ingList, state.ingredient.replace(FAMILY_SUFFIX, '').trim())) {
          visible = false;
        }
      }

      /* LAST, deliberately. Everything above decides whether this row is one
         you asked for; this decides whether it is one you can't serve. Running
         it last is what makes excludedCount meaningful: it counts rows that
         survived every other filter and were dropped only for what they list,
         which is the number the panel reports back. */
      if (visible && rowIsExcluded(li)) {
        visible = false;
        excludedCount += 1;
      }

      if (visible) matchingLis.push(li);
      else if (!suppressList) li.style.display = 'none';
    });

    visibleCount = matchingLis.length;

    if (!suppressList) {
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

    // Matched by the badge's own data-tag/data-star, not by its text. The
    // text comparison this replaces could not tell a MOOD badge from a STAR
    // one: any badge whose words happened to equal the active star lit up as
    // matched. Latent while the two vocabularies had no overlap, and no
    // longer worth relying on now that issue #40 gives every badge the exact
    // value it stands for. Meta/draft badges carry neither attribute, so
    // they fall through both tests and are never matched, as before.
    document.querySelectorAll('.recipe-list .badge').forEach(function(badge) {
      var badgeTag = badge.dataset.tag;
      var badgeStar = badge.dataset.star;
      // 'badge-ingredient-hit' used to be removed here too. Nothing in the
      // repo ever ADDED it -- it was removed on every pass and applied on
      // none, so it could only ever be a no-op. Found when issue #237 deleted
      // its last stylesheet rule and the class turned out to have no other
      // reference anywhere. Gone with the rule.
      badge.classList.remove('badge--matched');
      if ((badgeTag && state.tags.has(badgeTag)) || (badgeStar && state.star === badgeStar)) {
        badge.classList.add('badge--matched');
      }
    });

    // Highlight matching ingredient pills
    var activeKey2 = state.ingredient ? state.ingredient.replace(' (all)', '').trim() : '';
    var activeSynonyms2 = activeKey2 ? IS.getSynonymWords(activeKey2) : null;
    var activeWords = (!activeSynonyms2 && activeKey2)
      ? getWords(activeKey2).map(IS.normaliseIngredientWord)
      : [];
    document.querySelectorAll('.recipe-list .ingredient-pill').forEach(function(pill) {
      pill.classList.remove('ingredient-pill--matched');
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
        pill.classList.add('ingredient-pill--matched');
        if (!pill.querySelector('.tag-shape')) {
          var shape = document.createElement('span');
          shape.className = 'tag-shape';
          shape.setAttribute('aria-hidden', 'true');
          pill.insertBefore(shape, pill.firstChild);
        }
      }
    });
    if (activeKey2 && window.HTF && HTF.tagShapes) HTF.tagShapes();

    // Null-guarded like every other lookup in this function. It was the one
    // exception among roughly fifteen, and the consequences were out of all
    // proportion to the omission: on a page without this element update()
    // threw HERE, three statements before updateInlineLabels(),
    // syncAriaPressed() and updateIngredientClamp(), so three unrelated
    // things silently stopped happening and nothing said why.
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

    var recipeCountEl = document.getElementById('recipe-count');
    if (recipeCountEl) {
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

    // Order matters between these two: syncAriaPressed() reads the .active
    // class syncFilterButtons() has just painted.
    syncFilterButtons();
    updateInlineLabels();
    updateIngredientClear();
    renderExcludeActive(excludedCount);
    syncAriaPressed();
    updateIngredientClamp();
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

      /* The exclude section is claimed whole, before any other branch. Its
         buttons wear .btn-tag for their appearance, so without this they would
         fall into the tag branch immediately below and toggle a MOOD tag
         called "peas" -- which does not exist, so the visible result would be
         a button that does nothing at all. The reveal button and the section's
         own inline clear have their own listeners; this just declines to
         second-guess them. */
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

      if (target.classList.contains('btn-meta')) {
        toggleMeta(target.dataset.meta);
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
        if (state.ingredient === ing) {
          state.ingredient = null;
          state.isSearching = true;
          target.classList.remove('active');
          var staleShape = target.querySelector('.tag-shape');
          if (staleShape) staleShape.remove();
        } else {
          state.ingredient = ing;
          state.isSearching = false;
          // The search box should echo what the button actually SHOWS, not
          // its internal match key -- for an aliased entry like "five-spice"
          // displayed as "Chinese five-spice powder", the two differ. See
          // display_names in _data/ingredient_words.yml.
          if (searchBox) searchBox.value = target.textContent.replace(' (all)', '').trim();
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

  // GitHub issue #40: a badge on a recipe row filters the list, and does
  // EXACTLY what clicking that filter's own button does -- same toggle, same
  // state, no second set of semantics to keep in step.
  //
  // Delegated on .recipe-list rather than bound per badge: there are eight
  // hundred-odd badges on this page, and pagination hides rows rather than
  // removing them, so a per-badge listener would be eight hundred listeners
  // for one behaviour.
  //
  // preventDefault(), because the href is a genuine link (see
  // _includes/recipe_badges.html) and following it would reload the index to
  // do in-place what has just been done in place. The href still earns its
  // keep: middle-click, ctrl/cmd-click and "open in new tab" never reach this
  // handler at all, and on a recipe page nothing intercepts it.
  if (recipeList) {
    recipeList.addEventListener('click', function(e) {
      if (!e.target || !e.target.closest) return;
      // closest(), not a check on e.target itself: a badge contains a
      // .tag-shape span with an injected <svg> inside it, so the click can
      // land on a descendant.
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
      // Reshuffle to a fresh random base order once the query is cleared —
      // same "returning to unfiltered" moment shuffleRecipeList() already
      // covers for the "clear all" button, so titles don't stay stuck in
      // whatever tiered order the last search left them in.
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

  if (clearButtons.length) {
    var clearAllFilters = function() {
      // ONE assignment, not a field-by-field emptying -- GitHub issue #52,
      // step one. A field-by-field version is a list that has to be kept in
      // step with hasAnythingToClear()'s list, and three times in two days it
      // wasn't. emptyState() walks the same FIELD_SPEC that predicate walks,
      // so a field added there is cleared here without this line changing.
      state = FilterState.emptyState();
      if (searchBox) searchBox.value = '';
      if (nameSearchBox) nameSearchBox.value = '';
      if (nameSearchClear) nameSearchClear.style.visibility = 'hidden';
      if (resultsPool) resultsPool.innerHTML = '';
      // The exclusions themselves are already gone -- emptyState() cleared the
      // Set, and update() repaints the "leaving out" list from it. These three
      // are the exclude picker's half-typed SEARCH, the same loose ends the
      // ingredient box's own box/pool/clear are being tidied for two lines up.
      // The panel is deliberately left open: revealing it was a decision about
      // what this session is doing, not a filter.
      if (excludeBox) excludeBox.value = '';
      if (excludePool) excludePool.innerHTML = '';
      if (excludeClear) excludeClear.style.visibility = 'hidden';
      // No button-class loop here any more: update() below calls
      // syncFilterButtons(), which paints every filter button from the state
      // this function has just emptied.
      // Reshuffles only here, on the deliberate "clear everything at once"
      // action — not on every incidental path back to zero active filters
      // (e.g. toggling the last individual tag off), which reads as an
      // unrelated action reordering the page underneath you.
      shuffleRecipeList();
      update();
    };
    clearButtons.forEach(function (btn) {
      btn.addEventListener('click', clearAllFilters);
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

  // GitHub issue #40: `/food/?star=lamb&tag=soup` arrives already filtered.
  // The grammar is assets/js/filter-state.js's; what belongs HERE is the
  // validation, because only this file can see which filters the page
  // actually offers.
  //
  // VALIDATED BY ITERATING THE BUTTONS AND COMPARING dataset, not by building
  // a `[data-tag="..."]` attribute selector out of the query string. The value
  // is arbitrary text off a URL, so a selector would raise the whole question
  // of quoting and escaping (and throw a SyntaxError on the wrong answer) for
  // no gain; a string comparison has no syntax to get wrong.
  //
  // Anything that survives parsing but matches no button is dropped in
  // silence -- same policy cook-timer.js already applies to `?protein=beef`.
  // A stale link to a retired tag lands on a perfectly good unfiltered index,
  // which is a better outcome than an error on a page that works fine.
  (function applyQueryString() {
    // No `!HTF.filterState` guard any more: since issue #52 this file's own
    // state object comes from that module at the top, so a page that loaded
    // filters.js without it never reaches this line. Same stance the file
    // already takes on HTF.ingredientSearch and HTF.recipeList.
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

    // Single-select, so the last one NAMED IN THE URL wins -- consistent with
    // clicking two star buttons in a row, where the second replaces the first.
    // Driven off the parsed list rather than off the buttons for exactly that
    // reason: iterating buttons would make DOM order, not the URL, decide.
    wanted.star.forEach(function(value) {
      if (isOffered('.btn-star', 'star', value)) state.star = value;
    });
  })();

  // A fresh page load starts from the same random base order "clear all"
  // produces, for the same reason: no recipe should be permanently stuck at
  // the bottom. That holds whether or not the query string above put a filter
  // on -- a filter narrows which rows show, it doesn't decide their order.
  // .recipe-list starts visibility:hidden in CSS specifically so this can run
  // before anything is shown — revealing it only now means the shuffled order
  // is what paints, not the server-rendered alphabetical order flashing first.
  shuffleRecipeList();
  update();
  if (recipeList) recipeList.style.visibility = 'visible';
});
