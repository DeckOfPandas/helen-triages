// HTF.foodShoppingRows (assets/js/food-shopping-rows.js): the words and markup
// of a food shopping list's rows (#801, #1297, #1457, #1521). These cases were
// the food index's, when its shortlist drew the list; the shortlists page
// draws it now, through this module.
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const rowsModule = require('../../assets/js/food-shopping-rows.js');

const esc = (text) => String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;')
  .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');

const RECIPES = {
  '/food/recipes/a/': {
    p: 4, y: '4', k: 'serves',
    i: [{ a: '200 g', n: 'plain flour', s: 'cupboard' },
      { a: '2', n: 'onions', s: 'produce' },
      { a: '', n: 'olive oil', s: 'cupboard' }]
  },
  '/food/recipes/gelato/': {
    p: 9, y: 'About 750 ml', k: 'makes', w: true, h: true,
    m: { kind: 'measure', base: 750, unit: 'ml', box: '750' },
    i: [{ a: '125 ml', n: 'whipping cream', s: 'dairy' }]
  },
  '/food/recipes/cookies/': {
    p: null, y: '18 cookies', k: 'makes', w: true, h: false,
    m: { kind: 'count', base: 18, stem: 'cookies', rest: '', box: '18' },
    i: [{ a: '100 g', n: 'peanut butter', s: 'cupboard' }, { a: '1', n: 'egg', s: 'dairy' }]
  },
  '/food/recipes/cake/': {
    p: null, y: 'one 8-inch cake', k: 'makes', w: true, h: false,
    m: { kind: 'count', base: 1, stem: '8-inch cake', rest: '', box: '1', times: true },
    i: [{ a: '250 g', n: 'plain flour', s: 'cupboard' }]
  },
  '/food/recipes/sauce/': {
    p: null, y: '1 jar', k: 'makes', w: true, h: false,
    m: { kind: 'count', base: 1, stem: 'jar', rest: '', box: '1' },
    i: [{ a: '200 g', n: 'peanuts', s: 'cupboard' }]
  },
  '/food/recipes/pies/': {
    p: null, y: '1 dozen mince pies', k: 'makes', w: true, h: false,
    m: { kind: 'count', base: 1, stem: 'dozen mince pies', rest: '', box: '1', invariable: true },
    i: [{ a: '300 g', n: 'mincemeat', s: 'cupboard' }]
  },
  '/food/recipes/traybake/': {
    p: null, y: 'one traybake', k: 'makes', w: true, h: false,
    m: { kind: 'count', base: 1, stem: 'traybake', rest: '', box: '1' },
    i: []
  },
  '/food/recipes/squares/': {
    p: null, y: '24 squares', k: 'makes', w: true, h: false,
    m: { kind: 'count', base: 24, stem: 'squares', rest: '', box: '24' },
    i: []
  },
  '/food/recipes/dozens/': {
    p: null, y: 'about 3 dozen', k: 'makes', w: true, h: false,
    m: { kind: 'count', base: 3, stem: 'dozen', rest: '', box: '3', invariable: true },
    i: []
  },
  '/food/recipes/qq/': {
    p: null, y: 'QQ', k: 'serves',
    i: [{ a: '200 g', n: 'plain flour', s: 'cupboard' }]
  }
};

const TITLES = {
  '/food/recipes/a/': 'Aubergine thing',
  '/food/recipes/gelato/': 'Blackberry gelato',
  '/food/recipes/cookies/': 'Peanut Butter Cookies',
  '/food/recipes/cake/': 'Beetroot Chocolate Cake',
  '/food/recipes/sauce/': 'Peanut Sauce',
  '/food/recipes/pies/': 'Mince Pies',
  '/food/recipes/traybake/': 'Rainbow Confetti',
  '/food/recipes/squares/': 'Sweet Potato Chocolate Brownies',
  '/food/recipes/dozens/': 'Mince Pies',
  '/food/recipes/qq/': 'A draft'
};

const AISLES = [
  { key: 'produce', label: 'produce' },
  { key: 'cupboard', label: 'store cupboard' },
  { key: 'dairy', label: 'dairy' }
];

function rows(extra) {
  return rowsModule.create(Object.assign({
    recipes: RECIPES, titles: TITLES, escape: esc,
    containerNouns: ['jar', 'tin', 'batch'],
    buildOptions: { aisles: AISLES, wholeMeasures: ['handful', 'pinch'], countNouns: ['onion', 'lemon'] }
  }, extra || {}));
}

