// The food index runs to the end, and its shopping list fills in (#801).
//
//   node --test tests/js/*.test.js
//
// All of filters.js is one `DOMContentLoaded` handler, so a throw anywhere in
// it leaves `.recipe-list` at `visibility: hidden`: a blank index, with the
// only evidence in the console. The canary is that list becoming visible, at
// the end of the handler, so one assertion covers every line above it.
//
// The scripts are the real files, in the order food/index.html loads them,
// run with `vm.runInContext` and not require(): in a browser they are not
// modules. The DOM, the storage and the window are stand-ins.
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const { createDocument, createStorage } = require('./dom-stub.js');

const ROOT = path.join(__dirname, '..', '..');
const JS_DIR = path.join(ROOT, 'assets', 'js');

// assets.js comes from _layouts/default.html; the rest are food/index.html's
// own tags, in its order. The test at the foot of this file pins this list to
// the template; test_the_food_shopping_scripts_load_in_dependency_order in
// tests/test_site_config.py pins the template's order.
const SCRIPTS = [
  'assets.js',
  'ingredient-search.js',
  'list-view.js',
  'filter-state.js',
  'shopping-list.js',
  'food-shopping-list.js',
  'filters.js',
  // Wires itself on DOMContentLoaded, after filters.js's handler, and returns
  // at once here: this sandbox has no IntersectionObserver, which is the path
  // a browser without the API takes.
  'results-bar.js',
  // #849. Nobody's dependency; listed because the test at the foot of this
  // file asserts this array is the template's script list.
  'shortlist-export.js'
];

/* Hand-built, and small enough to read in one screen. `b` keeps Helen's words
   after its number, as a yield line does. */
const RECIPES = {
  '/food/recipes/a/': {
    p: 4, y: '4', k: 'serves',
    i: [{ a: '200 g', n: 'plain flour', s: 'cupboard' },
      { a: '2', n: 'onions', s: 'produce' },
      { a: '', n: 'olive oil', s: 'cupboard' }]
  },
  '/food/recipes/b/': {
    p: 6, y: '6, depending on appetite', k: 'serves',
    i: [{ a: '300 g', n: 'plain flour', s: 'cupboard' },
      { a: '1', n: 'onion', s: 'produce' }]
  },
  /* The two `makes:` recipes, which count batches (#1297). `w` is
     page.whole_recipes, `h` page.half_recipe, `m` page.made: the figures the
     recipe page's own scaler reads (#1286). The gelato makes a measure and may
     be halved; the cookies make a count and may not. Neither has `p`: a
     `makes:` recipe counts people nowhere. */
  '/food/recipes/gelato/': {
    p: null, y: 'About 750 ml', k: 'makes', w: true, h: true,
    m: { kind: 'measure', base: 750, unit: 'ml', box: '750' },
    i: [{ a: '125 ml', n: 'whipping cream', s: 'dairy' },
      { a: '500 ml', n: 'whole milk', s: 'dairy' }]
  },
  '/food/recipes/cookies/': {
    p: null, y: '18 cookies', k: 'makes', w: true, h: false,
    m: { kind: 'count', base: 18, stem: 'cookies', rest: '', box: '18' },
    i: [{ a: '100 g', n: 'peanut butter', s: 'cupboard' },
      { a: '1', n: 'egg', s: 'dairy' }]
  }
};

const AISLES = [
  { key: 'produce', label: 'produce' },
  { key: 'cupboard', label: 'store cupboard' },
  { key: 'other', label: 'other' }
];

const TITLES = {
  '/food/recipes/a/': 'Aubergine thing',
  '/food/recipes/b/': 'Beetroot cake',
  '/food/recipes/gelato/': 'Blackberry gelato',
  '/food/recipes/cookies/': 'Peanut Butter Cookies',
  // Only in the list when a test passes SINGLE_THINGS as `options.recipes`.
  '/food/recipes/cake/': 'Beetroot Chocolate Cake',
  '/food/recipes/sauce/': 'Peanut Sauce',
  '/food/recipes/pies/': 'Mince Pies'
};

/* `makes:` recipes whose yield is one named thing, as _plugins/food_yield.rb
   reads "one 8-inch cake", "1 jar" and "1 dozen mince pies". None is offered a
   half: a yield has to halve to at least one of itself. Passed as
   `options.recipes`, so the standing fixture is unchanged. */
const SINGLE_THINGS = {
  '/food/recipes/cake/': {
    p: null, y: 'one 8-inch cake', k: 'makes', w: true, h: false,
    m: { kind: 'count', base: 1, stem: '8-inch cake', rest: '', box: '1',
      singular: true, times: true, invariable: false },
    i: [{ a: '250 g', n: 'plain flour', s: 'cupboard' }]
  },
  '/food/recipes/sauce/': {
    p: null, y: '1 jar', k: 'makes', w: true, h: false,
    m: { kind: 'count', base: 1, stem: 'jar', rest: '', box: '1',
      singular: true, times: false, invariable: false },
    i: [{ a: '200 g', n: 'peanuts', s: 'cupboard' }]
  },
  '/food/recipes/pies/': {
    p: null, y: '1 dozen mince pies', k: 'makes', w: true, h: false,
    m: { kind: 'count', base: 1, stem: 'dozen mince pies', rest: '', box: '1',
      singular: true, times: false, invariable: true },
    i: [{ a: '300 g', n: 'mincemeat', s: 'cupboard' }]
  }
};

/* `data-ingredients` -- main_ingredients, comma-joined as food/index.html
   joins them. What the HAS TO HAVE picker's vocabulary is built from, and so
   what `?ing=` (#1050) has to find. */
const MAIN_INGREDIENTS = {
  '/food/recipes/a/': 'aubergines,olive oil',
  '/food/recipes/b/': 'beetroot,plain flour',
  '/food/recipes/gelato/': 'blackberries,whipping cream',
  '/food/recipes/cookies/': 'peanut butter'
};

/**
 * A food index with everything the scripts read, and nothing else.
 *
 * @param {Object} [options]
 * @param {Object} [options.recipes] - replaces the #recipe-ingredients blob,
 *        for the tests about what happens when the build hands over something
 *        unexpected.
 */
