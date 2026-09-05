// =============================================================================
// Tests for assets/js/scale.js — GitHub issue #545's recipe scaler.
//
//   node --test tests/js/*.test.js
//
// RUN THROUGH THE STUB-DOM HARNESS RATHER THAN REQUIRED DIRECTLY, unlike
// shopping-list.test.js, and the difference is the point: this module has a
// DEPENDENCY, and the browser resolves it through `HTF.shoppingList` rather
// than through require(). Loading both files into a stub page the way
// _layouts/cocktail.html loads them tests the wiring as well as the maths —
// require() alone would pass happily on a page where scale.js was loaded first
// and `HTF.scale` was therefore never defined.
//
// WHAT THESE GUARD. Every rule below is Helen's, 2026-09-04, and each is a
// decision rather than an implementation detail: multiples of the recipe as
// written, the 2.5 ml grid, the floor that refuses instead of rounding, and
// the amounts that are not quantities and must survive untouched.
// =============================================================================
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { load } = require('./stub-dom.js');

/** The page's own load order, which is what makes HTF.scale exist. */
const scaler = load([
  'assets/js/shopping-list.js',
  'assets/js/scale.js'
]).HTF.scale;

/** The negroni, as written — the drink this was built against. */
const NEGRONI = ['30 ml', '22.5 ml', '30 ml', '2 drops'];

test('the module is on HTF, the way the drink page reaches it', () => {
  assert.strictEqual(typeof scaler.scale, 'function');
  assert.strictEqual(scaler.MIN_POUR, 2.5);
});

// --- volumes ------------------------------------------------------------------

test('a multiple that would move a ratio is REFUSED, not rounded', () => {
  // 22.5 × 1.5 is 33.75, which no jigger pours, and the old code printed 35 --
  // so the Campari grew by 4% of itself against the gin. Helen, 2026-09-04:
  // "that isn't as important as not poisoning my friends." ×1.5 is not a whole
  // number of this drink's own step (⅓), so it is refused outright.
  const out = scaler.scale(NEGRONI, 1.5);
  assert.strictEqual(out.ok, false);
  assert.strictEqual(out.why, 'grid');
  assert.strictEqual(out.amounts, undefined);
});

test('an allowed multiple is exact in every amount', () => {
  // ×⅔ of 30 / 22.5 / 30 is 20 / 15 / 20 -- every one on the 2.5 grid, every
  // ratio untouched, nothing rounded anywhere.
  const out = scaler.scale(NEGRONI, 2 / 3);
  assert.strictEqual(out.ok, true);
  assert.strictEqual(out.text, '⅔');
  assert.deepStrictEqual(out.amounts.slice(0, 3), ['20 ml', '15 ml', '20 ml']);
});

test('a whole number of millilitres prints without a decimal point', () => {
  const out = scaler.scale(['20 ml', '15 ml'], 2);
  assert.deepStrictEqual(out.amounts, ['40 ml', '30 ml']);
});

test('one decimal is kept when the grid lands on a half', () => {
  const out = scaler.scale(['75 ml'], 0.5);
  assert.deepStrictEqual(out.amounts, ['37.5 ml']);
});

test('the recipe as written comes back unchanged at ×1', () => {
  const out = scaler.scale(NEGRONI, 1);
  assert.deepStrictEqual(out.amounts, NEGRONI);
});

// --- counts -------------------------------------------------------------------

test('a count multiplies and re-pluralises with the shopping list’s own helper', () => {
  const out = scaler.scale(['1 dash', '3 drops', '8 leaves'], 3);
  // `3 dashs` is the bug unitLabel exists to prevent, and this is the second
  // caller relying on it rather than a second place that pluralises.
  assert.deepStrictEqual(out.amounts, ['3 dashes', '9 drops', '24 leaves']);
});

test('a count that comes back to one loses its plural', () => {
  const out = scaler.scale(['2 dashes'], 0.5);
  assert.deepStrictEqual(out.amounts, ['1 dash']);
});

test('a bare count keeps its bare number, and grams stay grams', () => {
  // `7.5` with no unit is real data (three entries), and so is `25 g`. Neither
  // is a volume, so neither is rounded to the pour grid or asked about 2.5 ml.
  const out = scaler.scale(['1', '25 g'], 2);
  assert.deepStrictEqual(out.amounts, ['2', '50 g']);
});

