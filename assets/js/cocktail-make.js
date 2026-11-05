/* The read-it / make-it toggle: one class on the article, and the stylesheet
   does the rest.

   Nothing is removed from the DOM, only hidden by CSS, so the page prints and
   reads whole with this file blocked. That is why the default state is the
   editorial one: if the script never runs, the reader gets the fuller page. */
(function () {
  var track = document.getElementById('cocktail-make');
  var labels = document.querySelectorAll('.cocktail-toggle-label');
  var article = document.querySelector('article.cocktail');
  if (!track || !labels.length || !article) return;

  /* A note `make it` keeps (`.note--for-making`, a house syrup's recipe) is
     pointed at from its ingredient's own note, which stays with it. The
     layout writes each note's `|label|` and each ingredient note's
     `|generic|generic|`; whole names, so `indexOf` cannot half-match. */
  var kept = article.querySelectorAll('.note--for-making[data-for]');
  Array.prototype.forEach.call(article.querySelectorAll('.cocktail-note[data-generics]'), function (note) {
    var generics = note.getAttribute('data-generics');
    Array.prototype.forEach.call(kept, function (k) {
      if (generics.indexOf(k.getAttribute('data-for')) !== -1) {
        note.classList.add('cocktail-note--for-making');
      }
    });
  });

  /* Three controls, one piece of state (`is-making` on the article). A label
     sets the mode its `data-mode` names; the track flips whatever is current. */
  function setMode(making) {
    article.classList.toggle('is-making', making);
    track.setAttribute('aria-checked', making ? 'true' : 'false');
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
