// print-link.js
// Reveals and wires the recipe page's "print" control. GitHub issue #86.
//
// WHY THE BUTTON SHIPS HIDDEN. Printing needs window.print(), so this control
// cannot work without JavaScript -- and a button that looks live and does
// nothing is worse than no button at all. _layouts/recipe.html emits it with
// the `hidden` attribute and this script takes that off, so the control only
// ever appears on a page that can actually honour it. Same shape as the
// index's .recipe-list, which starts hidden in CSS and is revealed by
// filters.js once the first render is done: CSS has no way to ask whether a
// script ran, so the markup assumes it did not.
//
// The PDF link beside it is a plain anchor to a real file and is deliberately
// NOT touched here -- it works with JS off, and pretending otherwise by
// managing it from a script would make a working link depend on this one.
//
// Nothing here knows which site it is on, per the shared-JS rule: it queries a
// class, and does nothing on a page that has none.
(function () {
  var btn = document.querySelector('.btn-print');
  if (!btn) return;

  btn.hidden = false;

  btn.addEventListener('click', function () {
    window.print();
  });
})();
