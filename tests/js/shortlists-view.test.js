// HTF.listsView (assets/js/shortlists-view.js): what the shortlists page shows
// for the lists it is given, with no DOM. MANUAL §8.9.
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const view = require('../../assets/js/shortlists-view.js');
const rowsModule = require('../../assets/js/food-shopping-rows.js');

const A = '/food/recipes/a/';
const B = '/food/recipes/b/';
const COOKIES = '/food/recipes/cookies/';

const LISTS = [
  { id: 'l1', name: 'Christmas starters', items: [{ recipe: A, portions: 4 }, { recipe: B, portions: 6 }] },
  { id: 'l2', name: 'Lemons', items: [{ recipe: A, portions: 8 }] },
  { id: 'l3', name: 'Empty', items: [] }
];

test('the overview counts every recipe on every list, and the cost when there is one', () => {
  assert.strictEqual(view.overviewText(LISTS, 'from £777.29'), '3 recipes on 3 lists · from £777.29');
  assert.strictEqual(view.overviewText([LISTS[1]], ''), '1 recipe on 1 list');
  assert.strictEqual(view.listText(LISTS[0], '£86.53'), '2 recipes · £86.53');
  assert.strictEqual(view.listText(LISTS[2], ''), '0 recipes');
});

test('a list\'s neighbours are in the reader\'s order, and the ends do not wrap round', () => {
  const names = (n) => [n.previous && n.previous.name, n.next && n.next.name];
  assert.deepStrictEqual(names(view.neighbours(LISTS, 'l1')), [null, 'Lemons']);
  assert.deepStrictEqual(names(view.neighbours(LISTS, 'l2')), ['Christmas starters', 'Empty']);
  assert.deepStrictEqual(names(view.neighbours(LISTS, 'l3')), ['Lemons', null]);
  assert.deepStrictEqual(names(view.neighbours(LISTS, 'l99')), [null, null]);
});

test('a list\'s rows are its recipes in order; everything is every list\'s, a recipe twice if on two', () => {
  assert.deepStrictEqual(view.rows(LISTS, 'l1').map((r) => [r.list, r.recipe, r.portions]),
    [['l1', A, 4], ['l1', B, 6]]);
  assert.deepStrictEqual(view.rows(LISTS, 'everything').map((r) => [r.list, r.recipe, r.portions]),
    [['l1', A, 4], ['l1', B, 6], ['l2', A, 8]],
    'every row belongs to one list, so a scaler writes to that list');
  assert.deepStrictEqual(view.rows(LISTS, 'l99'), [], 'a list that is gone has no rows');
});

test('counts say recipes, in the singular for one', () => {
  assert.strictEqual(view.countText(0), '0 recipes');
  assert.strictEqual(view.countText(1), '1 recipe');
  assert.strictEqual(view.countText(4), '4 recipes');
});

test('a list\'s colour goes round seven hues in the order lists were made', () => {
  assert.deepStrictEqual(['l1', 'l2', 'l7', 'l8', 'l15'].map(view.hueOf), [0, 1, 6, 0, 0]);
  assert.strictEqual(view.hueOf('everything'), -1, 'everything has no hue of its own');
  assert.strictEqual(view.hueOf('shared'), -1);
});

test('a list\'s colour is its own: moving or deleting another list leaves it alone', () => {
  const before = LISTS.map((l) => view.hueOf(l.id));
  const moved = [LISTS[2], LISTS[0]];
  assert.deepStrictEqual(moved.map((l) => view.hueOf(l.id)), [before[2], before[0]]);
});

// --- the merged shopping list -------------------------------------------------

const RECIPES = {
  [A]: { p: 4, y: '4', k: 'serves', i: [{ a: '200 g', n: 'plain flour', s: 'cupboard' }] },
  [B]: { p: 6, y: '6', k: 'serves', i: [{ a: '300 g', n: 'plain flour', s: 'cupboard' }] },
  [COOKIES]: {
    p: null, y: '18 cookies', k: 'makes', w: true, h: false,
    m: { kind: 'count', base: 18, stem: 'cookies', rest: '', box: '18' },
    i: [{ a: '1', n: 'egg', s: 'dairy' }]
  }
};
const shop = rowsModule.create({
  recipes: RECIPES, escape: String,
  buildOptions: { aisles: [{ key: 'cupboard', label: 'cupboard' }, { key: 'dairy', label: 'dairy' }] }
});

function totals(rows) {
  const aisles = shop.build(view.shoppingEntries(rows, shop));
  const out = {};
  aisles.forEach((aisle) => aisle.items.forEach((row) => { out[row.label] = row.text; }));
  return out;
}

test('a list\'s shopping is its own recipes at its own portions', () => {
  assert.deepStrictEqual(totals(view.rows(LISTS, 'l1')), { 'plain flour': '500 g' },
    'A for 4 (200 g) and B for 6 (300 g)');
  assert.deepStrictEqual(totals(view.rows(LISTS, 'l2')), { 'plain flour': '400 g' },
    'A for 8 is twice its 200 g');
});

test('everything\'s shopping adds every list, a recipe on two lists counted twice', () => {
  assert.deepStrictEqual(totals(view.rows(LISTS, 'everything')), { 'plain flour': '900 g' },
    '200 g + 300 g + 400 g: A is cooked once for each list');
});

test('a `makes:` recipe\'s portions are batches', () => {
  const lists = [{ id: 'l1', name: 'Bake', items: [{ recipe: COOKIES, portions: 3 }] }];
  assert.deepStrictEqual(totals(view.rows(lists, 'l1')), { egg: '3' });
});

