// =============================================================================
// Tests for assets/js/shopping-list.js — GitHub issue #546's shopping list.
//
//   node --test tests/js/*.test.js
//
// A pure module with a `module.exports` tail, so it is simply required — the
// same shape as filter-state.js and its tests, and unlike assets.js, which
// needs the stub-dom harness.
//
// WHAT THESE ARE REALLY GUARDING. The module's whole job is to take a pile of
// ingredient entries written by hand across 124 files and produce a list you
// can shop from, and every interesting case is a MESSY-DATA case: the same
// generic written with and without a bottle, `Woodford's` against `Woodford’s`,
// `dash` against `dashes`, and eleven entries that are not quantities at all.
// Those are exactly the cases that never show up while clicking around with a
// tidy shortlist of three drinks, and exactly the ones a weekend's shopping
// would be wrong about.
// =============================================================================
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const SL = require('../../assets/js/shopping-list.js');

/** Terser fixtures: one ingredient entry. */
const ing = (amount, generic, bottle) => ({ amount, generic, bottle });

const labels = (rows) => rows.map((r) => r.label);
const byLabel = (rows, label) => rows.find((r) => r.label === label);

// --- parsing ------------------------------------------------------------------

test('parseAmount splits a number from its unit', () => {
  assert.deepStrictEqual(SL.parseAmount('22.5 ml'), { quantity: 22.5, unit: 'ml' });
  assert.deepStrictEqual(SL.parseAmount('2 dashes'), { quantity: 2, unit: 'dash' });
  assert.deepStrictEqual(SL.parseAmount('1'), { quantity: 1, unit: '' });
});

test('parseAmount returns null for the entries that are not quantities', () => {
  // The eleven real ones in the collection, and the reason a null here is an
  // answer rather than a failure.
  assert.strictEqual(SL.parseAmount('to top'), null);
  assert.strictEqual(SL.parseAmount('to rinse'), null);
  assert.strictEqual(SL.parseAmount(''), null);
  assert.strictEqual(SL.parseAmount(undefined), null);
});

test('units fold to the singular, so dash and dashes are one total', () => {
  assert.strictEqual(SL.foldUnit('dashes'), 'dash');
  assert.strictEqual(SL.foldUnit('Drops'), 'drop');
  assert.strictEqual(SL.foldUnit('ml'), 'ml');
});

test('ml and g are never pluralised; words are, unless there is one', () => {
  assert.strictEqual(SL.unitLabel('ml', 60), 'ml');
  assert.strictEqual(SL.unitLabel('dash', 1), 'dash');
  assert.strictEqual(SL.unitLabel('dash', 3), 'dashes');
  assert.strictEqual(SL.unitLabel('leaf', 6), 'leaves');
  // `each` is a word with no plural, and the sibilant rule below would give it
  // one -- `18 eaches`. Three drinks are written with it.
  assert.strictEqual(SL.unitLabel('each', 18), 'each');
});

// --- totalling ----------------------------------------------------------------

test('the same generic across two drinks makes one line and one total', () => {
  const rows = SL.build([
    ing('30 ml', 'London dry gin'),
    ing('45 ml', 'London dry gin')
  ]);
  assert.strictEqual(rows.length, 1);
  assert.strictEqual(rows[0].text, '75 ml');
});

test('the decimals this collection is full of do not go floating-point', () => {
  // 22.5 and 7.5 are the second and fifth most common amounts in the data, so
  // this is the ordinary case rather than an edge one.
  const rows = SL.build([ing('22.5 ml', 'rum'), ing('22.5 ml', 'rum'), ing('22.5 ml', 'rum')]);
  assert.strictEqual(rows[0].text, '67.5 ml');

  const drops = SL.build([ing('0.1 ml', 'saline'), ing('0.2 ml', 'saline')]);
  assert.strictEqual(drops[0].text, '0.3 ml');
});

test('two units in one group are added separately, never converted', () => {
  // 2 dashes of bitters is not some number of millilitres, and this file must
  // not be the thing that decides it is.
  const rows = SL.build([ing('45 ml', 'absinthe'), ing('2 dashes', 'absinthe')]);
  assert.strictEqual(rows[0].text, '45 ml + 2 dashes');
});

test('an unquantified entry is counted, not summed', () => {
  const rows = SL.build([
    ing('to top', 'soda water'),
    ing('to top', 'soda water'),
    ing('to top', 'soda water')
  ]);
  assert.strictEqual(rows[0].text, 'to top (×3)');
});

test('a quantity and an unquantified entry can share a line', () => {
  const rows = SL.build([ing('15 ml', 'absinthe'), ing('to rinse', 'absinthe')]);
  assert.strictEqual(rows[0].text, '15 ml + to rinse');
});

// --- the label rule, which is Helen's ------------------------------------------
// Settled 2026-09-04, after she looked at the first version: "show generic
// first, with bottle on the same line in brackets, like the recipes." The
// generic ALWAYS leads; the bottles are always the bracketed note.

test('the generic leads and the bottle is the note, even when unanimous', () => {
  const rows = SL.build([
    ing('30 ml', 'aromatic bitters', 'Angostura'),
    ing('2 dashes', 'aromatic bitters', 'Angostura')
  ]);
  assert.strictEqual(rows[0].label, 'aromatic bitters');
  assert.strictEqual(rows[0].note, 'Angostura');
});

