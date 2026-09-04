// =============================================================================
// Tests for HTF.shortlist in assets/js/assets.js — GitHub issue #546.
//
// Run from the repo root:
//
//   node --test tests/js/*.test.js
//
// (tests/js/ingredient-search.test.js documents the local .node-runtime this
// repo normally uses; it is gitignored and so is absent from a worktree.)
//
// WHY THIS FILE EXISTS, and it is the same argument index-memory.test.js makes
// about its own module: every failure mode here is invisible from a browser you
// happen to have open. Private mode throws on setItem; a browser with site data
// blocked can make the getter throw; a record left by an older build parses
// fine and is the wrong shape. And this one has a rule index memory does not —
// a failed WRITE must not cost you the click you just made, because you asked
// for it. That is a behaviour with no way to produce it by clicking around.
//
// WHAT IS NOT TESTED HERE: the DOM half. assets/js/shortlist.js finds the
// controls, paints them and dispatches the event; it needs a real document and
// this harness stubs only enough page for a script to read two meta tags.
// =============================================================================
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { makePage, load } = require('./stub-dom.js');

const FOOD_KEY = 'htf-shortlist-food-v1';

/* ACROSS THE REALM BOUNDARY, so array comparisons go through JSON.
   `assert.deepStrictEqual` checks prototypes, and an array built inside the vm
   context is an instance of THAT context's Array, not this one's — so an
   otherwise identical list fails with "same structure but not reference-equal".
   The same fact filter-state.js's own comments cite as the reason it duck-types
   Sets rather than using `instanceof`. Round-tripping through JSON rebuilds the
   value in this realm and compares what the test is actually about. */
const plain = (value) => JSON.parse(JSON.stringify(value));

/** A working localStorage: the browser's, minus everything unused here. */
function workingStorage(initial) {
  const store = Object.assign(Object.create(null), initial);
  return {
    getItem: (key) => (key in store ? store[key] : null),
    setItem: (key, value) => { store[key] = String(value); },
    read: (key) => store[key],
    /* Not part of the localStorage surface — the tests' own window on what was
       actually persisted, so "nothing was written" can be asserted without
       counting the helper's own methods. */
    keys: () => Object.keys(store)
  };
}

/**
 * A page with a localStorage of our choosing and assets.js run into it.
 *
 * @param {Object} [storage] - anything with getItem/setItem; omit for a working one
 * @param {string} [siteKey] - the <meta name="site-key">; omit for food
 * @returns {Object} { HTF, storage }
 */
function pageWith(storage, siteKey) {
  const store = storage || workingStorage();
  const page = makePage({
    'base-url': '/',
    'site-key': siteKey === undefined ? 'food' : siteKey
  });
  page.localStorage = store;
  load(['assets/js/assets.js'], page);
  return { HTF: page.HTF, storage: store };
}

// --- the ordinary case --------------------------------------------------------

test('an empty store has nothing in it', () => {
  const { HTF } = pageWith();
  assert.deepStrictEqual(plain(HTF.shortlist.list()), []);
  assert.strictEqual(HTF.shortlist.count(), 0);
  assert.strictEqual(HTF.shortlist.has('/food/recipes/dal/'), false);
});

test('toggle adds, and reports the state it ended in', () => {
  const { HTF } = pageWith();
  assert.strictEqual(HTF.shortlist.toggle('/food/recipes/dal/'), true);
  assert.strictEqual(HTF.shortlist.has('/food/recipes/dal/'), true);
  assert.strictEqual(HTF.shortlist.count(), 1);
});

test('toggle removes what it added, and says so', () => {
  const { HTF } = pageWith();
  HTF.shortlist.toggle('/food/recipes/dal/');
  assert.strictEqual(HTF.shortlist.toggle('/food/recipes/dal/'), false);
  assert.strictEqual(HTF.shortlist.has('/food/recipes/dal/'), false);
  assert.strictEqual(HTF.shortlist.count(), 0);
});

test('entries come back oldest first — the order they were marked in', () => {
  const { HTF } = pageWith();
  ['/a/', '/b/', '/c/'].forEach((u) => HTF.shortlist.toggle(u));
  assert.deepStrictEqual(plain(HTF.shortlist.list()), ['/a/', '/b/', '/c/']);
});

test('list() hands back a copy — a caller sorting it cannot reorder the store', () => {
  const { HTF } = pageWith();
  ['/a/', '/b/'].forEach((u) => HTF.shortlist.toggle(u));
  HTF.shortlist.list().reverse();
  assert.deepStrictEqual(plain(HTF.shortlist.list()), ['/a/', '/b/']);
});

test('an empty key is refused rather than stored', () => {
  const { HTF } = pageWith();
  assert.strictEqual(HTF.shortlist.toggle(''), false);
  assert.strictEqual(HTF.shortlist.count(), 0);
});

test('clear() empties it', () => {
  const { HTF, storage } = pageWith();
  HTF.shortlist.toggle('/a/');
  HTF.shortlist.clear();
  assert.strictEqual(HTF.shortlist.count(), 0);
  assert.strictEqual(storage.read(FOOD_KEY), '[]');
});

