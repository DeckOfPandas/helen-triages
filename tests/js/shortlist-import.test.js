// =============================================================================
// Tests for HTF.shortlist.restore() — GitHub issue #850.
//
// Run from the repo root:
//
//   node --test tests/js/*.test.js
//
// WHY A SEPARATE FILE FROM shortlist-export.test.js. That one is about the
// snapshot and its single judgement (a count for an unlisted entry is not
// exported). This is the return journey, and it carries THREE judgements that
// are each the kind of thing a later reader would "simplify" away without
// knowing why they are there:
//
//   1. ENTRIES MATCH BY SLUG, NOT BY KEY. Helen's real dump names
//      `/cocktails/drafts/to-promote/aviation/` from before the drink was
//      promoted; the live card says `/cocktails/recipes/aviation/`. A key-equal
//      match would restore nothing from any dump older than the site.
//   2. IT MERGES. What is already marked stays; a number already set in this
//      browser beats the dump's, because the dump is old by definition.
//   3. NOTHING IS DROPPED IN SILENCE. An entry no card answers to comes back
//      by slug, so the person can finish the job by hand -- a renamed drink is
//      exactly that case, and Helen's own dump has one.
//
// WHAT IS NOT TESTED HERE: the DOM half. assets/js/shortlist-export.js reads
// the paste box, collects the page's keys and prints the result; it needs a
// real document, and this harness stubs only enough page for a script to read
// two meta tags.
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
    read: (k) => data.get(k)
  };
}

function pageWith(siteKey, storage) {
  const page = makePage({
    'base-url': '/',
    'site-key': siteKey === undefined ? 'cocktails' : siteKey
  });
  page.localStorage = storage || workingStorage();
  load(['assets/js/assets.js'], page);
  return page.HTF;
}

/* The keys a live cocktails index carries today, in the shape the cards emit. */
const LIVE = [
  '/cocktails/recipes/aviation/',
  '/cocktails/recipes/between-the-sheets/',
  '/cocktails/recipes/negroni/',
  '/cocktails/recipes/pear-apricot-and-rosemary-bellini/'
];

/* The shape Helen's real dump has: draft keys from before promotion, and one
   drink whose slug has since changed. */
const OLD_DUMP = {
  version: 1,
  site: 'cocktails',
  entries: [
    '/cocktails/drafts/between-the-sheets/',
    '/cocktails/drafts/to-promote/pear-apricot-honey-lemon-and-rosemary-bellini/',
    '/cocktails/drafts/to-promote/aviation/'
  ],
  glasses: {
    '/cocktails/drafts/between-the-sheets/': 12,
    '/cocktails/drafts/to-promote/pear-apricot-honey-lemon-and-rosemary-bellini/': 12,
    '/cocktails/drafts/to-promote/aviation/': 12
  },
  portions: {}
};

// --- the round trip -----------------------------------------------------------

test('a snapshot restores into an empty store, exactly', () => {
  const HTF = pageWith();
  HTF.shortlist.toggle(LIVE[0]);
  HTF.shortlist.toggle(LIVE[2]);
  HTF.shortlist.setGlasses(LIVE[2], 3);
  const dump = plain(HTF.shortlist.snapshot());
  HTF.shortlist.clear();

  const result = HTF.shortlist.restore(dump, LIVE);
  assert.strictEqual(result.ok, true);
  assert.strictEqual(result.restored, 2);
  assert.strictEqual(result.added, 2);
  assert.deepStrictEqual(plain(result.unmatched), []);
  assert.deepStrictEqual(plain(HTF.shortlist.snapshot()), dump);
});

test('the pasted TEXT is accepted, not only a parsed object', () => {
  const HTF = pageWith();
  const result = HTF.shortlist.restore(JSON.stringify(OLD_DUMP, null, 2), LIVE);
  assert.strictEqual(result.ok, true);
  assert.strictEqual(result.restored, 2);
});

test('what is restored is persisted, under this site\'s own keys', () => {
  const storage = workingStorage();
  const HTF = pageWith('cocktails', storage);
  HTF.shortlist.restore(OLD_DUMP, LIVE);
  assert.deepStrictEqual(
    JSON.parse(storage.read('htf-shortlist-cocktails-v1')),
    [LIVE[1], LIVE[0]]
  );
  assert.deepStrictEqual(
    JSON.parse(storage.read('htf-shortlist-glasses-cocktails-v1')),
    { [LIVE[1]]: 12, [LIVE[0]]: 12 }
  );
});

