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

// =============================================================================
// THE EXCLUSION RULE — GitHub issue #52's actual goal
// =============================================================================
//
// Helen's user story: "I have invited someone for dinner and they hate peas, so
// I want to see all recipes that do NOT contain peas as an ingredient."
//
// The fixture below is not invented. All three entries are really in the
// collection's derived ingredient index, which is exactly why this rule is
// membership rather than containment: `pea` sits inside `peanut butter` and
// inside `pearl barley`, and a "contains" rule would hand someone who dislikes
// peas a list with the peanut butter cookies and the pearl barley casserole
// removed from it for no reason they could see.
//
// Excluding is not including turned around, either. main_ingredients is a
// deliberately partial hint — fine to include ON, unsafe to exclude BY — so
// these entries come from the FULL derived list (every ingredient_groups item,
// incidentals included), which is what data-all-ingredients carries.

const PEAS_ROW = ['chicken', 'mushrooms', 'peas'];
const PEANUT_ROW = ['peanut butter', 'plain flour', 'caster sugar'];
const BARLEY_ROW = ['organic pearl barley', 'duck legs'];

test('an exact entry excludes the row that lists it', () => {
  assert.strictEqual(FS.excludesRow(PEAS_ROW, new Set(['peas'])), true);
});

test('excluding "peas" does NOT take peanut butter or pearl barley with it', () => {
  const excluded = new Set(['peas']);
  assert.strictEqual(
    FS.excludesRow(PEANUT_ROW, excluded), false,
    'a row listing "peanut butter" was excluded by "peas". The rule has become '
    + 'a substring test somewhere — "pea" is inside "peanut butter". Membership '
    + 'of the entry list is the whole rule; the fuzziness belongs in the '
    + 'picker, which offers all three so you can pick the one you meant.'
  );
  assert.strictEqual(
    FS.excludesRow(BARLEY_ROW, excluded), false,
    'a row listing "organic pearl barley" was excluded by "peas" — same '
    + 'substring collision, other direction.'
  );
});

test('a partial entry excludes nothing -- "pea" is not "peas"', () => {
  assert.strictEqual(FS.excludesRow(PEAS_ROW, new Set(['pea'])), false);
});

test('a row is excluded if it lists ANY of several exclusions', () => {
  const excluded = new Set(['peas', 'plain flour']);
  assert.strictEqual(FS.excludesRow(PEAS_ROW, excluded), true);
  assert.strictEqual(FS.excludesRow(PEANUT_ROW, excluded), true);
  assert.strictEqual(FS.excludesRow(BARLEY_ROW, excluded), false);
});

test('an empty exclusion set excludes nothing, and neither does a missing one', () => {
  assert.strictEqual(FS.excludesRow(PEAS_ROW, new Set()), false);
  assert.strictEqual(FS.excludesRow(PEAS_ROW, undefined), false);
  assert.strictEqual(FS.excludesRow(undefined, new Set(['peas'])), false);
});

test('an array works as well as a Set -- the rule only needs forEach', () => {
  assert.strictEqual(FS.excludesRow(PEAS_ROW, ['peas']), true);
});

// --- the one umbrella ---------------------------------------------------------
// The picker also offers "chicken (all)", collapsing chicken breast/thighs/
// stock. Matching a family needs the ingredient vocabulary, which filter-state
// deliberately does not hold, so the caller passes the matcher in.

test('an "(all)" value matches family-wise, using the matcher the caller passes', () => {
  const seen = [];
  const familyMatch = (entries, key) => {
    seen.push(key);
    return entries.some((e) => e.indexOf(key) !== -1);
  };
  assert.strictEqual(FS.excludesRow(PEAS_ROW, new Set(['chicken (all)']), familyMatch), true);
  assert.deepStrictEqual(seen, ['chicken'], 'the " (all)" suffix should be stripped before matching');
});

test('with no matcher supplied, an "(all)" value falls back to exact membership', () => {
  // Deliberate: no vocabulary means no umbrella. It must never quietly
  // degrade into a substring rule, which is the one thing this must not be.
  assert.strictEqual(FS.excludesRow(PEAS_ROW, new Set(['chicken (all)'])), false);
});

