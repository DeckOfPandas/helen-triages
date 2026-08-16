// =============================================================================
// Tests for assets/js/filter-state.js — the index's filter query-string
// grammar (GitHub issue #40) and its filter STATE SHAPE (issue #52, step
// one). No DOM required.
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

// =============================================================================
// THE STATE SHAPE — GitHub issue #52, step one
// =============================================================================
//
// The bug these exist to end happened three times in two days, always the same
// shape: filters.js's clearAllFilters() emptied N pieces of state and the
// clear-all button's visibility predicate checked N-1, so the button hid while
// it still had work to do. nameQuery was missed; then isSearching was missed;
// before that two rival copies of the predicate disagreed with each other.
// Every one was found by eye, on the page.
//
// THE CASES BELOW ARE GENERATED FROM FS.FIELDS, NOT LISTED BY HAND. A
// hand-written list of six cases has precisely the omission problem it is
// meant to catch: the day someone adds a seventh field, the hand-written list
// is quietly one short again and passes. Generated, a new field is covered by
// the same line that declares it.

// A non-empty value for a field, derived from that field's OWN empty value, so
// this helper needs nothing per-field written down either. A field whose empty
// value is of a kind not handled here throws loudly rather than being skipped
// — a skipped field is the whole bug.
function aNonEmptyValueLike(emptyValue, field) {
  if (emptyValue && typeof emptyValue.size === 'number') return new Set(['something']);
  if (emptyValue === '') return 'something';
  if (emptyValue === null) return 'something';
  if (emptyValue === false) return true;
  throw new Error(
    `filter-state.test.js does not know how to build a non-empty value for ` +
    `field "${field}" (empty value: ${JSON.stringify(emptyValue)}). Teach ` +
    `aNonEmptyValueLike() about this kind — do not skip the field.`
  );
}

function stateWithOnly(field) {
  const state = FS.emptyState();
  state[field] = aNonEmptyValueLike(state[field], field);
  return state;
}

test('FIELDS is not empty, and is exactly the keys of a cleared state', () => {
  assert.ok(FS.FIELDS.length > 0, 'FIELDS must name at least one field');
  assert.deepStrictEqual(Object.keys(FS.emptyState()).sort(), FS.FIELDS.slice().sort());
});

test('a cleared state has nothing to clear', () => {
  assert.strictEqual(FS.hasAnythingToClear(FS.emptyState()), false);
  assert.strictEqual(FS.isEmpty(FS.emptyState()), true);
  assert.strictEqual(FS.hasNarrowingFilter(FS.emptyState()), false);
});

// --- the load-bearing one -----------------------------------------------------
// One generated case per field. This is the test that would have caught all
// three of the real bugs at once, and caught them before the page did.

FS.FIELDS.forEach((field) => {
  test(`with only "${field}" set, there is something to clear`, () => {
    const state = stateWithOnly(field);
    assert.strictEqual(
      FS.hasAnythingToClear(state), true,
      `hasAnythingToClear() ignores the "${field}" field. clear-all empties ` +
      `every field in FIELDS, so the clear button would hide while it still ` +
      `had work to do — the exact defect issue #52 exists to make impossible.`
    );
    assert.strictEqual(FS.isEmpty(state), false, `isEmpty() ignores the "${field}" field.`);
  });
});

// The mirror of the above: nothing may be *only* narrowing. If a field
// narrows the list, clear-all had better be able to clear it.
FS.NARROWING_FIELDS.forEach((field) => {
  test(`"${field}" narrows the list, so it must also be clearable`, () => {
    assert.strictEqual(FS.hasNarrowingFilter(stateWithOnly(field)), true);
    assert.strictEqual(FS.hasAnythingToClear(stateWithOnly(field)), true);
  });
});

test('NARROWING_FIELDS is a subset of FIELDS -- no filter exists outside the shape', () => {
  FS.NARROWING_FIELDS.forEach((f) => {
    assert.ok(FS.FIELDS.indexOf(f) !== -1, `${f} narrows but is not a declared field`);
  });
});

