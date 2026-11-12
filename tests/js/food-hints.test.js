// food-hints.js: the words behind a stock or spice hint. Run from the repo
// root with `node --test`. The data here is a fixture in the shape of
// _data/food/ingredient_hints.yml (tests/test_ingredient_hints.py holds that
// file to the shape), so these cases do not move when a packet's figure does.
'use strict';

const test = require('node:test');
const assert = require('node:assert');

const { stockHint, spiceHint } = require('../../assets/js/food-hints.js');

const DATA = {
  stock: {
    flavours: ['chicken', 'vegetable', 'beef', 'fish'],
    other_flavours: ['lamb', 'venison'],
    not_stock: ['stock cube', 'stock cubes', 'stock pot'],
    products: [
      { name: 'Kallo', unit: 'cube', flavours: { chicken: 500, vegetable: 500, beef: 500 } },
      { name: 'Oxo', unit: 'cube', flavours: { chicken: 190, beef: 190 } },
      { name: 'Knorr', unit: 'Stock Pot', flavours: { chicken: 500, fish: 500 } },
      { name: 'Marigold bouillon', unit: 'level tsp', flavours: { vegetable: 250, chicken: 250 } }
    ]
  },
  spices: [
    { name: 'cinnamon', match: ['ground cinnamon', 'cinnamon'], unless: ['stick', 'sticks'],
      g_per_tsp: 2.6, whole: 'cinnamon stick' },
    { name: 'ginger', match: ['ground ginger', 'ginger'], unless: ['fresh', 'grated', 'stem'],
      g_per_tsp: 1.8, fresh_tbsp_per_tsp: 4 },
    { name: 'nutmeg', match: ['ground nutmeg', 'grated nutmeg', 'nutmeg'], unless: ['whole'],
      g_per_tsp: 2.2, whole: 'whole nutmeg', per_whole_tsp: 2.5 },
    { name: 'cumin', match: ['ground cumin'], unless: ['seeds'], g_per_tsp: 2.1, whole: 'cumin seeds' }
  ]
};

function stock(amount, item) {
  const h = stockHint(amount, item, DATA);
  return h && [h.title].concat(h.lines);
}

function spice(amount, item) {
  const h = spiceHint(amount, item, DATA);
  return h && [h.title].concat(h.lines);
}

test('stock: Helen\'s way round -- for the recipe\'s water, how much of each', () => {
  assert.deepStrictEqual(stock('500 ml', 'chicken stock'), [
    'In 500 ml of boiling water:',
    '1 Kallo cube', '2½ Oxo cubes', '1 Knorr Stock Pot', '2 level tsp Marigold bouillon'
  ]);
});

test('stock: only the products that come in the line\'s flavour', () => {
  assert.deepStrictEqual(stock('500 ml', 'fish stock'),
    ['In 500 ml of boiling water:', '1 Knorr Stock Pot']);
  // "beef or venison stock" is beef: the first flavour named.
  assert.deepStrictEqual(stock('500 ml', 'beef or venison stock'),
    ['In 500 ml of boiling water:', '1 Kallo cube', '2½ Oxo cubes']);
});

test('stock: a flavour no product comes in gets no hint; no flavour gets them all', () => {
  assert.strictEqual(stock('500 ml', 'lamb stock'), null);
  assert.strictEqual(stock('500 ml', 'hot stock').length, 5);
});

test('stock: cubes and spoons go to the nearest half, never below a half', () => {
  assert.deepStrictEqual(stock('100 ml', 'chicken stock').slice(1, 3),
    ['½ Kallo cube', '½ Oxo cube']);
});

test('stock: litres, pints and ranges are read as volumes', () => {
  assert.strictEqual(stock('1.5 litres', 'vegetable stock')[0], 'In 1½ litres of boiling water:');
  assert.strictEqual(stock('1 pint', 'chicken stock')[0], 'In 568 ml of boiling water:');
  assert.deepStrictEqual(stock('300–400 ml', 'chicken stock').slice(0, 2),
    ['In 300–400 ml of boiling water:', '½–1 Kallo cube']);
});

test('stock: a line that is the product, or has no volume, gets none', () => {
  assert.strictEqual(stock('2', 'chicken stock cubes'), null);
  assert.strictEqual(stock('1', 'Knorr chicken stock pot'), null);
  assert.strictEqual(stock('a splash', 'chicken stock'), null);
  assert.strictEqual(stock('500 g', 'chicken stock'), null);
});

test('spice: a ground spice by the spoon gets its weight, to grind your own', () => {
  assert.deepStrictEqual(spice('1 tsp', 'ground cinnamon'),
    ['About 2.6 g.', 'Grinding your own? Weigh 2.6 g of cinnamon stick.']);
  assert.deepStrictEqual(spice('1 tbsp', 'ground cumin'),
    ['About 6.3 g.', 'Grinding your own? Weigh 6.3 g of cumin seeds.']);
  assert.strictEqual(spice('1 level tsp', 'cinnamon')[0], 'About 2.6 g.');
});

test('spice: ginger also says the classic fresh figure, 1 tbsp per ¼ tsp', () => {
  assert.deepStrictEqual(spice('1 tsp', 'ground ginger'),
    ['About 1.8 g.', 'Or 4 tbsp finely grated fresh ginger.']);
});

test('spice: nutmeg also says how much of a nutmeg', () => {
  assert.deepStrictEqual(spice('1 tsp', 'freshly grated nutmeg').slice(2),
    ['That is about ½ a nutmeg, grated.']);
  assert.deepStrictEqual(spice('2½ tsp', 'ground nutmeg').slice(2),
    ['That is about a whole nutmeg, grated.']);
});

test('spice: a whole spice, a fresh one, two spices or no spoon gets none', () => {
  assert.strictEqual(spice('1', 'cinnamon stick'), null);
  assert.strictEqual(spice('1 tsp', 'cinnamon sticks, broken'), null);
  assert.strictEqual(spice('1 tbsp', 'grated ginger'), null);
  assert.strictEqual(spice('½ tsp', 'each ground cumin and ground cinnamon'), null);
  assert.strictEqual(spice('1 tsp', 'ground cumin and ground cinnamon'), null);
  assert.strictEqual(spice('a pinch', 'ground cinnamon'), null);
  assert.strictEqual(spice('1 tsp', 'paprika'), null);
});