test('a recipe the page has no data for adds nothing and breaks nothing', () => {
  const lists = [{ id: 'l1', name: 'L', items: [{ recipe: '/food/recipes/gone/', portions: 2 }, { recipe: A, portions: 4 }] }];
  assert.deepStrictEqual(totals(view.rows(lists, 'l1')), { 'plain flour': '200 g' });
});

// --- the index's words ----------------------------------------------------------

test('the recipe button says how many lists, or offers to shortlist', () => {
  assert.deepStrictEqual(plainButton(view.buttonWords(0)), { word: 'shortlist', on: false });
  assert.deepStrictEqual(plainButton(view.buttonWords(1)), { word: '1 list', on: true });
  assert.deepStrictEqual(plainButton(view.buttonWords(3)), { word: '3 lists', on: true });
});

test('in adding-to mode the button names the list and says whether the recipe is on it', () => {
  assert.deepStrictEqual(plainButton(view.buttonWords(2, { name: 'Lemons', on: false })), { word: 'Lemons', on: false });
  assert.deepStrictEqual(plainButton(view.buttonWords(2, { name: 'Lemons', on: true })), { word: 'Lemons', on: true });
});

test('the link to the page counts lists, so the number matches the noun', () => {
  assert.strictEqual(view.linkText(0), 'shortlists');
  assert.strictEqual(view.linkText(1), 'your 1 shortlist');
  assert.strictEqual(view.linkText(6), 'your 6 shortlists');
});

function plainButton(b) { return { word: b.word, on: b.on }; }

test('a refused name says why, naming the list it clashes with as that list spells it', () => {
  assert.strictEqual(view.nameProblemText('empty', '', LISTS), 'Give the list a name.');
  assert.strictEqual(view.nameProblemText('clash', 'LEMONS', LISTS), 'You already have a list called “Lemons”.');
});

// --- the recipe page's scaler and a list's portions ------------------------------

test('a serves: recipe\'s scaler and its list hold the same number of portions', () => {
  assert.strictEqual(view.scalerFromPortions(6, { made: false, base: 4 }), 6);
  assert.strictEqual(view.portionsFromScaler(6, { made: false, base: 4 }), 6);
});

test('a makes: recipe\'s list counts batches; its scaler counts the things made', () => {
  const cookies = { made: true, base: 18 };
  assert.strictEqual(view.scalerFromPortions(2, cookies), 36, 'two batches of 18 is 36 cookies');
  assert.strictEqual(view.portionsFromScaler(36, cookies), 2);
  assert.strictEqual(view.portionsFromScaler(9, cookies), 0.5, 'half a batch is half the things');
});

test('a note under the scaler says which lists the recipe is on', () => {
  assert.strictEqual(view.inListsText(0), '');
  assert.strictEqual(view.inListsText(1), 'in 1 list');
  assert.strictEqual(view.inListsText(3), 'in 3 lists');
});

// --- moving -------------------------------------------------------------------

test('a move is announced by place', () => {
  assert.strictEqual(view.movedText('Christmas starters', 0, 4), 'Christmas starters moved to 1 of 4.');
  assert.strictEqual(view.movedText('Trifle', 3, 4), 'Trifle moved to 4 of 4.');
});

test('a list\'s recipes come in the list\'s order on its page and on the overview', () => {
  const moved = [{ id: 'l1', name: 'Christmas starters', items: [{ recipe: B, portions: 6 }, { recipe: A, portions: 4 }] }];
  assert.deepStrictEqual(view.rows(moved, 'l1').map((r) => r.recipe), [B, A]);
  assert.deepStrictEqual(view.rows(moved, 'everything').map((r) => r.recipe), [B, A]);
});

// --- sharing ------------------------------------------------------------------

test('a link\'s missing recipes are counted in words, and none says nothing', () => {
  assert.strictEqual(view.missingText(0), '');
  assert.strictEqual(view.missingText(1), '1 recipe in the link is not on this site, so it is left out.');
  assert.strictEqual(view.missingText(3), '3 recipes in the link are not on this site, so they are left out.');
});

test('a name in use offers keep both (under its free name), merge, or leave out', () => {
  const words = view.clashChoices('Lemons', 'Lemons (2)');
  assert.strictEqual(words.question, 'You already have a list called “Lemons”.');
  assert.strictEqual(words.both, 'keep both, this one as “Lemons (2)”');
  assert.match(words.merge, /your portions stay/);
  assert.strictEqual(words.skip, 'leave it out');
});

test('what was brought in is announced, and kept when it came from a link', () => {
  assert.strictEqual(view.broughtText(0), 'Nothing brought in.');
  assert.strictEqual(view.broughtText(1, true), 'Kept one list.');
  assert.strictEqual(view.broughtText(3, false), 'Brought in 3 lists.');
});

// --- links --------------------------------------------------------------------

test('the browse link carries the list it fills, and a recipe link the list it is opened from', () => {
  assert.strictEqual(view.intoUrl('/helen-triages/food/', 'l3'), '/helen-triages/food/?into=l3');
  assert.strictEqual(view.pageUrl('/helen-triages/food/shortlists/', 'l3'), '/helen-triages/food/shortlists/?list=l3');
  assert.strictEqual(view.listUrl('/helen-triages/food/recipes/a/', 'l1'),
    '/helen-triages/food/recipes/a/?list=l1');
});