// --- hasNarrowingFilter is a DIFFERENT question, and must stay different -----
// Issue #248: collapsing it into hasAnythingToClear would trade a documented
// difference for a silent behaviour change at whichever call site lost its own
// answer. It feeds suppressList only.

test('hasNarrowingFilter EXCLUDES ingredient -- it is nulled on every keystroke', () => {
  const state = stateWithOnly('ingredient');
  assert.strictEqual(FS.hasNarrowingFilter(state), false);
  assert.strictEqual(FS.hasAnythingToClear(state), true);
});

test('hasNarrowingFilter EXCLUDES isSearching -- it is the state being asked about', () => {
  const state = stateWithOnly('isSearching');
  assert.strictEqual(FS.hasNarrowingFilter(state), false);
  assert.strictEqual(FS.hasAnythingToClear(state), true);
});

test('hasNarrowingFilter INCLUDES nameQuery -- a title search keeps the list on screen', () => {
  assert.strictEqual(FS.hasNarrowingFilter(stateWithOnly('nameQuery')), true);
});

test('hasNarrowingFilter INCLUDES tags, star and meta', () => {
  ['tags', 'star', 'meta'].forEach((field) => {
    assert.strictEqual(FS.hasNarrowingFilter(stateWithOnly(field)), true, field);
  });
});

test('the two predicates are genuinely two -- some field separates them', () => {
  const onlyClearable = FS.FIELDS.filter((f) => FS.NARROWING_FIELDS.indexOf(f) === -1);
  assert.ok(
    onlyClearable.length > 0,
    'every field now narrows, so hasNarrowingFilter and hasAnythingToClear ' +
    'have become the same question. If that is genuinely true, delete one ' +
    'of them deliberately rather than leaving two names for one answer.'
  );
});

// --- clearing ------------------------------------------------------------------

test('clearing returns something equal to a fresh empty state', () => {
  const dirty = FS.emptyState();
  FS.FIELDS.forEach((f) => { dirty[f] = aNonEmptyValueLike(FS.emptyState()[f], f); });
  assert.strictEqual(FS.hasAnythingToClear(dirty), true);
  assert.deepStrictEqual(FS.emptyState(), FS.emptyState());
  assert.strictEqual(FS.isEmpty(FS.emptyState()), true);
});

test('emptyState hands out FRESH collections, never one shared Set', () => {
  const a = FS.emptyState();
  const b = FS.emptyState();
  FS.FIELDS.forEach((f) => {
    if (a[f] && typeof a[f].size === 'number') {
      assert.notStrictEqual(a[f], b[f], `${f} is the same Set object in two states`);
      a[f].add('x');
      assert.strictEqual(b[f].size, 0, `mutating ${f} in one state reached another`);
    }
  });
});

// --- isFieldSet ----------------------------------------------------------------
// The generic "does this field hold anything?" that means a new field needs no
// predicate of its own.

test('isFieldSet answers from the value, for every kind the shape uses', () => {
  assert.strictEqual(FS.isFieldSet(new Set()), false);
  assert.strictEqual(FS.isFieldSet(new Set(['soup'])), true);
  assert.strictEqual(FS.isFieldSet(null), false);
  assert.strictEqual(FS.isFieldSet('lamb'), true);
  assert.strictEqual(FS.isFieldSet(''), false);
  assert.strictEqual(FS.isFieldSet(false), false);
  assert.strictEqual(FS.isFieldSet(true), true);
  assert.strictEqual(FS.isFieldSet(undefined), false);
});

test('a missing or undefined state is answered, not thrown at', () => {
  assert.strictEqual(FS.hasAnythingToClear(undefined), false);
  assert.strictEqual(FS.hasNarrowingFilter(undefined), false);
  assert.strictEqual(FS.hasAnythingToClear({}), false);
});
