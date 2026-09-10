/* =============================================================================
   COCKTAILS INDEX — DOM wiring. Designed with Helen, 2026-08-26.
   =============================================================================
   Five named questions: YOLO, mood, hassle, has-to-have/leave-out, and the way
   past all of it. Everything is already in the DOM — 115 drinks is nothing —
   so this toggles [hidden] and reorders the list in place. No fetch.

   THIS FILE IS DOM WIRING AND NOTHING ELSE, since GitHub issue #579. It used to
   be 428 lines that reused nothing from the food index's stack and hand-rolled
   three things food had deliberately extracted: vocabulary derivation, ranked
   prefix matching, and filter state as loose variables. Two of those were
   wrong, and neither could be asked a question without opening a browser:

     - both matching directions were a raw SUBSTRING test against the whole
       concatenated attribute, so `gin` hid twelve drinks whose only gin-shaped
       ingredient was ginger, and `apple juice` matched fifteen drinks that
       have pineapple juice;
     - nothing was folded, so nineteen accented ingredients and three accented
       drink names were unreachable from an ASCII keyboard.

   Where it lives now:

     assets/js/cocktail-search.js   the pool, the ranking, the declared-family
                                    umbrellas, and the two matching rules.
                                    Pure. tests/js/cocktail-search.test.js.
     assets/js/filter-state.js      WHAT this index's filter state is, as
                                    COCKTAIL_FIELDS — the same mechanism food
                                    uses over a different table.
     assets/js/ingredient-search.js fold, getWords, and orderByBand: the
                                    three-band ordering rule, shared rather
                                    than re-derived for the second time.

   NOTHING IS PARSED OUT OF THE RENDERED MARKUP. Every fact a filter needs was
   written into a data- attribute at build time by cocktails/index.html:
   data-moods, data-chaos, data-name and a pre-lowercased data-ingredients. A
   filter that reads textContent is a filter that breaks the first time someone
   restyles a card — and #501 is the case where it broke for real, when the card
   stopped printing the item the script was matching on.

   HOW THE AXES COMBINE. Settled by Helen 2026-08-27, #478 and #479:

     - Two moods selected means EITHER, and drinks matching BOTH rank first.
     - Include chips are AND: adding an ingredient narrows.
     - Mood AND ingredient(s) AND chaos, between sections.
     - Everything shown is in RANDOMISED order, within its rank.

   The ranking is what makes OR usable. AND across moods is nearly always empty
   -- `tiki` AND `no juicing` is a handful of drinks -- so OR is the only
   answer that keeps the index alive, but plain OR stops narrowing anything
   once you pick a second mood.

   THE SHUFFLE HAPPENS ONCE PER PAGE LOAD, NOT PER KEYSTROKE, and that is the
   part worth not undoing. Each card is given a random sort key at startup and
   keeps it; filtering re-ranks against those fixed keys. Re-shuffling on every
   filter change would make cards leap around while you type into the
   has-to-have box, which reads as a bug however correct it is.
   ============================================================================= */