// --- the amounts that are not quantities --------------------------------------

test('an amount that is not a quantity passes through untouched', () => {
  const out = scaler.scale(['to top', 'to rinse', '30 ml'], 4);
  assert.deepStrictEqual(out.amounts, ['to top', 'to rinse', '120 ml']);
});

// --- ranges -------------------------------------------------------------------

test('a range keeps its shape, with both ends scaled', () => {
  const out = scaler.scale(['20–30 ml', '1 to 2 dashes'], 2);
  assert.deepStrictEqual(out.amounts, ['40–60 ml', '2 to 4 dashes']);
});

test('a unit that merely begins with "to" is not read as a range', () => {
  // Without the spaces around the `to` alternative, "5 tonic" parses as a
  // range from 5 to "nic".
  const out = scaler.scale(['5 tonic'], 2);
  assert.deepStrictEqual(out.amounts, ['10 tonics']);
});

// --- the floor ----------------------------------------------------------------

test('the floor is the drink’s own smallest allowed multiple', () => {
  // 50 and 5 ml are 100 and 10 half-ml units, gcd 10, so the step is 5/10 =
  // ×0.5 -- and at ×0.5 the 5 ml rinse is exactly 2.5 ml. The floor and the
  // step are the same number here, which the header says is the usual case.
  assert.strictEqual(scaler.floorMultiple(['50 ml', '5 ml']), 0.5);
  assert.strictEqual(scaler.allowedStep(['50 ml', '5 ml']).value, 0.5);
  // Nothing volumetric: nothing can go under 2.5 ml, so the fallback step is
  // the floor -- halves, as this control offered before the grid existed.
  assert.strictEqual(scaler.floorMultiple(['2 dashes', 'to top']), 0.5);
});

test('the allowed step is 2.5 ml over the gcd of the amounts', () => {
  // The header's own two worked examples. 30/22.5/30 is 60/45/60 half-ml units
  // with gcd 15, so the step is 5/15 = ⅓; 45/22.5/15/5 is 90/45/30/10 with
  // gcd 5, so the step is 5/5 = 1 and that drink has no half of itself.
  // Field by field, not deepStrictEqual: this module is loaded through the
  // stub-dom harness, so the objects it returns carry the SANDBOX's
  // Object.prototype and `deepStrictEqual` fails them on the prototype alone.
  const third = scaler.allowedStep(NEGRONI);
  assert.strictEqual(third.n, 1);
  assert.strictEqual(third.d, 3);
  assert.strictEqual(third.value, 1 / 3);
  const whole = scaler.allowedStep(['45 ml', '22.5 ml', '15 ml', '5 ml']);
  assert.strictEqual(whole.n, 1);
  assert.strictEqual(whole.d, 1);
  assert.strictEqual(whole.value, 1);
});

test('an amount that was never on the grid is left out of it, and not rounded', () => {
  // cobra-effect's 22.75 ml is the only one in the collection. It cannot be
  // kept exact by any multiple, so it does not get to set the step -- and it is
  // multiplied rather than rounded, because rounding it would move a ratio.
  const cobra = ['30 ml', '30 ml', '22.75 ml', '15 ml', '15 ml'];
  assert.strictEqual(scaler.allowedStep(cobra).d, 6);      // gcd of the other four
  assert.deepStrictEqual(scaler.scale(cobra, 2).amounts,
    ['60 ml', '60 ml', '45.5 ml', '30 ml', '30 ml']);
  // And the recipe as written still prints as written.
  assert.deepStrictEqual(scaler.scale(cobra, 1).amounts, cobra);
});

test('a multiple under the floor is REFUSED, and says how far down it can go', () => {
  // Helen, 2026-09-04: "say you can't go below X ml if any ingredient wants to
  // go below 2.5 ml". A refusal, not a silent round up to 2.5.
  const out = scaler.scale(['50 ml', '5 ml'], 0.25);
  assert.strictEqual(out.ok, false);
  assert.strictEqual(out.floor, 0.5);
  assert.strictEqual(out.offender, 1);          // the 5 ml is what stops it
  assert.strictEqual(out.floorTotalMl, 27.5);   // 25 + 2.5, as poured
  assert.strictEqual(out.amounts, undefined);   // nothing to show
});

