// =============================================================================
// Tests for assets/js/ingredient-search.js — the pure matching/ranking
// algorithm behind the ingredient search box, no DOM required.
//
// Run from the repo root, with the local Node runtime (see
// model_instructions/DEV_JOBS_v22.md §3.4 for why it's not system-wide).
// No arguments — Node's test runner auto-discovers *.test.js files from
// the current directory; passing this file's directory explicitly does
// NOT work the same way (tries to require() it as a module and fails):
//
//   .node-runtime/node/bin/node --test
//
// This file uses a small, hand-built vocabulary and ingredient list rather
// than the real site data, so each test is self-contained and readable —
// what's being checked doesn't depend on what recipes currently exist. A
// separate ad hoc check against the real data ran once, by hand, when this
// module was extracted from filters.js, to confirm the extraction changed
// nothing; these tests are the permanent record.
// =============================================================================
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const IS = require('../../assets/js/ingredient-search.js');

const VOCAB = {
  search: { family_button_min_chars: 3 },
  singulars: { cherries: 'cherry' },
  synonyms: {
    cheese: ['cheese', 'cheddar', 'feta']
  },
  modifiers: ['chopped'],
  never_family: [],
  family_exceptions: [],
  stopwords: ['and'],
  // GitHub issue #273 — the three strips the DERIVED vocabulary needs. Kept
  // to the real lists' shape but not their full contents, same as every
  // other list here: what's being checked is the algorithm, not which words
  // happen to be in _data/food/ingredient_words.yml today.
  quantity_units: ['g', 'kg', 'ml', 'tsp', 'tbsp', 'fl', 'oz'],
  measure_phrases: ['a few sprigs of', 'a good pinch of', 'a pat of', 'a large handful of', 'a glass of'],
  trailing_phrases: ['to taste', 'to serve', 'to glaze', 'to garnish']
};

const RAW_INGREDIENTS = [
  'chicken breast',
  'chicken thigh',
  'Chinese five spice',
  'cheddar',
  'cream cheese',
  'chopped pistachios',
  'pistachios',
  'chicken thighs and drumsticks',
  'cherries'
];

function matcher() {
  return IS.create(VOCAB);
}

test('buildMasterList sorts case-insensitively', () => {
  const master = matcher().buildMasterList(RAW_INGREDIENTS);
  // "Chinese five spice" must sit between "cherries" and "chopped..." —
  // not jump to the front because it's capitalised. A plain .sort() gets
  // this wrong: capitals sort before every lowercase letter.
  const chIndex = master.indexOf('Chinese five spice');
  const cherriesIndex = master.indexOf('cherries');
  const chickenBreastIndex = master.indexOf('chicken breast');
  assert.ok(chIndex > cherriesIndex, 'Chinese five spice should sort after cherries');
  assert.ok(chIndex > chickenBreastIndex, 'Chinese five spice should sort after chicken breast');
});

test('buildMasterList strips modifiers and deduplicates', () => {
  const master = matcher().buildMasterList(RAW_INGREDIENTS);
  // "chopped pistachios" and "pistachios" are the same ingredient once the
  // modifier is stripped — the master list should hold "pistachios" once,
  // never "chopped pistachios" as its own entry.
  assert.ok(master.includes('pistachios'));
  assert.ok(!master.includes('chopped pistachios'));
  assert.strictEqual(master.filter((ing) => ing === 'pistachios').length, 1);
});

test('search finds a literal substring match', () => {
  const master = matcher().buildMasterList(RAW_INGREDIENTS);
  const result = matcher().search('chicken', master);
  const found = result.results.map((r) => r.ing);
  assert.ok(found.includes('chicken breast'));
  assert.ok(found.includes('chicken thigh'));
});

test('search ranks a whole-string prefix match above a mid-word match', () => {
  const master = matcher().buildMasterList(RAW_INGREDIENTS);
  // "chi" prefixes "chicken breast"/"chicken thigh"/"Chinese five spice" —
  // real matches, should rank first. "pistachios" contains "chi" too, but
  // buried mid-word (pis-ta-CHI-os) — the actual historical bug this rule
  // exists to fix (see DEV_JOBS_v22.md / the "chi" screenshot). It should
  // still be found, just ranked below the real prefix matches, never mixed
  // in with them.
  const result = matcher().search('chi', master);
  const prefixIngs = result.results.filter((r) => r.isPrefixMatch).map((r) => r.ing);
  const restIngs = result.results.filter((r) => !r.isPrefixMatch).map((r) => r.ing);
  assert.ok(prefixIngs.includes('chicken breast'));
  assert.ok(prefixIngs.includes('chicken thigh'));
  assert.ok(prefixIngs.includes('Chinese five spice'));
  assert.ok(!prefixIngs.includes('pistachios'), 'pistachios should NOT be ranked as a prefix match');
  assert.deepStrictEqual(restIngs, ['pistachios']);
});

