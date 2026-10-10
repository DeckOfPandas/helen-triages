// =============================================================================
// Tests for assets/js/filter-fold.js -- the phone fold on both indexes. #1219,
// Helen, 2026-10-10, from a candidates page: "The mobile view is simplest:
// sections fold."
//
//   node --test tests/js/*.test.js
// =============================================================================
// WHAT THE SCRIPT OWNS IS SMALL, and each test is one piece of it: which
// sections start folded, what a tap on the row does and when it does nothing,
// and the chosen-chip count. Whether a folded section is actually out of sight
// is the stylesheet's (`_sass/shared/_filter-fold.scss`), and this stub has no
// layout to ask.
//
// `getComputedStyle` IS STUBBED HERE, one property deep: the script asks the
// stylesheet whether the mark is displayed rather than restating the
// breakpoint, so a test says "phone" or "wide" by saying what that returns.
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const { createDocument } = require('./dom-stub.js');

const SRC = fs.readFileSync(
  path.join(__dirname, '..', '..', 'assets', 'js', 'filter-fold.js'), 'utf8');

class StubMutationObserver {
  constructor(callback) {
    this.callback = callback;
    StubMutationObserver.instances.push(this);
  }
  observe(el, options) { this.el = el; this.options = options; }
  fire() { this.callback([], this); }
}
StubMutationObserver.instances = [];

/** Three chip sections in the shape both indexes emit, then the script. */
function boot(options) {
  options = options || {};
  StubMutationObserver.instances = [];
  const doc = createDocument();
  const el = (tag, attrs) => {
    const node = doc.createElement(tag);
    Object.entries(attrs || {}).forEach(([k, v]) => node.setAttribute(k, v));
    return node;
  };

  const sections = ['star', 'mood', 'practicalities'].map((name) => {
    const section = el('div', { class: 'category', id: 'filter-' + name, 'data-fold': '' });
    const head = el('div', { 'data-fold-head': '' });
    const label = el('span', { 'data-fold-label': '' });
    label.textContent = name.toUpperCase();
    const count = el('span', { 'data-fold-count': '' });
    count.hidden = true;
    const clear = el('button', { class: 'btn-clear-inline' });
    const mark = el('button', { 'data-fold-mark': '', 'aria-expanded': 'true' });
    mark.hidden = true;
    [label, count, clear, mark].forEach((n) => head.appendChild(n));
    const body = el('div', { 'data-fold-body': '' });
    const chips = ['a', 'b', 'c'].map(() => {
      const chip = el('button', { 'aria-pressed': 'false' });
      body.appendChild(chip);
      return chip;
    });
    section.appendChild(head);
    section.appendChild(body);
    doc.body.appendChild(section);
    return { section, head, label, count, clear, mark, body, chips };
  });

  const timers = [];
  const sandbox = {
    document: doc,
    location: { hash: options.hash || '' },
    setTimeout: (fn) => { timers.push(fn); },
    console: { warn() {}, error() {}, log() {} }
  };
  if (!options.noComputedStyle) {
    sandbox.getComputedStyle = () => ({ display: options.wide ? 'none' : 'inline-block' });
  }
  if (!options.noMutationObserver) sandbox.MutationObserver = StubMutationObserver;
  sandbox.window = sandbox;
  vm.runInContext(SRC, vm.createContext(sandbox), { filename: 'filter-fold.js' });
  doc.dispatch('DOMContentLoaded');

  const flush = () => { while (timers.length) timers.shift()(); };
  return { doc, sections, flush };
}

const folded = (s) => s.section.classList.contains('is-folded');

test('the first section starts open and the rest folded', () => {
  const r = boot();
  assert.deepStrictEqual(r.sections.map(folded), [false, true, true]);
});

test('the mark is revealed, says which way it goes, and is named by the label', () => {
  const r = boot();
  const [open, shut] = r.sections;
  assert.strictEqual(open.mark.hidden, false, 'the script reveals the mark it ships hidden.');
  assert.strictEqual(open.mark.textContent, '−');
  assert.strictEqual(open.mark.getAttribute('aria-expanded'), 'true');
  assert.strictEqual(shut.mark.textContent, '+');
  assert.strictEqual(shut.mark.getAttribute('aria-expanded'), 'false');
  assert.strictEqual(shut.mark.getAttribute('aria-label'), 'MOOD',
    'the accessible name is the section\'s own label, not words of the script\'s.');
});

