// Tests for assets/js/ingredient-search.js: the pure matching and ranking
// algorithm behind the ingredient search box. No DOM required.
//
// Run from the repo root, with the local Node runtime and no arguments:
//
//   .node-runtime/node/bin/node --test
//
// The vocabulary and ingredient list are small and hand-built, so no test
// depends on which recipes currently exist.
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
  // The three strips the derived vocabulary needs (#273): the real lists'
  // shape, not their full contents.
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
  // "pistachios" contains "chi" mid-word (pis-ta-CHI-os): it is still found,
  // but ranked below the real prefix matches, never mixed in with them.
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
  // "cherries" does not contain "cherry" as a substring, so matching has to
  // consult the normalised form (`singulars`), or this returns nothing.
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
  // No rule suppresses a longer entry as a variant of a shorter one: "soft
  // brown sugar" is a different product from "brown sugar".
  const found = result.results.map((r) => r.ing);
  assert.ok(found.includes('brown sugar'));
  assert.ok(found.includes('soft brown sugar'));
});

// --- the derived vocabulary's three extra strips, #273 -------------------------
// The exclude picker's list is derived from `item:` free text rather than from
// the curated main_ingredients, so it arrives carrying quantities, portion
// phrasings and method notes.

test('a leading quantity is stripped, unit and all', () => {
  const master = matcher().buildMasterList([
    '1 tsp salt', '150 g gruyère', '4–5.5 kg fresh goose',
    '¼–½ tsp sea salt', '⅛ tsp vanilla essence', '3 fl oz milk'
  ]);
  // "3 fl oz" checks that a two-word unit goes in one pass rather than
  // leaving "oz milk" behind.
  assert.deepStrictEqual(master.sort(), [
    'fresh goose', 'gruyère', 'milk', 'salt', 'sea salt', 'vanilla essence'
  ].sort());
});

test('a first word that only looks numeric is left alone', () => {
  // "3-bone" and "70%" are not bare numbers, so neither is a quantity.
  // Under-stripping is deliberate: for an exclude filter an odd-looking entry
  // is visible, while a wrong merge silently hides recipes.
  const master = matcher().buildMasterList(['3-bone rib of beef', '70% dark chocolate']);
  assert.deepStrictEqual(master.sort(), ['3-bone rib of beef', '70% dark chocolate']);
});

test('a quantity strip never eats the whole entry', () => {
  // An entry reduced to the empty string would be an unnamed, unpickable
  // button.
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
  // Over-stripping is invisible and wrong: a rule that reduces "bicarbonate
  // of soda" to "soda", or "apple cider vinegar" to "vinegar", silently merges
  // two ingredients and hides recipes the cook never asked to hide. Some of
  // these carry an "of" a general measure rule would strip through; the rest
  // are compounds a general qualifier strip would flatten.
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

// --- `aliases` in its list forms, #273 -----------------------------------------
// A name renames (tested above), a list splits an entry that names two
// ingredients, an empty list drops one that names none. Named phrases and
// never a rule, so nothing can fire on text nobody wrote.

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
  // "grated" cannot be in `modifiers`, because "grated coconut" is a
  // different product from coconut, so this one phrase is named outright.
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
  // The list's justification over a general "split on and/or" rule or a
  // prep-word stripper is that it cannot reach anything it does not name, so
  // these survive verbatim: some carry a connector word, the others are
  // near-misses of aliased phrases.
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
  const cheeseIdx = order.indexOf('cheese');
  const creamCheeseIdx = order.indexOf('cream cheese');
  const fetaIdx = order.indexOf('feta');
  assert.ok(cheeseIdx > -1 && creamCheeseIdx > -1 && fetaIdx > -1, 'all three should be found');
  assert.ok(cheeseIdx < creamCheeseIdx, 'a prefix match should rank before a word-only match');
  assert.ok(creamCheeseIdx < fetaIdx, 'a real word match should rank before a family-only member');
});

