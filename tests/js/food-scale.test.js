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
  // Both half-step lists as one, which is how _layouts/recipe.html joins them.
  halfStep: yamlList('scaling.yml', 'half_step_measures')
    .concat(yamlList('scaling.yml', 'half_step_counts')),
  quarterStep: yamlList('scaling.yml', 'quarter_step_measures'),
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
  ['salt, to taste', 'cream of tartar', 'a slab of salted butter, to finish',
    'a glass of robust red wine', 'fresh parsley, a handful of it',
    'handful fresh parsley', ''].forEach((text) => {
    const r = scaleLeadingMeasure(text, 3, WORDS);
    assert.strictEqual(r.text, text);
    assert.strictEqual(r.scaled, false, text);
  });
  // No list, no scaling: the caller that hands nothing over changes nothing.
  assert.strictEqual(scaleLeadingMeasure('a handful of parsley', 3).scaled, false);
  // A pat IS a stepped measure since 2026-10-10, so one written into the item
  // scales like a handful written there: it was left alone until then.
  assert.strictEqual(
    scaleLeadingMeasure('a pat of salted butter, to finish', 3, WORDS).text,
    '3 pats of salted butter, to finish');
});

test('"2 large" still scales with the list in hand', () => {
  // Helen, #1005: "Things like '2 large' can scale, surely". scaling.yml says
  // why a size word must never join the list; this is what would notice.
  assert.strictEqual(scaleAmount('2 large', 2, WORDS).text, '4 large');
  assert.strictEqual(scaleAmount('4 medium', 0.5, WORDS).text, '2 medium');
  assert.strictEqual(scaleAmount('1 small', 3, WORDS).text, '3 small');
});

test('counts of things you can pick up scale -- Helen: "4 sprigs double is 8, and so on"', () => {
  // RULED, 2026-10-04, not merely left: drop, twist and lot are absent from
  // both step lists on her word. Sprig and bunch still double to 8 and 2; what
  // changed for them on 2026-10-10 is the fractions, in the test below.
  assert.strictEqual(scaleAmount('4 sprigs', 2, WORDS).text, '8 sprigs');
  assert.strictEqual(scaleAmount('1 bunch', 2, WORDS).text, '2 bunches');
  assert.strictEqual(scaleAmount('3–4 drops', 2, WORDS).text, '6–8 drops');
  assert.strictEqual(scaleAmount('5 twists', 2, WORDS).text, '10 twists');
  assert.strictEqual(scaleAmount('2 lots', 2, WORDS).text, '4 lots');
});

test('a sprig and a bunch go to the nearest quarter, in fractions -- never 1.17', () => {
  // Helen, 2026-10-10, shown "1.17 sprigs" and "1.17 bunches" at seven for
  // six: "Sprigs: Let's round to 1/4 please, and express in fractions not
  // decimals."
  assert.deepStrictEqual(WORDS.quarterStep, ['sprig', 'bunch']);
  assert.strictEqual(scaleAmount('1 sprig', 7 / 6, WORDS).text, '1¼ sprigs');
  assert.strictEqual(scaleAmount('1 bunch', 7 / 6, WORDS).text, '1¼ bunches');
  assert.strictEqual(scaleAmount('1 sprig', 2 / 3, WORDS).text, '¾ sprigs');
  assert.strictEqual(scaleAmount('1 sprig', 4 / 3, WORDS).text, '1¼ sprigs');
  assert.strictEqual(scaleAmount('3 sprigs', 0.5, WORDS).text, '1½ sprigs');
  assert.strictEqual(scaleAmount('2 sprigs', 0.5, WORDS).text, '1 sprig');
  assert.strictEqual(scaleAmount('1 sprig', 0.1, WORDS).text, '¼ sprigs',
    'never less than a quarter');
  assert.strictEqual(scaleAmount('2 large sprigs', 7 / 6, WORDS).text, '2¼ large sprigs');
  assert.strictEqual(scaleAmount('2–3 sprigs', 7 / 6, WORDS).text, '2¼–3½ sprigs');
  // Nothing printed for either measure is ever a decimal.
  [7 / 6, 5 / 6, 2 / 3, 1.1, 0.37, 3.3].forEach((factor) => {
    ['1 sprig', '3 sprigs', '1 bunch', '2 small bunches'].forEach((amount) => {
      assert.ok(!/\d\.\d/.test(scaleAmount(amount, factor, WORDS).text),
        amount + ' x' + factor + ' -> ' + scaleAmount(amount, factor, WORDS).text);
    });
  });
  // A twist is a half-step count, not a quarter one (the test below).
  assert.strictEqual(scaleAmount('5 twists', 2 / 3, WORDS).text, '3½ twists');
  // And handed no list, a sprig scales as it did before.
  assert.strictEqual(scaleAmount('1 sprig', 4 / 3, {}).text, '1⅓ sprigs');
});

