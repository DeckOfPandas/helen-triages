// =============================================================================
// Tests for assets/js/recipe-list.js — the pure shuffle and pagination-maths
// behind the index's recipe list, no DOM required.
//
// Run from the repo root, with the local Node runtime:
//
//   .node-runtime/node/bin/node --test
//
// See tests/js/ingredient-search.test.js for why not the system node.
// =============================================================================
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const RL = require('../../assets/js/recipe-list.js');

test('shuffle returns a permutation, not a subset or a superset', () => {
  const input = ['a', 'b', 'c', 'd', 'e'];
  const result = RL.shuffle(input);
  assert.strictEqual(result.length, input.length);
  assert.deepStrictEqual([...result].sort(), [...input].sort());
});

test('shuffle does not mutate the array it was given', () => {
  const input = ['a', 'b', 'c', 'd', 'e'];
  const copy = input.slice();
  RL.shuffle(input);
  assert.deepStrictEqual(input, copy);
});

test('shuffle on an empty or single-item array is a harmless no-op', () => {
  assert.deepStrictEqual(RL.shuffle([]), []);
  assert.deepStrictEqual(RL.shuffle(['only']), ['only']);
});

test('paginate: first page of a list larger than one page', () => {
  const page = RL.paginate(45, 1, 20, false);
  assert.strictEqual(page.currentPage, 1);
  assert.strictEqual(page.totalPages, 3);
  assert.strictEqual(page.start, 0);
  assert.strictEqual(page.end, 20);
});

test('paginate: a middle page covers the next slice along', () => {
  const page = RL.paginate(45, 2, 20, false);
  assert.strictEqual(page.start, 20);
  assert.strictEqual(page.end, 40);
});

test('paginate: requesting a page below 1 clamps to page 1', () => {
  const page = RL.paginate(45, 0, 20, false);
  assert.strictEqual(page.currentPage, 1);
});

test('paginate: requesting a page past the end clamps to the last real page -- the "a filter just narrowed the results out from under you" case', () => {
  const page = RL.paginate(45, 99, 20, false);
  assert.strictEqual(page.currentPage, 3);
  assert.strictEqual(page.totalPages, 3);
});

test('paginate: zero matching items is still one (empty) page, never zero pages', () => {
  const page = RL.paginate(0, 1, 20, false);
  assert.strictEqual(page.totalPages, 1);
  assert.strictEqual(page.currentPage, 1);
});

test('paginate: showAll ignores the requested page and pageSize entirely', () => {
  const page = RL.paginate(45, 2, 20, true);
  assert.strictEqual(page.start, 0);
  assert.strictEqual(page.end, 45);
});

// titleMatchTier doesn't fold accents/hyphens itself -- that's the folder's
// job, injected as a parameter -- so these tests use a trivial identity
// fold, matching the real fold() closely enough for plain-ASCII titles.
const identityFold = (s) => s;

test('titleMatchTier: title starting with the query is tier 1', () => {
  assert.strictEqual(RL.titleMatchTier('Chicken Fajitas', 'chi', identityFold), 1);
});

test('titleMatchTier: query prefixing a later word, not the first, is tier 2', () => {
  assert.strictEqual(RL.titleMatchTier('Chicken Fajitas', 'faj', identityFold), 2);
});

test('titleMatchTier: query buried mid-word, matching no word\'s start, is tier 3', () => {
  assert.strictEqual(RL.titleMatchTier('Chicken Fajitas', 'hic', identityFold), 3);
});

test('titleMatchTier: no match anywhere is tier 0', () => {
  assert.strictEqual(RL.titleMatchTier('Chicken Fajitas', 'beef', identityFold), 0);
});

test('titleMatchTier: an empty query is always tier 0', () => {
  assert.strictEqual(RL.titleMatchTier('Chicken Fajitas', '', identityFold), 0);
});
