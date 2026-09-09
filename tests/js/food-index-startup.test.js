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
  'filters.js',
  // #849. Nobody's dependency: it reads HTF.shortlist at run time rather than
  // lifting helpers off another module at startup, and it subscribes to
  // `htf:shortlist-change` rather than being called. Listed anyway because the
  // test at the foot of this file asserts this array IS the template's script
  // list -- which is the point of that test, and is what caught its absence.
  'shortlist-export.js'
];

/* Two recipes and the panel, hand-built rather than sliced out of a real build:
   a fixture you can read in one screen is what makes a failure diagnosable, and
   the alternative drags a megabyte of markup into the repo.

   `b` IS THE GUESSED ONE (`e: true`), because the tilde on a guessed serving
   size is the only thing on the page saying a number is this repo's rather
   than Helen's. */
const RECIPES = {
  '/food/recipes/a/': {
    p: 4, e: false, y: '4', k: 'serves',
    i: [{ a: '200 g', n: 'plain flour', s: 'cupboard' },
      { a: '2', n: 'onions', s: 'produce' },
      { a: '', n: 'olive oil', s: 'cupboard' }]
  },
  '/food/recipes/b/': {
    p: 6, e: true, y: 'one 8-inch cake', k: 'makes',
    i: [{ a: '300 g', n: 'plain flour', s: 'cupboard' },
      { a: '1', n: 'onion', s: 'produce' }]
  },
  /* THE ESTIMATED ONE. `henrys-blackberry-gelato-sicilian-style` says
     `makes: "About 750 ml"` and no `serves:`, so its number comes from
     `serves_estimate:` and is flagged -- it prints with a `~`. This fixture
     had `p: null` for a fortnight, when such a recipe got a batch box; #815
     gave every recipe a count and the batch box went. */
  '/food/recipes/gelato/': {
    p: 6, e: true, y: 'About 750 ml', k: 'makes',
    i: [{ a: '125 ml', n: 'whipping cream', s: 'dairy' },
      { a: '500 ml', n: 'whole milk', s: 'dairy' }]
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
  '/food/recipes/gelato/': 'Blackberry gelato'
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

  /* THE THREE JSON BLOCKS THE PAGE EMITS. Supplied so the scripts take their
     REAL path rather than their graceful-degradation one -- each warns and
     falls back to nothing when its block is missing, which would quietly test
     a different program from the one that ships. */
  json('ingredient-vocabulary', { search: { family_button_min_chars: 3 } });
  json('recipe-aisles', AISLES);
  json('recipe-ingredients', recipes);

  doc.body.appendChild(el('div', 'controls'));

  const list = el('ul', 'recipe-list');
  Object.keys(recipes).forEach((url) => {
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

test('the yield is on the control, never printed beside the name', () => {
  /* Helen, 2026-09-07, with a screenshot of `7  Moules Marinière serves 4`:
     "This screenshot makes it look like I'm asking for 28 portions of
     mussels." A number at each end of a short line reads as one expression,
     so the yield moved into the input rather than being dimmed further. */
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
  assert.ok(html.includes('which ~6 portions') || html.includes('~6 portions'),
    'a guessed serving size must still carry its tilde somewhere -- it is the '
    + 'only thing saying the number came from _data/food/servings.yml.');
  assert.ok(html.includes('title='), 'the yield is reachable on hover');
});

test('the visible row is the number and the name, and nothing else', () => {
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/a/');
  showTheList(doc);
  // The text between the closing input and the end of the row: name only.
  const visible = recipesHtml(panel).replace(/<[^>]*>/g, '').trim();
  assert.strictEqual(visible, 'Aubergine thing');
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

// --- a recipe whose yield is not stated in people -----------------------------
// Helen, 2026-09-07: "Changing the amount of blackberry gelato I want doesn't
// change anything (that I can see) in the shopping list -- e.g. whipping cream
// is always 125 ml." Then, on the batch box that answered it: "clearly 750 ml
// of gelato doesn't feed 50."
//
// So every recipe carries a portion count now (#815) and there is one kind of
// number in this panel. These are the tests that the estimated ones behave
// exactly like the stated ones, and are still marked as estimates.

test('THE BOX ON A `makes:` RECIPE ACTUALLY CHANGES THE TOTALS', () => {
  // The original regression: the control rendered, accepted a number, and
  // silently scaled by 1.
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/gelato/');
  showTheList(doc);
  assert.match(aislesHtml(panel), /125 ml/, 'its estimate of 6, to begin with');

  panel.querySelector('.shopping-list-recipes')
    .dispatch('input', { target: typedInto('/food/recipes/gelato/', 12) });

  assert.match(aislesHtml(panel), /250 ml/,
    'twelve portions of a recipe estimated at six is twice the cream. This is '
    + 'the bug Helen reported: the box did nothing at all.');
});

test('an estimated recipe starts at its estimate, like a stated one', () => {
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/gelato/');
  showTheList(doc);
  assert.match(recipesHtml(panel), /value="6" data-url="\/food\/recipes\/gelato\//);
});

test('there is one kind of number in the panel -- no batch mark anywhere', () => {
  // `.shopping-list-times` and `.shopping-list-batch-note` were the batch
  // box's furniture. #815 removed the box; this is the guard that they do not
  // come back with it.
  const { win, doc, panel } = boot();
  Object.keys(RECIPES).forEach((url) => win.HTF.shortlist.toggle(url));
  showTheList(doc);
  assert.ok(!recipesHtml(panel).includes('shopping-list-times'));
  assert.ok(!recipesHtml(panel).includes('×'));
  Object.keys(RECIPES).forEach((url) => {
    assert.ok(recipesHtml(panel).includes('aria-label="portions of '
      + TITLES[url]), url);
  });
});

test('an estimate is marked with a ~ and a stated serving size is not', () => {
  // Helen's ruling, #815: "yes, mark an estimate on the scaler with a ~". It
  // is the only thing saying a figure was reasoned rather than written down.
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/a/');       // serves: "4"
  win.HTF.shortlist.toggle('/food/recipes/gelato/');  // serves_estimate: 6
  showTheList(doc);

  const html = recipesHtml(panel);
  assert.ok(html.includes('~6 portions'), 'the estimate carries its tilde');
  assert.ok(html.includes('which serves 4'), 'the stated one is quoted');
  assert.ok(!html.includes('~4'), 'a stated serving size is never marked');
});

test('a `makes:` value is never printed behind the word "serves"', () => {
  // It read "serves About 750 ml" until 2026-09-07, because the blob carried
  // the yield text without saying which key it came from. `k` fixed that, and
  // an estimated recipe prints its ~ figure instead of either.
  const { win, doc, panel } = boot();
  win.HTF.shortlist.toggle('/food/recipes/gelato/');
  showTheList(doc);
  assert.ok(!recipesHtml(panel).includes('serves About 750 ml'));
});

test('"set all to" now reaches every shortlisted recipe', () => {
  // It skipped the batch ones, which is what Helen hit: "the set all to X
  // portions input field doesn't change the input field for blackberry
  // gelato". There is nothing left to skip.
  const { win, doc, panel } = boot();
  Object.keys(RECIPES).forEach((url) => win.HTF.shortlist.toggle(url));
  showTheList(doc);

  const setAll = doc.getElementById('shopping-list-setall');
  setAll.value = '12';
  setAll.dispatch('input');

  Object.keys(RECIPES).forEach((url) => {
    assert.strictEqual(win.HTF.shortlist.portions(url), 12, url);
  });
  // a: 200 g x3, b: 300 g x2, so the flour is 600 + 600.
  assert.match(aislesHtml(panel), /1\.2 kg/);
});

test('A STORED NUMBER CANNOT RESURRECT A BOX THE RECIPE CANNOT SUPPORT', () => {
  /* Helen, 2026-09-07, with a screenshot: the gelato's box read 200 and the
     list did not move, while the cheesecake beside it scaled to ⅝ of an egg.

     THE GUARD WAS ASKING THE WRONG QUESTION. `portionsFor()` returned the
     STORED number before it looked at the recipe, so a figure she had typed
     earlier -- kept in localStorage, and outliving the recipe's own data --
     made the "no portion count, no box" test pass for a recipe that had none.
     A box was drawn, it accepted 200, and scaleFor() silently returned 1.

     THE SAME BUG AS THE FIRST ONE, through a different door, which is why this
     test asks about the STORE rather than about the render: her machine had a
     value in it, and mine did not. */
  const { win, doc, panel } = boot({
    recipes: {
      '/food/recipes/a/': {
        p: null, e: false, y: 'About 750 ml', k: 'makes',
        i: [{ a: '125 ml', n: 'whipping cream', s: 'cupboard' }]
      }
    }
  });
  // What she had typed before the recipe lost (or never had) its count.
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
  /* Every recipe carries one since #815 and a test keeps it that way, so this
     is what a NEW recipe looks like between being written and being given its
     `serves_estimate:`. It contributes at x1 and says what is missing, rather
     than offering a control that would do nothing -- the rule this feature
     broke twice before learning it. */
  const { win, doc, panel } = boot({
    recipes: {
      '/food/recipes/a/': {
        p: null, e: false, y: 'a big tray', k: 'makes',
        i: [{ a: '200 g', n: 'plain flour', s: 'cupboard' }]
      }
    }
  });
  win.HTF.shortlist.toggle('/food/recipes/a/');
  showTheList(doc);

  const html = recipesHtml(panel);
  assert.ok(!html.includes('<input'), 'no control that cannot work');
  assert.match(html, /no serving size/);
  assert.match(html, /serves_estimate/, 'the note names the key to add');
  // Its ingredients still count, at the recipe as written.
  assert.match(aislesHtml(panel), /200 g/);
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