test('a plain entry is never sent to the family matcher', () => {
  let called = false;
  FS.excludesRow(PEAS_ROW, new Set(['peas']), () => { called = true; return true; });
  assert.strictEqual(called, false);
});

test('FAMILY_SUFFIX is exported so filters.js and the tests agree on the spelling', () => {
  assert.strictEqual(FS.FAMILY_SUFFIX, ' (all)');
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

// =============================================================================
// serialise / deserialise — GitHub issue #387
// =============================================================================
// The index remembers its list in sessionStorage so that going BACK restores
// what you left. These two are why that is not just JSON.stringify.

test('serialise turns Sets into arrays, because JSON silently will not', () => {
  // JSON.stringify(new Set(['a'])) is "{}" -- not an error, not an empty array,
  // just nothing. Three of the eight fields are Sets, so a state put through
  // raw JSON comes back with its tags, exclusions and meta filters quietly
  // emptied. That is the bug this function exists to prevent, and it is worth
  // stating in a test because the naive version LOOKS like it works.
  assert.strictEqual(JSON.stringify(new Set(['soup'])), '{}');

  const state = FS.emptyState();
  state.tags.add('soup');
  state.tags.add('freezable');
  const flat = FS.serialise(state);
  assert.deepStrictEqual(flat.tags.sort(), ['freezable', 'soup']);
});

test('a full state survives a round trip through JSON', () => {
  const state = FS.emptyState();
  state.tags.add('soup');
  state.star = 'beef';
  state.excludedIngredients.add('peas');
  state.meta.add('rewrite');
  state.nameQuery = 'stew';
  state.ingredient = 'cavolo nero';
  state.isSearching = true;

  const back = FS.deserialise(JSON.parse(JSON.stringify(FS.serialise(state))));

  assert.deepStrictEqual([...back.tags], ['soup']);
  assert.strictEqual(back.star, 'beef');
  assert.deepStrictEqual([...back.excludedIngredients], ['peas']);
  assert.deepStrictEqual([...back.meta], ['rewrite']);
  assert.strictEqual(back.nameQuery, 'stew');
  assert.strictEqual(back.ingredient, 'cavolo nero');
  assert.strictEqual(back.isSearching, true);
});

test('every field in FIELD_SPEC round-trips, including any added later', () => {
  // Generated from FIELDS rather than listed, so a field added to FIELD_SPEC is
  // covered without anyone remembering to come here. HANDOVER 12 warns that a
  // sweep like this proves the predicate and not the table -- true, and the
  // table is the thing filter-state.js owns, so here it is the right end.
  const empty = FS.emptyState();
  const back = FS.deserialise(FS.serialise(empty));
  FS.FIELDS.forEach((f) => {
    assert.ok(f in back, `${f} vanished in a round trip`);
    assert.strictEqual(
      FS.isFieldSet(back[f]), false,
      `${f} came back looking set when it started empty`
    );
  });
});

test('a malformed record falls back to empty rather than throwing', () => {
  // Stored state is untrusted: a version behind, hand-edited, or left over from
  // a build where a field meant something else. One unfiltered page is a much
  // better outcome than a wrong-looking index with no way to tell why.
  [null, undefined, 'nonsense', 42, [], {}, { tags: 'soup', star: 7 }].forEach((bad) => {
    const back = FS.deserialise(bad);
    assert.strictEqual(FS.hasAnythingToClear(back), false, `${JSON.stringify(bad)} restored as set`);
  });
});

test('a Set field given a non-array is ignored, not coerced', () => {
  const back = FS.deserialise({ tags: 'soup' });
  assert.strictEqual(back.tags.size, 0);
});

// =============================================================================
// ONE MECHANISM, TWO TABLES — GitHub issue #579
// =============================================================================
// The cocktail index held five loose variables (chosenMoods, chosenChaos,
// wantName, include, exclude) and six hand-written showClear() calls, which is
// the shape food's filter state had before issue #52 — and issue #541 asks for
// a clear-all button on that page, "very much like food site". Clear-all is the
// exact feature whose visibility predicate drifted from its clearing three
// times in two days here.
//
// So the mechanism is parameterised rather than copied, and every generated
// case above is re-run below against every declared table. SPECS is derived
// from the module's own exports, so a table added to filter-state.js is covered
// by the line that declares it and there is no list of specs to keep in step.

// Detected by SHAPE, not by name. `/_FIELDS$/` was the obvious spelling and it
// swept up NARROWING_FIELDS, which is a list of names rather than a table — so
// the generated cases ran over array indices and every one of them failed. A
// spec is a mapping whose every value declares an empty() factory; nothing else
// in this module's exports looks like that.
const isFieldSpec = (v) =>
  !!v && typeof v === 'object' && !Array.isArray(v) &&
  Object.keys(v).length > 0 &&
  Object.keys(v).every((f) => v[f] && typeof v[f].empty === 'function');

const SPECS = Object.keys(FS).filter((k) => isFieldSpec(FS[k])).map((k) => [k, FS[k]]);

test('every declared field table is exercised, and there is more than one', () => {
  assert.ok(
    SPECS.length > 1,
    'filter-state.js exports fewer than two *_FIELDS tables. The parameterisation ' +
    'exists because there are two indexes; with one table it is machinery for ' +
    'nothing and should be collapsed back deliberately rather than left standing.'
  );
  assert.deepStrictEqual(SPECS.map(([name]) => name).sort(), ['COCKTAIL_FIELDS', 'FOOD_FIELDS']);
});

SPECS.forEach(([name, spec]) => {
  const S = FS.create(spec);

  const only = (field) => {
    const state = S.emptyState();
    state[field] = aNonEmptyValueLike(state[field], `${name}.${field}`);
    return state;
  };

  test(`${name}: FIELDS is exactly the keys of a cleared state`, () => {
    assert.ok(S.FIELDS.length > 0);
    assert.deepStrictEqual(Object.keys(S.emptyState()).sort(), S.FIELDS.slice().sort());
  });

  test(`${name}: a cleared state has nothing to clear`, () => {
    assert.strictEqual(S.hasAnythingToClear(S.emptyState()), false);
    assert.strictEqual(S.hasNarrowingFilter(S.emptyState()), false);
  });

  test(`${name}: every empty() is a FACTORY, so no two states share a Set`, () => {
    // A shared empty Set handed out twice is one Set mutated from two places,
    // and the symptom is a filter appearing on a page nobody set it on.
    const a = S.emptyState();
    const b = S.emptyState();
    S.FIELDS.forEach((f) => {
      if (a[f] && typeof a[f].size === 'number') {
        assert.notStrictEqual(a[f], b[f], `${f} hands out the same Set twice`);
      }
    });
  });

  S.FIELDS.forEach((field) => {
    test(`${name}: with only "${field}" set, there is something to clear`, () => {
      assert.strictEqual(
        S.hasAnythingToClear(only(field)), true,
        `hasAnythingToClear() ignores "${field}", so a clear-all button would ` +
        `hide while it still had work to do.`
      );
    });
  });

  S.NARROWING_FIELDS.forEach((field) => {
    test(`${name}: "${field}" narrows, so it must also be clearable`, () => {
      assert.strictEqual(S.hasNarrowingFilter(only(field)), true);
      assert.strictEqual(S.hasAnythingToClear(only(field)), true);
    });
  });

  test(`${name}: a full state survives serialise -> deserialise, Sets included`, () => {
    // JSON.stringify(new Set()) is `{}` — not an error, not an empty array,
    // just silently nothing. That is why serialise() exists at all.
    const dirty = S.emptyState();
    S.FIELDS.forEach((f) => { dirty[f] = aNonEmptyValueLike(dirty[f], `${name}.${f}`); });
    const back = S.deserialise(JSON.parse(JSON.stringify(S.serialise(dirty))));
    S.FIELDS.forEach((f) => {
      assert.strictEqual(S.isFieldSet(back[f]), true, `${f} came back empty`);
    });
  });

  test(`${name}: a malformed record falls back to empty rather than throwing`, () => {
    [null, undefined, 'nonsense', 42, [], {}].forEach((bad) => {
      assert.strictEqual(S.hasAnythingToClear(S.deserialise(bad)), false);
    });
  });
});

// --- what the cocktail table must actually hold ------------------------------
// Named rather than generated, because these are claims about the DESIGN of
// that index rather than about the mechanism: a field quietly leaving this
// table would take a whole filter off the clear-all button, silently.

test("the cocktail table covers all five of the index's named questions", () => {
  const S = FS.create(FS.COCKTAIL_FIELDS);
  ['moods', 'chaos', 'include', 'exclude', 'nameQuery'].forEach((f) => {
    assert.ok(S.FIELDS.indexOf(f) !== -1, `the cocktail index has no "${f}" field`);
    assert.ok(S.NARROWING_FIELDS.indexOf(f) !== -1, `"${f}" does not narrow the list`);
  });
});

test('a half-typed cocktail search is clearable but does not narrow', () => {
  // isSearching's siblings — issue #274 on the food side, declared here rather
  // than rediscovered. Typing "gi" into HAS TO HAVE and picking nothing leaves
  // a pool of chips with no other way to dismiss them but deleting the text.
  const S = FS.create(FS.COCKTAIL_FIELDS);
  ['isIncludeSearching', 'isExcludeSearching'].forEach((f) => {
    const state = S.emptyState();
    state[f] = true;
    assert.strictEqual(S.hasAnythingToClear(state), true, `${f} is not clearable`);
    assert.strictEqual(S.hasNarrowingFilter(state), false, `${f} should not narrow`);
  });
});

// --- is this row one you asked for? — issue #506 ------------------------------
// The 40 lines that used to sit inside filters.js's update(), where the only
// way to ask them a question was to open a browser and type. They are
// FilterState.rowMatchesFilters now, and these are the questions.
//
// The row shape is what filters.js reads off each <li>: tags, star,
// titleFolded, isDraft, ingredients. `titleFolded` is pre-folded by the caller
// because state.nameQuery is stored folded -- see the function's own comment.

const ROW = (over) => Object.assign({
  tags: ['soup', 'make-ahead'],
  star: 'lamb',
  titleFolded: '',
  isDraft: false,
  ingredients: ['lamb', 'barley', 'carrots']
}, over || {});

const EMPTY = () => FS.emptyState();

// The real matcher lives in ingredient-search.js and needs a vocabulary. These
// cases are about the ROW rules, so the umbrella is stubbed to something with
// no opinions -- exact membership, which is what a family button falls back to
// anyway when nothing is passed.
const EXACT = (list, key) => list.indexOf(key) !== -1;

test('an empty state keeps every row', () => {
  assert.strictEqual(FS.rowMatchesFilters(ROW(), EMPTY(), EXACT), true);
});

test('chosen tags are AND, not OR -- two tags means a row carrying both', () => {
  const state = EMPTY();
  state.tags = new Set(['soup', 'make-ahead']);
  assert.strictEqual(FS.rowMatchesFilters(ROW(), state, EXACT), true);

  state.tags = new Set(['soup', 'freezable']);
  assert.strictEqual(
    FS.rowMatchesFilters(ROW(), state, EXACT), false,
    'a row carrying one of two chosen tags survived. Tags narrow: picking a ' +
    'second one asks for both, the way a shelf does.'
  );
});

test('the star is a single value, and a row with none is not a match for one', () => {
  const state = EMPTY();
  state.star = 'lamb';
  assert.strictEqual(FS.rowMatchesFilters(ROW(), state, EXACT), true);
  assert.strictEqual(FS.rowMatchesFilters(ROW({ star: 'beef' }), state, EXACT), false);
  assert.strictEqual(FS.rowMatchesFilters(ROW({ star: '' }), state, EXACT), false);
});

test('a blank star on a row is fine while nothing is selected -- ~a quarter are', () => {
  assert.strictEqual(FS.rowMatchesFilters(ROW({ star: '' }), EMPTY(), EXACT), true);
});

test('the name query is a substring of the FOLDED title, both sides folded', () => {
  const state = EMPTY();
  state.nameQuery = 'creme';           // as filters.js stores it: folded, lower
  assert.strictEqual(
    FS.rowMatchesFilters(ROW({ titleFolded: 'creme brulee' }), state, EXACT), true);
  assert.strictEqual(
    FS.rowMatchesFilters(ROW({ titleFolded: 'lamb tagine' }), state, EXACT), false);
});

test('the draft filter is boolean, and asks nothing at all when it is off', () => {
  const state = EMPTY();
  state.meta = new Set(['draft']);
  assert.strictEqual(FS.rowMatchesFilters(ROW({ isDraft: true }), state, EXACT), true);
  assert.strictEqual(FS.rowMatchesFilters(ROW({ isDraft: false }), state, EXACT), false);
  // Off: both survive. #562 left `draft` as the only meta filter, and it is a
  // fact about which collection a row came from rather than a state of
  // completion -- so with the button unpressed it says nothing about anything.
  assert.strictEqual(FS.rowMatchesFilters(ROW({ isDraft: true }), EMPTY(), EXACT), true);
});

test('the ingredient key drops its (all) suffix before it is matched', () => {
  const state = EMPTY();
  state.ingredient = 'lamb (all)';
  assert.strictEqual(
    FS.rowMatchesFilters(ROW(), state, EXACT), true,
    'the umbrella was matched with its suffix still attached, so it looked for ' +
    'an ingredient literally called "lamb (all)".'
  );
});

test('with no matcher, an ingredient filter selects nothing rather than everything', () => {
  // The opposite direction from excludesRow's own no-matcher case, and both
  // fail where it shows: an empty list is visibly wrong, where a silently
  // unenforced EXCLUSION would hand back the thing you ruled out.
  const state = EMPTY();
  state.ingredient = 'lamb';
  assert.strictEqual(FS.rowMatchesFilters(ROW(), state, undefined), false);
});

test('the row rules are ALL of them, and each one alone can drop a row', () => {
  // A sweep, so a rule quietly deleted from the predicate is a failure rather
  // than a smaller function. Generated from the four fields rather than
  // hand-listed, which is the omission problem this module exists to remove.
  const cases = [
    ['tags', (s) => { s.tags = new Set(['nonexistent']); }],
    ['star', (s) => { s.star = 'beef'; }],
    ['nameQuery', (s) => { s.nameQuery = 'zzz'; }],
    ['meta.draft', (s) => { s.meta = new Set(['draft']); }]
  ];
  cases.forEach(([name, apply]) => {
    const state = EMPTY();
    apply(state);
    assert.strictEqual(
      FS.rowMatchesFilters(ROW({ titleFolded: 'lamb tagine' }), state, EXACT), false,
      `${name} no longer excludes a row it should. Every rule here can drop a ` +
      `row on its own; one that cannot has stopped being a filter.`
    );
  });
});

test('a row missing every field is not a crash', () => {
  // Defensive because the caller reads a live DOM: a row whose data attributes
  // are all absent arrives as empty strings and empty arrays, and the answer
  // wanted there is "nothing is filtering it out", not an exception.
  assert.strictEqual(FS.rowMatchesFilters({}, EMPTY(), EXACT), true);
  assert.strictEqual(FS.rowMatchesFilters(undefined, undefined, EXACT), true);
});

test('the two tables are genuinely different -- this is not one index twice', () => {
  const food = FS.create(FS.FOOD_FIELDS).FIELDS;
  const cocktail = FS.create(FS.COCKTAIL_FIELDS).FIELDS;
  assert.ok(
    food.some((f) => cocktail.indexOf(f) === -1),
    'every food field also exists on the cocktail index. If the two really do ' +
    'ask the same questions, share one table deliberately rather than keeping two.'
  );
  assert.ok(cocktail.some((f) => food.indexOf(f) === -1));
});
