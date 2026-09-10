// card-line-budget.js
// =============================================================================
// A CARD IS A FIXED HEIGHT, SO ITS THREE STACKS SHARE ONE BUDGET.
// =============================================================================
// GitHub issue #776, Helen: "if cocktail card ingredients have three lines, only
// allow the chips two lines", and "if the cocktail name has two lines, only
// allow ingredients and chips two lines each".
//
// `$card-height` is 12.9rem and does not move -- the grid depends on every card
// being the same height. Three things inside it can grow: the name (one line or
// two, decided by card-name-fit.js), the ingredient line (clamped at three) and
// the chip rows (capped at three). Each cap was chosen on its own and they can
// all be spent at once, which is the overflow this closes.
//
// THE NAME HALF NEEDS NO SCRIPT and is done in the stylesheet. card-name-fit.js
// already marks a wrapped name with `.drink-card-name--wrap`, and the name, the
// ingredient line and the foot are siblings, so `~` reaches both from it. See
// `_sass/cocktails/_cards.scss`.
//
// THE INGREDIENT HALF DOES, because CSS cannot ask how many lines a clamped
// element actually rendered -- only how many it is allowed. `-webkit-line-clamp:
// 3` is a ceiling, and most cards do not reach it: the median drink has five
// ingredients and fits two lines. A rule keyed on the clamp would punish every
// card for what the tiki drinks do.
//
// SO IT MEASURES, the same way card-name-fit.js does, and for
// the same stated reason: the browser already knows. Height divided by line
// height, rounded, is the line count; three or more sets the class.
//
// ROUNDED, NOT FLOORED. `getBoundingClientRect().height` is fractional and
// `line-height: 1.5` at `font-size: 0.82rem` is not a whole pixel, so three
// lines can measure as 2.98 or 3.02 depending on zoom and font metrics.
// Flooring turns the first into two lines and silently drops the rule on a card
// that visibly has three.
//
// THE CLASS GOES ON THE CARD, not the paragraph, because what it governs lives
// in a different subtree -- the chips are inside `.drink-card-foot`. The
// stylesheet keeps every decision about what it MEANS; this file measures and
// has no opinion about chips.
//
// IT RUNS AFTER card-name-fit.js, AND IS NOW THE LAST PASS IN THE CHAIN.
// The name decides how much room the ingredients get, and the ingredients
// decide how much the chips get, so running before the name pass is not a crash
// -- it is a budget computed against a name that had not been fitted yet.
// `_layouts/default.html` fixes the order; see its script tags.
//
// A THIRD PASS USED TO FOLLOW THIS ONE. chip-rows.js measured where the chip
// rows actually broke, so the stylesheet could suppress a leading separator dot
// on a chip that began a row (#698). #846 moved the dot to a trailing `::after`
// on every chip but the last, so nothing depends on where a row breaks and the
// file was deleted.
//
// AND IT MUST RE-RUN WHEN THE VISIBLE SET CHANGES, which is why `run` hangs off
// HTF. The index paginates by setting `card.hidden`, not by removing cards, and
// A HIDDEN ELEMENT MEASURES ZERO HEIGHT -- so the load-time pass can only ever
// classify page one. cocktail-index.js calls this on every filter pass.
// =============================================================================
(function () {
  'use strict';

  var THREE_LINES = 'drink-card--ingredients-3';

  // THE SHIP AND THE LAST CHIP ROW -- 2026-09-10. #760 took the ship out of
  // flow so no chip row would pay for it, and masked it over the chips so a
  // chip reaching it reads as cut off rather than overprinted. Helen, seeing
  // it live: cut off mid-word is wrong ("sugar crav", "no juici"). CSS cannot
  // pad only the row that collides, and padding every row is the cost #760
  // refused, so this measures: if any chip on the ship's row reaches past the
  // ship's left edge, the card gets this class and `--ship-w`, and the
  // stylesheet pads the chips clear of the ship ON THAT CARD ONLY. A chip that
  // then falls to a fourth row is hidden whole by the row cap, which is the
  // lesser thing to lose.
  var CLEAR_SHIP = 'drink-card--chips-clear-ship';

  function lineCount(el) {
    var style = window.getComputedStyle(el);
    var lh = parseFloat(style.lineHeight);
    // `normal` computes to a keyword in some engines. Fall back to the font
    // size times the 1.5 the stylesheet sets, rather than guessing 1.
    if (!isFinite(lh) || lh <= 0) lh = parseFloat(style.fontSize) * 1.5;
    if (!isFinite(lh) || lh <= 0) return 0;
    return Math.round(el.getBoundingClientRect().height / lh);
  }

  function apply(card) {
    var line = card.querySelector('.drink-card-ingredients');
    if (!line) return;
    // Reset first, so a re-run at a new width can take the class OFF again --
    // the bug card-name-fit.js's step 1 exists to prevent.
    card.classList.remove(THREE_LINES);
    if (lineCount(line) >= 3) card.classList.add(THREE_LINES);
    clearShip(card);
  }

  /* Measured with the class OFF, so a re-run at a new width can take it away
     again -- the same reset-then-measure order the ingredient pass keeps. The
     ship's left edge is the line; a chip whose box crosses it AND sits on the
     ship's row (vertical overlap) is the collision. Chips on rows above the
     ship are not in the way and are not counted. */
  function clearShip(card) {
    var ship = card.querySelector('.drink-card-ship');
    var moods = card.querySelector('.drink-card-moods');
    card.classList.remove(CLEAR_SHIP);
    if (card.style) card.style.removeProperty('--ship-w');
    if (!ship || !moods) return;
    var s = ship.getBoundingClientRect();
    if (!s.width) return;   // hidden card, or no verdict drawn
    var chips = moods.querySelectorAll('.drink-card-mood');
    for (var i = 0; i < chips.length; i++) {
      var c = chips[i].getBoundingClientRect();
      var sameRow = c.bottom > s.top && c.top < s.bottom;
      if (sameRow && c.right > s.left) {
        if (card.style) card.style.setProperty('--ship-w', s.width + 'px');
        card.classList.add(CLEAR_SHIP);
        return;
      }
    }
  }

  function run() {
    var cards = document.querySelectorAll('.drink-card');
    for (var i = 0; i < cards.length; i++) apply(cards[i]);
  }

  window.HTF = window.HTF || {};
  window.HTF.cardLineBudget = run;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
  window.addEventListener('resize', run);

  // AND AGAIN ONCE THE REAL FACE ARRIVES -- 2026-09-10, found by the ship
  // pass. At DOMContentLoaded the chips are set in the fallback Courier, which
  // is narrower than Courier Prime; the rows measured clean, then the web font
  // landed, the last row grew into the ship and nothing re-measured. Seven of
  // twenty cards on the first deal. card-name-fit.js re-runs on
  // `document.fonts.ready` for the same reason; this pass now does too, and
  // stays after it in the chain.
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(run);
  }
})();