function boot(options) {
  const recipes = (options && options.recipes) || RECIPES;
  const doc = createDocument();
  const el = (tag, cls, attrs) => {
    const node = doc.createElement(tag);
    if (cls) node.setAttribute('class', cls);
    Object.entries(attrs || {}).forEach(([k, v]) => node.setAttribute(k, v));
    return node;
  };
  const json = (id, value) => {
    const node = el('script', '', { type: 'application/json', id });
    node.textContent = JSON.stringify(value);
    doc.body.appendChild(node);
  };

  doc.body.appendChild(el('meta', '', { name: 'base-url', content: '' }));
  doc.body.appendChild(el('meta', '', { name: 'site-key', content: 'food' }));

  /* The three JSON blocks the page emits. Without one, its script warns and
     falls back to nothing, which would test a different program from the one
     that ships. */
  json('ingredient-vocabulary', { search: { family_button_min_chars: 3 } });
  json('recipe-aisles', AISLES);
  json('recipe-ingredients', recipes);

  // The name box, so `?q=` (#1024) has somewhere to land; the input handler
  // is not exercised here, only the query's arrival.
  const controls = el('div', 'controls');
  controls.appendChild(el('input', '', { id: 'name-search-box', type: 'text' }));
  // HAS TO HAVE's box and pool, so `?ing=` (#1050) has somewhere to land.
  controls.appendChild(el('input', '', { id: 'ingredient-search-box', type: 'text' }));
  controls.appendChild(el('div', 'category-buttons search-results', { id: 'ingredient-results-pool' }));
  doc.body.appendChild(controls);

  // `id="results"` (#1050) and `id="filter-star"` (#1059): the two kinds of
  // fragment a link on this site can end in, the count line and a filter
  // section. One section is enough to prove the startup block scrolls to
  // whatever `location.hash` names.
  const results = el('div', 'results-heading', { id: 'results' });
  // The count's real shape: the number and the word in their own spans inside
  // `#recipe-count`. filters.js paints the two spans and falls back to the
  // outer element's text when they are absent.
  const countOuter = el('span', 'category-label-text', { id: 'recipe-count' });
  countOuter.appendChild(el('span', 'results-count-number', { id: 'recipe-count-n' }));
  countOuter.appendChild(doc.createTextNode(' '));
  countOuter.appendChild(el('span', '', { id: 'recipe-count-word' }));
  results.appendChild(countOuter);
  doc.body.appendChild(results);
  const starSection = el('div', 'category category--star', { id: 'filter-star' });
  doc.body.appendChild(starSection);

  const list = el('ul', 'recipe-list');
  Object.keys(recipes).forEach((url) => {
    const li = el('li', '', {
      'data-url': url, 'data-tags': '', 'data-star': '',
      'data-ingredients': MAIN_INGREDIENTS[url] || '', 'data-all-ingredients': '|'
    });
    const link = el('a', 'recipe-title-link', { href: url });
    link.textContent = TITLES[url];
    li.appendChild(link);
    li.appendChild(el('button', 'btn-shortlist', { 'data-shortlist-key': url }));
    list.appendChild(li);
  });
  doc.body.appendChild(list);

  const countRow = el('div', 'results-count-row');
  countRow.appendChild(el('button', 'btn-shortlist-only', { id: 'shortlist-only' }));
  // #1093's note over a shared list, with the attributes filters.js reaches for.
  const shared = el('p', 'shared-shortlist', { 'data-shared-shortlist': '' });
  shared.appendChild(el('span', '', { 'data-shared-shortlist-text': '' }));
  shared.appendChild(el('button', 'btn-shared-keep', { 'data-shared-shortlist-keep': '' }));
  countRow.appendChild(shared);
  doc.body.appendChild(countRow);

  // The stub has `dispatch(type)`; the page calls the DOM's dispatchEvent with
  // a CustomEvent, which "keep these" (#1093) does to repaint everything.
  doc.dispatchEvent = (ev) => doc.dispatch(ev.type, ev);

  const panel = el('section', 'shopping-list', {
    id: 'shopping-list', 'data-whole-measures': 'handful,pinch',
    'data-count-nouns': 'onion,lemon', 'data-container-nouns': 'jar,tin,batch'
  });
  const head = el('div', 'shopping-list-head');
  head.appendChild(el('input', '', { id: 'shopping-list-setall', type: 'number' }));
  panel.appendChild(head);
  panel.appendChild(el('ul', 'shopping-list-recipes'));
  panel.appendChild(el('p', 'shopping-list-note'));
  panel.appendChild(el('div', 'shopping-list-aisles'));
  panel.appendChild(el('p', 'shopping-list-empty'));
  doc.body.appendChild(panel);

  const win = {
    document: doc,
    localStorage: createStorage(),
    // HTF.indexMemory in assets.js (#387, #1057) reads and writes
    // sessionStorage and treats a missing one as a fresh load, so without this
    // a back navigation is untestable here and nothing fails.
    sessionStorage: createStorage(),
    console: { warn() {}, error() {}, log() {} },
    setTimeout, clearTimeout,
    location: {
      search: (options && options.search) || '',
      pathname: '/food/',
      hash: (options && options.hash) || ''
    },
    history: { replaceState() {}, pushState() {} },
    // `options.backForward` (#387, #1057): FilterState.arrivedByGoingBack
    // reads this entry, so a test can make a load a back navigation.
    performance: {
      getEntriesByType: () => (options && options.backForward
        ? [{ type: 'back_forward' }] : []),
      navigation: { type: 0 }
    },
    matchMedia: () => ({ matches: false, addEventListener() {} }),
    requestAnimationFrame: (fn) => fn(),
    __scrollToCalls: [],
    scrollTo(...args) { this.__scrollToCalls.push(args); },
    CustomEvent: class {
      constructor(type, options) { this.type = type; Object.assign(this, options || {}); }
    },
    addEventListener() {}, removeEventListener() {}, dispatchEvent() {}
  };
  win.window = win;
  win.self = win;
  const context = vm.createContext(win);

  SCRIPTS.forEach((name) => {
    vm.runInContext(fs.readFileSync(path.join(JS_DIR, name), 'utf8'),
      context, { filename: name });
  });

  // `options.beforeStart` runs after the scripts load, so win.HTF exists, and
  // before DOMContentLoaded, so nothing has read location or sessionStorage.
  if (options && typeof options.beforeStart === 'function') {
    options.beforeStart(win, doc);
  }

  // filters.js is one big DOMContentLoaded handler; nothing above has run yet.
  doc.dispatch('DOMContentLoaded');

  return { doc, win, panel, list, results, starSection };
}

const aislesHtml = (panel) => panel.querySelector('.shopping-list-aisles').innerHTML;
const recipesHtml = (panel) => panel.querySelector('.shopping-list-recipes').innerHTML;

/** Turn the shortlisted-only filter on, the way pressing the pill does. */
function showTheList(doc) {
  doc.getElementById('shortlist-only').dispatch('click');
}

// --- the canary ---------------------------------------------------------------

test('the index gets to the end of filters.js', () => {
  const { list } = boot();
  assert.strictEqual(list.style.visibility, 'visible',
    'filters.js threw somewhere before its last few lines, which on the real '
    + 'page is a blank index with nothing in the console anybody will see.');
});

test('it still gets to the end with a shortlist to render', () => {
  // The interesting half: the panel's own code path, run at startup rather
  // than from a click.
  const { win, doc, list } = boot();
  win.HTF.shortlist.toggle('/food/recipes/a/');
  showTheList(doc);
  assert.strictEqual(list.style.visibility, 'visible');
});

test('the count paints its number and its word into separate spans', () => {
  // The digits take `.results-count-number` and the word stays bare; the
  // outer element still reads "N survivors".
  const { doc } = boot();
  assert.strictEqual(doc.getElementById('recipe-count-n').textContent, '4');
  assert.strictEqual(doc.getElementById('recipe-count-word').textContent, 'survivors');
  assert.strictEqual(doc.getElementById('recipe-count').textContent, '4 survivors');
});

test('a page with no shopping list at all still runs', () => {
  // Every other food page shares filters.js's ancestors, and a template that
  // has not been given the panel must not take the index down with it.
  const { doc, list } = boot();
  const panel = doc.getElementById('shopping-list');
  panel.parentNode.removeChild(panel);
  assert.strictEqual(list.style.visibility, 'visible');
});

// --- the panel ----------------------------------------------------------------

test('the panel is hidden until the shortlisted filter is on', () => {
  const { doc, panel } = boot();
  assert.strictEqual(panel.hidden, true);
  showTheList(doc);
  assert.strictEqual(panel.hidden, false);
});

