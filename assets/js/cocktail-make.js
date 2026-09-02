/* =============================================================================
   THE READ-IT / MAKE-IT TOGGLE. One class on the article; the stylesheet does
   the rest.
   =============================================================================
   Editorial by default — tagline, mood chips, bottle suggestions and notes
   shown, glass drawn large. `make it` strips to the bar-side spec: bigger
   amounts, bigger method, small glass, everything you do not need with your
   hands full hidden.

   NOTHING IS REMOVED FROM THE DOM, only hidden by CSS, so the page prints
   whole and reads whole with this file blocked. That is the same contract
   assets/js/back-link.js follows, and it is the reason the DEFAULT state is
   the editorial one: if the script never runs, the reader gets the version
   with more in it rather than less.

   REBUILT AS A THREE-PART TOGGLE, 2026-09-02, superseding the #494 reasoning
   this file used to open with. That reasoning was about a SINGLE button whose
   one label had to describe both the state you were in and the action a click
   would take — genuinely ambiguous ("read about it" could mean either), and
   #494's fix was to hold the label constant so it always named the action and
   let `aria-pressed`/the fill carry the state.

   Helen's brief asks for a different shape entirely: "remake this button as a
   binary slider/toggle... with 'read it' or 'make it' active (lighter colour,
   bolder text)." A binary toggle has TWO always-visible labels rather than one
   that changes, so #494's ambiguity cannot arise in the first place — the
   active label answers "what state am I in" on sight, without depending on
   what the word meant a click ago. The two constructions solve the same
   problem in different, non-overlapping ways; this file no longer needs #494's
   single-constant-label trick because it no longer has a single label to keep
   constant.
   ============================================================================= */
(function () {
  var track = document.getElementById('cocktail-make');
  var labels = document.querySelectorAll('.cocktail-toggle-label');
  var article = document.querySelector('article.cocktail');
  if (!track || !labels.length || !article) return;

  /* THE MODE IS DERIVED FROM WHICH LABEL WAS CLICKED, AND THE TRACK FLIPS
     WHATEVER IS CURRENT — three inputs, one piece of state (`is-making` on the
     article), so there is nothing for the three controls to disagree about.
     `data-mode` on each label ("read"/"make") is read at click time rather than
     assumed from position, so the labels could be reordered in the markup
     without this file needing to change. */
  function setMode(making) {
    article.classList.toggle('is-making', making);
    Array.prototype.forEach.call(labels, function (label) {
      var active = (label.getAttribute('data-mode') === 'make') === making;
      label.classList.toggle('is-active', active);
      label.setAttribute('aria-pressed', active ? 'true' : 'false');
    });
  }

  Array.prototype.forEach.call(labels, function (label) {
    label.addEventListener('click', function () {
      setMode(label.getAttribute('data-mode') === 'make');
    });
  });

  track.addEventListener('click', function () {
    setMode(!article.classList.contains('is-making'));
  });
})();
