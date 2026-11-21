// HTF.lists (assets/js/shortlists-store.js): named shortlists, their recipes
// and portions, and the one place their storage key lives. MANUAL §8.9.
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { makePage, load } = require('./stub-dom.js');

const plain = (value) => JSON.parse(JSON.stringify(value));

function storage(initial) {
  const store = Object.assign(Object.create(null), initial);
  return {
    getItem: (key) => (key in store ? store[key] : null),
    setItem: (key, value) => { store[key] = String(value); },
    removeItem: (key) => { delete store[key]; },
    clear: () => { throw new Error('localStorage.clear() wipes every site on the origin'); },
    keys: () => Object.keys(store).sort(),
    read: (key) => store[key]
  };
}

function boot(initial, site) {
  const store = storage(initial);
  const page = makePage({ 'base-url': '/', 'site-key': site || 'food' });
  page.localStorage = store;
  load(['assets/js/assets.js', 'assets/js/shortlists-store.js'], page);
  return { lists: page.HTF.lists, core: page.HTF.lists.core, store };
}

const A = '/food/recipes/a/';
const B = '/food/recipes/b/';
const C = '/food/recipes/c/';

// --- names ---------------------------------------------------------------------

test('a new list keeps its trimmed name and starts empty', () => {
  const { core } = boot();
  const made = core.create(core.empty(), '  Christmas starters  ');
  assert.strictEqual(made.error, undefined, 'a good name is accepted');
  assert.deepStrictEqual(plain(made.state.lists),
    [{ id: made.id, name: 'Christmas starters', items: [], ticked: [] }]);
});

test('an empty or all-space name is refused, saying so', () => {
  const { core } = boot();
  for (const name of ['', '   ', null]) {
    const made = core.create(core.empty(), name);
    assert.strictEqual(made.error, 'empty', `"${name}" should be refused as empty`);
    assert.strictEqual(made.state.lists.length, 0, 'and nothing is made');
  }
});

test('a clashing name is refused whatever its case, for new lists and renames', () => {
  const { core } = boot();
  let s = core.create(core.empty(), 'Lemons').state;
  const other = core.create(s, 'Limes');
  s = other.state;
  assert.strictEqual(core.create(s, ' lemons ').error, 'clash', 'a new list may not repeat a name');
  assert.strictEqual(core.rename(s, other.id, 'LEMONS').error, 'clash', 'nor may a rename');
  assert.strictEqual(core.rename(s, other.id, 'limes').error, undefined,
    'a list may be renamed to its own name in another case');
  assert.strictEqual(core.rename(s, other.id, '  ').error, 'empty', 'a rename to nothing is refused');
});

test('ids are never reused, even after a delete', () => {
  const { core } = boot();
  let s = core.create(core.empty(), 'One').state;
  const firstId = s.lists[0].id;
  s = core.remove(s, firstId);
  const again = core.create(s, 'Two');
  assert.notStrictEqual(again.id, firstId, 'a deleted id must not come back on a new list');
});

// --- membership and portions -------------------------------------------------

test('ticking a recipe into a list sets its portions to the default given', () => {
  const { core } = boot();
  const made = core.create(core.empty(), 'Lemons');
  const s = core.setMember(made.state, made.id, A, true, 4);
  assert.deepStrictEqual(plain(s.lists[0].items), [{ recipe: A, portions: 4 }]);
});

test('a recipe may be on several lists, each with its own portions', () => {
  const { core } = boot();
  let s = core.empty();
  const one = core.create(s, 'One'); s = one.state;
  const two = core.create(s, 'Two'); s = two.state;
  s = core.setMember(s, one.id, A, true, 4);
  s = core.setMember(s, two.id, A, true, 4);
  s = core.setPortions(s, two.id, A, 8);
  assert.deepStrictEqual(plain(core.listsWith(s, A)), [one.id, two.id]);
  assert.strictEqual(core.portions(s, one.id, A), 4, 'one list keeps its own number');
  assert.strictEqual(core.portions(s, two.id, A), 8, 'when the other changes');
});

