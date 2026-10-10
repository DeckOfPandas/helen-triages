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
  // Never the folded key. Three is more than one, and a recipe wrote the
  // plural, so the row takes it (#1297); with nothing to choose between, the
  // label is the first spelling seen -- the Parma ham below.
  assert.strictEqual(built[0].label, 'onions');
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

// =============================================================================
// #1297, 2026-10-09 -- by-eye measures in whole ones, one fruit from two parts,
// and a line that only points at another.
// =============================================================================

const PRODUCE = [{ key: 'produce', label: 'produce' }];
const BY_EYE = ['handful', 'pinch', 'dash', 'splash', 'knob'];

const line = (entries, label, options) => {
  const built = F.build(entries, Object.assign({ aisles: PRODUCE }, options || {}));
  const all = built.reduce((acc, aisle) => acc.concat(aisle.items), []);
  const found = all.filter((row) => row.label === label);
  assert.strictEqual(found.length, 1,
    `expected one "${label}" row, got: ${all.map((r) => r.text + ' ' + r.label).join(' | ')}`);
  return found[0].text;
};

const QUARTERS = ['sprig', 'bunch'];
const STEPPED = { wholeMeasures: BY_EYE.concat(['drop', 'twist', 'lot', 'pat']),
  quarterMeasures: QUARTERS };

// "2 sprigs (1¼ in the recipes)": the amount, and the bracket where there is one.
const bought = (entries, label, options) => {
  const built = F.build(entries, Object.assign({ aisles: PRODUCE }, options || STEPPED));
  const found = built.reduce((acc, aisle) => acc.concat(aisle.items), [])
    .filter((row) => row.label === label);
  assert.strictEqual(found.length, 1, 'one "' + label + '" row');
  return found[0].text + (found[0].aside ? ' (' + found[0].aside + ')' : '');
};
const eye = (amount, scale) => bought(
  [{ amount: amount, name: 'parsley', aisle: 'produce', scale: scale }], 'parsley');

test('#1297: a stepped measure is bought whole, rounded UP, with what the recipes ask for beside it', () => {
  // Helen, 2026-10-10: "I'd like the shopping list not to write 1.17 sprigs
  // either, so please round that upwards to the next integer like this: '2
  // handfuls fresh parsley (1 1/4 in the recipes)'."
  assert.strictEqual(eye('1 handful', 7 / 6), '2 handfuls (1¼ in the recipes)');
  assert.strictEqual(eye('1 sprig', 7 / 6), '2 sprigs (1¼ in the recipes)');
  assert.strictEqual(eye('1 bunch', 7 / 6), '2 bunches (1¼ in the recipes)');
  assert.strictEqual(eye('1 handful', 1.5), '2 handfuls (1½ in the recipes)');
  assert.strictEqual(eye('1 sprig', 2 / 3), '1 sprig (¾ in the recipes)');
  assert.strictEqual(eye('1 handful', 2 / 3), '1 handful (¾ in the recipes)');
  assert.strictEqual(eye('5 twists', 2 / 3), '4 twists (3¼ in the recipes)');
  assert.strictEqual(eye('2 pats', 2 / 3), '2 pats (1¼ in the recipes)');
});

test('#1297: 1.17 handfuls buys TWO -- the list does not borrow the recipe page\'s half step', () => {
  // The first build quoted the recipe page's own figure ("1 handful") and so
  // bought one. Helen: "1.17 handfuls should buy 2, again giving the
  // bracketed requested number."
  assert.strictEqual(eye('1 handful', 7 / 6), '2 handfuls (1¼ in the recipes)');
  assert.strictEqual(eye('2 handfuls', 7 / 6), '3 handfuls (2¼ in the recipes)');
  assert.strictEqual(eye('1 pinch', 7 / 6), '2 pinches (1¼ in the recipes)');
});

test('#1297: no bracket when what to buy is what the recipes ask for', () => {
  assert.strictEqual(eye('1 handful', 3), '3 handfuls');
  assert.strictEqual(eye('4 sprigs', 2), '8 sprigs');
  assert.strictEqual(eye('2 handfuls', 0.5), '1 handful');
  // Within an eighth of a whole number is that number: 0.02 buys nothing.
  assert.strictEqual(eye('1 handful', 1.02), '1 handful');
  assert.strictEqual(eye('4 sprigs', 1.02), '4 sprigs');
});

