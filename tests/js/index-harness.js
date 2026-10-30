// Loads the real index scripts, in the real order, against a stub DOM (#633).
// Not a test file: `node --test` only discovers *.test.js.
//
// The point is the wiring, so the scripts are the actual files, attaching to
// the same `window.HTF` namespace by the UMD branch they use in a browser.
// The DOM and the storage are stand-ins.
//
// `vm.runInContext`, not require(): each file is an IIFE closing over
// `window`, and require() would take the `module.exports` branch instead,
// which is not the path a browser runs.
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const { createDocument, createStorage, Element } = require('./dom-stub.js');

const JS_DIR = path.join(__dirname, '..', '..', 'assets', 'js');

// The order cocktails/index.html loads them, plus assets.js from the layout.
// A test asserts this list still matches the template.
const PAGE_SCRIPTS = [
  'assets.js',
  // #694: cocktail-index.js calls HTF.listView.paginate, and without this the
  // script throws on its first apply().
  'list-view.js',
  'ingredient-search.js',
  'filter-state.js',
  'cocktail-search.js',
  'shopping-list.js',
  'cocktail-index.js',
  // Wires itself on DOMContentLoaded, which this harness never dispatches, so
  // here it only has to load without throwing. tests/js/results-bar.test.js
  // drives it against its own fixture.
  'results-bar.js',
  // #849. Nobody's dependency; here because cocktail-index-startup.test.js
  // asserts this list is the template's. It loads after universe.js on the
  // page, and universe.js is filtered out of that comparison.
  'shortlist-export.js',
  // #1440. Nobody's dependency either. The stub page has no `#ship-key`, so
  // here it returns at its first line.
  'ship-key.js'
];

// The two card measurement passes, from the shared layout (#1107).
// `_layouts/default.html` loads them for both sites, below `{{ content }}`, so
// they run after every script above, the name fit first: the name decides how
// much room the ingredients get, and the ingredients how much the chips get.
//
// A separate list, because the drift test for PAGE_SCRIPTS reads
// `cocktails/index.html` and these two are not in it. The layout's order is
// pinned by its own test in cocktail-index-startup.test.js.
const LAYOUT_SCRIPTS = [
  'card-name-fit.js',
  'card-line-budget.js'
];

const SCRIPTS = PAGE_SCRIPTS.concat(LAYOUT_SCRIPTS);

/* A small cocktails index, hand-built and readable in one screen. The panel's
   vocabulary is overridable: a mood with no button in the panel cannot be
   clicked, so a test about chip order supplies the moods its drink carries. */
const DEFAULT_MOODS = ['sharp', 'aperitivo'];
const DEFAULT_HASSLES = ['no juicing'];

