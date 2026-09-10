// shortlist-view.test.js
// =============================================================================
// THE SHORTLIST IS A VIEW, NOT A FACET -- GitHub issue #918.
// =============================================================================
// Helen, 2026-09-10, fourteen steps and four surprises, all of them the
// shortlisted filter ANDing with a title search: shortlist one recipe, type
// "lasa", shortlist the lasagne, press `shortlisted (2)` and see ONE recipe;
// type "duck" while the view is on and see NONE. She called it a bug rather
// than a preference, and the rule that removes it is two functions in
// filter-state.js, generated here across BOTH field tables so neither index
// can quietly keep composing:
//
//   enterShortlistView()          everything cleared, `shortlisted` true
//   reconcileShortlistView(state) the view gives way to any other set field,
//                                 except a half-typed search (`keepsView`)
//
// Pure functions over a spec, no DOM -- the same argument filter-state.test.js
// makes for everything else in that module.
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const FS = require('../../assets/js/filter-state.js');

const TABLES = { food: FS.FOOD_FIELDS, cocktails: FS.COCKTAIL_FIELDS };

// A non-empty value of the right shape for a field, from its own factory.
function filled(spec, field) {
  const empty = spec[field].empty();
  if (empty && typeof empty.size === 'number') return new Set(['x']);
  if (typeof empty === 'string') return 'x';
  if (typeof empty === 'boolean') return true;
  return 'x';
}

Object.keys(TABLES).forEach((name) => {
  const spec = TABLES[name];
  const B = FS.create(spec);

  test(`${name}: both tables declare shortlisted, or this rule has nothing to hold`, () => {
    assert.ok('shortlisted' in spec, `${name} has no shortlisted field`);
  });

  test(`${name}: entering the view sets shortlisted and NOTHING else`, () => {
    const s = B.enterShortlistView();
    assert.strictEqual(s.shortlisted, true);
    Object.keys(spec).forEach((f) => {
      if (f === 'shortlisted') return;
      assert.strictEqual(FS.isFieldSet(s[f]), false, `${f} survived entering the view`);
    });
  });

  test(`${name}: entering the view hands out FRESH collections`, () => {
    const a = B.enterShortlistView();
    const b = B.enterShortlistView();
    Object.keys(spec).forEach((f) => {
      if (a[f] && typeof a[f].size === 'number') assert.notStrictEqual(a[f], b[f], `${f} is shared`);
    });
  });

  test(`${name}: the view alone is left alone`, () => {
    const s = B.enterShortlistView();
    assert.strictEqual(B.reconcileShortlistView(s), false);
    assert.strictEqual(s.shortlisted, true);
  });

  test(`${name}: a state with the view off is never touched`, () => {
    const s = B.emptyState();
    s.nameQuery = 'duck';
    assert.strictEqual(B.reconcileShortlistView(s), false);
    assert.strictEqual(s.shortlisted, false);
    assert.strictEqual(s.nameQuery, 'duck');
  });

  Object.keys(spec).forEach((field) => {
    if (field === 'shortlisted') return;
    if (spec[field].keepsView) {
      test(`${name}: "${field}" is a half-typed search and KEEPS the view`, () => {
        const s = B.enterShortlistView();
        s[field] = filled(spec, field);
        assert.strictEqual(B.reconcileShortlistView(s), false,
          `typing into a box narrows nothing yet, so it must not leave the view`);
        assert.strictEqual(s.shortlisted, true);
      });
    } else {
      test(`${name}: setting "${field}" while the view is on LEAVES the view`, () => {
        const s = B.enterShortlistView();
        s[field] = filled(spec, field);
        assert.strictEqual(B.reconcileShortlistView(s), true,
          `"${field}" composed with the shortlist -- the exact surprise #918 describes`);
        assert.strictEqual(s.shortlisted, false);
        assert.strictEqual(FS.isFieldSet(s[field]), true, `the filter that was set must survive`);
      });
    }
  });

  test(`${name}: every keepsView field is a non-narrowing flag, never a real filter`, () => {
    Object.keys(spec).forEach((f) => {
      if (spec[f].keepsView) {
        assert.strictEqual(spec[f].narrows, false, `${f} narrows the list and cannot keep the view`);
        assert.strictEqual(typeof spec[f].empty(), 'boolean', `${f} is not a flag`);
      }
    });
  });
});

test('the food-shaped exports carry the two functions, so filters.js can call them unqualified', () => {
  assert.strictEqual(typeof FS.enterShortlistView, 'function');
  assert.strictEqual(typeof FS.reconcileShortlistView, 'function');
  assert.strictEqual(FS.enterShortlistView().shortlisted, true);
});

test('a missing state is answered, not thrown at', () => {
  assert.strictEqual(FS.reconcileShortlistView(undefined), false);
});