// --- JUDGEMENT 1: by slug -----------------------------------------------------

test('an old draft key resolves to the live drink with the same slug, and the LIVE key is stored', () => {
  const HTF = pageWith();
  HTF.shortlist.restore(OLD_DUMP, LIVE);
  assert.strictEqual(HTF.shortlist.has('/cocktails/recipes/aviation/'), true);
  assert.strictEqual(HTF.shortlist.has('/cocktails/drafts/to-promote/aviation/'), false,
    'the stale key must not be written back -- nothing on the page reads it');
});

test('the count rides across to the live key', () => {
  const HTF = pageWith();
  HTF.shortlist.restore(OLD_DUMP, LIVE);
  assert.strictEqual(HTF.shortlist.glasses('/cocktails/recipes/aviation/'), 12);
});

test('the slug match is case-insensitive and ignores a missing trailing slash', () => {
  const HTF = pageWith();
  const result = HTF.shortlist.restore(
    { entries: ['/cocktails/recipes/Negroni', 'aviation'] }, LIVE);
  assert.strictEqual(result.restored, 2);
  assert.strictEqual(HTF.shortlist.has('/cocktails/recipes/negroni/'), true);
  assert.strictEqual(HTF.shortlist.has('/cocktails/recipes/aviation/'), true);
});

// --- JUDGEMENT 2: merge -------------------------------------------------------

test('what was already shortlisted stays, and is counted as restored but not added', () => {
  const HTF = pageWith();
  HTF.shortlist.toggle(LIVE[2]);          // the negroni, not in the dump
  HTF.shortlist.toggle(LIVE[0]);          // the aviation, in the dump
  const result = HTF.shortlist.restore(OLD_DUMP, LIVE);
  assert.strictEqual(result.restored, 2);
  assert.strictEqual(result.added, 1);
  assert.deepStrictEqual(plain(HTF.shortlist.list()), [LIVE[2], LIVE[0], LIVE[1]]);
});

test('a number already set in this browser is NOT overwritten by the dump\'s', () => {
  const HTF = pageWith();
  HTF.shortlist.toggle(LIVE[0]);
  HTF.shortlist.setGlasses(LIVE[0], 4);
  HTF.shortlist.restore(OLD_DUMP, LIVE);
  assert.strictEqual(HTF.shortlist.glasses(LIVE[0]), 4,
    'the number in front of you is newer than any dump');
  assert.strictEqual(HTF.shortlist.glasses(LIVE[1]), 12, 'but a gap is filled');
});

test('portions merge by the same rule, and one portion is a real number to carry', () => {
  const HTF = pageWith('food');
  const live = ['/food/recipes/dal/', '/food/recipes/moules-mariniere/'];
  HTF.shortlist.toggle(live[0]);
  HTF.shortlist.setPortions(live[0], 6);
  const result = HTF.shortlist.restore({
    site: 'food',
    entries: ['/food/drafts/dal/', '/food/drafts/moules-mariniere/'],
    glasses: {},
    portions: { '/food/drafts/dal/': 2, '/food/drafts/moules-mariniere/': 1 }
  }, live);
  assert.strictEqual(result.ok, true);
  assert.strictEqual(HTF.shortlist.portions(live[0]), 6);
  assert.strictEqual(HTF.shortlist.portions(live[1]), 1);
});

test('restoring the same dump twice changes nothing the second time', () => {
  const HTF = pageWith();
  HTF.shortlist.restore(OLD_DUMP, LIVE);
  const before = plain(HTF.shortlist.snapshot());
  const again = HTF.shortlist.restore(OLD_DUMP, LIVE);
  assert.strictEqual(again.added, 0);
  assert.strictEqual(again.restored, 2);
  assert.deepStrictEqual(plain(HTF.shortlist.snapshot()), before);
});

// --- JUDGEMENT 3: nothing dropped in silence ---------------------------------

test('an entry no card answers to is reported by slug, in order, once', () => {
  const HTF = pageWith();
  const result = HTF.shortlist.restore({
    entries: [
      '/cocktails/drafts/to-promote/pear-apricot-honey-lemon-and-rosemary-bellini/',
      '/cocktails/drafts/gone/',
      '/cocktails/drafts/to-promote/gone/'
    ]
  }, LIVE);
  assert.strictEqual(result.ok, true);
  assert.strictEqual(result.restored, 0);
  assert.deepStrictEqual(plain(result.unmatched),
    ['pear-apricot-honey-lemon-and-rosemary-bellini', 'gone']);
});