test('#1297: no figure in either place is ever a decimal', () => {
  [7 / 6, 5 / 6, 2 / 3, 1.1, 0.37, 3.3].forEach((factor) => {
    ['1 sprig', '3 sprigs', '1 bunch', '1 handful', '2 pinches', '5 twists', '1 pat']
      .forEach((amount) => {
        assert.ok(!/\d\.\d/.test(eye(amount, factor)),
          amount + ' x' + factor + ' -> ' + eye(amount, factor));
      });
  });
});

test('#1297: a size word, a range and a tilde survive', () => {
  assert.strictEqual(eye('1 small handful', 2.4), '3 small handfuls (2½ in the recipes)');
  assert.strictEqual(eye('1 small handful', 2.2), '3 small handfuls (2¼ in the recipes)');
  assert.strictEqual(eye('1–2 sprigs', 7 / 6), '2–3 sprigs (1¼–2¼ in the recipes)');
  assert.strictEqual(eye('~1 handful', 2.2), '~3 handfuls (2¼ in the recipes)');
});

test('#1297: the TOTAL is stepped once, never each recipe on its own', () => {
  // 1.17 and 1.17 sprigs are 2.33 between them: 2¼ in the recipes, 3 to buy.
  // Stepped apart they would be 1¼ + 1¼, which is 2½.
  assert.strictEqual(bought([
    { amount: '1 sprig', name: 'thyme', aisle: 'produce', scale: 7 / 6, recipe: 'x' },
    { amount: '1 sprig', name: 'thyme', aisle: 'produce', scale: 7 / 6, recipe: 'y' }
  ], 'thyme'), '3 sprigs (2¼ in the recipes)');
});

test('#1297: a row with a second total says which unit the bracket is about', () => {
  assert.strictEqual(bought([
    { amount: '1 sprig', name: 'thyme', aisle: 'produce', scale: 7 / 6, recipe: 'x' },
    { amount: '10 g', name: 'thyme', aisle: 'produce', scale: 1, recipe: 'y' }
  ], 'thyme'), '2 sprigs + 10 g (1¼ sprigs in the recipes)');
});

test('#1297: nothing else is rounded -- grams, spoons and counts are as they were', () => {
  const other = (amount, scale) => bought(
    [{ amount: amount, name: 'thing', aisle: 'produce', scale: scale }], 'thing');
  assert.strictEqual(other('200 g', 2 / 3), '133 g');
  assert.strictEqual(other('1 tsp', 2 / 3), '⅔ tsp');
  assert.strictEqual(other('1', 7 / 6), '1.17', 'a chicken a sixth bigger');
  assert.strictEqual(other('3 cloves', 0.5), '1½ cloves');
});

test('#1297: with no list of measures handed over, a handful totals as before', () => {
  assert.strictEqual(line(
    [{ amount: '1 handful', name: 'parsley', aisle: 'produce', scale: 1.5 }],
    'parsley'), '1½ handfuls');
});

// --- one fruit, two parts ------------------------------------------------------
// Helen: 'I would like to cleverly combine e.g. "zest of 1 lemon" and "juice of
// 1 lemon" to make "1 lemon" in the shopping list.'

// The literal form: the count is inside the item, and the plugin reads it out.
const literal = (recipe, name, fruit, count, parts, scale) => ({
  amount: '', name: name, aisle: 'produce', scale: scale || 1,
  recipe: recipe, fruit: fruit, count: count, parts: parts
});
// The house form: an amount, the fruit, and the part after the comma.
const house = (recipe, amount, name, parts, scale) => ({
  amount: amount, name: name, aisle: 'produce', scale: scale || 1,
  recipe: recipe, parts: parts
});

test('#1297: "zest of 1 lemon" and "juice of 1 lemon" are 1 lemon', () => {
  assert.strictEqual(line([
    literal('cake', 'zest of 1 lemon', 'lemon', '1', ['zest']),
    literal('cake', 'juice of 1 lemon', 'lemon', '1', ['juice'])
  ], 'lemon'), '1');
});

test('#1297: one such line alone is that many of the fruit, where it was a row with no figure', () => {
  assert.strictEqual(line(
    [literal('salad', 'juice of ½ lemon', 'lemon', '½', ['juice'])], 'lemon'), '½');
});

