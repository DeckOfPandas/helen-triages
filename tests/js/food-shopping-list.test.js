// Tests for assets/js/food-shopping-list.js (#801).
//
//   node --test tests/js/*.test.js
//
// A pure module, required directly, the same shape as shopping-list.js and its
// tests. The DOM half is filters.js and is not tested here.
//
// Two things are pinned. The messy data: hand-written amounts in every shape
// from `½ tsp` to `2 x 400 g cans` to `1 tbsp (6 g)` to nothing at all; the
// fixtures are real strings out of real recipes. And the arithmetic: nothing is
// rounded coarser than a gram, so two thirds of 200 g is 133 g. Getting that
// wrong is a quiet wrong number on a page, not an error anybody would see.
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
  // ingredient still has to appear: a silently dropped line is a thing you then
  // do not buy.
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
  // Four portions of a recipe that serves six.
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
  // Two rows here means two totals to add up by hand, which is the one job this
  // panel has.
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
  // A litre is a thousand millilitres, which is not the conversion
  // shopping-list.js refuses: one stock is one row, and a twelfth of `1½ l`
  // prints as `125 ml`.
  assert.strictEqual(textOf([
    ing('1½ l', 'stock', 'cupboard'),
    ing('500 ml', 'stock', 'cupboard')
  ], 'stock'), '2 l');
  assert.strictEqual(textOf([ing('1½ l', 'stock', 'cupboard', 1 / 12)], 'stock'),
    '125 ml');
  assert.strictEqual(textOf([ing('1 kg', 'pearl barley', 'cupboard', 0.083)],
    'pearl barley'), '83 g');
});

test('tablespoons and teaspoons are never converted into each other', () => {
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
  // Doubling the tablespoons without the grams would print a contradiction.
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
  // Every magic-bag item (MANUAL 4.3) and many recipe items. The name is the
  // useful half; a count appears once more than one recipe wants it.
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
  // is still shoppable.
  const built = F.build([ing('200 g', 'plain flour', 'cupboard')]);
  assert.strictEqual(built.length, 1);
  assert.strictEqual(built[0].items[0].label, 'plain flour');
});

test('a real weeknight, end to end', () => {
  // Three dinners for four, one of which serves six, asserted once so a
  // refactor has to keep the whole shape.
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
    ['butter beans: 2 x 400 g tins', 'orzo: 133 g', 'stock: 1 l']);
});

// --- #1297: by-eye measures in whole ones, one fruit from two parts, and a
// --- line that only points at another ------------------------------------------

const PRODUCE = [{ key: 'produce', label: 'produce' }];
// As food/index.html passes them: `half_step_measures` step in halves,
// `quarter_step_measures` in quarters.
const BY_EYE = ['pinch', 'dash', 'splash', 'knob'];

const line = (entries, label, options) => {
  const built = F.build(entries, Object.assign({ aisles: PRODUCE }, options || {}));
  const all = built.reduce((acc, aisle) => acc.concat(aisle.items), []);
  const found = all.filter((row) => row.label === label);
  assert.strictEqual(found.length, 1,
    `expected one "${label}" row, got: ${all.map((r) => r.text + ' ' + r.label).join(' | ')}`);
  return found[0].text;
};

const QUARTERS = ['handful', 'sprig', 'bunch'];
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
  // The list never writes "1.17 sprigs": it buys the next whole one and quotes
  // the recipes' own stepped figure in the bracket.
  assert.strictEqual(eye('1 handful', 7 / 6), '2 handfuls (1¼ in the recipes)');
  assert.strictEqual(eye('1 sprig', 7 / 6), '2 sprigs (1¼ in the recipes)');
  assert.strictEqual(eye('1 bunch', 7 / 6), '2 bunches (1¼ in the recipes)');
  assert.strictEqual(eye('1 handful', 1.5), '2 handfuls (1½ in the recipes)');
  assert.strictEqual(eye('1 sprig', 2 / 3), '1 sprig (¾ in the recipes)');
  assert.strictEqual(eye('1 handful', 2 / 3), '1 handful (¾ in the recipes)');
});