const text = (html) => html.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
const said = (url, n) => text(rows().rowInner(url, n));

// --- what a row counts --------------------------------------------------------

test('a recipe starts at its own portions, or one batch, or one', () => {
  const r = rows();
  assert.strictEqual(r.defaultCount('/food/recipes/a/'), 4, 'serves 4 starts at 4');
  assert.strictEqual(r.defaultCount('/food/recipes/gelato/'), 1,
    'a makes: recipe starts at one batch, never its portion estimate');
  assert.strictEqual(r.defaultCount('/food/recipes/qq/'), 1);
});

test('a stored count is taken only as far as the recipe can support it', () => {
  const r = rows();
  assert.strictEqual(r.count('/food/recipes/gelato/', 0.5), 0.5, 'half a gelato is offered');
  assert.strictEqual(r.count('/food/recipes/cookies/', 0.5), 1, 'half the cookies is half an egg');
  assert.strictEqual(r.count('/food/recipes/qq/', 200), 1,
    'A STORED NUMBER CANNOT RESURRECT A BOX THE RECIPE CANNOT SUPPORT');
  assert.strictEqual(r.count('/food/recipes/a/', null), 4, 'nothing stored is the recipe as written');
});

test('portions or batches scale the recipe; a recipe with no count scales by one', () => {
  const r = rows();
  assert.strictEqual(r.scale('/food/recipes/a/', 8), 2);
  assert.strictEqual(r.scale('/food/recipes/cookies/', 3), 3);
  assert.strictEqual(r.scale('/food/recipes/qq/', 7), 1);
});

test('there is no batch and a half: the spinner goes on to the next whole one', () => {
  const r = rows();
  assert.strictEqual(r.batchCount('/food/recipes/gelato/', 1.5, 1), 2, 'up from 1');
  assert.strictEqual(r.batchCount('/food/recipes/gelato/', 1.5, 2), 1, 'down from 2');
  assert.strictEqual(r.batchCount('/food/recipes/gelato/', 0.3, 1), 0.5);
  assert.strictEqual(r.batchCount('/food/recipes/cookies/', 0.5, 1), 1);
  assert.strictEqual(r.batchCount('/food/recipes/cookies/', 0, 1), null, 'nothing usable is null');
});

test('portions are whole, from 1 to 99', () => {
  const r = rows();
  assert.strictEqual(r.portionCount('3.6'), 4);
  assert.strictEqual(r.portionCount(0), null);
  assert.strictEqual(r.portionCount(500), 99);
});

// --- the words of a row ---------------------------------------------------------

test('a serves: row counts portions, then names the recipe', () => {
  assert.strictEqual(said('/food/recipes/a/', 4), 'portions of Aubergine thing');
  assert.strictEqual(said('/food/recipes/a/', 1), 'portion of Aubergine thing');
});

test('a makes: row counts batches, and says the figure after "of" only for a count above one', () => {
  assert.strictEqual(said('/food/recipes/cookies/', 1), 'batch of 18 Peanut Butter Cookies');
  assert.strictEqual(said('/food/recipes/cookies/', 2), 'batches of 18 Peanut Butter Cookies');
  assert.strictEqual(said('/food/recipes/gelato/', 1), 'batch of Blackberry gelato',
    '"batch of 750 ml Blackberry gelato" reads worse than the name alone');
});

test('one cake is a cake, a jar holds the sauce, and a dozen stays a dozen', () => {
  assert.strictEqual(said('/food/recipes/cake/', 1), '× 8-inch Beetroot Chocolate Cake');
  assert.strictEqual(said('/food/recipes/cake/', 2), '× 8-inch Beetroot Chocolate Cake');
  assert.strictEqual(said('/food/recipes/sauce/', 1), 'jar of Peanut Sauce');
  assert.strictEqual(said('/food/recipes/sauce/', 2), 'jars of Peanut Sauce');
  assert.strictEqual(said('/food/recipes/pies/', 2), 'dozen Mince Pies');
});

test('one thing that IS the dish, and is not in its name, follows the name', () => {
  assert.strictEqual(said('/food/recipes/traybake/', 1), 'Rainbow Confetti traybake');
  assert.strictEqual(said('/food/recipes/traybake/', 3), 'Rainbow Confetti traybakes');
});