test('#1297: the part that needs the most fruit decides', () => {
  // lemon-buttermilk-pound-cake: 4 zested, then ½ and 2 large juiced ("use
  // the ones you've zested"). It printed 4½ + 2 large.
  assert.strictEqual(line([
    house('cake', '4', 'lemons', ['zest']),
    house('cake', '½', 'lemon', ['juice']),
    house('cake', '2 large', 'lemons', ['juice'])
  ], 'lemons'), '4');
  // And the other way about: one zested, three juiced, is three.
  assert.strictEqual(line([
    house('cake', '1', 'lemon', ['zest']),
    house('cake', '3', 'lemons', ['juice'])
  ], 'lemons'), '3');
});

test('#1297: the same part twice still adds up', () => {
  // slow-cooked-short-rib-and-pineapple-tacos: a lime juiced, another lime
  // juiced, and the zest and juice of half a lime.
  assert.strictEqual(line([
    house('tacos', '1', 'lime', ['juice']),
    house('tacos', '1', 'lime', ['juice']),
    literal('tacos', 'finely grated zest and juice of ½ lime', 'lime', '½', ['zest', 'juice'])
  ], 'lime'), '2½');
});

test('#1297: a line naming no part is a different fruit, and is added', () => {
  assert.strictEqual(line([
    house('fish', '1', 'lemon', ['zest']),
    house('fish', '1', 'lemon', ['juice']),
    { amount: '1', name: 'lemon', aisle: 'produce', scale: 1, recipe: 'fish' }
  ], 'lemon'), '2');
});

test('#1297: two RECIPES each wanting a lemon are two lemons', () => {
  assert.strictEqual(line([
    literal('cake', 'zest of 1 lemon', 'lemon', '1', ['zest']),
    literal('salad', 'juice of 1 lemon', 'lemon', '1', ['juice'])
  ], 'lemon'), '2');
});

test('#1297: the merged fruit scales with its recipe', () => {
  assert.strictEqual(line([
    literal('cake', 'zest of 1 lemon', 'lemon', '1', ['zest'], 3),
    literal('cake', 'juice of 1 lemon', 'lemon', '1', ['juice'], 3)
  ], 'lemon'), '3');
});

test('#1297: lines that say no recipe are never merged', () => {
  // The callers before #1297 pass no `recipe`; they get the old sum.
  assert.strictEqual(line([
    { amount: '1', name: 'lemon', aisle: 'produce', scale: 1, parts: ['zest'] },
    { amount: '1', name: 'lemon', aisle: 'produce', scale: 1, parts: ['juice'] }
  ], 'lemon'), '2');
});

// --- a line that only points -----------------------------------------------------

const oil = (recipe, amount, pointer) => ({
  amount: amount, name: 'olive oil', aisle: 'produce', scale: 1,
  recipe: recipe, pointer: pointer
});

test('#1297: "the rest of the oil above" adds nothing to the oil', () => {
  assert.strictEqual(line([oil('pasta', '85 ml'), oil('pasta', '', true)],
    'olive oil'), '85 ml');
});

test('#1297: two recipes with a pointer each no longer print a stray ×2', () => {
  // The charred-asparagus pasta salad and the cauliflower-anchovy orzo.
  const text = line([
    oil('pasta', '85 ml'), oil('pasta', '', true),
    oil('orzo', '3 tbsp'), oil('orzo', '', true)
  ], 'olive oil');
  assert.strictEqual(text, '85 ml + 3 tbsp');
});

test('#1297: a no-amount line that is NOT a pointer is still counted', () => {
  // "salted butter, extra, for greasing" really is extra.
  const text = line([oil('loaf', '100 g'), oil('loaf', '', false)], 'olive oil');
  assert.strictEqual(text, '100 g');
  const two = line([
    oil('loaf', '100 g'), oil('loaf', '', false), oil('turkey', '', false)
  ], 'olive oil');
  assert.strictEqual(two, '100 g + ×2');
});

test('#1297: a pointer with nothing to point at stays a line', () => {
  assert.strictEqual(line([oil('pasta', '', true)], 'olive oil'), '');
});

// --- "2 lemons", not "2 lemon" -- #1297, Helen, 2026-10-10 ----------------------

const NOUNS = ['lemon', 'lime', 'apple', 'peach', 'avocado'];
const labelOf = (entries, nouns) => {
  const built = F.build(entries, { aisles: PRODUCE, countNouns: nouns || NOUNS });
  assert.strictEqual(built[0].items.length, 1);
  return built[0].items[0].text + ' ' + built[0].items[0].label;
};
const count = (amount, name, recipe) =>
  ({ amount: amount, name: name, aisle: 'produce', scale: 1, recipe: recipe });

