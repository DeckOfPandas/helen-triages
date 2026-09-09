// =============================================================================
// Tests for HTF.shortlist.snapshot() — GitHub issue #849.
//
// Run from the repo root:
//
//   node --test tests/js/*.test.js
//
// WHY A SEPARATE FILE FROM shortlist.test.js. That one is about the STORE's
// behaviour under a hostile localStorage -- private mode throwing, a record
// left by an older build, a failed write that must not cost you the click. This
// is about one derived VALUE and the single judgement inside it, which is
// worth naming rather than burying among thirty storage tests.
//
// THE JUDGEMENT UNDER TEST: the glasses and portions maps are deliberately
// sparse and self-healing -- a drink dropped from the list leaves its number
// behind because nothing reads it -- which is right for storage and wrong for
// an export. A dump carrying a count for something not on the list states a
// fact the list itself contradicts, and anyone reading it (a person, or #850's
// importer) would have to know the self-healing rule to discount it. So the
// snapshot filters both maps to what is actually shortlisted, and that is the
// thing most likely to be "simplified" back out by someone who does not know
// why it is there.
//
// WHAT IS NOT TESTED HERE: the DOM half. assets/js/shortlist-export.js finds
// the textarea, fills it and subscribes to the change event; it needs a real
// document, and this harness stubs only enough page for a script to read two
// meta tags.
// =============================================================================
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { makePage, load } = require('./stub-dom.js');

/* ACROSS THE REALM BOUNDARY, so structural comparisons go through JSON --
   shortlist.test.js's own note explains why: a value built inside the vm
   context is an instance of THAT context's Array/Object. */
const plain = (value) => JSON.parse(JSON.stringify(value));

function workingStorage() {
  const data = new Map();
  return {
    getItem: (k) => (data.has(k) ? data.get(k) : null),
    setItem: (k, v) => { data.set(k, String(v)); },
    removeItem: (k) => { data.delete(k); }
  };
}

function pageWith(siteKey) {
  const page = makePage({
    'base-url': '/',
    'site-key': siteKey === undefined ? 'food' : siteKey
  });
  page.localStorage = workingStorage();
  load(['assets/js/assets.js'], page);
  return page.HTF;
}

// --- the shape ----------------------------------------------------------------

test('an empty shortlist exports an empty but complete document', () => {
  const HTF = pageWith();
  assert.deepStrictEqual(plain(HTF.shortlist.snapshot()), {
    version: 1,
    site: 'food',
    entries: [],
    glasses: {},
    portions: {}
  });
});

test('the site is named, so a dump cannot be pasted into the wrong index blind', () => {
  assert.strictEqual(pageWith('cocktails').shortlist.snapshot().site, 'cocktails');
  assert.strictEqual(pageWith('food').shortlist.snapshot().site, 'food');
});

test('entries keep the order they were marked in', () => {
  const HTF = pageWith();
  ['/a/', '/b/', '/c/'].forEach((u) => HTF.shortlist.toggle(u));
  assert.deepStrictEqual(plain(HTF.shortlist.snapshot().entries), ['/a/', '/b/', '/c/']);
});

test('the snapshot is a copy — mutating it cannot reach the store', () => {
  const HTF = pageWith();
  HTF.shortlist.toggle('/a/');
  const snap = HTF.shortlist.snapshot();
  snap.entries.push('/never-marked/');
  assert.deepStrictEqual(plain(HTF.shortlist.snapshot().entries), ['/a/']);
});

// --- counts -------------------------------------------------------------------

test('a glasses count is exported when one has been set', () => {
  const HTF = pageWith('cocktails');
  HTF.shortlist.toggle('/cocktails/negroni/');
  HTF.shortlist.setGlasses('/cocktails/negroni/', 3);
  assert.deepStrictEqual(plain(HTF.shortlist.snapshot().glasses),
    { '/cocktails/negroni/': 3 });
});

test('a default of one glass is absent, because a missing entry IS one', () => {
  const HTF = pageWith('cocktails');
  HTF.shortlist.toggle('/cocktails/negroni/');
  assert.deepStrictEqual(plain(HTF.shortlist.snapshot().glasses), {});
});

test('portions are exported alongside, and are a separate map', () => {
  const HTF = pageWith();
  HTF.shortlist.toggle('/food/dal/');
  HTF.shortlist.setPortions('/food/dal/', 2);
  const snap = HTF.shortlist.snapshot();
  assert.deepStrictEqual(plain(snap.portions), { '/food/dal/': 2 });
  assert.deepStrictEqual(plain(snap.glasses), {});
});

// --- THE JUDGEMENT ------------------------------------------------------------

test('a count left behind by an UNSHORTLISTED entry is not exported', () => {
  const HTF = pageWith('cocktails');
  HTF.shortlist.toggle('/cocktails/negroni/');
  HTF.shortlist.setGlasses('/cocktails/negroni/', 4);
  // Drop it from the list. The store deliberately leaves the 4 behind: the map
  // is sparse and self-healing, and nothing reads a count for something absent.
  HTF.shortlist.toggle('/cocktails/negroni/');

  const snap = HTF.shortlist.snapshot();
  assert.deepStrictEqual(plain(snap.entries), []);
  assert.deepStrictEqual(plain(snap.glasses), {},
    'the export must not state a count for a drink it also says is not listed');
});

test('the same holds for portions', () => {
  const HTF = pageWith();
  HTF.shortlist.toggle('/food/dal/');
  HTF.shortlist.setPortions('/food/dal/', 6);
  HTF.shortlist.toggle('/food/dal/');
  assert.deepStrictEqual(plain(HTF.shortlist.snapshot().portions), {});
});

test('a surviving entry keeps its count when a NEIGHBOUR is dropped', () => {
  const HTF = pageWith('cocktails');
  ['/a/', '/b/'].forEach((u) => HTF.shortlist.toggle(u));
  HTF.shortlist.setGlasses('/a/', 2);
  HTF.shortlist.setGlasses('/b/', 5);
  HTF.shortlist.toggle('/b/');

  const snap = HTF.shortlist.snapshot();
  assert.deepStrictEqual(plain(snap.entries), ['/a/']);
  assert.deepStrictEqual(plain(snap.glasses), { '/a/': 2 });
});

// --- it survives the thing it exists for --------------------------------------

test('the snapshot round-trips through JSON unchanged', () => {
  const HTF = pageWith('cocktails');
  ['/a/', '/b/'].forEach((u) => HTF.shortlist.toggle(u));
  HTF.shortlist.setGlasses('/a/', 2);
  const snap = plain(HTF.shortlist.snapshot());
  assert.deepStrictEqual(JSON.parse(JSON.stringify(snap)), snap);
});

test('clear() empties the export too, counts included', () => {
  const HTF = pageWith('cocktails');
  HTF.shortlist.toggle('/a/');
  HTF.shortlist.setGlasses('/a/', 9);
  HTF.shortlist.clear();
  assert.deepStrictEqual(plain(HTF.shortlist.snapshot()), {
    version: 1, site: 'cocktails', entries: [], glasses: {}, portions: {}
  });
});
