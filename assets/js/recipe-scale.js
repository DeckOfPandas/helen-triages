// recipe-scale.js
// =============================================================================
// THE RECIPE SCALER'S DOM HALF -- read the amounts, write them back for N people.
// =============================================================================
// GitHub issue #1005, 2026-09-14. The arithmetic is assets/js/food-scale.js
// (HTF.foodScale) and this file holds none of it -- the split cocktail-scale.js
// runs against scale.js, for the same reason: the maths is the part worth
// testing without a browser, and tests/js/food-scale.test.js is where it is.
//
// PORTIONS, NOT MULTIPLES. The box starts at however many the recipe makes
// (`data-portions`, from _plugins/food_shopping.rb via the layout) and the
// factor is wanted over made, so a recipe for six shown for four is at x0.67
// -- the shopping list's own arithmetic. Helen's ruling for food; the drink
// page's whole-recipes rule is the drink page's.
//
// THE ORIGINAL AMOUNTS ARE STASHED ON FIRST RUN and every redraw scales from
// those, never from what is on screen -- scaling the displayed text would
// compound. AT THE RECIPE'S OWN COUNT THE ORIGINAL TEXT GOES BACK, byte for
// byte, rather than a re-rendering of it: "1.2 kg" as Helen wrote it, not the
// formatter's opinion of it.
//
// THE AMOUNT SPAN HOLDS A DECORATION AND A TEXT NODE. `.ingredient-amount-number`
// wraps the highlighter's slot (an aria-hidden span decorations.js fills with
// an SVG) and then the amount as text. Only the text nodes are read and
// replaced; the slot is left alone, so the yellow stays under the number.
//
// THE NOTE NAMES WHAT DID NOT MOVE. Helen: "let's add a note to bitters and
// handfuls (copy tbc, just put in a placeholder)". Two kinds of line cannot
// scale: an amount with no number in it ("a few handfuls", "some") and an
// ingredient with no amount at all. When the portions differ from the
// recipe's own, both kinds are listed by name under the control; at the
// recipe's own count the note is hidden, because nothing has moved.
// PLACEHOLDER COPY -- the sentence is marked in the layout and is hers.
//
// THE CONTROL SHIPS `hidden` AND THIS REVEALS IT -- the rule every
// JS-dependent control on both sites follows.
//
// AN EMPTY OR HALF-TYPED BOX IS NO CHANGE (the backspace rule, from
// cocktail-scale.js: `input` fires on every keystroke and clearing the box to
// type `4` must not flash anything), and the box is tidied on the way out.
// =============================================================================
(function () {
  'use strict';

  var HTF = window.HTF;
  if (!HTF || !HTF.foodScale) return;

  var article = document.querySelector('article.recipe');
  if (!article) return;

  var control = article.querySelector('.recipe-scale-controls');
  var input = control && control.querySelector('.recipe-scale-portions');
  var minus = control && control.querySelector('.recipe-scale-minus');
  var plus = control && control.querySelector('.recipe-scale-plus');
  var note = article.querySelector('.recipe-scale-note');
  if (!control || !input || !minus || !plus || !note) return;

  var base = parseInt(input.getAttribute('data-portions'), 10);
  if (!(base > 0)) return;

  var spans = Array.prototype.slice.call(
    article.querySelectorAll('.ingredient-amount-number')
  );
  var rows = Array.prototype.slice.call(
    article.querySelectorAll('.ingredients li.ingredient')
  );
  if (!spans.length) return;

  function textOf(span) {
    var out = '';
    Array.prototype.forEach.call(span.childNodes, function (node) {
      if (node.nodeType === 3) out += node.nodeValue;
    });
    return out.trim();
  }

  function write(span, text) {
    Array.prototype.slice.call(span.childNodes).forEach(function (node) {
      if (node.nodeType === 3) span.removeChild(node);
    });
    span.appendChild(document.createTextNode(text));
  }

  var original = spans.map(textOf);

  /** The ingredient's own name: the row's text with its amount and its note
      taken out. For the note under the control, not for anything else. */
  function nameFor(row) {
    var copy = row.cloneNode(true);
    Array.prototype.slice.call(
      copy.querySelectorAll('.ingredient-amount, .ingredient-annotation')
    ).forEach(function (el) { el.parentNode.removeChild(el); });
    return copy.textContent.replace(/\s+/g, ' ').trim();
  }

  var last = base;

  function put(field, value) {
    if (field !== document.activeElement) field.value = value;
  }

  function apply(wanted) {
    var n = Math.max(1, Math.round(wanted));
    var factor = n / base;
    var still = [];

    spans.forEach(function (span, index) {
      if (n === base) {
        write(span, original[index]);
        return;
      }
      var result = HTF.foodScale.scaleAmount(original[index], factor);
      write(span, result.text);
      if (!result.scaled) {
        var row = span.closest ? span.closest('li.ingredient') : null;
        if (row) still.push(nameFor(row));
      }
    });

    // An ingredient with no amount at all is as written whatever the box says.
    if (n !== base) {
      rows.forEach(function (row) {
        if (!row.querySelector('.ingredient-amount-number')) still.push(nameFor(row));
      });
    }

    last = n;
    put(input, String(n));

    /* PLACEHOLDER COPY, Helen's to write -- the layout marks the element. */
    if (n !== base && still.length) {
      note.textContent = 'Not scaled: ' + still.join('; ') + '.';
      note.hidden = false;
    } else {
      note.hidden = true;
    }
  }

  function pending(box) {
    var n = parseFloat(box.value);
    return box.value.trim() === '' || !isFinite(n) || n <= 0;
  }

  function redraw() {
    if (pending(input)) return;
    apply(parseFloat(input.value));
  }

  function settle() {
    input.value = String(last);
  }

  function step(delta) {
    return function () { apply(last + delta); };
  }

  input.value = String(base);
  control.hidden = false;

  input.addEventListener('input', redraw);
  input.addEventListener('change', settle);
  input.addEventListener('blur', settle);
  minus.addEventListener('click', step(-1));
  plus.addEventListener('click', step(1));
})();