test('an empty shortlist says so rather than showing an empty list', () => {
  const { doc, panel } = boot();
  showTheList(doc);
  assert.strictEqual(panel.querySelector('.shopping-list-empty').hidden, false);
  assert.strictEqual(aislesHtml(panel), '');
});

test('each recipe starts at however many it makes', () => {
  // Not at 1, and not at some global default: an untouched list shops for
  // every recipe exactly as written, which is the answer you want before you
  // have said anything.
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/a/');   // serves 4
  win.HTF.shortlist.toggle('/food/recipes/b/');   // guessed at 6
  showTheList(doc);

  const html = recipesHtml(panel);
  assert.match(html, /value="4" data-url="\/food\/recipes\/a\/"/);
  assert.match(html, /value="6" data-url="\/food\/recipes\/b\/"/);
});

test('the yield is on the control, never printed beside the name', () => {
  // A number at each end of a short line reads as one expression, so the
  // yield is on the input and never beside the name.
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/a/');
  win.HTF.shortlist.toggle('/food/recipes/b/');
  showTheList(doc);

  const html = recipesHtml(panel);
  assert.ok(!html.includes('shopping-list-yield'),
    'the yield is beside the recipe name again -- see the note in '
    + '_sass/food/_shopping-list.scss before putting it back.');
  // Still SAID, so it is there on hover and for a screen reader.
  assert.ok(html.includes('which serves 4'), 'the stated serving size, quoted');
  assert.ok(html.includes('which serves 6, depending on appetite'),
    'her words after the number are quoted with it');
  assert.ok(html.includes('title='), 'the yield is reachable on hover');
});

test('the visible row says what the number counts, then the name', () => {
  // #1297. The number is the input; the yield is still not on the row.
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/a/');
  showTheList(doc);
  const visible = recipesHtml(panel).replace(/<[^>]*>/g, '').trim();
  assert.strictEqual(visible, 'portions of Aubergine thing');
});

test('the totals are grouped by aisle, in the declared order', () => {
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/a/');
  win.HTF.shortlist.toggle('/food/recipes/b/');
  showTheList(doc);

  const html = aislesHtml(panel);
  assert.ok(html.indexOf('produce') < html.indexOf('store cupboard'));
  // 200 g + 300 g, from two recipes, on one line.
  assert.match(html, /<span class="shopping-list-amount">500 g<\/span>/);
  // `onion` and `onions` are the same shopping, and three of them are onions
  // -- the plural reaching build() through `data-count-nouns` (#1297).
  assert.match(html,
    /<span class="shopping-list-amount">3<\/span><span class="shopping-list-name">onions<\/span>/);
});

test('typing into "set all to" rescales every recipe', () => {
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/a/');
  win.HTF.shortlist.toggle('/food/recipes/b/');
  showTheList(doc);

  const setAll = doc.getElementById('shopping-list-setall');
  setAll.value = '8';
  setAll.dispatch('input');

  // a: 200 g x (8/4) = 400. b: 300 g x (8/6) = 400. Total 800.
  assert.match(aislesHtml(panel), /<span class="shopping-list-amount">800 g<\/span>/);
});

test('a number below one is ignored rather than emptying the list', () => {
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/a/');
  showTheList(doc);

  const setAll = doc.getElementById('shopping-list-setall');
  ['', '0', '-4', 'x'].forEach((value) => {
    setAll.value = value;
    setAll.dispatch('input');
    assert.match(aislesHtml(panel),
      /<span class="shopping-list-amount">200 g<\/span>/, `value ${value!== '' ? value : '(empty)'}`);
  });
});

/* The per-recipe inputs are written with innerHTML, which this stub stores as
   a string, so they cannot be found and clicked. The listener is delegated and
   reads `ev.target`, so a stand-in carrying the three things it looks at runs
   the same code. */
const typedInto = (url, value) => ({
  classList: { contains: (cls) => cls === 'shopping-list-portions' },
  dataset: { url: url },
  value: String(value)
});

test('one recipe can be rescaled on its own', () => {
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/a/');
  win.HTF.shortlist.toggle('/food/recipes/b/');
  showTheList(doc);

  panel.querySelector('.shopping-list-recipes')
    .dispatch('input', { target: typedInto('/food/recipes/a/', 8) });

  // a doubles to 400 g, b is untouched at 300 g.
  assert.match(aislesHtml(panel), /<span class="shopping-list-amount">700 g<\/span>/);
  assert.strictEqual(win.HTF.shortlist.portions('/food/recipes/a/'), 8);
  assert.strictEqual(win.HTF.shortlist.portions('/food/recipes/b/'), null,
    'a recipe nobody typed into must stay at however many it makes');
});

test('rescaling one recipe does not replace the input being typed into', () => {
  // The per-recipe list is rebuilt whole on every shortlist change, but not
  // from the input handler: replacing the node under a typing cursor loses
  // the caret and the keystroke.
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/a/');
  showTheList(doc);

  const before = recipesHtml(panel);
  panel.querySelector('.shopping-list-recipes')
    .dispatch('input', { target: typedInto('/food/recipes/a/', 8) });

  assert.strictEqual(recipesHtml(panel), before,
    'the per-recipe controls were re-rendered from the input handler, which on '
    + 'a real page takes the caret out of the box being typed into.');
  // ...while the totals DID move.
  assert.match(aislesHtml(panel), /<span class="shopping-list-amount">400 g<\/span>/);
});

test('an input event from something else is ignored', () => {
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/a/');
  showTheList(doc);

  assert.doesNotThrow(() => {
    panel.querySelector('.shopping-list-recipes').dispatch('input', {
      target: { classList: { contains: () => false }, dataset: {}, value: '9' }
    });
  });
  assert.match(aislesHtml(panel), /<span class="shopping-list-amount">200 g<\/span>/);
});

test('un-shortlisting a recipe takes it out of the totals', () => {
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/a/');
  win.HTF.shortlist.toggle('/food/recipes/b/');
  showTheList(doc);
  assert.match(aislesHtml(panel), /500 g/);

  // What shortlist.js dispatches when a row's own toggle is pressed.
  win.HTF.shortlist.toggle('/food/recipes/b/');
  doc.dispatch('htf:shortlist-change');
  assert.match(aislesHtml(panel), /200 g/);
});

test('an ingredient with no amount is still a line', () => {
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/a/');
  showTheList(doc);
  assert.match(aislesHtml(panel),
    /<span class="shopping-list-name">olive oil<\/span>/);
});

// --- a `makes:` recipe counts BATCHES -- #1297 --------------------------------
// Half a batch only where the build allows it, and no portion figure: a
// portion of 18 cookies has no meaning. `serves:` recipes still count people.

const batchInput = (url, value) => ({
  classList: { contains: (cls) => cls === 'shopping-list-portions' },
  dataset: { url: url },
  value: String(value)
});

test('a `makes:` recipe starts at one batch, and its row says batches', () => {
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/cookies/');
  showTheList(doc);

  const html = recipesHtml(panel);
  assert.match(html, /value="1" data-url="\/food\/recipes\/cookies\/" data-batches/);
  assert.strictEqual(html.replace(/<[^>]*>/g, '').trim(),
    'batch of 18 Peanut Butter Cookies');
  assert.ok(html.includes('aria-label="batches of Peanut Butter Cookies'));
  assert.match(aislesHtml(panel), /100 g/);
});

