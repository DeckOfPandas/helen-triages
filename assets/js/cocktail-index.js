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
      card.querySelectorAll('.drink-card-ing').forEach(function (el) {
        var text = el.textContent.toLowerCase();
        var hit = include.some(function (w) { return text.indexOf(w) !== -1; });
        el.classList.toggle('drink-card-hit', hit);
      });
    });

    if (countEl) countEl.textContent = shown;
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
      vocabulary
        .filter(function (w) { return w.indexOf(typed) !== -1 && chosen.indexOf(w) === -1; })
        .slice(0, 8)   /* capped, and the cap is visible: a pool longer than
                          this stops being a shortlist and becomes a second
                          index to read. */
        .forEach(function (w) { pool.appendChild(chip(w, false)); });
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

  apply();
})();
