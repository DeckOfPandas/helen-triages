// =============================================================================
// Tests for assets/js/filter-state.js — the index's filter query-string
// grammar (GitHub issue #40), no DOM required.
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
const FS = require('../../assets/js/filter-state.js');

test('the documented example parses to the documented shape', () => {
  assert.deepStrictEqual(
    FS.parseQuery('?star=lamb&tag=soup,make-ahead'),
    { star: ['lamb'], tag: ['soup', 'make-ahead'] }
  );
});

test('a leading ? is optional', () => {
  assert.deepStrictEqual(FS.parseQuery('star=lamb'), { star: ['lamb'], tag: [] });
});

// --- the + trap ---------------------------------------------------------------
// Jekyll's url_encode is CGI.escape, which spells a space as `+`, and
// decodeURIComponent does not undo that. Six real taxonomy values contain a
// space, and they are among the first things anyone will click.

test('+ decodes to a space -- Jekyll url_encode spells a space that way', () => {
  assert.deepStrictEqual(FS.parseQuery('?star=oily+fish').star, ['oily fish']);
});

test('every space-bearing taxonomy value survives the + round trip', () => {
  const encoded = 'tag=carbs+party,hot+snack,ice+cream,one-handed+food&star=root+veg';
  const parsed = FS.parseQuery(encoded);
  assert.deepStrictEqual(parsed.tag, ['carbs party', 'hot snack', 'ice cream', 'one-handed food']);
  assert.deepStrictEqual(parsed.star, ['root veg']);
});

test('%20 works too -- a hand-written or browser-normalised URL is not a special case', () => {
  assert.deepStrictEqual(FS.parseQuery('?star=oily%20fish').star, ['oily fish']);
});

test('a genuine plus, spelled %2B, stays a plus rather than becoming a space', () => {
  assert.deepStrictEqual(FS.parseQuery('?tag=a%2Bb').tag, ['a+b']);
});

// --- the reserved leading hyphen ---------------------------------------------

test('interior hyphens are not signs: make-ahead and no-cook stay positive', () => {
  assert.deepStrictEqual(
    FS.parseQuery('?tag=make-ahead,no-cook,one-handed+food').tag,
    ['make-ahead', 'no-cook', 'one-handed food']
  );
});

test('a leading - is reserved for exclusion (#52) and is dropped, not read as a tag name', () => {
  assert.deepStrictEqual(FS.parseQuery('?tag=soup,-fakeaway').tag, ['soup']);
});

test('a percent-encoded leading hyphen is the same claim and is dropped too', () => {
  assert.deepStrictEqual(FS.parseQuery('?tag=%2Dfakeaway').tag, []);
});

test('a bare - names nothing and is dropped', () => {
  assert.deepStrictEqual(FS.parseQuery('?tag=-').tag, []);
});

// --- tolerance ----------------------------------------------------------------
// Same policy cook-timer.js applies to ?protein=beef: a bad query string is
// not worth an error on a page that works fine without it.

test('an empty string parses to empty, with every known kind still present', () => {
  assert.deepStrictEqual(FS.parseQuery(''), { star: [], tag: [] });
});

test('undefined and a bare ? parse to empty rather than throwing', () => {
  assert.deepStrictEqual(FS.parseQuery(undefined), { star: [], tag: [] });
  assert.deepStrictEqual(FS.parseQuery('?'), { star: [], tag: [] });
});

test('unknown parameters are ignored, and do not become keys', () => {
  const parsed = FS.parseQuery('?protein=beef&tag=soup&utm_source=newsletter');
  assert.deepStrictEqual(parsed, { star: [], tag: ['soup'] });
});

test('a parameter with no value at all says nothing', () => {
  assert.deepStrictEqual(FS.parseQuery('?tag&star=lamb'), { star: ['lamb'], tag: [] });
});

test('empty values between commas are dropped, not returned as empty strings', () => {
  assert.deepStrictEqual(FS.parseQuery('?tag=soup,,salad,').tag, ['soup', 'salad']);
});

test('a malformed percent escape drops that value instead of throwing', () => {
  assert.deepStrictEqual(FS.parseQuery('?tag=%zz,soup').tag, ['soup']);
});

test('a repeated value appears once', () => {
  assert.deepStrictEqual(FS.parseQuery('?tag=soup,soup&tag=soup').tag, ['soup']);
});

test('a kind repeated as two parameters accumulates rather than overwriting', () => {
  assert.deepStrictEqual(FS.parseQuery('?tag=soup&tag=salad').tag, ['soup', 'salad']);
});

test('arity is the caller\'s business -- two stars both come back', () => {
  assert.deepStrictEqual(FS.parseQuery('?star=lamb,beef').star, ['lamb', 'beef']);
});

test('KINDS is exported so filters.js and the tests agree on what exists', () => {
  assert.deepStrictEqual(FS.KINDS, ['star', 'tag']);
});

test('toQuery is deliberately absent until something writes the URL back', () => {
  assert.strictEqual(FS.toQuery, undefined);
});
