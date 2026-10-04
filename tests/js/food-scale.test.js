// =============================================================================
// food-scale.js — one food amount at a factor. #1005
//
// Run from the repo root with `node --test`.
// =============================================================================
// Every expectation below is a rule Helen has already given for the shopping
// list (#801), because this module prints through the same formatter: grams
// to the gram, spoons in cook's fractions, ranges carried at both ends, the
// bracket scaled with its number. The only thing new is the shape -- one
// amount in, one amount out -- and the two answers at the edges: an amount
// with no number comes back as written and says so, and a kilogram halved
// comes back as grams.
'use strict';

const test = require('node:test');
const assert = require('node:assert');

const foodScale = require('../../assets/js/food-scale.js');
const { scaleAmount } = foodScale;

function at(amount, factor, options) {
  return scaleAmount(amount, factor, options).text;
}

test('grams scale to the gram, never coarser', () => {
  assert.strictEqual(at('200 g', 2), '400 g');
  assert.strictEqual(at('200 g', 2 / 3), '133 g');
  assert.strictEqual(at('200 g', 0.5), '100 g');
});

test('a kilogram halved is grams, and a kilogram kept is a kilogram', () => {
  assert.strictEqual(at('1.2 kg', 2), '2.4 kg');
  assert.strictEqual(at('1.2 kg', 0.5), '600 g');
  assert.strictEqual(at('600 g', 2), '1.2 kg');
});

test('spoons and counts print in cook\'s fractions', () => {
  assert.strictEqual(at('½ tsp', 2), '1 tsp');
  assert.strictEqual(at('½ tsp', 3), '1½ tsp');
  assert.strictEqual(at('1 tbsp', 2 / 3), '⅔ tbsp');
  assert.strictEqual(at('2', 1.5), '3');
});

test('"2 large" scales -- Helen: "Things like 2 large can scale, surely"', () => {
  assert.strictEqual(at('2 large', 2), '4 large');
  assert.strictEqual(at('1 large', 3), '3 large');
});

test('a range is carried at both ends', () => {
  assert.strictEqual(at('30–50 g', 2), '60–100 g');
});

test('a tilde survives', () => {
  assert.strictEqual(at('~2 tbsp', 2), '~4 tbsp');
});

test('a bracket that restates the quantity scales with it', () => {
  assert.strictEqual(at('1 tbsp (6 g)', 2), '2 tbsp (12 g)');
});

test('a compound unit keeps its plural', () => {
  assert.strictEqual(at('2 x 400 g cans', 2), '4 x 400 g cans');
  assert.strictEqual(at('3 cloves', 1 / 3), '1 clove');
});

test('an amount with no number comes back as written, and says so', () => {
  // The line the note under the control is built from -- Helen: "let's add a
  // note to bitters and handfuls".
  const r = scaleAmount('a few handfuls', 2);
  assert.strictEqual(r.text, 'a few handfuls');
  assert.strictEqual(r.scaled, false);
  assert.strictEqual(scaleAmount('some', 0.5).scaled, false);
  assert.strictEqual(scaleAmount('', 2).text, '');
});

// -----------------------------------------------------------------------------
// #1125 -- a measure taken by hand scales IN HALF STEPS, and the note names
// only what genuinely did not scale. Helen: "Currently some recipes scale 1
// handful to e.g. 1.17 handfuls, which is obvious nonsense." Then: 'If a
// recipe calls for "a handful of parsley", three orders of that recipe should
// call for "3 handfuls of parsley".' Then: "Handfuls can scale in half steps."
//
// THE LIST IS READ FROM THE REAL DATA FILE, not restated here, so a word taken
// out of _data/food/scaling.yml fails these by name. The file is a flat YAML
// list and node has no YAML parser; the reader below takes the `  - word`
// lines under the one key and nothing cleverer.
// -----------------------------------------------------------------------------
const fs = require('node:fs');
const path = require('node:path');

function yamlList(file, key) {
  const lines = fs.readFileSync(
    path.join(__dirname, '..', '..', '_data', 'food', file), 'utf8').split('\n');
  const start = lines.indexOf(key + ':');
  assert.notStrictEqual(start, -1, `${file} has no top-level ${key}: key`);
  const out = [];
  for (const line of lines.slice(start + 1)) {
    if (/^\S/.test(line) && !line.startsWith('#')) break;
    const item = /^\s+-\s+(.+?)\s*$/.exec(line);
    if (item) out.push(item[1]);
  }
  return out;
}

