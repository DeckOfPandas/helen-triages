// Tests for HTF.indexMemory in assets/js/assets.js: the sessionStorage record
// that returns you to the list you were reading when you go back from a recipe
// or a drink (#387, #686).
//
// Run from the repo root, with the local Node runtime:
//
//   .node-runtime/node/bin/node --test tests/js/*.test.js
//
// tests/js/stub-dom.js says why assets.js is loaded through a fake page.
//
// The failures here are invisible ones: private mode throws on setItem,
// blocked site data can make the read throw, and a record from an older page
// parses fine in the wrong shape. Each must end as a fresh list.
//
// Not tested here: the decision to restore at all. That is
// FilterState.arrivedByGoingBack(), asked at each index's call site and
// covered by tests/js/filter-state.test.js.
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
 * The stub page is a separate realm, so an object JSON.parse built inside it
 * has that realm's Object.prototype and deepStrictEqual refuses it. Re-parsing
 * here compares the data, which is all this module promises.
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
  // Both pages are the same origin, so one sessionStorage holds both records.
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
  // Safari private browsing throws QuotaExceededError on setItem. The index
  // saves on pagehide, so an escaping throw would fire while the reader is on
  // their way to a recipe.
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
  // setItem coerces whatever it is given with String(), so storing the object
  // itself would put "[object Object]" in the store and lose everything,
  // silently, until someone went back.
  const { HTF, storage } = withStorage(workingStorage());
  HTF.indexMemory.save(KEY, { order: ['a'], scrollY: 10 });
  assert.deepStrictEqual(JSON.parse(storage.read(KEY)), { order: ['a'], scrollY: 10 });
});
