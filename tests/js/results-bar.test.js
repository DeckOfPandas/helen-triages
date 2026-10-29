// Tests for assets/js/results-bar.js: the sticky "N survivors" bar and the
// "N survivors ↓" jump pill (#1441) on both indexes.
//
//   node --test tests/js/*.test.js
//
// Both are mirrors: they show the count the index script painted, the bar
// shows the clear-all's own visibility, and its button presses the index's
// button. Nothing here checks a count, because neither computes one.
//
// IntersectionObserver and MutationObserver are stubbed here, not in
// tests/js/dom-stub.js, which must not invent geometry: each records what it
// was asked to observe and lets a test fire its callback with a chosen entry.
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const { createDocument } = require('./dom-stub.js');

const SRC = fs.readFileSync(
  path.join(__dirname, '..', '..', 'assets', 'js', 'results-bar.js'), 'utf8');

class StubIntersectionObserver {
  constructor(callback) {
    this.callback = callback;
    this.targets = [];
    StubIntersectionObserver.instances.push(this);
  }
  observe(el) { this.targets.push(el); }
  disconnect() {}
  /** Report one entry for the observed heading, as the browser would. */
  fire(entry) { this.callback([entry], this); }
}
StubIntersectionObserver.instances = [];

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

/**
 * An index with the parts the script reaches for, and nothing else: the bar
 * (deliberately FIRST in the DOM, so a lookup for "the first `.btn-clear`"
 * that forgot to skip the bar's own would find the wrong one), the filter
 * panel with the top and bottom clear-alls the index script would have built,
 * and the count line.
 */
function boot(options) {
  options = options || {};
  StubIntersectionObserver.instances = [];
  StubMutationObserver.instances = [];

  const doc = createDocument();
  const el = (tag, cls, attrs) => {
    const node = doc.createElement(tag);
    if (cls) node.setAttribute('class', cls);
    Object.entries(attrs || {}).forEach(([k, v]) => node.setAttribute(k, v));
    return node;
  };

  let bar = null;
  let barN = null;
  let barWord = null;
  let barClear = null;
  if (!options.noBar) {
    bar = el('div', 'results-bar', { 'data-results-bar': '' });
    bar.hidden = true;
    const inner = el('div', 'results-bar-inner');
    const barCount = el('span', 'results-bar-count');
    barN = el('span', 'results-count-number', { 'data-results-bar-n': '' });
    barWord = el('span', '', { 'data-results-bar-word': '' });
    barCount.appendChild(barN);
    barCount.appendChild(doc.createTextNode(' '));
    barCount.appendChild(barWord);
    inner.appendChild(barCount);
    barClear = el('button', 'btn-clear results-bar-clear', { 'data-results-bar-clear': '' });
    inner.appendChild(barClear);
    bar.appendChild(inner);
    doc.body.appendChild(bar);
  }

  let jump = null;
  let jumpN = null;
  let jumpWord = null;
  if (!options.noJump) {
    jump = el('button', 'results-jump', { 'data-results-jump': '', type: 'button' });
    jump.hidden = true;
    jumpN = el('span', 'results-count-number', { 'data-results-jump-n': '' });
    jumpWord = el('span', '', { 'data-results-jump-word': '' });
    jump.appendChild(jumpN);
    jump.appendChild(doc.createTextNode(' '));
    jump.appendChild(jumpWord);
    doc.body.appendChild(jump);
  }

  const panel = el('div', 'controls');
  const topClear = el('button', 'btn-clear');
  topClear.style.visibility = options.clearVisibility || 'visible';
  topClear.clicks = 0;
  topClear.addEventListener('click', () => { topClear.clicks += 1; });
  panel.appendChild(topClear);
  const bottomClear = el('button', 'btn-clear btn-clear--bottom');
  bottomClear.clicks = 0;
  bottomClear.addEventListener('click', () => { bottomClear.clicks += 1; });
  panel.appendChild(bottomClear);
  doc.body.appendChild(panel);

  const heading = el('div', 'results-heading', { id: 'results' });
  // The stub has no focus; record what the pill asks of it.
  heading._focusCalls = [];
  heading.focus = (opts) => { heading._focusCalls.push(opts); };
  // `ids: null` is a page with no count spans at all; absent means food's.
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

  const sandbox = { document: doc, console: { warn() {}, error() {}, log() {} } };
  if (!options.noIntersectionObserver) sandbox.IntersectionObserver = StubIntersectionObserver;
  if (!options.noMutationObserver) sandbox.MutationObserver = StubMutationObserver;
  if ('reduceMotion' in options) {
    sandbox.matchMedia = (query) => ({
      matches: query === '(prefers-reduced-motion: reduce)' && options.reduceMotion
    });
  }
  // A phone's screen; the entries below are placed against it.
  sandbox.innerHeight = VIEWPORT_HEIGHT;
  const scrollHandlers = [];
  sandbox.addEventListener = (type, fn) => { if (type === 'scroll') scrollHandlers.push(fn); };
  // Frames run when the test says so, as the browser runs them after a scroll.
  const frames = [];
  sandbox.requestAnimationFrame = (fn) => { frames.push(fn); };
  sandbox.window = sandbox;
  vm.runInContext(SRC, vm.createContext(sandbox), { filename: 'results-bar.js' });

  // The script waits for DOMContentLoaded, as filters.js does, so that the
  // buttons that script builds exist by the time this one looks for them.
  doc.dispatch('DOMContentLoaded');

  const io = StubIntersectionObserver.instances[0] || null;
  const mo = StubMutationObserver.instances[0] || null;
  /** Put the count line at `box` and scroll: every handler, then one frame. */
  const scrollTo = (box) => {
    heading.__box = box;
    scrollHandlers.forEach((fn) => fn());
    frames.splice(0).forEach((fn) => fn());
  };

  return {
    doc, bar, barN, barWord, barClear, jump, jumpN, jumpWord,
    topClear, bottomClear, heading, n, w, io, mo, scrollTo, scrollHandlers
  };
}

