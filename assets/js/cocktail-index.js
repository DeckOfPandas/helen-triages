/* =============================================================================
   COCKTAILS INDEX — filtering. Designed with Helen, 2026-08-26.
   =============================================================================
   Four controls: mood, chaos, has-to-have, leave-out. Everything is already in
   the DOM — 115 drinks is nothing — so this toggles [hidden] and reorders the
   list in place. No fetch, no dependency on the site's other scripts.

   NOTHING IS PARSED OUT OF THE RENDERED MARKUP. Every fact a filter needs was
   written into a data- attribute at build time by cocktails/index.html:
   data-moods, data-chaos and a pre-lowercased data-ingredients. A filter that
   reads textContent is a filter that breaks the first time someone restyles a
   card.

   HOW THE AXES COMBINE. Settled by Helen 2026-08-27, #478 and #479:

     - Two moods selected means EITHER, and drinks matching BOTH rank first.
     - Include chips are AND: adding an ingredient narrows.
     - Mood AND ingredient(s) AND chaos, between sections.
     - Everything shown is in RANDOMISED order, within its rank.

   The ranking is what makes OR usable. AND across moods is nearly always empty
   -- `tiki` AND `no juicing` is a handful of drinks -- so OR is the only
   answer that keeps the index alive, but plain OR stops narrowing anything
   once you pick a second mood. Ranking gives back the precision: the drinks
   that match both float to the top without the ones matching only one
   disappearing.

   WHY RANDOM RATHER THAN ALPHABETICAL. Alphabetical is a stable answer to a
   question nobody asked -- it buries everything after M and it means the same
   drink greets you every time. Random ordering is what makes the index a way
   of FINDING something rather than a list you scroll past, which is the
   principle in _data/cocktails/taxonomy.yml: this exists to get Helen the
   drink she wants, not to be an encyclopaedia.

   THE SHUFFLE HAPPENS ONCE PER PAGE LOAD, NOT PER KEYSTROKE, and that is the
   part worth not undoing. Each card is given a random sort key at startup and
   keeps it; filtering re-ranks against those fixed keys. Re-shuffling on every
   filter change would make cards leap around while you type into the
   has-to-have box, which reads as a bug however correct it is.
   ============================================================================= */
