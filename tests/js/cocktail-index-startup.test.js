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

const { boot, SCRIPTS, PAGE_SCRIPTS, LAYOUT_SCRIPTS } = require('./index-harness.js');
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
  const got = PAGE_SCRIPTS.filter(function (n) { return n !== 'assets.js'; });
  assert.deepStrictEqual(got, wanted,
    'index-harness.js loads a different set or order of scripts than the page ' +
    'does. Follow the page.');
});

test('the card measurement passes follow _layouts/default.html', () => {
  // #1107. These two are NOT in cocktails/index.html -- the shared layout
  // loads them for both sites, below {{ content }}, so they run after every
  // script the page itself loads. The harness has to keep both facts: that it
  // loads them, and that it loads them in the layout's order.
  //
  // THE ORDER IS THE ONE card-line-budget.js SAYS IT NEEDS: the name pass
  // decides how much room the ingredient line gets, and the ingredient line
  // decides how much the chips get. Running the budget first is not a crash,
  // it is a budget computed against a name that had not been fitted yet --
  // which is exactly the kind of wrong a harness in the wrong order would
  // report as fine.
  const layout = fs.readFileSync(path.join(ROOT, '_layouts', 'default.html'), 'utf8');
  const inLayout = [];
  const re = /<script src="\{\{\s*'\/assets\/js\/([a-z-]+\.js)'/g;
  let m;
  while ((m = re.exec(layout)) !== null) {
    if (LAYOUT_SCRIPTS.indexOf(m[1]) !== -1 && inLayout.indexOf(m[1]) === -1) {
      inLayout.push(m[1]);
    }
  }

  assert.deepStrictEqual(inLayout, LAYOUT_SCRIPTS,
    '_layouts/default.html loads the card measurement passes in a different ' +
    'order than index-harness.js does, or has stopped loading one of them. ' +
    'The tag for card-line-budget.js went missing once already (#846 deleted ' +
    'chip-rows.js and took it with it) and nothing noticed for two days, ' +
    'because cocktail-index.js guards its call with `if (HTF.cardLineBudget)`.');

  assert.deepStrictEqual(SCRIPTS.slice(-LAYOUT_SCRIPTS.length), LAYOUT_SCRIPTS,
    'the harness must run the card passes LAST, as the layout does: they sit ' +
    'below {{ content }}, so every script the page loads has already run.');
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

  // `drink-costs`, `drink-rates` and `shopping-list` belong to features this
  // harness does not build; they are named here so the exemption is a decision
  // rather than a gap that grew.
  //
  // THE TWO PRICE BLOCKS ARE ALSO ABSENT IN PRODUCTION, which is the stronger
  // reason to leave them out: both sit behind `site.show_costs`, declared in
  // _config_local.yml and nowhere else, so a page WITHOUT them is the deployed
  // page and the null path is the one most readers get. `drink-top-ups` is
  // deliberately NOT here — it is emitted ungated, so a page missing it is a
  // real anomaly and the fixture carries the real rows (#746).
  const NOT_BUILT = ['drink-costs', 'drink-rates', 'shopping-list',
                     'shopping-list-setall'];
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

// --- pagination, #694 --------------------------------------------------------
//
// THESE ARE THE FIRST TESTS THIS FEATURE COULD HAVE HAD. Paging lives inside
// cocktail-index.js's IIFE like everything else here, so before the harness the
// only way to check "does next actually advance" was to open a browser. The
// harness caught a real break while this was being written: #694 added
// `list-view.js` to the page and the script threw on its first apply() until
// the harness was told, with every other test green.

function manyDrinks(n) {
  const out = [];
  for (let i = 0; i < n; i++) {
    out.push({
      url: '/d' + i,
      name: 'drink ' + i,
      title: 'Drink ' + i,
      moods: ['sharp'],
      ingredients: ['gin|gin'],
      chaos: 'good',
      madeBefore: true
    });
  }
  return out;
}

test('#694: only the first twenty of a long list are shown', () => {
  const r = boot({ drinks: manyDrinks(45) });
  assert.strictEqual(visibleTitles(r.page).length, 20,
    'the page size is 20; a 45-drink list should show one page of it.');
  assert.strictEqual(r.doc.getElementById('drink-count-n').textContent, '45',
    'the SURVIVOR COUNT is the whole matching set, not the page. Paging is a ' +
    'view of the results and must not change what the count claims.');
  assert.strictEqual(
    r.doc.getElementById('drink-page-status').textContent, 'page 1 of 3');
});

test('#694: a list that fits on one page shows no pager at all', () => {
  // Hidden rather than disabled: "page 1 of 1" beside two dead arrows is
  // furniture answering a question nobody asked.
  const r = boot({ drinks: manyDrinks(5) });
  assert.strictEqual(r.page.pager.style.display, 'none');
  assert.strictEqual(visibleTitles(r.page).length, 5);
});

test('#694: next advances, prev goes back, and the ends disable', () => {
  const r = boot({ drinks: manyDrinks(45) });
  const prev = r.doc.getElementById('drink-page-prev');
  const next = r.doc.getElementById('drink-page-next');

  assert.strictEqual(prev.disabled, true, 'prev should be dead on page one.');
  assert.strictEqual(next.disabled, false);

  next.dispatch('click');
  assert.strictEqual(r.doc.getElementById('drink-page-status').textContent, 'page 2 of 3');
  assert.strictEqual(prev.disabled, false);
  assert.strictEqual(visibleTitles(r.page).length, 20);

  next.dispatch('click');
  assert.strictEqual(r.doc.getElementById('drink-page-status').textContent, 'page 3 of 3');
  assert.strictEqual(next.disabled, true, 'next should be dead on the last page.');
  assert.strictEqual(visibleTitles(r.page).length, 5, 'the last page is the remainder.');

  prev.dispatch('click');
  assert.strictEqual(r.doc.getElementById('drink-page-status').textContent, 'page 2 of 3');
});

test('#694: the pages between them cover every drink exactly once', () => {
  // The property that matters and the one an off-by-one breaks silently: a
  // reader paging through must see all 45, and no drink twice.
  const r = boot({ drinks: manyDrinks(45) });
  const next = r.doc.getElementById('drink-page-next');
  const seen = [];
  for (let page = 0; page < 3; page++) {
    seen.push(...visibleTitles(r.page));
    if (page < 2) next.dispatch('click');
  }
  assert.strictEqual(seen.length, 45, 'a drink was shown twice or not at all.');
  assert.strictEqual(new Set(seen).size, 45);
});

test('#694: (see all) drops the pager and shows everything', () => {
  const r = boot({ drinks: manyDrinks(45) });
  r.doc.getElementById('drink-page-see-all').dispatch('click');
  assert.strictEqual(visibleTitles(r.page).length, 45);
  assert.strictEqual(r.page.pager.style.display, 'none',
    'once (see all) is pressed there is nothing left to page.');
});

test('#694: changing a filter returns you to page one', () => {
  // The whole difference between paging and filtering. Landing on page 3 of a
  // set that now has one page -- or of a different set entirely -- is
  // disorienting in a way that going back to the top is not.
  const r = boot({ drinks: manyDrinks(45) });
  r.doc.getElementById('drink-page-next').dispatch('click');
  assert.strictEqual(r.doc.getElementById('drink-page-status').textContent, 'page 2 of 3');

  clickByData(r.page, 'data-mood', 'sharp');
  assert.strictEqual(r.doc.getElementById('drink-page-status').textContent, 'page 1 of 3',
    'a filter change must reset the page.');
});

// --- matched chips lead the row, #757 ----------------------------------------
//
// Helen's own example, and her diagnosis was right: "'no juicing' returns
// Caribbean Sazerac first, but the chip isn't on the card, presumably because
// the full list of chips doesn't fit on the two lines we give them."
//
// `.drink-card-moods` clips past its row cap, so on a chip-heavy drink the word
// that EXPLAINS why the card is here could be the one cut off -- which is the
// one job the card's foot has.

const CHIPPY = [{
  url: '/sazerac',
  name: 'caribbean sazerac',
  title: 'Caribbean Sazerac',
  // As #710 renders them: alphabetical.
  moods: ['aperitivo', 'clear', 'nightcap', 'no juicing', 'tiki', 'warming'],
  ingredients: ['rye|rye'],
  chaos: 'good',
  madeBefore: true
}];

// The panel has to offer every mood this drink carries, or the test would be
// clicking buttons that do not exist. `no juicing` is the HASSLE section, as it
// is on the real index.
const CHIP_HASSLES = ['no juicing'];
const CHIP_MOODS = ['aperitivo', 'clear', 'nightcap', 'tiki', 'warming'];

function chipOrder(page) {
  return page.list.children[0]
    .querySelectorAll('.drink-card-mood')
    .map(function (c) { return c.dataset.mood; });
}

function matchedChips(page) {
  return page.list.children[0]
    .querySelectorAll('.drink-card-mood')
    .filter(function (c) { return c.classList.contains('is-match'); })
    .map(function (c) { return c.dataset.mood; });
}

test('#757: a matched chip moves to the front of the row', () => {
  const r = boot({ drinks: CHIPPY, moods: CHIP_MOODS, hassles: CHIP_HASSLES });
  assert.deepStrictEqual(chipOrder(r.page),
    ['aperitivo', 'clear', 'nightcap', 'no juicing', 'tiki', 'warming'],
    'the resting order should be the alphabetical one #710 renders.');

  clickByData(r.page, 'data-mood', 'no juicing');

  assert.deepStrictEqual(matchedChips(r.page), ['no juicing']);
  assert.strictEqual(chipOrder(r.page)[0], 'no juicing',
    'the chip that explains why this card is here must not be the one clipped.');
});

test('#757: alphabetical order survives inside both groups', () => {
  // The two lists are built by walking `d.moodEls`, which is read once at
  // startup in document order -- so #710's sort is preserved within the matched
  // group and within the rest, rather than being undone by the regrouping.
  const r = boot({ drinks: CHIPPY, moods: CHIP_MOODS, hassles: CHIP_HASSLES });
  clickByData(r.page, 'data-mood', 'tiki');
  clickByData(r.page, 'data-mood', 'aperitivo');

  assert.deepStrictEqual(chipOrder(r.page),
    ['aperitivo', 'tiki', 'clear', 'nightcap', 'no juicing', 'warming'],
    'matched chips first in alphabetical order, then the rest in theirs.');
});

test('#757: clearing the filter puts the row back in plain alphabetical order', () => {
  const r = boot({ drinks: CHIPPY, moods: CHIP_MOODS, hassles: CHIP_HASSLES });
  clickByData(r.page, 'data-mood', 'warming');
  assert.strictEqual(chipOrder(r.page)[0], 'warming');

  clickByData(r.page, 'data-mood', 'warming');   // toggles off
  assert.deepStrictEqual(chipOrder(r.page),
    ['aperitivo', 'clear', 'nightcap', 'no juicing', 'tiki', 'warming'],
    'with nothing matched there is no group to lead, so the row is just sorted.');
});

test('#757: the chips are moved in the DOM, not merely reordered visually', () => {
  // Load-bearing, and the reason flex `order` was not used: the separator dot
  // is drawn by `.drink-card-mood + .drink-card-mood::before`, a DOM-order
  // selector. Reordering visually would leave the dot on whichever chip is
  // second in the MARKUP -- a leading dot on the row and a missing one inside
  // it. Asserting document order is asserting the dot lands correctly.
  const r = boot({ drinks: CHIPPY, moods: CHIP_MOODS, hassles: CHIP_HASSLES });
  clickByData(r.page, 'data-mood', 'no juicing');

  const parent = r.page.list.children[0].querySelector('.drink-card-moods');
  assert.strictEqual(parent.children[0].dataset.mood, 'no juicing',
    'the matched chip is not first in the DOM, so the dot will be wrong.');
  parent.children.forEach(function (chip) {
    assert.strictEqual(chip.style.order, undefined,
      'a chip carries an `order` style, which would divorce what is seen from ' +
      'what the dot selector reads.');
  });
});

// --- arriving at the shortlist by URL, #994 ----------------------------------
//
// `?shortlist=1` is the one query the index reads besides `?mood=`. It was
// added for a drink page's see-all link, and #1000 removed that link two days
// later -- so nothing on the site points here now and the query is kept
// deliberately (cocktail-index.js says why). These tests are half of what
// keeps it honest: a URL nothing links to is a URL nobody would notice
// breaking.
//
// What they assert is that the index turns the VIEW on when it arrives, and
// specifically that it calls the same `enterShortlistView()` the
// `shortlisted (N)` button calls, so the two doors lead to one state
// (#918, MANUAL 8.9).
//
// THE SHORTLIST IS EMPTY IN THIS HARNESS, deliberately and not by accident:
// HTF.shortlist keys its storage on `HTF.site`, which comes from a meta tag the
// stub page does not carry, so the store is a no-op here. That is enough for
// what these assert -- the view is ON and it has narrowed to nothing -- and it
// keeps them about the wiring rather than about the store, which
// shortlist.test.js and shortlist-view.test.js already own.

function shortlistViewIsOn(r) {
  const btn = r.doc.getElementById('shortlist-only');
  assert.ok(btn, 'the fixture has no shortlisted-only button.');
  return btn.getAttribute('aria-pressed') === 'true' &&
         btn.classList.contains('is-on');
}

test('#994: ?shortlist=1 turns the shortlist view on at startup', () => {
  const r = boot({ drinks: DRINKS, search: '?shortlist=1' });
  assert.ok(shortlistViewIsOn(r),
    'if the index does not read the query, the URL lands on an ordinary ' +
    'index -- which looks like a working page and is not one.');
  assert.deepStrictEqual(visibleTitles(r.page), [],
    'the view is on and this browser has shortlisted nothing, so nothing ' +
    'survives -- which is also what proves the state reached apply().');
});

test('#994: without the query the view stays off', () => {
  // The control. A test that only ever boots with the query would pass on an
  // index that turned the view on unconditionally.
  const r = boot({ drinks: DRINKS });
  assert.ok(!shortlistViewIsOn(r));
  assert.strictEqual(visibleTitles(r.page).length, DRINKS.length);
});

// --- arriving with a name, #1024 -----------------------------------------------
// `?q=` is what the search box on a drink page's furniture line sends. The
// index must put it into I KNOW WHAT I WANT and apply it, exactly as typing
// there would, so the two boxes are one control in two places.

test('#1024: ?q= fills the name box and narrows the list', () => {
  const r = boot({ drinks: DRINKS, search: '?q=negroni' });
  assert.strictEqual(r.doc.getElementById('drink-name').value, 'negroni',
    'the box should show what the reader typed on the page they came from.');
  // BY KEY, NOT BY TITLE. A matched name is re-rendered with a <mark> through
  // innerHTML, which this stub CLEARS rather than parses (dom-stub.js), so
  // the matched card's title reads as '' here and nowhere else.
  const visible = r.page.list.children.filter(function (li) { return !li.hidden; });
  assert.deepStrictEqual(visible.map(function (li) { return li.getAttribute('data-url'); }),
    ['/b'], 'the query must reach apply(), not only the box.');
});

// --- arriving with an ingredient, #1050 -----------------------------------------
// `?ing=` is what the search-for-anything box on a drink page sends when the
// reader picks an ingredient: a card's own ingredient name, which is the chip
// HAS TO HAVE offers. It must be added to `include` exactly as choosing that
// chip would, so the two are one control in two places.

test('#1050: ?ing= adds the chip to HAS TO HAVE and narrows the list', () => {
  const r = boot({ drinks: DRINKS, search: '?ing=gin' });
  const on = r.doc.getElementById('drink-include-pool').querySelectorAll('.btn-pool')
    .filter((b) => b.classList.contains('is-on'))
    .map((b) => b.querySelector('.btn-pool-label').textContent);
  assert.deepStrictEqual(on, ['gin'],
    'the chip should be on screen as chosen, or the reader cannot undo it.');
  assert.deepStrictEqual(visibleTitles(r.page), ['Negroni'],
    'the chip must reach apply(), not only the pool.');
});

test('#1050: an ingredient no card names is dropped in silence', () => {
  // A joined label ("X or Y") or a stale name matches no chip WHOLE, and the
  // rule is the exclusion rule's: never a substring. The index lands
  // unfiltered, which is a working page rather than a stuck one.
  const r = boot({ drinks: DRINKS, search: '?ing=gi' });
  assert.strictEqual(visibleTitles(r.page).length, DRINKS.length);
  const on = r.doc.getElementById('drink-include-pool').querySelectorAll('.btn-pool')
    .filter((b) => b.classList.contains('is-on'));
  assert.deepStrictEqual(on, []);
});

// --- a shortlist someone sent, #1093 ------------------------------------------------
// food-index-startup.test.js carries the full set, including "keep these"
// (this harness's store is a no-op, see above). These are the wiring: the
// sent list reaches matches(), and the own-list button is not lit over it.

test('#1093: ?shortlist=<slugs> shows exactly those drinks', () => {
  const r = boot({ drinks: DRINKS, search: '?shortlist=c,a' });
  assert.deepStrictEqual(visibleTitles(r.page).sort(), ['Bamboo', 'Daiquiri']);
  assert.ok(!shortlistViewIsOn(r),
    'the button counts THIS browser\'s shortlist and must not claim a sent one.');
});

test('#1093: a sent list beats a mood in the same URL, as shortlist=1 does', () => {
  const r = boot({ drinks: DRINKS, search: '?mood=sharp&shortlist=c' });
  assert.deepStrictEqual(visibleTitles(r.page), ['Bamboo']);
});

test('#1093: a slug beginning with 1 is not read as the own-list flag', () => {
  const drinks = DRINKS.concat([{ url: '/12-mile-limit', name: '12 mile limit',
    title: '12 Mile Limit', moods: [], ingredients: ['rum|rum'] }]);
  const r = boot({ drinks, search: '?shortlist=12-mile-limit' });
  assert.deepStrictEqual(visibleTitles(r.page), ['12 Mile Limit']);
});

test('#994: shortlist=1 beats a mood in the same URL', () => {
  // It is a VIEW, not a facet (#918): pressing the button clears every other
  // filter, and arriving by the link must mean the same thing or the two doors
  // lead somewhere different. The order in the file is what decides it, so
  // this is the assertion that a later edit reordering those two blocks would
  // trip.
  const r = boot({ drinks: DRINKS, search: '?mood=sharp&shortlist=1' });
  assert.ok(shortlistViewIsOn(r));
  const lit = r.page.filters.querySelectorAll("[data-mood='sharp']")
    .filter(function (b) { return b.classList.contains('is-on'); });
  assert.deepStrictEqual(lit, [],
    'the mood button is still lit, so the view did not clear it -- a filter ' +
    'the reader can see but the list is not obeying.');
});

// --- arriving at a fragment, #1057 and #1059 ------------------------------------
// food-index-startup.test.js carries the fuller set and the reasoning; this is
// the cocktails half of the same widening -- any element id named by
// location.hash, not only the literal string "results" -- since a drink
// page's own mood chips (_layouts/cocktail.html) end their href in
// `#filter-mood` or `#filter-hassle`, and the actions row's "see shortlist"
// link ends in `#results` the same way a search result does.

test('#1050/#1057: arriving at #results scrolls the count line into view', () => {
  const r = boot({ drinks: DRINKS, hash: '#results' });
  assert.strictEqual(r.page.count._scrollCalls.length, 1,
    'the startup block must scroll to location.hash again after apply(), the ' +
    'same landing a search result and "see shortlist" both rely on.');
  assert.strictEqual(r.page.count._scrollCalls[0].block, 'start');
});

test('#1059: arriving at #filter-mood scrolls the MOOD section, not #results', () => {
  const r = boot({ drinks: DRINKS, hash: '#filter-mood' });
  assert.strictEqual(r.page.mood._scrollCalls.length, 1,
    'a mood chip\'s own fragment must be read generically off location.hash, ' +
    'not hardcoded to "results".');
  assert.strictEqual(r.page.count._scrollCalls, undefined,
    'only the id location.hash actually names should be scrolled to.');
});

test('#1059: arriving at #filter-hassle scrolls the HASSLE section', () => {
  const r = boot({ drinks: DRINKS, hash: '#filter-hassle' });
  assert.strictEqual(r.page.hassle._scrollCalls.length, 1);
  assert.strictEqual(r.page.mood._scrollCalls, undefined);
});

test('with no hash at all, nothing is scrolled', () => {
  const r = boot({ drinks: DRINKS });
  assert.strictEqual(r.page.count._scrollCalls, undefined);
  assert.strictEqual(r.page.mood._scrollCalls, undefined);
  assert.strictEqual(r.page.hassle._scrollCalls, undefined);
});