// The script builds its option objects inside the vm sandbox, another realm,
// so deepStrictEqual would fail them on prototype alone.
const plain = (value) => JSON.stringify(value);

const VIEWPORT_HEIGHT = 844;
const ABOVE = { isIntersecting: false, boundingClientRect: { top: -120, bottom: -90 } };
const IN_VIEW = { isIntersecting: true, boundingClientRect: { top: 200, bottom: 230 } };
const BELOW = { isIntersecting: false, boundingClientRect: { top: 1400, bottom: 1430 } };
// The top few pixels over the bottom edge: intersecting, but not yet seen.
const PEEKING = { isIntersecting: true, boundingClientRect: { top: 830, bottom: 860 } };

// --- when it shows -------------------------------------------------------------

test('it watches #results and stays hidden until the observer has spoken', () => {
  const r = boot();
  assert.ok(r.io, 'no IntersectionObserver was constructed.');
  assert.deepStrictEqual(r.io.targets, [r.heading],
    'the observer should watch the count line and nothing else.');
  assert.strictEqual(r.bar.hidden, true,
    'the bar must not appear on its own: only an observer report reveals it.');
});

test('the heading above the viewport shows the bar', () => {
  const r = boot();
  r.io.fire(ABOVE);
  assert.strictEqual(r.bar.hidden, false);
});

test('the heading in view hides it', () => {
  const r = boot();
  r.io.fire(ABOVE);
  r.io.fire(IN_VIEW);
  assert.strictEqual(r.bar.hidden, true,
    'a heading in view is a bar hidden -- the bar never sits over the line it mirrors.');
});

test('the heading below the fold does NOT show it', () => {
  // Not intersecting is not enough: on arrival the count line is below the
  // panel, and a bar then would sit over the header and the filters.
  const r = boot();
  r.io.fire(BELOW);
  assert.strictEqual(r.bar.hidden, true,
    'not intersecting with its top BELOW the viewport is the arrival state, '
    + 'and the bar must not cover the panel there.');
});

// --- what it shows -------------------------------------------------------------

test('it mirrors the number, the word and the clear-all\'s visibility', () => {
  const r = boot();
  r.io.fire(ABOVE);
  assert.strictEqual(r.barN.textContent, '42');
  assert.strictEqual(r.barWord.textContent, 'survivors');
  assert.strictEqual(r.barClear.style.visibility, 'visible');
});

test('with nothing to clear, its clear-all is hidden too', () => {
  const r = boot({ clearVisibility: 'hidden' });
  r.io.fire(ABOVE);
  assert.strictEqual(r.barClear.style.visibility, 'hidden',
    'the bar only offers clearing when the index\'s own button does.');
});

test('it follows the count while it is up, through the mutation observer', () => {
  const r = boot();
  r.io.fire(ABOVE);
  assert.ok(r.mo, 'no MutationObserver was constructed.');
  const watched = r.mo.observed.map((o) => o.el);
  assert.ok(watched.indexOf(r.n) !== -1, 'the number span is not observed.');
  assert.ok(watched.indexOf(r.w) !== -1, 'the word span is not observed.');
  assert.ok(watched.indexOf(r.topClear) !== -1,
    'the top clear-all is not observed, so its visibility could not be followed.');

  r.n.textContent = '1';
  r.w.textContent = 'survivor';
  r.topClear.style.visibility = 'hidden';
  r.mo.fire();
  assert.strictEqual(r.barN.textContent, '1');
  assert.strictEqual(r.barWord.textContent, 'survivor');
  assert.strictEqual(r.barClear.style.visibility, 'hidden');
});