const WORDS = {
  halfStep: yamlList('scaling.yml', 'half_step_measures'),
  trailing: yamlList('ingredient_words.yml', 'trailing_phrases')
};

test('the two word lists were actually read', () => {
  assert.ok(WORDS.halfStep.includes('handful'), WORDS.halfStep.join());
  assert.ok(WORDS.trailing.includes('to taste'), WORDS.trailing.join());
});

test('three orders of a handful is three handfuls -- Helen\'s own example', () => {
  const r = scaleAmount('1 handful', 3, WORDS);
  assert.strictEqual(r.text, '3 handfuls');
  assert.strictEqual(r.scaled, true);
});

test('a handful never prints a fraction -- 1.17 handfuls is "obvious nonsense"', () => {
  // Seven portions of a recipe for six: the case in the issue. It SCALED -- to
  // the nearest half handful, which is the one it started with -- so it is
  // not named on the Not-scaled line.
  const r = scaleAmount('1 handful', 7 / 6, WORDS);
  assert.strictEqual(r.text, '1 handful');
  assert.strictEqual(r.scaled, true);
});

test('THE ROUNDING: the nearest half, and never less than a half', () => {
  // Helen, 2026-10-04: "Handfuls can scale in half steps." `halfStep` in
  // food-scale.js is the one function that decides this; this test is the one
  // to change with it.
  assert.strictEqual(at('1 handful', 1.5, WORDS), '1½ handfuls');
  assert.strictEqual(at('1 handful', 7 / 6, WORDS), '1 handful');
  assert.strictEqual(at('1 handful', 4 / 3, WORDS), '1½ handfuls');
  assert.strictEqual(at('1 handful', 1.2, WORDS), '1 handful');
  assert.strictEqual(at('2 handfuls', 2 / 3, WORDS), '1½ handfuls');
  assert.strictEqual(at('2 handfuls', 7 / 6, WORDS), '2½ handfuls');
  assert.strictEqual(at('2 handfuls', 1.1, WORDS), '2 handfuls');
  // Two thirds is nearer a half than one; a twelfth still leaves a half.
  assert.strictEqual(at('1 handful', 2 / 3, WORDS), '½ handfuls');
  assert.strictEqual(at('1 handful', 1 / 12, WORDS), '½ handfuls');
  assert.strictEqual(foodScale.halfStep(1.17), 1);
  assert.strictEqual(foodScale.halfStep(0.1), 0.5);
  assert.strictEqual(foodScale.halfStep(1.25), 1.5);
});

test('THE PLURAL is the site\'s existing rule: singular at exactly one, plural otherwise', () => {
  // Not a rule invented for handfuls. A unit that is NOT on the list already
  // prints this way through shopping-list.js's `unitLabel`, and the half-step
  // measures match it -- so "½ handfuls" reads as "½ pats" does. If Helen
  // wants "½ handful", the change is in `unitLabel`, for every unit at once.
  assert.strictEqual(at('1 pat', 0.5, WORDS), '½ pats');
  assert.strictEqual(at('1 pat', 1.5, WORDS), '1½ pats');
  assert.strictEqual(at('1 handful', 0.5, WORDS), '½ handfuls');
  assert.strictEqual(at('1 handful', 1.5, WORDS), '1½ handfuls');
  assert.strictEqual(at('1 pinch', 0.5, WORDS), '½ pinches');
  assert.strictEqual(at('2 handfuls', 0.5, WORDS), '1 handful');
});

test('every way the collection writes a hand measure scales, plural and all', () => {
  // Each of these is a real `amount:` in _food_recipes/ or _food_drafts/.
  const cases = {
    '1 handful': '3 handfuls',
    '2 handfuls': '6 handfuls',
    '1 small handful': '3 small handfuls',
    '1 large handful each': '3 large handfuls each',
    '1 small handful each': '3 small handfuls each',
    '1 pinch': '3 pinches',
    '1 splash': '3 splashes',
    '1 knob': '3 knobs'
  };
  Object.keys(cases).forEach((amount) => {
    const r = scaleAmount(amount, 3, WORDS);
    assert.strictEqual(r.text, cases[amount]);
    assert.strictEqual(r.scaled, true, amount);
  });
});

test('a plural comes back to the singular at one', () => {
  assert.strictEqual(at('2 pinches', 0.5, WORDS), '1 pinch');
  assert.strictEqual(at('3 dashes', 1 / 3, WORDS), '1 dash');
  assert.strictEqual(at('2 splashes', 0.5, WORDS), '1 splash');
});

