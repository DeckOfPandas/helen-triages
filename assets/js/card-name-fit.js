// card-name-fit.js
// =============================================================================
// A NAME THAT DOES NOT FIT: SHRINK IT IF ONE STEP REACHES IT, OTHERWISE WRAP.
// =============================================================================
// Design audit critical #9, DESIGN_PLAN §3 item 5, decided 2026-09-04 from a
// candidates page on the real cocktails index. Helen, having switched between
// the treatments on the page itself:
//
//   "Let's do: shrink when it's just one short-ish word too long, then two
//    lines where it's more than that. The one super-long title we have I'll
//    just shorten, and retain that principle."
//
// THE PRINCIPLE, WHICH IS THE PART THAT BINDS: the rule is about HOW MUCH the
// name is over by, not about how long the name is. One size step of 0.86 buys
// about 14% of the line — four or five characters of Courier Prime, which is
// what "one short-ish word" comes to. If the overflow is inside that, stepping
// makes the name fit and nobody can see that it stepped. If it is outside it,
// no plausible step reaches the name and shrinking would only produce small
// type that still ellipsises, so the tape takes a second line instead.
//
// Which is why the test is a MEASUREMENT rather than a character count. A
// character count would need the face's real advance width (Courier Prime ships
// here as woff2 only, with no parser available), would be wrong for a card at
// one width and right at another, and would have to know which of the two sizes
// the element is currently rendering at. The browser already knows all three.
//
// WHAT IT DOES, per `.drink-card-name` on the page:
//
//   1. Reset both classes, so every run measures the UNSTEPPED, UNWRAPPED
//      element. Without this the second run measures the first run's output and
//      a name can never step back up when the card gets wider.
//   2. Ask its `.drink-card-tape-word` whether it overflows —
//      `scrollWidth > clientWidth + 1`. The 1px is sub-pixel layout: a word
//      exactly filling its box reports a scrollWidth a fraction over.
//   3. If it does and `scrollWidth <= clientWidth / 0.86`, the step reaches it:
//      add `drink-card-name--step`. Dividing rather than multiplying is the
//      right way round — the QUESTION is how wide the box would have to be to
//      hold today's word, and 0.86 of the type needs 1/0.86 of the space.
//   4. Re-measure once after stepping. The predicted fit is a linear model of
//      type, and type is not quite linear: hinting, letter-spacing rounding and
//      the tape's own em padding all move a little. If it still overflows, the
//      step is undone and the name wraps. One re-measure, not a loop — see
//      below.
//   5. Otherwise add `drink-card-name--wrap`, and the Sass turns the tape into
//      a two-line object (`_sass/cocktails/_cards.scss`).
//
// ONE STEP AND ONE RE-MEASURE, NEVER A BINARY SEARCH. A search would settle on
// whatever scale each individual name needs, and a grid of cards would then
// carry titles at a dozen sizes — which is the fixed-anchor card design losing
// its argument for a case it can already answer by wrapping. Helen asked for
// two states and the file has two states.
//
// IT RUNS THREE TIMES, each load-bearing and each the same three-line pattern
// as `last-line-rule.js`, which was written the day before this for the same
// reason. Once at load; again on `document.fonts.ready`, because until the real
// face arrives every width is measured in the fallback and the answers change
// when it lands; and on a debounced resize, because a card's width follows the
// viewport — the grid is `auto-fill, minmax(370px, 1fr)`, so a card grows and
// shrinks continuously between breakpoints and a name that fits at 470px does
// not at 380px.
//
// THE PASS IS ALSO EXPOSED AS `HTF.fitCardNames()`, for anything that puts a
// new `.drink-card-name` on the page after load. `universe.js` is the one
// caller today and its reason is in the comment at that call. HTF is optional
// here: this file works with no namespace at all, so it can never be the reason
// a page fails to draw.
//
// SITE-AGNOSTIC, like print-link.js, universe.js and last-line-rule.js: it
// queries a class list and does nothing on a page that has none. Food has no
// `.drink-card-name`, so it finds nothing and returns. Cocktails has them on
// the index (every card, plus the universe pick) and on a drink page (the
// title, at 3.2rem through the same classes) — one rule covers all three,
// because the size lives in `--card-name-size` and this file never reads it.
// =============================================================================

(function () {

  // The step, and the two places it has to agree. `.drink-card-name--step` sets
  // `--card-name-scale: 0.86` in _sass/cocktails/_cards.scss; this is the same
  // number, used to predict whether stepping will be enough. They are two
  // copies of one decision and there is no way to have only one — CSS cannot
  // do the arithmetic in step 3 and JS should not be setting type sizes — so
  // the pairing is named here rather than left to be discovered.
  var STEP = 0.86;

  var NAME = '.drink-card-name';
  var WORD = '.drink-card-tape-word';
  var STEP_CLASS = 'drink-card-name--step';
  var WRAP_CLASS = 'drink-card-name--wrap';

  /**
   * Does this element's content run wider than its box?
   *
   * 1px of tolerance rather than a bare `>`: sub-pixel layout makes a word that
   * exactly fills its box report a scrollWidth a fraction larger, and without
   * the tolerance a comfortable name would be stepped for nothing.
   */
  function overflows(el) {
    return el.scrollWidth > el.clientWidth + 1;
  }

  function fit(name) {
    var word = name.querySelector(WORD);
    if (!word) return;

    // ALWAYS FROM THE BASE STATE. Every run has to measure the element as the
    // stylesheet would draw it with no class on it, or the second run measures
    // the first run's output: a stepped name looks like it fits, so it stays
    // stepped for ever even on a card twice as wide.
    name.classList.remove(STEP_CLASS);
    name.classList.remove(WRAP_CLASS);

    if (!overflows(word)) return;

    // How much wider the box would have to be to hold this word. At 0.86 of the
    // type the word needs 0.86 of the width it needs now, so it fits exactly
    // when today's scrollWidth is within clientWidth / 0.86 — about 16% over.
    if (word.scrollWidth <= word.clientWidth / STEP) {
      name.classList.add(STEP_CLASS);

      // THE PREDICTION IS A MODEL AND THE BROWSER IS THE FACT. Re-measure once,
      // now the smaller type is actually laid out; if the model was optimistic
      // (hinting, letter-spacing rounding, the tape's own em padding shrinking
      // with the type) the name wraps rather than sitting at a smaller size and
      // ellipsising anyway, which would be the worst of both treatments.
      if (overflows(word)) {
        name.classList.remove(STEP_CLASS);
        name.classList.add(WRAP_CLASS);
      }
      return;
    }

    name.classList.add(WRAP_CLASS);
  }

  /**
   * Measure and classify every card name on the page.
   *
   * Re-queries the document each time rather than caching the list, because
   * the index deals a fresh `.universe-pick` card in after load — see the call
   * in universe.js. A cached list would classify the first pick and never any
   * later one.
   */
  function fitAll() {
    var names = document.querySelectorAll(NAME);
    for (var i = 0; i < names.length; i++) fit(names[i]);
  }

  // Exposed BEFORE the first pass, so a caller that runs during this file's own
  // parse still finds it. Guarded, because this file has no dependency on the
  // namespace and must not acquire one: on a page where assets.js somehow did
  // not run, the three passes below still work.
  if (window.HTF) window.HTF.fitCardNames = fitAll;

  fitAll();

  var timer;
  window.addEventListener('resize', function () {
    clearTimeout(timer);
    timer = setTimeout(fitAll, 120);
  });

  // The real face is wider than the fallback at these sizes, so a name measured
  // before it loads is measured against the wrong type.
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(fitAll);
  }
})();
