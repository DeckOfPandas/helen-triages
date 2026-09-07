// =============================================================================
// The food index actually RUNS, and its shopping list actually fills in — #801.
//
//   node --test tests/js/*.test.js
// =============================================================================
// THE SAME ARGUMENT tests/js/cocktail-index-startup.test.js MAKES, on the other
// index. Every other JS test in this repo asks a pure module a question and gets
// a correct answer; the faults that have actually shipped were in the WIRING
// between modules, which is the one place a suite of pure-function tests cannot
// look. cocktail-index.js read a property off the wrong object once and the
// entire tail of the file stopped running, with every test green.
//
// FOOD IS WORSE THAN COCKTAILS IN ONE RESPECT, which is why this exists now:
// the whole of filters.js is inside a single `DOMContentLoaded` handler, so
// anything that throws anywhere in it takes the rest of the file with it -- the
// shuffle, the filter buttons, the query-string restore, and the line that
// lifts `.recipe-list`'s `visibility: hidden`. The failure is a BLANK INDEX,
// with the only evidence in a console nobody has open. #801 adds two scripts
// and about a hundred lines to that handler.
//
// THE CANARY IS `.recipe-list` BECOMING VISIBLE, and it is the right one for
// the same reason cocktails picked its `pagehide` listener: it is one of the
// last statements in the file, so anything that throws above it stops it
// happening, and one assertion covers every line before it.
//
// THE SCRIPTS ARE THE REAL FILES, in the order food/index.html loads them, run
// through `vm.runInNewContext` rather than require() -- these are not modules
// in a browser, and the browser path is the one that breaks. Only the DOM and
// localStorage are stand-ins.
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
// own tags, in its own order. test_the_food_shopping_scripts_load_in_dependency
// _order in tests/test_site_config.py guards the last three in the template;
// the test at the foot of this file guards that THIS list still matches it.
const SCRIPTS = [
  'assets.js',
  'ingredient-search.js',
  'recipe-list.js',
  'filter-state.js',
  'shopping-list.js',
  'food-shopping-list.js',
  'filters.js'
];

/* Two recipes and the panel, hand-built rather than sliced out of a real build:
   a fixture you can read in one screen is what makes a failure diagnosable, and
   the alternative drags a megabyte of markup into the repo.

   `b` IS THE GUESSED ONE (`e: true`), because the tilde on a guessed serving
   size is the only thing on the page saying a number is this repo's rather
   than Helen's. */
const RECIPES = {
  '/food/recipes/a/': {
    p: 4, e: false, y: '4',
    i: [{ a: '200 g', n: 'plain flour', s: 'cupboard' },
      { a: '2', n: 'onions', s: 'produce' },
      { a: '', n: 'olive oil', s: 'cupboard' }]
  },
  '/food/recipes/b/': {
    p: 6, e: true, y: 'one 8-inch cake',
    i: [{ a: '300 g', n: 'plain flour', s: 'cupboard' },
      { a: '1', n: 'onion', s: 'produce' }]
  }
};

const AISLES = [
  { key: 'produce', label: 'produce' },
  { key: 'cupboard', label: 'store cupboard' },
  { key: 'other', label: 'other' }
];

const TITLES = {
  '/food/recipes/a/': 'Aubergine thing',
  '/food/recipes/b/': 'Beetroot cake'
};