test('the long generic is used, never a shortened card name', () => {
  // `card_names` shortens "moderately aged Jamaican rum" to "Jamaican rum" to
  // fit a 370px card (#501). Helen: "give the long rum names, not the shortened
  // ones we generated for cards." Nothing in this module reads that map, and
  // this is the test that says so.
  const rows = SL.build([ing('30 ml', 'moderately aged Jamaican rum', 'Appleton 8')]);
  assert.strictEqual(rows[0].label, 'moderately aged Jamaican rum');
});

test('two bottles for one generic: the generic leads and both are kept', () => {
  // The case that makes bottle-as-identity unusable — measured at 20 generics
  // in the real collection.
  const rows = SL.build([
    ing('50 ml', 'London dry gin', 'Beefeater'),
    ing('30 ml', 'London dry gin', 'Tanqueray')
  ]);
  assert.strictEqual(rows.length, 1, 'one bottle of gin to buy, so one line');
  assert.strictEqual(rows[0].label, 'London dry gin');
  assert.strictEqual(rows[0].note, 'Beefeater / Tanqueray');
  assert.strictEqual(rows[0].text, '80 ml');
});

test('one bottle plus one bare entry: the generic still leads', () => {
  // 41 generics in the collection appear both ways. The bare entry means the
  // group is "the generic, sometimes as this bottle" — not "this bottle".
  const rows = SL.build([
    ing('50 ml', 'bourbon', "Woodford's Reserve"),
    ing('30 ml', 'bourbon')
  ]);
  assert.strictEqual(rows[0].label, 'bourbon');
  assert.strictEqual(rows[0].note, "Woodford's Reserve");
});

test('a curly apostrophe does not split a group or duplicate a bottle', () => {
  // Real: `Woodford's Reserve` and `Woodford’s Reserve` are both in the data.
  const rows = SL.build([
    ing('50 ml', 'bourbon', "Woodford's Reserve"),
    ing('30 ml', 'bourbon', 'Woodford’s Reserve')
  ]);
  assert.strictEqual(rows.length, 1);
  assert.strictEqual(rows[0].note, "Woodford's Reserve", 'one bottle, written two ways');
  assert.strictEqual(rows[0].text, '80 ml');
});

test('case does not split a group either', () => {
  // Real: `Dolin Dry` and `Dolin dry`.
  const rows = SL.build([
    ing('15 ml', 'dry vermouth', 'Dolin Dry'),
    ing('15 ml', 'dry vermouth', 'Dolin dry')
  ]);
  assert.strictEqual(rows.length, 1);
  assert.strictEqual(rows[0].bottles.length, 1);
  assert.strictEqual(rows[0].text, '30 ml');
});

test('a generic written as a list is one ingredient, joined with "or"', () => {
  // Issue #441: a list generic means "either would do", not two ingredients.
  const rows = SL.build([
    ing('30 ml', ['aged rum', 'Demerara rum']),
    ing('30 ml', ['aged rum', 'Demerara rum'])
  ]);
  assert.strictEqual(rows.length, 1);
  assert.strictEqual(rows[0].label, 'aged rum or Demerara rum');
  assert.strictEqual(rows[0].text, '60 ml');
});

test('a bottle written as a list is one suggestion, joined the same way', () => {
  const rows = SL.build([ing('30 ml', 'blanco tequila', ['Patrón Silver', 'Tapatio'])]);
  assert.strictEqual(rows[0].label, 'blanco tequila');
  assert.strictEqual(rows[0].note, 'Patrón Silver / Tapatio');
  assert.deepStrictEqual(rows[0].bottles, ['Patrón Silver or Tapatio'],
    'the "or" form is still on the row for a caller that wants it');
});

// --- the scaler ---------------------------------------------------------------

test('the multiplier scales every quantity', () => {
  const rows = SL.build([ing('22.5 ml', 'rum'), ing('2 dashes', 'bitters')], { multiplier: 4 });
  assert.strictEqual(byLabel(rows, 'rum').text, '90 ml');
  assert.strictEqual(byLabel(rows, 'bitters').text, '8 dashes');
});

test('the multiplier scales the DRINKS for an unquantified entry, not a volume', () => {
  // "to top" x2 drinks, made 3 times each, is six toppings-up. There is no
  // volume here to multiply and inventing one would be the dishonest answer.
  const rows = SL.build([
    ing('to top', 'soda water'),
    ing('to top', 'soda water')
  ], { multiplier: 3 });
  assert.strictEqual(rows[0].text, 'to top (×6)');
});

test('a missing, zero or negative multiplier falls back to one glass each', () => {
  const one = SL.build([ing('30 ml', 'gin')])[0].text;
  [undefined, 0, -2, 'lots', null].forEach((m) => {
    assert.strictEqual(SL.build([ing('30 ml', 'gin')], { multiplier: m })[0].text, one,
      `for multiplier ${JSON.stringify(m)}`);
  });
});

// --- exclusions and shape -----------------------------------------------------

test('excluded generics are left out, and the caller supplies the list', () => {
  // `not_on_cards: ['water']` comes from _data/cocktails/ingredients.yml, so the
  // cards and this list can never disagree about what an ingredient is.
  const rows = SL.build([ing('30 ml', 'water'), ing('30 ml', 'gin')], { exclude: ['water'] });
  assert.deepStrictEqual(labels(rows), ['gin']);
});