test('search widens a curated synonym family beyond literal substring matches', () => {
  const master = matcher().buildMasterList(RAW_INGREDIENTS);
  const result = matcher().search('chees', master);
  const found = result.results.map((r) => r.ing);
  // "cheddar" doesn't contain "chees" anywhere — it's only found because
  // "cheese" is a curated family and the query is heading towards it.
  assert.ok(found.includes('cheddar'), 'cheddar should surface via the curated cheese family');
  assert.ok(found.includes('cream cheese'), 'cream cheese should match literally');
  assert.ok(result.familyButtons.includes('cheese'), 'cheese (all) should be offered');
});

test('stopwords are never a match target, wherever they fall in the phrase', () => {
  const master = matcher().buildMasterList(RAW_INGREDIENTS);
  const result = matcher().search('a', master);
  const found = result.results.map((r) => r.ing);
  // "and" is the only word in "chicken thighs and drumsticks" that starts
  // with "a" — chicken/thighs/drumsticks don't. Without stopword
  // filtering, this entry only ever matched because "and" happened to.
  assert.ok(!found.includes('chicken thighs and drumsticks'),
    'should not match solely via the connector "and"');
});

test('an irregular plural is findable by its singular form', () => {
  const master = matcher().buildMasterList(['cherries']);
  const result = matcher().search('cherry', master);
  // "cherries" is declared in `singulars` as the plural of "cherry", but
  // the raw text "cherries" never literally contains "cherry" as a
  // substring — "y" becomes "ies", the ending changes rather than just
  // extending — so matching has to consult the normalised form, not just
  // raw text, or this returns nothing at all.
  const cherries = result.results.find((r) => r.ing === 'cherries');
  assert.ok(cherries, 'cherries should be found');
  assert.ok(cherries.isPrefixMatch, 'cherries should rank as a prefix match, not fall to the bottom tier');
});

test('never_family words never earn an (all) button, even when they head 2+ entries', () => {
  const vocab = Object.assign({}, VOCAB, { never_family: ['red'] });
  const ingredients = ['red wine', 'red onion', 'red pepper'];
  const master = IS.create(vocab).buildMasterList(ingredients);
  const result = IS.create(vocab).search('red', master);
  // All three genuinely match "red" and should still be individually
  // findable...
  assert.deepStrictEqual(
    result.results.map((r) => r.ing).sort(),
    ['red onion', 'red pepper', 'red wine']
  );
  // ...but "red" heads all three, which — without never_family — would be
  // enough to form "red (all)". They're unrelated foods that merely share
  // a colour word, not a real family.
  assert.ok(!result.familyButtons.includes('red'), 'red (all) should not form');
});

test("family_exceptions are excluded from their own head word's family count", () => {
  const vocab = Object.assign({}, VOCAB, { family_exceptions: ['cherry tomatoes'] });
  const ingredients = ['cherries', 'cherry tomatoes'];
  const master = IS.create(vocab).buildMasterList(ingredients);
  const result = IS.create(vocab).search('cherr', master);
  // Both still show up as individual results...
  const found = result.results.map((r) => r.ing);
  assert.ok(found.includes('cherries'));
  assert.ok(found.includes('cherry tomatoes'));
  // ...but "cherry tomatoes" doesn't count towards "cherry"'s family, so
  // with only one genuine member left (cherries), no (all) button forms.
  assert.ok(!result.familyButtons.includes('cherry'),
    'cherry (all) should not form once the impostor is excluded from the count');
});

test('aliases collapse a whole phrase into another, so only the canonical form appears', () => {
  const vocab = Object.assign({}, VOCAB, { aliases: { 'five-spice powder': 'five-spice' } });
  const ingredients = ['five-spice', 'five-spice powder'];
  const master = IS.create(vocab).buildMasterList(ingredients);
  assert.deepStrictEqual(master, ['five-spice']);
  const result = IS.create(vocab).search('five', master);
  // Two recipes, but one collapsed entry -- and with only one entry left,
  // there's nothing to group into a "five (all)" button.
  assert.deepStrictEqual(result.results.map((r) => r.ing), ['five-spice']);
  assert.ok(!result.familyButtons.includes('five'), 'five (all) should not form once collapsed to one entry');
});