test('a section the URL fragment names starts open too', () => {
  const r = boot({ hash: '#filter-practicalities' });
  assert.deepStrictEqual(r.sections.map(folded), [false, true, false],
    'a tag on a recipe page links to its section (#1059); folded, the lit chip would be hidden.');
});

test('a tap on the mark, or anywhere on the row, toggles the section', () => {
  const r = boot();
  const mood = r.sections[1];
  mood.mark.click();
  assert.strictEqual(folded(mood), false);
  assert.strictEqual(mood.mark.textContent, '−');
  mood.label.click();
  assert.strictEqual(folded(mood), true, 'the whole row is the control, not only the mark.');
});

test('the section\'s own clear button in the row does not fold it', () => {
  const r = boot();
  const star = r.sections[0];
  star.clear.click();
  assert.strictEqual(folded(star), false);
});

test('above phone width a tap on the row does nothing', () => {
  const r = boot({ wide: true });
  const mood = r.sections[1];
  mood.label.click();
  assert.strictEqual(folded(mood), true,
    'the class is inert on a wide screen; toggling it there would change what a later narrow view shows.');
});

test('the count is the chips pressed in that section, and hides at none', () => {
  const r = boot();
  const mood = r.sections[1];
  assert.strictEqual(mood.count.hidden, true);
  mood.chips[0].setAttribute('aria-pressed', 'true');
  mood.chips[2].setAttribute('aria-pressed', 'true');
  mood.chips[0].click();
  r.flush();
  assert.strictEqual(mood.count.textContent, '2');
  assert.strictEqual(mood.count.hidden, false);
  assert.strictEqual(r.sections[0].count.hidden, true, 'one section\'s chips are not another\'s count.');

  // `x clear all` presses nothing inside the section; the observer catches it.
  mood.chips.forEach((c) => c.setAttribute('aria-pressed', 'false'));
  StubMutationObserver.instances.forEach((o) => o.fire());
  assert.strictEqual(mood.count.textContent, '');
  assert.strictEqual(mood.count.hidden, true);
});

test('it watches aria-pressed on the chips, and nothing wider', () => {
  const r = boot();
  const seen = StubMutationObserver.instances[1];
  assert.strictEqual(seen.el, r.sections[1].body);
  // joined, because an array made inside the vm sandbox is another realm's
  // Array and deepStrictEqual compares prototypes
  assert.strictEqual(seen.options.attributeFilter.join(','), 'aria-pressed');
});

test('a chip already pressed at load is counted on the first paint', () => {
  // filters.js sets a filter from the URL inside its own DOMContentLoaded
  // handler, which runs first; this is that state arriving before the script.
  StubMutationObserver.instances = [];
  const doc = createDocument();
  const section = doc.createElement('div');
  section.setAttribute('data-fold', '');
  const head = doc.createElement('div');
  head.setAttribute('data-fold-head', '');
  const count = doc.createElement('span');
  count.setAttribute('data-fold-count', '');
  const mark = doc.createElement('button');
  mark.setAttribute('data-fold-mark', '');
  head.appendChild(count);
  head.appendChild(mark);
  const body = doc.createElement('div');
  body.setAttribute('data-fold-body', '');
  const chip = doc.createElement('button');
  chip.setAttribute('aria-pressed', 'true');
  body.appendChild(chip);
  section.appendChild(head);
  section.appendChild(body);
  doc.body.appendChild(section);
  const sandbox = { document: doc, location: { hash: '' }, setTimeout() {} };
  sandbox.window = sandbox;
  vm.runInContext(SRC, vm.createContext(sandbox), { filename: 'filter-fold.js' });
  doc.dispatch('DOMContentLoaded');
  assert.strictEqual(count.textContent, '1');
});

test('without getComputedStyle or MutationObserver it still folds', () => {
  const r = boot({ noComputedStyle: true, noMutationObserver: true });
  const mood = r.sections[1];
  mood.mark.click();
  assert.strictEqual(folded(mood), false);
});

test('a page with no foldable section is left alone', () => {
  const doc = createDocument();
  const sandbox = { document: doc, location: { hash: '' }, setTimeout() {} };
  sandbox.window = sandbox;
  vm.runInContext(SRC, vm.createContext(sandbox), { filename: 'filter-fold.js' });
  assert.doesNotThrow(() => doc.dispatch('DOMContentLoaded'));
});