// --- order --------------------------------------------------------------------
// Helen, 2026-09-04: "order by descending volume required." The big pours are
// what you shop for; two dashes of bitters is a bottle you almost certainly own.

test('rows come back largest volume first', () => {
  const rows = SL.build([
    ing('10 ml', 'benedictine'), ing('180 ml', 'rum'), ing('45 ml', 'lime juice')
  ]);
  assert.deepStrictEqual(labels(rows), ['rum', 'lime juice', 'benedictine']);
});

test('rows with no volume at all follow the ones that have it', () => {
  // Sorting 2 dashes against 45 ml would need the conversion this module
  // refuses to invent, so everything volumetric sorts first and the rest
  // follows in a block.
  const rows = SL.build([
    ing('2 dashes', 'aromatic bitters'),
    ing('10 ml', 'benedictine'),
    ing('to top', 'soda water'),
    ing('180 ml', 'rum')
  ]);
  assert.deepStrictEqual(labels(rows),
    ['rum', 'benedictine', 'aromatic bitters', 'soda water']);
});

test('equal volumes fall back to the label, case-insensitively', () => {
  const rows = SL.build([
    ing('10 ml', 'rum'), ing('10 ml', 'Angostura'), ing('10 ml', 'benedictine')
  ]);
  assert.deepStrictEqual(labels(rows), ['Angostura', 'benedictine', 'rum']);
});

// --- whole fruits -------------------------------------------------------------
// Helen, 2026-09-04: "375 ml lemon juice (X to Y lemons)". Yields are declared
// in _data/cocktails/ingredients.yml and passed in; only the four you squeeze
// yourself have them.

const YIELDS = {
  'lemon juice': { fruit: 'lemon', ml_min: 30, ml_max: 45 },
  'lime juice': { fruit: 'lime', ml_min: 20, ml_max: 30 },
  'grapefruit juice': { fruit: 'grapefruit', ml_min: 180, ml_max: 240 }
};

test('the worked example from the brief', () => {
  // 375 / 45 = 8.33 -> 9 at best; 375 / 30 = 12.5 -> 13 at worst.
  const rows = SL.build([ing('375 ml', 'lemon juice')], { juiceYields: YIELDS });
  assert.strictEqual(rows[0].fruit.text, '9 to 13 lemons');
});

test('the FEWEST fruits comes from the LARGEST yield, which is the easy one to invert', () => {
  const [row] = SL.build([ing('120 ml', 'lime juice')], { juiceYields: YIELDS });
  assert.strictEqual(row.fruit.fewest, 4, '120 / 30, the generous lime');
  assert.strictEqual(row.fruit.most, 6, '120 / 20, the mean one');
});

test('both ends round up — three quarters of a lemon is a lemon you bought', () => {
  const [row] = SL.build([ing('10 ml', 'lemon juice')], { juiceYields: YIELDS });
  assert.strictEqual(row.fruit.fewest, 1);
  assert.strictEqual(row.fruit.most, 1);
});

test('a range that collapses is printed once, and singular', () => {
  const [row] = SL.build([ing('20 ml', 'lime juice')], { juiceYields: YIELDS });
  assert.strictEqual(row.fruit.text, '1 lime');
});

test('a collapsed range above one is still printed once, and plural', () => {
  const [row] = SL.build([ing('180 ml', 'grapefruit juice')], { juiceYields: YIELDS });
  assert.strictEqual(row.fruit.text, '1 grapefruit');
  // 360 / 240 = 1.5 -> 2, and 360 / 180 = 2 -> 2. (480 does NOT collapse:
  // it is 2 to 3, which is what this test asserted on its first run.)
  const [two] = SL.build([ing('360 ml', 'grapefruit juice')], { juiceYields: YIELDS });
  assert.strictEqual(two.fruit.text, '2 grapefruits');
});

test('the count follows the scaler, because the total does', () => {
  const [row] = SL.build([ing('45 ml', 'lemon juice')], { juiceYields: YIELDS, multiplier: 8 });
  assert.strictEqual(row.text, '360 ml');
  assert.strictEqual(row.fruit.text, '8 to 12 lemons');
});

test('a juice with no declared yield gets no count, and does not throw', () => {
  // Pineapple, cranberry and apple arrive in a carton — deliberately absent
  // from the data rather than forgotten.
  const [row] = SL.build([ing('90 ml', 'pineapple juice')], { juiceYields: YIELDS });
  assert.strictEqual(row.fruit, null);
});

test('only millilitres make fruit — 2 dashes of lemon juice is not a lemon', () => {
  const [row] = SL.build([ing('2 dashes', 'lemon juice')], { juiceYields: YIELDS });
  assert.strictEqual(row.fruit, null);
});

test('with no yields passed at all, every total is still right', () => {
  const [row] = SL.build([ing('375 ml', 'lemon juice')]);
  assert.strictEqual(row.fruit, null);
  assert.strictEqual(row.text, '375 ml');
});

// --- per-drink quantities ------------------------------------------------------
// Helen, 2026-09-04: "Per drink quantities, zomg yes please!" An entry's own
// `glasses` wins; the global multiplier is the fallback, which is why it needed
// no second code path.