test('a batch says what it is a batch OF, the title\'s own noun going singular before it', () => {
  assert.strictEqual(said('/food/recipes/squares/', 1), 'batch of 24 Sweet Potato Chocolate Brownie squares');
  assert.strictEqual(said('/food/recipes/dozens/', 1), 'batch of 3 dozen Mince Pies');
});

function sayOne(recipe, title, n) {
  return text(rowsModule.create({
    recipes: { '/r/': recipe }, titles: { '/r/': title }, escape: esc,
    containerNouns: ['jar', 'tin', 'batch', 'bowl']
  }).rowInner('/r/', n || 1));
}

test('a sized bowl holds the dish: "× 24-cm trifle bowl of", not after the name', () => {
  assert.strictEqual(sayOne({
    p: null, y: 'one 24-cm trifle bowl', k: 'makes', w: true, h: false,
    m: { kind: 'count', base: 1, stem: '24-cm trifle bowl', rest: '', box: '1', times: true }
  }, 'Blackberry Syllabub'), '× 24-cm trifle bowl of Blackberry Syllabub',
  'Helen\'s example: never "24-cm trifle Blackberry Syllabub bowl"');
});

test('a hyphened title names its parts: Sacher-Torte is a torte', () => {
  assert.strictEqual(sayOne({
    p: null, y: 'one 19-cm torte', k: 'makes', w: true, h: false,
    m: { kind: 'count', base: 1, stem: '19-cm torte', rest: '', box: '1', times: true }
  }, 'Sacher-Torte'), '× 19-cm Sacher-Torte');
});

test('the thing made goes after the title\'s noun, before its "with"', () => {
  assert.strictEqual(sayOne({
    p: null, y: '30 pieces', k: 'makes', w: true, h: false,
    m: { kind: 'count', base: 30, stem: 'pieces', rest: '', box: '30' }
  }, 'Potato Cakes with Smoked Salmon'), 'batch of 30 Potato Cake pieces with Smoked Salmon');
});

test('"enough marinade for 4 portions of fish" follows the name, as written', () => {
  assert.strictEqual(sayOne({
    p: null, y: 'enough marinade for 4 portions of fish', k: 'makes', w: true, h: false,
    m: { kind: 'count', base: 4, prefix: 'enough marinade for', stem: 'portions', rest: ' of fish', box: '4' }
  }, 'Sticky Soy and Miso Dipping Sauce'),
  'batch of Sticky Soy and Miso Dipping Sauce, enough marinade for 4 portions of fish');
});

test('NO PORTION FIGURE IS PRINTED FOR A `makes:` RECIPE, in its words, title or label', () => {
  const r = rows();
  const html = (r.boxHtml('/food/recipes/gelato/', 2) + r.rowInner('/food/recipes/gelato/', 2))
    .replace(/ class="[^"]*"/g, '');
  assert.ok(!/portion/.test(html), html);
  assert.ok(html.includes('which makes About 750 ml'), 'the yield, in its own words');
});

test('the name is a link in the row title\'s class, the figure and words outside it', () => {
  const html = rows({ hrefs: { '/food/recipes/cookies/': '/base/food/recipes/cookies/' } })
    .rowInner('/food/recipes/cookies/', 1);
  assert.ok(html.includes(
    '18 <a class="shopping-list-recipe-link" href="/base/food/recipes/cookies/">Peanut Butter Cookies</a>'), html);
  assert.ok(rows().rowInner('/food/recipes/a/', 4, '/x/?list=l1').includes('href="/x/?list=l1"'),
    'a caller may send the link somewhere of its own');
});

test('a title is escaped wherever it goes', () => {
  const r = rows({ titles: { '/food/recipes/a/': 'Fish <& chips>' } });
  const html = r.rowInner('/food/recipes/a/', 4) + r.boxHtml('/food/recipes/a/', 4);
  assert.ok(!html.includes('<&'), html);
  assert.ok(html.includes('Fish &lt;&amp; chips&gt;'));
});

// --- the box ----------------------------------------------------------------------

test('a portions box quotes the yield on hover and to a screen reader, never beside the name', () => {
  const html = rows().boxHtml('/food/recipes/a/', 4);
  assert.match(html, /min="1" max="99" step="1"/);
  assert.match(html, /value="4" data-url="\/food\/recipes\/a\/"/);
  assert.ok(html.includes('title="Aubergine thing, which serves 4"'), html);
  assert.ok(html.includes('aria-label="portions of Aubergine thing, which serves 4"'), html);
  assert.ok(!rows().rowInner('/food/recipes/a/', 4).includes('serves'), 'the yield is beside the name again');
});