function buildPage(doc, options) {
  options = options || {};
  const moodWords = options.moods || DEFAULT_MOODS;
  const hassleWords = options.hassles || DEFAULT_HASSLES;
  const el = (tag, cls, attrs) => {
    const node = doc.createElement(tag);
    if (cls) node.setAttribute('class', cls);
    Object.entries(attrs || {}).forEach(([k, v]) => node.setAttribute(k, v));
    return node;
  };

  /* The JSON blocks the page emits, and the base-url meta. Without a block
     its script warns and falls back to an empty vocabulary, which would test
     a different program from the one that ships. Minimal, but the right
     shape. */
  const meta = el('meta', '', { name: 'base-url', content: '' });
  doc.body.appendChild(meta);

  const json = (id, value) => {
    const node = el('script', '', { id: id, type: 'application/json' });
    node.textContent = JSON.stringify(value);
    doc.body.appendChild(node);
  };

  /* Overridable (#1130): a test about a chip needs the vocabulary to declare
     that chip. `cocktail-search.js` treats every list-valued key here as a
     generic vocabulary (bar `families` and `*_characters`). */
  json('drink-vocabulary', Object.assign({
    search: { family_button_min_chars: 3 },
    families: ['rum'],
    family_of: { 'lightly aged and filtered rum': 'rum' },
    card_names: { 'lightly aged and filtered rum': 'lightly aged rum' }
  }, options.vocabulary || {}));
  json('drink-bottles', { bottles: {} });
  json('drink-ingredients', {});
  /* #746. cocktails/index.html emits this ungated, unlike the local-only
     `drink-costs`, so a page without it is an anomaly and `readJson` warns.
     The fixture carries the real rows. */
  json('drink-top-ups', {
    champagne: { ml_min: 75, ml_max: 100 },
    prosecco: { ml_min: 75, ml_max: 100 },
    'soda water': { ml_min: 100, ml_max: 150 }
  });

  const filters = el('div', 'drink-filters');
  doc.body.appendChild(filters);

  // YOLO
  const chaos = el('div', 'drink-filter drink-filter--chaos');
  filters.appendChild(chaos);
  ['good', 'open', 'chaos'].forEach((v) => {
    chaos.appendChild(el('button', 'btn-chaos', { 'data-chaos': v, type: 'button' }));
  });
  chaos.appendChild(el('button', 'btn-clear-filter', { id: 'clear-chaos' }));

  // MOOD and HASSLE: two sections, one state.moods behind them (#695).
  // `filter-mood` and `filter-hassle` are the page's real ids (#1059): a test
  // of which section the scroll lands on needs them.
  const mood = el('div', 'drink-filter drink-filter--mood', { id: 'filter-mood' });
  filters.appendChild(mood);
  moodWords.forEach((m) => {
    mood.appendChild(el('button', 'btn-mood', { 'data-mood': m, type: 'button' }));
  });
  mood.appendChild(el('button', 'btn-clear-filter', { id: 'clear-mood' }));

  const hassle = el('div', 'drink-filter drink-filter--hassle', { id: 'filter-hassle' });
  filters.appendChild(hassle);
  hassleWords.forEach((m) => {
    hassle.appendChild(el('button', 'btn-mood', { 'data-mood': m, type: 'button' }));
  });
  hassle.appendChild(el('button', 'btn-clear-filter', { id: 'clear-hassle' }));

  /* The two search boxes, with the page's own ids. The script reaches for
     `drink-include` / `drink-include-pool` by id, and a fixture that spells
     them differently exercises the null-guard path instead of the real one.
     A test asserts every id the script asks for is in this fixture. */
  [['include', 'drink-include'], ['exclude', 'drink-exclude']].forEach(
    ([kind, id]) => {
      const box = el('div', 'drink-search drink-search--' + kind);
      filters.appendChild(box);
      box.appendChild(el('input', 'drink-search-input', { id: id }));
      box.appendChild(el('div', 'btn-pool-row', { id: id + '-pool' }));
      box.appendChild(el('button', 'btn-clear-filter', { id: 'clear-' + kind }));
    }
  );

  filters.appendChild(el('input', 'drink-search-input', { id: 'drink-name' }));
  filters.appendChild(el('button', 'btn-clear-filter', { id: 'clear-name' }));

  doc.body.appendChild(el('p', 'drink-none'));
  // The count line carries `id="results"` (#1050), where a search result
  // lands; the script scrolls there after apply().
  const count = el('p', 'drink-count', { id: 'results' });
  count.appendChild(el('span', '', { id: 'drink-count-n' }));
  count.appendChild(el('span', '', { id: 'drink-count-word' }));
  doc.body.appendChild(count);
  // The ship legend and its clear (#1412), beside the count on the page.
  const legend = el('span', 'drink-count-legend');
  const legendValue = el('span', 'drink-count-legend-value', { 'data-ship-legend-value': '' });
  legendValue.appendChild(el('span', '', { 'data-ship-legend-word': '' }));
  legend.appendChild(legendValue);
  doc.body.appendChild(legend);
  doc.body.appendChild(el('button', 'btn-shortlist-only', { id: 'shortlist-only' }));
  doc.body.appendChild(el('button', 'btn-clear-filter', { id: 'clear-ship' }));
  // The results pill's ×, the page's one clear-all (#1448), which
  // cocktail-index.js adopts by this attribute.
  doc.body.appendChild(el('button', 'results-pill-clear', { 'data-results-pill-clear': '' }));

  const list = el('ul', 'drink-cards');
  doc.body.appendChild(list);

  // Pagination (#694). `style.display` rather than `hidden`, matching the
  // template -- the script sets the property, so the fixture must offer the
  // same mechanism or the visibility assertions test nothing.
  const pager = el('div', 'drink-pagination');
  pager.style.display = 'none';
  const nav = el('div', 'drink-pagination-nav');
  nav.appendChild(el('button', 'btn-page', { id: 'drink-page-prev' }));
  nav.appendChild(el('span', '', { id: 'drink-page-status' }));
  nav.appendChild(el('button', 'btn-page', { id: 'drink-page-next' }));
  pager.appendChild(nav);
  pager.appendChild(el('button', 'btn-page btn-page-see-all', { id: 'drink-page-see-all' }));
  doc.body.appendChild(pager);

  return { filters, list, pager, el, mood, hassle, count };
}

