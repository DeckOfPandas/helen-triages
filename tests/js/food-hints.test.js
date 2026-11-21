// food-hints.js: the words behind a stock or spice hint. Run from the repo
// root with `node --test`. The data here is a fixture in the shape of
// _data/food/ingredient_hints.yml (tests/test_ingredient_hints.py holds that
// file to the shape), so these cases do not move when a packet's figure does.
'use strict';

const test = require('node:test');
const assert = require('node:assert');

const {
  stockHint, spiceHint, wholeSpiceHint, pasteHint, vanillaHint
} = require('../../assets/js/food-hints.js');

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
  vanilla: {
    unless: ['sugar', 'ice cream', 'essence', 'orange', 'almond'],
    forms: [
      { name: 'vanilla bean paste', match: ['vanilla bean paste', 'vanilla paste', 'bean paste', 'or paste'],
        unit: 'tsp', per_pod: 1 },
      { name: 'vanilla pod', match: ['vanilla pod', 'vanilla pods', 'vanilla bean pod', 'vanilla bean'],
        unit: 'pod', per_pod: 1 },
      { name: 'vanilla extract', match: ['vanilla extract', 'or extract'], unit: 'tsp', per_pod: 1 }
    ]
  },
  spices: [
    { name: 'cinnamon', match: ['ground cinnamon', 'cinnamon'], unless: ['stick', 'sticks'],
      g_per_tsp: 2.6 },
    { name: 'ginger', match: ['ground ginger', 'ginger'], unless: ['fresh', 'grated', 'stem'],
      g_per_tsp: 1.8, fresh_tbsp_per_tsp: 4 },
    { name: 'nutmeg', match: ['ground nutmeg', 'grated nutmeg', 'nutmeg'], unless: ['whole'],
      g_per_tsp: 2.2, per_whole_tsp: 2.5,
      whole: { match: ['whole nutmeg', 'nutmeg'], unless: ['ground'], g_each: 4.5 } },
    { name: 'cumin', match: ['ground cumin'], unless: ['seeds'], g_per_tsp: 2.1,
      whole: { match: ['cumin seeds'], unless: ['ground'], g_per_tsp: 2.1 } },
    { name: 'black pepper', match: ['ground black pepper'], unless: ['peppercorns'], g_per_tsp: 2.3,
      whole: { match: ['black peppercorns'], unless: ['ground'], g_per_tsp: 2.9 } }
  ],
  pastes: [
    { name: 'ginger', paste: ['ginger paste'], fresh_match: ['ginger'],
      fresh_unless: ['ground', 'stem', 'paste'], fresh: 'cm', fresh_name: 'fresh ginger', tsp_per: [1, 1] },
    { name: 'garlic', paste: ['garlic paste'], fresh_match: ['garlic cloves', 'garlic clove', 'garlic'],
      fresh_unless: ['granules', 'paste', 'wild'], fresh: 'count',
      unit: ['garlic clove', 'garlic cloves'], tsp_per: [1, 1] },
    { name: 'lemongrass', paste: ['lemongrass paste'], fresh_match: ['lemongrass stalks', 'lemongrass'],
      fresh_unless: ['paste'], fresh: 'count',
      unit: ['lemongrass stalk', 'lemongrass stalks'], tsp_per: [1, 2] }
  ]
};

function title(fn, amount, item) {
  const h = fn(amount, item, DATA);
  return h && h.title;
}

test('whole spice: its weight, and the ground spoonfuls it grinds to (#1528)', () => {
  assert.strictEqual(title(wholeSpiceHint, '1 tsp', 'cumin seeds, toasted'),
    'About 2.1 g, or 1 tsp ground cumin.');
  assert.strictEqual(title(wholeSpiceHint, '1 tsp', 'black peppercorns'),
    'About 2.9 g, or 1¼ tsp ground black pepper.');
  assert.strictEqual(title(wholeSpiceHint, '3 tbsp', 'black peppercorns'),
    'About 26 g, or 4 tbsp ground black pepper.');
});

test('whole spice: a nutmeg is counted, and grates to its teaspoons', () => {
  assert.strictEqual(title(wholeSpiceHint, '½', 'whole nutmeg'),
    'About 2.3 g, or 1¼ tsp ground nutmeg.');
  assert.strictEqual(title(wholeSpiceHint, '¼', 'nutmeg, grated'),
    'About 1.1 g, or ¾ tsp ground nutmeg.');
  assert.strictEqual(title(wholeSpiceHint, '1 tsp', 'whole nutmeg'), null);
});

test('whole spice: ground, by weight, or two spices gets none', () => {
  assert.strictEqual(title(wholeSpiceHint, '1 tsp', 'ground black peppercorns'), null);
  assert.strictEqual(title(wholeSpiceHint, '30 g', 'cumin seeds'), null);
  assert.strictEqual(title(wholeSpiceHint, '1 tsp', 'cumin seeds and black peppercorns'), null);
});

test('paste: fresh root in cm gets the paste, the paste gets the root', () => {
  assert.strictEqual(title(pasteHint, '2.5 cm', 'piece of fresh ginger, grated'),
    'Or 2½ tsp ginger paste.');
  assert.strictEqual(title(pasteHint, '2 cm piece', 'ginger, peeled and grated'),
    'Or 2 tsp ginger paste.');
  assert.strictEqual(title(pasteHint, '1 tbsp', 'ginger paste'),
    'Or a 3 cm piece of fresh ginger.');
  assert.strictEqual(title(pasteHint, '2 inches', 'fresh ginger'), 'Or 5 tsp ginger paste.');
});

