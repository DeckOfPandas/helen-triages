// The drink scaler's DOM half (#545): read the amounts, write them back at a
// multiple. The arithmetic is assets/js/scale.js (HTF.scale), tested in
// tests/js/scale.test.js; this file holds none of it.
//
// The box holds whole recipes, never below one: an amount on the 2.5 ml grid
// stays on it at an integer multiple, so no ratio moves.
//
// The written amounts are stashed in `data-amount` on first run and every
// redraw scales from those; scaling the displayed text would compound.
//
// The control ships `hidden` and this reveals it, so a page whose script did
// not run shows no dead control.
//
// An empty or half-typed box is no change, never a refusal: `input` fires on
// every keystroke. The box is tidied on `change` and `blur`.
(function () {
  'use strict';

  var HTF = window.HTF;
  if (!HTF || !HTF.scale) return;

  var article = document.querySelector('article.cocktail');
  if (!article) return;

  var control = article.querySelector('.cocktail-scale-controls');
  var input = control && control.querySelector('.cocktail-scale-multiple');
  var minus = control && control.querySelector('.cocktail-scale-minus');
  var plus = control && control.querySelector('.cocktail-scale-plus');
  var spans = Array.prototype.slice.call(
    article.querySelectorAll('.cocktail-amount')
  );
  /* Every element in this guard must exist in the layout: removing one there
     without removing it here stops the scaler initialising, silently, since
     the control ships `hidden`. */
  if (!control || !input || !minus || !plus || !spans.length) return;

  /* The amount spans are the index, not the ingredient list: an ingredient
     with no `amount` renders no span, so the two differ in length. */
  var original = spans.map(function (span) {
    if (!span.hasAttribute('data-amount')) {
      span.setAttribute('data-amount', span.textContent.trim());
    }
    return span.getAttribute('data-amount');
  });

  var last = 1;
  input.value = box(last);
  control.hidden = false;

  /* What the box shows for a multiple. Whole recipes only (see the header);
     HTF.scale can still snap to fractional multiples, but this page never
     asks it to. */
  function box(n) {
    return String(n);
  }

  /* The box is never written to while it has focus: typing is the one thing
     the script cannot redo. `settle` tidies it when the reader leaves. */
  function put(field, value) {
    if (field !== document.activeElement) field.value = value;
  }

  /* A refusal puts the last working multiple back, through `put`, and says
     nothing (#1088): a message would fire on a drink's own written recipe if
     it held a pour under the floor. */
  function refuse() {
    put(input, box(last));
  }

  /* A unit the name already says is not said twice (#1132). On a row the
     layout marks `data-unit-quiet` the number goes in the amount and the unit
     in the name's `.cocktail-unit-in-name` slot ("2" beside "sugar cubes");
     an `each` row has no slot and its unit is dropped. The layout decides
     which rows; `data-amount` keeps the written "1 cube" for the arithmetic. */
  function show(span, text) {
    if (!span.hasAttribute('data-unit-quiet')) {
      span.textContent = text;
      return;
    }
    var parts = HTF.scale.splitUnit(text);
    span.textContent = parts.number;
    var row = span.closest ? span.closest('.cocktail-ingredient') : null;
    var slot = row && row.querySelector('.cocktail-unit-in-name');
    if (slot && parts.unit) slot.textContent = parts.unit;
  }

  /** Render the drink at a whole multiple, or leave it as it is. */
  function apply(wanted) {
    /* Rounded to a whole recipe and never below one: `1.5` becomes 2, and
       `settle` writes the rounded number back so the reader sees it. */
    var n = Math.max(1, Math.round(wanted));

    var verdict = HTF.scale.scale(original, n);
    if (!verdict.ok) {
      refuse();
      return;
    }

    last = n;
    spans.forEach(function (span, index) {
      show(span, verdict.amounts[index]);
    });
    put(input, box(last));
    batch(n);
  }

  /* The batch note is the bitters caveat and nothing else (#1121), shown only
     above ×1 and only where the layout's `data-has-dashes` says the drink has
     dashes or drops (#720). The layout renders the element only for such a
     drink, so a null `batchNote` is normal. */
  var batchNote = article.querySelector('.cocktail-scale-batch');

  /* Above ×1 a pour in dashes or drops is struck through with a `*` beside
     it, matching the note's `*` (#1293). The amount still scales, so the
     reader can see which way to err. The layout marks the rows (`data-dashes`)
     and prints the star hidden; this only flips attributes. */
  var dashed = spans.filter(function (span) {
    return span.hasAttribute('data-dashes');
  });
  var stars = Array.prototype.slice.call(
    article.querySelectorAll('.cocktail-amount-star')
  );

  function batch(n) {
    var above = n > 1;
    dashed.forEach(function (span) {
      if (above) span.setAttribute('data-struck', '');
      else span.removeAttribute('data-struck');
    });
    stars.forEach(function (star) { star.hidden = !above; });

    if (!batchNote) return;
    if (!above) {
      batchNote.hidden = true;
      return;
    }

    var text = batchNote.getAttribute('data-has-dashes') === 'true'
      ? '* Don’t scale bitters linearly — add to taste.'
      : '';

    batchNote.textContent = text;
    batchNote.hidden = !text;
  }

  /* Nothing typed yet, not a number, or not positive: a keystroke on the way
     somewhere (`0` is the first key of `0.5`), never a request. */
  function pending(box) {
    var n = parseFloat(box.value);
    return box.value.trim() === '' || !isFinite(n) || n <= 0;
  }

  function redraw() {
    if (pending(input)) return;
    apply(parseFloat(input.value));
  }

  input.addEventListener('input', redraw);

  /* Tidied on the way out, deliberately without `put`'s guard: the job is to
     write into the field just typed in. `blur` as well as `change`, because
     `change` does not fire when the same number is retyped. */
  function settle() {
    input.value = box(last);
  }

  input.addEventListener('change', settle);
  input.addEventListener('blur', settle);

  /* The − and + buttons (#731) go through `apply`, the function a typed value
     reaches, so the ×1 minimum is one piece of code. Minus at ×1 asks for 0,
     which `apply` clamps back to 1. */
  function step(delta) {
    return function () {
      apply(last + delta);
    };
  }

  minus.addEventListener('click', step(-1));
  plus.addEventListener('click', step(1));
})();
