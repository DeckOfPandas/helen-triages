/* =============================================================================
   THE MAKE-IT TOGGLE. One class on the article; the stylesheet does the rest.
   =============================================================================
   Editorial by default — tagline, bottle suggestions, character notes, notes,
   glass drawn large. `make it` strips to the bar-side spec: bigger amounts,
   bigger method, small glass, everything you do not need with your hands full
   hidden.

   NOTHING IS REMOVED FROM THE DOM, only hidden by CSS, so the page prints
   whole and reads whole with this file blocked. That is the same contract
   assets/js/back-link.js follows, and it is the reason the DEFAULT state is
   the editorial one: if the script never runs, the reader gets the version
   with more in it rather than less.
   ============================================================================= */
(function () {
  var btn = document.getElementById('cocktail-make');
  var article = document.querySelector('article.cocktail');
  if (!btn || !article) return;

  /* THE LABEL DOES NOT CHANGE, and that is the fix -- #494. It used to swap to
     "read about it" when on, which is the classic ambiguous toggle: the reader
     cannot tell whether the label describes the STATE they are in or the
     ACTION the button will take. "read about it" could equally mean "you are
     reading about it" or "press to read about it", and the two are opposites.

     Helen: "Maybe just 'make it' as a toggle, obvious whether it's on or off."
     So the label is constant and always names the action, and the STATE is
     carried by the fill and by aria-pressed -- which is what a screen reader
     was already being told, and was the only part that had it right. */
  btn.addEventListener('click', function () {
    var making = article.classList.toggle('is-making');
    btn.classList.toggle('is-on', making);
    btn.setAttribute('aria-pressed', making ? 'true' : 'false');
  });
})();