test('the renamed Bellini in Helen\'s real dump is the one unmatched entry', () => {
  // The live slug is pear-apricot-and-rosemary-bellini. Nothing here guesses
  // that; the report is what lets a person finish it by hand.
  const HTF = pageWith();
  const result = HTF.shortlist.restore(OLD_DUMP, LIVE);
  assert.deepStrictEqual(plain(result.unmatched),
    ['pear-apricot-honey-lemon-and-rosemary-bellini']);
  assert.strictEqual(HTF.shortlist.has(LIVE[3]), false,
    'and the live Bellini is not silently marked on its behalf');
});

// --- refusals ------------------------------------------------------------------

test('the other site\'s dump is refused, naming the site', () => {
  const HTF = pageWith('cocktails');
  const result = HTF.shortlist.restore(
    { site: 'food', entries: ['/food/recipes/dal/'] }, LIVE);
  assert.strictEqual(result.ok, false);
  assert.strictEqual(result.reason, 'wrong-site');
  assert.strictEqual(result.site, 'food');
  assert.strictEqual(HTF.shortlist.count(), 0, 'and nothing was written');
});

test('a dump with no site at all is judged on its entries', () => {
  const HTF = pageWith();
  const result = HTF.shortlist.restore({ entries: [LIVE[0]] }, LIVE);
  assert.strictEqual(result.ok, true);
  assert.strictEqual(result.restored, 1);
});

test('text that is not JSON is refused, and does not throw', () => {
  const HTF = pageWith();
  ['', '   ', 'not json', '{', '[1, 2]', '"a string"', '42'].forEach((text) => {
    let result;
    assert.doesNotThrow(() => { result = HTF.shortlist.restore(text, LIVE); }, text);
    assert.strictEqual(result.ok, false, JSON.stringify(text));
    assert.strictEqual(result.reason, 'unreadable', JSON.stringify(text));
  });
  assert.strictEqual(HTF.shortlist.count(), 0);
});

test('a document of the wrong shape is refused', () => {
  const HTF = pageWith();
  [null, undefined, 7, [], {}, { entries: 'aviation' }, { entries: { a: 1 } }]
    .forEach((doc) => {
      const result = HTF.shortlist.restore(doc, LIVE);
      assert.strictEqual(result.ok, false, JSON.stringify(doc));
      assert.strictEqual(result.reason, 'unreadable', JSON.stringify(doc));
    });
});

test('junk inside an otherwise good dump is skipped, not fatal', () => {
  const HTF = pageWith();
  const result = HTF.shortlist.restore({
    entries: [LIVE[0], 42, null, '', { url: LIVE[2] }, LIVE[2]],
    glasses: { [LIVE[0]]: 'six', [LIVE[2]]: -2 },
    portions: [1, 2]
  }, LIVE);
  assert.strictEqual(result.ok, true);
  assert.strictEqual(result.restored, 2);
  assert.strictEqual(HTF.shortlist.glasses(LIVE[0]), 1);
  assert.strictEqual(HTF.shortlist.glasses(LIVE[2]), 1);
});

test('a page with no cards restores nothing and reports every slug', () => {
  const HTF = pageWith();
  const result = HTF.shortlist.restore(OLD_DUMP, []);
  assert.strictEqual(result.ok, true);
  assert.strictEqual(result.restored, 0);
  assert.strictEqual(result.unmatched.length, 3);
});

test('an empty dump is a valid nothing', () => {
  const HTF = pageWith();
  const result = HTF.shortlist.restore(
    { version: 1, site: 'cocktails', entries: [], glasses: {}, portions: {} }, LIVE);
  assert.strictEqual(result.ok, true);
  assert.strictEqual(result.restored, 0);
  assert.deepStrictEqual(plain(result.unmatched), []);
});

// --- storage that fights back --------------------------------------------------

test('a failed write does not lose the restore for this visit', () => {
  const HTF = pageWith('cocktails', {
    getItem: () => null,
    setItem: () => { throw new Error('QuotaExceededError'); }
  });
  const result = HTF.shortlist.restore(OLD_DUMP, LIVE);
  assert.strictEqual(result.ok, true);
  assert.strictEqual(HTF.shortlist.has(LIVE[0]), true);
  assert.strictEqual(HTF.shortlist.glasses(LIVE[0]), 12);
});
