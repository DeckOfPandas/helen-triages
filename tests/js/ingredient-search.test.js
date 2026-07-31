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
  stopwords: ['and']
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