test('each entry can carry its own number of glasses', () => {
  const rows = SL.build([
    { amount: '50 ml', generic: 'gin', glasses: 2 },
    { amount: '50 ml', generic: 'rum', glasses: 6 }
  ]);
  assert.strictEqual(byLabel(rows, 'rum').text, '300 ml');
  assert.strictEqual(byLabel(rows, 'gin').text, '100 ml');
});

test('two drinks sharing an ingredient each scale by their own count', () => {
  // A negroni x2 and a boulevardier x6, both wanting Campari.
  const rows = SL.build([
    { amount: '30 ml', generic: 'Campari', glasses: 2 },
    { amount: '20 ml', generic: 'Campari', glasses: 6 }
  ]);
  assert.strictEqual(rows[0].text, '180 ml', '60 + 120');
});

test('an entry with no count of its own falls back to the global multiplier', () => {
  const rows = SL.build([
    { amount: '50 ml', generic: 'gin', glasses: 2 },
    { amount: '50 ml', generic: 'rum' }
  ], { multiplier: 10 });
  assert.strictEqual(byLabel(rows, 'gin').text, '100 ml', 'its own count wins');
  assert.strictEqual(byLabel(rows, 'rum').text, '500 ml', 'the fallback applies');
});

test('per-drink counts scale an unquantified entry by drinks too', () => {
  const rows = SL.build([{ amount: 'to top', generic: 'soda water', glasses: 5 }]);
  assert.strictEqual(rows[0].text, 'to top (×5)');
});

// --- declared bottle aliases ---------------------------------------------------
// bottles.yml carries them for 77 bottles and the ingredient search already
// reads them (#529). Case-folding cannot reach these: nothing about `ED3` says
// `El Dorado 3` except that Helen wrote it down.

test('a declared alias collapses onto the canonical bottle', () => {
  const rows = SL.build([
    ing('30 ml', 'lightly aged and filtered rum', 'ED3'),
    ing('30 ml', 'lightly aged and filtered rum', 'El Dorado 3')
  ], { bottleAliases: { ed3: 'El Dorado 3' } });
  assert.strictEqual(rows[0].note, 'El Dorado 3', 'one bottle, written two ways');
  assert.strictEqual(rows[0].text, '60 ml');
});

test('each alternative of a list suggestion resolves on its own', () => {
  const rows = SL.build([ing('30 ml', 'rum', ['ED3', 'Havana Club 3'])], {
    bottleAliases: { ed3: 'El Dorado 3', 'havana club 3': 'Havana 3' }
  });
  assert.strictEqual(rows[0].note, 'El Dorado 3 / Havana 3');
});

test('the note names each bottle once, even when a suggestion was a list', () => {
  // Real, on `lightly aged and filtered rum`: one drink says `Havana Club 3`,
  // another says `El Dorado 3 or Havana Club 3`. Deduping the JOINED strings
  // printed "Havana Club 3 / El Dorado 3 or Havana Club 3" — two bottles, one
  // of them twice.
  const rows = SL.build([
    ing('30 ml', 'lightly aged and filtered rum', 'Havana Club 3'),
    ing('30 ml', 'lightly aged and filtered rum', ['El Dorado 3', 'Havana Club 3'])
  ]);
  assert.strictEqual(rows[0].label, 'lightly aged and filtered rum');
  assert.strictEqual(rows[0].note, 'Havana Club 3 / El Dorado 3');
});

test('the suggestion as Helen wrote it survives on the row', () => {
  // The note flattens to individual bottles; `bottles` keeps the "or" form,
  // which is her own wording for a choice she is happy with (#441).
  const rows = SL.build([
    ing('30 ml', 'rum', ['El Dorado 3', 'Havana Club 3']),
    ing('30 ml', 'rum', ['El Dorado 3', 'Havana Club 3'])
  ]);
  assert.strictEqual(rows[0].label, 'rum');
  assert.strictEqual(rows[0].note, 'El Dorado 3 / Havana Club 3');
  assert.deepStrictEqual(rows[0].bottles, ['El Dorado 3 or Havana Club 3']);
});

test('with no alias map the fold is still the answer, and nothing throws', () => {
  const rows = SL.build([ing('30 ml', 'rum', 'ED3')]);
  assert.strictEqual(rows[0].note, 'ED3');
});

test('an entry with no generic is dropped rather than making a nameless line', () => {
  const rows = SL.build([ing('30 ml', ''), ing('30 ml', null), ing('30 ml', 'gin')]);
  assert.deepStrictEqual(labels(rows), ['gin']);
});

test('no entries at all is an empty list, not a throw', () => {
  [[], null, undefined].forEach((input) => {
    assert.deepStrictEqual(SL.build(input), []);
  });
});

// --- #801: what the food shopping list needed the parser to learn -------------
// Every case below is a real amount string out of _food_recipes/, and every one
// returned null before #801 or lost part of itself on the way through. The last
// test in this block is the important one: it is the claim that widening the
// parser changed nothing at all for the drinks.