test('a range and a tilde survive the whole step', () => {
  assert.strictEqual(at('1–2 handfuls', 3, WORDS), '3–6 handfuls');
  assert.strictEqual(at('~1 handful', 3, WORDS), '~3 handfuls');
  assert.strictEqual(at('1–2 handfuls', 0.5, WORDS), '½–1 handful');
  // Both ends landing on the same step is one number, not "½–½".
  assert.strictEqual(at('1–2 handfuls', 0.1, WORDS), '½ handfuls');
});

test('an amount that is only the measure counts as one of it', () => {
  // Real draft amounts: `amount: "pinch"`, `"dash"`, `"a handful"`,
  // `"small handful"`. No digit, but a singular measure is one.
  assert.strictEqual(at('pinch', 3, WORDS), '3 pinches');
  assert.strictEqual(at('dash', 2, WORDS), '2 dashes');
  assert.strictEqual(at('a handful', 3, WORDS), '3 handfuls');
  assert.strictEqual(at('small handful', 3, WORDS), '3 small handfuls');
  // At a factor that rounds back to one, the recipe's own words stand.
  assert.strictEqual(at('a handful', 7 / 6, WORDS), 'a handful');
  assert.strictEqual(scaleAmount('a handful', 7 / 6, WORDS).scaled, true);
  // "a few" is not a number. Unscaled, and named on the line.
  assert.strictEqual(scaleAmount('a few handfuls', 3, WORDS).scaled, false);
  assert.strictEqual(scaleAmount('a few sprigs each', 3, WORDS).scaled, false);
  assert.strictEqual(scaleAmount('some', 3, WORDS).scaled, false);
});

test('the measure is a whole word, so nothing else is caught by it', () => {
  // `dash` must not step a dashi sachet, nor `pinch` a pinchos stick: a third
  // of three would read "1" either way, but two thirds of one would read "½".
  assert.strictEqual(at('1 pinchos', 2 / 3, WORDS), '⅔ pinchos');
  assert.strictEqual(at('1 dashi sachet', 2 / 3, WORDS), '⅔ dashi sachets');
  assert.strictEqual(at('200 g', 2, WORDS), '400 g');
});

// --- the measure written into the item, with no amount at all -----------------

test('"a handful of fresh parsley" x3 is "3 handfuls of fresh parsley"', () => {
  // Helen's sentence, as a test. 96 items in the two collections open this way.
  const { scaleLeadingMeasure } = foodScale;
  const r = scaleLeadingMeasure('a handful of fresh parsley', 3, WORDS);
  assert.strictEqual(r.text, '3 handfuls of fresh parsley');
  assert.strictEqual(r.scaled, true);
});

test('a leading measure: a, an, one or nothing is ONE, and a size word is kept', () => {
  const lead = (text, f) => foodScale.scaleLeadingMeasure(text, f, WORDS).text;
  // Real `item:` lines.
  assert.strictEqual(lead('pinch of salt', 3), '3 pinches of salt');
  assert.strictEqual(lead('a good pinch of salt', 2), '2 good pinches of salt');
  assert.strictEqual(lead('A large handful of fresh coriander, to serve', 3),
    '3 large handfuls of fresh coriander, to serve');
  assert.strictEqual(lead('small handful of parsley, roughly chopped', 2),
    '2 small handfuls of parsley, roughly chopped');
  assert.strictEqual(lead('knob of butter, for the tin', 2), '2 knobs of butter, for the tin');
  assert.strictEqual(lead('a splash of lime juice', 4), '4 splashes of lime juice');
  assert.strictEqual(lead('one handful of rocket', 2), '2 handfuls of rocket');
  // A digit counts as itself.
  assert.strictEqual(lead('2 handfuls of rocket', 2), '4 handfuls of rocket');
  // The page's text node starts with the template's own whitespace; kept.
  assert.strictEqual(lead('\n            a handful of mint, chopped\n', 3),
    '\n            3 handfuls of mint, chopped\n');
});

test('at one, a leading measure keeps the recipe\'s own words', () => {
  const r = foodScale.scaleLeadingMeasure('a handful of fresh parsley', 7 / 6, WORDS);
  assert.strictEqual(r.text, 'a handful of fresh parsley');
  assert.strictEqual(r.scaled, true, 'it scaled, to the one it started with');
  // Anything but one is a number, in the same glyphs the amounts use.
  assert.strictEqual(
    foodScale.scaleLeadingMeasure('a handful of fresh parsley', 2 / 3, WORDS).text,
    '½ handfuls of fresh parsley');
  assert.strictEqual(
    foodScale.scaleLeadingMeasure('a handful of fresh parsley', 1.5, WORDS).text,
    '1½ handfuls of fresh parsley');
});

