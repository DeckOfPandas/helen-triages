// Tests for assets/js/results-bar.js: the results pill (#1448) on both
// indexes, from _includes/results-pill.html.
//
//   node --test tests/js/*.test.js
//
// The pill is a mirror: it shows the count the index script painted, and its
// × is the index script's own clear-all, whose visibility that script sets.
// Nothing here checks a count or a clearing, because the pill does neither.
//
// MutationObserver is stubbed here, not in tests/js/dom-stub.js, which must not
// invent geometry: each records what it was asked to observe and lets a test
// fire its callback. Rects are set by hand with `__box`.
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const { createDocument } = require('./dom-stub.js');

const SRC = fs.readFileSync(
  path.join(__dirname, '..', '..', 'assets', 'js', 'results-bar.js'), 'utf8');

class StubMutationObserver {
  constructor(callback) {
    this.callback = callback;
    this.observed = [];
    StubMutationObserver.instances.push(this);
  }
  observe(el, options) { this.observed.push({ el, options }); }
  disconnect() {}
  fire() { this.callback([], this); }
}
StubMutationObserver.instances = [];

const FOOD_IDS = ['recipe-count-n', 'recipe-count-word'];
const DRINK_IDS = ['drink-count-n', 'drink-count-word'];

const VIEWPORT_HEIGHT = 844;
// Where the filter panel and the count line are, against a phone's screen.
const AT_FILTERS = { panel: { top: 120, bottom: 1300 }, line: { top: 1400, bottom: 1430 } };
const BOTH_ON_SCREEN = { panel: { top: 120, bottom: 600 }, line: { top: 650, bottom: 680 } };
const AT_RESULTS = { panel: { top: -1300, bottom: -60 }, line: { top: 16, bottom: 46 } };
// The top few pixels of the line over the bottom edge: not yet seen.
const PEEKING = { panel: { top: 120, bottom: 800 }, line: { top: 830, bottom: 860 } };

/**
 * An index with the parts the script reaches for, and nothing else: the
 * filter panel, the count line, the section "top" returns to, and the pill as
 * _includes/results-pill.html renders it. `clear` is what the index script
 * would have left on the ×: 'visible' while a filter is on.
 */