test('a batch box steps in halves only where a half is offered, and says what it counts', () => {
  const r = rows();
  assert.match(r.boxHtml('/food/recipes/gelato/', 1), /min="0\.5" max="99" step="0\.5"/);
  assert.match(r.boxHtml('/food/recipes/cookies/', 1), /min="1" max="99" step="1"/);
  assert.match(r.boxHtml('/food/recipes/cookies/', 1), /data-batches/);
  assert.ok(r.boxHtml('/food/recipes/cookies/', 1).includes(
    'aria-label="batches of Peanut Butter Cookies, which makes 18 cookies"'));
  assert.ok(r.boxHtml('/food/recipes/cake/', 1).includes(
    'aria-label="how many: Beetroot Chocolate Cake, which makes one 8-inch cake"'),
    'one whole thing is counted as itself; the label cannot move with the number');
});

test('a caller\'s attributes ride on the box', () => {
  assert.match(rows().boxHtml('/food/recipes/a/', 4, 'data-list="l3"'), /data-url="\/food\/recipes\/a\/" data-list="l3"/);
});

test('a recipe with NO portion count gets no box, and says why', () => {
  const r = rows();
  assert.strictEqual(r.boxHtml('/food/recipes/qq/', 1), '', 'no control that cannot work');
  assert.match(r.unscalableHtml('/food/recipes/qq/'), /no serving size — open <code>serves:<\/code> with a number/);
});

// --- the aisles ---------------------------------------------------------------------

function aisles(list) {
  const r = rows();
  let entries = [];
  list.forEach(([url, n]) => { entries = entries.concat(r.entries(url, r.scale(url, n))); });
  return r.build(entries);
}

const ticks = (on) => ({
  box: (key) => '<input type="checkbox" class="shopping-list-tick" data-key="' + key + '"' + (on.includes(key) ? ' checked' : '') + '>',
  rowClass: (key) => (on.includes(key) ? ' is-ticked' : '')
});

test('each row carries its tick box inside its label, and a ticked row is marked', () => {
  const html = rows().aislesHtml(aisles([['/food/recipes/a/', 4]]), ticks(['onion']));
  assert.ok(html.includes(
    '<li class="shopping-list-row is-ticked"><label class="shopping-list-line">' +
    '<input type="checkbox" class="shopping-list-tick" data-key="onion" checked>' +
    '<span class="shopping-list-amount">2</span>'), html);
  assert.ok(html.indexOf('produce') < html.indexOf('store cupboard'), 'aisles in the declared order');
});

test('asked for, each row says which recipes it is for, closed until its own chevron opens it', () => {
  const r = rows();
  const both = aisles([['/food/recipes/a/', 4], ['/food/recipes/cake/', 1]]);
  const closed = r.aislesHtml(both, ticks([]), { open: () => false });
  const flour = closed.slice(closed.indexOf('data-from-toggle="plain flour'));
  assert.match(flour, /^data-from-toggle="[^"]*" aria-expanded="false" aria-controls="(shopping-from-\d+)" aria-label="which recipes use plain flour"><\/button>/);
  const id = /aria-controls="(shopping-from-\d+)"/.exec(flour)[1];
  assert.ok(closed.includes('<p class="shopping-list-from" id="' + id + '" hidden>for ' +
    '<a class="shopping-list-recipe-link" href="/food/recipes/a/">Aubergine thing</a>, ' +
    '<a class="shopping-list-recipe-link" href="/food/recipes/cake/">'), closed);
  assert.ok(closed.indexOf('</label><button') !== -1, 'the chevron is outside the label, so it never ticks the row');
  const open = r.aislesHtml(both, ticks([]), { open: (key) => key.indexOf('plain flour') === 0 });
  assert.ok(open.includes('id="' + id + '">for '), 'a row asked open starts open');
  assert.strictEqual(new Set(closed.match(/id="shopping-from-\d+"/g)).size, closed.match(/id="shopping-from-\d+"/g).length,
    'every breakdown has its own id');
});

