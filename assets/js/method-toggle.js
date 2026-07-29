// method-toggle.js
// Switches a recipe page between the full method and the short one.
//
// Elements are found by CLASS, not id. The full list used to carry
// class="instructions" and id="method-full" simultaneously — one concept with
// two names, which is exactly the sort of thing that makes a codebase hard to
// hold in your head. The data calls it `method`, so everything calls it method.
(function () {
  var SESSION_KEY = 'htf-method-short';

  var btn = document.querySelector('.btn-method-toggle');
  if (!btn) return;

  var fullMethod  = document.querySelector('.method-full');
  var shortMethod = document.querySelector('.method-short');
  if (!fullMethod || !shortMethod) return;

  function setMode(mode) {
    var isShort = mode === 'short';
    fullMethod.hidden  =  isShort;
    shortMethod.hidden = !isShort;
    btn.textContent    =  isShort ? 'click for full method' : 'click for short method';
    btn.setAttribute('aria-pressed', isShort ? 'true' : 'false');
    btn.classList.toggle('active', isShort);
    sessionStorage.setItem(SESSION_KEY, mode);
  }

  if (sessionStorage.getItem(SESSION_KEY) === 'short') setMode('short');

  btn.addEventListener('click', function () {
    setMode(shortMethod.hidden === false ? 'full' : 'short');
  });
})();
