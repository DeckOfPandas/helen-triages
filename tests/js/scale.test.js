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

test('a volume scales and lands on the 2.5 ml grid', () => {
  // 22.5 × 1.5 is 33.75 on paper and 35 in a jigger. Helen: a barspoon is 5 ml
  // and a jigger is marked in 2.5s. 33.75 is exactly half way between two
  // marks, and a tie goes UP -- the ordinary convention, and the generous pour.
  const out = scaler.scale(NEGRONI, 1.5);
  assert.strictEqual(out.ok, true);
  assert.deepStrictEqual(out.amounts, ['45 ml', '35 ml', '45 ml', '3 drops']);
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

test('the floor is the smallest volume rounded up to the next half step', () => {
  // 2.5 / 5 = 0.5 exactly: a 5 ml absinthe rinse can be halved and no further.
  assert.strictEqual(scaler.floorMultiple(['50 ml', '5 ml']), 0.5);
  // 2.5 / 4 = 0.625, which is not a value the spinner offers, so ×1.
  assert.strictEqual(scaler.floorMultiple(['50 ml', '4 ml']), 1);
  // Nothing volumetric: nothing can go under 2.5 ml, so the step is the floor.
  assert.strictEqual(scaler.floorMultiple(['2 dashes', 'to top']), 0.5);
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
  assert.strictEqual(scaler.scale(['30 ml', '1 ml'], 1).ok, true);
  assert.strictEqual(scaler.scale(['30 ml', '1 ml'], 0.5).ok, false);
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
  // Halved and re-gridded: 15 + 12.5 + 15. 11.25 lands on 12.5, not 11.25.
  assert.strictEqual(scaler.totalMl(NEGRONI, 0.5), 42.5);
});
