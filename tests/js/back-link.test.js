// Tests for assets/js/back-link.js: the decision behind the back arrow on a
// recipe or cocktail page (#387). No DOM required.
//
// Run from the repo root, with the local Node runtime:
//
//   .node-runtime/node/bin/node --test tests/js/*.test.js
//
// The trap: a recipe opened in a new tab has the index as its referrer and one
// entry of session history, so history.back() does nothing and the arrow is
// inert with no error. Only a pure function lets a test pose that.
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const BL = require('../../assets/js/back-link.js');

const ORIGIN = 'https://deckofpandas.github.io';
const INDEX = ORIGIN + '/helen-triages/food/';
const RECIPE = ORIGIN + '/helen-triages/food/recipes/caramel/';

/** The arrow's own context, with one thing varied per test. */
function ctx(over) {
  return Object.assign({
    referrer: INDEX,
    linkHref: INDEX,
    origin: ORIGIN,
    historyLength: 2
  }, over);
}

test('clicked through from the index in the same tab: go back', () => {
  assert.strictEqual(BL.shouldGoBackToIndex(ctx()), true);
});

test('opened in a NEW TAB from the index: follow the link, do not call back', () => {
  // The referrer still says "the index", truthfully. The tab's history is
  // what makes back() a no-op, so history length is the deciding fact.
  assert.strictEqual(BL.shouldGoBackToIndex(ctx({ historyLength: 1 })), false);
});

test('history length of 0 is treated the same as 1', () => {
  assert.strictEqual(BL.shouldGoBackToIndex(ctx({ historyLength: 0 })), false);
});

test('no referrer at all — typed, bookmarked, or withheld: follow the link', () => {
  assert.strictEqual(BL.shouldGoBackToIndex(ctx({ referrer: '' })), false);
});

test('arrived from another site: follow the link', () => {
  assert.strictEqual(
    BL.shouldGoBackToIndex(ctx({ referrer: 'https://example.com/somewhere/' })),
    false
  );
});

test('arrived from another page on this site: follow the link', () => {
  // Index -> recipe A -> recipe B via a cross-recipe link in A's method. Going
  // back from B lands on A, which is not where an arrow pointing at the index
  // should take you.
  assert.strictEqual(BL.shouldGoBackToIndex(ctx({ referrer: RECIPE })), false);
});

test('came from the cocktails index while the arrow points at food: follow the link', () => {
  assert.strictEqual(
    BL.shouldGoBackToIndex(ctx({ referrer: ORIGIN + '/helen-triages/cocktails/' })),
    false
  );
});

test('a cocktail page returns to the cocktails index', () => {
  const cocktails = ORIGIN + '/helen-triages/cocktails/';
  assert.strictEqual(
    BL.shouldGoBackToIndex(ctx({ referrer: cocktails, linkHref: cocktails })),
    true
  );
});

test('a query string on the index still counts as coming from the index', () => {
  // Compared on pathname, so /food/?tag=soup does not disqualify the
  // shortcut: going back to a filtered index is more right, not less.
  assert.strictEqual(
    BL.shouldGoBackToIndex(ctx({ referrer: INDEX + '?tag=soup' })),
    true
  );
});

test('a fragment on the referrer still counts', () => {
  assert.strictEqual(
    BL.shouldGoBackToIndex(ctx({ referrer: INDEX + '#results' })),
    true
  );
});

test('an unparseable referrer does not throw: follow the link', () => {
  assert.strictEqual(BL.shouldGoBackToIndex(ctx({ referrer: 'not a url' })), false);
});

test('a same-path referrer on a DIFFERENT origin is refused', () => {
  // The pathname matching is only meaningful once the origin has been checked;
  // without that, any site could host /helen-triages/food/ and be trusted.
  assert.strictEqual(
    BL.shouldGoBackToIndex(ctx({ referrer: 'https://evil.example/helen-triages/food/' })),
    false
  );
});