test('display_names relabels a result without changing its match key', () => {
  const vocab = Object.assign({}, VOCAB, {
    aliases: { 'five-spice powder': 'five-spice' },
    display_names: { 'five-spice': 'Chinese five-spice powder' }
  });
  const master = IS.create(vocab).buildMasterList(['five-spice', 'five-spice powder']);
  const result = IS.create(vocab).search('five', master);
  assert.strictEqual(result.results.length, 1);
  // The match key -- what filters.js stores as dataset.ingredient and uses
  // to test recipes -- stays the literal text that's actually in the data.
  assert.strictEqual(result.results[0].ing, 'five-spice');
  // Only the label shown on the button changes.
  assert.strictEqual(result.results[0].label, 'Chinese five-spice powder');
});

test('a longer entry is never hidden behind a similar shorter one', () => {
  const master = matcher().buildMasterList(['brown sugar', 'soft brown sugar']);
  const result = matcher().search('sugar', master);
  // There used to be a rule that suppressed "soft brown sugar" as a
  // supposed redundant variant of "brown sugar". Checked against the real
  // site data, every one of the 31 cases it actually fired on hid a
  // genuinely different product — this is that case. Removed entirely
  // rather than patched further.
  const found = result.results.map((r) => r.ing);
  assert.ok(found.includes('brown sugar'));
  assert.ok(found.includes('soft brown sugar'));
});

// =============================================================================
// GitHub issue #273 — the derived vocabulary's three extra strips.
//
// The exclude picker's list is derived from `item:` free text rather than
// from the curated main_ingredients, so it arrives carrying quantities,
// portion phrasings and method notes. Each of the four tests below is a real
// entry the live picker offered; the fifth is the one that matters most.
// =============================================================================

test('a leading quantity is stripped, unit and all', () => {
  const master = matcher().buildMasterList([
    '1 tsp salt', '150 g gruyère', '4–5.5 kg fresh goose',
    '¼–½ tsp sea salt', '⅛ tsp vanilla essence', '3 fl oz milk'
  ]);
  // Every one of these is a real recipe that put its amount in `item:`
  // instead of `amount:`. "3 fl oz" checks that a two-word unit goes in one
  // pass rather than leaving "oz milk" behind.
  assert.deepStrictEqual(master.sort(), [
    'fresh goose', 'gruyère', 'milk', 'salt', 'sea salt', 'vanilla essence'
  ].sort());
});

test('a first word that only looks numeric is left alone', () => {
  // "3-bone" and "70%" carry a letter and a percent sign respectively, so
  // neither is a bare number and neither is a quantity. Both are
  // under-strips, on purpose: for an EXCLUDE filter, an entry that reads
  // oddly is visible and annoying, while a wrong merge silently hides
  // recipes the cook never meant to exclude.
  const master = matcher().buildMasterList(['3-bone rib of beef', '70% dark chocolate']);
  assert.deepStrictEqual(master.sort(), ['3-bone rib of beef', '70% dark chocolate']);
});

test('a quantity strip never eats the whole entry', () => {
  // Nothing in the collection is written this way, but an entry reduced to
  // the empty string would be an unnamed, unpickable button.
  assert.deepStrictEqual(matcher().buildMasterList(['500 g']), ['g']);
  assert.deepStrictEqual(matcher().buildMasterList(['200']), ['200']);
});

test('a measure phrase is stripped so the entry is the ingredient', () => {
  const master = matcher().buildMasterList([
    'a few sprigs of fresh thyme', 'a good pinch of salt', 'a pat of salted butter',
    'a large handful of fresh coriander', 'a glass of robust red wine', 'salt'
  ]);
  // "a good pinch of salt" collapses onto the "salt" that was already there
  // — one entry, not two spellings of the same avoidance.
  assert.deepStrictEqual(master.sort(), [
    'fresh coriander', 'fresh thyme', 'robust red wine', 'salt', 'salted butter'
  ].sort());
});