test('the floor is capped at ×1, so a recipe as written is never refused', () => {
  // Ten drinks are written with a 2.5 ml ingredient and one could be written
  // with less. That is Helen's recipe, not an error for this file to report.
  assert.strictEqual(scaler.floorMultiple(['30 ml', '1 ml']), 1);
  const asWritten = scaler.scale(['30 ml', '1 ml'], 1);
  assert.strictEqual(asWritten.ok, true);
  assert.deepStrictEqual(asWritten.amounts, ['30 ml', '1 ml']);
  assert.strictEqual(scaler.scale(['30 ml', '1 ml'], 0.5).ok, false);
});

test('×1 is allowed on every drink, by construction', () => {
  // Every millilitre amount in the collection is a whole number of 2.5 ml, so 5
  // divides the gcd, so ×1 is always a whole number of steps. Spot-checked here
  // across several of the step sizes the collection actually produces.
  [NEGRONI, ['45 ml', '22.5 ml', '15 ml', '5 ml'], ['52.5 ml', '15 ml', '7.5 ml'],
   ['60 ml', '30 ml'], ['90 ml']].forEach((drink) => {
    assert.strictEqual(scaler.scale(drink, 1).ok, true, String(drink));
  });
});

test('a multiple that is not a number at all is refused rather than printed', () => {
  ['', null, undefined, 'lots', 0, -2].forEach((bad) => {
    assert.strictEqual(scaler.scale(NEGRONI, bad).ok, false, String(bad));
  });
});

// --- the total ----------------------------------------------------------------

test('the total is the poured volumes only, never the dashes', () => {
  // 30 + 22.5 + 30 = 82.5, and the 2 drops are not some number of millilitres
  // anyone should be told by this file — shopping-list.js's own rule.
  assert.strictEqual(scaler.totalMl(NEGRONI, 1), 82.5);
  // At ⅔, which is a multiple this drink allows: 20 + 15 + 20, exact.
  assert.strictEqual(scaler.totalMl(NEGRONI, 2 / 3), 55);
});

test('every non-volumetric amount sits outside the total', () => {
  // Helen, 2026-09-04: "Ignore drops and dashes and pinches in target ml."
  // Grams, leaves, `each`, a bare count and `to top` are outside it for the
  // same reason — the total is millilitres, and only millilitres are.
  assert.strictEqual(
    scaler.totalMl(['30 ml', '2 dashes', '1 small pinch', '25 g', '8 leaves',
                    'to top', '1', 'half'], 1),
    30);
});

test('a range counts its LOWER end in the total', () => {
  // The total is a figure you pour against, and the smaller end is the one you
  // can always make. Changed 2026-09-04; it totalled at the top end before.
  assert.strictEqual(scaler.totalMl(['20–30 ml', '30 ml'], 1), 50);
});

// --- a target total -----------------------------------------------------------

test('a target total becomes the multiple that reaches it', () => {
  // The Aviation: 52.5 + 15 + 7.5 + 15 = 90 ml as written, so 180 is ×2.
  const AVIATION = ['52.5 ml', '15 ml', '7.5 ml', '15 ml'];
  assert.strictEqual(scaler.totalMl(AVIATION, 1), 90);
  assert.strictEqual(scaler.multipleForTotal(AVIATION, 180), 2);
  assert.deepStrictEqual(
    scaler.scale(AVIATION, scaler.multipleForTotal(AVIATION, 180)).amounts,
    ['105 ml', '30 ml', '15 ml', '30 ml']);
});

test('a target is worked backwards and then made sane', () => {
  // Helen, 2026-09-04: the target "works the ratios out backwards within reason
  // but then updates the target ml the user has entered to something more sane,
  // that is, based on 2.5-ml increments." 100 ml of an 82.5 ml drink is ×1.212
  // on paper; the nearest allowed multiple is ×1⅓, which pours 110 ml, and 110
  // is what the box is rewritten to.
  assert.strictEqual(scaler.multipleForTotal(NEGRONI, 100), 1.212);
  const snapped = scaler.snapMultiple(NEGRONI, 1.212);
  assert.strictEqual(snapped.steps, 4);
  assert.strictEqual(snapped.text, '1⅓');
  assert.strictEqual(snapped.moved, true);
  assert.strictEqual(scaler.totalMl(NEGRONI, snapped.multiple), 110);
  assert.deepStrictEqual(scaler.scale(NEGRONI, snapped.multiple).amounts.slice(0, 3),
                         ['40 ml', '30 ml', '40 ml']);
});