test('unticking removes the recipe from that list only; ticking twice adds once', () => {
  const { core } = boot();
  let s = core.empty();
  const one = core.create(s, 'One'); s = one.state;
  const two = core.create(s, 'Two'); s = two.state;
  s = core.setMember(s, one.id, A, true, 4);
  s = core.setMember(s, one.id, A, true, 6);
  assert.strictEqual(s.lists[0].items.length, 1, 'a second tick must not add a second row');
  assert.strictEqual(core.portions(s, one.id, A), 4, 'nor reset its portions');
  s = core.setMember(s, two.id, A, true, 4);
  s = core.setMember(s, one.id, A, false);
  assert.deepStrictEqual(plain(core.listsWith(s, A)), [two.id]);
});

test('portions take halves, and nothing below a half or above 99', () => {
  const { core } = boot();
  const made = core.create(core.empty(), 'L');
  let s = core.setMember(made.state, made.id, A, true, 1);
  const cases = [[2.5, 2.5], [2.4, 2.5], [0, 0.5], [-3, 0.5], [500, 99], [NaN, 1], ['6', 6]];
  for (const [given, kept] of cases) {
    s = core.setPortions(s, made.id, A, given);
    assert.strictEqual(core.portions(s, made.id, A), kept, `setPortions(${given}) should keep ${kept}`);
  }
});

// --- order ---------------------------------------------------------------------

test('lists and their recipes keep the order given, and move one step or to a place', () => {
  const { core } = boot();
  let s = core.empty();
  const ids = ['One', 'Two', 'Three'].map((name) => {
    const made = core.create(s, name); s = made.state; return made.id;
  });
  s = core.moveList(s, ids[2], 0);
  assert.deepStrictEqual(plain(s.lists.map((l) => l.name)), ['Three', 'One', 'Two'], 'moved to the front');
  s = core.moveList(s, ids[2], 99);
  assert.deepStrictEqual(plain(s.lists.map((l) => l.name)), ['One', 'Two', 'Three'], 'past the end lands last');
  [A, B, C].forEach((r) => { s = core.setMember(s, ids[0], r, true, 1); });
  s = core.moveItem(s, ids[0], C, 0);
  assert.deepStrictEqual(plain(s.lists[0].items.map((i) => i.recipe)), [C, A, B]);
});

// --- delete and view ---------------------------------------------------------

test('deleting the list on view lands the view on everything', () => {
  const { core } = boot();
  const made = core.create(core.empty(), 'Lemons');
  let s = core.setView(made.state, made.id);
  assert.strictEqual(s.view, made.id);
  s = core.remove(s, made.id);
  assert.strictEqual(s.view, core.EVERYTHING);
  assert.strictEqual(s.lists.length, 0);
});

test('a view naming no list reads as everything', () => {
  const { core } = boot();
  assert.strictEqual(core.setView(core.empty(), 'l99').view, core.EVERYTHING);
});

// --- shopping ticks -----------------------------------------------------------

test('shopping ticks are kept per list and for everything, apart', () => {
  const { core } = boot();
  const made = core.create(core.empty(), 'L');
  let s = core.setTicked(made.state, made.id, 'onion', true);
  s = core.setTicked(s, core.EVERYTHING, 'flour', true);
  assert.deepStrictEqual(plain(core.ticked(s, made.id)), ['onion']);
  assert.deepStrictEqual(plain(core.ticked(s, core.EVERYTHING)), ['flour']);
  s = core.setTicked(s, made.id, 'onion', false);
  assert.deepStrictEqual(plain(core.ticked(s, made.id)), []);
});

test('unticking named rows leaves the rest, and no names unticks them all', () => {
  const { core } = boot();
  const made = core.create(core.empty(), 'L');
  let s = made.state;
  ['onion', 'flour', 'egg'].forEach((key) => { s = core.setTicked(s, made.id, key, true); });
  s = core.setTicked(s, core.EVERYTHING, 'onion', true);
  s = core.untick(s, made.id, ['onion', 'egg']);
  assert.deepStrictEqual(plain(core.ticked(s, made.id)), ['flour'], 'only the named rows go');
  assert.deepStrictEqual(plain(core.ticked(s, core.EVERYTHING)), ['onion'], 'and only in that scope');
  s = core.untick(s, made.id);
  assert.deepStrictEqual(plain(core.ticked(s, made.id)), [], 'no names is every row');
});