test('"a few" is not a number: Tabasco stays as written and is named', () => {
  // Helen's other example. It must come back unscaled so the page lists it.
  const { scaleLeadingMeasure, noteName } = foodScale;
  const tabasco = 'a few dashes of Tabasco sauce to taste';
  const r = scaleLeadingMeasure(tabasco, 3, WORDS);
  assert.strictEqual(r.text, tabasco);
  assert.strictEqual(r.scaled, false);
  assert.strictEqual(noteName(tabasco, WORDS), 'Tabasco sauce');

  ['a few handfuls of wild rocket leaves', 'some handfuls of rocket',
    'a couple of handfuls of rocket', 'several pinches of salt',
    'handfuls of rocket', 'a handfuls of rocket'].forEach((text) => {
    assert.strictEqual(scaleLeadingMeasure(text, 3, WORDS).scaled, false, text);
  });
});

test('an item that does not open with a whole measure is not touched', () => {
  const { scaleLeadingMeasure } = foodScale;
  ['salt, to taste', 'cream of tartar', 'a pat of salted butter, to finish',
    'a glass of robust red wine', 'fresh parsley, a handful of it',
    'handful fresh parsley', ''].forEach((text) => {
    const r = scaleLeadingMeasure(text, 3, WORDS);
    assert.strictEqual(r.text, text);
    assert.strictEqual(r.scaled, false, text);
  });
  // No list, no scaling: the caller that hands nothing over changes nothing.
  assert.strictEqual(scaleLeadingMeasure('a handful of parsley', 3).scaled, false);
});

test('"2 large" still scales with the list in hand', () => {
  // Helen, #1005: "Things like '2 large' can scale, surely". scaling.yml says
  // why a size word must never join the list; this is what would notice.
  assert.strictEqual(scaleAmount('2 large', 2, WORDS).text, '4 large');
  assert.strictEqual(scaleAmount('4 medium', 0.5, WORDS).text, '2 medium');
  assert.strictEqual(scaleAmount('1 small', 3, WORDS).text, '3 small');
});

test('counts of things you can pick up scale -- Helen: "4 sprigs double is 8, and so on"', () => {
  // RULED, 2026-10-04, not merely left: sprig, bunch, drop, twist and lot are
  // absent from scaling.yml on her word. Each amount is a real one.
  assert.strictEqual(scaleAmount('4 sprigs', 2, WORDS).text, '8 sprigs');
  assert.strictEqual(scaleAmount('1 bunch', 2, WORDS).text, '2 bunches');
  assert.strictEqual(scaleAmount('3–4 drops', 2, WORDS).text, '6–8 drops');
  assert.strictEqual(scaleAmount('5 twists', 2, WORDS).text, '10 twists');
  assert.strictEqual(scaleAmount('2 lots', 2, WORDS).text, '4 lots');
});

test('a pat scales, and reads "pats" -- Helen: "scaled linearly as pats"', () => {
  // `pat` was in the list for a few hours and came out on her word: '"pat" is
  // a correct term, and should be scaled linearly as "pats"'.
  assert.ok(!WORDS.halfStep.includes('pat'), 'pat is back in scaling.yml');
  assert.strictEqual(scaleAmount('2 pats', 2 / 3, WORDS).text, '1⅓ pats');
  assert.strictEqual(scaleAmount('1 pat', 2, WORDS).text, '2 pats');
  assert.strictEqual(scaleAmount('2 pats', 2, WORDS).text, '4 pats');
  assert.strictEqual(scaleAmount('2 pats', 0.5, WORDS).text, '1 pat');
  // The size word stays where it was: pan-seared venison's own amount.
  assert.strictEqual(scaleAmount('2 large pats', 2, WORDS).text, '4 large pats');
  assert.strictEqual(scaleAmount('2 large pats', 0.5, WORDS).text, '1 large pat');
  assert.strictEqual(scaleAmount('2 pats', 2, WORDS).scaled, true);
});