/** A food index with everything the scripts read, and nothing else. */
function boot() {
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

  /* THE THREE JSON BLOCKS THE PAGE EMITS. Supplied so the scripts take their
     REAL path rather than their graceful-degradation one -- each warns and
     falls back to nothing when its block is missing, which would quietly test
     a different program from the one that ships. */
  json('ingredient-vocabulary', { search: { family_button_min_chars: 3 } });
  json('recipe-aisles', AISLES);
  json('recipe-ingredients', RECIPES);

  doc.body.appendChild(el('div', 'controls'));

  const list = el('ul', 'recipe-list');
  Object.keys(RECIPES).forEach((url) => {
    const li = el('li', '', {
      'data-url': url, 'data-tags': '', 'data-star': '',
      'data-ingredients': '', 'data-all-ingredients': '|'
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
  doc.body.appendChild(countRow);

  const panel = el('section', 'shopping-list', { id: 'shopping-list' });
  const head = el('div', 'shopping-list-head');
  head.appendChild(el('input', '', { id: 'shopping-list-setall', type: 'number' }));
  panel.appendChild(head);
  panel.appendChild(el('ul', 'shopping-list-recipes'));
  panel.appendChild(el('div', 'shopping-list-aisles'));
  panel.appendChild(el('p', 'shopping-list-empty'));
  doc.body.appendChild(panel);

  const win = {
    document: doc,
    localStorage: createStorage(),
    console: { warn() {}, error() {}, log() {} },
    setTimeout, clearTimeout,
    location: { search: '', pathname: '/food/', hash: '' },
    history: { replaceState() {}, pushState() {} },
    performance: { getEntriesByType: () => [], navigation: { type: 0 } },
    matchMedia: () => ({ matches: false, addEventListener() {} }),
    requestAnimationFrame: (fn) => fn(),
    scrollTo() {},
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

  // filters.js is one big DOMContentLoaded handler; nothing above has run yet.
  doc.dispatch('DOMContentLoaded');

  return { doc, win, panel, list };
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

test('a guessed serving size is marked and a stated one is quoted', () => {
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/a/');
  win.HTF.shortlist.toggle('/food/recipes/b/');
  showTheList(doc);

  const html = recipesHtml(panel);
  assert.ok(html.includes('serves 4'), 'the stated serving size is Helen\'s own words');
  assert.ok(html.includes('~6 portions'),
    'a guessed serving size must carry its tilde -- it is the only thing on '
    + 'the page saying the number came from _data/food/servings.yml.');
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
  // `onion` and `onions` are the same shopping.
  assert.match(html, /<span class="shopping-list-amount">3<\/span>/);
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

/* THE PER-RECIPE INPUTS ARE WRITTEN WITH innerHTML, which this stub stores as
   a string rather than parsing into nodes -- so they cannot be found with
   querySelector and clicked. That costs nothing here: the listener is
   DELEGATED and reads `ev.target`, so a stand-in carrying the three things it
   actually looks at exercises exactly the code the browser would. The markup
   those inputs are built from is asserted above, from the same render. */
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
  // The caret rule: the per-recipe list is rebuilt whole on every shortlist
  // change, but NOT from the input handler, because replacing the node under a
  // typing cursor loses the caret and the keystroke. cocktail-index.js carries
  // the same split for the same reason.
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

test('a shortlisted recipe that is no longer on the page is dropped quietly', () => {
  // A renamed or unpublished recipe, left in localStorage. The same silence
  // the rest of this feature gives one.
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/gone/');
  win.HTF.shortlist.toggle('/food/recipes/a/');
  showTheList(doc);
  assert.ok(!recipesHtml(panel).includes('/food/recipes/gone/'));
  assert.match(aislesHtml(panel), /200 g/);
});

// --- the list of scripts is the template's list --------------------------------

test('this harness loads what food/index.html actually loads', () => {
  // The harness is only worth having if it runs the real program. A tag added
  // to the template and not here means the thing under test drifts away from
  // the thing that ships -- which is how #694 put recipe-list.js on the
  // cocktails index without its harness noticing.
  const html = fs.readFileSync(path.join(ROOT, 'food', 'index.html'), 'utf8');
  const inTemplate = [...html.matchAll(/<script src="\{\{ '\/assets\/js\/([^']+)'/g)]
    .map((m) => m[1]);

  // assets.js is the layout's, not this page's, and is loaded first in both.
  assert.deepStrictEqual(SCRIPTS.slice(1), inTemplate,
    'tests/js/food-index-startup.test.js loads a different set of scripts from '
    + 'food/index.html. Update SCRIPTS to match the template.');
});