// --- entriesMatchKey — issue #506 --------------------------------------------
// The rule that decides whether a row answers a picked ingredient. Both
// directions ask it: the include filter of a row's main_ingredients, and the
// exclude filter's "(all)" umbrella through filter-state.js's excludesRow. It
// is one function so "chicken (all)" means the same thing both ways.

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
  // Feta is a cheese and says so nowhere in its own name; a prefix rule
  // cannot reach it.
  const m = matcher();
  assert.strictEqual(m.entriesMatchKey(['feta'], 'cheese'), true);
  assert.strictEqual(m.entriesMatchKey(['mature cheddar'], 'cheese'), true);
  assert.strictEqual(m.entriesMatchKey(['cream cheese'], 'cheese'), true);
  assert.strictEqual(m.entriesMatchKey(['butter'], 'cheese'), false);
});

test('the family rule is containment, so a family member matches mid-word too', () => {
  // `cheddar` inside `cheddary crumbs` matches, where the non-family branch
  // wants a word start. Over-reaching here shows a recipe; it hides none.
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

// --- entriesMatchKey matches by PREFIX — issue #619 --------------------------
// Containment hands back, for `salt`, recipes whose only salt is UNsalted
// butter. A key word must start an entry word.

test('a key matches the START of a word, not the middle of one', () => {
  const m = matcher();
  assert.strictEqual(
    m.entriesMatchKey(['unsalted butter'], 'salt'), false,
    'asking for salt returned a recipe whose only salt is UNsalted butter — ' +
    'issue #619, and the case Helen raised it from.'
  );
  assert.strictEqual(m.entriesMatchKey(['salted butter'], 'salt'), true);
  assert.strictEqual(m.entriesMatchKey(['sea salt'], 'salt'), true);
});

test('the opposite of what was asked is the worst version of the same bug', () => {
  // Not merely a loose match: the entry is the negation of the key.
  assert.strictEqual(
    matcher().entriesMatchKey(['unsalted butter'], 'salted butter'), false
  );
});

test('the short words that made this worth fixing', () => {
  const m = matcher();
  assert.strictEqual(m.entriesMatchKey(['brown rice'], 'ice'), false);
  assert.strictEqual(m.entriesMatchKey(['citrus juice'], 'ice'), false);
  assert.strictEqual(m.entriesMatchKey(['five-spice powder'], 'ice'), false);
  assert.strictEqual(m.entriesMatchKey(['ice cubes'], 'ice'), true);

  // cocktail-search.js names this exact pair in its own header, having made
  // the same choice on the other site first.
  assert.strictEqual(m.entriesMatchKey(['pineapple juice'], 'apple'), false);
  assert.strictEqual(m.entriesMatchKey(['apple juice'], 'apple'), true);

  assert.strictEqual(m.entriesMatchKey(['chickpeas'], 'peas'), false);
  assert.strictEqual(m.entriesMatchKey(['buttermilk'], 'milk'), false);
  assert.strictEqual(m.entriesMatchKey(['aubergine'], 'gin'), false);
  assert.strictEqual(m.entriesMatchKey(['pork sausages'], 'sage'), false);
});

test('a prefix still reaches a longer word, which is the point of prefix', () => {
  // The rule is not "whole words": typing toward something has to keep
  // working while it is still being typed.
  const m = matcher();
  assert.strictEqual(m.entriesMatchKey(['chicken thighs'], 'chick'), true);
  assert.strictEqual(m.entriesMatchKey(['coriander'], 'cori'), true);
});

// #1386. A phone keyboard types no accents, so a two-word query must fold the
// entry as the one-word query always has.
test('a two-word query typed without accents finds the accented entry', () => {
  const master = ['crème fraîche', 'cream cheese', 'comté'];
  const found = (q) => matcher().search(q, master).results.map((r) => r.ing);
  assert.deepStrictEqual(found('creme'), ['crème fraîche']);
  assert.deepStrictEqual(found('creme fraiche'), ['crème fraîche']);
  assert.deepStrictEqual(found('fraiche creme'), ['crème fraîche']);
  assert.ok(found('creme fraiche')[0] === 'crème fraîche');
});

test('a two-word query lists an entry once however its accents or plural are spelled', () => {
  const master = ['crème fraîche', 'creme fraiche', 'sour cherries', 'sour cherry'];
  const once = (q) => matcher().search(q, master).results.length;
  assert.strictEqual(once('creme'), 1, 'one word: one result, as before');
  assert.strictEqual(once('creme fr'), 1);
  assert.strictEqual(once('sour cherr'), 1);
});