test('the index shopping list totals a handful linearly, and is NOT half-stepped', () => {
  // `half_step_measures` is the RECIPE PAGE's rule. The shortlist's shopping
  // list has its own totalling in food-shopping-list.js and does not go
  // through `halfStep`; it was left alone and reported. The whole-number cases
  // are pinned so that a later change there is a decision, not a drift.
  const FSL = require('../../assets/js/food-shopping-list.js');
  const row = (amount, scale) => FSL.build(
    [{ amount: amount, name: 'fresh flat-leaf parsley', aisle: 'produce', scale: scale }],
    { aisles: [{ key: 'produce', label: 'Produce' }] })[0].items[0].text;
  assert.strictEqual(row('1 handful', 2), '2 handfuls');
  assert.strictEqual(row('2 handfuls', 0.5), '1 handful');
  assert.strictEqual(row('1 small handful', 2), '2 small handfuls');
  // WHAT A FRACTION OF A HANDFUL PRINTS IS DELIBERATELY NOT PINNED. Today it
  // is "⅔ handfuls" (the plural follows any number that is not exactly 1) and
  // "1.17 handfuls" at seven for six; both were reported to Helen rather than
  // decided here, so no assertion freezes either answer.
});

test('with no list given, a handful scales as it did before #1125', () => {
  // The list is passed in, never assumed: a caller that hands none over gets
  // the old linear arithmetic rather than a guess at what the data says.
  assert.strictEqual(at('1 handful', 7 / 6), '1.17 handfuls');
  assert.strictEqual(at('1 handful', 7 / 6, {}), '1.17 handfuls');
  assert.strictEqual(at('1 handful', 7 / 6, { halfStep: [] }), '1.17 handfuls');
});

test('the note names the ingredient -- Helen\'s Tabasco example, verbatim', () => {
  const { noteName } = foodScale;
  // "few dashes of Tabasco sauce to taste, unless feeding Helen" ->
  // "Not scaled: Tabasco sauce"
  assert.strictEqual(
    noteName('few dashes of Tabasco sauce to taste, unless feeding Helen', WORDS),
    'Tabasco sauce');
});

test('the note name drops the preparation and the aside', () => {
  const { noteName } = foodScale;
  // Real `item:` lines, as the row prints them once the amount is taken out.
  assert.strictEqual(noteName('fresh flat-leaf parsley, chopped', WORDS),
    'fresh flat-leaf parsley');
  assert.strictEqual(noteName('paprika, unless feeding Helen', WORDS), 'paprika');
  assert.strictEqual(noteName('coriander, torn (optional)', WORDS), 'coriander');
  assert.strictEqual(noteName('milk (any kind), to glaze', WORDS), 'milk');
  assert.strictEqual(noteName('salt, to taste', WORDS), 'salt');
  assert.strictEqual(noteName('lemongrass paste to taste', WORDS), 'lemongrass paste');
  assert.strictEqual(noteName('  sultanas \n ', WORDS), 'sultanas');
});

test('the note name drops a measure written into the item', () => {
  const { noteName } = foodScale;
  assert.strictEqual(noteName('a few dashes of Tabasco sauce to taste', WORDS),
    'Tabasco sauce');
  assert.strictEqual(noteName('a few handfuls of wild rocket leaves', WORDS),
    'wild rocket leaves');
  assert.strictEqual(noteName('A large handful of fresh coriander, to serve', WORDS),
    'fresh coriander');
  assert.strictEqual(noteName('a good pinch of salt', WORDS), 'salt');
  assert.strictEqual(noteName('pinch of salt', WORDS), 'salt');
  // `pat` is not a declared measure (it scales), so its phrase is left alone.
  assert.strictEqual(noteName('a pat of salted butter, to finish', WORDS),
    'a pat of salted butter');
});

test('"of" inside a name is not a measure phrase', () => {
  // ingredient_words.yml's own trap: stripping up to any "of" would hand back
  // "tartar" and "soda". Only a DECLARED measure before the "of" is cut.
  const { noteName } = foodScale;
  assert.strictEqual(noteName('cream of tartar', WORDS), 'cream of tartar');
  assert.strictEqual(noteName('bicarbonate of soda', WORDS), 'bicarbonate of soda');
  assert.strictEqual(noteName('a glass of robust red wine, preferably Cab or Merlot', WORDS),
    'a glass of robust red wine');
});

test('a note name is never cut to nothing', () => {
  const { noteName } = foodScale;
  assert.strictEqual(noteName('to taste', WORDS), 'to taste');
  assert.strictEqual(noteName('(optional) capers', WORDS), '(optional) capers');
  assert.strictEqual(noteName('', WORDS), '');
  assert.strictEqual(noteName('sea salt, to taste'), 'sea salt');
});

test('a scaled amount says it moved', () => {
  assert.strictEqual(scaleAmount('200 g', 2).scaled, true);
});

test('a factor that is not a positive number leaves the amount alone', () => {
  assert.strictEqual(scaleAmount('200 g', 0).text, '200 g');
  assert.strictEqual(scaleAmount('200 g', NaN).scaled, false);
});