function addCard(doc, list, spec) {
  const card = doc.createElement('li');
  card.setAttribute('class', 'drink-card');
  card.setAttribute('data-url', spec.url);
  card.setAttribute('data-name', spec.name);
  card.setAttribute('data-moods', (spec.moods || []).join('|') + '|');
  card.setAttribute('data-chaos', spec.chaos || 'good');
  card.setAttribute('data-ship', spec.ship || 'meh');
  card.setAttribute('data-ingredients', (spec.ingredients || []).join('|'));

  /* The page's real shape: cocktails/index.html emits
     `.drink-card-name > .drink-card-tape-word > a`, and card-name-fit.js
     queries `.drink-card-tape-word` (#1107). `.drink-card-name a` still
     matches, for anything that reads the title. */
  const nameP = doc.createElement('p');
  nameP.setAttribute('class', 'drink-card-name');
  const word = doc.createElement('span');
  word.setAttribute('class', 'drink-card-tape-word');
  const a = doc.createElement('a');
  a.textContent = spec.title;
  word.appendChild(a);
  nameP.appendChild(word);
  card.appendChild(nameP);
  if (spec.name_box) {
    word.__box = spec.name_box;
    /* The one piece of modelling in this fixture. card-name-fit.js steps the
       type down and then re-measures, and a stub returning the same width
       before and after can never take the step path. `contentWidthStepped`
       is what the lettering measures once `--step` is on; this reads it back
       through the class the pass itself set. Omit it and the width does not
       change: a step that did not help. */
    Object.defineProperty(word, '__contentWidth', {
      get() {
        const stepped = nameP.classList.contains('drink-card-name--step');
        if (stepped && spec.name_box.contentWidthStepped !== undefined) {
          return spec.name_box.contentWidthStepped;
        }
        return spec.name_box.contentWidth || 0;
      }
    });
  }

  const ings = doc.createElement('p');
  ings.setAttribute('class', 'drink-card-ingredients');
  (spec.ingredients || []).forEach((entry) => {
    const s = doc.createElement('span');
    s.setAttribute('class', 'drink-card-ing');
    s.setAttribute('data-ing', entry);
    s.textContent = entry;
    ings.appendChild(s);
  });
  card.appendChild(ings);
  // #1107: what card-line-budget.js divides by its line height.
  if (spec.ingredients_box) ings.__box = spec.ingredients_box;

  /* The foot's real shape: a `.drink-card-moods` wrapper and a
     `.drink-card-ship` beside it, which is what cocktails/index.html emits
     and _cards.scss lays out as one flex row (#552). A fixture that
     simplifies the page finds nothing where the page has something. */
  const foot = doc.createElement('div');
  foot.setAttribute('class', 'drink-card-foot');

  const moods = doc.createElement('span');
  moods.setAttribute('class', 'drink-card-moods');
  (spec.moods || []).forEach((m, i) => {
    const chip = doc.createElement('button');
    chip.setAttribute('class', 'drink-card-mood');
    chip.setAttribute('data-mood', m);
    chip.textContent = m;
    /* #1107: `chip_boxes[i]` is where this chip sits, so a test can put one on
       the ship's row and past its left edge, the collision
       card-line-budget.js measures. */
    if (spec.chip_boxes && spec.chip_boxes[i]) chip.__box = spec.chip_boxes[i];
    if ((spec.matched_moods || []).indexOf(m) !== -1) {
      chip.classList.add('is-match');
    }
    moods.appendChild(chip);
  });
  foot.appendChild(moods);

  /* A <button> carrying its value, as on the page (#1412); the word is the
     card's spelling, `ship_word` where a test needs it to differ. */
  const ship = doc.createElement('button');
  ship.setAttribute('class', 'drink-card-ship');
  ship.setAttribute('data-ship', spec.ship || 'meh');
  const shipWord = doc.createElement('span');
  shipWord.setAttribute('class', 'drink-card-ship-word');
  shipWord.textContent = spec.ship_word || spec.ship || 'meh';
  ship.appendChild(shipWord);
  if (spec.ship_box) ship.__box = spec.ship_box;
  foot.appendChild(ship);

  card.appendChild(foot);

  list.appendChild(card);
  return card;
}

