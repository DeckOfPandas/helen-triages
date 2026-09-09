// =============================================================================
// Tests for assets/js/food-shopping-list.js — GitHub issue #801.
//
//   node --test tests/js/*.test.js
//
// A pure module, required directly, the same shape as shopping-list.js and its
// tests. The DOM half is filters.js and is not tested here.
//
// WHAT THESE ARE REALLY GUARDING. Two things, and neither shows up while
// clicking around with a tidy shortlist of three recipes:
//
//   THE MESSY DATA. 778 hand-written ingredient amounts across 86 files, in
//   every shape from `½ tsp` to `2 x 400 g cans` to `1 tbsp (6 g)` to nothing
//   at all. The fixtures below are real strings out of real recipes, named
//   where it helps.
//
//   THE ARITHMETIC HELEN RULED ON. 2026-09-07: "For now, don't tidy/round
//   beyond 1 g precision", then "I mean don't round to 10 g or 5 g, round to
//   1g". Two thirds of 200 g is 133 g. Getting that wrong is a quiet wrong
//   number on a page rather than an error anybody would see.
// =============================================================================
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const F = require('../../assets/js/food-shopping-list.js');

/** Terser fixtures: one ingredient entry. */
const ing = (amount, name, aisle, scale) => ({ amount, name, aisle, scale });

const AISLES = [
  { key: 'produce', label: 'produce' },
  { key: 'dairy', label: 'dairy & eggs' },
  { key: 'cupboard', label: 'store cupboard' },
  { key: 'other', label: 'other' }
];

const opts = { aisles: AISLES };

/** Every row across every aisle, flattened, for the tests that do not care. */
const rows = (entries, options) =>
  F.build(entries, options || opts).reduce((all, a) => all.concat(a.items), []);

const byLabel = (entries, label) =>
  rows(entries).find((r) => r.label.toLowerCase() === label.toLowerCase());

const textOf = (entries, label) => byLabel(entries, label).text;

// --- the aisles ---------------------------------------------------------------

test('aisles come back in the declared order, and empty ones do not come back', () => {
  const built = F.build([
    ing('1', 'plain flour', 'cupboard'),
    ing('1', 'onion', 'produce')
  ], opts);
  assert.deepStrictEqual(built.map((a) => a.key), ['produce', 'cupboard']);
  assert.deepStrictEqual(built.map((a) => a.label), ['produce', 'store cupboard']);
});

test('an unknown aisle falls to the last one rather than vanishing', () => {
  // A blob emitted by an older build, or a key removed from aisles.yml. The
  // ingredient still has to appear: a silently dropped line is a thing you
  // then do not buy.
  const built = F.build([ing('1', 'kohlrabi', 'greengrocer')], opts);
  assert.deepStrictEqual(built.map((a) => a.key), ['other']);
  assert.strictEqual(built[0].items[0].label, 'kohlrabi');
});

test('items are alphabetical inside an aisle', () => {
  // Not by volume, which is what the drinks list does -- the aisle heading has
  // already done that job here. food-shopping-list.js's own note says why.
  const built = F.build([
    ing('1', 'onion', 'produce'),
    ing('1', 'carrot', 'produce'),
    ing('1', 'Bay leaf', 'produce')
  ], opts);
  assert.deepStrictEqual(built[0].items.map((r) => r.label),
    ['Bay leaf', 'carrot', 'onion']);
});

// --- scaling ------------------------------------------------------------------

test('the scale multiplies, and a gram is the floor', () => {
  // Helen's ruling, and the arithmetic behind the number she will see: four
  // portions of a recipe that serves six.
  assert.strictEqual(textOf([ing('200 g', 'plain flour', 'cupboard', 2 / 3)],
    'plain flour'), '133 g');
  assert.strictEqual(textOf([ing('500 g', 'chicken', 'produce', 2)],
    'chicken'), '1 kg');
});

test('a missing, zero or nonsense scale is x1', () => {
  [undefined, 0, -2, null, 'two'].forEach((scale) => {
    assert.strictEqual(
      textOf([ing('200 g', 'plain flour', 'cupboard', scale)], 'plain flour'),
      '200 g', String(scale));
  });
});