test('drops, twists, lots and pats step in halves -- Helen: "round to the nearest 1/2"', () => {
  // 2026-10-10: "Drops, twists, lots etc, please round to the nearest 1/2 --
  // these are smaller than handfuls and sprigs." It replaces "scaled linearly"
  // (2026-10-04) for the four, `pat` among them.
  assert.deepStrictEqual(yamlList('scaling.yml', 'half_step_counts'),
    ['drop', 'twist', 'lot', 'pat']);
  assert.strictEqual(scaleAmount('5 twists', 2 / 3, WORDS).text, '3½ twists');
  assert.strictEqual(scaleAmount('2 pats', 2 / 3, WORDS).text, '1½ pats');
  assert.strictEqual(scaleAmount('3–4 drops', 7 / 6, WORDS).text, '3½–4½ drops');
  assert.strictEqual(scaleAmount('1 lot', 7 / 6, WORDS).text, '1 lot');
  assert.strictEqual(scaleAmount('1 drop', 0.1, WORDS).text, '½ drops');
  // Whole multiples are what they always were.
  assert.strictEqual(scaleAmount('1 pat', 2, WORDS).text, '2 pats');
  assert.strictEqual(scaleAmount('2 pats', 0.5, WORDS).text, '1 pat');
  assert.strictEqual(scaleAmount('2 large pats', 2, WORDS).text, '4 large pats');
  assert.strictEqual(scaleAmount('2 large pats', 0.5, WORDS).text, '1 large pat');
  assert.strictEqual(scaleAmount('2 pats', 2, WORDS).scaled, true);
});

