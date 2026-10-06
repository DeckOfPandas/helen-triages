// card-tagline.js
// =============================================================================
// A CARD'S TAGLINE, WHERE THERE IS NOTHING TO HOVER WITH -- #1292.
// =============================================================================
// On a computer, pointing at a drink card lets its tagline take the card, and
// that half is the stylesheet's alone (`_sass/cocktails/_cards.scss`). A phone
// or a tablet has no pointer to hover with, so each card with a written
// tagline carries a `?` beside its shortlist `+`: press it and the card shows
// the tagline, press it again and the ingredients come back. Helen,
// 2026-10-06: "a simple question mark to the left of the + icon".
//
// THE STYLESHEET DECIDES WHO SEES THE MARK, not this file: the button is drawn
// only under `(hover: none)`. This file un-hides it (it ships `hidden`, the
// shortlist button's habit, so a page with no script has no dead control) and
// keeps two things in step when it is pressed: `is-tagline-shown` on the card,
// which is the state the stylesheet reads, and `aria-pressed` on the button.
//
// ONE LISTENER ON THE DOCUMENT, so a card that arrives later needs no wiring of
// its own. `preventDefault` and `stopPropagation` because the whole card is the
// drink's link (#971) and this must not open it.
//
// LOADED FROM THE SHARED LAYOUT, like card-name-fit.js: a related card on a
// drink page is the index card (#991) and gets the same mark. A page with no
// card finds nothing and does nothing.
// =============================================================================
(function () {
  'use strict';

  var SHOWN = 'is-tagline-shown';

  function reveal() {
    var marks = document.querySelectorAll('.btn-card-tagline');
    for (var i = 0; i < marks.length; i++) marks[i].hidden = false;
  }

  document.addEventListener('click', function (ev) {
    var mark = ev.target.closest ? ev.target.closest('.btn-card-tagline') : null;
    if (!mark) return;
    ev.preventDefault();
    ev.stopPropagation();
    var card = mark.closest('.drink-card');
    if (!card) return;
    var on = card.classList.toggle(SHOWN);
    mark.setAttribute('aria-pressed', on ? 'true' : 'false');
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', reveal);
  } else {
    reveal();
  }
})();