test('vulgar fractions are numbers', () => {
  assert.deepStrictEqual(SL.parseAmount('½ tsp'), { quantity: 0.5, unit: 'tsp' });
  assert.deepStrictEqual(SL.parseAmount('⅛ tsp'), { quantity: 0.125, unit: 'tsp' });
  // A digit and a fraction are ONE token: `1½` is 1.5, not 1 and then a range.
  assert.deepStrictEqual(SL.parseAmount('1½ tbsp'), { quantity: 1.5, unit: 'tbsp' });
  assert.deepStrictEqual(SL.parseAmount('1¾ cups'), { quantity: 1.75, unit: 'cup' });
  assert.deepStrictEqual(SL.parseAmount('½'), { quantity: 0.5, unit: '' });
});

test('a range keeps both ends', () => {
  assert.deepStrictEqual(SL.parseAmount('30–50 g'), { quantity: 30, unit: 'g', max: 50 });
  assert.deepStrictEqual(SL.parseAmount('1–2'), { quantity: 1, unit: '', max: 2 });
  assert.deepStrictEqual(SL.parseAmount('1½–2 tsp'), { quantity: 1.5, unit: 'tsp', max: 2 });
  assert.deepStrictEqual(SL.parseAmount('¼–½ tsp'), { quantity: 0.25, unit: 'tsp', max: 0.5 });
  // The word, as well as the dash -- thai-green-chicken-curry writes `~½ to 1`.
  assert.deepStrictEqual(
    SL.parseAmount('~½ to 1'), { quantity: 0.5, unit: '', max: 1, approx: true });
});

test('a hyphen inside a unit is not a range, and the unit survives', () => {
  // classic-masala-chai's ginger, and sticky-oxtail-stew's tomatoes. A looser
  // rule ate the hyphen and, worse, read the `400` as the top of a range.
  assert.deepStrictEqual(SL.parseAmount('2.5-cm piece'),
    { quantity: 2.5, unit: '-cm piece' });
  assert.deepStrictEqual(SL.parseAmount('2 x 400-g tins'),
    { quantity: 2, unit: 'x 400-g tin' });
  assert.deepStrictEqual(SL.parseAmount('2 x 400 g cans'),
    { quantity: 2, unit: 'x 400 g can' });
});

test('a range that runs backwards is not a range', () => {
  // Nothing writes one; the point is that the low end still comes back, rather
  // than the two ends crossing over inside a total.
  const parsed = SL.parseAmount('5–2 g');
  assert.strictEqual(parsed.quantity, 5);
  assert.strictEqual(parsed.max, undefined);
});

test('a tilde is carried, not swallowed', () => {
  assert.deepStrictEqual(SL.parseAmount('~2 tbsp'),
    { quantity: 2, unit: 'tbsp', approx: true });
  assert.deepStrictEqual(SL.parseAmount('~1'), { quantity: 1, unit: '', approx: true });
});

test('an ordinary plural unit folds, and comes back for the page', () => {
  // The ROUND TRIP is what matters: fold for the total, label for the page.
  // `1 clove` and `3 cloves` of garlic were two lines of one bulb before this.
  [['cloves', 'clove'], ['bunches', 'bunch'], ['handfuls', 'handful'],
    ['slices', 'slice'], ['inches', 'inch'], ['stalks', 'stalk'],
    ['x 400 g cans', 'x 400 g can']].forEach(function (pair) {
    assert.strictEqual(SL.foldUnit(pair[0]), pair[1], pair[0]);
    assert.strictEqual(SL.unitLabel(pair[1], 2), pair[0], pair[1]);
    assert.strictEqual(SL.unitLabel(pair[1], 1), pair[1], pair[1]);
  });
});

test('a compound unit pluralises its last word, and leaves a symbol alone', () => {
  assert.strictEqual(SL.unitLabel('heaped tbsp', 2), 'heaped tbsp');
  assert.strictEqual(SL.unitLabel('large head', 2), 'large heads');
  // Adjectives standing in for a noun have no plural: `8 mediums` was real.
  assert.strictEqual(SL.unitLabel('medium', 4), 'medium');
  assert.strictEqual(SL.unitLabel('small', 4), 'small');
  assert.strictEqual(SL.unitLabel('tsp', 3), 'tsp');
});

test('`ss` is never a plural', () => {
  assert.strictEqual(SL.foldUnit('glass'), 'glass');
  assert.strictEqual(SL.foldUnit('ml'), 'ml');
  assert.strictEqual(SL.foldUnit('oz'), 'oz');
});

test('a bracket that restates the quantity is split off the unit', () => {
  // chai-spice-powder and garam-masala-powder are written this way throughout.
  assert.deepStrictEqual(SL.splitParenthetical('tbsp (6 g)'),
    { unit: 'tbsp', lo: 6, hi: null, unit2: 'g' });
  assert.deepStrictEqual(SL.splitParenthetical('tbsp (9–10 g)'),
    { unit: 'tbsp', lo: 9, hi: 10, unit2: 'g' });
  assert.deepStrictEqual(SL.splitParenthetical('medium (1 g)'),
    { unit: 'medium', lo: 1, hi: null, unit2: 'g' });
});

test('a bracket with no number in it is not a restatement', () => {
  assert.deepStrictEqual(SL.splitParenthetical('(optional)'), { unit: '(optional)' });
  assert.deepStrictEqual(SL.splitParenthetical('ml'), { unit: 'ml' });
});

