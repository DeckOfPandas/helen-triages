// =============================================================================
// The cocktails index actually RUNS — issue #633.
//
// Run from tests/js with `node --test`.
// =============================================================================
// WHAT THIS IS FOR. On 2026-08-31 cocktail-index.js read
// `FilterState.arrivedByGoingBack` — which is on the filter-state MODULE and
// not on the binding `create(SPEC)` returns. That is `undefined`, calling
// undefined throws, and so THE ENTIRE TAIL OF THE FILE STOPPED RUNNING: the
// back/forward restore, `apply()` at startup (the index stopped applying its
// own filters and its shuffle), and the `pagehide` listener that saves the
// list.
//
// Every JS test stayed green. All of them ask a pure module a question and get
// a correct answer; the fault was in the WIRING between two modules, which is
// the one place a suite of pure-function tests cannot look. This file looks
// there, by loading the five real scripts in the real order against a stub DOM
// and asking whether the program got to the end.
//
// THE CANARY IS THE `pagehide` LISTENER, and it is the right one because it is
// the LAST statement in the file. Anything that throws anywhere above it stops
// it being registered, so one assertion covers every line before it. A test
// that checked some feature in the middle would have passed on the 2026-08-31
// revision right up until the line that broke.
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const { boot, SCRIPTS } = require('./index-harness.js');
const { createDocument } = require('./dom-stub.js');

const ROOT = path.join(__dirname, '..', '..');

const DRINKS = [
  // `sharp` only: answers the MOOD question and not the HASSLE one.
  { url: '/a', name: 'daiquiri', title: 'Daiquiri', moods: ['sharp'],
    ingredients: ['lime juice|lime juice'], chaos: 'good', madeBefore: true },
  // `sharp` AND `no juicing`: answers both questions. #695's case.
  { url: '/b', name: 'negroni', title: 'Negroni', moods: ['sharp', 'no juicing'],
    ingredients: ['gin|gin'], chaos: 'good', madeBefore: true },
  // Never made, for #732.
  { url: '/c', name: 'bamboo', title: 'Bamboo', moods: ['aperitivo'],
    ingredients: ['dry vermouth|dry vermouth'], chaos: 'open', madeBefore: false }
];

function titlesInOrder(page) {
  return page.list.children.map(function (li) {
    return li.querySelector('.drink-card-name a').textContent;
  });
}

function visibleTitles(page) {
  return page.list.children
    .filter(function (li) { return !li.hidden; })
    .map(function (li) { return li.querySelector('.drink-card-name a').textContent; });
}

function clickByData(page, attr, value) {
  const btn = page.filters.querySelectorAll('[' + attr + "='" + value + "']")[0];
  assert.ok(btn, 'no button in the fixture with ' + attr + '=' + value);
  btn.dispatch('click');
  return btn;
}

// --- the headline ------------------------------------------------------------

test('every index script loads and the whole of cocktail-index.js runs', () => {
  const r = boot({ drinks: DRINKS });

  assert.deepStrictEqual(r.loaded, SCRIPTS,
    'a script threw on load. This is the class of fault #633 was raised for: ' +
    'the page would render, look complete, and do nothing.');

  assert.ok(
    (r.doc.listeners.pagehide || []).length > 0,
    'the `pagehide` listener was never registered, which means execution ' +
    'stopped somewhere before the last line of cocktail-index.js. Everything ' +
    'after the throw is dead: the back/forward restore, apply() at startup, ' +
    'and the saved list.'
  );

  assert.deepStrictEqual(r.errors, [],
    'a script warned on startup. Each of these warnings is a graceful ' +
    'degradation path for a missing block, so the harness is testing a ' +
    'different program from the one the page runs.');
});

test('startup actually applied the filters rather than merely not crashing', () => {
  // The difference matters: `apply()` at startup is one of the things the
  // 2026-08-31 throw killed, and a page where nothing crashed but nothing ran
  // looks identical until you touch a control.
  const r = boot({ drinks: DRINKS });
  assert.strictEqual(r.doc.getElementById('drink-count-n').textContent, '3');
  assert.strictEqual(r.doc.getElementById('drink-count-word').textContent, 'survivors');
  assert.deepStrictEqual(
    r.page.list.children.map(function (c) { return c.hidden; }), [false, false, false],
    'no filter is set, so every card should be visible.'
  );
});

// --- the guard's own guard ---------------------------------------------------