test('a trailing method note is stripped from the end', () => {
  const master = matcher().buildMasterList([
    'herbs to taste', 'sriracha to serve', 'apricot jam to glaze', 'watercress to garnish'
  ]);
  assert.deepStrictEqual(master.sort(), ['apricot jam', 'herbs', 'sriracha', 'watercress']);
});

test('none of the new strips touch an ingredient whose name genuinely contains those words', () => {
  // THE TEST THAT MATTERS. Under-stripping is visible and annoying;
  // over-stripping is invisible and wrong — a rule that reduces
  // "bicarbonate of soda" to "soda", or "apple cider vinegar" to "vinegar",
  // silently merges two ingredients and hides recipes the cook never asked
  // to hide. Every one of these six survived a real pass over the derived
  // vocabulary and must keep surviving: three carry an "of" that a general
  // measure rule would strip through, and three are long compounds that a
  // general "strip the qualifier" rule would flatten.
  const protectedEntries = [
    'apple cider vinegar',
    'bicarbonate of soda',
    'black cardamom pods',
    'coconut palm sugar',
    'cream of tartar',
    'chicken stock cube'
  ];
  const master = matcher().buildMasterList(protectedEntries);
  assert.deepStrictEqual(master.slice().sort(), protectedEntries.slice().sort());
});

// =============================================================================
// GitHub issue #273 — `aliases` in its list forms.
//
// The derived vocabulary also offered entries that name TWO ingredients at
// once ("beef or venison stock") or none at all ("flavouring or fruit"), plus
// preparation states the leading-word `modifiers` strip can't reach ("grated
// parmesan"). All three are the job `aliases` already did for "five-spice
// powder", so `aliases` took them rather than a second list being invented:
// a NAME renames (tested above), a LIST splits, an EMPTY LIST drops. Named
// phrases and never a rule, so nothing can fire on text nobody wrote.
// =============================================================================

const ALIAS_VOCAB = Object.assign({}, VOCAB, {
  aliases: {
    'grated parmesan': 'parmesan',
    'beef or venison stock': ['beef stock', 'venison stock'],
    'flavouring or fruit': [],
    'sorrel or more': ['sorrel']
  }
});

test('an alias written as a bare name still renames, list forms or not', () => {
  const master = IS.create(ALIAS_VOCAB).buildMasterList(['grated parmesan', 'parmesan']);
  // "grated" isn't in `modifiers` and can't be, because "grated coconut" is a
  // different product from coconut — so this one phrase is named outright.
  // Both spellings collapse onto the one entry, not two. The bare-name form
  // is the original alias shape and must keep working beside the list ones.
  assert.deepStrictEqual(master, ['parmesan']);
});

test('an alias written as a list splits one entry into all of them', () => {
  const master = IS.create(ALIAS_VOCAB).buildMasterList(['beef or venison stock']);
  // The picker has to offer each stock separately: a cook avoiding venison
  // has no way to say so while the two are welded into one button.
  assert.deepStrictEqual(master, ['beef stock', 'venison stock']);
  assert.ok(!master.includes('beef or venison stock'), 'the compound entry should be gone');
});

test('an alias written as an empty list drops the entry entirely', () => {
  const master = IS.create(ALIAS_VOCAB).buildMasterList(['flavouring or fruit', 'apples']);
  // "flavouring or fruit" names no food, so there is nothing to offer to
  // exclude — and an entry nobody could act on is worse than no entry.
  assert.deepStrictEqual(master, ['apples']);
});

test('aliases match the POST-STRIP form of an entry, not the raw text', () => {
  // "sorrel or more to taste" is not a key — "sorrel or more" is, because the
  // trailing-phrase strip has already run by the time aliases are consulted.
  // Keying the raw form would make the entry inert while looking correct.
  const master = IS.create(ALIAS_VOCAB).buildMasterList(['sorrel or more to taste']);
  assert.deepStrictEqual(master, ['sorrel']);
});

test('an entry `aliases` does not name is left exactly as it was', () => {
  // THE TEST THAT MATTERS, again. The list's whole justification over a
  // general "split on and/or" rule, or a general prep-word stripper, is that
  // it cannot reach anything it doesn't name — so these must survive it
  // verbatim. Three carry a connector word a general rule would cut them in
  // half at; two are near-misses of real keys in the live list ("roasted
  // peanuts" and "smoked mackerel fillets" ARE aliased there, "dry roasted
  // peanuts" and "smoked haddock" are deliberately not).
  const untouched = [
    'almonds or whatever you prefer',
    'bicarbonate of soda',
    'chicken thighs and drumsticks',
    'dry roasted peanuts',
    'smoked haddock'
  ];
  const master = IS.create(ALIAS_VOCAB).buildMasterList(untouched);
  assert.deepStrictEqual(master.slice().sort(), untouched.slice().sort());
});

