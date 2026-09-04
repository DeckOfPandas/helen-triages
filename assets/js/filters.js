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

  /* THE SHORTLISTED-ONLY BUTTON — #546, on the results heading rather than in
     the matrix. See food/index.html for why it is not one of the META FILTERS
     (that whole block is local-only) and why there is no separate shortlist
     page. Wired below, revealed there too: it ships `hidden`, and it is this
     script rather than shortlist.js that proves the filter half exists. */
  var shortlistOnlyBtn = document.getElementById('shortlist-only');
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

  // The dislike navigator (GitHub issue #52). It is a plain section beside HAS
  // TO HAVE now, always visible -- #exclude-reveal and #exclude-panel went with
  // issue #586, and with them this module's only piece of disclosure state.
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

  // ---------------------------------------------------------------------------
  // INDEX MEMORY — GitHub issue #387
  // ---------------------------------------------------------------------------
  // Going BACK to the index restores the list you left: same shuffle order,
  // same filters, same page, same scroll position. Arriving any other way is
  // untouched, so §13.7's rule that a fresh visit shuffles still holds exactly.
  //
  // WHY THIS EXISTS RATHER THAN JUST TRUSTING THE BROWSER. The first attempt at
  // #387 leaned on the back/forward cache: go back, the browser restores the
  // page without re-running anything, the order survives for free. It does not
  // work. Jekyll's dev server sends `Cache-Control: ... no-store ...` (measured,
  // not assumed -- curl -I against :4001), and no-store disqualifies a page from
  // bfcache in Chrome and Firefox. So on the machine this site is actually
  // developed on, bfcache can NEVER apply: the index re-renders and reshuffles,
  // which is what Helen saw, with her own back button as well as the new arrow.
  //
  // The deeper problem is that bfcache is an optimisation a browser may decline
  // for its own reasons. Building a feature on it means the feature works
  // sometimes -- and worse here, it would likely work on the deployed site and
  // never on :4001, so the page she looks at all day would disagree with the
  // live one. That is issue #235's trap running backwards.
  //
  // performance navigation type is a FACT rather than an optimisation: it says
  // whether this load was a back/forward navigation, and it says so whether or
  // not bfcache was involved. Paired with sessionStorage it needs nothing from
  // the browser's goodwill.
  var MEMORY_KEY = 'htf-index-memory-v1';

  // Rows carry no id of their own; the title link's href is the one thing on a
  // row that is unique and stable. Named class, not querySelector('a') -- see
  // reorderForTitleSearch() for why the first <a> stopped being the title.
  function rowKey(li) {
    var a = li.querySelector('.recipe-title-link');
    return a ? a.getAttribute('href') : '';
  }

  // FilterState.arrivedByGoingBack since #595, where the cocktail index needed
  // the same fact. The reasoning above moved with it, into that module's own
  // comment, where a test can reach the function it explains.
  var arrivedByGoingBack = FilterState.arrivedByGoingBack;

  /* Saved on pagehide rather than on every update: it fires on the way out of
     the page, including into bfcache, and unlike `unload` it does not itself
     disqualify the page from bfcache -- which matters on the deployed site,
     where bfcache DOES apply and this whole mechanism should stay out of its
     way. Storage being full, disabled or blocked is not worth breaking a page
     over; the fallback is a fresh list, which is what you had before -- and
     since #686 that swallowing lives once, in HTF.indexMemory, which the drinks
     index shares. The KEY and the RECORD stay here: they are this index's. */
  function saveIndexMemory() {
    if (!recipeList) return;
    HTF.indexMemory.save(MEMORY_KEY, {
      order: items.map(rowKey),
      filters: FilterState.serialise(state),
      // The chosen ingredient result's DISPLAY text, which is not its match
      // key -- an aliased entry like "five-spice" shows as "Chinese five-spice
      // powder" (see display_names in ingredient_words.yml). The box echoes
      // what the button shows, so that is what has to come back.
      ingredientLabel: searchBox ? searchBox.value : '',
      page: currentPage,
      showAll: showAll,
      scrollY: window.scrollY || 0
    });
  }

  /* Returns the saved record when it restored, or null. Null means "carry on as
     a fresh load" and every failure path returns it: not a back navigation,
     nothing stored, unparseable, or a record whose shape does not fit. Stored
     state is untrusted input -- see FilterState.deserialise's own note. */
  function restoreIndexMemory() {
    if (!recipeList || !arrivedByGoingBack()) return null;

    var saved = HTF.indexMemory.restore(MEMORY_KEY);
    if (!saved || !Array.isArray(saved.order)) return null;

    // Reorder by the saved keys, then append anything the record did not know
    // about. A recipe added since the record was written is new to the list and
    // belongs at the end rather than being dropped -- and dropping it would be
    // silent, which is the failure mode to avoid.
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

    /* HALF-FINISHED SEARCHES ARE NOT RESTORED, deliberately. isSearching and
       isExcludeSearching mean "there is text in that box and nothing chosen
       from its results yet" -- a pool of candidates mid-thought, not a filter.
       Rebuilding one would mean re-running a search to recreate buttons nobody
       had picked, and getting it slightly wrong leaves a results pool that does
       not match the text above it. A CHOSEN result is different and is restored
       below: it is an applied filter. */
    state.isSearching = false;
    state.isExcludeSearching = false;

    if (nameSearchBox) nameSearchBox.value = state.nameQuery || '';
    if (excludeBox) excludeBox.value = '';
    if (searchBox) searchBox.value = state.ingredient ? (saved.ingredientLabel || '') : '';

    /* Rebuild the chosen ingredient's button exactly as clicking it leaves
       things (see the .btn-ingredient branch of the matrix click handler): the
       pool holds that one button, active, with its tape shape. Reproducing the
       end state rather than replaying a search -- a replay would re-derive the
       whole candidate pool to then throw all but one of it away. */
    if (state.ingredient && resultsPool) {
      resultsPool.innerHTML = '';
      resultsPool.appendChild(makeIngredientButton(
        state.ingredient, saved.ingredientLabel || state.ingredient, true
      ));
      ensureActiveIngredientShape();
    }

    currentPage = (typeof saved.page === 'number' && saved.page > 0) ? saved.page : 1;
    showAll = !!saved.showAll;
    return saved;
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
     rules ingredient search already uses?

     THE RULE ITSELF IS IS.entriesMatchKey, moved into ingredient-search.js by
     issue #506 so it can be asked a question without a browser. It reads the
     vocabulary (singulars, synonyms), which is why it lives on the instance
     rather than here. This name stays as the local alias because it is what
     both call sites below already read as, and because it is what gets handed
     to FilterState.excludesRow -- which takes a matcher precisely so that
     module need not grow a vocabulary of its own. */
  var entriesMatchKey = IS.entriesMatchKey;

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

  /* `wordMatch` is the same flag makeIngredientButton() has always taken, and
     the two pickers now agree on it -- issue #390. They did not: this builder
     simply dropped `r.hasWordMatch` on the floor, so LEAVE OUT rendered every
     candidate identically while HAS TO HAVE, one box above, picked
     out the genuine matches. Same query, same ranked results, same code path
     (HANDOVER 8.1) -- one of them just never used the answer.

     What the flag means is worth restating here because it is the whole point
     of the treatment: it is a WORD-PREFIX match, not a substring one. Typing
     "pas" word-matches "anchovy paste" and "choux pastry", and does NOT match
     "antipasti vegetables" -- which is in the list, correctly, on a substring
     match. Nor does it match "farfalle" or "gnocchi", which are there as
     members of the `pasta` family and contain no "pas" at all. So the styled
     entries are the ones you meant, and the plain ones are the ones the
     vocabulary brought along. */
  function makeExcludeButton(value, label, wordMatch) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn-tag btn-exclude';
    if (wordMatch) btn.classList.add('btn-exclude--word-match');
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
      // Always a word match by construction, same as the include picker's
      // (all) buttons: a family only ever forms when its word already starts
      // with the query, so this is never in doubt.
      excludePool.appendChild(makeExcludeButton(label, label, true));
    });
    result.results.forEach(function (r) {
      // Same "don't offer 'chicken' next to 'chicken (all)'" suppression
      // renderResultsPool() applies, and for the same reason (issue #51):
      // two adjacent buttons that look like the same answer make you check
      // both.
      if (result.familyButtons.indexOf(fold(r.ing.trim().toLowerCase())) !== -1) return;
      excludePool.appendChild(makeExcludeButton(r.ing, r.label || r.ing, r.hasWordMatch));
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

    /* NO "leaving out" LABEL ANY MORE -- GitHub issue #363. The struck-through
       pill already says it, and the count sentence after it ("hiding 1 recipe
       that lists peas") says it again in full, so the words were the third
       telling of the same fact and the only one that could not also be clicked.

       The aria-label on each pill still says "stop leaving out <value>", and
       that is deliberate rather than an oversight: a screen reader gets no
       strikethrough, so for that reader the words were never redundant. What
       came out is the redundant VISIBLE copy, not the accessible name. */
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

  /* THE DISCLOSURE IS GONE -- issue #586, and what it took with it is the
     interesting part. This module used to own a reveal button, two label
     strings ("(I know what I don't want)" / "(hide leave out)"), an
     aria-expanded attribute, a `hidden` attribute on the panel, and a focus
     hand-off on open. Six moving parts, all of them bookkeeping for a piece of
     state that was deliberately NOT filter state -- so clear-all had to know to
     leave it alone, and #exclude-active had to live outside the panel so
     chosen pills survived a dismiss.

     None of that is here now, because the section is simply visible. Helen's
     ruling was that pairing LEAVE OUT with HAS TO HAVE frames it better than
     hiding it did, and the framing was the only thing the disclosure was
     buying. */

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

  /* THE SHORTLISTED-ONLY BUTTON — #546. Painted from state for exactly the
     reason syncFilterButtons() above is, and separately from it because it does
     not live in `.controls`: it sits on the results heading, beside the count it
     changes. `clear all` reassigns the whole state object without touching any
     markup, so a class toggled at click time would survive a clear that had
     already turned the filter off.

     BOTH THE CLASS AND aria-pressed HERE, where the matrix buttons have those
     painted by two functions one after the other. There is one of these, the
     ordering hazard that split them does not arise, and a single call site is
     one fewer thing to keep in step. */
  function syncShortlistOnly() {
    if (!shortlistOnlyBtn) return;
    /* `is-on`, NOT the `.active` every button in the matrix above wears. This
       one is not in the matrix, and `is-on` is what the shortlist's own
       controls already use on both sites (shortlist.js, and the cocktail
       index's mood and chaos buttons). One feature, one state class. */
    shortlistOnlyBtn.classList.toggle('is-on', !!state.shortlisted);
    shortlistOnlyBtn.setAttribute('aria-pressed', state.shortlisted ? 'true' : 'false');
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
      /* THE ROW, AS THE PREDICATE NEEDS IT. Every rule that used to be spelled
         out here is FilterState.rowMatchesFilters now (issue #506) -- the same
         decisions, with a DOM-free shape so they can be asked a question
         without a browser. What is left here is reading the attributes, which
         is this file's actual job.

         `titleFolded` IS BUILT ONLY WHEN THERE IS A NAME QUERY, exactly as the
         old inline branch did: it is a querySelector plus a fold per row per
         update, and there are ~370 rows on the local build. The predicate reads
         it only under the same condition, and its own comment says an empty one
         means "not asked". */
      var row = {
        tags: (li.dataset.tags || '').split(',').filter(Boolean),
        star: li.dataset.star || '',
        ingredients: (li.dataset.ingredients || '').split(',').map(function(s) { return s.trim(); }),
        isDraft: li.dataset.metaDraft === 'true',
        /* THE ONE ROW FACT THE BUILD DID NOT WRITE — #546. Every other key
           above is read off a data- attribute Jekyll emitted; this one is in
           this browser's localStorage and cannot be. Asked only when the filter
           is on, for the reason `titleFolded` below is: it is a lookup per row
           per update, and a lookup nobody is waiting on is worth not doing. */
        shortlisted: state.shortlisted
          ? HTF.shortlist.has(li.dataset.url || '')
          : false,
        // Named class, not querySelector('a') -- see reorderForTitleSearch()
        // above for why that stopped being safe with issue #40's badge links.
        titleFolded: state.nameQuery
          ? HTF.ingredientSearch.fold(
            ((li.querySelector('.recipe-title-link') || {}).textContent || '').toLowerCase())
          : ''
      };

      var visible = FilterState.rowMatchesFilters(row, state, entriesMatchKey);

      /* LAST, deliberately. Everything above decides whether this row is one
         you asked for; this decides whether it is one you can't serve. Running
         it last is what makes excludedCount meaningful: it counts rows that
         survived every other filter and were dropped only for what they list,
         which is the number the panel reports back. Two calls rather than one
         merged predicate for exactly that reason. */
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
    // threw HERE, three statements before updateInlineLabels() and
    // syncAriaPressed(), so two unrelated
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
    syncShortlistOnly();
    updateInlineLabels();
    updateIngredientClear();
    renderExcludeActive(excludedCount);
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

      /* The exclude section is claimed whole, before any other branch. Its
         buttons wear .btn-tag for their appearance, so without this they would
         fall into the tag branch immediately below and toggle a MOOD tag
         called "peas" -- which does not exist, so the visible result would be
         a button that does nothing at all. The section's own inline clear has
         its own listener; this just declines to second-guess it. */
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
      // There is no panel to leave open any more (issue #586). The reasoning
      // that used to sit here -- that revealing it was a decision about what
      // this session is doing rather than a filter, so clear-all must not undo
      // it -- is the reasoning the disclosure needed and the plain section
      // does not.
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

  /* --- the shortlist ---------------------------------------------------------
     GitHub issue #546. Two listeners: one for the filter's own button, one for
     any shortlist toggle anywhere on the page.

     REVEALED HERE. It ships `hidden` like every other JS-dependent control on
     both sites, and this is the script that makes its half of the feature real
     -- shortlist.js reveals the per-row toggles, this reveals the filter. A
     page that somehow loaded one and not the other shows exactly the half that
     works, rather than a filter that does nothing when pressed. */
  if (shortlistOnlyBtn) {
    shortlistOnlyBtn.hidden = false;
    shortlistOnlyBtn.addEventListener('click', function () {
      state.shortlisted = !state.shortlisted;
      update();
    });
  }

  /* A ROW'S OWN TOGGLE CHANGED — dispatched by shortlist.js, which owns the
     store and the controls and knows nothing about this page's filters.

     UNCONDITIONAL, not gated on `state.shortlisted`. When the filter is on, the
     row that was just un-shortlisted has to leave the list, which is what the
     filter means. When it is off, `update()` still has work: it repaints the
     count on the button, and the row object it rebuilds is the only place the
     shortlisted flag is ever read from.

     `update(true)` PRESERVES THE PAGE NUMBER, and that is the point. Marking
     something on page 3 of the results must not throw you back to page 1 --
     you did not change what you were looking for. Every other caller that
     passes `true` here (the pager, the see-all button, the restore) is making
     the same claim: the filter set has not changed. */
  document.addEventListener('htf:shortlist-change', function () {
    update(true);
  });

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
  //
  // ARRIVING BY GOING BACK IS THE ONE EXCEPTION (issue #387): the list you left
  // is restored instead, order and filters together, and the shuffle is skipped
  // because reshuffling is precisely what you did not want. Every other way of
  // reaching this page -- typed, bookmarked, followed, reloaded -- still
  // shuffles, so the rule above is unchanged rather than weakened.
  var restored = restoreIndexMemory();
  if (!restored) shuffleRecipeList();
  update(!!restored);          // preserve the restored page number
  if (recipeList) recipeList.style.visibility = 'visible';

  // After the reveal, so the page has its real height to scroll within.
  if (restored && typeof restored.scrollY === 'number') {
    window.scrollTo(0, restored.scrollY);
  }

  window.addEventListener('pagehide', saveIndexMemory);
});
