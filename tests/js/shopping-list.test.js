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

test('one bottle named by every entry: the bottle leads, generic as the note', () => {
  const rows = SL.build([
    ing('30 ml', 'aromatic bitters', 'Angostura'),
    ing('2 dashes', 'aromatic bitters', 'Angostura')
  ]);
  assert.strictEqual(rows[0].label, 'Angostura');
  assert.strictEqual(rows[0].note, 'aromatic bitters');
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
  assert.strictEqual(rows[0].bottles.length, 1, 'one bottle, written two ways');
  assert.strictEqual(rows[0].label, "Woodford's Reserve");
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
  assert.strictEqual(rows[0].label, 'Patrón Silver or Tapatio');
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

test('rows come back sorted by their label, case-insensitively', () => {
  const rows = SL.build([
    ing('10 ml', 'rum'), ing('10 ml', 'Angostura'), ing('10 ml', 'benedictine')
  ]);
  assert.deepStrictEqual(labels(rows), ['Angostura', 'benedictine', 'rum']);
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
  assert.strictEqual(rows[0].bottles.length, 1, 'one bottle, written two ways');
  assert.strictEqual(rows[0].label, 'El Dorado 3', 'and the bottle may now lead');
  assert.strictEqual(rows[0].text, '60 ml');
});

test('each alternative of a list suggestion resolves on its own', () => {
  const rows = SL.build([ing('30 ml', 'rum', ['ED3', 'Havana Club 3'])], {
    bottleAliases: { ed3: 'El Dorado 3', 'havana club 3': 'Havana 3' }
  });
  assert.strictEqual(rows[0].label, 'El Dorado 3 or Havana 3');
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

test('a unanimous list suggestion still keeps its "or" in the label', () => {
  // The note flattens; the label must not. "El Dorado 3 or Havana Club 3" is
  // Helen's own wording for a choice she is happy with (#441), and where it is
  // the only suggestion in the group it is what the line should be called.
  const rows = SL.build([
    ing('30 ml', 'rum', ['El Dorado 3', 'Havana Club 3']),
    ing('30 ml', 'rum', ['El Dorado 3', 'Havana Club 3'])
  ]);
  assert.strictEqual(rows[0].label, 'El Dorado 3 or Havana Club 3');
  assert.strictEqual(rows[0].note, 'rum');
});

test('with no alias map the fold is still the answer, and nothing throws', () => {
  const rows = SL.build([ing('30 ml', 'rum', 'ED3')]);
  assert.strictEqual(rows[0].label, 'ED3');
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