test('without a MutationObserver it still shows the right numbers when it appears', () => {
  const r = boot({ noMutationObserver: true });
  r.n.textContent = '7';
  r.io.fire(ABOVE);
  assert.strictEqual(r.barN.textContent, '7',
    'every observer report resyncs, so a browser without MutationObserver '
    + 'still gets the current count each time the bar appears.');
});

// --- what its button does ------------------------------------------------------

test('its clear-all presses the index\'s TOP clear-all, and only that one', () => {
  const r = boot();
  r.io.fire(ABOVE);
  r.barClear.dispatch('click');
  assert.strictEqual(r.topClear.clicks, 1,
    'the bar\'s button must forward to the index\'s top button -- the bar has '
    + 'no clearing of its own.');
  assert.strictEqual(r.bottomClear.clicks, 0);
});

test('the lookup for the top button skips the bar\'s own `.btn-clear`', () => {
  // The fixture puts the bar BEFORE the panel in the DOM, so "the first
  // .btn-clear" is the bar's own. Forwarding to itself would loop forever.
  const r = boot();
  r.io.fire(ABOVE);
  let barClicks = 0;
  r.barClear.addEventListener('click', () => { barClicks += 1; });
  r.barClear.dispatch('click');
  assert.strictEqual(barClicks, 1, 'the bar\'s button clicked itself.');
  assert.strictEqual(r.topClear.clicks, 1);
});

test('after its click the bar re-reads the count the index just repainted', () => {
  const r = boot();
  r.io.fire(ABOVE);
  // What clearAll() on either index does synchronously: repaint the count
  // and hide the clear-alls.
  r.topClear.addEventListener('click', () => {
    r.n.textContent = '99';
    r.topClear.style.visibility = 'hidden';
  });
  r.barClear.dispatch('click');
  assert.strictEqual(r.barN.textContent, '99');
  assert.strictEqual(r.barClear.style.visibility, 'hidden');
});

// --- both indexes, and the pages without the pieces --------------------------

test('it finds the cocktails index\'s count spans by their own ids', () => {
  const r = boot({ ids: DRINK_IDS });
  r.io.fire(ABOVE);
  assert.strictEqual(r.bar.hidden, false);
  assert.strictEqual(r.barN.textContent, '42');
  assert.strictEqual(r.barWord.textContent, 'survivors');
});

test('no IntersectionObserver: the bar stays hidden and the page is unchanged', () => {
  const r = boot({ noIntersectionObserver: true });
  assert.strictEqual(r.bar.hidden, true);
  assert.strictEqual(r.io, null);
  assert.strictEqual(r.mo, null, 'nothing should be wired at all without the API that reveals the bar.');
  r.barClear.dispatch('click');
  assert.strictEqual(r.topClear.clicks, 0,
    'a bar that can never show must not have a live button behind it.');
});

test('a page with a heading but no count spans wires nothing', () => {
  const r = boot({ ids: null });
  assert.strictEqual(r.io, null);
  assert.strictEqual(r.bar.hidden, true);
  assert.strictEqual(r.jump.hidden, true);
});

// --- the jump pill (#1441) ------------------------------------------------------

test('the pill stays hidden until the observer has spoken', () => {
  const r = boot();
  assert.strictEqual(r.jump.hidden, true,
    'the pill must not appear on its own: only an observer report reveals it.');
});

test('the count line below the fold shows the pill and not the bar', () => {
  // The arrival state on a phone: the count line is under the filters.
  const r = boot();
  r.io.fire(BELOW);
  assert.strictEqual(r.jump.hidden, false);
  assert.strictEqual(r.bar.hidden, true);
});

test('the count line in view hides the pill', () => {
  const r = boot();
  r.io.fire(BELOW);
  r.io.fire(IN_VIEW);
  assert.strictEqual(r.jump.hidden, true,
    'with the count on screen there is nothing to jump to.');
});

test('the count line above the viewport hides the pill and shows the bar', () => {
  // Only one floating copy of the count at a time: past the count the bar
  // stands in for it.
  const r = boot();
  r.io.fire(BELOW);
  r.io.fire(ABOVE);
  assert.strictEqual(r.jump.hidden, true);
  assert.strictEqual(r.bar.hidden, false);
});