function boot(options) {
  options = options || {};
  StubMutationObserver.instances = [];

  const doc = createDocument();
  const el = (tag, cls, attrs) => {
    const node = doc.createElement(tag);
    if (cls) node.setAttribute('class', cls);
    Object.entries(attrs || {}).forEach(([k, v]) => node.setAttribute(k, v));
    return node;
  };

  const panel = el('div', 'controls', options.noPanel ? {} : { 'data-filter-panel': '' });
  const star = el('div', 'category', { id: 'filter-star' });
  star._focusCalls = [];
  star.focus = (opts) => { star._focusCalls.push(opts); };
  panel.appendChild(star);
  doc.body.appendChild(panel);

  const heading = el('div', 'results-heading', { id: 'results' });
  heading._focusCalls = [];
  heading.focus = (opts) => { heading._focusCalls.push(opts); };
  const ids = 'ids' in options ? options.ids : FOOD_IDS;
  let n = null;
  let w = null;
  if (ids) {
    n = el('span', 'results-count-number', { id: ids[0] });
    n.textContent = '42';
    w = el('span', '', { id: ids[1] });
    w.textContent = 'survivors';
    heading.appendChild(n);
    heading.appendChild(doc.createTextNode(' '));
    heading.appendChild(w);
  }
  doc.body.appendChild(heading);

  let pill = null;
  const parts = {};
  if (!options.noPill) {
    pill = el('div', 'results-pill', { 'data-results-pill': '' });
    pill.hidden = true;
    const copy = (parent) => {
      const cn = el('span', 'results-count-number', { 'data-results-pill-n': '' });
      const cw = el('span', '', { 'data-results-pill-word': '' });
      parent.appendChild(cn);
      parent.appendChild(cw);
      return [cn, cw];
    };
    parts.plain = el('span', 'results-pill-part', { 'data-results-pill-count': '' });
    parts.plainCopy = copy(parts.plain);
    parts.down = el('button', 'results-pill-part', { 'data-results-pill-down': '', type: 'button' });
    parts.downCopy = copy(parts.down);
    parts.up = el('button', 'results-pill-part', {
      'data-results-pill-up': options.noTopTarget ? 'filter-nowhere' : 'filter-star', type: 'button'
    });
    parts.clear = el('button', 'results-pill-part results-pill-clear', { 'data-results-pill-clear': '', type: 'button' });
    parts.clear.style.visibility = options.clear || 'hidden';
    [parts.plain, parts.down, parts.up, parts.clear].forEach((p) => pill.appendChild(p));
    doc.body.appendChild(pill);
  }

  // The index script's own clear-all, registered first as it is on the page:
  // it hides the × and repaints the count.
  const indexClears = [];
  if (pill) {
    parts.clear.addEventListener('click', () => {
      indexClears.push(1);
      parts.clear.style.visibility = 'hidden';
      if (n) n.textContent = '90';
    });
  }

  const place = (where) => {
    panel.__box = where.panel;
    heading.__box = where.line;
  };
  place(options.at || AT_FILTERS);

  const sandbox = { document: doc, console: { warn() {}, error() {}, log() {} } };
  if (!options.noMutationObserver) sandbox.MutationObserver = StubMutationObserver;
  if ('reduceMotion' in options) {
    sandbox.matchMedia = (query) => ({
      matches: query === '(prefers-reduced-motion: reduce)' && options.reduceMotion
    });
  }
  sandbox.innerHeight = VIEWPORT_HEIGHT;
  const handlers = { scroll: [], resize: [], load: [] };
  sandbox.addEventListener = (type, fn) => { if (handlers[type]) handlers[type].push(fn); };
  // Frames run when the test says so, as the browser runs them after a scroll.
  const frames = [];
  if (!options.noAnimationFrame) sandbox.requestAnimationFrame = (fn) => { frames.push(fn); };
  sandbox.window = sandbox;
  vm.runInContext(SRC, vm.createContext(sandbox), { filename: 'results-bar.js' });
  doc.dispatch('DOMContentLoaded');

  const mo = StubMutationObserver.instances[0] || null;
  /** Move the panel and the line, then scroll: every handler, then one frame. */
  const scrollTo = (where) => {
    place(where);
    handlers.scroll.forEach((fn) => fn());
    frames.splice(0).forEach((fn) => fn());
  };
  /** What the pill shows, face by face, as a reader would list it. */
  const shows = () => {
    if (!pill || pill.hidden) return 'nothing';
    const out = [];
    if (!parts.up.hidden) out.push('top');
    if (!parts.down.hidden) out.push('survivors ↓');
    if (!parts.plain.hidden) out.push('survivors');
    if (pill.classList.contains('results-pill--clear')) out.push('×');
    return out.join(' ');
  };

  return { doc, pill, parts, panel, heading, star, n, w, mo, handlers, frames, scrollTo, shows, indexClears };
}

// The script builds its option objects inside the vm sandbox, another realm,
// so deepStrictEqual would fail them on prototype alone.
const plain = (value) => JSON.stringify(value);

// --- which face, where --------------------------------------------------------

test('arriving at the filters with the results below: "N survivors ↓"', () => {
  const r = boot();
  assert.strictEqual(r.shows(), 'survivors ↓');
});

test('with a filter on, the same place adds the ×', () => {
  const r = boot({ clear: 'visible' });
  assert.strictEqual(r.shows(), 'survivors ↓ ×');
});

test('the filters above the screen: "top", with the × only when there is something to clear', () => {
  assert.strictEqual(boot({ at: AT_RESULTS }).shows(), 'top');
  assert.strictEqual(boot({ at: AT_RESULTS, clear: 'visible' }).shows(), 'top ×');
});

test('landing on the results shows "top" at once, with no scrolling first', () => {
  // The stuck reader of #1448: a search result or "N survivors ↓" puts the
  // count line at the top, which is neither below the screen nor past it.
  const r = boot({ at: AT_RESULTS, clear: 'visible' });
  assert.strictEqual(r.pill.hidden, false);
  assert.strictEqual(r.parts.up.hidden, false);
});