/* Build a page, run the scripts over it, hand back everything a test needs.
   `throwOnError: false` lets a test assert the crash rather than inherit it. */
function boot(options) {
  options = options || {};
  const doc = createDocument();
  const page = buildPage(doc, options);
  (options.drinks || []).forEach((d) => addCard(doc, page.list, d));

  const errors = [];
  const sandbox = {
    document: doc,
    localStorage: createStorage(options.storage),
    // HTF.indexMemory (assets.js) reads and writes sessionStorage for the
    // back-navigation restore and treats a missing one as a fresh load (#387),
    // so a restore is testable only with this.
    sessionStorage: createStorage(options.sessionStorage),
    location: {
      search: options.search || '',
      pathname: '/cocktails/',
      href: 'http://x/cocktails/',
      hash: options.hash || ''
    },
    history: { replaceState() {}, pushState() {} },
    console: { log() {}, warn(...a) { errors.push(a.join(' ')); }, error(...a) { errors.push(a.join(' ')); } },
    setTimeout: (fn) => fn(),
    clearTimeout() {},
    requestAnimationFrame: (fn) => fn(),
    // `options.backForward`: FilterState.arrivedByGoingBack reads this shape.
    // Without it every boot() is a fresh visit (#387, #1057).
    performance: {
      now: () => 0,
      getEntriesByType: () => (options.backForward ? [{ type: 'back_forward' }] : [])
    },
    Math: Math,
    Date: Date,
    JSON: JSON,
    Set: Set,
    Map: Map,
    Array: Array,
    Object: Object,
    String: String,
    Number: Number,
    Boolean: Boolean,
    RegExp: RegExp,
    Error: Error,
    parseInt: parseInt,
    parseFloat: parseFloat,
    isNaN: isNaN,
    encodeURIComponent: encodeURIComponent,
    decodeURIComponent: decodeURIComponent
  };
  sandbox.window = sandbox;
  sandbox.self = sandbox;
  sandbox.globalThis = sandbox;
  doc.defaultView = sandbox;
  sandbox.window.scrollY = 0;
  sandbox.window.scrollTo = () => {};
  sandbox.window.addEventListener = (type, fn) => {
    (doc.listeners[type] = doc.listeners[type] || []).push(fn);
  };

  /* #1107. card-line-budget.js asks for `lineHeight` and, when that is
     `normal`, `fontSize`. Both come off the element's own `__computed`, which
     a test sets; the defaults are the stylesheet's values (`_cards.scss`:
     0.82rem at line-height 1.5, 16px root). Nothing here computes style;
     dom-stub.js says why it must not. */
  sandbox.window.getComputedStyle = (el) => {
    const c = (el && el.__computed) || {};
    return {
      lineHeight: c.lineHeight === undefined ? '19.68px' : c.lineHeight,
      fontSize: c.fontSize === undefined ? '13.12px' : c.fontSize
    };
  };

  const context = vm.createContext(sandbox);
  const loaded = [];
  let thrown = null;

  /* `skip` leaves a script unloaded so a test can run its own version of it
     in a context the others have already populated. */
  const skip = options.skip || [];

  for (const name of SCRIPTS) {
    if (skip.indexOf(name) !== -1) continue;
    const src = fs.readFileSync(path.join(JS_DIR, name), 'utf8');
    try {
      vm.runInContext(src, context, { filename: name });
      loaded.push(name);
    } catch (e) {
      thrown = { script: name, error: e };
      if (options.throwOnError !== false) throw e;
      break;
    }
  }

  return { doc, page, sandbox, errors, loaded, thrown, SCRIPTS: SCRIPTS.slice() };
}

module.exports = {
  boot, buildPage, addCard, SCRIPTS, PAGE_SCRIPTS, LAYOUT_SCRIPTS, Element
};
