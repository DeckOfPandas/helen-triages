// Tests for HTF.shortlist in assets/js/assets.js (#546).
//
// Run from the repo root:
//
//   node --test tests/js/*.test.js
//
// Every failure mode here is invisible from an ordinary browser: private mode
// throws on setItem, blocked site data makes the getter throw, and a record
// from an older build parses fine in the wrong shape. A failed write must not
// cost the click that asked for it.
//
// Not tested here: the DOM half, assets/js/shortlist.js, which needs a real
// document. This harness stubs only enough page to read two meta tags.
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { makePage, load } = require('./stub-dom.js');

const FOOD_KEY = 'htf-shortlist-food-v1';

/* Array comparisons go through JSON: `assert.deepStrictEqual` checks
   prototypes, and an array built inside the vm context is an instance of that
   context's Array, so an identical list fails. The round trip rebuilds the
   value in this realm. */
const plain = (value) => JSON.parse(JSON.stringify(value));

/** A working localStorage: the browser's, minus everything unused here. */
function workingStorage(initial) {
  const store = Object.assign(Object.create(null), initial);
  return {
    getItem: (key) => (key in store ? store[key] : null),
    setItem: (key, value) => { store[key] = String(value); },
    read: (key) => store[key],
    /* Not part of the localStorage surface — the tests' own window on what was
       actually persisted, so "nothing was written" can be asserted without
       counting the helper's own methods. */
    keys: () => Object.keys(store)
  };
}

/**
 * A page with a localStorage of our choosing and assets.js run into it.
 *
 * @param {Object} [storage] - anything with getItem/setItem; omit for a working one
 * @param {string} [siteKey] - the <meta name="site-key">; omit for food
 * @returns {Object} { HTF, storage }
 */
function pageWith(storage, siteKey) {
  const store = storage || workingStorage();
  const page = makePage({
    'base-url': '/',
    'site-key': siteKey === undefined ? 'food' : siteKey
  });
  page.localStorage = store;
  load(['assets/js/assets.js'], page);
  return { HTF: page.HTF, storage: store };
}

// --- the ordinary case --------------------------------------------------------

test('an empty store has nothing in it', () => {
  const { HTF } = pageWith();
  assert.deepStrictEqual(plain(HTF.shortlist.list()), []);
  assert.strictEqual(HTF.shortlist.count(), 0);
  assert.strictEqual(HTF.shortlist.has('/food/recipes/dal/'), false);
});

test('toggle adds, and reports the state it ended in', () => {
  const { HTF } = pageWith();
  assert.strictEqual(HTF.shortlist.toggle('/food/recipes/dal/'), true);
  assert.strictEqual(HTF.shortlist.has('/food/recipes/dal/'), true);
  assert.strictEqual(HTF.shortlist.count(), 1);
});

test('toggle removes what it added, and says so', () => {
  const { HTF } = pageWith();
  HTF.shortlist.toggle('/food/recipes/dal/');
  assert.strictEqual(HTF.shortlist.toggle('/food/recipes/dal/'), false);
  assert.strictEqual(HTF.shortlist.has('/food/recipes/dal/'), false);
  assert.strictEqual(HTF.shortlist.count(), 0);
});

test('entries come back oldest first — the order they were marked in', () => {
  const { HTF } = pageWith();
  ['/a/', '/b/', '/c/'].forEach((u) => HTF.shortlist.toggle(u));
  assert.deepStrictEqual(plain(HTF.shortlist.list()), ['/a/', '/b/', '/c/']);
});

test('list() hands back a copy — a caller sorting it cannot reorder the store', () => {
  const { HTF } = pageWith();
  ['/a/', '/b/'].forEach((u) => HTF.shortlist.toggle(u));
  HTF.shortlist.list().reverse();
  assert.deepStrictEqual(plain(HTF.shortlist.list()), ['/a/', '/b/']);
});

test('an empty key is refused rather than stored', () => {
  const { HTF } = pageWith();
  assert.strictEqual(HTF.shortlist.toggle(''), false);
  assert.strictEqual(HTF.shortlist.count(), 0);
});

