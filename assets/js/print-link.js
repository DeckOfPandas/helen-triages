// print-link.js
// Reveals and wires a recipe or drink page's "print" control (#86).
//
// The button ships `hidden` because it cannot work without JavaScript; this
// script takes the attribute off. The PDF link beside it is a plain anchor
// that works with JS off, and must not be managed from here.
(function () {
  var btn = document.querySelector('.btn-print');
  if (!btn) return;

  btn.hidden = false;

  btn.addEventListener('click', function () {
    window.print();
  });
})();