test('paste: garlic cloves and lemongrass stalks are counted', () => {
  assert.strictEqual(title(pasteHint, '2', 'garlic cloves, crushed'), 'Or 2 tsp garlic paste.');
  assert.strictEqual(title(pasteHint, '1 large', 'garlic clove'), 'Or 1 tsp garlic paste.');
  assert.strictEqual(title(pasteHint, '3 cloves', 'garlic, minced'), 'Or 3 tsp garlic paste.');
  assert.strictEqual(title(pasteHint, '1 tbsp', 'garlic paste'), 'Or 3 garlic cloves.');
  assert.strictEqual(title(pasteHint, '6', 'garlic cloves'), 'Or 2 tbsp garlic paste.');
  assert.strictEqual(title(pasteHint, '2', 'lemongrass stalks, bruised'),
    'Or 2–4 tsp lemongrass paste.');
  assert.strictEqual(title(pasteHint, '2 tsp', 'lemongrass paste'), 'Or 1–2 lemongrass stalks.');
});

test('paste: granules, grams, a spoon of fresh or two pastes in one gets none', () => {
  assert.strictEqual(title(pasteHint, '1 tsp', 'garlic granules'), null);
  assert.strictEqual(title(pasteHint, '30 g', 'fresh ginger'), null);
  assert.strictEqual(title(pasteHint, '1 tbsp', 'grated ginger'), null);
  assert.strictEqual(title(pasteHint, '4 tbsp', 'garlic and ginger paste'), null);
  assert.strictEqual(title(pasteHint, '1 tsp', 'ground ginger'), null);
});

test('vanilla: a line without the word vanilla is not vanilla', () => {
  assert.strictEqual(title(vanillaHint, '1 tbsp', 'tamarind concentrate or paste'), null);
});

function stock(amount, item) {
  const h = stockHint(amount, item, DATA);
  return h && [h.title].concat(h.rows.map((r) => r.amount + ' ' + r.what));
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

test('spice: a ground spice by the spoon gets its weight, and nothing more (#1527)', () => {
  assert.deepStrictEqual(spice('1 tsp', 'ground cinnamon'), ['About 2.6 g.']);
  assert.deepStrictEqual(spice('1 tbsp', 'ground cumin'), ['About 6.3 g.']);
  assert.strictEqual(spice('1 level tsp', 'cinnamon')[0], 'About 2.6 g.');
});

test('spice: ginger also says the classic fresh figure, 1 tbsp per ¼ tsp', () => {
  assert.deepStrictEqual(spice('1 tsp', 'ground ginger'),
    ['About 1.8 g.', 'Or 4 tbsp finely grated fresh ginger.']);
});

test('spice: nutmeg also says how much of a nutmeg', () => {
  assert.deepStrictEqual(spice('1 tsp', 'freshly grated nutmeg').slice(1),
    ['That is about ½ a nutmeg, grated.']);
  assert.deepStrictEqual(spice('2½ tsp', 'ground nutmeg').slice(1),
    ['That is about a whole nutmeg, grated.']);
});

function vanilla(amount, item) {
  const h = vanillaHint(amount, item, DATA);
  return h && h.title;
}

test('vanilla: 1 tsp paste = 1 tsp extract = 1 pod, every way round (#1517)', () => {
  assert.strictEqual(vanilla('1 tsp', 'vanilla bean paste'),
    'Or 1 vanilla pod, or 1 tsp vanilla extract.');
  assert.strictEqual(vanilla('2 tsp', 'vanilla extract'),
    'Or 2 tsp vanilla bean paste, or 2 vanilla pods.');
  assert.strictEqual(vanilla('1', 'vanilla pod, split lengthways'),
    'Or 1 tsp vanilla bean paste, or 1 tsp vanilla extract.');
  assert.strictEqual(vanilla('1 tbsp', 'vanilla extract'),
    'Or 3 tsp vanilla bean paste, or 3 vanilla pods.');
});

test('vanilla: pods go to the nearest half, never below a half', () => {
  assert.strictEqual(vanilla('¼ tsp', 'vanilla extract'),
    'Or ¼ tsp vanilla bean paste, or ½ vanilla pod.');
  assert.strictEqual(vanilla('1½ tsp', 'vanilla paste'),
    'Or 1½ vanilla pods, or 1½ tsp vanilla extract.');
});

test('vanilla: a form the line already names is not offered again', () => {
  assert.strictEqual(vanilla('1 tsp', 'vanilla bean paste or extract'), 'Or 1 vanilla pod.');
  assert.strictEqual(vanilla('2 tsp', 'vanilla extract, bean paste or 1 vanilla pod, split'), null);
  assert.strictEqual(vanilla('1 tsp', 'vanilla extract or vanilla bean paste'),
    'Or 1 vanilla pod.');
  assert.strictEqual(vanilla('1', 'vanilla pod, seeds scraped out, or 1 tsp vanilla paste'),
    'Or 1 tsp vanilla extract.');
});

test('vanilla: sugar, ice cream, essence, another flavour or no spoon gets none', () => {
  assert.strictEqual(vanilla('6 tbsp', 'vanilla sugar'), null);
  assert.strictEqual(vanilla('200 g', 'vanilla ice cream'), null);
  assert.strictEqual(vanilla('½ tsp', 'vanilla essence'), null);
  assert.strictEqual(vanilla('1 tsp', 'orange or vanilla extract'), null);
  assert.strictEqual(vanilla('3–4 drops', 'pure vanilla extract'), null);
  assert.strictEqual(vanilla('1 tsp', 'vanilla pod'), null);
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
