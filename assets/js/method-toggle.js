// method-toggle.js
// Switches a recipe page between the full method and the short one.
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
    // Storage can be blocked (a strict private window) and then throws; the
    // toggle must still work, only unremembered (#1386).
    try { sessionStorage.setItem(SESSION_KEY, mode); } catch (e) {}
  }

  var remembered = null;
  try { remembered = sessionStorage.getItem(SESSION_KEY); } catch (e) {}
  if (remembered === 'short') setMode('short');

  btn.addEventListener('click', function () {
    setMode(shortMethod.hidden === false ? 'full' : 'short');
  });
})();
