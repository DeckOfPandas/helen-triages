// =============================================================================
// Tests for HTF.indexMemory in assets/js/assets.js — the sessionStorage record
// that returns you to the list you were reading when you go BACK from a recipe
// or a drink. GitHub issues #387 (the feature) and #686 (one copy, not two).
//
// Run from the repo root, with the local Node runtime:
//
//   .node-runtime/node/bin/node --test tests/js/*.test.js
//
// See tests/js/ingredient-search.test.js for why not the system node, and
// tests/js/stub-dom.js for why this file loads assets.js through a fake page
// rather than requiring it.
//
// WHY THIS FILE EXISTS. The failure modes here are all invisible ones. A
// browser in private mode throws on setItem; site data blocked can make even
// the read throw; a record left by an older version of the page parses fine
// and is the wrong shape. Every one of those must end as "carry on as a fresh
// list", and none of them can be produced by clicking around in the browser
// you happen to have open — which is exactly why the swallowing was worth
// having in one place with a stub storage pointed at it.
//
// WHAT IS NOT TESTED HERE, because it is deliberately not in this module: the
// decision to restore AT ALL. That is FilterState.arrivedByGoingBack(), asked
// at each index's own call site and covered by tests/js/filter-state.test.js.
// =============================================================================
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { makePage, loadHTF } = require('./stub-dom.js');

const KEY = 'htf-index-memory-v1';

/** A working sessionStorage: the browser's, minus everything unused here. */
function workingStorage(initial) {
  const store = Object.assign(Object.create(null), initial);
  return {
    getItem: (key) => (key in store ? store[key] : null),
    setItem: (key, value) => { store[key] = String(value); },
    read: (key) => store[key]
  };
}

/** A page with assets.js loaded and the given storage as its sessionStorage. */
function withStorage(sessionStorage) {
  const page = makePage();
  page.sessionStorage = sessionStorage;
  return { HTF: loadHTF(page), storage: sessionStorage };
}

/** Bring an object back across the vm boundary before comparing it.
 *
 * The stub page is a separate realm with its own intrinsics, so an object
 * JSON.parse built INSIDE it has that realm's Object.prototype and
 * deepStrictEqual refuses it -- same structure, different prototype. Re-parsing
 * here is the smallest honest fix: it compares the DATA, which is the only
 * thing this module promises, and keeps the strict comparison everywhere else.
 */
function plain(value) {
  return value === null ? null : JSON.parse(JSON.stringify(value));
}

test('a record saved under a key comes back from that key', () => {
  const { HTF } = withStorage(workingStorage());
  const state = {
    order: ['/food/recipes/caramel/', '/food/recipes/soup/'],
    filters: '?tag=soup',
    page: 2,
    showAll: false,
    scrollY: 2400
  };
  HTF.indexMemory.save(KEY, state);
  assert.deepStrictEqual(plain(HTF.indexMemory.restore(KEY)), state);
});

test('the two indexes do not read each other: a key is a key', () => {
  // The whole reason the key is a parameter. Both pages are the same origin,
  // so one sessionStorage holds both records.
  const { HTF } = withStorage(workingStorage());
  HTF.indexMemory.save('htf-index-memory-v1', { order: ['a'] });
  HTF.indexMemory.save('htf-drinks-memory-v1', { order: ['b'] });
  assert.deepStrictEqual(plain(HTF.indexMemory.restore('htf-index-memory-v1')), { order: ['a'] });
  assert.deepStrictEqual(plain(HTF.indexMemory.restore('htf-drinks-memory-v1')), { order: ['b'] });
});

test('nothing stored under the key: null, the fresh-load answer', () => {
  const { HTF } = withStorage(workingStorage());
  assert.strictEqual(HTF.indexMemory.restore(KEY), null);
});

test('a corrupt record is null rather than a throw', () => {
  // Truncated by a browser under storage pressure, or written by a hand at a
  // devtools console. JSON.parse throws; the page must not.
  const { HTF } = withStorage(workingStorage({ [KEY]: '{"order":["a"' }));
  assert.strictEqual(HTF.indexMemory.restore(KEY), null);
});

test('a stored literal null is null, not a record', () => {
  const { HTF } = withStorage(workingStorage({ [KEY]: 'null' }));
  assert.strictEqual(HTF.indexMemory.restore(KEY), null);
});

test('storage that throws on READ: null, and nothing escapes', () => {
  // Site data blocked. The getter itself throws, before there is anything to
  // parse.
  const { HTF } = withStorage({
    getItem: () => { throw new Error('access denied'); },
    setItem: () => {}
  });
  assert.strictEqual(HTF.indexMemory.restore(KEY), null);
});

test('storage that throws on WRITE — private mode — does not break the page', () => {
  // The real one: Safari private browsing has thrown QuotaExceededError on
  // setItem for years. saveIndexMemory runs on pagehide, so an escaping throw
  // would fire while the reader is on their way to a recipe.
  const { HTF } = withStorage({
    getItem: () => null,
    setItem: () => { throw new Error('QuotaExceededError'); }
  });
  assert.doesNotThrow(() => HTF.indexMemory.save(KEY, { order: [] }));
  assert.strictEqual(HTF.indexMemory.restore(KEY), null);
});

test('no sessionStorage in the context at all: still null, still no throw', () => {
  // A bare reference to a missing global is a ReferenceError, not undefined,
  // so this is a genuinely different path from the two above.
  const page = makePage();
  const HTF = loadHTF(page);
  assert.strictEqual(HTF.indexMemory.restore(KEY), null);
  assert.doesNotThrow(() => HTF.indexMemory.save(KEY, { order: [] }));
});

test('what lands in storage is JSON, so the record survives a page load', () => {
  // Not a formality: setItem coerces whatever it is given with String(), so
  // storing the object itself would put "[object Object]" in the store and
  // lose everything, silently, until someone went back.
  const { HTF, storage } = withStorage(workingStorage());
  HTF.indexMemory.save(KEY, { order: ['a'], scrollY: 10 });
  assert.deepStrictEqual(JSON.parse(storage.read(KEY)), { order: ['a'], scrollY: 10 });
});