// --- persistence --------------------------------------------------------------

test('a toggle is written to localStorage under this site\'s own key', () => {
  const { HTF, storage } = pageWith();
  HTF.shortlist.toggle('/food/recipes/dal/');
  assert.deepStrictEqual(JSON.parse(storage.read(FOOD_KEY)), ['/food/recipes/dal/']);
});

test('what a previous visit wrote is read back', () => {
  const stored = workingStorage({ [FOOD_KEY]: JSON.stringify(['/food/recipes/dal/']) });
  const { HTF } = pageWith(stored);
  assert.strictEqual(HTF.shortlist.has('/food/recipes/dal/'), true);
});

test('the two sites keep two lists, from one localStorage', () => {
  // Both sites are served from one origin, so this is the same store. Helen
  // asked for two lists rather than a mixed one; HTF.site is what separates
  // them, and this is the check that it does.
  const shared = workingStorage();
  const food = pageWith(shared, 'food');
  const cocktails = pageWith(shared, 'cocktails');

  food.HTF.shortlist.toggle('/food/recipes/dal/');
  cocktails.HTF.shortlist.toggle('/cocktails/drinks/negroni/');

  assert.deepStrictEqual(plain(food.HTF.shortlist.list()), ['/food/recipes/dal/']);
  assert.deepStrictEqual(plain(cocktails.HTF.shortlist.list()), ['/cocktails/drinks/negroni/']);
  assert.ok(shared.read('htf-shortlist-food-v1'));
  assert.ok(shared.read('htf-shortlist-cocktails-v1'));
});

test('a page with no site-key has no store at all, and does not throw', () => {
  // The root landing page. A shared key would be a third list appearing under
  // a name neither site reads.
  const shared = workingStorage();
  const { HTF } = pageWith(shared, '');
  assert.strictEqual(HTF.shortlist.toggle('/anything/'), true);
  assert.strictEqual(HTF.shortlist.count(), 1, 'the click still responds');
  assert.deepStrictEqual(shared.keys(), [], 'but nothing is persisted');
});

// --- stored state is untrusted input ------------------------------------------

test('a stored value that is not an array reads as an empty shortlist', () => {
  [JSON.stringify({ dal: true }), JSON.stringify('dal'), 'not json at all', '7']
    .forEach((raw) => {
      const { HTF } = pageWith(workingStorage({ [FOOD_KEY]: raw }));
      assert.deepStrictEqual(plain(HTF.shortlist.list()), [], `for stored ${raw}`);
    });
});

test('non-string entries are dropped, and the rest of the list survives', () => {
  const raw = JSON.stringify(['/a/', 42, null, { url: '/b/' }, '/c/']);
  const { HTF } = pageWith(workingStorage({ [FOOD_KEY]: raw }));
  assert.deepStrictEqual(plain(HTF.shortlist.list()), ['/a/', '/c/']);
});

test('a duplicated entry is read once, so toggling it off actually removes it', () => {
  // A hand-edited or older record could carry the same url twice; splice()
  // removes one occurrence, so a second copy would leave it apparently
  // shortlisted after being switched off.
  const raw = JSON.stringify(['/a/', '/a/']);
  const { HTF } = pageWith(workingStorage({ [FOOD_KEY]: raw }));
  assert.deepStrictEqual(plain(HTF.shortlist.list()), ['/a/']);
  HTF.shortlist.toggle('/a/');
  assert.strictEqual(HTF.shortlist.has('/a/'), false);
});

// --- storage that fights back --------------------------------------------------
// The rule this module has and HTF.indexMemory does not: a failed WRITE must
// still leave the click working for this visit. Nobody asked for an index-memory
// record, so losing one costs nothing; somebody just pressed this control.

test('setItem throwing (private mode) does not lose the click', () => {
  const { HTF } = pageWith({
    getItem: () => null,
    setItem: () => { throw new Error('QuotaExceededError'); }
  });
  assert.strictEqual(HTF.shortlist.toggle('/a/'), true);
  assert.strictEqual(HTF.shortlist.has('/a/'), true);
  assert.strictEqual(HTF.shortlist.count(), 1);
});

test('getItem throwing (site data blocked) reads as empty and still works', () => {
  const { HTF } = pageWith({
    getItem: () => { throw new Error('SecurityError'); },
    setItem: () => {}
  });
  assert.deepStrictEqual(plain(HTF.shortlist.list()), []);
  assert.strictEqual(HTF.shortlist.toggle('/a/'), true);
  assert.strictEqual(HTF.shortlist.has('/a/'), true);
});

test('no localStorage in the context at all is survivable', () => {
  // A bare `localStorage` reference is a ReferenceError, not undefined — the
  // third failure mode HTF.indexMemory's own comment names.
  const page = makePage({ 'base-url': '/', 'site-key': 'food' });
  load(['assets/js/assets.js'], page);
  assert.doesNotThrow(() => page.HTF.shortlist.list());
  assert.strictEqual(page.HTF.shortlist.toggle('/a/'), true);
  assert.strictEqual(page.HTF.shortlist.has('/a/'), true);
});
