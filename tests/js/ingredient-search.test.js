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
