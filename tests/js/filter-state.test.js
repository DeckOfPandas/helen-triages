// Tests for assets/js/filter-state.js: the index's filter query-string grammar
// (#40) and its filter state shape (#52). No DOM required.
//
// Run from the repo root: .node-runtime/node/bin/node --test
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const FS = require('../../assets/js/filter-state.js');

test('the documented example parses to the documented shape', () => {
  assert.deepStrictEqual(
    FS.parseQuery('?star=lamb&tag=soup,make-ahead'),
    { star: ['lamb'], tag: ['soup', 'make-ahead'], mood: [], ing: [] }
  );
});

test('a leading ? is optional', () => {
  assert.deepStrictEqual(FS.parseQuery('star=lamb'), { star: ['lamb'], tag: [], mood: [], ing: [] });
});

// --- the + trap ---------------------------------------------------------------
// Jekyll's url_encode spells a space as `+`, and decodeURIComponent does not
// undo that. Real taxonomy values contain a space.

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
// A bad query string is not worth an error on a page that works without it.

test('an empty string parses to empty, with every known kind still present', () => {
  assert.deepStrictEqual(FS.parseQuery(''), { star: [], tag: [], mood: [], ing: [] });
});

test('undefined and a bare ? parse to empty rather than throwing', () => {
  assert.deepStrictEqual(FS.parseQuery(undefined), { star: [], tag: [], mood: [], ing: [] });
  assert.deepStrictEqual(FS.parseQuery('?'), { star: [], tag: [], mood: [], ing: [] });
});

test('unknown parameters are ignored, and do not become keys', () => {
  const parsed = FS.parseQuery('?protein=beef&tag=soup&utm_source=newsletter');
  assert.deepStrictEqual(parsed, { star: [], tag: ['soup'], mood: [], ing: [] });
});

