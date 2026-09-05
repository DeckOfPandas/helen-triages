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
// ONE BOX, SINCE 2026-09-05, AND THE MILLILITRE BOX IS GONE. It let you type a
// total and worked the ratios backwards to a multiple. Helen, issue #721: "it's
// just baffling. Typing some numbers changes nothing, typing others changes the
// recipe but you can't see it... It is not clear how the numbers in each box
// relate to each other."
//
// EVERY WORD OF THAT WAS TRUE AND NONE OF IT WAS A BUG, which is why the answer
// was to delete the control rather than to fix it. The amounts have to stay on
// the 2.5 ml grid, so a drink can only be poured at certain multiples -- Aviation
// steps in thirds, because its smallest pour is 7.5 ml -- and therefore only
// certain TOTALS exist: 30, 60, 90, 120. Type 100 and it snapped to 90 and the
// box rewrote itself on the way out. The grid was real, correct, and completely
// invisible, and a control whose valid inputs cannot be seen or guessed reads as
// broken however right its arithmetic is. The multiple box asks the same
// question in the one form where every value you can type is a value you can
// have.
//
// WHAT WENT WITH IT: the running total (`= 90 ml`), the `or`/`ml in total`
// wording, and the `put`-guarded cross-writing that kept two boxes in step.
// `last` is still the one piece of state, but now only one control reads it.
//
// THE NUMBER TYPED IS STILL SNAPPED TO A MULTIPLE THE DRINK ALLOWS -- Helen,
// 2026-09-04: the recipe's ratios do not move. The arithmetic is HTF.scale's
// (its header has the proof); what this file adds is that the snap happens on
// the way IN, so `HTF.scale.scale` is never handed a raw typed value and the
// amounts are never approximate.
//
// THE FLOOR IS ASKED BEFORE THE SNAP, and that order is load-bearing: the snap
// clamps to the floor, so asking after it would turn "you can't make a drink
// that small" into a silent nudge and Helen's message would never appear.
//
// THE BOX HOLDS A WHOLE NUMBER, AND THAT IS THE WHOLE OF IT -- Helen,
// 2026-09-05: "logically I think we can solve the rounding/ratio issue by only
// allowing integer multiples."
//
// It does solve it, in one line: every written amount is already on the 2.5 ml
// grid, and an integer multiple of a number on a grid is on that grid. No pour
// can be asked for that a jigger cannot measure, no ratio has to move, and
// there is nothing left to snap.
//
// It also settles a run of problems that were all the same problem wearing
// different hats. The box spent an hour holding `1⅔` -- a vulgar fraction,
// parsed back by a lookup table -- purely because a drink stepping in thirds
// settled to `1.6667` and four decimals do not fit a two-character box. With
// whole recipes the value is `2`, the width Helen asked for is a real width,
// and the fraction machinery, the drink's own step and the snap all go with it.
// See `box` below for what that deletes and what deliberately stays.
//
// AN EMPTY OR HALF-TYPED BOX IS NO CHANGE, NEVER A REFUSAL, and this rule is
// the survivor of a bug that used to have two boxes to go wrong in. Helen,
// 2026-09-04: "I can't delete numbers in the target ml input field." `input`
// fires on EVERY keystroke, so deleting the `0` from `180` asked for 18 ml of a
// drink whose floor is higher than that; the refusal path then wrote the last
// working value straight back into the box being typed in, and the deletion was
// undone before the key was up.
//
// With one box the cross-writing that made that possible is gone, but the
// keystroke half is not: clearing the box to type `2` still fires `input` twice
// with nothing usable in between, and answering that with a floor message
// scolds someone for pressing Backspace. So a blank or unparseable value does
// nothing at all, and the box is tidied on the way OUT (`change` and `blur`
// both settle it) to whatever the drink is actually being poured at.
//
// `blur` AS WELL AS `change`: `change` fires only when the committed value
// differs from what the field had on focus, so clearing the box and retyping
// the same number fires only the second.
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
  var note = article.querySelector('.cocktail-scale-note');
  var list = article.querySelector('.cocktail-ingredients');
  var spans = Array.prototype.slice.call(
    article.querySelectorAll('.cocktail-amount')
  );
  if (!control || !input || !note || !spans.length) return;

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

  /* THE SPINNER AND ITS `min`/`step` ARE GONE WITH THE NUMBER INPUT -- see
     `box` below for why this is a text box now. They set the arrows to walk
     the multiples this drink allows (the Negroni in thirds, a drink with a 5 ml
     pour in whole recipes), which was good behaviour on a control wide enough
     to have arrows. At two characters there is no room for a pair, and the
     values that matter -- 2, 3, a half -- are one keystroke each. The snap that
     the step was expressing still happens, on every value, on the way in. */
  /* THE AMOUNT COLUMN WIDENS ONLY WHEN A SCALED AMOUNT NEEDS IT -- Helen,
     2026-09-05: "please reduce the space between ingredient amounts and names
     again, but increase it when an amount would otherwise linebreak due to use
     of the scaler."

     COUNTED, NOT MEASURED, and that is sound rather than lazy: `.cocktail-amount`
     is set in $font-label, which is IBM Plex MONO, so every character is the
     same width and a character count IS a width. Measuring would mean asking
     the browser for layout on every keystroke to learn something arithmetic
     already knows.

     NINE IS THE FIT. The narrow column is 5.5rem = 88px; Plex Mono advances
     0.6em and the amount is set at 0.95rem, so one character is 0.6 x 0.95 x 16
     = 9.12px and the column holds 88 / 9.12 = 9.6 of them. Nine fit, ten do
     not. "112.5 ml" is eight and "1012.5 ml" is nine, so the common scaled
     amounts stay in the narrow column and only the genuinely long ones open it.

     A DRINK CAN ALSO BE BORN WIDE. The Airmail's "Top (30-45) ml" is fourteen
     characters at x1 and has always wrapped inside its column; it now gets the
     wide pair at rest, which is the same fix arriving for the same reason. */
  var AMOUNT_FITS = 9;

  function fitAmountColumn(amounts) {
    if (!list || !list.classList) return;
    var longest = 0;
    amounts.forEach(function (a) {
      if (a.length > longest) longest = a.length;
    });
    list.classList.toggle('cocktail-ingredients--wide-amounts',
                          longest > AMOUNT_FITS);
  }

  var last = 1;
  input.value = box(last);
  fitAmountColumn(original);
  control.hidden = false;

  /* WHOLE RECIPES ONLY, SINCE 2026-09-05 -- Helen: "logically I think we can
     solve the rounding/ratio issue by only allowing integer multiples."

     It solves it outright, and the proof is one line: every written amount is
     already on the 2.5 ml grid, and an integer multiple of a number on a grid
     is on that grid. So no drink can be asked for a pour it cannot measure, no
     ratio ever has to move, and there is nothing left to snap.

     WHAT THAT DELETES. `snapMultiple` and the drink's own step went, and with
     them: a Negroni stepping in thirds, `1.5` silently becoming `1.6667`, and
     the vulgar-fraction pair (`multipleText` writing `1⅔`, `readMultiple`
     reading it back) that existed only because the box had to display a third.
     Two characters is now a real width for a real value rather than a width the
     display had to be bent to fit -- which was the last thing propping that
     machinery up.

     THE FLOOR CANNOT FIRE EITHER, and that was checked against the data rather
     than assumed: no drink in the collection has a written millilitre pour
     under MIN_POUR, and scaling UP can never take an amount below where it
     started. `refuse` stays anyway, because it costs nothing and the day a
     drink is ingested with a 1 ml pour it will be telling the truth.

     THE ARITHMETIC ITSELF IS UNTOUCHED. HTF.scale keeps its step, its snap and
     its fractions -- the shopping list's own scaler still uses them, and this
     is the drink page choosing a simpler question to ask, not the library
     losing the ability to answer a harder one. */
  function box(n) {
    return String(n);
  }

  /* THE BOX IS NEVER WRITTEN TO WHILE IT HAS FOCUS -- see the header. Typing is
     the one thing on this control the script cannot redo, so it wins; with the
     millilitre box gone there is no second field to carry the state meanwhile,
     which is why a refusal now simply leaves the typed text alone until the
     reader leaves the field and `settle` tidies it. */
  function put(field, value) {
    if (field !== document.activeElement) field.value = value;
  }

  /** The ingredient's own name, for the note. */
  function nameFor(index) {
    var span = spans[index];
    var item = span && span.closest ? span.closest('.cocktail-ingredient') : null;
    var name = item ? item.querySelector('.cocktail-item-name') : null;
    return name ? name.textContent.trim() : 'an ingredient';
  }

  /* THE BOX SNAPS BACK to the last multiple that worked -- through `put`, so
     the box being typed in is left alone. That was the deletion bug (header),
     and it is the reason a refusal mid-type shows a message without yanking the
     text out from under the cursor. */
  function refuse(verdict) {
    put(input, box(last));
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
    /* ROUNDED TO A WHOLE RECIPE, AND NEVER BELOW ONE. `1.5` becomes 2 rather
       than being refused: someone typing a decimal into a box this size has
       asked for "about that much", and the nearest whole recipe is the answer
       to it. `settle` writes the number back on the way out, so the rounding is
       shown rather than done behind the reader.

       ONE IS THE FLOOR BECAUSE HALF A DRINK IS NOT A THING THIS PAGE OFFERS --
       and, usefully, because it is also what makes the 2.5 ml grid safe (see
       `box` above). Typing 0 never reaches here at all; `pending` treats a
       non-positive value as a keystroke on the way somewhere. */
    var n = Math.max(1, Math.round(wanted));

    var verdict = HTF.scale.scale(original, n);
    if (!verdict.ok) {
      refuse(verdict);
      return;
    }

    last = n;
    note.hidden = true;
    spans.forEach(function (span, index) {
      span.textContent = verdict.amounts[index];
    });
    fitAmountColumn(verdict.amounts);
    put(input, box(last));
  }

  /* NOTHING TYPED YET, NOTHING A NUMBER CAN BE READ OUT OF, OR A NUMBER NOBODY
     IS ASKING FOR.

     THE `<= 0` CLAUSE IS THE 2-CHARACTER BOX'S OWN VERSION OF THE BACKSPACE BUG
     -- 2026-09-05. Zero is finite and parses, so it used to reach `apply`, get
     refused by the floor, and flash "can't go below ×⅓" -- on the way to `0.5`,
     because `0` is the first keystroke of it. Helen, #721: the warning "changes
     on single character typing or deletion".
     Nobody ever wants zero of a drink, and the box's `min` is the drink's own
     floor, which is always above it. So a non-positive value is never a request;
     it is always a keystroke on the way somewhere, and the page holds still for
     it exactly as it does for the empty string. */
  function pending(box) {
    var n = parseFloat(box.value);
    return box.value.trim() === '' || !isFinite(n) || n <= 0;
  }

  function redraw() {
    /* AN EMPTY OR HALF-TYPED BOX IS SOMEONE MID-TYPE, NOT A REFUSAL. `input`
       fires on every keystroke, and clearing the field to type `2` would
       otherwise flash the floor message and put the old number back under the
       cursor -- the bug Helen hit in the millilitre box that used to sit beside
       this one. Do nothing until there is a number to act on. */
    if (pending(input)) return;
    apply(parseFloat(input.value));
  }

  input.addEventListener('input', redraw);

  /* THE BOX IS TIDIED ON THE WAY OUT, and this is where `put`'s guard is
     deliberately NOT used: the whole job here is to write into the field that
     was just being typed in. A refused or half-typed value leaves the reader's
     own text on screen while the drink is poured at `last`, and this replaces
     it with what was actually made.

     A BLANK BOX SETTLES RATHER THAN REFUSING -- Helen, 2026-09-04. Someone who
     clears the box and clicks away has asked nothing, so the answer is what the
     drink is currently poured at, not a floor message about the empty string.

     `blur` AS WELL AS `change`, because `change` fires only when the committed
     value actually differs from what the field had on focus -- clear the box,
     type the same number back, click away, and only `blur` runs. */
  function settle() {
    input.value = box(last);
  }

  input.addEventListener('change', settle);
  input.addEventListener('blur', settle);
})();