(function () {
  /* THE LIST'S OWN ITEMS, NOT EVERYTHING WEARING THE CLASS. `.drink-cards > li`
     is what the template has always meant by "a card in the list", and the
     section's own `data-universe-rows` names the same shape.

     IT WAS ONCE LOAD-BEARING AND IS NOW MERELY CORRECT, which is worth saying
     rather than deleting: on 2026-09-04 the universe pick carried `.drink-card`
     too, so selecting by class swept in a card with no data- attributes, and the
     index died on the first `card.dataset.ingredients` before drawing a single
     drink. The pick dropped that class on 2026-09-05 and the crash cannot happen
     today -- but the scoping stays, because the rule it encodes is about what
     belongs to the list, not about which element last collided with it. */
  var cards = Array.prototype.slice.call(document.querySelectorAll('.drink-cards > li'));
  if (!cards.length) return;

  /* PAGINATION -- #694, ported from the food index rather than designed again.
     The arithmetic is HTF.recipeList.paginate (assets/js/recipe-list.js), the
     same pure function filters.js uses, so the two indexes cannot drift about
     what page 3 of 7 means.

     TWENTY, WHICH IS FOOD'S NUMBER. The card grid is two columns at the site's
     900px width, so 20 is ten full rows and no ragged last one -- and picking a
     different number for the same control on the other site would be a decision
     nobody made. */
  var PAGE_SIZE = 20;
  var currentPage = 1;
  var showAll = false;

  var pagination = document.querySelector('.drink-pagination');
  var pagePrevBtn = document.getElementById('drink-page-prev');
  var pageNextBtn = document.getElementById('drink-page-next');
  var pageStatusEl = document.getElementById('drink-page-status');
  var pageSeeAllBtn = document.getElementById('drink-page-see-all');

  var CS = HTF.cocktailSearch;
  var FAMILY_SUFFIX = CS.FAMILY_SUFFIX;
  // Accent folding, shared with food rather than re-derived -- the same
  // function the search itself compares with, so "what the picker suppresses"
  // and "what the picker matched" can never disagree about a ç.
  var fold = HTF.ingredientSearch.fold;

  /* THE VOCABULARY comes from _data/cocktails/ingredients.yml, emitted as JSON
     by cocktails/index.html. Nothing about families or search thresholds is
     written down in this file; to change either, edit the YAML. Same contract
     food/index.html has with filters.js, and the same fallback: a page without
     the block still searches, it just offers no (all) buttons. */
  function readJson(id, what, fallback) {
    var node = document.getElementById(id);
    if (!node) {
      console.warn(
        'cocktail-index.js: no #' + id + ' block found. cocktails/index.html ' +
        'should emit ' + what + ' as JSON before loading this script.'
      );
      return fallback;
    }
    try {
      return JSON.parse(node.textContent);
    } catch (e) {
      console.warn('cocktail-index.js: could not parse #' + id + ' — ' + e.message);
      return fallback;
    }
  }

  var VOCABULARY = (function () {
    var fallback = { search: { min_query_chars: 2, family_button_min_chars: 3, pool_cap: 8 },
                     families: [], family_of: {}, card_names: {} };
    var parsed = readJson('drink-vocabulary', '_data/cocktails/ingredients.yml', fallback);
    parsed.search = parsed.search || fallback.search;
    parsed.families = parsed.families || [];
    parsed.family_of = parsed.family_of || {};
    parsed.card_names = parsed.card_names || {};
    return parsed;
  })();

  /* The bottle dictionary (#529). Absent, the pool still works and still refuses
     a disjunction -- that rule is structural -- but two spellings of one bottle
     stop collapsing. A degraded picker, not a broken page. */
  var BOTTLES = readJson('drink-bottles', '_data/cocktails/bottles.yml',
                         { bottles: {}, unresolved_suggestions: {} });

  var Search = CS.create(VOCABULARY, BOTTLES);

  /* WHAT EACH DRINK IS MADE OF, for the shopping list -- #546. Keyed by the same
     `drink.url` the cards carry as `data-url` and the shortlist stores, so the
     three agree by construction. Absent, the shopping list renders nothing and
     the rest of the index is untouched. */
  var INGREDIENTS = readJson('drink-ingredients', 'the drinks’ own front matter', {});

  /* HOW MUCH A `to top` POURS -- #746, `top_up_ml` from costs.yml. Present on
     both sites, unlike the costs below: it is a volume rather than a price.
     Absent, every `to top` keeps the `(×3)` count reading it had before, which
     is why this can use `readJson`'s fallback without a special case. */
  var TOP_UPS = readJson('drink-top-ups', '_data/cocktails/costs.yml', {});

  /* WHAT EACH DRINK COSTS A GLASS. LOCAL ONLY and USUALLY ABSENT: the block is
     emitted by cocktails/index.html behind `site.show_costs`, declared in
     _config_local.yml and nowhere else, so on the deployed site this is `{}`
     and every price below simply does not render.

     READ WITHOUT `readJson` DELIBERATELY, because that helper warns to the
     console when a block is missing -- correct for the vocabulary, wrong here,
     where missing is the NORMAL state and a warning on every production page
     load would be noise teaching people to ignore warnings. */
  var COSTS = (function () {
    var node = document.getElementById('drink-costs');
    if (!node) return {};
    try {
      return JSON.parse(node.textContent);
    } catch (e) {
      console.warn('cocktail-index.js: could not parse #drink-costs — ' + e.message);
      return {};
    }
  })();

  /* GBP PER LITRE PER GENERIC AND PER BOTTLE — #820. Local-only and usually
     absent, exactly like COSTS above and read the same silent way; `null`
     rather than `{}` so `shopping-list.js` can tell "no table" from "an empty
     one" and price nothing at all. */
  var RATES = (function () {
    var node = document.getElementById('drink-rates');
    if (!node) return null;
    try {
      return JSON.parse(node.textContent);
    } catch (e) {
      console.warn('cocktail-index.js: could not parse #drink-rates — ' + e.message);
      return null;
    }
  })();

  /* "@ £2.34", or "@ £2.10–£3.40" where the drink spans a range, or nothing at
     all. Helen asked for it "quietly again", so it is a suffix on a line that
     already exists rather than a column of its own.

     THE FIGURE IS PER GLASS AND IS NOT MULTIPLIED BY THE COUNT. "2 Mai Tai @
     £5.24" is two of a drink that costs £5.24 each -- the same reading as a
     menu, and the same number the drink's own page shows. Multiplying here
     would make the glasses box change a price labelled per glass, which is the
     bug that had to be taken out of cocktail-scale.js on the same day. */
  /* WHICH BOTTLE HELEN HAS PICKED FOR WHICH POUR -- #818, and "per drink" is
     her ruling: two drinks that both want a reposado may choose differently.
     Keyed url -> generic -> bottle name.

     IN MEMORY ONLY, DELIBERATELY. She chose "price and the list line" over
     "and it sticks": a stored choice outlives the bottle it names, and a list
     that opens tomorrow already committed to a rum that left the house is
     worse than one that asks again. The shortlist itself persists; this does
     not. */
  var CHOSEN = {};

  function chosenBottle(url, generic) {
    return (CHOSEN[url] || {})[generic] || null;
  }

  /* WHAT ONE GLASS COSTS, AFTER ANY CHOICE -- #818.

     THE ARITHMETIC IS SUBTRACT-AND-ADD, and the plugin emitted exactly what it
     needs: each choosable pour carries what it contributes to the range TODAY
     (`lo`, `hi`) and what each candidate bottle would cost instead. So a chosen
     bottle is `total - what that pour was contributing + what this one costs`,
     and the browser never has to know what an excluded unit is or which of a
     suggestion and a generic wins.

     UNCHOSEN POURS ARE LEFT ALONE, which is what makes the opening state the
     full range Helen asked for: a drink with two choices and one made narrows
     by exactly that one. */
  function costFor(url) {
    var c = COSTS[url];
    if (!c) return null;
    var lo = Number(c.lo);
    var hi = Number(c.hi);
    (c.choices || []).forEach(function (choice) {
      var bottle = chosenBottle(url, choice.generic);
      if (!bottle) return;
      var price = choice.bottles[bottle];
      if (typeof price !== 'number') return;
      lo = lo - Number(choice.lo) + price;
      hi = hi - Number(choice.hi) + price;
    });
    return { lo: lo, hi: hi };
  }

  function costSuffix(url) {
    var c = costFor(url);
    if (!c) return '';
    var lo = '£' + Number(c.lo).toFixed(2);
    if (Math.abs(c.hi - c.lo) < 0.005) return ' @ ' + lo;
    return ' @ ' + lo + '–£' + Number(c.hi).toFixed(2);
  }

  /* THE RADIO ROWS UNDER A DRINK -- #818, and Helen picked the shape: "a row
     per pour that has a choice", with the generic labelling each set so you can
     see WHICH pour you are choosing a bottle for.

     ONE `name` PER DRINK AND POUR, which is what makes them behave as radios
     rather than as a row of unrelated buttons -- and it has to include the URL,
     or two shortlisted drinks wanting a reposado would share one group and
     choosing for the second would silently unchoose the first. That is the same
     bug in miniature as the per-list choice Helen ruled against.

     NO "no preference" OPTION, because the unchosen state IS no preference and
     it is where every list starts. Clearing one is not a thing she asked for;
     if it turns out to be wanted, it is a fifth radio rather than a redesign. */
  function choiceRows(url) {
    var c = COSTS[url];
    if (!c || !c.choices || !c.choices.length) return '';
    return c.choices.map(function (choice, i) {
      var group = 'bottle-' + i + '-' + url;
      var options = Object.keys(choice.bottles).map(function (bottle) {
        var id = group + '-' + bottle;
        return '<label class="shopping-list-bottle-choice">' +
          '<input type="radio" name="' + HTF.escapeHtml(group) + '"' +
          ' value="' + HTF.escapeHtml(bottle) + '"' +
          ' data-url="' + HTF.escapeHtml(url) + '"' +
          ' data-generic="' + HTF.escapeHtml(choice.generic) + '"' +
          (chosenBottle(url, choice.generic) === bottle ? ' checked' : '') +
          ' aria-label="' + HTF.escapeHtml(bottle) + '">' +
          '<span>' + HTF.escapeHtml(bottle) + '</span>' +
          '</label>';
      }).join('');
      return '<span class="shopping-list-choice">' +
        '<span class="shopping-list-choice-name">' +
        HTF.escapeHtml(choice.generic) + '</span>' +
        options +
        '</span>';
    }).join('');
  }

  /* ONE BOTTLE, HOWEVER IT WAS WRITTEN. Built from the dictionary already on the
     page rather than from a second blob: every declared name maps to itself and
     every alias maps to its bottle, which is what stops a shopping list printing
     `El Dorado 3 / ED3 / El Dorado 3yo` beside one line. The ingredient search
     does the same job with its own copy inside cocktail-search.js (#529); this
     is fifteen lines against widening that module's contract, and if the
     dictionary is missing the list falls back to case-folding on its own. */
  var BOTTLE_ALIASES = (function () {
    var map = {};
    var declared = (BOTTLES && BOTTLES.bottles) || {};
    var names = Object.keys(declared);
    function fold(name) { return HTF.shoppingList.foldKey(name); }

    /* TWO PASSES, AND THE ORDER IS THE POINT: aliases first, then the declared
       names over the top. A DECLARED BOTTLE NAME MUST ALWAYS WIN -- if one
       bottle lists another bottle's real name among its aliases, the real name
       is the answer, and a single pass would let whichever came later in the
       object decide. That is a bug that would show up as one bottle silently
       renamed to another, on a page nobody would think to check. */
    names.forEach(function (name) {
      ((declared[name] || {}).aliases || []).forEach(function (alias) {
        if (!map[fold(alias)]) map[fold(alias)] = name;
      });
    });
    names.forEach(function (name) { map[fold(name)] = name; });
    return map;
  })();

  /* ONE state object, not five loose variables — GitHub issue #579. The fields,
     their cleared values and the "is anything set" answer all come from
     COCKTAIL_FIELDS in assets/js/filter-state.js, where the reasoning for each
     lives and where tests/js/filter-state.test.js can reach them.

     Reassigned wholesale by clearAll(), never rebuilt field by field: that is
     the whole point, and it is why #541's clear-all button can be added at all
     without re-running the bug food hit three times in two days. */
  var FilterState = HTF.filterState.create(HTF.filterState.COCKTAIL_FIELDS);
  var state = FilterState.emptyState();

  /* OFF THE MODULE, NOT OFF THE BINDING ABOVE, and the difference is not
     cosmetic: `create(spec)` returns only the seven spec-bound functions, so
     `FilterState.arrivedByGoingBack` is undefined -- and calling undefined
     throws, taking the rest of this file's startup with it. It did, for one
     commit: the restore never ran, apply() never ran, and the pagehide listener
     was never registered, so the index stopped shuffling as well as stopped
     remembering. Helen found it in the first minute of looking.

     Bound here rather than called inline so there is one place to be wrong,
     and test_a_filter_state_binding_is_only_asked_for_what_it_has now checks
     every such name in both index scripts. */
  var arrivedByGoingBack = HTF.filterState.arrivedByGoingBack;

  var moodBtns  = Array.prototype.slice.call(document.querySelectorAll('.btn-mood'));
  var chaosBtns = Array.prototype.slice.call(document.querySelectorAll('.btn-chaos'));
  var incInput  = document.getElementById('drink-include');
  var excInput  = document.getElementById('drink-exclude');
  var incPool   = document.getElementById('drink-include-pool');
  var excPool   = document.getElementById('drink-exclude-pool');
  var countEl   = document.getElementById('drink-count-n');
  var wordEl    = document.getElementById('drink-count-word');
  var noneEl    = document.querySelector('.drink-none');
  var nameInput = document.getElementById('drink-name');
  var filters   = document.querySelector('.drink-filters');
  var list      = cards[0].parentNode;

  /* THE SHORTLISTED-ONLY BUTTON -- #546, on the count line rather than in
     `.drink-filters`. cocktails/index.html says why: the five filter sections
     are all questions about what a drink IS, and a sixth holding one button
     about what this browser has marked would read as another of them. Food's
     index carries the twin of this on its own results heading. */
  var shortlistOnlyBtn = document.getElementById('shortlist-only');

  // Declared here rather than beside the code that builds them, so apply() can
  // never read them before they exist. Populated further down.
  var clearAllButtons = [];
  var redrawPool = {};

  /* Mood and hassle are one filter with two headings: both render .btn-mood
     and both write into `state.moods`, because a drink matching either is
     matched the same way. Only the CLEAR links are per-section, so the two
     sets are told apart by which block they sit in rather than by a second
     data attribute the template would have to keep in step. */
  function inHassle(btn) {
    return !!btn.closest('.drink-filter--hassle');
  }

  function moodBtnsIn(hassle) {
    return moodBtns.filter(function (b) { return inHassle(b) === hassle; });
  }

  /* Everything each card needs, read ONCE. The attribute is split here rather
     than probed on every keystroke, which is also what makes the seam between
     two ingredients unreachable: the old substring test ran against the joined
     string, where a query could match across the `|` and nothing on the card
     corresponded to what had matched.

     The random sort key is fixed for the life of the page — see the note on
     ordering at the top. */
  var model = cards.map(function (card) {
    var nameEl = card.querySelector('.drink-card-name a');
    return {
      card: card,
      entries: CS.splitEntries(card.dataset.ingredients),
      moods: (card.dataset.moods || '').split('|').filter(Boolean),
      name: card.dataset.name || '',
      chaos: card.dataset.chaos || '',
      /* #732. A STRING, NOT A BOOLEAN, and read as one all the way through:
         `dataset` hands back the attribute text, so `'false'` is a truthy
         JavaScript value and coercing it here would make every drink look
         made. Compared against `'false'` in matches() for the same reason. */
      madeBefore: card.dataset.madeBefore || '',
      /* The shortlist's key -- #546, `drink.url` written by the template. Read
         once here with everything else; whether it IS shortlisted is asked in
         matches(), because that answer can change under the page while this one
         cannot. */
      url: card.dataset.url || '',
      key: Math.random(),
      nameEl: nameEl,
      /* The unmarked title, stashed once. The highlight always rebuilds from
         this rather than from the link's current (possibly already wrapped)
         text, so re-running it on every keystroke never compounds — the same
         reason filters.js stashes dataset.titleText. */
      title: nameEl ? nameEl.textContent : '',
      moodEls: Array.prototype.slice.call(card.querySelectorAll('.drink-card-mood')),
      ingEls: Array.prototype.slice.call(card.querySelectorAll('.drink-card-ing')).map(function (el) {
        return { el: el, entries: CS.splitEntries(el.dataset.ing) };
      })
    };
  });

  /* ONE GROUP PER INGREDIENT, from data-ing, not one per card from
     data-ingredients. A `suggestion` is a bottle FOR the generic written beside
     it, and the card-level attribute has already flattened that pairing away --
     so it is the only shape that can express "do not offer a bottle when its
     category is offered". See buildPool's own note. */
  var pool = Search.buildPool(model.reduce(function (groups, d) {
    d.ingEls.forEach(function (ing) { groups.push(ing.el.dataset.ing); });
    return groups;
  }, []));

  function chosen(field) {
    var out = [];
    state[field].forEach(function (v) { out.push(v); });
    return out;
  }

  /* The two chip lists, flattened ONCE per pass rather than per card. matches()
     reads these; apply() refreshes them before the loop. 115 cards times two
     Set walks per keystroke is not expensive, but it is a rebuild of something
     that cannot change inside the loop. */
  var activeInclude = [];
  var activeExclude = [];

  /* How many of the SELECTED moods this drink has. 0 when nothing is selected,
     which is what makes the no-filter case fall through to pure random order
     without a special case. */
  function moodScore(d) {
    if (!state.moods.size) return 0;
    var n = 0;
    d.moods.forEach(function (m) { if (state.moods.has(m)) n++; });
    return n;
  }

  /* WHICH MOOD VALUES BELONG TO WHICH SECTION -- #695. Read once from the
     buttons, because the section is a fact about the MARKUP (which
     `.drink-filter--hassle` a button sits in) and not about the drink.

     MOOD AND HASSLE ARE TWO QUESTIONS SHARING ONE Set. `state.moods` holds the
     selections from both sections, and that is right -- they are ORed together
     and a drink matching either survives. But it means `moodScore` cannot tell
     "answers both of my questions" from "answers one of them twice", and those
     are not the same drink. */
  var MOOD_VALUES = null;
  var HASSLE_VALUES = null;

  function sectionValues() {
    if (MOOD_VALUES) return;
    MOOD_VALUES = {};
    HASSLE_VALUES = {};
    moodBtnsIn(false).forEach(function (b) { MOOD_VALUES[b.dataset.mood] = true; });
    moodBtnsIn(true).forEach(function (b) { HASSLE_VALUES[b.dataset.mood] = true; });
  }

  /* How many of the mood SECTIONS this drink answers: 0, 1 or 2.
     Helen's ruling on #695, 2026-09-06: "extend the ranking, keep the
     narrowing" -- all filter hits first, then fewer.

     IT ONLY EVER CHANGES THE ORDER WHEN BOTH SECTIONS ARE ASKED, and that falls
     out rather than being special-cased. If only MOOD has selections then every
     survivor answers it (they survived `matches`), so every survivor scores 1
     and the tie falls through to moodScore exactly as before. Ask both, and a
     drink answering `sharp` AND `no juicing` comes above one answering `sharp`
     and `aperitivo` -- which is the sense in which it has more of what you
     asked for.

     WHY NOT COUNT THE OTHER SECTIONS TOO, which is what "every filter that
     matched" sounds like. Because they cannot discriminate: HAS TO HAVE, LEAVE
     OUT, YOLO and the name search all NARROW, so by the time a drink is in this
     list it satisfies every one of them and they score identically for
     everybody. Mood is the only OR section on the page, so it is the only place
     a rank has anything to rank. Counting the rest would add four constants to
     every comparison. */
  function sectionScore(d) {
    if (!state.moods.size) return 0;
    sectionValues();
    var mood = false;
    var hassle = false;
    d.moods.forEach(function (m) {
      if (!state.moods.has(m)) return;
      if (HASSLE_VALUES[m]) hassle = true;
      else if (MOOD_VALUES[m]) mood = true;
    });
    return (mood ? 1 : 0) + (hassle ? 1 : 0);
  }

  function matches(d) {
    /* SHORTLISTED -- #546, and first because it is the cheapest test here and
       the most narrowing one anybody turns on: one lookup against a list that
       is usually a handful of drinks long, in front of four ingredient walks.
       Everything below it is unchanged.

       ASKED OF THE STORE, NOT OF THE MODEL. Every other fact in `d` was written
       into the markup by the build; this one is in this browser's localStorage
       and can change between two calls of this function -- which is exactly
       what happens when you press a card's own toggle while the filter is on. */
    if (state.shortlisted && !HTF.shortlist.has(d.url)) return false;

    /* mood: OR within the section, ranked by moodScore below. If this ever
       becomes AND the ranking is redundant rather than merely unused — see the
       note at the top, and issue #478. */
    if (state.moods.size && moodScore(d) === 0) return false;

    /* `open` IS A STATE, NOT A FILTER, and this is the fix rather than an
       oversight. It used to be `yolo`, meaning ship is not yes-or-better -- so
       the button for "I'll try anything" was the one button guaranteed to hide
       all 55 of the best drinks. Helen, 2026-08-27: "'I'm open to chaos' ...
       includes all drinks". So only `good` narrows. */
    if (state.chaos === 'good' && d.chaos !== 'good') return false;

    /* `unmade` DOES narrow, and that is fine -- #732. The rule the comment
       above protects is that the button for "I'll try anything" must not
       narrow, not that no third button ever may. This one says what it narrows
       to, which is the 20 drinks Helen has never made.

       IT READS `madeBefore` AND NOT `chaos`/`ship`. Every unmade drink says
       `ship: "who knows"` today, so `d.chaos` would give the same 20 -- and it
       would stop the day she makes one, because `made_before` flips while
       `ship` stays `who knows` until she rates it. The drink she just made
       would vanish from the wrong list. */
    if (state.chaos === 'unmade' && d.madeBefore !== 'false') return false;

    /* AND across include: each chip you add narrows. That is the opposite of
       the mood rule and deliberately so — adding an ingredient means "and this
       one too", which is how a cupboard works. */
    var i;
    for (i = 0; i < activeInclude.length; i++) {
      if (!Search.matchesInclude(d.entries, activeInclude[i])) return false;
    }
    for (i = 0; i < activeExclude.length; i++) {
      if (Search.matchesExclude(d.entries, activeExclude[i])) return false;
    }

    return Search.matchesName(d.name, state.nameQuery);
  }

  /* Put the list in rank order: more matched moods first, random within a
     rank, hidden cards last so they never split a run of visible ones.

     REWRITTEN ONLY WHEN IT ACTUALLY CHANGES. Moving 115 nodes on every
     keystroke is wasteful and, worse, it would scroll the page under the
     reader's cursor while they type. */
  function reorder(order) {
    var same = true;
    var kids = list.children;
    for (var i = 0; i < order.length; i++) {
      if (kids[i] !== order[i]) { same = false; break; }
    }
    if (same) return;
    var frag = document.createDocumentFragment();
    order.forEach(function (card) { frag.appendChild(card); });
    list.appendChild(frag);
  }

  /* THE MATCHED RUN OF A DRINK NAME — GitHub issue #564, food's own treatment.
     The offsets come from cocktail-search.js and index the ORIGINAL title, so a
     name keeps its accents while an unaccented query still finds it: "vieux
     carre" marks the "Carré" in Vieux Carré. Rebuilt from the stashed title
     every pass rather than patched in place. */
  function paintNameHighlight(d) {
    if (!d.nameEl) return;
    var at = state.nameQuery ? Search.nameHighlight(d.title, state.nameQuery) : null;
    var mark = at ? (at.start + ':' + at.end) : '';
    // Only when it actually changes. Every card's name would otherwise be
    // rewritten on every keystroke, including the 114 that are not highlighted
    // at all -- and rewriting a node's contents under a reader is the same
    // wastefulness reorder() already declines.
    if (d.painted === mark) return;
    d.painted = mark;
    if (!at) {
      d.nameEl.textContent = d.title;
      return;
    }
    d.nameEl.innerHTML =
      HTF.escapeHtml(d.title.slice(0, at.start)) +
      '<mark class="drink-name-hit">' + HTF.escapeHtml(d.title.slice(at.start, at.end)) + '</mark>' +
      HTF.escapeHtml(d.title.slice(at.end));
  }

  function showClear(id, active) {
    var el = document.getElementById(id);
    if (el) el.hidden = !active;
  }

  /* --- the shopping list ---------------------------------------------------
     #546's stretch goal. The arithmetic is assets/js/shopping-list.js; this
     gathers the entries and paints the answer.

     SHOWN ONLY WHILE THE SHORTLISTED FILTER IS ON, which is what makes it "the
     bottom of my shortlist listing" rather than a running total under a browse.

     IT READS THE STORE, NOT THE VISIBLE CARDS, and the difference matters the
     moment a second filter is on: shortlist three drinks, then narrow to `no
     chaos please`, and the cards on screen are a subset of the shortlist. The
     list you shop from is the one you shortlisted. */
  var shoppingEl = document.getElementById('shopping-list');
  var shoppingItems = shoppingEl && shoppingEl.querySelector('.shopping-list-items');
  // #817. Absent is normal: the paragraph is only useful where prices are.
  var shoppingTotal = shoppingEl && shoppingEl.querySelector('.shopping-list-total');
  var shoppingDrinks = shoppingEl && shoppingEl.querySelector('.shopping-list-drinks');
  var shoppingEmpty = shoppingEl && shoppingEl.querySelector('.shopping-list-empty');
  var setAllInput = document.getElementById('shopping-list-setall');

  /* The card's own title, for the per-drink list. Read off the model rather than
     re-derived: `d.title` is the unmarked title card-name highlighting stashes,
     so a drink found by a name search still lists under its real name. */
  var titleByUrl = (function () {
    var map = {};
    model.forEach(function (d) { if (d.url) map[d.url] = d.title || d.url; });
    return map;
  })();

  /* THE DRINKS, IN THE ORDER THEY WERE SHORTLISTED. The store keeps insertion
     order, which is the order Helen marked them in -- a more useful order for
     a planning list than either alphabetical or the index's own ranking, and
     one she can predict. Drinks no longer on the page are dropped, the same
     silence a renamed drink already gets everywhere else in this feature. */
  function shortlistedDrinks() {
    return HTF.shortlist.list().filter(function (url) {
      return Object.prototype.hasOwnProperty.call(INGREDIENTS, url);
    });
  }

  function renderShoppingList() {
    if (!shoppingEl) return;
    shoppingEl.hidden = !state.shortlisted;
    if (!state.shortlisted) return;

    var urls = shortlistedDrinks();

    if (shoppingEmpty) shoppingEmpty.hidden = urls.length > 0;

    /* THE PER-DRINK COUNTS. Rebuilt whole, like the totals below -- but NOT
       while one of its own inputs has focus, because replacing the node under a
       typing cursor loses the caret and the keystroke. `renderTotals()` is
       called on its own from the input handler for exactly that reason. */
    if (shoppingDrinks) {
      shoppingDrinks.innerHTML = urls.map(function (url) {
        return '<li>' +
          '<input type="number" class="shopping-list-glasses" min="1" max="99" step="1" ' +
          'inputmode="numeric" value="' + HTF.shortlist.glasses(url) + '" ' +
          'data-url="' + HTF.escapeHtml(url) + '" ' +
          'aria-label="glasses of ' + HTF.escapeHtml(titleByUrl[url] || url) + '">' +
          '<span>' + HTF.escapeHtml(titleByUrl[url] || url) +
          /* The price is INSIDE the title span, not a sibling, so it wraps with
             the name on a narrow screen instead of being pushed onto a line of
             its own away from the drink it belongs to. Empty string everywhere
             `show_costs` is off, which is everywhere but Helen's laptop. */
          '<span class="shopping-list-cost">' + costSuffix(url) + '</span>' +
          '</span>' +
          // #818. After the name, indented, one row per pour with a choice.
          choiceRows(url) +
          '</li>';
      }).join('');
    }

    renderTotals(urls);
  }

  function renderTotals(urls) {
    if (!shoppingItems) return;

    var entries = [];
    (urls || shortlistedDrinks()).forEach(function (url) {
      var glasses = HTF.shortlist.glasses(url);
      (INGREDIENTS[url] || []).forEach(function (ing) {
        /* A CHOICE NARROWS THE LIST LINE, NOT JUST THE PRICE -- #818, Helen
           picked "price and the list line" over price alone: "choosing is how
           you decide what to buy, so the list should say what you decided."

           IT IS DONE HERE, ON THE ENTRY, rather than anywhere downstream, and
           that is what makes it cost nothing: `shopping-list.js` already
           prefers the named bottles over the generic when pricing, and already
           builds the bracketed note from them. Replacing the suggestion with
           the one she chose therefore fixes the price AND the note in one
           move, with no new argument to thread through.

           THE GENERIC IS JOINED THE SAME WAY THE PLUGIN JOINED IT, because a
           list generic ("either would do", #441) is one choosable pour and the
           key has to match on both sides. */
        var generic = Array.isArray(ing.g) ? ing.g.join(' or ') : ing.g;
        var picked = chosenBottle(url, generic);
        entries.push({
          amount: ing.a,
          generic: ing.g,
          bottle: picked || ing.b,
          glasses: glasses
        });
      });
    });

    var rows = HTF.shoppingList.build(entries, {
      // The cards' own list, not a second copy -- `not_on_cards: ['water']`.
      exclude: VOCABULARY.not_on_cards || [],
      bottleAliases: BOTTLE_ALIASES,
      // Declared in the same file, for the four juices you squeeze yourself.
      juiceYields: VOCABULARY.juice_yields || {},
      // #746: champagne, prosecco and soda water declare what a top pours, so
      // the list can say a volume instead of counting tops.
      topUpMl: TOP_UPS,
      // #820. Absent on the deployed site, where no row carries a price.
      rates: RATES,
      // #848: shelf order first, then volume within a shelf. Both halves come
      // from the vocabulary already on the page, so this needs no new block.
      shelves: {
        order: VOCABULARY.shopping_shelves || [],
        of: VOCABULARY.shelf_of || {}
      }
    });

    /* REBUILT WHOLE, not patched. It is at most a couple of dozen rows, it
       changes only when the shortlist or a count does, and a diffing render
       here would be complexity bought for nothing. */
    shoppingItems.innerHTML = rows.map(function (row) {
      /* THE BOTTLE IN BRACKETS ON THE SAME LINE -- Helen, 2026-09-04, "like the
         recipes", which is `.cocktail-item-name` then `.cocktail-suggestion` on
         a drink page. The fruit count joins it in the same brackets when there
         is one, because "(Beefeater) (9 to 13 lemons)" is two parentheticals
         where the sentence wants one.

         TWO SPANS INSIDE THE ONE BRACKET, because they are not the same kind of
         fact and Helen coloured only one of them: a bottle is a thing she chose
         and the has-to-have search matches against, which is what
         `.cocktail-suggestion` is cosmopolitan for (_sass/cocktails/_cocktail.scss
         says so where it declines to give `optional` a hue); a fruit count is
         arithmetic this page did. No drink pairs them today -- none of the four
         squeezed juices carries a suggestion -- so the comma between them is
         written for the day one does rather than for anything on screen now. */
      var suffix = '';
      if (row.note || row.fruit) {
        var inner = [];
        if (row.note) {
          inner.push('<span class="shopping-list-bottle">' +
            HTF.escapeHtml(row.note) + '</span>');
        }
        if (row.fruit) {
          inner.push('<span class="shopping-list-fruit">' +
            HTF.escapeHtml(row.fruit.text) + '</span>');
        }
        suffix = ' <span class="shopping-list-note">(' + inner.join(', ') + ')</span>';
      }
      /* THE PRICE AT THE END OF THE LINE — #820. A span of its own rather than
         part of the bracketed note, because it is the one thing on the row that
         is absent on the deployed site: keeping it separate means production
         renders the line it always did, with nothing to strip out.

         SILENT WHEN THERE IS NO RATE. 20 generics have none — the herbs, zest
         and bitters that are free under Helen's rule, and the whole fruit and
         weighed solids of #748 — and a line that cannot be priced says nothing
         rather than nothing-shaped-like-zero. */
      var price = row.price
        ? '<span class="shopping-list-price">' + HTF.escapeHtml(row.price.text) + '</span>'
        : '';

      return '<li>' +
        '<span class="shopping-list-amount">' + HTF.escapeHtml(row.text) + '</span>' +
        '<span class="shopping-list-name">' + HTF.escapeHtml(row.label) + suffix + '</span>' +
        price +
        '</li>';
    }).join('');

    renderShoppingTotal(rows);
  }

  /* WHAT THE SHOP COMES TO — #817. Summed from the rows just rendered, so the
     figure can never disagree with the column above it.

     IT SAYS WHAT IT COULD NOT PRICE. A bare total would claim to be the cost of
     the shop while being short by whatever the unpriced lines are worth, and
     "roughly" is doing enough work already. */
  function renderShoppingTotal(rows) {
    if (!shoppingTotal) return;
    var sum = HTF.shoppingList.total(rows);
    if (!sum) {
      shoppingTotal.hidden = true;
      shoppingTotal.textContent = '';
      return;
    }
    var text = 'roughly ' + sum.text;
    if (sum.unpriced) {
      text += ' — ' + sum.unpriced +
        (sum.unpriced === 1 ? ' line has no price' : ' lines have no price');
    }
    shoppingTotal.textContent = text;
    shoppingTotal.hidden = false;
  }

  if (shoppingDrinks) {
    // Delegated, because the inputs are replaced on every shortlist change.
    shoppingDrinks.addEventListener('input', function (ev) {
      var input = ev.target;
      if (!input.classList || !input.classList.contains('shopping-list-glasses')) return;
      HTF.shortlist.setGlasses(input.dataset.url, input.value);
      // Totals only. Re-rendering the drinks list would replace the very input
      // being typed into and take the caret with it.
      renderTotals();
    });

    /* CHOOSING A BOTTLE -- #818. `change` rather than `input`, because a radio
       fires `input` on every arrow-key pass through the group while it is being
       browsed, and re-costing the whole list on each one would make the keyboard
       route through the options feel like it was doing work.

       THE ROW IS PATCHED, NOT RE-RENDERED, for the same reason the glasses
       handler calls `renderTotals()` alone: rebuilding the list would replace
       the radio that was just clicked and take the focus ring with it, which
       for a keyboard user is the control vanishing mid-choice. So the price
       span is written in place and the totals below are rebuilt. */
    shoppingDrinks.addEventListener('change', function (ev) {
      var input = ev.target;
      if (!input.dataset || !input.dataset.generic) return;
      var url = input.dataset.url;
      CHOSEN[url] = CHOSEN[url] || {};
      CHOSEN[url][input.dataset.generic] = input.value;

      var row = input.closest ? input.closest('li') : null;
      var cost = row && row.querySelector('.shopping-list-cost');
      if (cost) cost.textContent = costSuffix(url);

      renderTotals();
    });
  }

  if (setAllInput) {
    /* SET ALL: it writes every drink's own count and then has no further
       opinion. One number per drink, one place it lives -- rather than a global
       factor on top of a per-drink figure, where nobody can say what six times
       two is meant to mean. */
    setAllInput.addEventListener('input', function () {
      var n = parseInt(setAllInput.value, 10);
      if (!isFinite(n) || n < 1) return;
      shortlistedDrinks().forEach(function (url) { HTF.shortlist.setGlasses(url, n); });
      renderShoppingList();
    });
  }

  /* MATCHED CHIPS TO THE FRONT OF THE ROW -- #757. Helen: "cocktail card chips
     hit by filters should be grouped at the beginning of the card... e.g. 'no
     juicing' returns Caribbean Sazerac first, but the chip isn't on the card,
     presumably because the full list of chips doesn't fit on the two lines we
     give them."

     She had the diagnosis exactly right. `.drink-card-moods` caps at three chip
     rows and clips the rest, so on a chip-heavy drink the word that EXPLAINS
     why the card is here could be the one cut off -- which is the one job the
     card's foot has (MANUAL 9.13).

     THE DOM MOVES, NOT THE `order` PROPERTY, and this is the reason: the
     separator dot is drawn by `.drink-card-mood + .drink-card-mood::before`,
     which is a DOM-order selector. Flex `order` would reorder what you see and
     leave the dot on whichever chip happens to be second in the markup, so the
     row would show a leading dot and lose one in the middle.

     ALPHABETICAL SURVIVES INSIDE EACH GROUP. `d.moodEls` is read once at
     startup in document order, which #710 made alphabetical, and both lists are
     built by walking it -- so the matched chips are alphabetical among
     themselves and so are the rest.

     REORDERED ONLY WHEN IT CHANGES, the same guard `reorder()` above applies to
     the cards: moving ~600 nodes on every keystroke is wasteful, and the row is
     usually already in the order this wants. */
  function moveMatchedChipsFirst(d, matched, others) {
    /* NO EARLY EXIT ON "NOTHING MATCHED", and that was a bug this function had
       for about ten minutes. Bailing when `matched` was empty left the row in
       whatever order the LAST filter had put it in, so clearing a mood left its
       chip stranded at the front for ever. With no matches, `wanted` is simply
       the original alphabetical order, and the sameness check below makes
       restoring it free. */
    var wanted = matched.concat(others);
    if (!wanted.length) return false;
    var parent = wanted[0].parentNode;
    if (!parent) return false;

    var kids = parent.children;
    var same = true;
    for (var i = 0; i < wanted.length; i++) {
      if (kids[i] !== wanted[i]) { same = false; break; }
    }
    if (same) return false;

    var frag = document.createDocumentFragment();
    wanted.forEach(function (chip) { frag.appendChild(chip); });
    parent.appendChild(frag);
    return true;
  }

  /* `preservePage` IS THE ONLY ARGUMENT AND IT IS FALSE EVERYWHERE BUT THE
     PAGER. Every other caller has just changed what the results ARE, and
     landing on page 4 of a set that now has two pages -- or on page 4 of a
     completely different set -- is disorienting in a way that going back to the
     top is not. Same rule filters.js states for the food index. */
  function apply(preservePage) {
    if (!preservePage) { currentPage = 1; showAll = false; }
    /* THE SHORTLIST VIEW GIVES WAY TO ANY OTHER FILTER -- #918. Every handler
       ends in apply(), so this is the whole of that rule on this page; the
       button is painted from `state.shortlisted` further down in this same
       pass. See filter-state.js. */
    FilterState.reconcileShortlistView(state);
    var shown = 0;
    var ranked = [];
    /* Set by moveMatchedChipsFirst below. Collected across the whole pass so
       the row-start marks are recomputed ONCE rather than 124 times. */
    var chipsMoved = false;
    activeInclude = chosen('include');
    activeExclude = chosen('exclude');

    model.forEach(function (d) {
      var ok = matches(d);
      d.card.hidden = !ok;
      if (ok) shown++;
      ranked.push({
        card: d.card,
        ok: ok,
        /* TWO SCORES, COARSE FIRST -- #695. `sections` is how many of the two
           mood questions this drink answers and `score` is how many individual
           moods; the sort below reads them in that order, so "answers both
           questions" beats "answers one twice" and the old ordering survives
           inside each band. -1 for a hidden card keeps it below every visible
           one without a second test. */
        sections: ok ? sectionScore(d) : -1,
        score: ok ? moodScore(d) : -1,
        key: d.key
      });

      /* The card answers "why am I here" in the colour of the control that put
         it there. Both are cleared and re-applied on every pass rather than
         tracked, which is cheap at this size and cannot drift out of step. */
      var matchedChips = [];
      var otherChips = [];
      d.moodEls.forEach(function (chip) {
        var on = state.moods.has(chip.dataset.mood);
        chip.classList.toggle('is-match', on);
        (on ? matchedChips : otherChips).push(chip);
        /* These became real <button>s when they gained the power to filter, so
           the state has to be announced as well as painted -- `is-match` is a
           class and a screen reader cannot see it. Set here rather than at
           click time for the same reason the class is: clear-all reassigns the
           whole state object without touching any markup. */
        chip.setAttribute('aria-pressed', on ? 'true' : 'false');
      });
      if (moveMatchedChipsFirst(d, matchedChips, otherChips)) chipsMoved = true;

      /* MATCHED AGAINST data-ing, NOT THE RENDERED TEXT — #501. A rum shows its
         category on a card now ("Demerara rum"), while the filter matches the
         generic, the card name and the suggestion alike, so a card found by
         typing "El Dorado" prints no such words. Reading textContent here would
         leave it surviving the filter with nothing lit up: the card would be
         unable to say why it was there, which is the one job MANUAL §9.13
         gives it. And it is the SAME rule the filter used — Search.entryIsHit
         is matchesInclude — so a lit ingredient and a surviving card can never
         disagree about why. */
      d.ingEls.forEach(function (ing) {
        ing.el.classList.toggle('drink-card-hit', Search.entryIsHit(ing.entries, activeInclude));
      });

      paintNameHighlight(d);
    });

    /* THE ORDER OF THESE FOUR LINES IS THE FEATURE. Visible before hidden;
       then how many of the mood QUESTIONS were answered (#695); then how many
       individual moods; then the card's fixed random key, which is what keeps
       a band shuffled rather than alphabetical and keeps that shuffle stable
       across keystrokes. */
    ranked.sort(function (a, b) {
      if (a.ok !== b.ok) return a.ok ? -1 : 1;
      if (a.sections !== b.sections) return b.sections - a.sections;
      if (a.score !== b.score) return b.score - a.score;
      return a.key - b.key;
    });
    reorder(ranked.map(function (r) { return r.card; }));

    /* PAGING HAPPENS AFTER THE REORDER, and the order matters: "the first
       twenty" is only meaningful once the ranking has decided which twenty
       those are. Reversing these two would page the DOM order and then shuffle
       within it, so a drink could rank first and still be on page four.

       `hidden` RATHER THAN `style.display`, because that is how this index
       hides a card everywhere else -- `matches()` sets `card.hidden` and the
       stylesheet has no `display` opinion to fight. filters.js uses `display`
       on the food side for the same job; each file stays internally consistent
       rather than the two being made to look alike.

       THE PAGE NUMBER IS ADOPTED BACK, not just read. A filter can narrow the
       results out from under whatever page you were on, and `paginate` returns
       a legal page in that case -- so `currentPage` takes its answer rather
       than staying on a page that no longer exists. */
    var visible = ranked.filter(function (r) { return r.ok; });
    var pageInfo = HTF.recipeList.paginate(visible.length, currentPage, PAGE_SIZE, showAll);
    currentPage = pageInfo.currentPage;
    visible.forEach(function (r, i) {
      r.card.hidden = !(i >= pageInfo.start && i < pageInfo.end);
    });
    syncPagination(pageInfo.totalPages, visible.length);

    /* THE LINE BUDGET IS REDONE ON EVERY PASS, not just when chips moved --
       #776. Pagination hides a card with `card.hidden` rather than removing it,
       and a hidden element measures ZERO height, so card-line-budget.js's
       load-time pass could only ever classify the cards on page one. Every
       later page kept the three-row chip cap it should have lost, and nothing
       said so because the card still looked plausible.

       IT USED TO RUN BEFORE markChipRows, AND THAT ORDER WAS LOAD-BEARING:
       the budget sets the chips' max-height, which decides where the chip rows
       break, which was what the row marks described. #846 deleted chip-rows.js
       -- the dot trails every chip but the last now, so nothing depends on
       where a row breaks -- and this is the last pass standing in that chain.

       STILL REDONE UNCONDITIONALLY, for its own reason rather than that one:
       `chipsMoved` is about chip CONTENT, and this is about which cards are
       VISIBLE. A plain page turn moves no chips and still needs the budget. */
    if (HTF.cardLineBudget) HTF.cardLineBudget();

    /* Each clear appears only when its own section has something to clear.
       Driven from the same pass that filters, so a clear can never be visible
       for a filter that is already empty. */
    showClear('clear-mood', moodBtnsIn(false).some(function (b) { return state.moods.has(b.dataset.mood); }));
    showClear('clear-hassle', moodBtnsIn(true).some(function (b) { return state.moods.has(b.dataset.mood); }));
    showClear('clear-chaos', state.chaos !== null);
    showClear('clear-name', state.nameQuery !== '');
    showClear('clear-include', state.include.size > 0 || state.isIncludeSearching);
    showClear('clear-exclude', state.exclude.size > 0 || state.isExcludeSearching);

    /* THE CLEAR-ALL BUTTONS — #541, and their visibility is FilterState's
       answer rather than a hand-written run of `||`s. That run is what kept
       going wrong on the food side: it disagreed with what clear-all actually
       cleared, and the button hid while it still had work to do. Here the two
       agree by construction, because clearAll() assigns emptyState() and both
       walk the same table. */
    var clearVisibility = FilterState.hasAnythingToClear(state) ? 'visible' : 'hidden';
    clearAllButtons.forEach(function (btn) { btn.style.visibility = clearVisibility; });

    /* THE SHORTLISTED-ONLY BUTTON, painted from state in the same pass as
       everything else -- #546. Not at click time, for the reason the mood chips
       above carry in their own comment: `clear all` reassigns the whole state
       object without touching any markup, so a class set where it was clicked
       would outlive the filter it stands for. */
    if (shortlistOnlyBtn) {
      shortlistOnlyBtn.classList.toggle('is-on', !!state.shortlisted);
      shortlistOnlyBtn.setAttribute('aria-pressed', state.shortlisted ? 'true' : 'false');
    }

    /* In the same pass as everything else -- #546. So a card toggled while the
       filter is on updates the list in the same frame the card leaves it, and
       `clear all` (which empties `shortlisted` with every other field) hides it
       without a second thing to remember. */
    renderShoppingList();

    if (countEl) countEl.textContent = shown;
    /* The word has to move with the number or "1 survivors" appears the first
       time a filter narrows to one drink. The Liquid in the template does the
       first render; this does every one after it, on the same rule. */
    if (wordEl) wordEl.textContent = 'survivor' + (shown === 1 ? '' : 's');
    if (noneEl) noneEl.hidden = shown > 0;
  }

  /* --- mood and chaos ----------------------------------------------------- */
  moodBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var name = btn.dataset.mood;
      if (state.moods.has(name)) state.moods.delete(name);
      else state.moods.add(name);
      syncMoodButtons();
      apply();
    });
  });

  /* --- the same moods, clicked ON A CARD — Helen, 2026-09-02 -----------------
     "please make the chips on cocktail cards clickable, with mouseover
     outlining the chip in pink as when they're active from filtering, where
     clicking filters all cocktails by whatever the chip is for."

     ONE HANDLER FOR BOTH, DELEGATED, AND THAT IS THE POINT RATHER THAN A SAVING.
     A card chip and a filter button now do exactly the same thing, so they must
     not be two implementations that agree today: the toggle, the sync and the
     re-render are the mood button's own, called from here.

     DELEGATED ON THE LIST because there are ~370 chips across 125 cards, and
     because `apply()` re-ranks by reordering nodes — a listener bound per chip
     would have to be rebound every time the list changed, which is the class of
     bug MANUAL 12 records for `tagShapes()` on the food side.

     The chip's own `is-match` class is NOT toggled here. It is painted from
     state in apply(), which is what keeps it correct after `clear all`
     reassigns the whole state object without touching any markup — the same
     argument the note below makes for the buttons. */
  /* HIDDEN ENTIRELY ONCE THERE IS NOTHING TO PAGE, and once `(see all)` has
     been pressed -- not merely disabled. A pager showing "page 1 of 1" beside
     two dead arrows is furniture that answers a question nobody asked; food's
     own control made the same call. */
  function syncPagination(totalPages, visibleCount) {
    if (pagination) {
      pagination.style.display =
        (totalPages > 1 && !showAll && visibleCount > 0) ? 'grid' : 'none';
    }
    if (pagePrevBtn) pagePrevBtn.disabled = currentPage <= 1;
    if (pageNextBtn) pageNextBtn.disabled = currentPage >= totalPages;
    if (pageStatusEl) {
      pageStatusEl.textContent = 'page ' + currentPage + ' of ' + totalPages;
    }
  }

  /* THE THREE CONTROLS. `apply(true)` preserves the page, which is the whole
     difference between paging and filtering: changing a filter sends you back
     to page one (the results are a different set), while pressing `next` must
     not. */
  if (pagePrevBtn) {
    pagePrevBtn.addEventListener('click', function () {
      if (currentPage <= 1) return;
      currentPage -= 1;
      apply(true);
    });
  }
  if (pageNextBtn) {
    pageNextBtn.addEventListener('click', function () {
      currentPage += 1;
      apply(true);
    });
  }
  if (pageSeeAllBtn) {
    pageSeeAllBtn.addEventListener('click', function () {
      showAll = true;
      apply(true);
    });
  }

  var cardList = document.querySelector('.drink-cards');
  if (cardList) {
    cardList.addEventListener('click', function (ev) {
      var chip = ev.target.closest ? ev.target.closest('.drink-card-mood') : null;
      if (!chip || !cardList.contains(chip)) return;
      var name = chip.dataset.mood;
      if (!name) return;
      /* The chip sits inside the card, and the card's title is a link. Without
         this a click would filter AND navigate. */
      ev.preventDefault();
      if (state.moods.has(name)) state.moods.delete(name);
      else state.moods.add(name);
      syncMoodButtons();
      apply();
    });
  }

  /* Painted FROM STATE rather than at each place state changes — the argument
     filters.js's syncFilterButtons() makes, and the reason it matters here is
     the same: clear-all reassigns the whole state object and never touches this
     markup, so anything toggled at click time would survive a clear. */
  function syncMoodButtons() {
    moodBtns.forEach(function (b) {
      var on = state.moods.has(b.dataset.mood);
      b.classList.toggle('is-on', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
  }

  function syncChaosButtons() {
    chaosBtns.forEach(function (b) {
      var on = b.dataset.chaos === state.chaos;
      b.classList.toggle('is-on', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
  }

  chaosBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var want = btn.dataset.chaos;
      state.chaos = (state.chaos === want) ? null : want;
      syncChaosButtons();
      apply();
    });
  });

  /* --- the shortlist -------------------------------------------------------
     GitHub issue #546, and the same two listeners food's filters.js registers.

     REVEALED HERE, not by shortlist.js: that script owns the per-card toggles,
     this owns the filter, and each unhides the half it has actually wired. The
     button ships `hidden` like every other JS-dependent control on both sites.

     No sync call after the state change -- apply() paints this button in the
     same pass it filters, for the reason its own comment there gives. */
  /* A VIEW, NOT A FACET -- #918, the same rule filters.js states. ON clears
     every other filter (state, boxes, pools, lit buttons) and shows the whole
     shortlist; OFF is the plain toggle; any filter set while it is on takes it
     off again, in apply(). */
  if (shortlistOnlyBtn) {
    shortlistOnlyBtn.hidden = false;
    shortlistOnlyBtn.addEventListener('click', function () {
      if (state.shortlisted) {
        state.shortlisted = false;
      } else {
        state = FilterState.enterShortlistView();
        resetControls();
      }
      apply();
    });
  }

  /* A CARD'S OWN TOGGLE CHANGED -- dispatched by shortlist.js. Unconditional
     rather than gated on `state.shortlisted`: with the filter on, the card just
     un-shortlisted has to leave the list, and with it off apply() still has the
     count on the button to repaint. It is the same pass every other filter
     runs, which is what stops the shortlisted view and the toggles on it from
     ever disagreeing. */
  document.addEventListener('htf:shortlist-change', apply);

  /* --- the two ingredient fields ------------------------------------------ */
  /* One builder for both, because they are the same control with opposite
     signs — the only differences are which set a chip lands in, which
     searching-flag the half-typed state sets, and that the exclude side is
     struck through, which is CSS's business.

     THE TWO MATCHING RULES ARE NOT THE SAME, though, and that asymmetry is in
     cocktail-search.js where it can be tested: fuzzy to include, exact or
     declared-family to exclude. Over-including shows you a drink you may not
     want; over-excluding hides one you would have had. */
  /* What a chosen chip's × undoes, per field. Spoken by the aria-label, since
     "×" says nothing to a screen reader and "Havana 3 ×" says the wrong thing.
     Phrased as the section heading is, so the sentence a reader hears matches
     the words they clicked under. */
  var STOP_DOING = { include: 'stop requiring ', exclude: 'stop leaving out ' };

  function wireSearch(input, poolEl, field, searchingField) {
    if (!input || !poolEl) return;

    function redraw() {
      poolEl.textContent = '';

      /* "There is text in this box", which is a state clear-all empties and so
         must count towards the clear button — issue #274 on the food side, where
         a half-finished search set nothing and the clear button stayed hidden
         beside a pool you had no other way to dismiss. It narrows nothing, which
         is why COCKTAIL_FIELDS declares it narrows: false. */
      state[searchingField] = !!input.value.trim();

      state[field].forEach(function (word) {
        poolEl.appendChild(chip(word, true, false));
      });

      var result = Search.search(input.value, pool, chosen(field));

      /* THE (all) BUTTONS COME FIRST, as food's do: an umbrella is a different
         offer from the things it stands over, and putting it above them is what
         makes it read as one. #549 point 1, and the mechanism is
         _data/cocktails/ingredients.yml's `family_of` — declared since #322 for
         exactly this, and read by nothing until now. */
      result.familyButtons.forEach(function (family) {
        poolEl.appendChild(chip(family + FAMILY_SUFFIX, false, true));
      });

      /* A CHIP FOUND THROUGH A NAME IT DOES NOT SHOW SAYS WHICH — #603, and
         Helen picked this out of four candidates shown side by side on a dev
         page, which was deleted with the losers the moment she chose -- the
         comparison-switch contract, same as `?narrow=` and `?glass=margin`.
         Recover it from git if the argument ever reopens.

         Band 3 is the one that matches a hidden name: a bottle beside the
         generic, or a generic the card name abbreviates away. It is what makes
         "velvet" reach `falernum` and "beefeater" reach `gin`, and it is also
         what put `cachaça` in front of her when she typed "sa". Both are the
         same rule; the difference is only whether the chip can account for
         itself, so the fix is to let it.

         The bracket is a SEPARATE SPAN and the chip's value is untouched. What
         gets stored as a filter, compared against a card and read back by
         clear-all is still the chip's own name -- an annotation folded into the
         label would become part of the filter and match nothing. */
      /* An umbrella suppresses its own bare word -- #51's rule, applied inside
         cocktail-search.js where a test can reach it. Nothing to do here. */
      result.results.forEach(function (r) {
        /* Three shapes, one rule: show the name that answers the question.
             - matched on its own name        -> the chip, nothing added
             - matched on a name that CONTAINS the chip's  -> that name, alone,
               because a bracket there would print the chip to itself and
               append the bit its card name dropped
             - matched on a genuinely other name           -> the chip, and the
               name in a bracket after it
           The VALUE handed to the state is `r.entry` in every case; only the
           label moves. */
        var explains = r.band === 3 && r.via;
        poolEl.appendChild(chip(
          explains && r.viaReplacesName ? r.via : r.entry,
          false,
          r.hasWordMatch,
          explains && !r.viaReplacesName ? r.via : null,
          r.entry
        ));
      });

      /* THE CAP IS STATED, NOT SILENT. A pool that quietly stops at eight looks
         like a complete answer, and the one you wanted may be the ninth. */
      if (result.hidden > 0) {
        var more = document.createElement('span');
        more.className = 'drink-pool-more';
        more.textContent = '+' + result.hidden + ' more — keep typing';
        poolEl.appendChild(more);
      }
    }

    /* `wordMatch` marks the candidates you actually meant — #549 point 3, and
       the same treatment food's two pickers give theirs (#390). It is a WORD
       PREFIX, not a substring: typing "li" marks "lime juice" and "apricot
       liqueur" and does NOT mark "galliano", which is in the list correctly on
       a substring match. So the marked entries are the ones you meant and the
       plain ones are what the vocabulary brought along. An (all) button is
       always a word match by construction. */
    /* A CHOSEN CHIP CARRIES ITS OWN ×, AND THE × IS NOT PART OF THE LABEL.
       Helen, 2026-08-30: "add an x for a clear button to the right of selected
       chips on the cocktail site, same as food."

       The split into a span is not tidiness, it is the whole point. LEAVE OUT
       strikes a chosen chip through (_filters.scss), and a single text node
       reading "peas ×" strikes the × as well -- which reads as "this control is
       disabled" rather than "this ingredient is out". Food hit exactly that and
       fixed it the same way; the rule there now strikes only
       `.btn-exclude-label`, and here only `.btn-pool-label`.

       Still ONE button throughout. The × is a target, not a second control --
       clicking anywhere on the chip removes it, which is what it already did. */
    /* THE LABEL AND THE VALUE ARE TWO THINGS, since #603's annotation. What a
       chip SAYS may be the generic that found it; what it IS -- stored in the
       state, compared against a card, cleared by clear-all -- is always the
       chip's own name. `value` defaults to the label, so every other caller is
       untouched and a chip that says what it is stays one argument. */
    function chip(word, on, wordMatch, via, value) {
      var stored = value === undefined ? word : value;
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'btn-pool' + (on ? ' is-on' : '') + (wordMatch ? ' btn-pool--word-match' : '');
      b.setAttribute('aria-pressed', on ? 'true' : 'false');

      if (on) {
        var label = document.createElement('span');
        label.className = 'btn-pool-label';
        label.textContent = word;
        b.appendChild(label);
        b.appendChild(document.createTextNode(' \u00d7'));
        b.setAttribute('aria-label', STOP_DOING[field] + word);
      } else if (via) {
        // ONLY WHILE IT IS AN OFFER. The bracket answers "why is this here?",
        // which is a question about a candidate; once the chip is chosen it is
        // your filter and the reason has been spent.
        b.textContent = word + ' ';
        var reason = document.createElement('span');
        reason.className = 'btn-pool-via';
        reason.textContent = '(' + via + ')';
        b.appendChild(reason);
      } else {
        b.textContent = word;
      }

      b.addEventListener('click', function () {
        if (state[field].has(stored)) {
          state[field].delete(stored);
        } else {
          state[field].add(stored);
          /* CHOOSING ONE CLEARS THE SEARCH, so the candidates vanish and the
             chosen chips are all that is left. Helen, 2026-08-30, on food doing
             this: "it frees the input field for more typing, and reclaims the
             space on the page." The next thing you want is to name the NEXT
             ingredient, and the one you just picked is now sitting in front of
             you as a chip.

             Only on ADD. Removing a chip leaves the pool alone -- you are
             correcting the list you can see, not starting a new search.

             Clearing input.value is the whole mechanism: redraw() below reads
             it for `state[searchingField]`, and Search.search() returns nothing
             for a query under MIN_QUERY_CHARS, so the pool comes back holding
             the chosen chips and no candidates. No second code path. */
          input.value = '';
        }
        redraw();
        apply();
      });
      return b;
    }

    input.addEventListener('input', function () { redraw(); apply(); });
    redrawPool[field] = redraw;
    redraw();
  }

  wireSearch(incInput, incPool, 'include', 'isIncludeSearching');
  wireSearch(excInput, excPool, 'exclude', 'isExcludeSearching');

  /* I KNOW WHAT I WANT. No candidate pool: the ingredient fields offer one
     because their vocabulary is closed and you are picking FROM it, whereas a
     drink name is something you already hold and are merely typing. */
  if (nameInput) {
    nameInput.addEventListener('input', function () {
      state.nameQuery = nameInput.value.trim().toLowerCase();
      apply();
    });
  }

  /* --- the clears ---------------------------------------------------------- */
  /* Each per-section clear resets ONE section and nothing else. Deliberately
     separate controls rather than only a clear-all: with five axes, the filter
     you want to drop is almost never all of them — you have found the mood and
     are now arguing with the cupboard. #541 adds the clear-all BESIDE them, not
     instead of them, which is exactly how food's index reads. */
  function wireClear(id, reset) {
    var btn = document.getElementById(id);
    if (btn) btn.addEventListener('click', function () { reset(); apply(); });
  }

  /* MOOD and HASSLE clear independently even though they share `state.moods`.
     Clearing one must not drop the other. */
  function clearGroup(hassle) {
    moodBtnsIn(hassle).forEach(function (b) { state.moods.delete(b.dataset.mood); });
    syncMoodButtons();
  }

  wireClear('clear-mood', function () { clearGroup(false); });
  wireClear('clear-hassle', function () { clearGroup(true); });

  wireClear('clear-chaos', function () {
    state.chaos = null;
    syncChaosButtons();
  });

  wireClear('clear-name', function () {
    state.nameQuery = '';
    if (nameInput) nameInput.value = '';
  });

  /* The input is cleared as well as the chips. Leaving the typed text behind
     would redraw its candidate pool on the next keystroke and look like the
     clear had partly failed. */
  function clearField(field, input) {
    state[field].clear();
    if (input) input.value = '';
    if (redrawPool[field]) redrawPool[field]();
  }

  wireClear('clear-include', function () { clearField('include', incInput); });
  wireClear('clear-exclude', function () { clearField('exclude', excInput); });

  /* --- clear all, top and bottom — #541 ------------------------------------ */
  /* Two buttons, one action, the same shape food's index has had since #67: the
     top one is pinned above the filters, the bottom one repeats it after the
     last section so clearing does not mean scrolling back up past five of them.

     Built here rather than in the template for the same reason food builds its
     pair in filters.js: a control that only works with script has no business
     rendering before the script that makes it work. */
  if (filters) {
    ['btn-clear', 'btn-clear btn-clear--bottom'].forEach(function (cls, i) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = cls;
      btn.textContent = '× clear all';
      if (i === 0) filters.insertBefore(btn, filters.firstChild);
      else filters.appendChild(btn);
      clearAllButtons.push(btn);
    });
  }

  /* THE BOXES, POOLS AND BUTTONS THAT ARE NOT STATE, emptied and repainted
     after the state has been. Shared by clear-all and by the shortlist button
     turning its view on (#918), which is a clear-all with one field kept --
     filters.js's resetFilterControls() is the same split for the same reason. */
  function resetControls() {
    [incInput, excInput, nameInput].forEach(function (input) {
      if (input) input.value = '';
    });
    Object.keys(redrawPool).forEach(function (field) { redrawPool[field](); });
    syncMoodButtons();
    syncChaosButtons();
  }

  function clearAll() {
    /* ONE assignment, not a field-by-field emptying. A field-by-field version
       is a list that has to be kept in step with hasAnythingToClear()'s list,
       and on the food side it wasn't, three times in two days. emptyState()
       walks the same table that predicate walks. */
    state = FilterState.emptyState();
    resetControls();
    apply();
  }

  clearAllButtons.forEach(function (btn) { btn.addEventListener('click', clearAll); });

  /* --- GOING BACK RETURNS THE LIST YOU LEFT — #595 -------------------------- */
  /* Helen: "exactly as the food site does", and it is food's #387 mechanism
     with one difference that matters.

     FOOD RESTORES AN ARRAY; THIS RESTORES THE SORT KEYS. The food index keeps
     its order in `items` and reorders the DOM to match. Here the order is
     DERIVED on every pass -- rank by matched moods, then by each card's random
     key -- so putting the cards back in the right nodes and calling apply()
     would immediately re-sort them by keys that were freshly randomised at
     startup. The order is the keys, so the keys are what comes back: each card
     takes its INDEX in the saved order, and a drink the record has never seen
     sorts after all of them rather than being dropped.

     WHAT IS NOT RESTORED, on food's own reasoning: a half-typed picker.
     isIncludeSearching / isExcludeSearching mean "there is text in that box and
     nothing chosen from its results yet", which is candidates mid-thought
     rather than a filter. A CHOSEN chip is different and does come back -- it
     is an applied filter, and it rebuilds from the state like any other.

     THE STORE ITSELF IS SHARED SINCE #686: HTF.indexMemory in assets.js holds
     the sessionStorage read and write and the swallowing of every way it can
     fail. What stays here is what is this index's own -- the key, the record,
     and the question of whether you arrived by going back. */
  var MEMORY_KEY = 'htf-drinks-memory-v1';

  /* Cards carry no id; the drink link's href is the one thing on a card that is
     unique and stable. `data-name` is not -- two drinks may share a name and
     the Modern Zombie already writes "(makes 2)" into its slug and not its
     name. */
  function cardKey(d) {
    return d.nameEl ? d.nameEl.getAttribute('href') : '';
  }

  function saveDrinksMemory() {
    var order = model.slice().sort(function (a, b) { return a.key - b.key; });
    HTF.indexMemory.save(MEMORY_KEY, {
      order: order.map(cardKey),
      filters: FilterState.serialise(state),
      /* #694. Restoring the filters and the shuffle but not the PAGE would put
         you back on page one of the list you left from page three, which is the
         same lost-place problem this whole memory exists to fix. */
      page: currentPage,
      showAll: showAll,
      scrollY: window.scrollY || 0
    });
  }

  /* Returns the record when it restored, or null for "carry on as a fresh
     load" -- which every failure path returns: not a back navigation, nothing
     stored, unparseable, or a record whose shape does not fit. Stored state is
     untrusted input; see FilterState.deserialise's own note. */
  function restoreDrinksMemory() {
    if (!arrivedByGoingBack()) return null;

    var saved = HTF.indexMemory.restore(MEMORY_KEY);
    if (!saved || !Array.isArray(saved.order)) return null;

    var position = Object.create(null);
    saved.order.forEach(function (key, i) { position[key] = i; });
    var unseen = saved.order.length;
    model.forEach(function (d) {
      var at = position[cardKey(d)];
      d.key = (typeof at === 'number') ? at : unseen++;
    });

    /* UNTRUSTED, like everything else in this record -- see
       FilterState.deserialise's own note. A stored page is only adopted if it
       is a positive number; `paginate` then clamps it to something legal, so a
       tampered 9999 lands on the last page rather than an empty one. */
    currentPage = (typeof saved.page === 'number' && saved.page > 0) ? saved.page : 1;
    showAll = !!saved.showAll;

    state = FilterState.deserialise(saved.filters);
    state.isIncludeSearching = false;
    state.isExcludeSearching = false;

    if (nameInput) nameInput.value = state.nameQuery || '';
    [incInput, excInput].forEach(function (input) { if (input) input.value = ''; });
    Object.keys(redrawPool).forEach(function (field) { redrawPool[field](); });
    syncMoodButtons();
    syncChaosButtons();
    return saved;
  }

  var restored = restoreDrinksMemory();

  /* ARRIVING FROM A DRINK PAGE'S MOOD CHIP -- `?mood=sharp`, 2026-09-05.
     Helen: "let's wire the chips up to show a filtered index page please,
     echoing what we do on the food site, which feels lovely."

     THE SAME SHAPE AS food's `applyQueryString` in assets/js/filters.js, and
     the same two policies. A value that survives parsing but matches no button
     is dropped in silence, so a stale link to a retired mood lands on a
     perfectly good unfiltered index rather than erroring on a page that works.
     And the check is against the BUTTONS rather than the taxonomy, because the
     buttons are what the reader can undo: a filter nothing on screen can turn
     off is a filter the page is stuck in.

     IT ADDS TO THE RESTORED STATE RATHER THAN REPLACING IT, and runs after
     `restoreDrinksMemory` for that reason. Coming back from a drink page you
     opened out of a filtered list, the list you left is the one you want, plus
     the mood you just clicked -- which is the same "narrow what you are already
     looking at" a chip click on a card does. */
  (function applyQueryString() {
    if (!moodBtns.length) return;
    /* `HTF.filterState.parseQuery`, NOT `FilterState.parseQuery`. `FilterState`
       here is the COCKTAIL_FIELDS binding that `create()` returns -- state
       shape, serialisation, emptiness -- and the query grammar is not part of
       that: it is one grammar for both sites and lives on the module itself.
       Reaching for the binding gets `undefined` and throws on the next line. */
    var wanted = HTF.filterState.parseQuery(location.search);
    var changed = false;
    wanted.mood.forEach(function (value) {
      var offered = moodBtns.some(function (b) { return b.dataset.mood === value; });
      if (offered && !state.moods.has(value)) {
        state.moods.add(value);
        changed = true;
      }
    });
    if (changed) syncMoodButtons();
  })();

  apply();

  /* AFTER apply(), because the page is not its full height until the hidden
     cards are hidden -- scrolling to 2,400px on a list that is still 6,000px
     tall and about to become 900px lands somewhere else entirely. */
  if (restored && typeof restored.scrollY === 'number') {
    window.scrollTo(0, restored.scrollY);
  }

  /* pagehide rather than unload: it fires on the way out INCLUDING into
     bfcache, and unlike unload it does not itself disqualify the page from it.
     On the deployed site bfcache does apply, and this mechanism should stay out
     of its way rather than compete with it. */
  window.addEventListener('pagehide', saveDrinksMemory);
})();
