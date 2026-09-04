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