(function () {
  var cards = Array.prototype.slice.call(document.querySelectorAll('.drink-card'));
  if (!cards.length) return;

  var moodBtns  = document.querySelectorAll('.btn-mood');
  var chaosBtns = document.querySelectorAll('.btn-chaos');
  var incInput  = document.getElementById('drink-include');
  var excInput  = document.getElementById('drink-exclude');
  var incPool   = document.getElementById('drink-include-pool');
  var excPool   = document.getElementById('drink-exclude-pool');
  var countEl   = document.getElementById('drink-count-n');
  var wordEl    = document.getElementById('drink-count-word');
  var noneEl    = document.querySelector('.drink-none');
  var nameInput = document.getElementById('drink-name');

  /* Mood and hassle are one filter with two headings: both render .btn-mood
     and both write into `chosenMoods`, because a drink matching either is
     matched the same way. Only the CLEAR links are per-section, so the two
     sets are told apart by which block they sit in rather than by a second
     data attribute the template would have to keep in step. */
  function inHassle(btn) {
    return !!btn.closest('.drink-filter--hassle');
  }

  /* One random key per card, fixed for the life of the page. See the note on
     ordering at the top: this is what lets the order be random without cards
     jumping every time a filter changes. */
  var list = cards[0].parentNode;
  var shuffleKey = new Map();
  cards.forEach(function (card) { shuffleKey.set(card, Math.random()); });

  var chosenMoods = [];
  var chosenChaos = null;
  var wantName    = '';
  var include     = [];
  var exclude     = [];

  /* Every distinct ingredient word in the collection, gathered once from the
     data attributes rather than from a second copy of the vocabulary. The
     pools below are filtered slices of this. */
  var vocabulary = (function () {
    var seen = Object.create(null);
    cards.forEach(function (card) {
      (card.dataset.ingredients || '').split('|').forEach(function (word) {
        word = word.trim();
        if (word) seen[word] = true;
      });
    });
    return Object.keys(seen).sort();
  })();

  function cardMoods(card) {
    return (card.dataset.moods || '').split('|').filter(Boolean);
  }

  function moodBtnsIn(hassle) {
    return Array.prototype.filter.call(moodBtns, function (b) {
      return inHassle(b) === hassle;
    });
  }

  function isOn(btn) {
    return chosenMoods.indexOf(btn.dataset.mood) !== -1;
  }

  function showClear(id, active) {
    var el = document.getElementById(id);
    if (el) el.hidden = !active;
  }

  /* Does the query start a WORD inside this entry, rather than merely appear
     in it? "rum" starts a word in "Jamaican rum" and does not in "plumbago".
     Punctuation counts as a boundary as well as space, because the vocabulary
     contains things like "sugar syrup 2:1" and "demerara, aged". */
  function wordStarts(haystack, needle) {
    var at = haystack.indexOf(needle);
    while (at !== -1) {
      if (at === 0 || /[^a-z0-9]/.test(haystack.charAt(at - 1))) return true;
      at = haystack.indexOf(needle, at + 1);
    }
    return false;
  }

  var POOL_CAP = 8;

  /* How many of the SELECTED moods this drink has. 0 when nothing is selected,
     which is what makes the no-filter case fall through to pure random order
     without a special case. */
  function moodScore(card) {
    if (!chosenMoods.length) return 0;
    var mine = cardMoods(card);
    var n = 0;
    for (var i = 0; i < chosenMoods.length; i++) {
      if (mine.indexOf(chosenMoods[i]) !== -1) n++;
    }
    return n;
  }

  function matches(card) {
    /* mood: OR within the section. Change `.some` to `.every` for AND — see
       the note at the top, and issue #478. Ranking by moodScore is what makes
       OR narrow anything, so if this ever becomes AND the ranking is redundant
       rather than merely unused. */
    if (chosenMoods.length && moodScore(card) === 0) return false;
    /* `open` IS A STATE, NOT A FILTER, and this is the fix rather than an
       oversight. It used to be `yolo`, meaning ship is not yes-or-better --
       so the button for "I'll try anything" was the one button guaranteed to
       hide all 55 of the best drinks. Helen, 2026-08-27: "'I'm open to chaos'
       ... includes all drinks, not just not-known-to-be-definitely-good
       drinks." So only `good` narrows; `open` shows everything and exists to
       make that an answer you can give rather than a default you fall into. */
    if (chosenChaos === 'good' && card.dataset.chaos !== 'good') return false;

    var ing = card.dataset.ingredients || '';
    /* AND across include: each chip you add narrows. That is the opposite of
       the mood rule and deliberately so — adding an ingredient means "and this
       one too", which is how a cupboard works. */
    for (var i = 0; i < include.length; i++) {
      if (ing.indexOf(include[i]) === -1) return false;
    }
    for (var j = 0; j < exclude.length; j++) {
      if (ing.indexOf(exclude[j]) !== -1) return false;
    }

    /* I KNOW WHAT I WANT. Substring rather than word-start, unlike the
       ingredient fields: those match a vocabulary where "rum" starting a word
       is the meaningful test, whereas a drink name is a thing you are part-way
       through typing. "negr" should find the Negroni. */
    if (wantName && card.dataset.name.indexOf(wantName) === -1) return false;
    return true;
  }

  /* Put the list in rank order: more matched moods first, random within a
     rank, hidden cards last so they never split a run of visible ones.

     REWRITTEN ONLY WHEN IT ACTUALLY CHANGES. Moving 115 nodes on every
     keystroke is wasteful and, worse, it would scroll the page under the
     reader's cursor while they type. Comparing first makes the common case
     (typing narrows the same set in the same order) free. */
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

  function apply() {
    var shown = 0;
    var ranked = [];
    cards.forEach(function (card) {
      var ok = matches(card);
      card.hidden = !ok;
      if (ok) shown++;
      ranked.push({
        card: card,
        ok: ok,
        score: ok ? moodScore(card) : -1,
        key: shuffleKey.get(card)
      });
    });

    ranked.sort(function (a, b) {
      if (a.ok !== b.ok) return a.ok ? -1 : 1;
      if (a.score !== b.score) return b.score - a.score;
      return a.key - b.key;
    });
    reorder(ranked.map(function (r) { return r.card; }));

    cards.forEach(function (card) {
      /* The card answers "why am I here" in the colour of the control that put
         it there: a matched mood chip fills menthe, a matched ingredient fills
         violet. Both are cleared and re-applied on every pass rather than
         tracked, which is cheap at this size and cannot drift out of step. */
      card.querySelectorAll('.drink-card-mood').forEach(function (chip) {
        chip.classList.toggle('is-match',
          chosenMoods.indexOf(chip.dataset.mood) !== -1);
      });
      /* MATCHED AGAINST data-ing, NOT THE RENDERED TEXT — #501. A rum shows
         its category on a card now ("Demerara rum"), while the filter still
         matches the item and the generic alike, so a card found by typing
         "El Dorado" prints no such words. Reading textContent here would leave
         it surviving the filter with nothing lit up: the card would be unable
         to say why it was there, which is the one job the card section of
         HANDOVER §9.13 gives it. data-ing carries the same item-plus-generic
         string the card-level data-ingredients does, written at build time.
         The fallback keeps a card without the attribute behaving as before. */
      card.querySelectorAll('.drink-card-ing').forEach(function (el) {
        var text = (el.dataset.ing || el.textContent).toLowerCase();
        var hit = include.some(function (w) { return text.indexOf(w) !== -1; });
        el.classList.toggle('drink-card-hit', hit);
      });
    });

    /* Each clear appears only when its own section has something to clear.
       Driven from the same pass that filters, so a clear can never be visible
       for a filter that is already empty. */
    showClear('clear-mood', moodBtnsIn(false).some(isOn));
    showClear('clear-hassle', moodBtnsIn(true).some(isOn));
    showClear('clear-chaos', chosenChaos !== null);
    showClear('clear-name', wantName !== '');
    showClear('clear-include', include.length > 0 || incInput.value !== '');
    showClear('clear-exclude', exclude.length > 0 || excInput.value !== '');

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
      var at = chosenMoods.indexOf(name);
      if (at === -1) { chosenMoods.push(name); } else { chosenMoods.splice(at, 1); }
      btn.classList.toggle('is-on', at === -1);
      btn.setAttribute('aria-pressed', at === -1 ? 'true' : 'false');
      apply();
    });
  });

  chaosBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var want = btn.dataset.chaos;
      chosenChaos = (chosenChaos === want) ? null : want;
      chaosBtns.forEach(function (b) {
        var on = b.dataset.chaos === chosenChaos;
        b.classList.toggle('is-on', on);
        b.setAttribute('aria-pressed', on ? 'true' : 'false');
      });
      apply();
    });
  });

  /* --- the two ingredient fields ------------------------------------------ */
  /* One builder for both, because they are the same control with opposite
     signs — the only differences are which list a chip lands in and that the
     exclude side is struck through, which is CSS's business, not this file's. */
  function wireSearch(input, pool, chosen) {
    if (!input || !pool) return;

    function redraw() {
      var typed = input.value.trim().toLowerCase();
      pool.textContent = '';

      chosen.forEach(function (word) {
        pool.appendChild(chip(word, true));
      });

      if (typed.length < 2) { return; }

      /* THREE BANDS, MATCHING FOOD — #497. assets/js/ingredient-search.js
         orders its candidates the same way and its comment explains why: an
         entry STARTING with the query outranks everything else, full stop;
         below that a genuine word match outranks a merely-contains match, and
         is deliberately not promoted into the prefix tier, or a mid-word
         coincidence ranks alongside the thing you were obviously typing.
         Alphabetical within each band, which comes free because `vocabulary`
         is already sorted and filtering preserves order.

         Cocktails has no synonym or family layer, so food's third band
         (family-only members) has no equivalent here; its place is taken by
         the merely-contains matches. Two real bands and a tail, against
         food's two and a tail. */
      var pending = vocabulary.filter(function (w) {
        return w.indexOf(typed) !== -1 && chosen.indexOf(w) === -1;
      });

      var prefix = pending.filter(function (w) { return w.indexOf(typed) === 0; });
      var wordly = pending.filter(function (w) {
        return w.indexOf(typed) !== 0 && wordStarts(w, typed);
      });
      var rest = pending.filter(function (w) {
        return w.indexOf(typed) !== 0 && !wordStarts(w, typed);
      });

      prefix.concat(wordly, rest)
        .slice(0, POOL_CAP)
        .forEach(function (w) { pool.appendChild(chip(w, false)); });

      /* THE CAP IS STATED, NOT SILENT. A pool that quietly stops at eight
         looks like a complete answer, and the one you wanted may be the
         ninth. Food's own rule elsewhere in this repo: never truncate
         without saying so. */
      var hidden = prefix.length + wordly.length + rest.length - POOL_CAP;
      if (hidden > 0) {
        var more = document.createElement('span');
        more.className = 'drink-pool-more';
        more.textContent = '+' + hidden + ' more — keep typing';
        pool.appendChild(more);
      }
    }

    function chip(word, on) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'btn-pool' + (on ? ' is-on' : '');
      b.textContent = word;
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
      b.addEventListener('click', function () {
        var at = chosen.indexOf(word);
        if (at === -1) { chosen.push(word); } else { chosen.splice(at, 1); }
        redraw();
        apply();
      });
      return b;
    }

    input.addEventListener('input', redraw);
    redraw();
  }

  wireSearch(incInput, incPool, include);
  wireSearch(excInput, excPool, exclude);

  /* I KNOW WHAT I WANT. No candidate pool: the ingredient fields offer one
     because their vocabulary is closed and you are picking FROM it, whereas a
     drink name is something you already hold and are merely typing. Offering
     to complete it would be answering a question nobody asked. */
  if (nameInput) {
    nameInput.addEventListener('input', function () {
      wantName = nameInput.value.trim().toLowerCase();
      apply();
    });
  }

  wireClear('clear-name', function () {
    wantName = '';
    if (nameInput) nameInput.value = '';
  });

  /* --- the four clears ----------------------------------------------------- */
  /* Each resets ONE section and nothing else. Deliberately four separate
     controls rather than one "clear all": with four axes, the filter you want
     to drop is almost never all of them -- you have found the mood and are now
     arguing with the cupboard. */
  function wireClear(id, reset) {
    var btn = document.getElementById(id);
    if (btn) btn.addEventListener('click', function () { reset(); apply(); });
  }

  /* MOOD and HASSLE clear independently even though they share `chosenMoods`.
     Clearing one must not drop the other -- "I have found the mood and am now
     arguing with the cupboard" applies here too, one heading down. */
  function clearGroup(hassle) {
    moodBtnsIn(hassle).forEach(function (b) {
      var at = chosenMoods.indexOf(b.dataset.mood);
      if (at !== -1) chosenMoods.splice(at, 1);
      b.classList.remove('is-on');
      b.setAttribute('aria-pressed', 'false');
    });
  }

  wireClear('clear-mood', function () { clearGroup(false); });
  wireClear('clear-hassle', function () { clearGroup(true); });

  wireClear('clear-chaos', function () {
    chosenChaos = null;
    chaosBtns.forEach(function (b) {
      b.classList.remove('is-on');
      b.setAttribute('aria-pressed', 'false');
    });
  });

  /* The input is cleared as well as the chips. Leaving the typed text behind
     would redraw its candidate pool on the next keystroke and look like the
     clear had partly failed. */
  wireClear('clear-include', function () {
    include.length = 0;
    incInput.value = '';
    incInput.dispatchEvent(new Event('input'));
  });

  wireClear('clear-exclude', function () {
    exclude.length = 0;
    excInput.value = '';
    excInput.dispatchEvent(new Event('input'));
  });

  apply();
})();