test('spoons and counts keep their fractions instead', () => {
  // ⅔ tsp is a real measure; 0.67 tsp is not a number anyone has a spoon for.
  assert.strictEqual(textOf([ing('1 tsp', 'ground cumin', 'cupboard', 2 / 3)],
    'ground cumin'), '⅔ tsp');
  assert.strictEqual(textOf([ing('5', 'carrots', 'produce', 2 / 3)],
    'carrots'), '3⅓');
  assert.strictEqual(textOf([ing('1½ tbsp', 'dark soy sauce', 'cupboard', 2)],
    'dark soy sauce'), '3 tbsp');
});

test('a sub-gram total keeps a decimal rather than printing as zero', () => {
  assert.strictEqual(textOf([ing('1 g', 'saffron', 'cupboard', 0.2)], 'saffron'),
    '0.2 g');
});

// --- totalling ----------------------------------------------------------------

test('two recipes writing the same ingredient make one line', () => {
  assert.strictEqual(textOf([
    ing('200 g', 'plain flour', 'cupboard'),
    ing('50 g', 'plain flour', 'cupboard')
  ], 'plain flour'), '250 g');
});

test('a plural and its singular are the same shopping', () => {
  // The real pairs in the collection: onion/onions, carrot/carrots,
  // lemon/lemons, garlic clove/garlic cloves, cinnamon stick/cinnamon sticks.
  // Two rows here means two totals you have to add up yourself, which is the
  // one job this panel has.
  const built = rows([
    ing('1', 'onion', 'produce'),
    ing('2', 'onions', 'produce')
  ]);
  assert.strictEqual(built.length, 1);
  assert.strictEqual(built[0].text, '3');
  // The label is the FIRST spelling seen, never the folded key.
  assert.strictEqual(built[0].label, 'onion');
});

test('the label is the first spelling, and case does not split a total', () => {
  const built = rows([
    ing('4', 'Parma ham', 'cupboard'),
    ing('4', 'parma ham', 'cupboard')
  ]);
  assert.strictEqual(built.length, 1);
  assert.strictEqual(built[0].label, 'Parma ham');
  assert.strictEqual(built[0].text, '8');
});

test('units that cannot be added are kept apart, and joined with +', () => {
  // shopping-list.js's rule, and the reason for it: nobody can say how many
  // grams a clove is, so inventing the conversion would be worse than two
  // figures on one line.
  assert.strictEqual(textOf([
    ing('2 cloves', 'garlic', 'produce'),
    ing('1 tsp', 'garlic', 'produce')
  ], 'garlic'), '2 cloves + 1 tsp');
});

test('litres and kilograms total with millilitres and grams', () => {
  // A litre IS a thousand millilitres, on both sides of every recipe here --
  // which is not the conversion shopping-list.js refuses. Before this, one
  // stock was two rows, and a twelfth of `1½ l` printed as `0.125 l`.
  assert.strictEqual(textOf([
    ing('1½ l', 'stock', 'cupboard'),
    ing('500 ml', 'stock', 'cupboard')
  ], 'stock'), '2 l');
  assert.strictEqual(textOf([ing('1½ l', 'stock', 'cupboard', 1 / 12)], 'stock'),
    '125 ml');
  assert.strictEqual(textOf([ing('1 kg', 'pearl barley', 'cupboard', 0.083)],
    'pearl barley'), '83 g');
});

test('tablespoons, ounces and counts are never converted into anything', () => {
  assert.strictEqual(textOf([
    ing('2 tbsp', 'olive oil', 'cupboard'),
    ing('1 tsp', 'olive oil', 'cupboard')
  ], 'olive oil'), '2 tbsp + 1 tsp');
});

// --- ranges, tildes and brackets ----------------------------------------------

test('a range is scaled at both ends', () => {
  assert.strictEqual(textOf([ing('30–50 g', 'flaked almonds', 'cupboard', 2)],
    'flaked almonds'), '60–100 g');
});

test('a range and a plain amount total without a branch', () => {
  assert.strictEqual(textOf([
    ing('50 g', 'flaked almonds', 'cupboard'),
    ing('30–50 g', 'flaked almonds', 'cupboard')
  ], 'flaked almonds'), '80–100 g');
});

test('a range that collapses prints once', () => {
  assert.strictEqual(textOf([ing('2–2 g', 'salt', 'cupboard')], 'salt'), '2 g');
});

test('a tilde survives the arithmetic', () => {
  assert.strictEqual(textOf([ing('~2 tbsp', 'tamarind paste', 'cupboard', 2)],
    'tamarind paste'), '~4 tbsp');
});