test('clear() empties it', () => {
  const { HTF, storage } = pageWith();
  HTF.shortlist.toggle('/a/');
  HTF.shortlist.clear();
  assert.strictEqual(HTF.shortlist.count(), 0);
  assert.strictEqual(storage.read(FOOD_KEY), '[]');
});

// --- persistence --------------------------------------------------------------

test('a toggle is written to localStorage under this site\'s own key', () => {
  const { HTF, storage } = pageWith();
  HTF.shortlist.toggle('/food/recipes/dal/');
  assert.deepStrictEqual(JSON.parse(storage.read(FOOD_KEY)), ['/food/recipes/dal/']);
});

test('what a previous visit wrote is read back', () => {
  const stored = workingStorage({ [FOOD_KEY]: JSON.stringify(['/food/recipes/dal/']) });
  const { HTF } = pageWith(stored);
  assert.strictEqual(HTF.shortlist.has('/food/recipes/dal/'), true);
});

test('the two sites keep two lists, from one localStorage', () => {
  // Both sites are served from one origin, so this is the same store;
  // HTF.site is what separates the two lists (#546).
  const shared = workingStorage();
  const food = pageWith(shared, 'food');
  const cocktails = pageWith(shared, 'cocktails');

  food.HTF.shortlist.toggle('/food/recipes/dal/');
  cocktails.HTF.shortlist.toggle('/cocktails/drinks/negroni/');

  assert.deepStrictEqual(plain(food.HTF.shortlist.list()), ['/food/recipes/dal/']);
  assert.deepStrictEqual(plain(cocktails.HTF.shortlist.list()), ['/cocktails/drinks/negroni/']);
  assert.ok(shared.read('htf-shortlist-food-v1'));
  assert.ok(shared.read('htf-shortlist-cocktails-v1'));
});

test('a page with no site-key has no store at all, and does not throw', () => {
  // The root landing page. A shared key would be a third list appearing under
  // a name neither site reads.
  const shared = workingStorage();
  const { HTF } = pageWith(shared, '');
  assert.strictEqual(HTF.shortlist.toggle('/anything/'), true);
  assert.strictEqual(HTF.shortlist.count(), 1, 'the click still responds');
  assert.deepStrictEqual(shared.keys(), [], 'but nothing is persisted');
});

// --- stored state is untrusted input ------------------------------------------

test('a stored value that is not an array reads as an empty shortlist', () => {
  [JSON.stringify({ dal: true }), JSON.stringify('dal'), 'not json at all', '7']
    .forEach((raw) => {
      const { HTF } = pageWith(workingStorage({ [FOOD_KEY]: raw }));
      assert.deepStrictEqual(plain(HTF.shortlist.list()), [], `for stored ${raw}`);
    });
});

test('non-string entries are dropped, and the rest of the list survives', () => {
  const raw = JSON.stringify(['/a/', 42, null, { url: '/b/' }, '/c/']);
  const { HTF } = pageWith(workingStorage({ [FOOD_KEY]: raw }));
  assert.deepStrictEqual(plain(HTF.shortlist.list()), ['/a/', '/c/']);
});

test('a duplicated entry is read once, so toggling it off actually removes it', () => {
  // A hand-edited or older record could carry the same url twice; splice()
  // removes one occurrence, so a second copy would leave it apparently
  // shortlisted after being switched off.
  const raw = JSON.stringify(['/a/', '/a/']);
  const { HTF } = pageWith(workingStorage({ [FOOD_KEY]: raw }));
  assert.deepStrictEqual(plain(HTF.shortlist.list()), ['/a/']);
  HTF.shortlist.toggle('/a/');
  assert.strictEqual(HTF.shortlist.has('/a/'), false);
});

// --- how many of each ----------------------------------------------------------
// #546, per-drink quantities. A second key beside the list: the shortlist says
// WHAT, this says HOW MANY.

test('everything is one glass until it is told otherwise', () => {
  const { HTF } = pageWith();
  assert.strictEqual(HTF.shortlist.glasses('/a/'), 1);
});

