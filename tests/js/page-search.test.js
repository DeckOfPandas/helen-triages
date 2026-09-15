// =============================================================================
// Tests for assets/js/page-search.js -- the search-for-anything box's ranking
// and grouping (GitHub issue #1050), no DOM required.
//
//   node --test
//
// WHAT IS WORTH TESTING HERE is the part Helen ruled on: names first, then the
// kinds of word in the index's own order; a prefix match on a name outranks a
// substring and a substring is offered only when nothing prefixes; a word no
// page carries is never offered; and each result's link is one the index will
// actually read (assets/js/filter-state.js's grammar). The DOM half -- the
// dropdown, the keys -- is the rest of that file and is exercised by looking.
// =============================================================================
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const PS = require('../../assets/js/page-search.js');
const IS = require('../../assets/js/ingredient-search.js');
const FS = require('../../assets/js/filter-state.js');

/* A small food-shaped index: the shape food/search.json emits, with enough
   in it to exercise every rule. */
const FOOD = {
  home: '/helen-triages/food/',
  items_label: 'recipes',
  groups: [
    { kind: 'star', label: 'STAR INGREDIENT', param: 'star', field: 'star',
      values: ['beef', 'chocolate', 'duck', 'lamb', 'shellfish'] },
    { kind: 'mood', label: 'MOOD', param: 'tag', field: 'tags',
      values: ['bakes', 'dessert', 'soup', 'sweets'] },
    { kind: 'practicalities', label: 'PRACTICALITIES', param: 'tag', field: 'tags',
      values: ['festive', 'freezable', 'make-ahead'] },
    { kind: 'ingredient', label: 'HAS TO HAVE', param: 'ing', field: 'ing' }
  ],
  items: [
    { t: 'Chocolate mousse', u: '/helen-triages/food/recipes/chocolate-mousse/',
      star: 'chocolate', tags: ['dessert', 'make-ahead'], ing: ['dark chocolate', 'eggs'] },
    { t: 'Chicken sorrel potato stew', u: '/helen-triages/food/recipes/chicken-sorrel-potato-stew/',
      star: 'poultry', tags: ['soup'], ing: ['chicken thighs', 'sorrel', 'potatoes'] },
    { t: 'Duck à l’orange sanguine', u: '/helen-triages/food/recipes/duck-a-lorange-sanguine/',
      star: 'duck', tags: ['showstopper'], ing: ['duck', 'blood oranges'] },
    { t: 'Lemony cavolo nero butter bean soup', u: '/helen-triages/food/recipes/lemony-cavolo-nero-butter-bean-soup/',
      star: 'greens', tags: ['soup', 'freezable'], ing: ['cavolo nero', 'butter beans', 'lemon'] },
    { t: 'Sticky oxtail stew', u: '/helen-triages/food/recipes/sticky-oxtail-stew/',
      star: 'beef', tags: [], ing: ['oxtail'] }
  ]
};

const groupKinds = (found) => found.groups.map((g) => g.kind);
const labelsOf = (found, kind) => found.groups.find((g) => g.kind === kind).results.map((r) => r.label);

// --- the two folds agree ---------------------------------------------------------

test('page-search folds text exactly as ingredient-search does', () => {
  // page-search.js carries its own copy of fold() so a recipe page need not
  // load the picker's module. A copy is only safe while this holds.
  ['Comté', 'five-spice', 'crème fraîche', 'Jägerita', 'plain']
    .forEach((s) => assert.strictEqual(PS.fold(s), IS.fold(s), s));
});

test('folding by character keeps every index where it was', () => {
  const s = 'Duck à l’orange';
  const f = PS.foldByCharacter(s);
  assert.strictEqual(f.length, s.length);
  assert.strictEqual(f, 'duck a l’orange');
});

// --- when it says nothing ----------------------------------------------------------

test('under two characters the search says nothing', () => {
  const s = PS.create(FOOD);
  assert.strictEqual(s.search(''), null);
  assert.strictEqual(s.search('c'), null);
  assert.strictEqual(s.search('  c '), null);
});

test('a query matching nothing is an empty answer, not silence', () => {
  const found = PS.create(FOOD).search('zzq');
  assert.ok(found, 'null means "close the dropdown"; a miss is a fact to show.');
  assert.deepStrictEqual(found.groups, []);
});

