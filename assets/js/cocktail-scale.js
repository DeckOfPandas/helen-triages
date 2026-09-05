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
// EVERY NUMBER TYPED IN EITHER BOX IS SNAPPED TO A MULTIPLE THE DRINK ALLOWS --
// Helen, 2026-09-04: "recipe states single-order amount, target ml works the
// ratios out backwards within reason but then updates the target ml the user has
// entered to something more sane, that is, based on 2.5-ml increments." The
// arithmetic is HTF.scale's (its header has the proof); what this file adds is
// that the snap happens on the way IN, so `HTF.scale.scale` is never handed a
// raw typed value and the amounts are never approximate.
//
// THE FLOOR IS ASKED BEFORE THE SNAP, and that order is load-bearing: the snap
// clamps to the floor, so asking after it would turn "you can't make a drink
// that small" into a silent nudge and Helen's message would never appear.
//
// THE BOX SHOWS A DECIMAL AND THE TOTAL SHOWS THE FRACTION. `type="number"`
// cannot hold `⅓`, and `0.3333` is not a thing anyone thinks in, so the box
// carries the number the browser needs and the total line -- which is already
// `aria-live` -- says `30 ml, ×⅓`. Only when the multiple is not a whole one:
// `×2` beside a box reading 2 would be the page saying one thing twice.
//
// A FIELD THAT HAS FOCUS IS NEVER WRITTEN TO -- Helen, 2026-09-04: "I can't
// delete numbers in the target ml input field. I can add numbers, then
// increasing the number of servings causes the numbers in the target field to
// update." Both halves were the same bug seen from two sides. `input` fires on
// EVERY keystroke, so deleting the `0` from `180` asked for 18 ml of a drink
// whose floor is higher than that; the refusal path then wrote the last working
// total straight back into the box being typed in, and the deletion was undone
// before the key was up. Two of the three writers already checked
// `document.activeElement` and the third did not, which is exactly why the
// check is now ONE function (`put`) that every writer goes through -- a guard
// spelled three times is a guard with two of them missing.
//
// SO: while a box is being typed in, the OTHER box is what gets redrawn, and
// an empty or unparseable value is NO CHANGE rather than a refusal -- there is
// nothing to scale to yet, and answering a half-typed number with a floor
// message scolds someone for pressing Backspace. The box is tidied on the way
// OUT instead (`change` and `blur` both settle it), and a box left blank
// settles to what the drink is actually being poured at rather than refusing.
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
  /* OPTIONAL, deliberately: the caveat line is Helen's to word (see the layout),
     and a page rendered before she has written it must still work. */
  var caveat = article.querySelector('.cocktail-scale-caveat');
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

  /* THE SPINNER WALKS THE MULTIPLES THIS DRINK ALLOWS, and nothing else --
     Helen, 2026-09-04: the ratios do not move, so the step is the drink's own
     (HTF.scale's header has the arithmetic). The Negroni steps in thirds, a
     drink with a 5 ml pour in it steps in whole recipes. `min` is the floor for
     the same reason it always was: the arrows alone should never be able to
     produce a message.

     `step` AND `min` ARE ROUNDED FOR THE ATTRIBUTE and nowhere else. A ⅓ step
     is 0.3333333333333333, which is not a thing to put in HTML; the browser's
     arrows walk approximately and every value that comes back is snapped
     exactly, so the approximation never reaches the amounts. */
  var step = HTF.scale.allowedStep(original);
  var floor = HTF.scale.floorMultiple(original);
  input.setAttribute('min', box(floor));
  input.setAttribute('step', box(step.value));

  var last = HTF.scale.snapMultiple(original, 1).multiple;
  input.value = box(last);
  control.hidden = false;
  if (caveat) caveat.hidden = false;

  /* A NUMBER FIT FOR A `type="number"` BOX. Four decimals is finer than any
     step this collection produces (the smallest is 1/36) and short enough to
     read; the exact value lives in `last`, never in the box, so nothing is lost
     by shortening it here. */
  function box(n) {
    return String(Math.round(n * 10000) / 10000);
  }

  /* THE ONE DOOR EVERY WRITE TO AN INPUT GOES THROUGH -- see the header. The
     field with focus is the one a person is typing in, and typing is the only
     thing on this control that cannot be redone by the script; so it wins,
     always, and the other box carries the state instead. */
  function put(field, value) {
    if (field !== document.activeElement) field.value = value;
  }

  /* THE FORMAT IS THE AMOUNTS' OWN -- "90 ml", "112.5 ml" -- because it is the
     same kind of figure, and HTF.scale prints the number for both.

     THE MULTIPLE IS SAID OUT LOUD WHEN IT IS NOT A WHOLE ONE, because `0.3333`
     in the box is not a thing anybody thinks in and `⅓` is. It rides on the
     total rather than in new markup: this line is already `aria-live`, so a
     screen reader hears "30 ml, ×⅓" as one answer to one action. */
  function showTotal(multiple) {
    var ml = HTF.scale.totalMl(original, multiple);
    /* ONLY WHEN IT IS NOT A WHOLE NUMBER. `×2` beside a box already reading 2
       is the page saying one thing twice; `×⅓` beside a box reading 0.3333 is
       the page saying the thing the box cannot. */
    var text = HTF.scale.multipleText(original, multiple);
    var fraction = /^[0-9]+$/.test(text) ? '' : ', ×' + text;
    totalValue.textContent = ml + ' ml' + fraction;
    /* THE OTHER BOX IS REDRAWN, NEVER LEFT STALE -- unless it is the one being
       typed in: `18` on the way to `180` would otherwise be answered with the
       total 18 ml produces, in the box under the cursor. */
    put(target, String(ml));
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
     would be the page saying two things at once. THROUGH `put`, so the box
     being typed in is not one of them -- this was the deletion bug (header). */
  function refuse(verdict) {
    put(input, box(last));
    put(target, String(HTF.scale.totalMl(original, last)));
    var who = verdict.offender === null
      ? 'an ingredient'
      : 'the ' + nameFor(verdict.offender);
    note.textContent = 'can’t go below ×' + verdict.floorText +
      ' (' + verdict.floorTotalMl + ' ml): ' + who +
      ' would be under ' + HTF.scale.MIN_POUR + ' ml';
    note.hidden = false;
  }

  /**
   * Render the drink at the nearest multiple it can actually be poured at.
   *
   * EVERYTHING GOES THROUGH THE SNAP -- Helen, 2026-09-04: the recipe's ratios
   * are fixed and the number the reader typed is the thing that moves. So this
   * never hands `HTF.scale.scale` a raw typed value; it snaps first, and the
   * refusal below is only ever the floor.
   */
  function apply(wanted) {
    /* THE FLOOR IS ASKED OF THE RAW NUMBER, BEFORE THE SNAP, because the snap
       clamps to the floor and would turn "you can't make a drink that small"
       into a silent nudge. HTF.scale.scale answers `why: 'floor'` for exactly
       this and nothing else -- see its own note on the order. */
    var asked = HTF.scale.scale(original, wanted);
    if (!asked.ok && asked.why === 'floor') {
      refuse(asked);
      return;
    }

    var snapped = HTF.scale.snapMultiple(original, wanted);
    if (snapped === null) return;

    var verdict = HTF.scale.scale(original, snapped.multiple);
    if (!verdict.ok) {
      refuse(verdict);
      return;
    }

    last = snapped.multiple;
    note.hidden = true;
    spans.forEach(function (span, index) {
      span.textContent = verdict.amounts[index];
    });
    showTotal(last);
    put(input, box(last));
  }

  /** Nothing typed yet, or nothing a number can be read out of. */
  function pending(box) {
    return box.value.trim() === '' || !isFinite(parseFloat(box.value));
  }

  function redraw() {
    /* AN EMPTY OR HALF-TYPED BOX IS SOMEONE MID-TYPE, NOT A REFUSAL. `input`
       fires on every keystroke, and clearing the field to type `2` would
       otherwise flash the floor message and put the old number back under the
       cursor -- which is the multiple box's version of the bug Helen hit in the
       target box. Do nothing until there is a number to act on. */
    if (pending(input)) return;
    apply(parseFloat(input.value));
  }

  /* A TARGET IS WORKED BACKWARDS AND THEN MADE SANE -- Helen, 2026-09-04: it
     "works the ratios out backwards within reason but then updates the target
     ml the user has entered to something more sane, that is, based on 2.5-ml
     increments." So 100 ml of a 90 ml drink is ×1.111 on paper, snaps to ×1,
     and the box is rewritten to 90 on the way out. The number that moves is
     the one the reader typed, never the recipe's ratios. */
  function retarget() {
    /* SAME RULE AS THE MULTIPLE BOX, and this is the field Helen could not
       delete in: while the box is empty or half-typed there is no target to
       scale to, so the page holds still. */
    if (pending(target)) return;
    var wanted = HTF.scale.multipleForTotal(original, parseFloat(target.value));
    /* NOTHING TO SCALE, so there is no answer rather than a wrong one -- a
       drink of nothing but dashes has no total for a target to divide into. */
    if (wanted === null) return;
    apply(wanted);
  }

  input.addEventListener('input', redraw);
  target.addEventListener('input', retarget);

  /* THE BOX YOU LEAVE IS TIDIED ON THE WAY OUT, and this is where `put`'s guard
     is deliberately NOT used: the whole job here is to write into the field
     that was just being typed in. `apply` never writes there, so a target of
     100 ml leaves `100` on screen while the drink is poured at 102.5, and this
     replaces it with what was actually made.

     A BLANK BOX SETTLES RATHER THAN REFUSING -- Helen, 2026-09-04. Someone who
     clears the target and clicks away has asked nothing, so the answer is the
     total the drink is currently poured at, not a floor message about the
     empty string. Both fields are rewritten from `last` because `last` is the
     one state they both describe.

     `blur` AS WELL AS `change`, because `change` fires only when the committed
     value actually differs from what the field had on focus -- clear the box,
     type the same number back, click away, and only `blur` runs. */
  function settle() {
    input.value = box(last);
    target.value = String(HTF.scale.totalMl(original, last));
  }

  target.addEventListener('change', settle);
  target.addEventListener('blur', settle);
  input.addEventListener('change', settle);
  input.addEventListener('blur', settle);
})();