test('a count is stored and read back', () => {
  const { HTF, storage } = pageWith();
  assert.strictEqual(HTF.shortlist.setGlasses('/a/', 6), 6);
  assert.strictEqual(HTF.shortlist.glasses('/a/'), 6);
  assert.deepStrictEqual(JSON.parse(storage.read('htf-shortlist-glasses-food-v1')), { '/a/': 6 });
});

test('setting a count back to one REMOVES it, rather than storing the default', () => {
  // What keeps the map sparse, and what makes a dropped drink self-healing:
  // there is never a stored 1 for anything to have to tidy up.
  const { HTF, storage } = pageWith();
  HTF.shortlist.setGlasses('/a/', 6);
  assert.strictEqual(HTF.shortlist.setGlasses('/a/', 1), 1);
  assert.deepStrictEqual(JSON.parse(storage.read('htf-shortlist-glasses-food-v1')), {});
});

test('a nonsense count is one glass, not a stored nonsense', () => {
  const { HTF } = pageWith();
  [0, -3, 'six', NaN, null].forEach((n) => {
    assert.strictEqual(HTF.shortlist.setGlasses('/a/', n), 1, `for ${JSON.stringify(n)}`);
    assert.strictEqual(HTF.shortlist.glasses('/a/'), 1);
  });
});

test('a fractional count is floored — half a daiquiri is not a plan', () => {
  const { HTF } = pageWith();
  assert.strictEqual(HTF.shortlist.setGlasses('/a/', 3.7), 3);
});

test('a stored counts map that is the wrong shape reads as all-ones', () => {
  const KEY = 'htf-shortlist-glasses-food-v1';
  [JSON.stringify(['/a/', 6]), JSON.stringify('six'), 'not json', JSON.stringify({ '/a/': 'six' })]
    .forEach((raw) => {
      const { HTF } = pageWith(workingStorage({ [KEY]: raw }));
      assert.strictEqual(HTF.shortlist.glasses('/a/'), 1, `for stored ${raw}`);
    });
});

test('clear() empties the counts as well as the marks', () => {
  const { HTF } = pageWith();
  HTF.shortlist.toggle('/a/');
  HTF.shortlist.setGlasses('/a/', 6);
  HTF.shortlist.clear();
  assert.strictEqual(HTF.shortlist.count(), 0);
  assert.strictEqual(HTF.shortlist.glasses('/a/'), 1);
});

test('the two sites keep separate counts, like separate lists', () => {
  const shared = workingStorage();
  const food = pageWith(shared, 'food');
  const cocktails = pageWith(shared, 'cocktails');
  food.HTF.shortlist.setGlasses('/x/', 4);
  assert.strictEqual(cocktails.HTF.shortlist.glasses('/x/'), 1);
});

// --- storage that fights back --------------------------------------------------
// A failed write must still leave the click working for this visit: somebody
// just pressed this control.

test('setItem throwing (private mode) does not lose the click', () => {
  const { HTF } = pageWith({
    getItem: () => null,
    setItem: () => { throw new Error('QuotaExceededError'); }
  });
  assert.strictEqual(HTF.shortlist.toggle('/a/'), true);
  assert.strictEqual(HTF.shortlist.has('/a/'), true);
  assert.strictEqual(HTF.shortlist.count(), 1);
});

test('getItem throwing (site data blocked) reads as empty and still works', () => {
  const { HTF } = pageWith({
    getItem: () => { throw new Error('SecurityError'); },
    setItem: () => {}
  });
  assert.deepStrictEqual(plain(HTF.shortlist.list()), []);
  assert.strictEqual(HTF.shortlist.toggle('/a/'), true);
  assert.strictEqual(HTF.shortlist.has('/a/'), true);
});

test('no localStorage in the context at all is survivable', () => {
  // A bare `localStorage` reference is a ReferenceError, not undefined.
  const page = makePage({ 'base-url': '/', 'site-key': 'food' });
  load(['assets/js/assets.js'], page);
  assert.doesNotThrow(() => page.HTF.shortlist.list());
  assert.strictEqual(page.HTF.shortlist.toggle('/a/'), true);
  assert.strictEqual(page.HTF.shortlist.has('/a/'), true);
});