test('fractionText writes a number the way a cook would', () => {
  assert.strictEqual(SL.fractionText(2 / 3), '⅔');
  assert.strictEqual(SL.fractionText(1 / 3), '⅓');
  assert.strictEqual(SL.fractionText(1.5), '1½');
  assert.strictEqual(SL.fractionText(3 + 1 / 3), '3⅓');
  assert.strictEqual(SL.fractionText(2), '2');
  // NOTATION, NOT ROUNDING -- Helen, 2026-09-07. 0.7 is not two thirds, and is
  // never printed as one.
  assert.strictEqual(SL.fractionText(0.7), '0.7');
});

test('NOTHING THE COCKTAILS COLLECTION WRITES PARSES DIFFERENTLY', () => {
  // The claim that lets one parser serve both sites, written down so that the
  // next widening has to prove it too. These are the shapes the 682 pours are
  // actually in: plain decimals on the 2.5 ml grid, the counted units, the
  // whole fruit, and the two phrases that are not quantities at all.
  const unchanged = {
    '45 ml': { quantity: 45, unit: 'ml' },
    '22.5 ml': { quantity: 22.5, unit: 'ml' },
    '7.5 ml': { quantity: 7.5, unit: 'ml' },
    '2 dashes': { quantity: 2, unit: 'dash' },
    '1 dash': { quantity: 1, unit: 'dash' },
    '3 drops': { quantity: 3, unit: 'drop' },
    '2 cubes': { quantity: 2, unit: 'cube' },
    '8 leaves': { quantity: 8, unit: 'leaf' },
    '1 pinch': { quantity: 1, unit: 'pinch' },
    '1 sprig': { quantity: 1, unit: 'sprig' },
    '1 strip': { quantity: 1, unit: 'strip' },
    '9 each': { quantity: 9, unit: 'each' },
    '1 whole': { quantity: 1, unit: 'whole' },
    'half': { quantity: 0.5, unit: 'whole' },
    '60 g': { quantity: 60, unit: 'g' },
    '1': { quantity: 1, unit: '' }
  };
  Object.keys(unchanged).forEach(function (amount) {
    assert.deepStrictEqual(SL.parseAmount(amount), unchanged[amount], amount);
  });
  assert.strictEqual(SL.parseAmount('to top'), null);
  assert.strictEqual(SL.parseAmount('to rinse'), null);
});

// --- a declared top is a volume, #746 -----------------------------------------
// `to top (x3)` was the honest answer while nothing had told this file how much
// a top pours. `top_up_ml` in _data/cocktails/costs.yml now does, at Helen's
// request -- "We can calculate top volumes, well, slightly, can't we -- I'd
// like that to be captured actually so it can be added into the shopping list
// feature." So this is reading a declared number, not inventing a conversion,
// which is the same standing `juice_yields` has.
//
// THE REAL DECLARED VALUES, so a test failure means the behaviour moved rather
// than the fixture.

const TOP_UPS = {
  champagne: { ml_min: 75, ml_max: 100 },
  prosecco: { ml_min: 75, ml_max: 100 },
  'soda water': { ml_min: 100, ml_max: 150 }
};

test('a declared top becomes a volume range instead of a count', () => {
  const rows = SL.build([ing('to top', 'champagne')], { topUpMl: TOP_UPS });
  assert.strictEqual(rows[0].text, '75–100 ml');
  assert.deepStrictEqual(rows[0].unquantified, []);
});

test('both ends of the range scale, so three glasses is three tops', () => {
  const rows = SL.build([
    ing('to top', 'soda water'),
    ing('to top', 'soda water'),
    ing('to top', 'soda water')
  ], { topUpMl: TOP_UPS });
  // 3 x 100-150, not "to top (x3)" and not one top.
  assert.strictEqual(rows[0].text, '300–450 ml');
});

test('a fixed pour and a top on the same generic widen one total', () => {
  const rows = SL.build([
    ing('45 ml', 'champagne'),
    ing('to top', 'champagne')
  ], { topUpMl: TOP_UPS });
  assert.strictEqual(rows[0].text, '120–145 ml');
  assert.strictEqual(rows[0].millilitres, 120);
  assert.strictEqual(rows[0].millilitresMax, 145);
});

test('a generic with no declared top keeps the count reading', () => {
  // The honest fallback, and #746 asks for it explicitly. `tonic water` is not
  // in `top_up_ml`, so nothing here knows how much it pours.
  const rows = SL.build([
    ing('to top', 'tonic water'),
    ing('to top', 'tonic water')
  ], { topUpMl: TOP_UPS });
  assert.strictEqual(rows[0].text, 'to top (×2)');
});

test('only a top phrase converts, however well declared the generic is', () => {
  // `to rinse` on a generic that HAS a top_up_ml row must stay a count: the
  // declared volume is what a top pours, and a rinse is a different act.
  const rows = SL.build([ing('to rinse', 'champagne')], { topUpMl: TOP_UPS });
  assert.strictEqual(rows[0].text, 'to rinse');
  assert.strictEqual(rows[0].millilitres, 0);
});

test('a topped line sorts by volume now it has one', () => {
  // Before #746 a `to top` line had no millilitres at all and fell into the
  // alphabetical block below every measured pour. 300-450 ml of soda is one of
  // the largest things on the list and now sorts like it.
  const rows = SL.build([
    ing('45 ml', 'gin'),
    ing('to top', 'soda water'),
    ing('to top', 'soda water'),
    ing('to top', 'soda water')
  ], { topUpMl: TOP_UPS });
  assert.deepStrictEqual(labels(rows), ['soda water', 'gin']);
});

