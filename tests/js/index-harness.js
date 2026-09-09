// =============================================================================
// Load the REAL index scripts, in the REAL order, against a stub DOM. Issue #633.
// Not a test file — `node --test` only discovers *.test.js.
// =============================================================================
// THE POINT IS THE WIRING, so nothing here is mocked that the page does not
// mock. `ingredient-search.js`, `filter-state.js`, `cocktail-search.js`,
// `shopping-list.js` and `assets.js` are the actual files, run in the actual
// order cocktails/index.html loads them, attaching to the same `window.HTF`
// namespace by the same UMD branch they use in a browser. Only the DOM and
// localStorage are stand-ins.
//
// `vm.runInNewContext` RATHER THAN require(), because these files are not
// modules in the browser and the browser path is the one that breaks. Each is
// an IIFE closing over `window`; `require()` would take the `module.exports`
// branch instead and test a door nobody walks through.
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const { createDocument, createStorage, Element } = require('./dom-stub.js');

const JS_DIR = path.join(__dirname, '..', '..', 'assets', 'js');

// The order cocktails/index.html loads them, plus assets.js from the layout.
// A test asserts this list still matches the template.
const SCRIPTS = [
  'assets.js',
  // #694 put `recipe-list.js` on this page: cocktail-index.js calls
  // HTF.recipeList.paginate, and without it the script throws on its first
  // apply(). THIS HARNESS CAUGHT THAT, which is the plainest demonstration of
  // why it exists -- every other test stayed green while the index was dead.
  'recipe-list.js',
  'ingredient-search.js',
  'filter-state.js',
  'cocktail-search.js',
  'shopping-list.js',
  'cocktail-index.js',
  // #849. Nobody's dependency -- it reads HTF.shortlist at run time rather than
  // lifting helpers off another module at startup, and it subscribes to
  // `htf:shortlist-change` rather than being called. It is here because the
  // test at the foot of cocktail-index-startup.test.js asserts this list IS the
  // template's, which is the point of that test and is what caught its absence.
  // It loads AFTER universe.js on the page; universe.js is filtered out of the
  // comparison, so this sits last in both.
  'shortlist-export.js'
];

/* A small cocktails index: two drinks, two mood sections, the YOLO row and the
   list. Deliberately hand-built rather than sliced out of a real build -- a
   fixture you can read in one screen is what makes a failure diagnosable, and
   the alternative drags 1MB of markup into the repo. */
/* THE PANEL'S OWN VOCABULARY, overridable. It defaults to the three moods most
   tests need; a test about chip ORDER needs buttons for the moods its drink
   carries, because a mood with no button in the panel cannot be clicked and the
   test would be asserting about a filter nobody can set. */
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

  /* THE THREE JSON BLOCKS THE PAGE EMITS, and the base-url meta. Supplied so
     the scripts take their REAL path rather than their graceful-degradation
     one -- each warns and falls back to an empty vocabulary when its block is
     missing, which would quietly test a different program from the one that
     ships. Minimal, but the right SHAPE: what a shape has to be is the kind of
     thing this harness exists to catch. */
  const meta = el('meta', '', { name: 'base-url', content: '' });
  doc.body.appendChild(meta);

  const json = (id, value) => {
    const node = el('script', '', { id: id, type: 'application/json' });
    node.textContent = JSON.stringify(value);
    doc.body.appendChild(node);
  };

  json('drink-vocabulary', {
    search: { family_button_min_chars: 3 },
    families: ['rum'],
    family_of: { 'lightly aged and filtered rum': 'rum' },
    card_names: { 'lightly aged and filtered rum': 'lightly aged rum' }
  });
  json('drink-bottles', { bottles: {} });
  json('drink-ingredients', {});
  /* #746. Emitted UNGATED by cocktails/index.html — unlike `drink-costs`, which
     is local-only and whose absence is normal — so a page without it is a real
     anomaly and `readJson` is right to warn. This fixture carries the real
     three rows so the harness runs the same program the page does. */
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
  ['good', 'open'].forEach((v) => {
    chaos.appendChild(el('button', 'btn-chaos', { 'data-chaos': v, type: 'button' }));
  });
  chaos.appendChild(el('button', 'btn-clear-filter', { id: 'clear-chaos' }));

  // MOOD and HASSLE: two sections, one state.moods behind them (#695).
  const mood = el('div', 'drink-filter drink-filter--mood');
  filters.appendChild(mood);
  moodWords.forEach((m) => {
    mood.appendChild(el('button', 'btn-mood', { 'data-mood': m, type: 'button' }));
  });
  mood.appendChild(el('button', 'btn-clear-filter', { id: 'clear-mood' }));

  const hassle = el('div', 'drink-filter drink-filter--hassle');
  filters.appendChild(hassle);
  hassleWords.forEach((m) => {
    hassle.appendChild(el('button', 'btn-mood', { 'data-mood': m, type: 'button' }));
  });
  hassle.appendChild(el('button', 'btn-clear-filter', { id: 'clear-hassle' }));

  /* THE TWO SEARCH BOXES, WITH THE PAGE'S OWN IDS. They matter: the script
     reaches for `drink-include` / `drink-include-pool` by id, and a fixture
     that spells them differently silently exercises the null-guard path
     instead of the real one -- which is the same class of quiet miss #633 is
     about. Taken from cocktails/index.html, and a test asserts they still
     match it. */
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
  doc.body.appendChild(el('span', '', { id: 'drink-count-n' }));
  doc.body.appendChild(el('span', '', { id: 'drink-count-word' }));
  doc.body.appendChild(el('button', 'btn-shortlist-only', { id: 'shortlist-only' }));

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

  return { filters, list, pager, el };
}