test('within the non-prefix results, a real word match ranks above a family-only member', () => {
  const ingredients = ['cheese', 'cream cheese', 'feta'];
  const master = matcher().buildMasterList(ingredients);
  const result = matcher().search('chees', master);
  const order = result.results.map((r) => r.ing);
  // "cheese" is a prefix match (band 1). "cream cheese" is a real word
  // match — it literally contains "cheese" — but not a prefix match
  // (band 2). "feta" is included only because the curated family says
  // it's a cheese, with no textual relation to "chees" at all (band 3).
  // Merging bands 2 and 3 is the exact mistake that let "chocolate chips"
  // rank alongside "chicken breast" for "chi" — see the ranking test above.
  const cheeseIdx = order.indexOf('cheese');
  const creamCheeseIdx = order.indexOf('cream cheese');
  const fetaIdx = order.indexOf('feta');
  assert.ok(cheeseIdx > -1 && creamCheeseIdx > -1 && fetaIdx > -1, 'all three should be found');
  assert.ok(cheeseIdx < creamCheeseIdx, 'a prefix match should rank before a word-only match');
  assert.ok(creamCheeseIdx < fetaIdx, 'a real word match should rank before a family-only member');
});

// --- entriesMatchKey — issue #506 --------------------------------------------
// The rule that decides whether a row answers a picked ingredient. It sat in
// filters.js, untested, and it is asked by BOTH directions: the include filter
// of a row's main_ingredients, and the exclude filter's "(all)" umbrella of the
// row's derived entries, through filter-state.js's excludesRow. Two copies of
// this is how "chicken (all)" comes to mean one thing when you filter FOR it
// and another when you filter it OUT, which is why it is one function.

test('a plain key matches an entry containing it', () => {
  assert.strictEqual(matcher().entriesMatchKey(['chicken breast', 'thyme'], 'chicken'), true);
  assert.strictEqual(matcher().entriesMatchKey(['thyme', 'butter'], 'chicken'), false);
});

test('EVERY word of a two-word key has to land, not just one', () => {
  const m = matcher();
  assert.strictEqual(m.entriesMatchKey(['chicken breast'], 'chicken breast'), true);
  assert.strictEqual(
    m.entriesMatchKey(['chicken thighs'], 'chicken breast'), false,
    'half a key matched. "chicken breast" is not answered by chicken alone, ' +
    'or the picker offers a precision it does not have.'
  );
});

test('a curated family matches by CONTAINMENT, including members sharing no letters', () => {
  // The whole reason synonyms exist: feta is a cheese and says so nowhere in
  // its own name. A prefix rule cannot reach it and must not have to.
  const m = matcher();
  assert.strictEqual(m.entriesMatchKey(['feta'], 'cheese'), true);
  assert.strictEqual(m.entriesMatchKey(['mature cheddar'], 'cheese'), true);
  assert.strictEqual(m.entriesMatchKey(['cream cheese'], 'cheese'), true);
  assert.strictEqual(m.entriesMatchKey(['butter'], 'cheese'), false);
});

test('the family rule is containment, so a family member matches mid-word too', () => {
  // Recorded rather than admired: `cheddar` inside `cheddary crumbs` matches,
  // where the non-family branch would want a word. It is the include/umbrella
  // direction, where over-reaching shows you a recipe and the row says why.
  assert.strictEqual(matcher().entriesMatchKey(['cheddary crumbs'], 'cheese'), true);
});

test('an irregular plural is normalised on BOTH sides before comparing', () => {
  // singulars: { cherries: 'cherry' }. The row says one, the picker may say
  // the other, and the pair must not depend on which.
  const m = matcher();
  assert.strictEqual(m.entriesMatchKey(['cherries'], 'cherry'), true);
  assert.strictEqual(m.entriesMatchKey(['cherry'], 'cherries'), true);
});

test('an empty or missing list matches nothing, rather than throwing', () => {
  const m = matcher();
  assert.strictEqual(m.entriesMatchKey([], 'chicken'), false);
  assert.strictEqual(m.entriesMatchKey(undefined, 'chicken'), false);
});