// --- names first, prefix before substring -----------------------------------------

test('names come first, in title tiers', () => {
  const found = PS.create(FOOD).search('ch');
  assert.strictEqual(found.groups[0].kind, 'name');
  assert.strictEqual(found.groups[0].label, 'recipes');
  // "Chocolate mousse" and "Chicken ..." both START with ch (tier 1, in the
  // index's alphabetical order); nothing else has a word starting ch.
  assert.deepStrictEqual(labelsOf(found, 'name'),
    ['Chocolate mousse', 'Chicken sorrel potato stew']);
});

test('a word-start match outranks a title-start match only by tier, not by kind', () => {
  const found = PS.create(FOOD).search('so');
  // "Sticky ..." no; "sorrel" is a word in Chicken sorrel..., "soup" a word in
  // Lemony ... soup -- both tier 2, alphabetical.
  assert.deepStrictEqual(labelsOf(found, 'name'),
    ['Chicken sorrel potato stew', 'Lemony cavolo nero butter bean soup']);
});

test('a substring hit on a name is offered only when nothing prefixes', () => {
  // "tail" is inside oxTAIL and starts no word anywhere.
  const only = PS.create(FOOD).search('tail');
  assert.deepStrictEqual(labelsOf(only, 'name'), ['Sticky oxtail stew']);

  // "ick" is inside chICKen and stICKy -- but "st" prefixes "stew" and
  // "Sticky", so for "st" the substring hits must NOT join the prefix ones.
  const st = PS.create(FOOD).search('st');
  assert.deepStrictEqual(labelsOf(st, 'name'),
    ['Sticky oxtail stew', 'Chicken sorrel potato stew']);
});

test('the highlight marks the run that begins a word, accents intact', () => {
  const found = PS.create(FOOD).search('or');
  const duck = found.groups.find((g) => g.kind === 'name').results
    .find((r) => r.label.indexOf('Duck') === 0);
  // "l’orange": the o of orange, not the o in "Duck à l’Orange"'s ... there
  // is only one, and it is at index 9 in the ORIGINAL string.
  assert.deepStrictEqual(duck.hit, [9, 11]);
  assert.strictEqual(duck.label.slice(duck.hit[0], duck.hit[1]), 'or');
  assert.strictEqual(duck.href, '/helen-triages/food/recipes/duck-a-lorange-sanguine/');
});

// --- then the kinds of word, in the index's order ---------------------------------

test('word groups follow the names in the index\'s own order', () => {
  const found = PS.create(FOOD).search('d');
  assert.strictEqual(found, null, 'one letter is under the minimum');
  const du = PS.create(FOOD).search('du');
  assert.deepStrictEqual(groupKinds(du), ['name', 'star', 'ingredient']);
  assert.deepStrictEqual(labelsOf(du, 'star'), ['duck']);
  assert.deepStrictEqual(labelsOf(du, 'ingredient'), ['duck']);
});

test('a declared word no page carries is never offered', () => {
  // `lamb` and `shellfish` are declared stars with no recipe in this fixture;
  // `bakes` and `sweets` are declared moods nobody carries.
  const s = PS.create(FOOD);
  const la = s.search('lamb');
  assert.deepStrictEqual(la.groups, []);
  const sw = s.search('swe');
  assert.deepStrictEqual(sw.groups, []);
  // ...and a tag a page carries that is NOT declared (`showstopper`) is not a
  // mood either: the declared list is the vocabulary, the items only count.
  assert.deepStrictEqual(s.search('show').groups, []);
});

test('a group with no declared list is built from the pages, alphabetically', () => {
  const found = PS.create(FOOD).search('b');
  assert.strictEqual(found, null);
  const bu = PS.create(FOOD).search('bu');
  assert.deepStrictEqual(labelsOf(bu, 'ingredient'), ['butter beans']);
  const b = PS.create(FOOD).search('bl');
  assert.deepStrictEqual(labelsOf(b, 'ingredient'), ['blood oranges']);
});

test('a word is offered once however many pages carry it, with its count', () => {
  const found = PS.create(FOOD).search('sou');
  const soup = found.groups.find((g) => g.kind === 'mood').results[0];
  assert.strictEqual(soup.label, 'soup');
  assert.strictEqual(soup.count, 2);
});

