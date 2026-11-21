// HTF.listsShare (assets/js/shortlists-share.js): lists as links and links
// as lists, with no DOM. MANUAL §8.9.
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const share = require('../../assets/js/shortlists-share.js');

const BASE = 'https://example.org/helen-triages/food/shortlists/';
const STARTERS = { name: 'Christmas starters & nibbles', items: [
  { recipe: '/helen-triages/food/recipes/canapes/gougeres/', portions: 12 },
  { recipe: '/helen-triages/food/recipes/cookies/', portions: 1.5 }
] };

test('a list\'s link carries its recipes by slug, their portions in order, and its name', () => {
  assert.strictEqual(share.link(BASE, STARTERS),
    BASE + '?shortlist=gougeres,cookies&portions=12,1.5&list=Christmas%20starters%20%26%20nibbles');
});

test('a block is one "Name: link" line per list, in order, and reads back as it was', () => {
  const lemons = { name: 'Lemons', items: [] };
  const text = share.block(BASE, [STARTERS, lemons]);
  assert.strictEqual(text.split('\n').length, 2);
  assert.ok(text.startsWith('Christmas starters & nibbles: ' + BASE + '?shortlist='));
  assert.deepStrictEqual(share.readBlock(text), [
    { name: 'Christmas starters & nibbles', items: [{ slug: 'gougeres', portions: 12 }, { slug: 'cookies', portions: 1.5 }] },
    { name: 'Lemons', items: [] }
  ]);
});

test('an older link with no portions reads each as null, for the recipe\'s own default', () => {
  const old = 'Christmas sides: http://localhost:5000/helen-triages/food/?shortlist=roast-potatoes,sprouts&list=Christmas%20sides';
  assert.deepStrictEqual(share.readBlock(old), [{ name: 'Christmas sides',
    items: [{ slug: 'roast-potatoes', portions: null }, { slug: 'sprouts', portions: null }] }]);
});

test('an unnamed link is named by its line, or not at all', () => {
  assert.deepStrictEqual(share.readBlock('Pies: https://x.org/food/?shortlist=a,b'),
    [{ name: 'Pies', items: [{ slug: 'a', portions: null }, { slug: 'b', portions: null }] }]);
  assert.strictEqual(share.readBlock('https://x.org/food/?shortlist=a')[0].name, '');
  assert.strictEqual(share.read('?shortlist=a').name, '');
});

test('reading is lenient: odd slugs and repeats dropped, bad portions defaulted, chatter passed over', () => {
  const text = [
    'Here you go!',
    '',
    'Mine: https://x.org/food/shortlists/?shortlist=a,A,../etc,b&portions=2,9,x,-1&list=Mine',
    'and that is all'
  ].join('\n');
  assert.deepStrictEqual(share.readBlock(text),
    [{ name: 'Mine', items: [{ slug: 'a', portions: 2 }, { slug: 'b', portions: null }] }]);
  assert.deepStrictEqual(share.readBlock('nothing here'), []);
  assert.strictEqual(share.read('?list=Lemons'), null, 'no shortlist, no list');
});

test('a slug is the last part of a recipe\'s address, whatever folder it sits in', () => {
  assert.strictEqual(share.slugOf('/helen-triages/food/recipes/a/b/gougeres/'), 'gougeres');
  assert.strictEqual(share.slugOf('/food/recipes/gougeres/?list=l1'), 'gougeres');
});