test('the panel and the line both on screen, nothing chosen: no pill', () => {
  assert.strictEqual(boot({ at: BOTH_ON_SCREEN }).shows(), 'nothing');
});

test('the panel and the line both on screen, a filter on: "N survivors ×", so a filtered page always has its ×', () => {
  const r = boot({ at: BOTH_ON_SCREEN, clear: 'visible' });
  assert.strictEqual(r.shows(), 'survivors ×');
  assert.strictEqual(r.parts.down.hidden, true, 'no arrow: there is nowhere to go.');
});

test('a count line peeking over the bottom edge still counts as below', () => {
  assert.strictEqual(boot({ at: PEEKING }).shows(), 'survivors ↓');
});

test('one face at a time, never two of the three', () => {
  [AT_FILTERS, BOTH_ON_SCREEN, AT_RESULTS, PEEKING].forEach((at) => {
    const r = boot({ at, clear: 'visible' });
    const faces = [r.parts.up, r.parts.down, r.parts.plain].filter((p) => !p.hidden);
    assert.strictEqual(faces.length, 1, `${plain(at)} shows ${faces.length} faces.`);
  });
});

// --- scrolling ------------------------------------------------------------------

test('scrolling from the filters to the results swaps "survivors ↓" for "top"', () => {
  const r = boot({ clear: 'visible' });
  r.scrollTo(AT_RESULTS);
  assert.strictEqual(r.shows(), 'top ×');
  r.scrollTo(AT_FILTERS);
  assert.strictEqual(r.shows(), 'survivors ↓ ×');
});

test('scrolling re-reads the boxes at most once a frame', () => {
  const r = boot();
  let reads = 0;
  const real = r.heading.getBoundingClientRect.bind(r.heading);
  r.heading.getBoundingClientRect = () => { reads += 1; return real(); };
  r.handlers.scroll.forEach((fn) => fn());
  r.handlers.scroll.forEach((fn) => fn());
  r.handlers.scroll.forEach((fn) => fn());
  r.frames.splice(0).forEach((fn) => fn());
  assert.strictEqual(reads, 1, 'three scroll events before a frame are one read.');
});

test('a resize and the page\'s load re-place it too', () => {
  const r = boot();
  assert.strictEqual(r.handlers.resize.length, 1);
  assert.strictEqual(r.handlers.load.length, 1);
  r.panel.__box = AT_RESULTS.panel;
  r.heading.__box = AT_RESULTS.line;
  r.handlers.resize.forEach((fn) => fn());
  r.frames.splice(0).forEach((fn) => fn());
  assert.strictEqual(r.shows(), 'top');
});

// --- what it shows ----------------------------------------------------------------

test('every count copy mirrors the number and the word', () => {
  const r = boot({ clear: 'visible', at: BOTH_ON_SCREEN });
  [r.parts.plainCopy, r.parts.downCopy].forEach(([cn, cw]) => {
    assert.strictEqual(cn.textContent, '42');
    assert.strictEqual(cw.textContent, 'survivors');
  });
});

test('it follows the count and the × through the mutation observer', () => {
  const r = boot({ at: BOTH_ON_SCREEN, clear: 'visible' });
  assert.ok(r.mo, 'no MutationObserver was constructed.');
  const watched = r.mo.observed.map((o) => o.el);
  [r.n, r.w, r.parts.clear].forEach((node) => {
    assert.ok(watched.indexOf(node) !== -1, 'a span or the × is not observed.');
  });
  r.n.textContent = '1';
  r.w.textContent = 'survivor';
  r.mo.fire();
  assert.strictEqual(r.parts.plainCopy[0].textContent, '1');
  assert.strictEqual(r.parts.plainCopy[1].textContent, 'survivor');

  // The index script hides its clear-all when the last filter goes.
  r.parts.clear.style.visibility = 'hidden';
  r.mo.fire();
  assert.strictEqual(r.shows(), 'nothing', 'the line on screen and nothing chosen: no pill.');
});

