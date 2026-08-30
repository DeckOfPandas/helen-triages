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
  var cards = Array.prototype.slice.call(document.querySelectorAll('.drink-card'));
  if (!cards.length) return;

  var CS = HTF.cocktailSearch;
  var FAMILY_SUFFIX = CS.FAMILY_SUFFIX;

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

  /* ONE state object, not five loose variables — GitHub issue #579. The fields,
     their cleared values and the "is anything set" answer all come from
     COCKTAIL_FIELDS in assets/js/filter-state.js, where the reasoning for each
     lives and where tests/js/filter-state.test.js can reach them.

     Reassigned wholesale by clearAll(), never rebuilt field by field: that is
     the whole point, and it is why #541's clear-all button can be added at all
     without re-running the bug food hit three times in two days. */
  var FilterState = HTF.filterState.create(HTF.filterState.COCKTAIL_FIELDS);
  var state = FilterState.emptyState();

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

  function matches(d) {
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

  function escapeHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
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
      escapeHtml(d.title.slice(0, at.start)) +
      '<mark class="drink-name-hit">' + escapeHtml(d.title.slice(at.start, at.end)) + '</mark>' +
      escapeHtml(d.title.slice(at.end));
  }

  function showClear(id, active) {
    var el = document.getElementById(id);
    if (el) el.hidden = !active;
  }

  function apply() {
    var shown = 0;
    var ranked = [];
    activeInclude = chosen('include');
    activeExclude = chosen('exclude');

    model.forEach(function (d) {
      var ok = matches(d);
      d.card.hidden = !ok;
      if (ok) shown++;
      ranked.push({ card: d.card, ok: ok, score: ok ? moodScore(d) : -1, key: d.key });

      /* The card answers "why am I here" in the colour of the control that put
         it there. Both are cleared and re-applied on every pass rather than
         tracked, which is cheap at this size and cannot drift out of step. */
      d.moodEls.forEach(function (chip) {
        chip.classList.toggle('is-match', state.moods.has(chip.dataset.mood));
      });

      /* MATCHED AGAINST data-ing, NOT THE RENDERED TEXT — #501. A rum shows its
         category on a card now ("Demerara rum"), while the filter matches the
         generic, the card name and the suggestion alike, so a card found by
         typing "El Dorado" prints no such words. Reading textContent here would
         leave it surviving the filter with nothing lit up: the card would be
         unable to say why it was there, which is the one job HANDOVER §9.13
         gives it. And it is the SAME rule the filter used — Search.entryIsHit
         is matchesInclude — so a lit ingredient and a surviving card can never
         disagree about why. */
      d.ingEls.forEach(function (ing) {
        ing.el.classList.toggle('drink-card-hit', Search.entryIsHit(ing.entries, activeInclude));
      });

      paintNameHighlight(d);
    });

    ranked.sort(function (a, b) {
      if (a.ok !== b.ok) return a.ok ? -1 : 1;
      if (a.score !== b.score) return b.score - a.score;
      return a.key - b.key;
    });
    reorder(ranked.map(function (r) { return r.card; }));

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

      result.results.forEach(function (r) {
        poolEl.appendChild(chip(r.entry, false, r.hasWordMatch));
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
    function chip(word, on, wordMatch) {
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
      } else {
        b.textContent = word;
      }

      b.addEventListener('click', function () {
        if (state[field].has(word)) {
          state[field].delete(word);
        } else {
          state[field].add(word);
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

  function clearAll() {
    /* ONE assignment, not a field-by-field emptying. A field-by-field version
       is a list that has to be kept in step with hasAnythingToClear()'s list,
       and on the food side it wasn't, three times in two days. emptyState()
       walks the same table that predicate walks. */
    state = FilterState.emptyState();
    [incInput, excInput, nameInput].forEach(function (input) {
      if (input) input.value = '';
    });
    Object.keys(redrawPool).forEach(function (field) { redrawPool[field](); });
    syncMoodButtons();
    syncChaosButtons();
    apply();
  }

  clearAllButtons.forEach(function (btn) { btn.addEventListener('click', clearAll); });

  apply();
})();