test('#1297: a count of more than one takes the plural, whichever spelling came first', () => {
  // One lemon from each of two recipes printed "2 lemon".
  assert.strictEqual(labelOf([count('1', 'lemon', 'a'), count('1', 'lemon', 'b')]), '2 lemons');
  assert.strictEqual(labelOf([count('1', 'lemon', 'a'), count('2', 'lemons', 'b')]), '3 lemons');
  assert.strictEqual(labelOf([count('1', 'sharp green apple', 'a'),
    count('1', 'sharp green apple', 'b')]), '2 sharp green apples');
  assert.strictEqual(labelOf([count('1 large', 'lemon', 'a'),
    count('1 large', 'lemon', 'b')]), '2 large lemons');
});

test('#1297: one or less takes the singular', () => {
  assert.strictEqual(labelOf([count('½', 'lemons', 'a'), count('½', 'lemons', 'b')]), '1 lemon');
  assert.strictEqual(labelOf([count('½', 'limes', 'a')]), '½ lime');
  assert.strictEqual(labelOf([count('1½', 'lemon', 'a')]), '1½ lemons');
});

test('#1297: a spelling a recipe used is taken with no list at all', () => {
  // The two were folded onto one row, so they are the same noun.
  assert.strictEqual(labelOf([count('1', 'onion', 'a'), count('2', 'onions', 'b')], []),
    '3 onions');
  assert.strictEqual(labelOf([count('½', 'onions', 'a'), count('½', 'onion', 'b')], []),
    '1 onion');
});

test('#1297: a form nobody wrote is made only for a noun on the list', () => {
  assert.strictEqual(labelOf([count('1', 'ripe peach', 'a'), count('1', 'ripe peach', 'b')]),
    '2 ripe peaches');
  assert.strictEqual(labelOf([count('2', 'avocado', 'a')]), '2 avocados');
  // Real names from the collection, 2026-10-10, each of which a rule about
  // "the last word" got wrong.
  [['sprigs thyme', '2 sprigs thyme'], ['goose', '2 goose'],
    ['spoons butter', '2 spoons butter'], ['skinless', '2 skinless'],
    ['star anise', '2 star anise'], ['red chilli', '2 red chilli']
  ].forEach(([name, expected]) => {
    assert.strictEqual(labelOf([count('2', name, 'a')]), expected);
  });
  assert.strictEqual(labelOf([count('1', 'black peppercorns', 'a')]), '1 black peppercorns');
  // The count is of pinches, whatever the last word is.
  assert.strictEqual(F.build(
    [{ amount: '2', name: 'pinch ground lime', aisle: 'produce', scale: 1 }],
    { aisles: PRODUCE, countNouns: NOUNS, wholeMeasures: BY_EYE })[0].items[0].label,
    'pinch ground lime');
  assert.strictEqual(labelOf([count('1', 'lemon', 'a'), count('1', 'lemon', 'b')], []),
    '2 lemon', 'and with no list handed over, nothing is made');
});

test('#1297: only a bare count is touched -- a unit already agrees', () => {
  assert.strictEqual(labelOf([count('200 g', 'lemon', 'a'), count('300 g', 'lemon', 'b')]),
    '500 g lemon');
  assert.strictEqual(labelOf([count('2 cloves', 'garlic', 'a')]), '2 cloves garlic');
  assert.strictEqual(labelOf([count('2 tbsp', 'olive oil', 'a')]), '2 tbsp olive oil');
});

test('#1297: a name that cannot be made safely is left as written', () => {
  assert.strictEqual(labelOf([count('2', 'lemon or 30 ml lemon juice', 'a')]),
    '2 lemon or 30 ml lemon juice');
  assert.strictEqual(labelOf([count('2', 'Little Gem', 'a')]), '2 Little Gem');
  // No singular is invented for "tomatoes" or "hummus".
  assert.strictEqual(labelOf([count('1', 'tomatoes', 'a')]), '1 tomatoes');
  assert.strictEqual(labelOf([count('8', 'Parma ham', 'a')]), '8 Parma ham');
  // A mixed row is two totals, and is not one count.
  assert.strictEqual(labelOf([count('4', 'lemon', 'a'), count('2 large', 'lemon', 'b')]),
    '4 + 2 large lemon');
});
