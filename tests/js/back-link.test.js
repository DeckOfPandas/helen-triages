// =============================================================================
// Tests for assets/js/back-link.js — the decision behind the back arrow on a
// recipe or cocktail page (GitHub issue #387), no DOM required.
//
// Run from the repo root, with the local Node runtime:
//
//   .node-runtime/node/bin/node --test tests/js/*.test.js
//
// See tests/js/ingredient-search.test.js for why not the system node.
//
// WHY THIS FILE EXISTS. The first version of back-link.js checked the referrer
// and nothing else, which is correct for the case everyone pictures and wrong
// for the one Helen asked about within a minute of reading it: opening a recipe
// in a NEW TAB. Those index links carry no rel="noreferrer", so the new tab's
// referrer is the index and the check passed — while the tab's session history
// held one entry and history.back() did nothing at all. The arrow was inert,
// with no error and nothing on screen to explain it.
//
// That is invisible to every other kind of check here: the markup is right, the
// href resolves, the class has a rule, the page builds. It is only visible if
// you can pose "you came from the index, but this tab has no history", which is
// exactly what a pure function lets a test do and a browser does not.
// =============================================================================
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
  // The referrer still says "the index" and says it truthfully. The tab's
  // history is what makes back() a no-op, so history length is the deciding
  // fact and the referrer alone is not enough. This is the case the first
  // version of back-link.js got wrong.
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
  // Compared on pathname, so a future /food/?tag=soup does not disqualify the
  // shortcut — and going back to it is more right, not less.
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