// --- storage --------------------------------------------------------------------

test('food reads and writes one key, versioned, and nothing else', () => {
  const { lists, store } = boot();
  const made = lists.create('Lemons');
  lists.setMember(made.id, A, true, 4);
  assert.deepStrictEqual(store.keys(), [lists.KEY], 'only the new key is written');
  assert.match(lists.KEY, /^htf-lists-food-v\d+$/, 'the key names its site and version');
  const again = boot({ [lists.KEY]: store.read(lists.KEY) });
  assert.deepStrictEqual(plain(again.lists.all()), plain(lists.all()), 'a reload reads back what was written');
});

test("on load, food's old shortlist keys are removed by name; cocktails' are never touched", () => {
  const old = {
    'htf-shortlist-food-v1': '["/food/recipes/a/"]',
    'htf-shortlist-glasses-food-v1': '{}',
    'htf-shortlist-portions-food-v1': '{}',
    'htf-shortlist-portions-food-v2': '{}',
    'htf-shortlist-batches-food-v1': '{}',
    'htf-shortlist-ticked-food-v1': '[]',
    'htf-shortlists-food-v1': '{"lists":[]}',
    'htf-shortlist-cocktails-v1': '["/cocktails/x/"]',
    'htf-shortlist-glasses-cocktails-v1': '{"/cocktails/x/":2}',
    'isitrhubarbyet-season': 'keep me'
  };
  const { lists, store } = boot(old);
  lists.all();
  assert.deepStrictEqual(store.keys(), [
    'htf-shortlist-cocktails-v1', 'htf-shortlist-glasses-cocktails-v1', 'isitrhubarbyet-season'
  ], 'only food\'s old keys go; another site\'s data and cocktails\' live list stay');
});

test('a stored record in the wrong shape reads as no lists, and a bad list costs only itself', () => {
  for (const raw of ['not json', '[]', '{"lists": 3}', 'null']) {
    const { lists } = boot({ 'htf-lists-food-v1': raw });
    assert.deepStrictEqual(plain(lists.all()), [], `${raw} should read as no lists`);
  }
  const { lists } = boot({ 'htf-lists-food-v1': JSON.stringify({ lists: [
    { id: 'l1', name: 'Good', items: [{ recipe: A, portions: 4 }, { recipe: 7 }] },
    { id: 'l2', name: '' },
    'junk'
  ] }) });
  assert.deepStrictEqual(plain(lists.all()), [
    { id: 'l1', name: 'Good', items: [{ recipe: A, portions: 4 }], ticked: [] }
  ]);
});

test('refresh() reads the key again, so a page back from the cache shows what another page saved', () => {
  const { lists, store } = boot();
  lists.all();
  const other = boot({ [lists.KEY]: store.read(lists.KEY) });
  other.lists.create('Made elsewhere');
  store.setItem(lists.KEY, other.store.read(other.lists.KEY));
  assert.strictEqual(lists.all().length, 0, 'without a refresh the page keeps what it read');
  lists.refresh();
  assert.deepStrictEqual(plain(lists.all().map((l) => l.name)), ['Made elsewhere']);
});

test('a write that throws still leaves the lists working for this visit', () => {
  const store = storage();
  store.setItem = () => { throw new Error('QuotaExceededError'); };
  const page = makePage({ 'base-url': '/', 'site-key': 'food' });
  page.localStorage = store;
  load(['assets/js/assets.js', 'assets/js/shortlists-store.js'], page);
  const made = page.HTF.lists.create('Lemons');
  assert.strictEqual(page.HTF.lists.all().length, 1, 'the list exists in memory');
  assert.strictEqual(made.error, undefined);
});