test('a parameter with no value at all says nothing', () => {
  assert.deepStrictEqual(FS.parseQuery('?tag&star=lamb'), { star: ['lamb'], tag: [], mood: [], ing: [] });
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

// --- the name query, #1024 -----------------------------------------------------
// `?q=` is not a kind: it is one string, whole, and a title may carry a comma,
// so it stays out of parseQuery's return shape and has a reader of its own.

test('parseName reads ?q= whole, with the same decoding as the kinds', () => {
  assert.strictEqual(FS.parseName('?q=negroni'), 'negroni');
  assert.strictEqual(FS.parseName('?q=pear%2C+apricot+and+rosemary'),
    'pear, apricot and rosemary');
  assert.strictEqual(FS.parseName('?tag=soup&q=lemon+curd'), 'lemon curd');
});

test('parseName is empty when there is no q, an empty q, or no search at all', () => {
  assert.strictEqual(FS.parseName(''), '');
  assert.strictEqual(FS.parseName(undefined), '');
  assert.strictEqual(FS.parseName('?q='), '');
  assert.strictEqual(FS.parseName('?q=+'), '');
  assert.strictEqual(FS.parseName('?tag=soup'), '');
});

test('parseShip reads one whole ?ship= value, the last one winning (#1412)', () => {
  assert.strictEqual(FS.parseShip('?ship=IOU'), 'IOU');
  assert.strictEqual(FS.parseShip('?ship=oh+gods+yes#results'.split('#')[0]), 'oh gods yes');
  assert.strictEqual(FS.parseShip('?ship=meh&ship=who%20knows'), 'who knows');
  assert.strictEqual(FS.parseShip('?mood=sharp'), '');
  assert.strictEqual(FS.parseShip('?ship='), '');
  assert.deepStrictEqual(FS.parseQuery('?ship=IOU'), { star: [], tag: [], mood: [], ing: [] });
});

test('parseName does not leak into parseQuery', () => {
  assert.deepStrictEqual(FS.parseQuery('?q=negroni'), { star: [], tag: [], mood: [], ing: [] });
});

// --- ?shortlist=, #1093 ---------------------------------------------------------
// Two meanings in one parameter: `1` is this browser's own list, anything else
// is a list of slugs someone sent. A slug may begin with `1`, so the value is
// parsed, never substring-matched.

test('parseShortlist: ?shortlist=1 is the own list, with no slugs', () => {
  assert.deepStrictEqual(FS.parseShortlist('?shortlist=1'), { own: true, slugs: [] });
  assert.deepStrictEqual(FS.parseShortlist('?mood=sharp&shortlist=1'), { own: true, slugs: [] });
});

test('parseShortlist: a list of slugs is a sent list, in link order, once each', () => {
  assert.deepStrictEqual(FS.parseShortlist('?shortlist=negroni,aviation,negroni'),
    { own: false, slugs: ['negroni', 'aviation'] });
});

test('parseShortlist: a slug beginning with 1 is a slug, not the own-list flag', () => {
  assert.deepStrictEqual(FS.parseShortlist('?shortlist=10-minute-dal'),
    { own: false, slugs: ['10-minute-dal'] });
});

test('parseShortlist: anything that is not [a-z0-9-] is dropped, not matched', () => {
  // A link is untrusted input and a slug is only ever compared with a
  // Jekyll-written URL segment, which carries no other character.
  assert.deepStrictEqual(
    FS.parseShortlist('?shortlist=Dal,%3Cscript%3E,../x,,-lead,moules%20mariniere'),
    { own: false, slugs: ['dal'] });
});

test('parseShortlist: nothing, an empty value, or no parameter is neither', () => {
  const none = { own: false, slugs: [] };
  assert.deepStrictEqual(FS.parseShortlist(''), none);
  assert.deepStrictEqual(FS.parseShortlist(undefined), none);
  assert.deepStrictEqual(FS.parseShortlist('?shortlist='), none);
  assert.deepStrictEqual(FS.parseShortlist('?shortlist'), none);
  assert.deepStrictEqual(FS.parseShortlist('?tag=soup'), none);
});

test('parseShortlist: the last shortlist parameter wins', () => {
  assert.deepStrictEqual(FS.parseShortlist('?shortlist=dal&shortlist=1'), { own: true, slugs: [] });
  assert.deepStrictEqual(FS.parseShortlist('?shortlist=1&shortlist=dal'), { own: false, slugs: ['dal'] });
});

test('shortlistQuery writes what parseShortlist reads back', () => {
  const q = FS.shortlistQuery(['negroni', 'Aviation', 'negroni']);
  assert.strictEqual(q, 'shortlist=negroni,aviation');
  assert.deepStrictEqual(FS.parseShortlist('?' + q), { own: false, slugs: ['negroni', 'aviation'] });
});

test('shortlistQuery leaves out what the parser would drop, and is empty for nothing', () => {
  assert.strictEqual(FS.shortlistQuery(['1', 'a b', '']), '');
  assert.strictEqual(FS.shortlistQuery([]), '');
  assert.strictEqual(FS.shortlistQuery(undefined), '');
});

test('parseShortlist does not leak into parseQuery', () => {
  assert.deepStrictEqual(FS.parseQuery('?shortlist=dal'), { star: [], tag: [], mood: [], ing: [] });
});

test('KINDS is exported so filters.js and the tests agree on what exists', () => {
  assert.deepStrictEqual(FS.KINDS, ['star', 'tag', 'mood', 'ing']);
});

test('toQuery is deliberately absent until something writes the URL back', () => {
  assert.strictEqual(FS.toQuery, undefined);
});

// --- the state shape, #52 ------------------------------------------------------
// Clear-all empties every field, so the clear button's visibility predicate
// must read every field too; one it misses hides the button while it still has
// work to do. The cases are generated from FS.FIELDS, never listed by hand: a
// hand-written list goes one short, and still passes, when a field is added.

// A non-empty value derived from the field's own empty value, so nothing is
// written down per field. An unhandled kind throws rather than being skipped:
// a skipped field is the bug.
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

// --- one generated case per field ---------------------------------------------

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

// --- hasNarrowingFilter is a different question from hasAnythingToClear ------
// Collapsing the two silently changes behaviour at whichever call site loses
// its own answer (#248).

test('hasNarrowingFilter INCLUDES includedIngredients -- issue #1092 made it a real filter', () => {
  // A chosen entry survives the next keystroke and takes an explicit remove,
  // so it is a real filter.
  const state = stateWithOnly('includedIngredients');
  assert.strictEqual(FS.hasNarrowingFilter(state), true);
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

test('hasNarrowingFilter INCLUDES tags and star', () => {
  ['tags', 'star'].forEach((field) => {
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

// Clear-all in filters.js and cocktail-index.js is `state = emptyState()`, so
// what it yields is checked against each spec's own `empty()`, field by field.
test('clearing returns something equal to a fresh empty state', () => {
  [FS.FOOD_FIELDS, FS.COCKTAIL_FIELDS].forEach((spec) => {
    const bound = FS.create(spec);
    let state = bound.emptyState();
    bound.FIELDS.forEach((f) => { state[f] = aNonEmptyValueLike(state[f], f); });
    assert.strictEqual(bound.hasAnythingToClear(state), true);
    state = bound.emptyState();
    const expected = {};
    Object.keys(spec).forEach((f) => { expected[f] = spec[f].empty(); });
    assert.deepStrictEqual(state, expected);
    bound.FIELDS.forEach((f) => {
      assert.strictEqual(FS.isFieldSet(state[f]), false, `${f} survives a clear`);
    });
    assert.strictEqual(bound.isEmpty(state), true);
  });
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

// --- the exclusion rule, #52 ---------------------------------------------------
// Membership, not containment: `pea` sits inside `peanut butter` and inside
// `pearl barley`, and a "contains" rule removes both for someone who only
// excluded peas. Exclusion reads the full derived ingredient list
// (data-all-ingredients): main_ingredients is a partial hint, fine to include
// on and unsafe to exclude by.

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
  // No vocabulary means no umbrella; it must never degrade into a substring
  // rule.
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

// --- serialise / deserialise, #387 ---------------------------------------------
// The index keeps its list in sessionStorage so that going back restores it.

test('serialise turns Sets into arrays, because JSON silently will not', () => {
  // JSON.stringify(new Set(['a'])) is "{}": no error, so a state put through
  // raw JSON comes back with its Set fields quietly emptied.
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
  state.nameQuery = 'stew';
  state.includedIngredients.add('cavolo nero');
  state.isSearching = true;

  const back = FS.deserialise(JSON.parse(JSON.stringify(FS.serialise(state))));

  assert.deepStrictEqual([...back.tags], ['soup']);
  assert.strictEqual(back.star, 'beef');
  assert.deepStrictEqual([...back.excludedIngredients], ['peas']);
  assert.strictEqual(back.nameQuery, 'stew');
  assert.deepStrictEqual([...back.includedIngredients], ['cavolo nero']);
  assert.strictEqual(back.isSearching, true);
});

test('every field in FIELD_SPEC round-trips, including any added later', () => {
  // Generated from FIELDS, so an added field is covered without an edit here.
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
  // Stored state is untrusted: a version behind, or hand-edited. An unfiltered
  // page beats a wrong-looking index with no way to tell why.
  [null, undefined, 'nonsense', 42, [], {}, { tags: 'soup', star: 7 }].forEach((bad) => {
    const back = FS.deserialise(bad);
    assert.strictEqual(FS.hasAnythingToClear(back), false, `${JSON.stringify(bad)} restored as set`);
  });
});

test('a Set field given a non-array is ignored, not coerced', () => {
  const back = FS.deserialise({ tags: 'soup' });
  assert.strictEqual(back.tags.size, 0);
});

// --- one mechanism, two tables, #579 -------------------------------------------
// The generated cases run against every declared field table. SPECS is derived
// from the module's own exports, so a table added to filter-state.js is
// covered by the line that declares it.

// Detected by shape, not by name: `/_FIELDS$/` also matches NARROWING_FIELDS,
// which is a list of names. A spec is a mapping whose every value declares an
// empty() factory.
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
// Named rather than generated: a field leaving this table takes a whole filter
// off the clear-all button, silently.

test("the cocktail table covers all five of the index's named questions", () => {
  const S = FS.create(FS.COCKTAIL_FIELDS);
  ['moods', 'chaos', 'include', 'exclude', 'nameQuery'].forEach((f) => {
    assert.ok(S.FIELDS.indexOf(f) !== -1, `the cocktail index has no "${f}" field`);
    assert.ok(S.NARROWING_FIELDS.indexOf(f) !== -1, `"${f}" does not narrow the list`);
  });
});

test('a half-typed cocktail search is clearable but does not narrow', () => {
  // Typing into HAS TO HAVE and picking nothing leaves a pool of chips that
  // only clear-all or deleting the text dismisses (#274 on the food side).
  const S = FS.create(FS.COCKTAIL_FIELDS);
  ['isIncludeSearching', 'isExcludeSearching'].forEach((f) => {
    const state = S.emptyState();
    state[f] = true;
    assert.strictEqual(S.hasAnythingToClear(state), true, `${f} is not clearable`);
    assert.strictEqual(S.hasNarrowingFilter(state), false, `${f} should not narrow`);
  });
});

// --- is this row one you asked for? — issue #506 ------------------------------
// The row shape is what filters.js reads off each <li>: tags, star,
// titleFolded, isDraft, ingredients. `titleFolded` is pre-folded by the caller
// because state.nameQuery is stored folded.

const ROW = (over) => Object.assign({
  tags: ['soup', 'make-ahead'],
  star: 'lamb',
  titleFolded: '',
  isDraft: false,
  ingredients: ['lamb', 'barley', 'carrots']
}, over || {});

const EMPTY = () => FS.emptyState();

// The real matcher needs a vocabulary. These cases are about the row rules, so
// the umbrella is stubbed to exact membership.
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

test('a row answers a star it carries in starAlso, and only that one', () => {
  // taxonomy.yml `star_also`: a greens dish of pod beans is also legumes.
  const state = EMPTY();
  const beans = ROW({ star: 'greens', starAlso: ['legumes'] });
  state.star = 'legumes';
  assert.strictEqual(FS.rowMatchesFilters(beans, state, EXACT), true);
  state.star = 'greens';
  assert.strictEqual(FS.rowMatchesFilters(beans, state, EXACT), true);
  state.star = 'lamb';
  assert.strictEqual(FS.rowMatchesFilters(beans, state, EXACT), false);
  state.star = 'legumes';
  assert.strictEqual(FS.rowMatchesFilters(ROW({ star: 'greens' }), state, EXACT), false,
    'a greens row with no starAlso answered the legumes filter');
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

test('a draft row is not filtered on any more, in either direction', () => {
  // `isDraft` is on the row because it renders the `draft` badge; no filter
  // may read it. The food index has no META FILTERS block (DECISIONS).
  assert.strictEqual(FS.rowMatchesFilters(ROW({ isDraft: true }), EMPTY(), EXACT), true);
  assert.strictEqual(FS.rowMatchesFilters(ROW({ isDraft: false }), EMPTY(), EXACT), true);
});

test('the ingredient key drops its (all) suffix before it is matched', () => {
  const state = EMPTY();
  state.includedIngredients.add('lamb (all)');
  assert.strictEqual(
    FS.rowMatchesFilters(ROW(), state, EXACT), true,
    'the umbrella was matched with its suffix still attached, so it looked for ' +
    'an ingredient literally called "lamb (all)".'
  );
});

test('with no matcher, an ingredient filter selects nothing rather than everything', () => {
  // Fails where it shows: an empty list is visibly wrong.
  const state = EMPTY();
  state.includedIngredients.add('lamb');
  assert.strictEqual(FS.rowMatchesFilters(ROW(), state, undefined), false);
});

// --- HAS TO HAVE is AND across its chosen entries -- GitHub issue #1092 -------
// Each pick joins a Set and a row must satisfy every member; LEAVE OUT is the
// opposite direction, OR.

test('two chosen ingredients are AND -- a row must have both, not either', () => {
  const state = EMPTY();
  state.includedIngredients.add('lamb');
  state.includedIngredients.add('barley');
  assert.strictEqual(
    FS.rowMatchesFilters(ROW(), state, EXACT), true,
    'the row carries lamb, barley and carrots -- both chosen ingredients are on it.'
  );

  state.includedIngredients.add('peas');
  assert.strictEqual(
    FS.rowMatchesFilters(ROW(), state, EXACT), false,
    'the row does not carry peas, so requiring lamb AND barley AND peas must ' +
    'drop it -- the regression this issue was filed over replaced the first ' +
    'two choices with the third instead of joining them, which would have ' +
    'kept this row (peas alone matches nothing here, true, but the failure ' +
    'mode was "only the last pick counts", not "peas never matches").'
  );
});

test('an empty set of chosen ingredients filters nothing, same as excludedIngredients', () => {
  assert.strictEqual(FS.rowMatchesFilters(ROW(), EMPTY(), EXACT), true);
});

test('the row rules are ALL of them, and each one alone can drop a row', () => {
  // A sweep, so a rule deleted from the predicate is a failure rather than a
  // smaller function.
  const cases = [
    ['tags', (s) => { s.tags = new Set(['nonexistent']); }],
    ['star', (s) => { s.star = 'beef'; }],
    ['nameQuery', (s) => { s.nameQuery = 'zzz'; }]
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
  // The caller reads a live DOM: a row with no data attributes must come back
  // unfiltered, not as an exception.
  assert.strictEqual(FS.rowMatchesFilters({}, EMPTY(), EXACT), true);
  assert.strictEqual(FS.rowMatchesFilters(undefined, undefined, EXACT), true);
});

// --- did we get here by going back? — #387, shared with cocktails by #595 -----
// The one browser fact both indexes' restores rest on. `performance` is
// injected, so the question can be asked without a browser.

test('a back/forward navigation is recognised', () => {
  const perf = { getEntriesByType: () => [{ type: 'back_forward' }] };
  assert.strictEqual(FS.arrivedByGoingBack(perf), true);
});

test('every other kind of arrival is a fresh visit', () => {
  ['navigate', 'reload', 'prerender', ''].forEach((type) => {
    const perf = { getEntriesByType: () => [{ type }] };
    assert.strictEqual(
      FS.arrivedByGoingBack(perf), false,
      `a "${type}" navigation was treated as going back, which would restore a ` +
      `stale list over a deliberate reload.`
    );
  });
});

test('no Navigation Timing at all is a fresh visit, not a crash', () => {
  // The index runs this at startup; an exception here takes the whole page's
  // filtering with it.
  assert.strictEqual(FS.arrivedByGoingBack({ getEntriesByType: () => [] }), false);
  assert.strictEqual(FS.arrivedByGoingBack({}), false);
  assert.strictEqual(FS.arrivedByGoingBack(null), false);
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

// --- the cocktails half of the grammar ---------------------------------------
// The grammar is one thing for both sites; each index reads only the keys it
// has buttons for.

test('a mood parses like any other kind', () => {
  assert.deepStrictEqual(FS.parseQuery('?mood=sharp'),
    { star: [], tag: [], mood: ['sharp'], ing: [] });
});

test("a two-word mood survives Jekyll's url_encode, which spells a space as +", () => {
  // Both are real moods in _data/cocktails/taxonomy.yml; `url_encode` in
  // _layouts/cocktail.html emits the `+`.
  assert.deepStrictEqual(FS.parseQuery('?mood=sunny+terrace').mood, ['sunny terrace']);
  assert.deepStrictEqual(FS.parseQuery('?mood=no+juicing').mood, ['no juicing']);
});

test('moods and food kinds do not collide in one query', () => {
  assert.deepStrictEqual(FS.parseQuery('?tag=soup&mood=sharp'),
    { star: [], tag: ['soup'], mood: ['sharp'], ing: [] });
});