test('the top is not fruit: a squeezed count reads the fixed pour only', () => {
  // Nothing you squeeze is something you top, so this can never differ on real
  // data -- but counting lemons for a volume of champagne would be the wrong
  // answer if it ever did.
  const yields = { 'lemon juice': { fruit: 'lemon', ml_min: 30, ml_max: 40 } };
  const rows = SL.build([
    ing('60 ml', 'lemon juice'),
    ing('to top', 'lemon juice')
  ], { juiceYields: yields, topUpMl: { 'lemon juice': { ml_min: 75, ml_max: 100 } } });
  assert.strictEqual(rows[0].millilitres, 135);
  // 60 ml of juice, not 135: the fruit count ignores the top. 60/40 rounds up
  // to 2 lemons; 135 ml would have asked for 4.
  assert.strictEqual(rows[0].fruit.fewest, 2);
  assert.strictEqual(rows[0].fruit.most, 2);
});

test('amountRangeText collapses when the ends meet', () => {
  assert.strictEqual(SL.amountRangeText(75, 100, 'ml'), '75–100 ml');
  assert.strictEqual(SL.amountRangeText(100, 100, 'ml'), '100 ml');
  // Pluralised off the top of the range, the number the word agrees with.
  assert.strictEqual(SL.amountRangeText(1, 2, 'leaf'), '1–2 leaves');
});

test('an en dash, not a hyphen', () => {
  // House style, and the same dash costs.yml's own `basis` strings use.
  const rows = SL.build([ing('to top', 'champagne')], { topUpMl: TOP_UPS });
  assert.ok(rows[0].text.includes('–'), rows[0].text);
  assert.ok(!rows[0].text.includes('-'), rows[0].text);
});

// --- what a line costs, #820, and what the list costs, #817 -------------------
// GBP per litre, resolved at build time by _plugins/cocktail_costs.rb and handed
// over as a table. This file multiplies and never resolves: every rule about
// what a generic costs -- the union of declared bottles, `default_bottles`
// narrowing it, a squeezed juice priced from fruit and yield -- lives in the
// plugin, and a second copy here would be a second thing to keep in step.
//
// THE RATES ARE THE REAL ONES, checked against _data/cocktails/costs.yml on
// 2026-09-08, so a failure means behaviour moved rather than a fixture drifting.

const RATES = {
  generics: {
    'London dry gin': [31.43, 31.43],
    'lime juice': [6.0, 15.0],
    'moderately aged rum': [22.0, 40.0],
    mint: undefined
  },
  bottles: {
    Tanqueray: 31.43,
    Beefeater: 24.29,
    'Havana Club 7': 40.0
  }
};

test('a line is priced from its millilitres and a declared rate', () => {
  const rows = SL.build([ing('420 ml', 'London dry gin')], { rates: RATES });
  // 0.42 l x 31.43
  assert.strictEqual(rows[0].price.text, '£13.20');
  assert.strictEqual(rows[0].price.exact, true);
});

test('a generic that spans a range prices as a range', () => {
  const rows = SL.build([ing('500 ml', 'lime juice')], { rates: RATES });
  // 0.5 l x 6.00 to 0.5 l x 15.00
  assert.strictEqual(rows[0].price.text, '£3.00–£7.50');
});

test('the named bottles beat the generic when every one is priced', () => {
  // #820: "a range where suggested bottles are a range". Two drinks naming two
  // gins price cheapest to dearest across those two, not across the category.
  const rows = SL.build([
    ing('200 ml', 'London dry gin', 'Tanqueray'),
    ing('200 ml', 'London dry gin', 'Beefeater')
  ], { rates: RATES });
  // 0.4 l x 24.29 to 0.4 l x 31.43
  assert.strictEqual(rows[0].price.text, '£9.72–£12.57');
});

test('one unpriced bottle sends the whole line back to the generic', () => {
  // All or nothing on the named set: pricing from the priced ones only would
  // report a range narrower than the truth -- more certain for knowing less.
  const rows = SL.build([
    ing('200 ml', 'London dry gin', 'Tanqueray'),
    ing('200 ml', 'London dry gin', 'Some Undeclared Gin')
  ], { rates: RATES });
  assert.strictEqual(rows[0].price.text, '£12.57'); // the generic's rate
});

test('a generic with no rate carries no price, never a zero', () => {
  const rows = SL.build([ing('8 leaves', 'mint')], { rates: RATES });
  assert.strictEqual(rows[0].price, null);
});

test('a top-up range widens the price too', () => {
  // The two features meet: 3 x 100-150 ml of a generic priced 1.00-2.00 a litre
  // is 300-450 ml, so 30p to 90p.
  const rows = SL.build([
    ing('to top', 'soda water'),
    ing('to top', 'soda water'),
    ing('to top', 'soda water')
  ], {
    topUpMl: TOP_UPS,
    rates: { generics: { 'soda water': [1.0, 2.0] }, bottles: {} }
  });
  assert.strictEqual(rows[0].text, '300–450 ml');
  assert.strictEqual(rows[0].price.text, '£0.30–£0.90');
});

test('no rates at all means no prices, and everything else is unchanged', () => {
  const rows = SL.build([ing('420 ml', 'London dry gin')]);
  assert.strictEqual(rows[0].price, null);
  assert.strictEqual(rows[0].text, '420 ml');
});