test('the figure after "of" is shown only for a count above one', () => {
  // "2 batches of 750 ml Blackberry gelato" reads worse than the name alone.
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/gelato/');
  showTheList(doc);
  assert.strictEqual(recipesHtml(panel).replace(/<[^>]*>/g, '').trim(),
    'batch of Blackberry gelato');
});

// --- a yield that is ONE named thing is counted as that thing ------------------
// "one 8-inch cake" and "1 jar" are not batches: the row names the thing made.

const rowText = (panel) => recipesHtml(panel).split('</li>')
  .map((row) => row.replace(/<[^>]*>/g, '').trim()).filter(Boolean);

test('one cake is a cake, not a batch: the row names the thing made', () => {
  const { win, doc, panel } = boot({ recipes: SINGLE_THINGS });
  win.HTF.shortlist.toggle('/food/recipes/cake/');
  win.HTF.shortlist.toggle('/food/recipes/sauce/');
  win.HTF.shortlist.toggle('/food/recipes/pies/');
  showTheList(doc);

  assert.deepStrictEqual(rowText(panel), [
    // The title names the thing ("Cake"), so the noun is not said twice.
    '× 8-inch Beetroot Chocolate Cake',
    // A jar holds the sauce, so it comes first with "of". `jar` is in the
    // fixture's data-container-nouns.
    'jar of Peanut Sauce',
    // A dozen is counted in dozens; "mince pies" is already in the title.
    'dozen Mince Pies'
  ]);
  const html = recipesHtml(panel);
  assert.ok(!/batch/.test(html.replace(/data-batches/g, '')
    .replace(/shopping-list-recipe--first-batch/g, '')), html);
  // The label cannot move with the number, so it does not try to.
  assert.ok(html.includes('aria-label="how many: Beetroot Chocolate Cake, which makes one 8-inch cake"'), html);
});

test('two of them take the plural, and a dozen stays a dozen', () => {
  const { win, doc, panel } = boot({ recipes: SINGLE_THINGS });
  ['cake', 'sauce', 'pies'].forEach((slug) => {
    win.HTF.shortlist.toggle('/food/recipes/' + slug + '/');
    win.HTF.shortlist.setBatches('/food/recipes/' + slug + '/', 2);
  });
  showTheList(doc);

  assert.deepStrictEqual(rowText(panel), [
    // The title is not made plural, which is why the × is there at one too.
    '× 8-inch Beetroot Chocolate Cake',
    'jars of Peanut Sauce',
    'dozen Mince Pies'
  ]);
  assert.match(aislesHtml(panel), /500 g/, 'and two cakes is twice the flour');
});

test('one thing that IS the dish, and is not in its name, follows the name', () => {
  // A traybake is not a container, so there is no "of"; the noun takes the
  // plural above one.
  const recipes = {
    '/food/recipes/cake/': {
      p: null, y: 'one traybake', k: 'makes', w: true, h: false,
      m: { kind: 'count', base: 1, stem: 'traybake', rest: '', box: '1',
        singular: true, times: false, invariable: false },
      i: [{ a: '250 g', n: 'plain flour', s: 'cupboard' }]
    }
  };
  const { win, doc, panel } = boot({ recipes });
  win.HTF.shortlist.toggle('/food/recipes/cake/');
  showTheList(doc);
  assert.deepStrictEqual(rowText(panel), ['Beetroot Chocolate Cake traybake']);
  win.HTF.shortlist.setBatches('/food/recipes/cake/', 3);
  doc.dispatch('htf:shortlist-change');
  assert.deepStrictEqual(rowText(panel), ['Beetroot Chocolate Cake traybakes']);
});

test('the title\'s own noun goes singular before the thing made', () => {
  // A plural noun in the title goes singular when the thing made follows it.
  // The cookies' row, where nothing follows the title, keeps its plural.
  const recipes = {
    '/food/recipes/cookies/': Object.assign({}, RECIPES['/food/recipes/cookies/'], {
      y: '16 squares',
      m: { kind: 'count', base: 16, stem: 'squares', rest: '', box: '16' }
    })
  };
  const { win, doc, panel } = boot({ recipes });
  win.HTF.shortlist.toggle('/food/recipes/cookies/');
  showTheList(doc);
  assert.deepStrictEqual(rowText(panel), ['batch of 16 Peanut Butter Cookie squares']);
});

test('a batch says what it is a batch OF when the title does not', () => {
  // `makes: "24 squares"`: the row says what the batch is of. The cookies'
  // title already says cookies; a dozen stays a dozen.
  const recipes = {
    '/food/recipes/cake/': {
      p: null, y: '24 squares', k: 'makes', w: true, h: false,
      m: { kind: 'count', base: 24, stem: 'squares', rest: '', box: '24' },
      i: [{ a: '250 g', n: 'plain flour', s: 'cupboard' }]
    },
    '/food/recipes/cookies/': RECIPES['/food/recipes/cookies/'],
    '/food/recipes/pies/': {
      p: null, y: 'about 3 dozen', k: 'makes', w: true, h: false,
      m: { kind: 'count', base: 3, stem: 'dozen', rest: '', box: '3', invariable: true },
      i: [{ a: '300 g', n: 'mincemeat', s: 'cupboard' }]
    }
  };
  const { win, doc, panel } = boot({ recipes });
  Object.keys(recipes).forEach((url) => win.HTF.shortlist.toggle(url));
  showTheList(doc);
  assert.deepStrictEqual(rowText(panel), [
    'batch of 24 Beetroot Chocolate Cake squares',
    'batch of 18 Peanut Butter Cookies',
    'batch of 3 dozen Mince Pies'
  ]);
});

test('every recipe named in the panel is a link to it, in the row title\'s class', () => {
  // Each name is a link; the figure and the words stay outside it.
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/a/');
  win.HTF.shortlist.toggle('/food/recipes/cookies/');
  showTheList(doc);
  const html = recipesHtml(panel);
  assert.ok(html.includes(
    '<a class="shopping-list-recipe-link" href="/food/recipes/a/">Aubergine thing</a>'), html);
  assert.ok(html.includes(
    '18 <a class="shopping-list-recipe-link" href="/food/recipes/cookies/">Peanut Butter Cookies</a>'),
    'the figure and the words stay outside the link: ' + html);
});

test('an item nobody scaled names the recipe it came from, as a link', () => {
  // An unscaled item names its recipe in brackets, so the reader knows which
  // page to look at. Recipe `a` lists olive oil with no amount; its flour and
  // onions are scaled and say nothing.
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/a/');
  win.HTF.shortlist.toggle('/food/recipes/b/');
  showTheList(doc);
  const html = aislesHtml(panel);
  assert.ok(html.includes(
    '<span class="shopping-list-name">olive oil</span>' +
    '<span class="shopping-list-unscaled">(' +
    '<a class="shopping-list-recipe-link" href="/food/recipes/a/">Aubergine thing</a>)</span>'),
    html);
  assert.strictEqual(html.split('shopping-list-unscaled').length - 1, 1,
    'only the unscaled row carries a bracket');
});

test('a count above one is still batches of that many', () => {
  // 18 of something is a batch, unlike one named thing.
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/cookies/');
  win.HTF.shortlist.setBatches('/food/recipes/cookies/', 2);
  showTheList(doc);
  assert.deepStrictEqual(rowText(panel), ['batches of 18 Peanut Butter Cookies']);
});