test('with a breakdown, a line\'s not-scaled bracket goes under it, before the breakdown', () => {
  const html = rows().aislesHtml(aisles([['/food/recipes/a/', 4]]), ticks([]), { open: () => false });
  assert.ok(html.includes('</div><p class="shopping-list-unscaled">(' +
    '<a class="shopping-list-recipe-link" href="/food/recipes/a/">Aubergine thing</a>)</p>' +
    '<p class="shopping-list-from"'), html);
});

test('not asked for, a row has no breakdown and its markup is as before', () => {
  const html = rows().aislesHtml(aisles([['/food/recipes/a/', 4]]), ticks([]));
  assert.ok(!html.includes('shopping-list-from'), html);
});

test('an item nobody scaled names its recipe as a link, outside the tick\'s label', () => {
  const html = rows().aislesHtml(aisles([['/food/recipes/a/', 4]]), ticks([]));
  assert.ok(html.includes(
    '<span class="shopping-list-name">olive oil</span></label>' +
    '<span class="shopping-list-unscaled">(' +
    '<a class="shopping-list-recipe-link" href="/food/recipes/a/">Aubergine thing</a>)</span>'), html);
  assert.strictEqual(rows().unscaledNote(aisles([['/food/recipes/a/', 4]])), '(Not scaled: olive oil)');
  assert.strictEqual(rows().unscaledNote(aisles([['/food/recipes/cookies/', 1]])), '', 'nothing unscaled, no note');
});

test('a by-eye measure is totalled to a whole one, from the options handed over', () => {
  const r = rowsModule.create({
    recipes: { '/r/': { p: 4, y: '4', k: 'serves', i: [{ a: '1 handful', n: 'parsley', s: 'produce' }] } },
    titles: {}, escape: esc, buildOptions: { aisles: AISLES, wholeMeasures: ['handful'] }
  });
  const html = r.aislesHtml(r.build(r.entries('/r/', r.scale('/r/', 7))), ticks([]));
  assert.match(html, /<span class="shopping-list-amount">2 handfuls<\/span>/);
});

test('the juice and the zest of one lemon is one lemon, through the entries', () => {
  const r = rowsModule.create({
    recipes: { '/r/': { p: 4, y: '4', k: 'serves', i: [
      { a: '', n: 'juice of 1 lemon', s: 'produce', pt: ['juice'], f: 'lemon', c: '1' },
      { a: '', n: 'zest of 1 lemon', s: 'produce', pt: ['zest'], f: 'lemon', c: '1' },
      { a: '85 ml', n: 'olive oil', s: 'cupboard' },
      { a: '', n: 'olive oil', s: 'cupboard', x: true }] } },
    titles: {}, escape: esc, buildOptions: { aisles: AISLES }
  });
  const html = r.aislesHtml(r.build(r.entries('/r/', 1)), ticks([]));
  assert.match(html, /<span class="shopping-list-amount">1<\/span><span class="shopping-list-name">lemon<\/span>/);
  assert.ok(!html.includes('×'), 'the pointer line added a count to the oil');
});

test('a per-person amount is that many people\'s worth', () => {
  const r = rowsModule.create({
    recipes: { '/r/': { p: 4, y: '4', k: 'serves', i: [{ a: '250 g per person', n: 'mussels', s: 'produce' }] } },
    titles: {}, escape: esc, buildOptions: { aisles: AISLES }
  });
  const html = r.aislesHtml(r.build(r.entries('/r/', r.scale('/r/', 6))), ticks([]));
  assert.match(html, /1\.5 kg/);
});

test('a costed total hands back its figure and the sum that names what it left out', () => {
  const r = rows({ buildOptions: { aisles: AISLES, costUnits: {} } });
  const got = r.total([
    { label: 'flour', cost: { min: 1, max: 1 } },
    { label: 'kombu', cost: { unpriced: true } }
  ]);
  assert.strictEqual(got.text, 'from £1.00',
    'a total missing a line is "from" what is known, never "roughly"');
  assert.deepStrictEqual(Array.from(got.sum.unpricedNames), ['kombu'],
    'shoppingList.drawTotal names the unpriced lines from this (#1523)');
});

test('with no cost units nothing is costed or totalled', () => {
  assert.strictEqual(rows().total([{ label: 'x', cost: { min: 1, max: 1 } }]), null);
  assert.strictEqual(rows().withCost('/food/recipes/a/', '<span>s</span>'), '<span>s</span>');
});
