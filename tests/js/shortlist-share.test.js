// Tests for the store half of the share link (#1093). `node --test`.
//
// `?shortlist=negroni,aviation` opens an index showing those drinks without
// saving them (DECISIONS §8.3), so the store's part is:
//
//   1. slugOf()       the one spelling of a key's slug
//   2. resolveSlugs() which live keys a link names, and which it names that
//                     nothing on the page answers to. Writes nothing.
//   3. addAll(), keep()  "keep these": a merge into the list of the link's
//                     name (#1521), persisted once.
//   4. restore()      a pasted block of links, every list back by name.
//
// The URL grammar is filter-state.js's (filter-state.test.js); the wiring is
// each index's (food-index-startup.test.js, cocktail-index-startup.test.js).
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { makePage, load } = require('./stub-dom.js');

/* Structural comparisons go through JSON, across the vm realm boundary:
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
  '/cocktails/recipes/pear-and-rosemary-bellini/'
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

test('addAll persists, in this site\'s own record', () => {
  const storage = workingStorage();
  store(storage).addAll(['/cocktails/recipes/aviation/']);
  const record = JSON.parse(storage.read('htf-shortlists-cocktails-v1'));
  assert.deepStrictEqual(record.lists[0].entries, ['/cocktails/recipes/aviation/']);
});

test('addAll of nothing new writes nothing', () => {
  const storage = workingStorage();
  const s = store(storage);
  assert.strictEqual(s.addAll([]), 0);
  assert.strictEqual(s.addAll(undefined), 0);
  assert.strictEqual(storage.writes(), 0);
});

// --- keep these, by name (#1521) ----------------------------------------------

test('#1521: keep() makes a list of the link\'s name, and shows it', () => {
  const s = store();
  s.toggle('/cocktails/recipes/negroni/');
  const kept = s.keep('Friday', ['/cocktails/recipes/aviation/']);
  assert.strictEqual(kept.added, 1);
  assert.strictEqual(s.activeName(), 'Friday');
  assert.deepStrictEqual(plain(s.list()), ['/cocktails/recipes/aviation/']);
  assert.deepStrictEqual(plain(s.lists().map((l) => [l.name, l.count])),
    [['Shortlist', 1], ['Friday', 1]]);
});

test('#1521: keep() merges into the list that already has the name, whatever its case', () => {
  const s = store();
  const id = s.create('Friday');
  s.toggleIn(id, '/cocktails/recipes/negroni/');
  s.keep('  FRIDAY ', ['/cocktails/recipes/aviation/', '/cocktails/recipes/negroni/']);
  assert.strictEqual(s.lists().length, 2, 'no second Friday');
  assert.strictEqual(s.activeId(), id);
  assert.deepStrictEqual(plain(s.list()),
    ['/cocktails/recipes/negroni/', '/cocktails/recipes/aviation/']);
});

test('#1521: a nameless link keeps into the list on show, as before', () => {
  const s = store();
  const id = s.create('Friday');
  s.setActive(id);
  s.keep('', ['/cocktails/recipes/aviation/']);
  assert.strictEqual(s.activeId(), id);
  assert.strictEqual(s.count(), 1);
  assert.strictEqual(s.lists().length, 2);
});

// --- restore (#1521) -----------------------------------------------------------

test('#1521: restore() puts every list back by name, and leaves the list on show alone', () => {
  const s = store();
  const before = s.activeId();
  const done = s.restore([
    { name: 'Friday', slugs: ['aviation', 'negroni'] },
    { name: 'Shortlist', slugs: ['negroni'] },
    { name: 'Gone', slugs: ['old-bellini-name'] }
  ], LIVE);
  assert.deepStrictEqual(plain(done), { lists: 2, added: 3, unmatched: ['old-bellini-name'] });
  assert.strictEqual(s.activeId(), before);
  assert.deepStrictEqual(plain(s.lists().map((l) => [l.name, l.count])),
    [['Shortlist', 1], ['Friday', 2]], 'a list with nothing found is not made');
});

test('#1521: restoring the same block twice adds nothing the second time', () => {
  const s = store();
  const blocks = [{ name: 'Friday', slugs: ['aviation'] }];
  s.restore(blocks, LIVE);
  assert.strictEqual(s.restore(blocks, LIVE).added, 0);
  assert.strictEqual(s.lists().length, 2);
});

test('#1521: a nameless block line restores into "Shortlist"', () => {
  const s = store();
  const id = s.create('Friday');
  s.setActive(id);
  s.restore([{ name: '', slugs: ['aviation'] }], LIVE);
  assert.strictEqual(s.lists().find((l) => l.name === 'Shortlist').count, 1);
  assert.strictEqual(s.count(), 0, 'not into the list on show');
});

test('#1521: restore() persists, and survives junk', () => {
  const storage = workingStorage();
  const s = store(storage);
  s.restore([{ name: 'Friday', slugs: ['aviation'] }], LIVE);
  const record = JSON.parse(storage.read('htf-shortlists-cocktails-v1'));
  assert.deepStrictEqual(record.lists.map((l) => l.name), ['Shortlist', 'Friday']);
  assert.deepStrictEqual(plain(s.restore(undefined, LIVE)), { lists: 0, added: 0, unmatched: [] });
});