test('NO PORTION FIGURE IS PRINTED FOR A `makes:` RECIPE, anywhere on its row', () => {
  // The estimate is still in the blob (`p: 9`) and must not reach the row,
  // its title or its label.
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/cookies/');
  win.HTF.shortlist.toggle('/food/recipes/gelato/');
  showTheList(doc);
  // The input's CLASS is still `shopping-list-portions`; nothing a person or
  // a screen reader is given may say the word.
  const html = recipesHtml(panel).replace(/ class="[^"]*"/g, '');
  assert.ok(!/portion/.test(html), html);
  assert.ok(!html.includes('~'), html);
  assert.ok(html.includes('which makes 18 cookies'), 'the yield, in its own words');
});

test('typing a number of batches multiplies the recipe', () => {
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/cookies/');
  showTheList(doc);

  panel.querySelector('.shopping-list-recipes')
    .dispatch('input', { target: batchInput('/food/recipes/cookies/', 3) });

  assert.match(aislesHtml(panel), /300 g/);
  assert.match(aislesHtml(panel), /<span class="shopping-list-amount">3<\/span>/,
    'three eggs, never a fraction of one');
  assert.strictEqual(win.HTF.shortlist.batches('/food/recipes/cookies/'), 3);
  assert.strictEqual(win.HTF.shortlist.portions('/food/recipes/cookies/'), null,
    'a batch count must never be written into the portions store');
});

