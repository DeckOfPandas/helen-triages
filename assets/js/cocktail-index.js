/* =============================================================================
   COCKTAILS INDEX — filtering. Designed with Helen, 2026-08-26.
   =============================================================================
   Four controls: mood, chaos, has-to-have, leave-out. Everything is already in
   the DOM — 115 drinks is nothing — so this only toggles [hidden]. No reflow of
   the cards, no fetch, no dependency on the site's other scripts.

   NOTHING IS PARSED OUT OF THE RENDERED MARKUP. Every fact a filter needs was
   written into a data- attribute at build time by cocktails/index.html:
   data-moods, data-chaos and a pre-lowercased data-ingredients. A filter that
   reads textContent is a filter that breaks the first time someone restyles a
   card.

   HOW THE AXES COMBINE, and this is a decision recorded rather than a default:
   OR within a section, AND between sections. Two moods selected means "either
   of these", because AND across moods is nearly always empty — `tiki` AND
   `no juicing` is a handful of drinks — while mood AND an ingredient is the
   combination you actually want. This is the shape issue #478 asks about; if
   Helen wants AND within moods, it is the one line marked below.
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

  var chosenMoods = [];
  var chosenChaos = null;
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

  function matches(card) {
    /* mood: OR within the section. Change `.some` to `.every` for AND — see
       the note at the top, and issue #478. */
    if (chosenMoods.length) {
      var mine = cardMoods(card);
      if (!chosenMoods.some(function (m) { return mine.indexOf(m) !== -1; })) return false;
    }
    if (chosenChaos && card.dataset.chaos !== chosenChaos) return false;

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
    return true;
  }

  function apply() {
    var shown = 0;
    cards.forEach(function (card) {
      var ok = matches(card);
      card.hidden = !ok;
      if (ok) shown++;

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
    showClear('clear-mood', chosenMoods.length > 0);
    showClear('clear-chaos', chosenChaos !== null);
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

  /* --- the four clears ----------------------------------------------------- */
  /* Each resets ONE section and nothing else. Deliberately four separate
     controls rather than one "clear all": with four axes, the filter you want
     to drop is almost never all of them -- you have found the mood and are now
     arguing with the cupboard. */
  function wireClear(id, reset) {
    var btn = document.getElementById(id);
    if (btn) btn.addEventListener('click', function () { reset(); apply(); });
  }

  wireClear('clear-mood', function () {
    chosenMoods.length = 0;
    moodBtns.forEach(function (b) {
      b.classList.remove('is-on');
      b.setAttribute('aria-pressed', 'false');
    });
  });

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