test('one approximate entry makes the whole total approximate', () => {
  // Anything added to an estimate is an estimate; saying otherwise would be
  // the total claiming more than it knows.
  assert.strictEqual(textOf([
    ing('1 tbsp', 'tamarind paste', 'cupboard'),
    ing('~1 tbsp', 'tamarind paste', 'cupboard')
  ], 'tamarind paste'), '~2 tbsp');
});

test('a bracket restating the quantity scales with it', () => {
  // chai-spice-powder's cloves. Doubling the tablespoons without the grams
  // would print a contradiction.
  assert.strictEqual(textOf([ing('1 tbsp (6 g)', 'whole cloves', 'cupboard', 2)],
    'whole cloves'), '2 tbsp (12 g)');
});

test('a bracket does not split a total from the same unit written bare', () => {
  assert.strictEqual(textOf([
    ing('1 tbsp (6 g)', 'whole cloves', 'cupboard'),
    ing('2 tbsp (12 g)', 'whole cloves', 'cupboard')
  ], 'whole cloves'), '3 tbsp (18 g)');
});

// --- the entries that are not quantities --------------------------------------

test('an unquantified entry is counted, never summed', () => {
  assert.strictEqual(textOf([ing('some', 'salt', 'cupboard')], 'salt'), 'some');
  assert.strictEqual(textOf([
    ing('some', 'salt', 'cupboard'),
    ing('some', 'salt', 'cupboard')
  ], 'salt'), 'some (×2)');
});

test('an ingredient with no amount at all is a line with no amount', () => {
  // Every magic-bag item (MANUAL 4.3) and 100 of the 778 recipe items. The
  // name IS the useful half; a count appears once more than one recipe wants
  // it.
  const one = byLabel([ing('', 'olive oil', 'cupboard')], 'olive oil');
  assert.strictEqual(one.text, '');
  assert.strictEqual(one.label, 'olive oil');

  assert.strictEqual(textOf([
    ing('', 'olive oil', 'cupboard'),
    ing(undefined, 'olive oil', 'cupboard'),
    ing(null, 'olive oil', 'cupboard')
  ], 'olive oil'), '×3');
});

test('a quantity and a phrase on the same ingredient are both reported', () => {
  assert.strictEqual(textOf([
    ing('2 g', 'salt', 'cupboard'),
    ing('some', 'salt', 'cupboard')
  ], 'salt'), '2 g + some');
});

// --- the edges ----------------------------------------------------------------

test('an entry with no name is dropped rather than making a nameless line', () => {
  assert.deepStrictEqual(rows([
    ing('1', '', 'produce'), ing('1', null, 'produce'), ing('1', '  ', 'produce')
  ]), []);
});

test('no entries at all is an empty list, not a throw', () => {
  [[], null, undefined].forEach((input) => {
    assert.deepStrictEqual(F.build(input, opts), []);
  });
});

test('no aisle list at all still produces a list', () => {
  // The page emits _data/food/aisles.yml's own `order`; absent it, everything
  // is still shoppable, which is the standing every other blob on that index
  // has.
  const built = F.build([ing('200 g', 'plain flour', 'cupboard')]);
  assert.strictEqual(built.length, 1);
  assert.strictEqual(built[0].items[0].label, 'plain flour');
});

test('a real weeknight, end to end', () => {
  // Three dinners for four, one of which serves six. The shape of the thing
  // Helen actually asked for, asserted once so a refactor has to keep it.
  const built = F.build([
    ing('1', 'onion', 'produce', 1),
    ing('5', 'carrots', 'produce', 2 / 3),
    ing('200 g', 'orzo', 'cupboard', 2 / 3),
    ing('2 x 400 g cans', 'butter beans', 'cupboard', 1),
    ing('1½ l', 'stock', 'cupboard', 2 / 3),
    ing('100 g', 'halloumi', 'dairy', 2 / 3)
  ], opts);

  assert.deepStrictEqual(built.map((a) => a.label),
    ['produce', 'dairy & eggs', 'store cupboard']);
  assert.deepStrictEqual(
    built[0].items.map((r) => r.label + ': ' + r.text),
    ['carrots: 3⅓', 'onion: 1']);
  assert.deepStrictEqual(built[1].items.map((r) => r.text), ['67 g']);
  assert.deepStrictEqual(
    built[2].items.map((r) => r.label + ': ' + r.text),
    ['butter beans: 2 x 400 g cans', 'orzo: 133 g', 'stock: 1 l']);
});