test('the pill mirrors the number and the word, and follows them', () => {
  const r = boot();
  r.io.fire(BELOW);
  assert.strictEqual(r.jumpN.textContent, '42');
  assert.strictEqual(r.jumpWord.textContent, 'survivors');

  r.n.textContent = '1';
  r.w.textContent = 'survivor';
  r.mo.fire();
  assert.strictEqual(r.jumpN.textContent, '1');
  assert.strictEqual(r.jumpWord.textContent, 'survivor');
});

test('the pill shows "0 survivors" too, since the empty state is where it leads', () => {
  const r = boot();
  r.n.textContent = '0';
  r.io.fire(BELOW);
  assert.strictEqual(r.jump.hidden, false);
  assert.strictEqual(r.jumpN.textContent, '0');
});

test('pressing the pill scrolls the count line to the top, smoothly, and focuses it', () => {
  const r = boot({ reduceMotion: false });
  r.io.fire(BELOW);
  r.jump.dispatch('click');
  assert.strictEqual(plain(r.heading._scrollCalls), plain([{ behavior: 'smooth', block: 'start' }]));
  assert.strictEqual(r.heading.getAttribute('tabindex'), '-1',
    'a div or p takes focus only with a tabindex.');
  assert.strictEqual(plain(r.heading._focusCalls), plain([{ preventScroll: true }]),
    'focus must not scroll again, or it cancels the smooth scroll.');
});

test('with reduced motion asked for, the pill jumps at once', () => {
  const r = boot({ reduceMotion: true });
  r.io.fire(BELOW);
  r.jump.dispatch('click');
  assert.strictEqual(plain(r.heading._scrollCalls), plain([{ behavior: 'auto', block: 'start' }]));
});

test('the pill leaves a tabindex the count line already has alone', () => {
  const r = boot();
  r.heading.setAttribute('tabindex', '0');
  r.jump.dispatch('click');
  assert.strictEqual(r.heading.getAttribute('tabindex'), '0');
});

test('no IntersectionObserver: the pill stays hidden and has no live click', () => {
  const r = boot({ noIntersectionObserver: true });
  assert.strictEqual(r.jump.hidden, true);
  r.jump.dispatch('click');
  assert.strictEqual(r.heading._scrollCalls, undefined);
});

test('a page with the pill and no bar still wires the pill', () => {
  const r = boot({ noBar: true });
  r.io.fire(BELOW);
  assert.strictEqual(r.jump.hidden, false);
  assert.strictEqual(r.jumpN.textContent, '42');
});

test('a count line peeking over the bottom edge still shows the pill', () => {
  // A sliver of the line at the screen's foot is not something a reader has
  // seen; the pill goes once the whole line is on screen.
  const r = boot();
  r.io.fire(PEEKING);
  assert.strictEqual(r.jump.hidden, false);
  assert.strictEqual(r.bar.hidden, true);
});

test('a jump from the foot of the page to the top puts the pill back and the bar away', () => {
  // No observer report arrives for this: the line goes from above to below
  // without crossing the screen. The scroll listener is what notices.
  const r = boot();
  r.io.fire(ABOVE);
  assert.strictEqual(r.bar.hidden, false);
  r.scrollTo({ top: 1400, bottom: 1430 });
  assert.strictEqual(r.bar.hidden, true,
    'the bar left up after a jump to the top would sit over the header.');
  assert.strictEqual(r.jump.hidden, false);
});

test('a jump from the top to the foot of the page swaps them the other way', () => {
  const r = boot();
  r.io.fire(BELOW);
  r.scrollTo({ top: -3000, bottom: -2970 });
  assert.strictEqual(r.jump.hidden, true);
  assert.strictEqual(r.bar.hidden, false);
});

test('scrolling re-reads the line at most once a frame', () => {
  const r = boot();
  let reads = 0;
  const real = r.heading.getBoundingClientRect.bind(r.heading);
  r.heading.getBoundingClientRect = () => { reads += 1; return real(); };
  r.heading.__box = { top: 1400, bottom: 1430 };
  r.scrollHandlers.forEach((fn) => fn());
  r.scrollHandlers.forEach((fn) => fn());
  r.scrollHandlers.forEach((fn) => fn());
  r.scrollTo({ top: 1400, bottom: 1430 });
  assert.strictEqual(reads, 1, 'three scroll events before a frame are one read.');
});

test('no IntersectionObserver: no scroll listener either', () => {
  const r = boot({ noIntersectionObserver: true });
  assert.strictEqual(r.scrollHandlers.length, 0);
});

test('a page with the bar and no pill behaves as before', () => {
  const r = boot({ noJump: true });
  r.io.fire(BELOW);
  assert.strictEqual(r.bar.hidden, true);
  r.io.fire(ABOVE);
  assert.strictEqual(r.bar.hidden, false);
});