test('a half-step measure is quoted to the nearest half, as the recipe page steps it', () => {
  // Half a handful makes sense and a quarter of a pinch does not, so a pinch is
  // quoted to the nearest half.
  assert.strictEqual(eye('1 pinch', 7 / 6), '1 pinch');
  assert.strictEqual(eye('1 pinch', 1.5), '2 pinches (1½ in the recipes)');
  assert.strictEqual(eye('1 pinch', 1 / 3), '1 pinch (½ in the recipes)');
  assert.strictEqual(eye('5 twists', 2 / 3), '4 twists (3½ in the recipes)');
  assert.strictEqual(eye('2 pats', 2 / 3), '2 pats (1½ in the recipes)');
});

test('#1297: 1.17 handfuls buys TWO -- the list does not borrow the recipe page\'s half step', () => {
  // Quoting the recipe page's own figure ("1 handful") would buy one.
  assert.strictEqual(eye('1 handful', 7 / 6), '2 handfuls (1¼ in the recipes)');
  assert.strictEqual(eye('2 handfuls', 7 / 6), '3 handfuls (2¼ in the recipes)');
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
// "zest of 1 lemon" and "juice of 1 lemon" in one recipe are one lemon to buy.

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
  // 4 zested, then ½ and 2 large juiced ("use the ones you've zested"): 4, not
  // 4½ + 2 large.
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
  // A lime juiced, another lime juiced, and the zest and juice of half a lime.
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
  // A caller that passes no `recipe` gets the plain sum.
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

// --- "2 lemons", not "2 lemon" (#1297) ----------------------------------------

const NOUNS = ['lemon', 'lime', 'apple', 'peach', 'avocado'];
const labelOf = (entries, nouns) => {
  const built = F.build(entries, { aisles: PRODUCE, countNouns: nouns || NOUNS });
  assert.strictEqual(built[0].items.length, 1);
  return built[0].items[0].text + ' ' + built[0].items[0].label;
};
const count = (amount, name, recipe) =>
  ({ amount: amount, name: name, aisle: 'produce', scale: 1, recipe: recipe });

test('#1297: a count of more than one takes the plural, whichever spelling came first', () => {
  // One lemon from each of two recipes must not print "2 lemon".
  assert.strictEqual(labelOf([count('1', 'lemon', 'a'), count('1', 'lemon', 'b')]), '2 lemons');
  assert.strictEqual(labelOf([count('1', 'lemon', 'a'), count('2', 'lemons', 'b')]), '3 lemons');
  assert.strictEqual(labelOf([count('1', 'sharp green apple', 'a'),
    count('1', 'sharp green apple', 'b')]), '2 sharp green apples');
  assert.strictEqual(labelOf([count('1 large', 'lemon', 'a'),
    count('1 large', 'lemon', 'b')]), '2 large lemons');
});

test('#1457: a row\'s key, what its tick is stored under, does not move with the count', () => {
  // "1 lemon" becoming "2 lemons" must not drop a tick made on it.
  const keyOf = (entries) =>
    F.build(entries, { aisles: PRODUCE, countNouns: NOUNS })[0].items[0].key;
  assert.strictEqual(keyOf([count('1', 'lemon', 'a')]), keyOf([count('1', 'lemon', 'a'),
    count('1', 'lemon', 'b')]));
  assert.strictEqual(keyOf([count('2', 'Lemons', 'a')]), keyOf([count('½', 'lemon', 'a')]));
});

test('#1457: a row names every recipe behind it, once each, so a new count can untick it', () => {
  const row = F.build([count('1', 'lemon', 'a'), count('2', 'lemons', 'b'),
    count('1', 'lemon', 'a')], { aisles: PRODUCE, countNouns: NOUNS })[0].items[0];
  assert.deepStrictEqual(row.recipes, ['a', 'b']);
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
  // Real names from the collection, each of which a rule about "the last word"
  // gets wrong.
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

// --- #1458: what it costs, on a local build ------------------------------------
// The rates arrive per ingredient from _plugins/food_costs.rb (GBP per base
// unit) and the unit table from _data/food/costs.yml; this file only multiplies.

const UNITS = {
  g: ['g', 1], oz: ['g', 28.35], ml: ['ml', 1], tsp: ['ml', 5], tbsp: ['ml', 15],
  '': ['each', 1], large: ['each', 1], clove: ['each', 1], bunch: ['pack', 1],
  handful: ['pack', 0.5], pinch: ['free', 0]
};
const FLOUR = { g: [0.001, 0.002] };        // £1–£2 a kilo
const OIL = { ml: [0.005, 0.01] };          // £5–£10 a litre
const EGG = { each: [0.2, 0.5] };
const costed = (entries) => F.build(entries, { aisles: AISLES, costUnits: UNITS })
  .reduce((all, a) => all.concat(a.items), []);
const priced = (amount, rate, scale) =>
  costed([{ amount, name: 'thing', aisle: 'cupboard', scale, rate }])[0].cost;

test('#1458: a weight, a volume and a count are each priced by their own rate', () => {
  assert.strictEqual(priced('500 g', FLOUR).text, '£0.75 (£0.50–£1.00)');
  assert.strictEqual(priced('2 tbsp', OIL).text, '£0.22 (£0.15–£0.30)');
  assert.strictEqual(priced('3 large', EGG).text, '£1.05 (£0.60–£1.50)');
});

test('#1458: a line is priced after scaling, so four of a recipe for two is double', () => {
  assert.strictEqual(priced('500 g', FLOUR, 2).text, '£1.50 (£1.00–£2.00)');
});

test('#1458: a weight-priced thing measured in spoons is costed at 1 ml to 1 g', () => {
  assert.strictEqual(priced('2 tbsp', FLOUR).text, '£0.04 (£0.03–£0.06)');
  assert.strictEqual(priced('100 ml', { g: [0.01, 0.01] }).text, '£1.00');
});

test('#1458: a pinch, a free name and an unquantified line cost nothing, and draw nothing', () => {
  assert.strictEqual(priced('1 pinch', FLOUR), null);
  assert.deepStrictEqual(priced('2 tsp', { free: true }).free, true);
  assert.strictEqual(priced('', FLOUR), null);
});

test('#1458: no rate, or a unit the rate cannot reach, is unpriced, never zero', () => {
  assert.deepStrictEqual(priced('200 g', undefined), { unpriced: true });
  assert.deepStrictEqual(priced('2', FLOUR), { unpriced: true });
  assert.deepStrictEqual(priced('2 bags', FLOUR), { unpriced: true });
});

test('#1458: "2 x 400 g cans" is 800 g, whatever the container is called', () => {
  // Beef Wellington's "2 x 400 g beef fillets" is its dearest line; unpriced,
  // the dish read as "from £2.33 a portion".
  assert.strictEqual(priced('2 x 400 g cans', FLOUR).text, '£1.20 (£0.80–£1.60)');
  assert.strictEqual(priced('2 x 400 g', FLOUR).text, '£1.20 (£0.80–£1.60)');
  assert.strictEqual(priced('1 x 1 kg bag', FLOUR).text, '£1.50 (£1.00–£2.00)');
  assert.strictEqual(priced('2 x 250 ml cartons', OIL).text, '£3.75 (£2.50–£5.00)');
});

test('#1458: a row priced in part says "from" its known part', () => {
  const row = costed([
    { amount: '500 g', name: 'flour', aisle: 'cupboard', rate: FLOUR },
    { amount: '2 bags', name: 'flour', aisle: 'cupboard', rate: FLOUR }
  ])[0];
  assert.strictEqual(row.cost.text, 'from £0.50');
});

test('#1458: the total sums what is priced and counts what is not', () => {
  const list = costed([
    { amount: '500 g', name: 'flour', aisle: 'cupboard', rate: FLOUR },
    { amount: '2 tbsp', name: 'oil', aisle: 'cupboard', rate: OIL },
    { amount: '200 g', name: 'kohlrabi', aisle: 'produce' },
    { amount: '', name: 'salt', aisle: 'cupboard', rate: { free: true } }
  ]);
  const sum = F.costTotal(list);
  assert.strictEqual(sum.unpriced, 1);
  assert.strictEqual(sum.text, 'from £0.65');
  const whole = F.costTotal(list.filter((r) => r.label !== 'kohlrabi'));
  assert.strictEqual(whole.text, '£0.98 (£0.65–£1.30)');
  assert.strictEqual(whole.unpriced, 0);
});

test('#1458: a recipe costs per portion, or per batch with per = 1, and keeps "from"', () => {
  const lines = [
    { amount: '500 g', name: 'flour', aisle: 'cupboard', rate: FLOUR },
    { amount: '2 tbsp', name: 'oil', aisle: 'cupboard', rate: OIL }
  ];
  const o = { aisles: AISLES, costUnits: UNITS };
  assert.strictEqual(F.recipeCost(lines, 4, o).text, '£0.24 (£0.16–£0.33)');
  assert.strictEqual(F.recipeCost(lines, 1, o).text, '£0.98 (£0.65–£1.30)');
  const partial = F.recipeCost(lines.concat(
    [{ amount: '200 g', name: 'kohlrabi', aisle: 'produce' }]), 1, o);
  assert.strictEqual(partial.text, 'from £0.65');
  assert.strictEqual(partial.partial, true);
  // The recipe page says "not counting 1 unpriced item" from this count.
  assert.strictEqual(partial.unpriced, 1);
  assert.deepStrictEqual(partial.unpricedNames, ['kohlrabi']);
});

test('#1486: the cost line names what it could not price', () => {
  const o = { aisles: AISLES, costUnits: UNITS };
  const flour = { amount: '500 g', name: 'flour', aisle: 'cupboard', rate: FLOUR };
  const one = F.recipeCost([flour,
    { amount: '1', name: 'cockerel carcass', aisle: 'produce' }], 1, o);
  assert.strictEqual(F.unpricedText(one), ', not counting 1 unpriced item (cockerel carcass)');
  const three = F.recipeCost([flour,
    { amount: '200 g', name: 'kohlrabi', aisle: 'produce' },
    { amount: '1', name: 'cockerel carcass', aisle: 'produce' },
    { amount: '10 g', name: 'kombu', aisle: 'produce' }], 1, o);
  assert.strictEqual(F.unpricedText(three),
    ', not counting 3 unpriced items (cockerel carcass, kohlrabi and kombu)');
  // A row priced only in part is named too: it is part of the "from".
  const part = F.recipeCost([flour,
    { amount: '2 bags', name: 'flour', aisle: 'cupboard', rate: FLOUR }], 1, o);
  assert.strictEqual(F.unpricedText(part), ', not counting 1 unpriced item (flour)');
  assert.strictEqual(F.unpricedText(F.recipeCost([flour], 1, o)), '');
  assert.strictEqual(F.unpricedText(null), '');
});

test('#1458: no portion count, or no unit table, is no recipe figure at all', () => {
  const lines = [{ amount: '500 g', name: 'flour', aisle: 'cupboard', rate: FLOUR }];
  assert.strictEqual(F.recipeCost(lines, 0, { costUnits: UNITS }), null);
  assert.strictEqual(F.recipeCost(lines, 4, { aisles: AISLES }), null);
  assert.strictEqual(F.recipeCost([{ amount: '1', name: 'x', aisle: 'other' }], 4,
    { costUnits: UNITS }), null);
});

test('#1458: without the unit table, which only a local build carries, nothing is costed', () => {
  const row = F.build([{ amount: '500 g', name: 'flour', aisle: 'cupboard', rate: FLOUR }],
    { aisles: AISLES })[0].items[0];
  assert.strictEqual(row.cost, undefined);
  assert.strictEqual(F.costTotal([row]), null);
});


// --- metric, one spelling per unit, and the pinch: #1462 D2, D3, C5 ----------

test('#1462 D2: ounces and pounds total in grams, with the grams already there', () => {
  assert.strictEqual(textOf([
    ing('3 oz', 'butter', 'dairy'),
    ing('100 g', 'butter', 'dairy')
  ], 'butter'), '185 g');
  assert.strictEqual(textOf([ing('2 lb', 'apricots', 'produce')], 'apricots'), '907 g');
});

test('#1462 D2: fluid ounces, pints and cups total in millilitres', () => {
  assert.strictEqual(textOf([ing('½ pint', 'milk', 'dairy')], 'milk'), '284 ml');
  assert.strictEqual(textOf([ing('1½ fl oz', 'milk', 'dairy')], 'milk'), '43 ml');
  assert.strictEqual(textOf([ing('1¾ cups', 'buttermilk', 'dairy')], 'buttermilk'), '420 ml');
  // Four pints is over a litre, so it is shown in litres like any other total.
  assert.strictEqual(textOf([ing('4 pints', 'stock', 'cupboard')], 'stock'), '2.273 l');
});

test('#1462 D2: inches are centimetres, one decimal', () => {
  assert.strictEqual(textOf([ing('2 inches', 'ginger', 'produce')], 'ginger'), '5.1 cm');
});

test('#1462 D3: how full the spoon is does not split a row', () => {
  assert.strictEqual(textOf([
    ing('1 heaped tbsp', 'plain flour', 'cupboard'),
    ing('1 level tbsp', 'plain flour', 'cupboard'),
    ing('1 rounded tbsp', 'plain flour', 'cupboard'),
    ing('1 tbsp', 'plain flour', 'cupboard')
  ], 'plain flour'), '4 tbsp');
  assert.strictEqual(textOf([
    ing('1 slightly rounded tsp', 'ground ginger', 'cupboard'),
    ing('2 tsp, slightly rounded', 'ground ginger', 'cupboard')
  ], 'ground ginger'), '3 tsp');
});

test('#1462 D3: a size word that is not about a spoon stays', () => {
  assert.strictEqual(textOf([ing('1 large handful', 'spinach', 'produce')], 'spinach'),
    '1 large handful');
});

test('#1462 D3: cans are tins, and × is x', () => {
  assert.strictEqual(textOf([
    ing('2 x 400 g cans', 'chopped tomatoes', 'cupboard'),
    ing('1 × 400 g tin', 'chopped tomatoes', 'cupboard'),
    ing('1 x 400-g tin', 'chopped tomatoes', 'cupboard')
  ], 'chopped tomatoes'), '4 x 400 g tins');
});

test('#1462 D3: "400 g can" is one 400 g tin, and totals with "2 x 400 g tins"', () => {
  assert.strictEqual(textOf([ing('400 g can', 'chickpeas', 'cupboard')], 'chickpeas'),
    '1 x 400 g tin');
  assert.strictEqual(textOf([
    ing('400 g can', 'chickpeas', 'cupboard'),
    ing('2 x 400 g tins', 'chickpeas', 'cupboard')
  ], 'chickpeas'), '3 x 400 g tins');
  assert.strictEqual(textOf([ing('150 g pack', 'feta', 'dairy', 2)], 'feta'), '2 x 150 g packs');
  // A weight per something is a weight, not a pack.
  assert.ok(!/x/.test(textOf([ing('250 g per person', 'potatoes', 'produce')], 'potatoes')));
});

test('#1462 D3: the recipe page keeps the unit the recipe wrote', () => {
  // The metric table is the shopping list's alone: CANONICAL, which the
  // recipe page's scaler shares, must not learn ounces.
  assert.strictEqual(F.CANONICAL.oz, undefined);
  assert.strictEqual(F.CANONICAL.cup, undefined);
  assert.ok(F.METRIC.oz);
});

test('#1462 C5: under ⅛ tsp is a pinch, and ⅛ itself is still a spoon', () => {
  assert.strictEqual(textOf([ing('⅛ tsp', 'cayenne', 'cupboard', 0.5)], 'cayenne'), 'a pinch');
  assert.strictEqual(textOf([ing('¼ tsp', 'cayenne', 'cupboard', 0.5)], 'cayenne'), '⅛ tsp');
  assert.strictEqual(textOf([ing('⅛–¼ tsp', 'cayenne', 'cupboard', 0.5)], 'cayenne'),
    'a pinch to ⅛ tsp');
});

test('#1462 C5: a pinch is a teaspoon rule only; a tablespoon keeps its fraction', () => {
  assert.strictEqual(textOf([ing('⅛ tbsp', 'salt', 'cupboard', 0.5)], 'salt'), '0.06 tbsp');
});

// --- #1474: three quirks older than #1471 ------------------------------------

test('#1474: "approx" is read like a tilde, so the amount converts and totals', () => {
  assert.strictEqual(textOf([ing('approx 8 oz', 'flaked almonds', 'cupboard')],
    'flaked almonds'), '~227 g');
  assert.strictEqual(textOf([ing('approx. 2 lb', 'pork belly', 'meat')], 'pork belly'),
    '~907 g');
  assert.strictEqual(textOf([
    ing('Approx 100 g', 'butter', 'dairy'),
    ing('100 g', 'butter', 'dairy')
  ], 'butter'), '~200 g');
});

test('#1474: a word that only starts with "approx" is not an approximation', () => {
  // The lookahead wants a space after the word, so nothing is cut out of a unit.
  const SL = require('../../assets/js/shopping-list.js');
  assert.strictEqual(SL.parseAmount('approximately'), null);
});

test('#1474: a bracketed alternative is not pluralised', () => {
  assert.strictEqual(textOf([ing('2 oz (or 2 tbsp)', 'butter', 'dairy')], 'butter'),
    '2 oz (or 2 tbsp)');
  assert.strictEqual(textOf([ing('3 cloves (or 1 tsp paste)', 'garlic', 'produce')], 'garlic'),
    '3 cloves (or 1 tsp paste)');
});

test('#1481: a per-person amount is the total for the people chosen', () => {
  const potatoes = (people, scale) => F.build([{
    amount: '250 g per person', name: 'potatoes', aisle: 'produce', scale, people
  }], { aisles: AISLES })[0].items[0].text;
  assert.strictEqual(potatoes(4, 1), '1 kg');
  // The people, not the scale, decide: doubling a recipe for 4 is 8 people.
  assert.strictEqual(potatoes(8, 2), '2 kg');
  assert.strictEqual(potatoes(3, 1), '750 g');
  assert.strictEqual(potatoes(1, 0.25), '250 g');
});

test('#1481: with no count of people, a per-person amount is as written, never multiplied', () => {
  const row = F.build([{
    amount: '250 g per person', name: 'potatoes', aisle: 'produce', scale: 2
  }], { aisles: AISLES })[0].items[0];
  assert.strictEqual(row.text, '250 g per person');
});

test('#1481: only "per person" and its kin are read as a rate per person', () => {
  assert.strictEqual(F.perPerson('250 g per person'), '250 g');
  assert.strictEqual(F.perPerson('2 slices per portion'), '2 slices');
  assert.strictEqual(F.perPerson('90 g Per Head'), '90 g');
  assert.strictEqual(F.perPerson('250 g'), null);
  assert.strictEqual(F.perPerson('1 per cent fat'), null);
  assert.strictEqual(F.perPerson(undefined), null);
});

test('#1474: a rate is not pluralised', () => {
  assert.strictEqual(textOf([ing('250 g per person', 'potatoes', 'produce')], 'potatoes'),
    '250 g per person');
  assert.strictEqual(textOf([ing('2 slices per person', 'bread', 'bakery')], 'bread'),
    '2 slices per person');
});