// --- portions — GitHub issue #801 ---------------------------------------------
// Not `glasses` under another name: a missing glasses entry is one glass, but
// a missing portions entry is "however many this recipe makes", which only the
// build knows. So `null` is the unset answer and `1` is a real, storable one.

test('an unset recipe answers null, not a number', () => {
  const { HTF } = pageWith();
  assert.strictEqual(HTF.shortlist.portions('/food/recipes/dal/'), null);
});

test('one portion is a real answer and survives a reload', () => {
  // Unlike setGlasses, which deletes a 1 as its default.
  const { HTF, storage } = pageWith();
  assert.strictEqual(HTF.shortlist.setPortions('/a/', 1), 1);
  HTF.shortlist._forget();
  assert.strictEqual(HTF.shortlist.portions('/a/'), 1);
  assert.strictEqual(
    JSON.parse(storage.getItem('htf-shortlist-portions-food-v2'))['/a/'], 1);
});

test('anything below one forgets the entry rather than storing it', () => {
  const { HTF } = pageWith();
  HTF.shortlist.setPortions('/a/', 6);
  [0, -3, 'nonsense', null, undefined].forEach((value) => {
    HTF.shortlist.setPortions('/a/', 6);
    assert.strictEqual(HTF.shortlist.setPortions('/a/', value), null, String(value));
    assert.strictEqual(HTF.shortlist.portions('/a/'), null, String(value));
  });
});

test('a stored value that is not a positive number is not read back', () => {
  const { HTF } = pageWith(workingStorage({
    'htf-shortlist-portions-food-v2':
      JSON.stringify({ '/a/': 0, '/b/': -1, '/c/': 'six', '/d/': null, '/e/': 4 })
  }));
  ['/a/', '/b/', '/c/', '/d/'].forEach((url) => {
    assert.strictEqual(HTF.shortlist.portions(url), null, url);
  });
  assert.strictEqual(HTF.shortlist.portions('/e/'), 4);
});

test('a portions record that is not an object reads as empty', () => {
  [JSON.stringify([1, 2]), 'null', 'not json at all'].forEach((raw) => {
    const { HTF } = pageWith(workingStorage({
      'htf-shortlist-portions-food-v2': raw
    }));
    assert.strictEqual(HTF.shortlist.portions('/a/'), null, raw);
  });
});

test('clear() empties the portions as well as the counts and the marks', () => {
  const { HTF } = pageWith();
  HTF.shortlist.toggle('/a/');
  HTF.shortlist.setPortions('/a/', 6);
  HTF.shortlist.clear();
  assert.strictEqual(HTF.shortlist.portions('/a/'), null);
  assert.strictEqual(HTF.shortlist.count(), 0);
});

test('portions and glasses are separate maps, not one under two names', () => {
  const { HTF } = pageWith();
  HTF.shortlist.setPortions('/a/', 6);
  assert.strictEqual(HTF.shortlist.glasses('/a/'), 1);
  HTF.shortlist.setGlasses('/a/', 3);
  assert.strictEqual(HTF.shortlist.portions('/a/'), 6);
});

test('the two sites keep separate portions', () => {
  const shared = workingStorage();
  const food = pageWith(shared, 'food');
  const cocktails = pageWith(shared, 'cocktails');
  food.HTF.shortlist.setPortions('/x/', 8);
  assert.strictEqual(cocktails.HTF.shortlist.portions('/x/'), null);
});

test('a failed portions write does not lose the number just typed', () => {
  const { HTF } = pageWith({
    getItem: () => null,
    setItem: () => { throw new Error('QuotaExceededError'); }
  });
  assert.strictEqual(HTF.shortlist.setPortions('/a/', 6), 6);
  assert.strictEqual(HTF.shortlist.portions('/a/'), 6);
});

// --- how many BATCHES -- #1297 --------------------------------------------------
// On the shopping list a `makes:` recipe's box counts batches. A map of its
// own, because a stored 6 cannot say whether it meant people or batches.

test('#1297: an unset recipe has no batch count, which the caller reads as one', () => {
  const { HTF } = pageWith();
  assert.strictEqual(HTF.shortlist.batches('/food/recipes/cookies/'), null);
});

