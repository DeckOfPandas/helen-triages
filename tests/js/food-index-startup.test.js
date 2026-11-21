// The food index runs to the end, and its filters and address bar work.
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
// the template.
const SCRIPTS = [
  'assets.js',
  'ingredient-search.js',
  'list-view.js',
  'filter-state.js',
  'filters.js',
  // Wires itself on DOMContentLoaded, after filters.js's handler, and returns
  // at once here: this sandbox has no IntersectionObserver, which is the path
  // a browser without the API takes.
  'results-bar.js'
];

const TITLES = {
  '/food/recipes/a/': 'Aubergine thing',
  '/food/recipes/b/': 'Beetroot cake',
  '/food/recipes/gelato/': 'Blackberry gelato',
  '/food/recipes/cookies/': 'Peanut Butter Cookies'
};
const URLS = Object.keys(TITLES);

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
 * @param {Object} [options] - `search`, `hash`, `backForward`, `beforeStart`
 */
function boot(options) {
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

  /* The JSON block the page emits. Without it the script warns and falls
     back to nothing, which would test a different program from the one that
     ships. */
  json('ingredient-vocabulary', { search: { family_button_min_chars: 3 } });

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
  URLS.forEach((url) => {
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

  return { doc, win, list, results, starSection };
}

// --- the canary ---------------------------------------------------------------

test('the index gets to the end of filters.js', () => {
  const { list } = boot();
  assert.strictEqual(list.style.visibility, 'visible',
    'filters.js threw somewhere before its last few lines, which on the real '
    + 'page is a blank index with nothing in the console anybody will see.');
});

// --- the index only browses (#1521) ----------------------------------------------
// The shortlists have a page of their own: the index has no shortlist view,
// no shared list and no shopping list, and a link that asks for one lands on
// the whole index.

test('?shortlist=1 and a sent list are ignored: every row shows', () => {
  for (const search of ['?shortlist=1', '?shortlist=a,gelato']) {
    const { list } = boot({ search });
    assert.strictEqual(visibleRows(list).length, URLS.length, `${search} narrowed the index`);
  }
});

test('?into= rides through the address bar as the filters change', () => {
  const written = [];
  const { doc } = boot({
    search: '?into=l3',
    beforeStart: (win) => { win.history.replaceState = (s, t, url) => written.push(url); }
  });
  typeIngredient(doc, 'aubergines');
  assert.ok(written.length, 'choosing a filter wrote nothing to the address bar');
  assert.match(written[written.length - 1], /into=l3/,
    'the list being filled dropped out of the address: a reload would leave the mode');
});

test('the count paints its number and its word into separate spans', () => {
  // The digits take `.results-count-number` and the word stays bare; the
  // outer element still reads "N recipes", which is the word until a filter
  // narrows the list (#1462 A3).
  const { doc } = boot();
  assert.strictEqual(doc.getElementById('recipe-count-n').textContent, '4');
  assert.strictEqual(doc.getElementById('recipe-count-word').textContent, 'recipes');
  assert.strictEqual(doc.getElementById('recipe-count').textContent, '4 recipes');
});

function visibleRows(list) {
  return list.children.filter((li) => !li.hidden && li.style.display !== 'none');
}

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
  assert.strictEqual(doc.getElementById('recipe-count-word').textContent.replace(/s$/, ''), 'survivor',
    'a name search narrows the list, so the count says survivors (#1462 A3)');
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
  assert.strictEqual(visibleRows(list).length, URLS.length,
    'nothing was chosen, so nothing should be narrowing the list.');
});

// --- arriving at a fragment, #1057 and #1059 ------------------------------------
// The startup block scrolls to any element id `location.hash` names, not only
// "results": #1057 (a search result) and #1059 (a badge's own filter-section
// fragment) both rely on that.

test('#1050/#1057: arriving at #results scrolls the count line into view', () => {
  const { results } = boot({ hash: '#results' });
  assert.strictEqual(results._scrollCalls.length, 1,
    'the startup block must scroll to location.hash again after the reveal, ' +
    'the landing a search result relies on.');
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
        order: URLS,
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

// --- the address bar follows the filters, #1462 C3 ----------------------------
// What is chosen is written into the query, so a reload or a copied link shows
// the same list. replaceState is recorded and moves the stub's location, as a
// browser's does.

function recordAddressBar(win) {
  const urls = [];
  win.history.replaceState = (stateArg, title, url) => {
    urls.push(url);
    const q = url.indexOf('?');
    const h = url.indexOf('#');
    win.location.search = q === -1 ? '' : url.slice(q, h === -1 ? undefined : h);
  };
  return urls;
}

test('#1462 C3: choosing an ingredient writes it into the address bar', () => {
  let urls;
  const { doc } = boot({ beforeStart: (win) => { urls = recordAddressBar(win); } });
  typeIngredient(doc, 'aubergines');
  assert.strictEqual(urls[urls.length - 1], '/food/?ing=aubergines');
  typeIngredient(doc, 'olive oil');
  assert.strictEqual(urls[urls.length - 1], '/food/?ing=aubergines,olive%20oil',
    'a second HAS TO HAVE joins the first in the link, as it does in the filter.');
});

test('#1462 C3: what the address bar wrote is what a fresh load reads back', () => {
  const { doc, list } = boot({ search: '?ing=aubergines,olive%20oil' });
  assert.deepStrictEqual(visibleRows(list).map((li) => li.getAttribute('data-url')),
    ['/food/recipes/a/']);
  const active = Array.from(
    doc.getElementById('ingredient-results-pool').querySelectorAll('.btn-ingredient.active')
  ).map((b) => b.dataset.ingredient).sort();
  assert.deepStrictEqual(active, ['aubergines', 'olive oil'],
    'every ingredient in the link is chosen, not only the last one.');
});

test('#1462 C3: startup reads the whole query before anything rewrites it', () => {
  // Choosing the ingredient runs update(); were the address bar live by then,
  // it would drop `q` before the name search had read it.
  let urls;
  const { doc } = boot({
    search: '?ing=beetroot&q=beetroot',
    beforeStart: (win) => { urls = recordAddressBar(win); }
  });
  assert.strictEqual(doc.getElementById('name-search-box').value, 'beetroot');
  assert.strictEqual(urls[urls.length - 1] || '/food/?ing=beetroot&q=beetroot',
    '/food/?ing=beetroot&q=beetroot');
});

test('#1462 C3: clearing everything empties the query and keeps the fragment', () => {
  let urls;
  const { doc } = boot({
    search: '?ing=beetroot', hash: '#results',
    beforeStart: (win) => { urls = recordAddressBar(win); }
  });
  // The clear-all is the pill's ×, which this harness has not built, so the
  // chip is clicked off instead: the query goes with the last filter.
  doc.getElementById('ingredient-results-pool').querySelector('.btn-ingredient.active').dispatch('click');
  assert.strictEqual(urls[urls.length - 1], '/food/#results');
});