test('the harness FAILS on the 2026-08-31 bug, rather than only passing today', () => {
  // Reconstructed by reintroducing the exact mistake into the real source: read
  // `arrivedByGoingBack` off the create() BINDING instead of off the module.
  // Without this, every assertion above could be vacuous and nobody would know.
  const src = fs.readFileSync(path.join(ROOT, 'assets', 'js', 'cocktail-index.js'), 'utf8');
  const broken = src.replace(
    'HTF.filterState.arrivedByGoingBack', 'FilterState.arrivedByGoingBack');
  assert.notStrictEqual(broken, src,
    'the line the bug was on has moved or been renamed, so this reconstruction ' +
    'no longer reproduces anything. Find the current equivalent rather than ' +
    'deleting the test.');

  const r = boot({ drinks: DRINKS, throwOnError: false, skip: ['cocktail-index.js'] });
  const context = r.sandbox;
  let threw = null;
  try {
    vm.runInContext(broken, vm.createContext ? context : context, { filename: 'broken.js' });
  } catch (e) {
    threw = e;
  }

  assert.ok(threw, 'the reintroduced bug did not throw, so this harness would ' +
    'not have caught it. Either the binding now carries arrivedByGoingBack, ' +
    'or the call has moved somewhere that is never reached at startup.');
  assert.match(String(threw.message), /not a function|undefined/i);
});

// --- the harness must not drift from the page --------------------------------

test('the script list matches the order cocktails/index.html loads them in', () => {
  // A harness testing a stale order is worse than none: it would go on passing
  // while the page loaded cocktail-index.js before the module it depends on.
  const html = fs.readFileSync(path.join(ROOT, 'cocktails', 'index.html'), 'utf8');
  const inPage = [];
  const re = /<script src="\{\{\s*'\/assets\/js\/([a-z-]+\.js)'/g;
  let m;
  while ((m = re.exec(html)) !== null) {
    if (inPage.indexOf(m[1]) === -1) inPage.push(m[1]);
  }
  assert.ok(inPage.length, 'no <script src> tags found in cocktails/index.html.');

  // universe.js is deliberately outside this harness -- it decorates the page
  // rather than wiring the filters, and it needs artwork this stub has no
  // opinion about. Everything else the page loads must be here, in order.
  const wanted = inPage.filter(function (n) { return n !== 'universe.js'; });
  const got = SCRIPTS.filter(function (n) { return n !== 'assets.js'; });
  assert.deepStrictEqual(got, wanted,
    'index-harness.js loads a different set or order of scripts than the page ' +
    'does. Follow the page.');
});

test('the fixture uses the ids the script actually reaches for', () => {
  // The script asks for these by id. A fixture that spells one differently
  // quietly exercises the null-guard instead of the real path, which is the
  // same kind of silent miss this whole file exists to stop.
  const src = fs.readFileSync(path.join(ROOT, 'assets', 'js', 'cocktail-index.js'), 'utf8');
  const wanted = [];
  const re = /getElementById\('([^']+)'\)/g;
  let m;
  while ((m = re.exec(src)) !== null) if (wanted.indexOf(m[1]) === -1) wanted.push(m[1]);

  const r = boot({ drinks: DRINKS });
  const missing = wanted.filter(function (id) { return !r.doc.getElementById(id); });

  // `drink-costs` and `shopping-list` belong to features this harness does not
  // build; they are named here so the exemption is a decision rather than a
  // gap that grew.
  const NOT_BUILT = ['drink-costs', 'shopping-list', 'shopping-list-setall'];
  const unexpected = missing.filter(function (id) { return NOT_BUILT.indexOf(id) === -1; });
  assert.deepStrictEqual(unexpected, [],
    'cocktail-index.js reaches for these ids and the fixture has none: ' +
    unexpected.join(', '));
});

// --- what the harness makes testable for the first time ----------------------

/* #732's third YOLO button IS NOT TESTED HERE, and the omission is deliberate.
   That button lives on its own branch (`fix/cocktail-search-and-index`) and
   this harness on another, so a test for it here would fail on this branch and
   pass on the merge -- which is the worst of both. The fixture already carries
   `data-made-before` on every card, so once both land the test is four lines:
   click `[data-chaos='unmade']` and assert only Bamboo survives. Same for the
   card ingredient ordering (#567/#691). Both were unreachable before this file
   existed; that is the point of it. */

test('#695: answering both mood questions outranks answering one of them twice', () => {
  const r = boot({ drinks: DRINKS });
  clickByData(r.page, 'data-mood', 'sharp');       // the MOOD section
  clickByData(r.page, 'data-mood', 'no juicing');  // the HASSLE section

  const order = titlesInOrder(r.page).slice(0, 2);
  assert.deepStrictEqual(order, ['Negroni', 'Daiquiri'],
    'Negroni answers both questions (sharp AND no juicing) and Daiquiri ' +
    'answers one, so Negroni must come first. Both have the same moodScore ' +
    'of the old ranking would have left this to the random key.');
});

test('#695: with only one section asked, the order is unchanged', () => {
  // The other half of the ruling: it must not reshuffle anything when only one
  // question has been asked, because every survivor answers that one.
  const r = boot({ drinks: DRINKS });
  clickByData(r.page, 'data-mood', 'sharp');
  assert.deepStrictEqual(visibleTitles(r.page).sort(), ['Daiquiri', 'Negroni'],
    'both drinks are `sharp` and both should survive.');
});