test('the index shopping list buys whole ones, and does NOT borrow this page\'s half step', () => {
  // The same measures, two jobs. This page says what to USE, a handful in
  // halves; the shortlist's shopping list says what to BUY, the next whole
  // one, with the amount asked for in brackets to the nearest QUARTER --
  // Helen, 2026-10-10: "2 handfuls fresh parsley (1 1/4 in the recipes)", and
  // then "1.17 handfuls should buy 2".
  const FSL = require('../../assets/js/food-shopping-list.js');
  const row = (amount, scale) => {
    const item = FSL.build(
      [{ amount: amount, name: 'fresh flat-leaf parsley', aisle: 'produce', scale: scale }],
      { aisles: [{ key: 'produce', label: 'Produce' }],
        wholeMeasures: WORDS.halfStep, quarterMeasures: WORDS.quarterStep })[0].items[0];
    return item.text + (item.aside ? ' (' + item.aside + ')' : '');
  };
  assert.strictEqual(row('1 handful', 2), '2 handfuls');
  assert.strictEqual(row('2 handfuls', 0.5), '1 handful');
  assert.strictEqual(row('1 small handful', 2), '2 small handfuls');
  // Seven portions of a recipe for six: one handful here, two to buy there.
  assert.strictEqual(scaleAmount('1 handful', 7 / 6, WORDS).text, '1 handful');
  assert.strictEqual(row('1 handful', 7 / 6), '2 handfuls (1¼ in the recipes)');
  assert.strictEqual(row('1 handful', 1.5), '2 handfuls (1½ in the recipes)');
  // A sprig is in quarters on both, so the bracket is this page's figure.
  assert.strictEqual(scaleAmount('1 sprig', 7 / 6, WORDS).text, '1¼ sprigs');
  assert.strictEqual(row('1 sprig', 7 / 6), '2 sprigs (1¼ in the recipes)');
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
  // `pat` is a declared measure since 2026-10-10, so its phrase goes too.
  assert.strictEqual(noteName('a few pats of salted butter, to finish', WORDS),
    'salted butter');
  // A word that is on neither list is left alone.
  assert.strictEqual(noteName('a slab of salted butter, to finish', WORDS),
    'a slab of salted butter');
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

// -----------------------------------------------------------------------------
// #1286 -- on a `makes:` recipe the box counts THE THING MADE. Helen: "Never
// tell me how many cookies are in a portion!!!" and "Take the midpoint".
//
// THE SPECS BELOW ARE WHAT _plugins/food_yield.rb RETURNS for the real line
// named beside each (tests/test_food_yield.py pins that half). This file is
// the other half: what a press of plus does, and what the box and the word
// after it say.
// -----------------------------------------------------------------------------
const { yieldMode, portionsMode } = foodScale;

/** Press plus or minus `presses` times from `from`, as recipe-scale.js does. */
function press(mode, from, delta, presses) {
  let n = from;
  for (let i = 0; i < (presses || 1); i += 1) n = mode.clamp(mode.step(n, delta));
  return n;
}

/** The control as it reads: the box, then the word. */
function reads(mode, n) {
  return mode.box(n) + ' ' + mode.word(n);
}

// "4–6 waffles, depending on your waffle iron" -- Henry's Sunday Waffles.
// BASE 4, THE LOWER NUMBER, SINCE 2026-10-07 (Helen: "lower number please, new
// ruling"); it was 5, the midpoint, for the three days before.
const WAFFLES = { kind: 'count', base: 4, stem: 'waffles', rest: '',
  invariable: false, singular: false, times: false, plus: false };

test('#1286: the waffles step in WHOLE RECIPES -- 4 waffles, 8 waffles, 12', () => {
  // Helen: "the buttons should still multiply the recipe in integers, just
  // showing number of waffles. So 1x is 5 waffles, 2x is 10 waffles.
  // Otherwise we'll need to start showing eggs in units of 1/27". (Her fives
  // are the midpoint's; the stepping is the ruling, and it is unchanged.)
  const mode = yieldMode(WAFFLES);
  assert.strictEqual(mode.base, 4);
  assert.strictEqual(reads(mode, mode.base), '4 waffles');
  assert.strictEqual(reads(mode, press(mode, 4, 1)), '8 waffles');
  assert.strictEqual(reads(mode, press(mode, 4, 1, 2)), '12 waffles');
  // The ingredients scale by a whole number, always.
  assert.strictEqual(press(mode, 4, 1) / mode.base, 2);
  assert.strictEqual(press(mode, 4, 1, 2) / mode.base, 3);
  assert.strictEqual(reads(mode, press(mode, 8, -1)), '4 waffles');
});

test('#1286: a typed figure goes to the nearest whole recipe, and never to a part of one', () => {
  // The box shows a derived figure, so what is typed is a request, not a
  // value: 7 waffles is nearer two recipes than one. Helen: "not having half
  // recipes in between integers" -- 5 or 7 waffles is never x1½.
  const mode = yieldMode(WAFFLES);
  assert.strictEqual(mode.clamp(7), 8);
  assert.strictEqual(mode.clamp(5), 4);
  assert.strictEqual(mode.clamp(9), 8);
  assert.strictEqual(mode.clamp(11), 12);
  [5, 6, 7, 9, 10, 11, 13, 14, 23].forEach((typed) => {
    const multiple = mode.clamp(typed) / mode.base;
    assert.strictEqual(multiple, Math.round(multiple), `typing ${typed} gave x${multiple}`);
  });
});

test('#1286: a figure on a half is a range of one -- "5–6", then "11", then "16–17"', () => {
  // Helen: "Midpoints that land on a half can become a range of one."
  // "4–7 buns" is 5.5. Nothing published is this shape; the rule is hers.
  const mode = yieldMode({ kind: 'count', base: 5.5, stem: 'buns', rest: '',
    invariable: false, singular: false, times: false, plus: false });
  assert.strictEqual(reads(mode, mode.base), '5–6 buns');
  assert.strictEqual(reads(mode, press(mode, 5.5, 1)), '11 buns');
  assert.strictEqual(reads(mode, press(mode, 5.5, 1, 2)), '16–17 buns');
  assert.strictEqual(press(mode, 5.5, 1) / mode.base, 2);
  assert.strictEqual(foodScale.yieldBox(5.5), '5–6');
  assert.strictEqual(foodScale.yieldBox(5), '5');
});

test('#1286: "64+" keeps its plus -- 64+ tiny macarons, 128+ tiny macarons', () => {
  // Helen's own words, replacing her earlier '"64+" can be treated as "64"'.
  const mode = yieldMode({ kind: 'count', base: 64, stem: 'tiny macarons', rest: '',
    invariable: false, singular: false, times: false, plus: true });
  assert.strictEqual(reads(mode, mode.base), '64+ tiny macarons');
  assert.strictEqual(reads(mode, press(mode, 64, 1)), '128+ tiny macarons');
  assert.strictEqual(reads(mode, press(mode, 64, 1, 2)), '192+ tiny macarons');
});

test('#1286: "one 8-inch cake" is one; two read "2 × 8-inch cakes"', () => {
  // Helen: "Two 8-inch cakes". A digit straight before "8-inch" is
  // unreadable and the box is a number, so a × stands between them.
  const mode = yieldMode({ kind: 'count', base: 1, stem: '8-inch cake', rest: '',
    invariable: false, singular: true, times: true, plus: false });
  assert.strictEqual(reads(mode, mode.base), '1 × 8-inch cake');
  assert.strictEqual(reads(mode, press(mode, 1, 1)), '2 × 8-inch cakes');
  assert.strictEqual(reads(mode, press(mode, 2, -1)), '1 × 8-inch cake');
  assert.strictEqual(press(mode, 1, 1) / mode.base, 2);

  const pie = yieldMode({ kind: 'count', base: 1, stem: 'pie', rest: '',
    invariable: false, singular: true, times: false, plus: false });
  assert.strictEqual(reads(pie, 1), '1 pie');
  assert.strictEqual(reads(pie, 3), '3 pies');
});

test('#1286: a dozen stays a dozen -- "1 dozen" doubled is "2 dozen"', () => {
  // Helen: '"1 dozen" doubled can be "two dozen". Our scaler is integer.'
  const mode = yieldMode({ kind: 'count', base: 1, stem: 'dozen mince pies', rest: '',
    invariable: true, singular: true, times: false, plus: false });
  assert.strictEqual(reads(mode, mode.base), '1 dozen mince pies');
  assert.strictEqual(reads(mode, press(mode, 1, 1)), '2 dozen mince pies');
  assert.strictEqual(press(mode, 1, 1) / mode.base, 2);
});

test('#1286: a yield written with "of" carries the rest along', () => {
  // grandmas-scones: "2 large rounds of 4". Two recipes make four rounds.
  const mode = yieldMode({ kind: 'count', base: 2, stem: 'large rounds', rest: ' of 4',
    invariable: false, singular: false, times: false, plus: false });
  assert.strictEqual(reads(mode, 2), '2 large rounds of 4');
  assert.strictEqual(reads(mode, press(mode, 2, 1)), '4 large rounds of 4');
});

test('#1286: a volume scales by whole orders -- 950 ml, 1900 ml, 2850 ml', () => {
  // Helen: "950 ml for one order of a recipe becomes 1900 ml for 2".
  const mode = yieldMode({ kind: 'measure', base: 950, unit: 'ml', prefix: '' });
  assert.strictEqual(reads(mode, mode.base), '950 ml');
  assert.strictEqual(reads(mode, press(mode, 950, 1)), '1900 ml');
  assert.strictEqual(reads(mode, press(mode, 950, 1, 2)), '2850 ml');
  assert.strictEqual(press(mode, 950, 1) / mode.base, 2);
  // A typed figure goes to the nearest whole order.
  assert.strictEqual(mode.clamp(2000), 1900);
  assert.strictEqual(mode.clamp(2500), 2850);
});

test('#1286: a litre takes its plural, a gram does not', () => {
  const litre = yieldMode({ kind: 'measure', base: 1, unit: 'litre', prefix: '' });
  assert.strictEqual(reads(litre, 1), '1 litre');
  assert.strictEqual(reads(litre, press(litre, 1, 1)), '2 litres');
  const grams = yieldMode({ kind: 'measure', base: 75, unit: 'g', prefix: 'approx.' });
  assert.strictEqual(reads(grams, press(grams, 75, 1)), '150 g');
});

test('#1286: a `serves:` recipe steps a portion at a time, as it always did', () => {
  const mode = portionsMode(6);
  assert.strictEqual(mode.base, 6);
  assert.strictEqual(mode.box(7), '7');
  assert.strictEqual(press(mode, 6, 1), 7);
  assert.strictEqual(press(mode, 6, -1, 9), 1);
  assert.strictEqual(mode.clamp(2.6), 3);
  // The word "portions" is the markup's; the mode never rewrites it.
  assert.strictEqual(mode.word(7), null);
});

test('#1286: guessed portions on a `makes:` recipe step in whole recipes -- 4, 8, 12', () => {
  // Helen: 'if "some" is originally guessed to be 4 portions, 2x should be 8
  // portions'. cherry-glaze: `makes: "Some"`, `serves_estimate: 4`.
  const mode = portionsMode(4, true);
  assert.strictEqual(mode.box(mode.base), '4');
  assert.strictEqual(press(mode, 4, 1), 8);
  assert.strictEqual(press(mode, 4, 1, 2), 12);
  assert.strictEqual(press(mode, 4, 1) / mode.base, 2);
  assert.strictEqual(mode.clamp(6), 8);
  assert.strictEqual(mode.clamp(5), 4);
  // It still says portions: the markup's word is left alone.
  assert.strictEqual(mode.word(8), null);
});

// --- the one step below a whole recipe ----------------------------------------
// Helen: "Half a recipe would be great where the numbers aren't insane!" and
// "not having half recipes in between integers, just between 0 and 1". The
// BUILD decides which recipes get it (tests/test_food_yield.py); the second
// argument here is that verdict.

// A COUNT OF FIVE, which is what the waffles were while a range read as its
// midpoint. They read 4 since 2026-10-07; these three tests are about an ODD
// count -- the one case that halves to a range of one -- so they keep the five
// and stop borrowing the real recipe's line for it.
const FIVE_WAFFLES = { ...WAFFLES, base: 5 };

test('#1286: with the half step, a count of five goes ½, 1, 2, 3 -- "2–3", 5, 10, 15', () => {
  // THE REAL WAFFLES ARE NOT OFFERED THIS -- Helen: "Please take the half step
  // off the waffles. 2-3 waffles isn't enough!!!!" (the cup rule refuses
  // them). The spec is kept because an odd count is the case that shows the
  // range of one; the verdict passed in is what a recipe that halves gets.
  const mode = yieldMode(FIVE_WAFFLES, true);
  const half = press(mode, 5, -1);
  assert.strictEqual(half / mode.base, 0.5);
  assert.strictEqual(reads(mode, half), '2–3 waffles');
  // Minus again stays at a half: there is nothing below it.
  assert.strictEqual(press(mode, half, -1), half);
  // Plus from a half is ONE recipe, not one and a half.
  assert.strictEqual(reads(mode, press(mode, half, 1)), '5 waffles');
  assert.strictEqual(reads(mode, press(mode, half, 1, 2)), '10 waffles');
});

test('#1286: there is no half recipe BETWEEN whole ones, stepped or typed', () => {
  const mode = yieldMode(FIVE_WAFFLES, true);
  const seen = new Set();
  let n = press(mode, 5, -1, 3);
  for (let i = 0; i < 6; i += 1) { seen.add(n / mode.base); n = press(mode, n, 1); }
  assert.deepStrictEqual([...seen], [0.5, 1, 2, 3, 4, 5]);
  // Typed: every whole number of waffles from 1 to 40 lands on ½ or a whole
  // multiple -- 7 or 8 waffles is never x1½.
  for (let typed = 1; typed <= 40; typed += 1) {
    const m = mode.clamp(typed) / mode.base;
    assert.ok(m === 0.5 || m === Math.round(m), `typing ${typed} gave x${m}`);
  }
  // Under three quarters of a recipe is a half; from there up it is one.
  assert.strictEqual(mode.clamp(3) / mode.base, 0.5);
  assert.strictEqual(mode.clamp(4) / mode.base, 1);
  assert.strictEqual(mode.clamp(0.1) / mode.base, 0.5);
});

test('#1286: WITHOUT the half step, one recipe is the floor and minus does nothing', () => {
  const mode = yieldMode(FIVE_WAFFLES, false);
  assert.strictEqual(press(mode, 5, -1), 5);
  assert.strictEqual(press(mode, 5, -1, 5), 5);
  assert.strictEqual(mode.clamp(1), 5);
  assert.strictEqual(mode.clamp(0.1), 5);
  // ...and the same for a caller that passes no verdict at all.
  assert.strictEqual(press(yieldMode(FIVE_WAFFLES), 5, -1), 5);
  const cream = yieldMode({ kind: 'measure', base: 950, unit: 'ml', prefix: '' });
  assert.strictEqual(reads(cream, press(cream, 950, -1)), '950 ml');
  assert.strictEqual(cream.clamp(100), 950);
});

test('#1286: what half a recipe makes, by shape', () => {
  const half = (mode) => reads(mode, press(mode, mode.base, -1));
  // 12 fairy cakes -> 6
  assert.strictEqual(half(yieldMode({ kind: 'count', base: 12, stem: 'fairy cakes', rest: '',
    invariable: false, singular: false, times: false, plus: false }, true)), '6 fairy cakes');
  // 64+ tiny macarons -> 32+
  assert.strictEqual(half(yieldMode({ kind: 'count', base: 64, stem: 'tiny macarons', rest: '',
    invariable: false, singular: false, times: false, plus: true }, true)), '32+ tiny macarons');
  // 2 burgers -> 1 burger: the one place a plural line reaches one.
  assert.strictEqual(half(yieldMode({ kind: 'count', base: 2, stem: 'burgers', rest: '',
    invariable: false, singular: false, times: false, plus: false }, true)), '1 burger');
  // 950 ml -> 475 ml; an odd measure is a range of one.
  assert.strictEqual(half(yieldMode({ kind: 'measure', base: 950, unit: 'ml' }, true)), '475 ml');
  assert.strictEqual(half(yieldMode({ kind: 'measure', base: 125, unit: 'ml' }, true)), '62–63 ml');
  // Guessed portions: 4 -> 2, and still the markup's word.
  const some = portionsMode(4, true, true);
  assert.strictEqual(some.box(press(some, 4, -1)), '2');
  assert.strictEqual(press(some, 4, -1) / some.base, 0.5);
  assert.strictEqual(press(portionsMode(5, true, false), 5, -1), 5);
});

test('#1286: a `serves:` recipe is never given whole-recipe or half steps', () => {
  // The half verdict means nothing without whole-recipe stepping.
  const mode = portionsMode(6, false, true);
  assert.strictEqual(press(mode, 6, -1), 5);
  assert.strictEqual(press(mode, 6, 1), 7);
});

// --- "1 large egg", not "1 large eggs" -----------------------------------------
// Helen: "at 0.5x, that should read '1 large egg' not 'eggs'. Going from 1x to
// 0.5x eggs will be the only kind of occasion where a plural reduces to a
// single. Can we fix please?"

/** ingredient_words.yml's `singulars`, read as the flat map it is. */
function yamlMap(file, key) {
  const lines = fs.readFileSync(
    path.join(__dirname, '..', '..', '_data', 'food', file), 'utf8').split('\n');
  const start = lines.indexOf(key + ':');
  assert.notStrictEqual(start, -1, `${file} has no top-level ${key}: key`);
  const out = {};
  for (const line of lines.slice(start + 1)) {
    if (/^\S/.test(line) && !line.startsWith('#')) break;
    const pair = /^\s+([^#:\s][^:]*):\s+(.+?)\s*$/.exec(line);
    if (pair) out[pair[1]] = pair[2];
  }
  return out;
}

const SINGULARS = yamlMap('ingredient_words.yml', 'singulars');

test('#1286: the singulars map was actually read', () => {
  assert.strictEqual(SINGULARS.potatoes, 'potato');
  assert.strictEqual(SINGULARS.leaves, 'leaf');
});

test('#1286: an amount that comes down to exactly one says so, and only then', () => {
  // grandmas-fairy-cakes: `amount: "2 large"`, `item: "eggs"`, at half a recipe.
  const r = scaleAmount('2 large', 0.5, WORDS);
  assert.strictEqual(r.text, '1 large');
  assert.strictEqual(r.one, true);
  assert.strictEqual(scaleAmount('2', 0.5, WORDS).one, true);
  assert.strictEqual(scaleAmount('4 medium', 0.25, WORDS).one, true);
  // Not one; or one already; or a unit that carries its own noun.
  assert.strictEqual(scaleAmount('4 large', 0.5, WORDS).one, false);
  assert.strictEqual(scaleAmount('2 large', 2, WORDS).one, false);
  assert.strictEqual(scaleAmount('1 large', 1, WORDS).one, false);
  assert.strictEqual(scaleAmount('2 cloves', 0.5, WORDS).one, false);
  assert.strictEqual(scaleAmount('2 cloves', 0.5, WORDS).text, '1 clove');
  assert.strictEqual(scaleAmount('2 tbsp', 0.5, WORDS).one, false);
  assert.strictEqual(scaleAmount('2 g', 0.5, WORDS).one, false);
  assert.strictEqual(scaleAmount('1–2', 0.5, WORDS).one, false);
});

test('#1286: "1 large egg, separated" -- the item\'s leading noun goes singular', () => {
  const one = (item) => foodScale.singularItem(item, SINGULARS);
  // The waffles' own line, and the other shapes the published collection writes.
  assert.strictEqual(one('eggs, separated'), 'egg, separated');
  assert.strictEqual(one('eggs'), 'egg');
  assert.strictEqual(one('egg yolks'), 'egg yolk');
  assert.strictEqual(one('free-range eggs, separated'), 'free-range egg, separated');
  assert.strictEqual(one('onions, peeled and halved'), 'onion, peeled and halved');
  assert.strictEqual(one('soft-boiled eggs, halved (optional)'), 'soft-boiled egg, halved (optional)');
  // The house's own irregulars, from the data.
  assert.strictEqual(one('bay leaves'), 'bay leaf');
  assert.strictEqual(one('tomatoes, quartered'), 'tomato, quartered');
  assert.strictEqual(one('sweet potatoes'), 'sweet potato');
  assert.strictEqual(one('dried juniper berries'), 'dried juniper berry');
  // The noun is before "of" / "in" / "like".
  assert.strictEqual(one('rashers of streaky bacon'), 'rasher of streaky bacon');
  assert.strictEqual(one('spring onions in thin strips'), 'spring onion in thin strips');
  // The page's text node carries the template's whitespace; kept exactly.
  assert.strictEqual(one('\n            eggs, separated\n          '),
    '\n            egg, separated\n          ');
});

test('#1286: an item that cannot be made singular safely is left as written', () => {
  const same = (item) => assert.strictEqual(foodScale.singularItem(item, SINGULARS), item);
  same('star anise');                       // no plural to remove (3 published lines)
  same('shallots or 1 onion, peeled');      // two things
  same('chives and/or parsley');
  same('chillies, sliced');                 // -ies, and not in the map
  same('mangoes');                          // -oes, and not in the map: never "mangoe"
  same('watercress');                       // -ss
  same('Jersey Royals');                    // a capital in the noun
  same('egg');
  same('');
  // With no map, the irregulars are left alone rather than guessed.
  assert.strictEqual(foodScale.singularItem('tomatoes'), 'tomatoes');
  assert.strictEqual(foodScale.singularItem('eggs'), 'egg');
});

test('#1286: Delia\'s pancakes -- "about 8 pancakes" is 8 pancakes, then 16', () => {
  // Helen: 'Can Delia\'s pancakes please scale as "8 pancakes", "16 pancakes".'
  // The spec is what _plugins/food_yield.rb returns for `makes: "about 8
  // pancakes"` (tests/test_food_yield.py pins that); the "about" is printed
  // by the layout in front of the box, as it is for "about 300 ml".
  const mode = yieldMode({ kind: 'count', base: 8, prefix: 'about', stem: 'pancakes', rest: '',
    invariable: false, singular: false, times: false, plus: false }, false);
  assert.strictEqual(reads(mode, mode.base), '8 pancakes');
  assert.strictEqual(reads(mode, press(mode, 8, 1)), '16 pancakes');
  assert.strictEqual(reads(mode, press(mode, 8, 1, 2)), '24 pancakes');
});

test('#1286: a reading the box cannot use gives no mode at all', () => {
  // recipe-scale.js leaves the control hidden rather than show one that
  // cannot work.
  assert.strictEqual(yieldMode(null), null);
  assert.strictEqual(yieldMode({ kind: 'count', base: 0, stem: 'x' }), null);
  assert.strictEqual(yieldMode({}), null);
});