test('#1297: a batch count is stored under its own key and survives a reload', () => {
  const { HTF, storage } = pageWith();
  assert.strictEqual(HTF.shortlist.setBatches('/a/', 3), 3);
  HTF.shortlist._forget();
  assert.strictEqual(HTF.shortlist.batches('/a/'), 3);
  assert.strictEqual(
    JSON.parse(storage.getItem('htf-shortlist-batches-food-v1'))['/a/'], 3);
});

test('#1297: half a batch is storable, and nothing else below one is', () => {
  const { HTF } = pageWith();
  assert.strictEqual(HTF.shortlist.setBatches('/a/', 0.5), 0.5);
  assert.strictEqual(HTF.shortlist.setBatches('/a/', 0.2), 0.5);
  // No batch and a half: the nearest whole one.
  assert.strictEqual(HTF.shortlist.setBatches('/a/', 1.2), 1);
  assert.strictEqual(HTF.shortlist.setBatches('/a/', 2.6), 3);
});

test('#1297: nothing, zero or nonsense forgets the entry', () => {
  const { HTF } = pageWith();
  [0, -3, 'nonsense', null, undefined, ''].forEach((value) => {
    HTF.shortlist.setBatches('/a/', 4);
    assert.strictEqual(HTF.shortlist.setBatches('/a/', value), null, String(value));
    assert.strictEqual(HTF.shortlist.batches('/a/'), null, String(value));
  });
});

test('#1297: batches and portions are separate maps', () => {
  const { HTF } = pageWith();
  HTF.shortlist.setPortions('/a/', 6);
  assert.strictEqual(HTF.shortlist.batches('/a/'), null,
    'six PEOPLE was read back as six batches');
  HTF.shortlist.setBatches('/a/', 2);
  assert.strictEqual(HTF.shortlist.portions('/a/'), 6);
});

test('#1297: clear() empties the batches too', () => {
  const { HTF } = pageWith();
  HTF.shortlist.setBatches('/a/', 2);
  HTF.shortlist.clear();
  HTF.shortlist._forget();
  assert.strictEqual(HTF.shortlist.batches('/a/'), null);
});

// --- ticking the shopping list off (#1457) ------------------------------------
// The lists are rebuilt whole on every number change, so a tick lives here
// and nowhere else. It must survive a reload (a phone drops the tab mid-shop)
// and go only when "untick all" says so.

const TICKED_KEY = 'htf-shortlist-ticked-food-v1';

test('#1457: nothing is ticked until something is', () => {
  const { HTF } = pageWith();
  assert.strictEqual(HTF.shortlist.ticked('onion'), false);
});

test('#1457: a tick is stored under its own key and survives a reload', () => {
  const storage = workingStorage();
  pageWith(storage).HTF.shortlist.setTicked('onion', true);
  assert.deepStrictEqual(JSON.parse(storage.read(TICKED_KEY)), ['onion']);
  assert.strictEqual(pageWith(storage).HTF.shortlist.ticked('onion'), true);
});

test('#1457: unticking one row leaves the others ticked', () => {
  const { HTF } = pageWith();
  HTF.shortlist.setTicked('onion', true);
  HTF.shortlist.setTicked('plain flour', true);
  assert.strictEqual(HTF.shortlist.setTicked('onion', false), false);
  assert.strictEqual(HTF.shortlist.ticked('onion'), false);
  assert.strictEqual(HTF.shortlist.ticked('plain flour'), true);
});

test('#1457: ticking twice stores the row once, so one untick clears it', () => {
  const { HTF, storage } = pageWith();
  HTF.shortlist.setTicked('onion', true);
  HTF.shortlist.setTicked('onion', true);
  HTF.shortlist.setTicked('onion', false);
  assert.deepStrictEqual(JSON.parse(storage.read(TICKED_KEY)), []);
});

test('#1457: untickAll() clears every tick, and leaves the shortlist alone', () => {
  const { HTF, storage } = pageWith();
  HTF.shortlist.toggle('/a/');
  HTF.shortlist.setTicked('onion', true);
  HTF.shortlist.setTicked('lime', true);
  HTF.shortlist.untickAll();
  HTF.shortlist._forget();
  assert.strictEqual(HTF.shortlist.ticked('onion'), false);
  assert.strictEqual(HTF.shortlist.ticked('lime'), false);
  assert.deepStrictEqual(JSON.parse(storage.read(TICKED_KEY)), []);
  assert.strictEqual(HTF.shortlist.has('/a/'), true);
});

