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
// scale: an amount with no count in it ("a few handfuls", "some") and an
// ingredient with no amount at all ("salt, to taste"). When the portions
// differ from the recipe's own, both kinds are listed by name under the
// control; at the recipe's own count the note is hidden, because nothing has
// moved.
//
// A HANDFUL SCALES, IN HALF STEPS -- #1125. "1 handful" for three times the
// people is "3 handfuls", for half as many again "1½ handfuls"; seven for six
// used to come out as 1.17 and is now still 1. And a row with NO
// amount whose text opens with such a measure scales too: Helen's own example
// is `item: "a handful of fresh parsley"`, which becomes "3 handfuls of fresh
// parsley". That is the one place this file writes outside an amount span --
// see `leadFor` below. The rounding is HTF.foodScale's, in one function.
// HELEN'S WORDS SINCE #1088, 2026-09-20 -- "(Not scaled: salt, black pepper;
// olive oil)", settled as commas throughout. See `apply` below.
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

  /* PORTIONS, OR THE THING MADE -- #1286. A `makes:` recipe's control carries
     `data-made`, the build's reading of that line as JSON, and the box then
     counts waffles (or millilitres, or 8-inch cakes) and never portions --
     Helen: "Never tell me how many cookies are in a portion!!!" It steps in
     WHOLE RECIPES and shows what that many make: 5 waffles, 10, 15. Everything
     that differs between the two is in the MODE, which is HTF.foodScale's:
     this file asks it what a press of plus means and what the box should
     say, and holds no arithmetic for either. A `data-made` that cannot be
     read leaves the control hidden, which is the rule for any control here
     that cannot work. */
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
    /* `data-whole-recipes`: a `makes:` recipe with no count to show keeps
       the word "portions" and steps 4, 8, 12 -- whole recipes, like every
       other `makes:` recipe. A `serves:` recipe has no such mark. */
    if (people > 0) {
      mode = HTF.foodScale.portionsMode(people,
        input.hasAttribute('data-whole-recipes'),
        input.hasAttribute('data-half-recipe'));
    }
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

  /* THE TWO WORD LISTS ARE THE BUILD'S, #1125 -- `data-half-step-measures` is
     _data/food/scaling.yml's `half_step_measures` (a handful, a pinch: measures
     that scale in half steps) and `data-trailing` is ingredient_words.yml's
     `trailing_phrases` ("to taste"). _layouts/recipe.html joins each with `|`
     onto the control. Absent, both are empty and the scaler behaves as it did
     before the issue. */
  function listFrom(attribute) {
    return (control.getAttribute(attribute) || '').split('|')
      .map(function (word) { return word.trim(); })
      .filter(function (word) { return word !== ''; });
  }

  var words = {
    halfStep: listFrom('data-half-step-measures'),
    trailing: listFrom('data-trailing')
  };

  /* A ROW WITH NO AMOUNT, AND THE TEXT NODE ITS WORDS START IN. "a handful of
     fresh parsley" has no span to rewrite: the measure is the opening of the
     item's own text. `leadFor` finds the row's FIRST text, and only if it is
     a bare text node directly inside the <li> -- an item that opens with a
     link or any other element has no lead and is simply not scaled. The
     node's original value is stashed here, once, for the same reason the
     amounts are: every redraw scales from what the recipe wrote.

     ONLY THAT ONE NODE IS EVER WRITTEN, so a link, an emphasis or the
     annotation later in the row is never touched. */
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
      if (n === base) {
        write(span, original[index]);
        return;
      }
      var result = HTF.foodScale.scaleAmount(original[index], factor, words);
      write(span, result.text);
      if (!result.scaled) {
        var row = span.closest ? span.closest('li.ingredient') : null;
        if (row) still.push(nameFor(row));
      }
    });

    /* An ingredient with no amount is as written whatever the box says --
       UNLESS its text opens with a countable by-eye measure ("a handful of",
       "pinch of"), which scales in place. The name for the note is taken
       after the text is put back, so it is always the recipe's own words. */
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

    /* HELEN'S LINE, #1088, 2026-09-20: "(Not scaled: salt, black pepper;
       olive oil)". Parenthesised, no full stop, and COMMAS between the names
       -- her example carried one of each and she settled it as commas
       throughout when asked, so the semicolon this used to join with is gone
       along with the trailing period.

       A NAME CONTAINING A COMMA WOULD READ AS TWO. That is the one thing the
       semicolon bought, and it was given up knowingly. SINCE #1125 NO NAME
       HAS ONE: `noteName` cuts each at its first comma, which is also what
       turns "paprika, unless feeding Helen" into the "paprika" her line
       wants. (This comment used to say the names came from
       `.recipe-item-name` and so never held a comma. No such class exists;
       they were the whole `item:` text, and dozens of published lines had one
       -- "salt, to taste" among them.)

       A NAME IS LISTED ONCE. Two rows can cut down to the same ingredient --
       "salt" in the cake and "salt" in the icing -- and saying it twice says
       nothing more. */
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