test('snapping goes to the NEAREST allowed multiple, up or down', () => {
  // ×0.5 of the Negroni sits exactly between ⅓ and ⅔, and a tie goes up --
  // the ordinary convention, and the generous pour.
  assert.strictEqual(scaler.snapMultiple(NEGRONI, 0.5).text, '⅔');
  // ×0.4 is nearer ⅓.
  assert.strictEqual(scaler.snapMultiple(NEGRONI, 0.4).text, '⅓');
  // A drink whose step is ×1 has no half of itself at all.
  assert.strictEqual(
    scaler.snapMultiple(['45 ml', '22.5 ml', '15 ml', '5 ml'], 0.5).text, '1');
  // Never below the floor, however small the number.
  assert.strictEqual(scaler.snapMultiple(NEGRONI, 0.01).text, '⅓');
});

test('a snapped multiple prints as a person would write it', () => {
  assert.strictEqual(scaler.multipleText(NEGRONI, 1 / 3), '⅓');
  assert.strictEqual(scaler.multipleText(NEGRONI, 1), '1');
  assert.strictEqual(scaler.multipleText(NEGRONI, 5 / 3), '1⅔');
  assert.strictEqual(scaler.multipleText(NEGRONI, 2), '2');
  assert.strictEqual(scaler.multipleText(['50 ml', '5 ml'], 1.5), '1½');
});

test('a target below the floor is refused like any other multiple', () => {
  // 27.5 ml is the least ['50 ml', '5 ml'] can be poured as, so 10 ml is not a
  // drink this page can offer — the same refusal the multiple box gives, with
  // the same floor and the same smallest total to report.
  const out = scaler.scale(['50 ml', '5 ml'],
                           scaler.multipleForTotal(['50 ml', '5 ml'], 10));
  assert.strictEqual(out.ok, false);
  assert.strictEqual(out.floor, 0.5);
  assert.strictEqual(out.floorTotalMl, 27.5);
});

test('a target with nothing to scale, or no number, is null', () => {
  // Nothing volumetric: there is no total to divide into, so the control has
  // no answer rather than a wrong one.
  assert.strictEqual(scaler.multipleForTotal(['2 dashes', 'to top'], 50), null);
  [0, -30, '', null, undefined, 'lots'].forEach((bad) => {
    assert.strictEqual(scaler.multipleForTotal(NEGRONI, bad), null, String(bad));
  });
});

// --- half a lime --------------------------------------------------------------

test('half a lime scales in whole limes, and prints in words', () => {
  // Helen, 2026-09-04: `amount: "half"`, with `half` and `whole` as units. The
  // arithmetic is 0.5 of a `whole`; only the printing is special.
  assert.deepStrictEqual(scaler.scale(['half'], 1).amounts, ['half']);
  assert.deepStrictEqual(scaler.scale(['half'], 2).amounts, ['1 whole']);
  assert.deepStrictEqual(scaler.scale(['half'], 3).amounts, ['1½ whole']);
  assert.deepStrictEqual(scaler.scale(['half'], 4).amounts, ['2 whole']);
  // Half of half a lime is a quarter of one, and "0.25 whole" is the wart this
  // avoids -- as is `unitLabel`'s "0.5 wholes" one line further down.
  assert.deepStrictEqual(scaler.scale(['half'], 0.5).amounts, ['quarter']);
});

test('a whole fruit written as a count prints the same way', () => {
  assert.deepStrictEqual(scaler.scale(['1 whole'], 1).amounts, ['1 whole']);
  assert.deepStrictEqual(scaler.scale(['1 whole'], 2).amounts, ['2 whole']);
  assert.deepStrictEqual(scaler.scale(['1 whole'], 0.5).amounts, ['half']);
});

test('half a lime is not a volume, so it never sets the floor', () => {
  // A count, like a dash: nothing asks it to clear 2.5 ml, and it takes no part
  // in the gcd either. 45 ml alone is 90 half-ml units, so the step is 5/90 and
  // the floor is that same step -- at which the 45 ml is exactly 2.5 ml.
  assert.strictEqual(scaler.floorMultiple(['45 ml', 'half', '20 g']), 5 / 90);
  assert.strictEqual(scaler.scale(['45 ml', 'half', '20 g'], 5 / 90).amounts[0],
                     '2.5 ml');
});
