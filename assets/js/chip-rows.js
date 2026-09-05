// chip-rows.js
// =============================================================================
// A MOOD WORD THAT STARTS A LINE WEARS NO SEPARATOR.
// =============================================================================
// GitHub issue #698, Helen: "cocktail card: no dot before the first chip."
//
// THE DOT WAS NEVER BEFORE THE FIRST CHIP, WHICH IS WHY THIS TOOK A MEASUREMENT
// TO FIND. `_sass/cocktails/_cards.scss` draws the middle dot on the FOLLOWING
// word's `::before` through `& + &`, an adjacent-sibling rule, so chip one of a
// card has never had one and could not. What it has is a dot before the first
// chip OF THE SECOND ROW: `.drink-card-moods` is `flex-wrap: wrap` with room
// for two rows, and a wrapped chip takes its `::before` over the line break
// with it. The seam that reads correctly between two words on one line reads as
// a bullet hanging off the left margin when the line ends between them.
//
// IT IS THE MAJORITY OF CARDS, not an edge case, and that was measured rather
// than guessed at. The foot is 232.4px on the grid's minimum 370px card
// (370 less the 6.5rem glass column, the 0.95rem gutter and the 1.15rem pad),
// mood words are Courier at 0.72rem, and on 2026-09-05 SEVENTY-SIX of the 124
// drinks carrying a mood list -- 61% -- run past that and wrap. Thirty-three
// have four moods, fifteen have six, two have eight.
//
// WHY THIS IS A SCRIPT AND NOT A SELECTOR, which is the same argument
// last-line-rule.js already settled for the wrapped-title rules: CSS cannot
// ask where a line broke. `:first-child` is the first chip of the ELEMENT and
// there is no `:first-of-line`. Two CSS-only dodges were considered and both
// are worse than they look:
//
//   - Clip the dot with `overflow: hidden` on the container, drawing it
//     absolutely at `right: 100%` so a row-leading chip's dot falls at x < 0.
//     It works on a card, whose `.drink-card-moods` already clips for the
//     two-row cap -- and it costs the drink page's `.cocktail-chips` an
//     `overflow: hidden` it has no other reason to carry, which would then clip
//     the focus outline of a row-leading chip. Those chips are LINKS on that
//     page since 2026-09-05. A decorative dot is not worth a keyboard user's
//     focus ring.
//   - Move the dot to the preceding chip's `::after`. That only relocates the
//     orphan to the end of row one, where it reads as a sentence cut off.
//
// So: measure `offsetTop`, and mark the chips that begin a row. The stylesheet
// keeps every decision about what the mark MEANS -- this file adds a class and
// has no opinion about dots.
//
// SITE-AGNOSTIC AND CONTAINER-AGNOSTIC, the house pattern that print-link.js,
// universe.js, last-line-rule.js and card-name-fit.js all follow: it queries a
// class and does nothing on a page without one. Food has no `.drink-card-mood`.
// Cocktails has them in two containers -- the index card's `.drink-card-moods`
// and the drink page's wider `.cocktail-chips` -- and this file names neither.
// It groups by parent, so a third would work the day it was written.
//
// THE PASS IS EXPOSED AS `HTF.markChipRows()` for anything that puts chips on
// the page after load. NOTHING CALLS IT TODAY: universe.js would, on the same
// argument that has it calling `HTF.fitCardNames()` -- a freshly cloned chip in
// a container of a different width needs re-measuring, not the class it was
// cloned with -- but since 2026-09-05 its `data-universe-parts` does not clone a
// card's foot, and the foot is where the chips are. The hook stays for the day
// that changes; cocktails/index.html says so beside the attribute that would
// change it.
// =============================================================================

(function () {

  var CHIP = '.drink-card-mood';

  // `is-` rather than a `--` modifier: `--mood` / `--hassle` say what a chip is
  // and come from the taxonomy, this says where it landed at this width and
  // changes on resize. Same convention as `.is-match` on the chip beside it.
  var ROW_START = 'is-row-start';

  /**
   * Mark the chips that begin a row, across every chip container on the page.
   *
   * Grouped by parent rather than measured as one list, because a page can hold
   * several chip rows (125 cards on the index) and "the first chip of a row" is
   * a question about one container at a time.
   *
   * `offsetTop` is the test rather than `getBoundingClientRect().top`: it is
   * relative to the offset parent, so it does not move when the page scrolls,
   * and it is integral, so two chips on one line cannot differ by a sub-pixel
   * and be read as two rows. Chips on a line share a top because they share a
   * `line-height` and `align-items` is the flex default (`stretch`).
   */
  function markAll() {
    var chips = document.querySelectorAll(CHIP);
    var previous = null;

    for (var i = 0; i < chips.length; i++) {
      var chip = chips[i];

      // ALWAYS FROM THE BASE STATE, the same discipline card-name-fit.js keeps
      // and for the same reason: without the reset the second pass measures the
      // first pass's output, and a chip that stopped starting a row when the
      // card grew would keep the class for ever.
      chip.classList.remove(ROW_START);

      // A new container, or a different `offsetTop` inside the same one, both
      // mean this chip begins a row. querySelectorAll returns document order,
      // so the previous chip is the one to compare against.
      var isFirstInContainer = !previous || previous.parentNode !== chip.parentNode;
      if (isFirstInContainer || chip.offsetTop !== previous.offsetTop) {
        chip.classList.add(ROW_START);
      }

      previous = chip;
    }
  }

  // Exposed BEFORE the first pass, so a caller running during this file's parse
  // finds it. Guarded, because this file must not acquire a dependency on the
  // namespace: with no HTF at all the three passes below still work.
  if (window.HTF) window.HTF.markChipRows = markAll;

  markAll();

  // The three runs card-name-fit.js makes, each load-bearing for the same
  // reason: a chip row's break points follow the card's width, and until the
  // real face lands every word is measured in the fallback.
  var timer;
  window.addEventListener('resize', function () {
    clearTimeout(timer);
    timer = setTimeout(markAll, 120);
  });

  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(markAll);
  }
})();
