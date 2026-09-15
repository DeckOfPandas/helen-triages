// =============================================================================
// Tests for the store half of the SHARE LINK — GitHub issue #1093.
//
// Run from the repo root:
//
//   node --test tests/js/*.test.js
//
// `?shortlist=negroni,aviation` opens an index showing those drinks. Helen's
// ruling, 2026-09-15: "Show it, don't save it" -- so the store's part is two
// questions and one deliberate write:
//
//   1. slugOf()       the one spelling of a key's slug, shared with restore()
//   2. resolveSlugs() which live keys a link names, and which it names that
//                     nothing on the page answers to. WRITES NOTHING.
//   3. addAll()       "keep these": a merge, persisted once.
//
// The URL grammar is filter-state.js's (filter-state.test.js); the wiring is
// each index's (food-index-startup.test.js, cocktail-index-startup.test.js).
// =============================================================================
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { makePage, load } = require('./stub-dom.js');

/* ACROSS THE REALM BOUNDARY, so structural comparisons go through JSON --
   shortlist.test.js's own note explains why. */
const plain = (value) => JSON.parse(JSON.stringify(value));

function workingStorage() {
  const data = new Map();
  return {
    getItem: (k) => (data.has(k) ? data.get(k) : null),
    setItem: (k, v) => { data.set(k, String(v)); },
    removeItem: (k) => { data.delete(k); },
    writes: () => data.size,
    read: (k) => data.get(k)
  };
}

function store(storage) {
  const page = makePage({ 'base-url': '/', 'site-key': 'cocktails' });
  page.localStorage = storage || workingStorage();
  load(['assets/js/assets.js'], page);
  return page.HTF.shortlist;
}

const LIVE = [
  '/cocktails/recipes/aviation/',
  '/cocktails/recipes/negroni/',
  '/cocktails/recipes/pear-apricot-and-rosemary-bellini/'
];

test('slugOf is the last path segment, lowercased', () => {
  const s = store();
  assert.strictEqual(s.slugOf('/cocktails/recipes/Negroni/'), 'negroni');
  assert.strictEqual(s.slugOf('/cocktails/drafts/to-promote/aviation'), 'aviation');
  assert.strictEqual(s.slugOf('/'), '');
});

test('resolveSlugs names the live keys, in link order, once each', () => {
  const r = store().resolveSlugs(['negroni', 'aviation', 'negroni'], LIVE);
  assert.deepStrictEqual(plain(r), {
    keys: ['/cocktails/recipes/negroni/', '/cocktails/recipes/aviation/'],
    unmatched: []
  });
});

test('resolveSlugs reports what nothing on the page answers to, rather than dropping it', () => {
  const r = store().resolveSlugs(['aviation', 'old-bellini-name', 'old-bellini-name'], LIVE);
  assert.deepStrictEqual(plain(r.keys), ['/cocktails/recipes/aviation/']);
  assert.deepStrictEqual(plain(r.unmatched), ['old-bellini-name']);
});

test('resolveSlugs WRITES NOTHING -- opening a link must not save it', () => {
  // Helen, 2026-09-15: "Show it, don't save it".
  const storage = workingStorage();
  const s = store(storage);
  s.resolveSlugs(['aviation', 'negroni'], LIVE);
  assert.strictEqual(storage.writes(), 0);
  assert.strictEqual(s.count(), 0);
});

test('resolveSlugs tolerates junk input without throwing', () => {
  const s = store();
  assert.deepStrictEqual(plain(s.resolveSlugs(undefined, LIVE)), { keys: [], unmatched: [] });
  assert.deepStrictEqual(plain(s.resolveSlugs([null, 3, ''], LIVE)), { keys: [], unmatched: [] });
  assert.deepStrictEqual(plain(s.resolveSlugs(['aviation'], undefined)),
    { keys: [], unmatched: ['aviation'] });
});

test('addAll merges: what is marked stays, in its place, and the new ones follow', () => {
  const s = store();
  s.toggle('/cocktails/recipes/negroni/');
  const added = s.addAll(['/cocktails/recipes/aviation/', '/cocktails/recipes/negroni/']);
  assert.strictEqual(added, 1);
  assert.deepStrictEqual(plain(s.list()),
    ['/cocktails/recipes/negroni/', '/cocktails/recipes/aviation/']);
});

test('addAll persists, under this site\'s own key', () => {
  const storage = workingStorage();
  store(storage).addAll(['/cocktails/recipes/aviation/']);
  assert.deepStrictEqual(JSON.parse(storage.read('htf-shortlist-cocktails-v1')),
    ['/cocktails/recipes/aviation/']);
});

test('addAll of nothing new writes nothing', () => {
  const storage = workingStorage();
  const s = store(storage);
  assert.strictEqual(s.addAll([]), 0);
  assert.strictEqual(s.addAll(undefined), 0);
  assert.strictEqual(storage.writes(), 0);
});

test('restore still matches by slug after slugOf moved out of it', () => {
  // The refactor's own guard: restore() and the share link share one slugOf.
  const s = store();
  const result = s.restore({ version: 1, site: 'cocktails',
    entries: ['/cocktails/drafts/to-promote/aviation/'] }, LIVE);
  assert.strictEqual(result.restored, 1);
  assert.deepStrictEqual(plain(s.list()), ['/cocktails/recipes/aviation/']);
});