test('#1457: clear() empties the ticks too', () => {
  const { HTF } = pageWith();
  HTF.shortlist.setTicked('onion', true);
  HTF.shortlist.clear();
  HTF.shortlist._forget();
  assert.strictEqual(HTF.shortlist.ticked('onion'), false);
});

test('#1457: a ticks record of the wrong shape reads as nothing ticked', () => {
  ['{"onion": true}', '"onion"', 'not json', JSON.stringify([3, null, 'lime'])]
    .forEach((raw) => {
      const { HTF } = pageWith(workingStorage({ [TICKED_KEY]: raw }));
      assert.strictEqual(HTF.shortlist.ticked('onion'), false, raw);
    });
  // Inside a list, the strings survive what is dropped around them.
  const { HTF } = pageWith(workingStorage({ [TICKED_KEY]: JSON.stringify([3, null, 'lime']) }));
  assert.strictEqual(HTF.shortlist.ticked('lime'), true);
});

test('#1457: an empty row key is refused rather than stored', () => {
  const { HTF, storage } = pageWith();
  assert.strictEqual(HTF.shortlist.setTicked('', true), false);
  assert.strictEqual(storage.read(TICKED_KEY), undefined);
});

test('#1457: the two sites keep separate ticks', () => {
  const shared = workingStorage();
  pageWith(shared, 'food').HTF.shortlist.setTicked('lime', true);
  assert.strictEqual(pageWith(shared, 'cocktails').HTF.shortlist.ticked('lime'), false);
});

test('#1457: a failed write does not lose the tick just made', () => {
  const { HTF } = pageWith({
    getItem: () => null,
    setItem: () => { throw new Error('QuotaExceededError'); }
  });
  HTF.shortlist.setTicked('onion', true);
  assert.strictEqual(HTF.shortlist.ticked('onion'), true);
});

// --- the tick box and its wiring (#1457) --------------------------------------
// HTF.shoppingTicks, which both index scripts use. The list here is a
// hand-made stand-in: enough element for the delegated listener to walk.

function fakeRow(key, checked) {
  const row = {
    classes: new Set(),
    classList: {
      toggle: (c, on) => { if (on) row.classes.add(c); else row.classes.delete(c); },
      remove: (c) => row.classes.delete(c),
      contains: (c) => row.classes.has(c)
    }
  };
  const box = {
    checked: !!checked,
    dataset: { key },
    classList: { contains: (c) => c === 'shopping-list-tick' },
    closest: (sel) => (sel === 'li' ? row : null),
    focus() { box.focused = true; }
  };
  return { row, box };
}

function fakeList(rows) {
  const listeners = {};
  return {
    addEventListener: (type, fn) => { listeners[type] = fn; },
    fire: (type, target) => listeners[type]({ target }),
    querySelector: (sel) => {
      const boxes = rows.map((r) => r.box);
      if (sel === '.shopping-list-tick:checked') return boxes.find((b) => b.checked) || null;
      return boxes[0] || null;
    },
    querySelectorAll: () => rows.map((r) => r.box)
  };
}

function fakeButton() {
  const listeners = {};
  return {
    hidden: true,
    addEventListener: (type, fn) => { listeners[type] = fn; },
    click: () => listeners.click()
  };
}

test('#1457: box() draws a checkbox carrying the row key, checked when ticked', () => {
  const { HTF } = pageWith();
  assert.strictEqual(HTF.shoppingTicks.box('olive oil'),
    '<input type="checkbox" class="shopping-list-tick" data-key="olive oil">');
  HTF.shortlist.setTicked('olive oil', true);
  assert.strictEqual(HTF.shoppingTicks.box('olive oil'),
    '<input type="checkbox" class="shopping-list-tick" data-key="olive oil" checked>');
  assert.strictEqual(HTF.shoppingTicks.rowClass('olive oil'), ' is-ticked');
  assert.strictEqual(HTF.shoppingTicks.rowClass('lime'), '');
});