// --- every link is one the index reads -------------------------------------------

test('a word\'s link carries the parameter the index grammar reads', () => {
  const found = PS.create(FOOD).search('make');
  const tag = found.groups.find((g) => g.kind === 'practicalities').results[0];
  assert.strictEqual(tag.href, '/helen-triages/food/?tag=make-ahead#results');
  // What a browser hands the index as location.search: the query, no hash.
  const query = tag.href.slice(tag.href.indexOf('?'), tag.href.indexOf('#'));
  assert.deepStrictEqual(FS.parseQuery(query).tag, ['make-ahead']);

  const ing = PS.create(FOOD).search('cavolo').groups.find((g) => g.kind === 'ingredient').results[0];
  assert.strictEqual(ing.href, '/helen-triages/food/?ing=cavolo%20nero#results');
  assert.deepStrictEqual(FS.parseQuery('?ing=cavolo%20nero').ing, ['cavolo nero']);
});

test('a filtered link lands on the results, a page link on the page', () => {
  // Helen, 2026-09-15: "with the screen snapped to the returned recipes".
  // Every word's link ends in the fragment both indexes put on their count
  // line; a recipe's own link is the page and carries none.
  const s = PS.create(FOOD);
  const found = s.search('ch');
  found.groups.forEach((g) => g.results.forEach((r) => {
    if (g.kind === 'name') assert.ok(!/#/.test(r.href), r.href);
    else assert.ok(r.href.endsWith(s.RESULTS_FRAGMENT), r.href);
  }));
});

test('every group\'s parameter is a KIND filter-state.js knows', () => {
  const s = PS.create(FOOD);
  s.groups.forEach((g) => {
    assert.ok(FS.KINDS.indexOf(g.param) !== -1,
      `${g.kind} links with ?${g.param}=, which the index would ignore.`);
  });
});

// --- the caps are stated ----------------------------------------------------------

test('a long list is capped and the cap is stated', () => {
  const many = {
    home: '/x/', items_label: 'recipes', groups: [],
    items: Array.from({ length: 10 }, (_, i) => ({ t: 'Tart number ' + i, u: '/x/' + i + '/' }))
  };
  const found = PS.create(many).search('tart');
  assert.strictEqual(found.groups[0].results.length, PS.ITEM_CAP);
  assert.strictEqual(found.groups[0].hidden, 10 - PS.ITEM_CAP);
});

// --- a drinks-shaped index works the same way ---------------------------------------

test('the drinks index: one mood list, two groups, card ingredients', () => {
  const DRINKS = {
    home: '/helen-triages/cocktails/',
    items_label: 'drinks',
    groups: [
      { kind: 'mood', label: 'Mood', param: 'mood', field: 'moods', values: ['sharp', 'nightcap'] },
      { kind: 'hassle', label: 'Hassle', param: 'mood', field: 'moods', values: ['no juicing', 'on fire'] },
      { kind: 'ingredient', label: 'Has to have', param: 'ing', field: 'ing' }
    ],
    items: [
      { t: 'Negroni', u: '/helen-triages/cocktails/recipes/negroni/',
        moods: ['no juicing', 'aperitivo'], ing: ['gin', 'sweet vermouth', 'Campari'] },
      { t: 'Sazerac', u: '/helen-triages/cocktails/recipes/sazerac/',
        moods: ['strong brown drink', 'nightcap', 'no juicing'], ing: ['rye', 'cognac', 'absinthe'] }
    ]
  };
  const s = PS.create(DRINKS);
  const no = s.search('no');
  assert.deepStrictEqual(groupKinds(no), ['hassle']);
  assert.strictEqual(no.groups[0].results[0].href, '/helen-triages/cocktails/?mood=no%20juicing#results');
  const ni = s.search('nigh');
  assert.deepStrictEqual(groupKinds(ni), ['mood']);
  const ca = s.search('camp');
  assert.deepStrictEqual(labelsOf(ca, 'ingredient'), ['Campari']);
  assert.strictEqual(ca.groups[0].results[0].href, '/helen-triages/cocktails/?ing=Campari#results');
  // A substring on a drink name: "roni" is inside Negroni and starts no word.
  assert.deepStrictEqual(labelsOf(s.search('roni'), 'name'), ['Negroni']);
});
