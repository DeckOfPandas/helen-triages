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

  btn.addEventListener('click', function () {
    var making = article.classList.toggle('is-making');
    btn.classList.toggle('is-on', making);
    btn.setAttribute('aria-pressed', making ? 'true' : 'false');
    btn.textContent = making ? 'read about it' : 'make it';
  });
})();