test('#1457: box() escapes the key, which is a name from a recipe', () => {
  const { HTF } = pageWith();
  assert.ok(HTF.shoppingTicks.box('"><b>').includes('data-key="&quot;&gt;&lt;b&gt;"'));
});

test('#1457: ticking a box stores it, marks the row and shows "untick all"', () => {
  const { HTF } = pageWith();
  const onion = fakeRow('onion');
  const lime = fakeRow('lime');
  const list = fakeList([onion, lime]);
  const button = fakeButton();
  const refresh = HTF.shoppingTicks.wire(list, button);
  refresh();
  assert.strictEqual(button.hidden, true, 'nothing ticked, no button');

  onion.box.checked = true;
  list.fire('change', onion.box);
  assert.strictEqual(HTF.shortlist.ticked('onion'), true);
  assert.ok(onion.row.classes.has('is-ticked'));
  assert.strictEqual(button.hidden, false);

  onion.box.checked = false;
  list.fire('change', onion.box);
  assert.strictEqual(HTF.shortlist.ticked('onion'), false);
  assert.ok(!onion.row.classes.has('is-ticked'));
  assert.strictEqual(button.hidden, true);
});

test('#1457: "untick all" clears the store and every box, and keeps focus in the list', () => {
  const { HTF } = pageWith();
  const onion = fakeRow('onion', true);
  const lime = fakeRow('lime', true);
  HTF.shortlist.setTicked('onion', true);
  HTF.shortlist.setTicked('lime', true);
  // A tick from an earlier shop, on a row not shown today, goes too.
  HTF.shortlist.setTicked('saffron', true);
  const list = fakeList([onion, lime]);
  const button = fakeButton();
  HTF.shoppingTicks.wire(list, button)();
  assert.strictEqual(button.hidden, false);

  button.click();
  assert.strictEqual(onion.box.checked, false);
  assert.strictEqual(lime.box.checked, false);
  ['onion', 'lime', 'saffron'].forEach((k) => assert.strictEqual(HTF.shortlist.ticked(k), false, k));
  assert.strictEqual(button.hidden, true);
  assert.strictEqual(onion.box.focused, true, 'focus goes to the first box, not <body>');
});

test('#1457: a change from anything but a tick box is ignored', () => {
  const { HTF } = pageWith();
  const list = fakeList([]);
  HTF.shoppingTicks.wire(list, null);
  list.fire('change', { classList: { contains: () => false }, dataset: { key: 'x' }, checked: true });
  assert.strictEqual(HTF.shortlist.ticked('x'), false);
});

// --- the ceiling --------------------------------------------------------------
// A box's `max` is not enforced on typing; uncapped, 1e9 portions printed
// "6.2e+28 kg mussels" and came back after a reload.

test('no count goes past 99, however it is typed', () => {
  const { HTF } = pageWith();
  [100, 1e9, '123456789012345678901234567890', 1e300].forEach((value) => {
    assert.strictEqual(HTF.shortlist.setPortions('/a/', value), 99, String(value));
    assert.strictEqual(HTF.shortlist.setBatches('/a/', value), 99, String(value));
    assert.strictEqual(HTF.shortlist.setGlasses('/a/', value), 99, String(value));
  });
  assert.strictEqual(HTF.shortlist.setPortions('/a/', 99), 99);
  assert.strictEqual(HTF.shortlist.setGlasses('/a/', 98), 98);
});

test('a huge count saved before the ceiling comes back as 99', () => {
  const { HTF } = pageWith(workingStorage({
    'htf-shortlist-portions-food-v2': JSON.stringify({ '/a/': 1.2345678901234568e+29 }),
    'htf-shortlist-batches-food-v1': JSON.stringify({ '/a/': 5000 }),
    'htf-shortlist-glasses-food-v1': JSON.stringify({ '/a/': 1e12 })
  }));
  assert.strictEqual(HTF.shortlist.portions('/a/'), 99);
  assert.strictEqual(HTF.shortlist.batches('/a/'), 99);
  assert.strictEqual(HTF.shortlist.glasses('/a/'), 99);
});
