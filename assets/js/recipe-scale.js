// The recipe scaler's DOM half (#1005): read the amounts, write them back for
// N people. The arithmetic is assets/js/food-scale.js (HTF.foodScale), tested
// in tests/js/food-scale.test.js; this file holds none of it.
//
// The written amounts are stashed on first run and every redraw scales from
// those; scaling the displayed text would compound. At the recipe's own count
// the original text goes back byte for byte, not a re-rendering of it.
//
// `.ingredient-amount-number` holds a decoration slot and then the amount as
// text. Only the text nodes are read and replaced.
//
// The control ships `hidden` and this reveals it. An empty or half-typed box
// is no change (`input` fires on every keystroke); the box is tidied on the
// way out.
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

  /* Portions, or the thing made (#1286). A `makes:` recipe's input carries
     `data-made`, the build's reading of that line as JSON, and the box then
     counts the thing made, never portions. What differs between the two is
     the MODE, which is HTF.foodScale's. A `data-made` that cannot be read
     leaves the control hidden. */
  var word = control.querySelector('.recipe-scale-word');
  var mode = null;
  if (input.hasAttribute('data-made')) {
    try {
      mode = HTF.foodScale.yieldMode(
        JSON.parse(input.getAttribute('data-made')),
        input.hasAttribute('data-half-recipe'));
    } catch (e) {
      mode = null;
    }
  } else {
    var people = parseInt(input.getAttribute('data-portions'), 10);
    if (people > 0) mode = HTF.foodScale.portionsMode(people);
  }
  if (!mode) return;
  var base = mode.base;

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

  /* The word lists are the build's: _layouts/recipe.html joins each with `|`
     onto the control. Absent, a list is empty. */
  function listFrom(attribute) {
    return (control.getAttribute(attribute) || '').split('|')
      .map(function (word) { return word.trim(); })
      .filter(function (word) { return word !== ''; });
  }

  var words = {
    halfStep: listFrom('data-half-step-measures'),
    // Measures stepped to the nearest quarter (#1297).
    quarterStep: listFrom('data-quarter-step-measures'),
    trailing: listFrom('data-trailing')
  };

  /* When a counted ingredient comes down to exactly one, the noun in its ITEM
     goes singular (#1286, HTF.foodScale.singularItem). Only the item's first
     text node is written, and its written value is stashed so the recipe's
     own count puts back what the recipe said. An item that opens with a link
     has no such node and is left alone. */
  var singulars = {};
  try {
    singulars = JSON.parse(control.getAttribute('data-singulars') || '{}') || {};
  } catch (e) {
    singulars = {};
  }

  function itemNodeFor(span) {
    var row = span.closest ? span.closest('li.ingredient') : null;
    if (!row) return null;
    for (var i = 0; i < row.childNodes.length; i += 1) {
      var node = row.childNodes[i];
      if (node.nodeType === 3) {
        if (node.nodeValue.trim() !== '') return node;
      } else if (node.nodeType === 1) {
        var cls = ' ' + (node.className || '') + ' ';
        if (cls.indexOf(' ingredient-amount ') === -1) return null;
      }
    }
    return null;
  }

  var items = spans.map(function (span) {
    var node = itemNodeFor(span);
    return { node: node, written: node ? node.nodeValue : '' };
  });

  /* A row with no amount: the measure may open the item's own text ("a
     handful of fresh parsley"). `leadFor` finds the row's first text, only if
     it is a bare text node directly inside the <li>; that one node is the
     only thing written, and its original value is stashed. */
  function leadFor(row) {
    for (var i = 0; i < row.childNodes.length; i += 1) {
      var node = row.childNodes[i];
      if (node.nodeType === 3) {
        if (node.nodeValue.trim() !== '') return node;
      } else if (node.nodeType === 1) {
        return null;
      }
    }
    return null;
  }

  var bare = rows.filter(function (row) {
    return !row.querySelector('.ingredient-amount-number');
  }).map(function (row) {
    var lead = leadFor(row);
    return { row: row, lead: lead, written: lead ? lead.nodeValue : '' };
  });

  /** The ingredient's own name: the row's text with its amount and its note
      taken out, then cut down to the ingredient by HTF.foodScale.noteName --
      "fresh flat-leaf parsley", not "fresh flat-leaf parsley, chopped". For
      the note under the control, not for anything else. */
  function nameFor(row) {
    var copy = row.cloneNode(true);
    Array.prototype.slice.call(
      copy.querySelectorAll('.ingredient-amount, .ingredient-annotation')
    ).forEach(function (el) { el.parentNode.removeChild(el); });
    return HTF.foodScale.noteName(copy.textContent, words);
  }

  var last = base;

  function put(field, value) {
    if (field !== document.activeElement) field.value = value;
  }

  function apply(wanted) {
    var n = mode.clamp(wanted);
    var factor = n / base;
    var still = [];

    spans.forEach(function (span, index) {
      var item = items[index];
      if (item.node) item.node.nodeValue = item.written;
      if (n === base) {
        write(span, original[index]);
        return;
      }
      var result = HTF.foodScale.scaleAmount(original[index], factor, words);
      write(span, result.text);
      if (result.one && item.node) {
        item.node.nodeValue = HTF.foodScale.singularItem(item.written, singulars);
      }
      if (!result.scaled) {
        var row = span.closest ? span.closest('li.ingredient') : null;
        if (row) still.push(nameFor(row));
      }
    });

    /* An ingredient with no amount is as written, unless its text opens with
       a countable by-eye measure, which scales in place. The name for the
       note is taken after the text is put back. */
    bare.forEach(function (item) {
      if (item.lead) item.lead.nodeValue = item.written;
      if (n === base) return;
      var result = item.lead
        ? HTF.foodScale.scaleLeadingMeasure(item.written, factor, words)
        : { scaled: false };
      if (result.scaled) {
        item.lead.nodeValue = result.text;
      } else {
        still.push(nameFor(item.row));
      }
    });

    last = n;
    put(input, mode.box(n));
    /* The word after the box agrees with the number in it -- "1 waffle",
       "2 × 8-inch cakes", "2 litres". Portions returns null: that word is the
       markup's and never changes. */
    var said = mode.word(n);
    if (word && said !== null) word.textContent = said;

    /* "(Not scaled: salt, black pepper)" (#1088): parenthesised, no full stop,
       commas between the names. `noteName` cuts each name at its first comma,
       so no name holds one. A name is listed once. */
    var named = still.filter(function (name, index) {
      return name !== '' && still.indexOf(name) === index;
    });
    if (n !== base && named.length) {
      note.textContent = '(Not scaled: ' + named.join(', ') + ')';
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
    input.value = mode.box(last);
  }

  function step(delta) {
    return function () { apply(mode.step(last, delta)); };
  }

  input.value = mode.box(base);
  control.hidden = false;

  input.addEventListener('input', redraw);
  input.addEventListener('change', settle);
  input.addEventListener('blur', settle);
  minus.addEventListener('click', step(-1));
  plus.addEventListener('click', step(1));
})();
