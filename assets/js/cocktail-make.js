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

  /* Three controls, one piece of state (`is-making` on the article). A label
     sets the mode its `data-mode` names; the track flips whatever is current. */
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
