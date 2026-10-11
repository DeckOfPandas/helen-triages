// card-name-fit.js
// A drink name that does not fit its tape: shrink it if one size step reaches
// it, otherwise wrap it to two lines. The rule is about HOW MUCH the name is
// over by, so it is a measurement, never a character count.
//
// Two states and no more: one step and one re-measure, never a search for the
// scale each name needs, or a grid of cards carries titles at a dozen sizes.
//
// Runs at load, on `document.fonts.ready` (until the real face arrives every
// width is measured in the fallback) and on a debounced resize (a card's
// width follows the viewport). Also exposed as `HTF.fitCardNames()` for
// anything that puts a `.drink-card-name` on the page later or un-hides one.
// Site-agnostic: it does nothing on a page with no `.drink-card-name`, and it
// never reads the type size, so cards and the drink page's title share it.

(function () {

  // Must equal the scale `.drink-card-name--step` sets in
  // _sass/cocktails/_cards.scss (`$card-name-step`). Two copies of one
  // decision: CSS cannot do the arithmetic and JS should not set type sizes.
  var STEP = 0.86;

  var NAME = '.drink-card-name';
  var WORD = '.drink-card-tape-word';
  var STEP_CLASS = 'drink-card-name--step';
  var WRAP_CLASS = 'drink-card-name--wrap';

  // Not a third state: it says this script has measured the name, and every
  // measured name gets it. The stylesheet uses it to release the no-JS
  // ellipsis clip (`overflow: hidden` on the tape word), which would otherwise
  // clip the card's click overlay to the lettering (#971).
  var FITTED_CLASS = 'drink-card-name--fitted';

  /**
   * How wide is the lettering itself? A Range over the contents, not
   * `scrollWidth`: the card's click overlay is an absolutely positioned
   * pseudo-element whose containing block is this box, so it counts towards
   * scrollWidth and every name would read as overflowing (#971). A Range
   * measures the DOM, and a pseudo-element is not in it. It also measures the
   * drink page's `<h1>` at `display: contents`, which has no box of its own.
   */
  function contentWidth(el) {
    var range = document.createRange();
    range.selectNodeContents(el);
    var w = range.getBoundingClientRect().width;
    range.detach();
    return w;
  }

  /**
   * Does this element's content run wider than its box? The 1px is sub-pixel
   * layout: a word that exactly fills its box measures a fraction larger.
   */
  function overflows(el) {
    return contentWidth(el) > el.clientWidth + 1;
  }

  function fit(name) {
    var word = name.querySelector(WORD);
    if (!word) return;

    // A box with no client rects cannot be measured (#1115): a card paginated
    // away with `hidden` measures zero, and `0 > 0 + 1` reads as "it fits".
    // Returning BEFORE FITTED_CLASS is the point: the class releases the
    // no-JS clip on the strength of a measurement, and none happened. The
    // name is measured on a later pass; cocktail-index.js re-runs this on
    // every filter pass. Not a `hidden` check, so it also covers
    // `display: none` on an ancestor.
    if (!word.getClientRects().length) return;

    // Always from the base state, or the second run measures the first run's
    // output and a stepped name can never step back up on a wider card.
    name.classList.remove(STEP_CLASS);
    name.classList.remove(WRAP_CLASS);

    // Not reset with the two above: it is not a state.
    name.classList.add(FITTED_CLASS);

    if (!overflows(word)) return;

    // At STEP of the type the word needs STEP of the width, so the step
    // reaches it when today's content width is within clientWidth / STEP.
    if (contentWidth(word) <= word.clientWidth / STEP) {
      name.classList.add(STEP_CLASS);

      // The prediction is a linear model and type is not quite linear.
      // Re-measure once; a stepped name that still overflows wraps instead.
      if (overflows(word)) {
        name.classList.remove(STEP_CLASS);
        name.classList.add(WRAP_CLASS);
      }
      return;
    }

    name.classList.add(WRAP_CLASS);
  }

  /**
   * Measure and classify every card name on the page. Re-queries the document
   * each time: universe.js deals a fresh name into the page after load, and a
   * cached list would never classify it.
   */
  function fitAll() {
    var names = document.querySelectorAll(NAME);
    for (var i = 0; i < names.length; i++) fit(names[i]);
  }

  // Exposed BEFORE the first pass. Guarded: this file must work with no HTF
  // namespace at all.
  if (window.HTF) window.HTF.fitCardNames = fitAll;

  fitAll();

  // card-line-budget.js waits longer than this on resize so that it runs
  // after the names are refitted; keep this delay the shorter of the two.
  var timer;
  window.addEventListener('resize', function () {
    clearTimeout(timer);
    timer = setTimeout(fitAll, 120);
  });

  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(fitAll);
  }
})();
