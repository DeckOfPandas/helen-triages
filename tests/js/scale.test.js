// Tests for assets/js/scale.js, the recipe scaler (#545).
//
//   node --test tests/js/*.test.js
//
// Run through the stub-dom harness rather than required directly: scale.js
// reaches its dependency through `HTF.shoppingList`, not through require().
// Loading both files into a stub page in the drink page's order tests the
// wiring as well as the maths; require() alone would pass on a page where
// scale.js loaded first and `HTF.scale` was never defined.
//
// Each rule pinned here is a decision, not an implementation detail: multiples
// of the recipe as written, the 2.5 ml grid, the floor that refuses instead of
// rounding, and the amounts that are not quantities and must survive untouched.
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
  // 22.5 × 1.5 is 33.75, which no jigger measures, and rounding it to 35 would
  // grow the Campari against the gin. ×1.5 is not a whole number of this
  // drink's own step (⅓), so it is refused outright.
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
  // A bare `7.5` and `25 g` are both real data. Neither is a volume, so neither
  // is rounded to the 2.5 ml grid or held to the 2.5 ml floor.
  const out = scaler.scale(['1', '25 g'], 2);
  assert.deepStrictEqual(out.amounts, ['2', '50 g']);
});

test('#1132: a printed amount splits into its number and its one-word unit', () => {
  // For the rows the layout marks quiet ("1 cube" of "sugar cube"): the drink
  // page prints the number in the amount and the unit, if at all, in the name.
  assert.deepStrictEqual({ ...scaler.splitUnit('2 cubes') }, { number: '2', unit: 'cubes' });
  assert.deepStrictEqual({ ...scaler.splitUnit('3 each') }, { number: '3', unit: 'each' });
  assert.deepStrictEqual({ ...scaler.splitUnit('1.5 each') }, { number: '1.5', unit: 'each' });
  // The LAST space: a range is all number.
  assert.deepStrictEqual({ ...scaler.splitUnit('1 to 2 cubes') },
    { number: '1 to 2', unit: 'cubes' });
  // No unit at all is not an error.
  assert.deepStrictEqual({ ...scaler.splitUnit('3') }, { number: '3', unit: '' });
  assert.deepStrictEqual({ ...scaler.splitUnit('') }, { number: '', unit: '' });
  // ...and it is what the scaler itself prints that gets split.
  assert.deepStrictEqual({ ...scaler.splitUnit(scaler.scale(['1 cube'], 12).amounts[0]) },
    { number: '12', unit: 'cubes' });
});

// --- the amounts that are not quantities --------------------------------------

test('an amount that is not a quantity passes through untouched', () => {
  const out = scaler.scale(['(top)', '(rinse)', '30 ml'], 4);
  assert.deepStrictEqual(out.amounts, ['(top)', '(rinse)', '120 ml']);
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

test('an amount that was never on the grid is left out of it, and not rounded', () => {
  // cobra-effect's 22.75 ml is off the grid. It cannot be kept exact by any
  // multiple, so it is multiplied rather than rounded, because rounding it
  // would move a ratio.
  const cobra = ['30 ml', '30 ml', '22.75 ml', '15 ml', '15 ml'];
  assert.deepStrictEqual(scaler.scale(cobra, 2).amounts,
    ['60 ml', '60 ml', '45.5 ml', '30 ml', '30 ml']);
  // And the recipe as written still prints as written.
  assert.deepStrictEqual(scaler.scale(cobra, 1).amounts, cobra);
});

test('a multiple under the floor is REFUSED, and says how far down it can go', () => {
  // A refusal, not a silent round up to 2.5.
  const out = scaler.scale(['50 ml', '5 ml'], 0.25);
  assert.strictEqual(out.ok, false);
  assert.strictEqual(out.floor, 0.5);
  assert.strictEqual(out.offender, 1);          // the 5 ml is what stops it
  assert.strictEqual(out.floorTotalMl, 27.5);   // 25 + 2.5, as poured
  assert.strictEqual(out.amounts, undefined);   // nothing to show
});

test('the floor is capped at ×1, so a recipe as written is never refused', () => {
  // A drink may be written with 2.5 ml of something, or less. That is Helen's
  // recipe, not an error for this file to report.
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

test('a multiple below the floor is refused, with the smallest total it can make', () => {
  // 27.5 ml is the least ['50 ml', '5 ml'] can be measured as, so ×0.182 (10 ml)
  // is refused.
  const out = scaler.scale(['50 ml', '5 ml'], 0.182);
  assert.strictEqual(out.ok, false);
  assert.strictEqual(out.floor, 0.5);
  assert.strictEqual(out.floorTotalMl, 27.5);
});

// --- half a lime --------------------------------------------------------------

test('half a lime scales in whole limes, and prints in words', () => {
  // `amount: "half"`, with `half` and `whole` as units. The arithmetic is 0.5
  // of a `whole`; only the printing is special.
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
  assert.strictEqual(scaler.scale(['45 ml', 'half', '20 g'], 5 / 90).amounts[0],
                     '2.5 ml');
});