function addCard(doc, list, spec) {
  const card = doc.createElement('li');
  card.setAttribute('class', 'drink-card');
  card.setAttribute('data-url', spec.url);
  card.setAttribute('data-name', spec.name);
  card.setAttribute('data-moods', (spec.moods || []).join('|') + '|');
  card.setAttribute('data-chaos', spec.chaos || 'good');
  card.setAttribute('data-made-before', spec.madeBefore === false ? 'false' : 'true');
  card.setAttribute('data-ingredients', (spec.ingredients || []).join('|'));

  const nameP = doc.createElement('p');
  nameP.setAttribute('class', 'drink-card-name');
  const a = doc.createElement('a');
  a.textContent = spec.title;
  nameP.appendChild(a);
  card.appendChild(nameP);

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

  /* THE FOOT'S REAL SHAPE: a `.drink-card-moods` wrapper and a
     `.drink-card-ship` beside it, which is what cocktails/index.html emits and
     what _cards.scss lays out as one flex row (#552). The chips used to be
     direct children of the foot here, and a test asking for
     `.drink-card-moods` found nothing -- a fixture that is a simplification of
     the page rather than a copy of it, which is the failure mode this whole
     harness exists to avoid. */
  const foot = doc.createElement('div');
  foot.setAttribute('class', 'drink-card-foot');

  const moods = doc.createElement('span');
  moods.setAttribute('class', 'drink-card-moods');
  (spec.moods || []).forEach((m) => {
    const chip = doc.createElement('button');
    chip.setAttribute('class', 'drink-card-mood');
    chip.setAttribute('data-mood', m);
    chip.textContent = m;
    moods.appendChild(chip);
  });
  foot.appendChild(moods);

  const ship = doc.createElement('span');
  ship.setAttribute('class', 'drink-card-ship');
  ship.textContent = spec.ship || 'meh';
  foot.appendChild(ship);

  card.appendChild(foot);

  list.appendChild(card);
  return card;
}

/* Build a page, run the five scripts over it, hand back everything a test
   needs. `throwOnError: false` lets a test assert the CRASH rather than
   inherit it. */
function boot(options) {
  options = options || {};
  const doc = createDocument();
  const page = buildPage(doc, options);
  (options.drinks || []).forEach((d) => addCard(doc, page.list, d));

  const errors = [];
  const sandbox = {
    document: doc,
    localStorage: createStorage(options.storage),
    location: { search: options.search || '', pathname: '/cocktails/', href: 'http://x/cocktails/' },
    history: { replaceState() {}, pushState() {} },
    console: { log() {}, warn(...a) { errors.push(a.join(' ')); }, error(...a) { errors.push(a.join(' ')); } },
    setTimeout: (fn) => fn(),
    clearTimeout() {},
    requestAnimationFrame: (fn) => fn(),
    performance: { now: () => 0 },
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

  const context = vm.createContext(sandbox);
  const loaded = [];
  let thrown = null;

  /* `skip` leaves a script UNLOADED so a test can run its own version of it --
     the reconstruction of the 2026-08-31 bug loads a deliberately broken
     cocktail-index.js into a context the other five have already populated. */
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

module.exports = { boot, buildPage, addCard, SCRIPTS, Element };