test('half a batch is offered only where the build allows it', () => {
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/gelato/');     // h: true
  win.HTF.shortlist.toggle('/food/recipes/cookies/');    // h: false
  showTheList(doc);

  const html = recipesHtml(panel);
  assert.match(html, /min="0\.5" max="99" step="0\.5"[^>]*recipes\/gelato\//);
  assert.match(html, /min="1" max="99" step="1"[^>]*recipes\/cookies\//);

  const rows = panel.querySelector('.shopping-list-recipes');
  rows.dispatch('input', { target: batchInput('/food/recipes/gelato/', 0.5) });
  rows.dispatch('input', { target: batchInput('/food/recipes/cookies/', 0.5) });

  assert.strictEqual(win.HTF.shortlist.batches('/food/recipes/gelato/'), 0.5);
  assert.strictEqual(win.HTF.shortlist.batches('/food/recipes/cookies/'), 1,
    'half a batch of the cookies is half an egg');
  assert.match(aislesHtml(panel), /250 ml/, 'half the milk');
  assert.match(aislesHtml(panel), /100 g/, 'all of the peanut butter');
});

test('there is no batch and a half: the spinner goes on to the next whole one', () => {
  // The box steps in halves so that it can reach ½, and so lands on 1½ on the
  // way up from 1 and down from 2. Halves exist only between 0 and 1.
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/gelato/');
  showTheList(doc);
  const rows = panel.querySelector('.shopping-list-recipes');

  const up = batchInput('/food/recipes/gelato/', 1.5);
  rows.dispatch('input', { target: up });
  assert.strictEqual(win.HTF.shortlist.batches('/food/recipes/gelato/'), 2);
  assert.strictEqual(up.value, '2', 'the box is corrected under the spinner');

  rows.dispatch('input', { target: batchInput('/food/recipes/gelato/', 1.5) });
  assert.strictEqual(win.HTF.shortlist.batches('/food/recipes/gelato/'), 1);
});

test('"set all to" sets the portions rows and leaves the batch rows alone', () => {
  // "6 portions" of 18 cookies has no answer that does not decide how many
  // cookies a portion is, so "set all to" leaves the batch rows alone.
  const { win, doc, panel } = boot();
  Object.keys(RECIPES).forEach((url) => win.HTF.shortlist.toggle(url));
  showTheList(doc);

  const setAll = doc.getElementById('shopping-list-setall');
  setAll.value = '12';
  setAll.dispatch('input');

  assert.strictEqual(win.HTF.shortlist.portions('/food/recipes/a/'), 12);
  assert.strictEqual(win.HTF.shortlist.portions('/food/recipes/b/'), 12);
  assert.strictEqual(win.HTF.shortlist.portions('/food/recipes/gelato/'), null);
  assert.strictEqual(win.HTF.shortlist.batches('/food/recipes/cookies/'), null);
  // a: 200 g x3, b: 300 g x2, so the flour is 600 + 600; the cookies unmoved.
  assert.match(aislesHtml(panel), /1\.2 kg/);
  assert.match(aislesHtml(panel), /100 g/);
});

test('a portions number left in the store is not read as batches', () => {
  // The store may still hold a portions entry for a `makes:` recipe. A stored
  // 6 was six people; read as batches it shops for six times the gelato.
  const { win, doc, panel } = boot();
  win.HTF.shortlist.setPortions('/food/recipes/gelato/', 6);
  win.HTF.shortlist.toggle('/food/recipes/gelato/');
  showTheList(doc);
  assert.match(recipesHtml(panel), /value="1" data-url="\/food\/recipes\/gelato\//);
  assert.match(aislesHtml(panel), /125 ml/);
});

test('no figure is marked as a guess: every one is the recipe\'s own', () => {
  // serves_estimate is retired, so nothing on the list prints a `~`.
  const { win, doc, panel } = boot();
  ['/food/recipes/a/', '/food/recipes/b/', '/food/recipes/gelato/'].forEach(
    (u) => win.HTF.shortlist.toggle(u));
  showTheList(doc);
  assert.ok(!recipesHtml(panel).includes('~'), 'a figure is marked as estimated');
  assert.ok(recipesHtml(panel).includes('which makes About 750 ml'),
    'a makes: recipe quotes its own yield');
});

test('a by-eye measure is totalled to a whole one, from the panel\'s own list', () => {
  // #1297: the list reaches build() through `data-whole-measures`. Seven
  // portions of a recipe for four is 1.75 handfuls, and prints 2.
  const { win, doc, panel } = boot({
    recipes: {
      '/food/recipes/a/': {
        p: 4, y: '4', k: 'serves',
        i: [{ a: '1 handful', n: 'parsley', s: 'produce' }]
      }
    }
  });
  win.HTF.shortlist.setPortions('/food/recipes/a/', 7);
  win.HTF.shortlist.toggle('/food/recipes/a/');
  showTheList(doc);
  assert.match(aislesHtml(panel), /<span class="shopping-list-amount">2 handfuls<\/span>/);
});

test('the juice and the zest of one lemon is one lemon, on the real wiring', () => {
  // #1297: the marks ride from the blob (`pt`, `f`, `c`, `x`) into build().
  const { win, doc, panel } = boot({
    recipes: {
      '/food/recipes/a/': {
        p: 4, y: '4', k: 'serves',
        i: [{ a: '', n: 'juice of 1 lemon', s: 'produce', pt: ['juice'], f: 'lemon', c: '1' },
          { a: '', n: 'zest of 1 lemon', s: 'produce', pt: ['zest'], f: 'lemon', c: '1' },
          { a: '85 ml', n: 'olive oil', s: 'cupboard' },
          { a: '', n: 'olive oil', s: 'cupboard', x: true }]
      }
    }
  });
  win.HTF.shortlist.toggle('/food/recipes/a/');
  showTheList(doc);
  const html = aislesHtml(panel);
  assert.match(html,
    /<span class="shopping-list-amount">1<\/span><span class="shopping-list-name">lemon<\/span>/);
  assert.match(html, /<span class="shopping-list-amount">85 ml<\/span>/);
  assert.ok(!html.includes('×'), 'the pointer line added a count to the oil');
});

test('A STORED NUMBER CANNOT RESURRECT A BOX THE RECIPE CANNOT SUPPORT', () => {
  /* portionsFor() must ask the recipe before the store. A number typed
     earlier outlives the recipe's own data in localStorage; trusted, it draws
     a box that accepts 200 and scales nothing. So this test seeds the store. */
  const { win, doc, panel } = boot({
    recipes: {
      '/food/recipes/a/': {
        p: null, y: 'Depends on appetite', k: 'serves',
        i: [{ a: '125 ml', n: 'whipping cream', s: 'cupboard' }]
      }
    }
  });
  // A number typed before the recipe lost, or never had, its count.
  win.HTF.shortlist.setPortions('/food/recipes/a/', 200);
  win.HTF.shortlist.toggle('/food/recipes/a/');
  showTheList(doc);

  assert.ok(!recipesHtml(panel).includes('<input'),
    'a stored number drew a box for a recipe with no portion count');
  assert.match(recipesHtml(panel), /no serving size/);
  assert.match(aislesHtml(panel), /125 ml/,
    'and the amounts stay exactly as the recipe wrote them, not x200');
});

test('a recipe with NO portion count gets no box, and says why', () => {
  /* A draft whose yield is still Helen's `QQ`. It contributes at x1 and says
     what is missing, rather than offering a control that does nothing. */
  const { win, doc, panel } = boot({
    recipes: {
      '/food/recipes/a/': {
        p: null, y: 'QQ', k: 'serves',
        i: [{ a: '200 g', n: 'plain flour', s: 'cupboard' }]
      }
    }
  });
  win.HTF.shortlist.toggle('/food/recipes/a/');
  showTheList(doc);

  const html = recipesHtml(panel);
  assert.ok(!html.includes('<input'), 'no control that cannot work');
  assert.match(html, /no serving size/);
  assert.match(html, /open <code>serves:<\/code> with a number/, 'the note says what to write');
  // Its ingredients still count, at the recipe as written.
  assert.match(aislesHtml(panel), /200 g/);
});

test('a shortlisted recipe that is no longer on the page is dropped quietly', () => {
  // A renamed or unpublished recipe, left in localStorage.
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/gone/');
  win.HTF.shortlist.toggle('/food/recipes/a/');
  showTheList(doc);
  assert.ok(!recipesHtml(panel).includes('/food/recipes/gone/'));
  assert.match(aislesHtml(panel), /200 g/);
});

// --- arriving at the shortlist by URL, #1011 -----------------------------------
// `?shortlist=1` is what "see shortlist" on a recipe page links to. The index
// turns the view on through the same `enterShortlistView()` the
// `shortlisted (N)` button calls, so the two doors lead to one state (#918,
// MANUAL 8.9).

function shortlistViewIsOn(doc) {
  const btn = doc.getElementById('shortlist-only');
  assert.ok(btn, 'the fixture has no shortlisted-only button.');
  return btn.getAttribute('aria-pressed') === 'true' &&
         btn.classList.contains('is-on');
}

function visibleRows(list) {
  return list.children.filter((li) => !li.hidden && li.style.display !== 'none');
}

test('#1011: ?shortlist=1 turns the shortlist view on at startup', () => {
  const { doc, list } = boot({ search: '?shortlist=1' });
  assert.ok(shortlistViewIsOn(doc),
    'if the index does not read the query, the URL lands on an ordinary ' +
    'index -- which looks like a working page and is not one.');
  assert.strictEqual(visibleRows(list).length, 0,
    'the view is on and nothing is shortlisted, so nothing survives -- which ' +
    'is also what proves the state reached update().');
});

test('#1011: without the query the view stays off', () => {
  const { doc, list } = boot();
  assert.ok(!shortlistViewIsOn(doc));
  assert.strictEqual(visibleRows(list).length, Object.keys(RECIPES).length);
});

test('#1011: a shortlisted recipe is what the link shows', () => {
  const { win, doc, list } = boot({ search: '?shortlist=1' });
  // The store is read at update time, so marking one after boot and
  // dispatching the change event is what a row's own toggle does.
  win.HTF.shortlist.toggle('/food/recipes/a/');
  doc.dispatch('htf:shortlist-change');
  assert.ok(shortlistViewIsOn(doc), 'a toggle must not knock the view off');
  assert.deepStrictEqual(
    visibleRows(list).map((li) => li.getAttribute('data-url')),
    ['/food/recipes/a/']);
});

// --- a shortlist someone sent, #1093 ------------------------------------------------
// `?shortlist=a,gelato` opens the view `?shortlist=1` does, answering "is this
// row on it" from the link. It shows the list and saves none of it; "keep
// these" makes it yours.

const sharedNote = (doc) => doc.querySelector('[data-shared-shortlist]');
const visibleUrls = (list) => visibleRows(list).map((li) => li.getAttribute('data-url'));

test('#1093: a sent list shows exactly those recipes', () => {
  const { doc, list } = boot({ search: '?shortlist=gelato,a' });
  assert.deepStrictEqual(visibleUrls(list).sort(), ['/food/recipes/a/', '/food/recipes/gelato/']);
});

test('#1093: opening a sent list saves NOTHING to this browser', () => {
  const { win } = boot({ search: '?shortlist=gelato,a' });
  assert.strictEqual(win.HTF.shortlist.count(), 0,
    'the link wrote to the store. Helen: "Show it, don\'t save it".');
});

test('#1093: the sent list is shown over this browser\'s own, not merged with it', () => {
  const { win, doc, list } = boot({ search: '?shortlist=gelato' });
  win.HTF.shortlist.toggle('/food/recipes/b/');
  doc.dispatch('htf:shortlist-change');
  assert.deepStrictEqual(visibleUrls(list), ['/food/recipes/gelato/'],
    'a recipe marked in THIS browser leaked into the list someone sent.');
});

test('#1093: the button that counts YOUR shortlist is not lit over a sent one', () => {
  const { doc } = boot({ search: '?shortlist=gelato' });
  assert.ok(!shortlistViewIsOn(doc));
});

test('#1093: the note says how many, and names what it could not find', () => {
  const { doc } = boot({ search: '?shortlist=gelato,renamed-thing' });
  const note = sharedNote(doc);
  assert.strictEqual(note.hidden, false);
  const text = note.querySelector('[data-shared-shortlist-text]').textContent;
  assert.match(text, /\(1\)/);
  assert.match(text, /renamed-thing/);
});

test('a sent list opens WITH its shopping list, totalled from the link', () => {
  const { win, panel } = boot({ search: '?shortlist=gelato,a' });
  assert.strictEqual(panel.hidden, false);
  assert.deepStrictEqual(rowText(panel),
    ['portions of Aubergine thing', 'batch of Blackberry gelato']);
  assert.match(aislesHtml(panel), /500 ml/, 'the gelato\'s milk, as written');
  assert.strictEqual(win.HTF.shortlist.count(), 0,
    'and showing it still saved nothing: "Show it, don\'t save it".');
});

test('#1093: keep these merges the list in and shows YOUR shortlist', () => {
  const { win, doc, list, panel } = boot({ search: '?shortlist=gelato' });
  win.HTF.shortlist.toggle('/food/recipes/b/');
  doc.querySelector('[data-shared-shortlist-keep]').dispatch('click');

  // Through JSON: the array was made in the page's realm, not this one.
  assert.deepStrictEqual(JSON.parse(JSON.stringify(win.HTF.shortlist.list())),
    ['/food/recipes/b/', '/food/recipes/gelato/']);
  assert.ok(shortlistViewIsOn(doc), 'after keeping, the view is your own shortlist');
  assert.deepStrictEqual(visibleUrls(list).sort(), ['/food/recipes/b/', '/food/recipes/gelato/']);
  assert.strictEqual(sharedNote(doc).hidden, true);
  assert.strictEqual(panel.hidden, false, 'your own list shops again');
});

test('#1093: pressing shortlisted (N) over a sent list shows YOUR list instead', () => {
  const { win, doc, list } = boot({ search: '?shortlist=gelato' });
  win.HTF.shortlist.toggle('/food/recipes/b/');
  doc.getElementById('shortlist-only').dispatch('click');
  assert.ok(shortlistViewIsOn(doc));
  assert.deepStrictEqual(visibleUrls(list), ['/food/recipes/b/']);
  assert.strictEqual(sharedNote(doc).hidden, true);
});

test('#1093: a slug nothing answers to still enters the view, showing nothing', () => {
  const { doc, list } = boot({ search: '?shortlist=nothing-by-this-name' });
  assert.deepStrictEqual(visibleUrls(list), []);
  assert.strictEqual(sharedNote(doc).hidden, false, 'and the note says why');
  assert.strictEqual(doc.querySelector('[data-shared-shortlist-keep]').hidden, true,
    'there is nothing to keep');
});

// --- arriving with a name, #1024 -----------------------------------------------

test('#1024: ?q= fills the name box and narrows the list', () => {
  const { doc, list } = boot({ search: '?q=beetroot' });
  assert.strictEqual(doc.getElementById('name-search-box').value, 'beetroot',
    'the box should show what the reader typed on the page they came from.');
  // The order, not the visible set. The highlight rewrites the title through
  // innerHTML, which this stub clears rather than parses (dom-stub.js), so the
  // row's title reads as '' to the filter here. reorderForTitleSearch() runs
  // first, and the order is what proves the query reached the script.
  assert.strictEqual(list.children[0].getAttribute('data-url'), '/food/recipes/b/',
    'the query must reach reorderForTitleSearch(), not only the box.');
});

// --- arriving with an ingredient, #1050 -----------------------------------------
// `?ing=` is what the search-for-anything box on a recipe page sends when the
// reader picks an ingredient. It must land in HAS TO HAVE and be applied as
// choosing that result there would, so the dropdown and the picker are one
// control in two places.

test('#1050: ?ing= fills the HAS TO HAVE box and narrows the list to that ingredient', () => {
  const { doc, list } = boot({ search: '?ing=beetroot' });
  assert.strictEqual(doc.getElementById('ingredient-search-box').value, 'beetroot',
    'the box should show the word the reader chose on the page they came from.');
  assert.deepStrictEqual(
    visibleRows(list).map((li) => li.getAttribute('data-url')),
    ['/food/recipes/b/'],
    'the word must reach the picker and be CHOSEN, not only typed -- one row ' +
    'names beetroot and only that row should survive.');
});

test('#1050: an ingredient nothing names leaves the picker in a plain search', () => {
  // A stale value must not error and must not narrow the list: the text
  // stays in the box with nothing chosen, and every row still shows.
  const { doc, list } = boot({ search: '?ing=quince' });
  assert.strictEqual(doc.getElementById('ingredient-search-box').value, 'quince');
  assert.strictEqual(visibleRows(list).length, Object.keys(RECIPES).length,
    'nothing was chosen, so nothing should be narrowing the list.');
});

// --- arriving at a fragment, #1057 and #1059 ------------------------------------
// The startup block scrolls to any element id `location.hash` names, not only
// "results": #1057 (the see-shortlist link) and #1059 (a badge's own
// filter-section fragment) both rely on that.

test('#1050/#1057: arriving at #results scrolls the count line into view', () => {
  const { results } = boot({ hash: '#results' });
  assert.strictEqual(results._scrollCalls.length, 1,
    'the startup block must scroll to location.hash again after the reveal, ' +
    'the same landing a search result and "see shortlist" both rely on.');
  // Not assert.deepStrictEqual: the options object was built inside the vm
  // context filters.js runs in, so it has that realm's own Object.prototype
  // and fails a STRICT structural compare despite being the same shape.
  assert.strictEqual(results._scrollCalls[0].block, 'start');
});

test('#1059: arriving at a filter section\'s own fragment scrolls IT into view, not #results', () => {
  const { starSection, results } = boot({ hash: '#filter-star' });
  assert.strictEqual(starSection._scrollCalls.length, 1,
    'a badge\'s own fragment (e.g. #filter-star) must be read generically off ' +
    'location.hash, not hardcoded to "results".');
  assert.strictEqual(results._scrollCalls, undefined,
    'only the id location.hash actually names should be scrolled to.');
});

test('with no hash at all, nothing is scrolled', () => {
  const { results, starSection } = boot();
  assert.strictEqual(results._scrollCalls, undefined);
  assert.strictEqual(starSection._scrollCalls, undefined);
});

test('#387: a genuine back navigation restores scroll instead, and skips the fragment scroll', () => {
  // On a back navigation the remembered scroll wins over the fragment still
  // in the URL. restoreIndexMemory() fires only for a `back_forward`
  // navigation entry with a valid record to restore; both are arranged here.
  const { win, results } = boot({
    hash: '#results',
    backForward: true,
    beforeStart(w) {
      w.HTF.indexMemory.save('htf-index-memory-v1', {
        order: Object.keys(RECIPES),
        filters: w.HTF.filterState.serialise(w.HTF.filterState.emptyState()),
        ingredientLabels: {},
        page: 1,
        showAll: false,
        scrollY: 321
      });
    }
  });
  assert.strictEqual(win.__scrollToCalls[win.__scrollToCalls.length - 1][1], 321,
    'the remembered scroll position must still be restored.');
  assert.strictEqual(results._scrollCalls, undefined,
    'a genuine back navigation must not ALSO jump to location.hash -- the ' +
    'remembered scroll is the truer answer, same as before #1057/#1059 ' +
    'widened this from "#results" to any fragment.');
});

// --- HAS TO HAVE is AND-multi-select -- GitHub issue #1092 ---------------------
// A second pick joins the first, and every chosen ingredient is required.
// Each word typed below matches exactly one entry in MAIN_INGREDIENTS, so it
// commits as it is typed, with no click.

function typeIngredient(doc, word) {
  const box = doc.getElementById('ingredient-search-box');
  box.value = word;
  box.dispatch('input');
}

test('#1092: a second HAS TO HAVE pick joins the first instead of replacing it', () => {
  const { doc, list } = boot();
  typeIngredient(doc, 'aubergines');
  assert.deepStrictEqual(visibleRows(list).map((li) => li.getAttribute('data-url')),
    ['/food/recipes/a/'],
    'choosing "aubergines" alone should already narrow to the one recipe that names it.');

  typeIngredient(doc, 'olive oil');
  assert.deepStrictEqual(visibleRows(list).map((li) => li.getAttribute('data-url')),
    ['/food/recipes/a/'],
    'both chosen ingredients are on the SAME recipe, so it should still be the ' +
    'only survivor -- this alone cannot tell "AND both" from "replaced by the ' +
    'second", which the next assertion is for.');

  // No fixture recipe names both aubergines and beetroot, so requiring all
  // three leaves an empty list; a pick that replaced the others shows recipe b.
  typeIngredient(doc, 'beetroot');
  assert.deepStrictEqual(visibleRows(list).map((li) => li.getAttribute('data-url')), [],
    'aubergines, olive oil AND beetroot are three requirements now, and no ' +
    'fixture recipe carries all three -- if this shows recipe b, the third ' +
    'pick replaced the first two instead of joining them.');

  // Both a chosen ingredient's own button and the inline clear stay visible
  // for a filter that is actually still applied.
  const activeButtons = Array.from(
    doc.getElementById('ingredient-results-pool').querySelectorAll('.btn-ingredient.active')
  );
  assert.deepStrictEqual(
    activeButtons.map((b) => b.dataset.ingredient).sort(),
    ['aubergines', 'beetroot', 'olive oil'],
    'all three chosen entries should still show as active chips, not just the last one.'
  );
});

test('#1092: removing one chosen ingredient leaves the others in place', () => {
  const { doc, list } = boot();
  typeIngredient(doc, 'aubergines');
  typeIngredient(doc, 'olive oil');

  // Clicking an already-chosen chip removes just that one.
  const pool = doc.getElementById('ingredient-results-pool');
  const aubergineChip = Array.from(pool.querySelectorAll('.btn-ingredient'))
    .find((b) => b.dataset.ingredient === 'aubergines');
  assert.ok(aubergineChip, 'the chosen aubergines chip should still be on screen to click.');
  aubergineChip.dispatch('click');

  assert.deepStrictEqual(visibleRows(list).map((li) => li.getAttribute('data-url')),
    ['/food/recipes/a/'],
    'olive oil alone still narrows to recipe a; removing aubergines must not ' +
    'have cleared the whole picker with it.');
});

// --- choosing from several -----------------------------------------------------
// A chosen chip joins the others at the top, the other candidates go, and the
// chosen chip carries an x.

test('choosing one HAS TO HAVE candidate of several clears the search and keeps only the chosen', () => {
  const { doc } = boot();
  typeIngredient(doc, 'o');
  const pool = doc.getElementById('ingredient-results-pool');
  const offered = Array.from(pool.querySelectorAll('.btn-ingredient'));
  assert.ok(offered.length > 1, 'the fixture should offer several candidates for "o".');
  const picked = offered[0].dataset.ingredient;
  offered[0].dispatch('click');

  assert.strictEqual(doc.getElementById('ingredient-search-box').value, '',
    'the box should be free for the next ingredient.');
  const left = Array.from(pool.querySelectorAll('.btn-ingredient'));
  assert.deepStrictEqual(left.map((b) => b.dataset.ingredient), [picked],
    'the other candidates should have gone, leaving the chosen chip.');
  assert.ok(left[0].classList.contains('active'));
});

test('a chosen HAS TO HAVE chip carries an x, and a click on the x removes the chip', () => {
  const { doc } = boot();
  typeIngredient(doc, 'aubergines');
  const pool = doc.getElementById('ingredient-results-pool');
  const chip = Array.from(pool.querySelectorAll('.btn-ingredient'))
    .find((b) => b.dataset.ingredient === 'aubergines');
  assert.ok(chip.classList.contains('active'), 'a unique match is chosen as it is typed.');
  const x = chip.querySelector('.btn-ingredient-x');
  assert.ok(x, 'the chosen chip should carry its x.');
  assert.strictEqual(x.textContent, ' ×');
  assert.strictEqual(chip.getAttribute('aria-label'), 'stop requiring aubergines');

  // The click lands on the span, not the button, in a real browser.
  x.dispatch('click');
  assert.strictEqual(chip.classList.contains('active'), false,
    'a click on the x is a click on the chip, and should remove the requirement.');
  assert.strictEqual(chip.querySelector('.btn-ingredient-x'), null,
    'an unchosen chip keeps no x.');
});

// --- the list of scripts is the template's list --------------------------------

test('this harness loads what food/index.html actually loads', () => {
  // A tag added to the template and not here means the thing under test
  // drifts away from the thing that ships.
  const html = fs.readFileSync(path.join(ROOT, 'food', 'index.html'), 'utf8');
  const inTemplate = [...html.matchAll(/<script src="\{\{ '\/assets\/js\/([^']+)'/g)]
    .map((m) => m[1]);

  // assets.js is the layout's, not this page's, and is loaded first in both.
  assert.deepStrictEqual(SCRIPTS.slice(1), inTemplate,
    'tests/js/food-index-startup.test.js loads a different set of scripts from '
    + 'food/index.html. Update SCRIPTS to match the template.');
});

// --- #1297: batch rows last, and the not-scaled note ---------------------------

const noteOf = (panel) => panel.querySelector('.shopping-list-note');

test('#1297: the batch rows come last, under a rule, whatever order they were shortlisted in', () => {
  // Grouped at the bottom, so it is clear that "set all to" multiplies the
  // portions rows and the batch rows are set by hand.
  const { win, doc, panel } = boot();
  ['/food/recipes/cookies/', '/food/recipes/a/', '/food/recipes/gelato/',
    '/food/recipes/b/'].forEach((url) => win.HTF.shortlist.toggle(url));
  showTheList(doc);

  const html = recipesHtml(panel);
  const at = (slug) => html.indexOf('data-url="/food/recipes/' + slug + '/"');
  assert.ok(at('a') < at('b') && at('b') < at('cookies') && at('cookies') < at('gelato'),
    'portions rows first, then batch rows, each in shortlist order');
  assert.strictEqual(html.split('shopping-list-recipe--first-batch').length - 1, 1,
    'exactly one row carries the rule');
  assert.ok(html.indexOf('shopping-list-recipe--first-batch') < at('cookies') &&
    html.indexOf('shopping-list-recipe--first-batch') > at('b'),
    'and it is the first batch row');
});

test('#1297: with no portions rows above them, the batch rows have no rule', () => {
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/cookies/');
  win.HTF.shortlist.toggle('/food/recipes/gelato/');
  showTheList(doc);
  assert.ok(!recipesHtml(panel).includes('shopping-list-recipe--first-batch'));
});

test('#1297: what was not scaled is named under the rows, in her format', () => {
  // Bracketed, comma-joined, no full stop.
  const { win, doc, panel } = boot({
    recipes: {
      '/food/recipes/a/': {
        p: 4, y: '4', k: 'serves',
        i: [{ a: '200 g', n: 'plain flour', s: 'cupboard' },
          { a: '', n: 'olive oil', s: 'cupboard' },
          { a: 'some', n: 'salt', s: 'cupboard' },
          { a: '', n: 'coriander sprigs', s: 'produce' }]
      }
    }
  });
  win.HTF.shortlist.toggle('/food/recipes/a/');
  showTheList(doc);
  assert.strictEqual(noteOf(panel).textContent,
    '(Not scaled: coriander sprigs, olive oil, salt)');
  assert.strictEqual(noteOf(panel).hidden, false);
  // Still on the list below: it has to be bought.
  assert.match(aislesHtml(panel), /<span class="shopping-list-name">olive oil<\/span>/);
});

test('#1297: with everything scaled there is no note', () => {
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/cookies/');
  showTheList(doc);
  assert.strictEqual(noteOf(panel).textContent, '');
  assert.strictEqual(noteOf(panel).hidden, true);
});

test('#1297: a page without the note element still totals', () => {
  const { win, doc, panel } = boot();
  const note = noteOf(panel);
  note.parentNode.removeChild(note);
  win.HTF.shortlist.toggle('/food/recipes/a/');
  assert.doesNotThrow(() => showTheList(doc));
});