test('it finds the cocktails index\'s count spans by their own ids', () => {
  const r = boot({ ids: DRINK_IDS });
  assert.strictEqual(r.shows(), 'survivors ↓');
  assert.strictEqual(r.parts.downCopy[0].textContent, '42');
});

test('the pill shows "0 survivors" too, since the empty state is where it leads', () => {
  const r = boot({ clear: 'visible' });
  r.n.textContent = '0';
  r.mo.fire();
  assert.strictEqual(r.parts.downCopy[0].textContent, '0');
});

// --- what its parts do ------------------------------------------------------------

test('"N survivors ↓" scrolls the count line to the top, smoothly, and focuses it', () => {
  const r = boot({ reduceMotion: false });
  r.parts.down.dispatch('click');
  assert.strictEqual(plain(r.heading._scrollCalls), plain([{ behavior: 'smooth', block: 'start' }]));
  assert.strictEqual(r.heading.getAttribute('tabindex'), '-1',
    'a div or p takes focus only with a tabindex.');
  assert.strictEqual(plain(r.heading._focusCalls), plain([{ preventScroll: true }]),
    'focus must not scroll again, or it cancels the smooth scroll.');
});

test('with reduced motion asked for, it jumps at once', () => {
  const r = boot({ reduceMotion: true });
  r.parts.down.dispatch('click');
  assert.strictEqual(plain(r.heading._scrollCalls), plain([{ behavior: 'auto', block: 'start' }]));
});

test('it leaves a tabindex the count line already has alone', () => {
  const r = boot();
  r.heading.setAttribute('tabindex', '0');
  r.parts.down.dispatch('click');
  assert.strictEqual(r.heading.getAttribute('tabindex'), '0');
});

test('"top" scrolls to the section it names and focuses it', () => {
  const r = boot({ at: AT_RESULTS, reduceMotion: false });
  r.parts.up.dispatch('click');
  assert.strictEqual(plain(r.star._scrollCalls), plain([{ behavior: 'smooth', block: 'start' }]));
  assert.strictEqual(r.star.getAttribute('tabindex'), '-1');
  assert.strictEqual(plain(r.star._focusCalls), plain([{ preventScroll: true }]));
  assert.strictEqual(r.heading._scrollCalls, undefined, 'it goes to the section, not the count.');
});

test('a "top" naming an id the page lacks is never offered', () => {
  const r = boot({ at: AT_RESULTS, noTopTarget: true, clear: 'visible' });
  assert.strictEqual(r.parts.up.hidden, true, 'a part that scrolls nowhere must not be offered.');
  assert.strictEqual(r.shows(), 'survivors ×', 'the × is still within reach.');
});

test('the × is the index script\'s own button: after its click the pill re-reads what that script left', () => {
  const r = boot({ at: BOTH_ON_SCREEN, clear: 'visible' });
  r.parts.clear.dispatch('click');
  assert.strictEqual(r.indexClears.length, 1, 'the index script\'s listener did not run.');
  assert.strictEqual(r.shows(), 'nothing', 'nothing left to clear, the line on screen: no pill.');
  assert.strictEqual(r.parts.plainCopy[0].textContent, '90', 'the repainted count.');
});

// --- the pages without the pieces -----------------------------------------------

test('a page with no pill, no filter panel or no count spans wires nothing', () => {
  [{ noPill: true }, { noPanel: true }, { ids: null }].forEach((options) => {
    const r = boot(options);
    assert.strictEqual(r.handlers.scroll.length, 0, `${plain(options)} wired a scroll listener.`);
    if (r.pill) assert.strictEqual(r.pill.hidden, true);
  });
});

test('no requestAnimationFrame: the pill stays hidden and nothing is wired', () => {
  const r = boot({ noAnimationFrame: true, clear: 'visible' });
  assert.strictEqual(r.pill.hidden, true);
  assert.strictEqual(r.handlers.scroll.length, 0);
});

test('without a MutationObserver it still shows the current count on the next scroll', () => {
  const r = boot({ noMutationObserver: true });
  r.n.textContent = '7';
  r.scrollTo(AT_FILTERS);
  assert.strictEqual(r.parts.downCopy[0].textContent, '7');
});
