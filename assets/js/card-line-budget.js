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
// SO IT MEASURES, the same way card-name-fit.js and chip-rows.js do, and for
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
// IT RUNS AFTER card-name-fit.js AND BEFORE chip-rows.js. The name decides how
// much room the ingredients get, the ingredients decide how much the chips get,
// and chip-rows.js measures where the chip rows actually broke. Running out of
// order is not a crash -- it is a card whose dots are marked for a row count it
// no longer has. `_layouts/default.html` fixes the order; see its script tags.
//
// AND IT MUST RE-RUN WHEN THE VISIBLE SET CHANGES, which is why `run` hangs off
// HTF. The index paginates by setting `card.hidden`, not by removing cards, and
// A HIDDEN ELEMENT MEASURES ZERO HEIGHT -- so the load-time pass can only ever
// classify page one. cocktail-index.js calls this on every filter pass, ahead of
// HTF.markChipRows() for the ordering reason above.
// =============================================================================
(function () {
  'use strict';

  var THREE_LINES = 'drink-card--ingredients-3';

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
})();