test('the total is the sum of the lines above it', () => {
  const rows = SL.build([
    ing('420 ml', 'London dry gin'),
    ing('500 ml', 'lime juice')
  ], { rates: RATES });
  const sum = SL.total(rows);
  // 13.20 + 3.00, 13.20 + 7.50
  assert.strictEqual(sum.text, '£16.20–£20.70');
  assert.strictEqual(sum.priced, 2);
  assert.strictEqual(sum.unpriced, 0);
});

test('the total counts what it could not price, rather than hiding it', () => {
  // A bare figure would claim to be the cost of the shop and be short by
  // whatever the unpriced lines are worth.
  const rows = SL.build([
    ing('420 ml', 'London dry gin'),
    ing('8 leaves', 'mint')
  ], { rates: RATES });
  const sum = SL.total(rows);
  assert.strictEqual(sum.text, '£13.20');
  assert.strictEqual(sum.priced, 1);
  assert.strictEqual(sum.unpriced, 1);
});

test('a list with nothing priceable has no total at all', () => {
  const rows = SL.build([ing('8 leaves', 'mint')], { rates: RATES });
  assert.strictEqual(SL.total(rows), null);
});

test('moneyText collapses when the ends meet, and always shows pennies', () => {
  assert.strictEqual(SL.moneyText(13.2, 13.2), '£13.20');
  assert.strictEqual(SL.moneyText(3, 7.5), '£3.00–£7.50');
  // An en dash, like the drink page's own cost suffix.
  assert.ok(SL.moneyText(3, 7.5).includes('–'));
});

// --- shelf order, #848 --------------------------------------------------------
// Helen, 2026-09-08: "for cocktail shopping list, list items in shelf order then
// volume", with her own nine shelves. The order is a walk round the shop, so it
// is the OUTER sort key; the descending-volume rule she gave on 2026-09-04 is
// unchanged and now orders within a shelf.

const SHELVES = {
  order: ['spirits', 'fortified', 'liqueurs', 'freshly squeezed fruit juice',
          'bottled fruit juice', 'flavourings', 'sugar syrup', 'bitters', 'tops'],
  of: {
    'London dry gin': 'spirits',
    'moderately aged rum': 'spirits',
    'sweet vermouth': 'fortified',
    'triple sec': 'liqueurs',
    'lime juice': 'freshly squeezed fruit juice',
    'sugar syrup 2:1': 'sugar syrup',
    'aromatic bitters': 'bitters',
    'soda water': 'tops'
  }
};

test('shelf order beats volume, which is the whole of #848', () => {
  // By volume alone this is soda, gin, vermouth, lime, syrup, bitters. By shelf
  // the spirits lead and the soda goes last, however much of it there is.
  const rows = SHELVES && SL.build([
    ing('600 ml', 'soda water'),
    ing('120 ml', 'London dry gin'),
    ing('300 ml', 'sweet vermouth'),
    ing('90 ml', 'lime juice'),
    ing('60 ml', 'sugar syrup 2:1'),
    ing('4 dashes', 'aromatic bitters')
  ], { shelves: SHELVES });
  assert.deepStrictEqual(labels(rows), [
    'London dry gin', 'sweet vermouth', 'lime juice', 'sugar syrup 2:1',
    'aromatic bitters', 'soda water'
  ]);
});

test('within one shelf it is still descending volume', () => {
  const rows = SL.build([
    ing('30 ml', 'London dry gin'),
    ing('90 ml', 'moderately aged rum')
  ], { shelves: SHELVES });
  assert.deepStrictEqual(labels(rows), ['moderately aged rum', 'London dry gin']);
});

test('a generic on no shelf sorts last, never first', () => {
  // A gap in the data should be visible without being in the way.
  const rows = SL.build([
    ing('10 ml', 'something nobody has filed'),
    ing('30 ml', 'London dry gin')
  ], { shelves: SHELVES });
  assert.deepStrictEqual(labels(rows),
    ['London dry gin', 'something nobody has filed']);
});

test('the shelf is on the row, so a caller can group by it', () => {
  const rows = SL.build([ing('30 ml', 'London dry gin')], { shelves: SHELVES });
  assert.strictEqual(rows[0].shelf, 'spirits');
});

test('an unfiled generic carries a null shelf, not a guess', () => {
  const rows = SL.build([ing('30 ml', 'unfiled')], { shelves: SHELVES });
  assert.strictEqual(rows[0].shelf, null);
});

test('no shelves at all leaves the 2026-09-04 volume order alone', () => {
  // The guarantee that made this safe to land: every pre-#848 caller and test
  // describes what it always did.
  const rows = SL.build([
    ing('30 ml', 'London dry gin'),
    ing('600 ml', 'soda water')
  ]);
  assert.deepStrictEqual(labels(rows), ['soda water', 'London dry gin']);
});

test('no topUpMl at all leaves every existing answer alone', () => {
  // The guarantee that made this change safe to land: absent the option, this
  // file behaves exactly as it did before #746.
  const rows = SL.build([
    ing('to top', 'champagne'),
    ing('to top', 'champagne')
  ]);
  assert.strictEqual(rows[0].text, 'to top (×2)');
  assert.strictEqual(rows[0].millilitres, 0);
});
