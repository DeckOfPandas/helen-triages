// card-tagline.js
// A card's tagline where there is nothing to hover with (#1292): the `?`
// beside the shortlist `+` swaps the card between tagline and ingredients.
//
// The stylesheet decides who sees the mark (only under `(hover: none)`). This
// file un-hides it, since it ships `hidden` so a page with no script has no
// dead control, and keeps `is-tagline-shown` on the card and `aria-pressed`
// on the button in step.
//
// One listener on the document, so a card added later needs no wiring.
// `preventDefault` and `stopPropagation` because the whole card is the
// drink's link (#971). Loaded from the shared layout: a related card on a
// drink page is the index card (#991).
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
