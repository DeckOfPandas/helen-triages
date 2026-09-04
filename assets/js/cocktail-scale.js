// cocktail-scale.js
// =============================================================================
// THE SCALER'S DOM HALF — read the amounts, write them back at a multiple.
// =============================================================================
// GitHub issue #545, step one. The arithmetic is assets/js/scale.js (HTF.scale)
// and this file holds none of it, the same split cocktail-index.js runs against
// shopping-list.js and filters.js against filter-state.js: the maths is the
// part worth testing without a browser, and tests/js/scale.test.js is where it
// is tested.
//
// THE ORIGINAL AMOUNTS ARE STASHED ON FIRST RUN, in `data-amount`, and every
// redraw scales from THOSE rather than from what is on screen. Scaling the
// displayed text would compound: ×2 then ×1 would print four times the recipe,
// because the second pass would multiply a number the first pass had already
// doubled. It also means the floor is computed once, from the recipe as
// written, and cannot drift as the reader plays with the control.
//
// THE CONTROL SHIPS `hidden` AND THIS REVEALS IT -- the rule every JS-dependent
// control on both sites follows (`.btn-shortlist`, `.btn-print`, and
// _layouts/recipe.html's own sentence: "a control that silently fails is worse
// than no control"). A number box that renumbers nothing is exactly such a
// control, so the markup assumes the script did not run and this is the proof
// that it did. CSS cannot ask that question.
//
// A REFUSAL PUTS THE OLD VALUE BACK. Helen, 2026-09-04: "say you can't go below
// X ml if any ingredient wants to go below 2.5 ml." So the input reverts to the
// last multiple that worked and the note says what the limit is and which
// ingredient set it -- named from the page, since HTF.scale deals in indexes
// and knows nothing about markup.
//
// TWO BOXES, ONE STATE, AND NEITHER IS THE MASTER -- Helen, 2026-09-04, step
// two of #545: "please add total ml, either set by your input box, or
// user-entered number of ml." So there is a multiple box and a millilitre box,
// and `last` (the multiple that is actually on screen) is the single thing they
// both write to and both read back from. Whichever one you type in, the other
// is redrawn from that number rather than being left holding a stale figure --
// which is the whole failure mode of two inputs describing one quantity.
//
// THE MILLILITRE BOX IS REFUSED BY EXACTLY THE SAME PATH as the multiple box,
// because it goes through the same HTF.scale.scale(): a target is turned into a
// multiple and then handed over, so there is one floor, one message, and no
// second opinion about what this drink can be poured at. A target the drink
// cannot reach snaps both boxes back to the last pair that worked.
//
// `make it` NEEDS NOTHING FROM THIS FILE. That state is one class and a
// stylesheet (`.cocktail.is-making`, _sass/cocktails/_cocktail.scss); it
// changes the amount's SIZE and never its text, so scaled amounts are already
// scaled in both states and there is nothing here to keep in step.
// =============================================================================
(function () {
  'use strict';

  var HTF = window.HTF;
  if (!HTF || !HTF.scale) return;

  var article = document.querySelector('article.cocktail');
  if (!article) return;

  var control = article.querySelector('.cocktail-scale-controls');
  var input = control && control.querySelector('.cocktail-scale-multiple');
  var target = control && control.querySelector('.cocktail-scale-target');
  var totalValue = control && control.querySelector('.cocktail-scale-total-value');
  var note = article.querySelector('.cocktail-scale-note');
  var spans = Array.prototype.slice.call(
    article.querySelectorAll('.cocktail-amount')
  );
  if (!control || !input || !target || !totalValue || !note || !spans.length) return;

  /* THE AMOUNT SPANS ARE THE INDEX, NOT THE INGREDIENT LIST. An ingredient with
     no `amount` renders no span at all (the layout gates on `item.amount`), so
     the two lists are different lengths on any drink with such an entry. Every
     index in this file -- HTF.scale's `offender` included -- is an index into
     these spans, and a name is read from the span's OWN list item rather than
     looked up by position. */
  var original = spans.map(function (span) {
    if (!span.hasAttribute('data-amount')) {
      span.setAttribute('data-amount', span.textContent.trim());
    }
    return span.getAttribute('data-amount');
  });

  /* THE SPINNER CANNOT GO BELOW THE FLOOR. The refusal below is still the real
     guard -- the field is typeable -- but a `min` the browser enforces means
     the arrows alone can never produce a message, which is the difference
     between a control that explains itself and one that scolds you. */
  var floor = HTF.scale.floorMultiple(original);
  input.setAttribute('min', String(floor));
  input.setAttribute('step', String(HTF.scale.MULTIPLE_STEP));

  var last = Math.max(1, floor);
  input.value = String(last);
  control.hidden = false;

  /* THE FORMAT IS THE AMOUNTS' OWN -- "90 ml", "112.5 ml" -- because it is the
     same kind of figure, and HTF.scale prints the number for both. */
  function showTotal(multiple) {
    var ml = HTF.scale.totalMl(original, multiple);
    totalValue.textContent = ml + ' ml';
    /* THE OTHER BOX IS REDRAWN, NEVER LEFT STALE. `document.activeElement`
       keeps this from rewriting the field under someone's cursor mid-type:
       typing `18` on the way to `180` would otherwise be answered with the
       total 18 ml produces, in the box being typed into. */
    if (target !== document.activeElement) target.value = String(ml);
  }

  showTotal(last);

  /** The ingredient's own name, for the note. */
  function nameFor(index) {
    var span = spans[index];
    var item = span && span.closest ? span.closest('.cocktail-ingredient') : null;
    var name = item ? item.querySelector('.cocktail-item-name') : null;
    return name ? name.textContent.trim() : 'an ingredient';
  }

  /* BOTH BOXES SNAP BACK, not just the one that was typed in: they describe one
     quantity, so leaving the other showing a total the page is not rendering
     would be the page saying two things at once. */
  function refuse(verdict) {
    input.value = String(last);
    target.value = String(HTF.scale.totalMl(original, last));
    var who = verdict.offender === null
      ? 'an ingredient'
      : 'the ' + nameFor(verdict.offender);
    note.textContent = 'can’t go below ×' + verdict.floor +
      ' (' + verdict.floorTotalMl + ' ml): ' + who +
      ' would be under ' + HTF.scale.MIN_POUR + ' ml';
    note.hidden = false;
  }

  /** Render the drink at a multiple, or refuse it. */
  function apply(wanted) {
    var verdict = HTF.scale.scale(original, wanted);
    if (!verdict.ok) {
      refuse(verdict);
      return;
    }

    last = wanted;
    note.hidden = true;
    spans.forEach(function (span, index) {
      span.textContent = verdict.amounts[index];
    });
    showTotal(wanted);
    if (input !== document.activeElement) input.value = String(wanted);
  }

  function redraw() {
    /* AN EMPTY BOX IS SOMEONE MID-TYPE, NOT A REFUSAL. `input` fires on every
       keystroke, and clearing the field to type `2` would otherwise flash the
       floor message and put the old number back under the cursor. */
    if (input.value.trim() === '') return;
    apply(parseFloat(input.value));
  }

  /* A TARGET IS EXACT AND IS NOT SNAPPED TO THE HALF STEP -- HTF.scale's own
     header. 180 ml of a 90 ml drink is ×2; 100 ml of the Negroni is ×1.212,
     and the amounts it produces are still rounded to the 2.5 ml grid, so the
     poured total may land a little either side of what was typed. That is the
     honest answer: a jigger has marks. */
  function retarget() {
    if (target.value.trim() === '') return;
    var wanted = HTF.scale.multipleForTotal(original, parseFloat(target.value));
    /* NOTHING TO SCALE, so there is no answer rather than a wrong one -- a
       drink of nothing but dashes has no total for a target to divide into. */
    if (wanted === null) return;
    apply(wanted);
  }

  input.addEventListener('input', redraw);
  target.addEventListener('input', retarget);

  /* THE BOX YOU LEAVE IS TIDIED ON THE WAY OUT. Both handlers deliberately do
     not write into the field being typed in, so a target of 100 ml leaves `100`
     on screen while the drink is poured at 102.5; `change` fires when the field
     is committed, and redrawing then replaces it with what was actually made. */
  target.addEventListener('change', function () { showTotal(last); });
  input.addEventListener('change', function () { input.value = String(last); });
})();
