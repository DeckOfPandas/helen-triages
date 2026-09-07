// =============================================================================
// Tests for assets/js/card-line-budget.js — issue #776.
//
//   node --test tests/js/*.test.js
//
// WHAT THIS IS FOR. The script answers one question CSS cannot ask: how many
// lines did the ingredient line ACTUALLY render? `-webkit-line-clamp: 3` is a
// ceiling and most cards do not reach it, so a rule keyed on the clamp would
// cap the chips on every card for what the tiki drinks do.
//
// SO THE ARITHMETIC IS THE WHOLE OF IT, and it is the arithmetic that is easy
// to get subtly wrong: height divided by line-height, ROUNDED. Rounding rather
// than flooring is load-bearing — `line-height: 1.5` at `font-size: 0.82rem` is
// not a whole pixel and three lines can measure as 2.98, which floors to two and
// silently drops the rule on a card that visibly has three.
//
// THE DOM IS STUBBED, the way tests/js/cocktail-scale.test.js stubs one, and for
// the same stated reason: run the SHIPPED source byte for byte inside a fake
// `window` and read what it did. The stub carries only what the script touches —
// `querySelectorAll`, `querySelector`, `classList` and the two measurement APIs.
// =============================================================================
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const SOURCE = path.resolve(__dirname, '..', '..',
  'assets', 'js', 'card-line-budget.js');

/**
 * One card whose ingredient line reports `height` px at `lineHeight` px.
 *
 * @param {number} height     what getBoundingClientRect().height returns
 * @param {number} lineHeight what getComputedStyle().lineHeight returns
 * @param {boolean} hasLine   false to model a card with no ingredient line
 */
function card(height, lineHeight, hasLine) {
  const classes = new Set();
  const line = {
    getBoundingClientRect: () => ({ height }),
    _lineHeight: lineHeight
  };
  return {
    classList: {
      add: (c) => classes.add(c),
      remove: (c) => classes.delete(c),
      contains: (c) => classes.has(c)
    },
    querySelector: (sel) =>
      (sel === '.drink-card-ingredients' && hasLine !== false ? line : null),
    _line: line,
    capped: () => classes.has('drink-card--ingredients-3')
  };
}

/** Run the shipped source against these cards and hand them back. */
function run(cards) {
  const sandbox = {
    document: {
      readyState: 'complete',
      querySelectorAll: () => cards,
      addEventListener() {}
    },
    getComputedStyle: (el) => ({
      lineHeight: String(el._lineHeight),
      fontSize: '13.12px'
    }),
    addEventListener() {}
  };
  sandbox.window = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(SOURCE, 'utf8'), sandbox, { filename: SOURCE });
  return sandbox;
}

// The real values: font-size 0.82rem on a 16px root is 13.12px, line-height 1.5
// gives 19.68px. Two lines is 39.36, three is 59.04.
const LH = 19.68;

test('two lines of ingredients leave the chips alone', () => {
  const c = card(LH * 2, LH, true);
  run([c]);
  assert.strictEqual(c.capped(), false,
    'the median drink fits two lines and must not lose a chip row for it');
});

test('three lines of ingredients cap the chips', () => {
  const c = card(LH * 3, LH, true);
  run([c]);
  assert.strictEqual(c.capped(), true);
});

test('a fractional three lines still counts as three', () => {
  // THE BUG THIS EXISTS FOR. Sub-pixel metrics make three lines measure just
  // under; flooring would call it two and drop the rule on a card that has
  // visibly overflowed.
  const c = card(LH * 3 - 0.4, LH, true);
  assert.strictEqual(Math.floor((LH * 3 - 0.4) / LH), 2, 'floor would say two');
  run([c]);
  assert.strictEqual(c.capped(), true, 'rounding says three, which is what it is');
});

test('one line is not three', () => {
  const c = card(LH, LH, true);
  run([c]);
  assert.strictEqual(c.capped(), false);
});

test('the class is removed again when a re-run no longer earns it', () => {
  // Reset-before-measure, the bug card-name-fit.js's step 1 exists to prevent:
  // without it a card widened by a resize can never lose the cap.
  const c = card(LH * 3, LH, true);
  run([c]);
  assert.strictEqual(c.capped(), true);

  c._line.getBoundingClientRect = () => ({ height: LH * 2 });
  run([c]);
  assert.strictEqual(c.capped(), false, 'it is a state, not a ratchet');
});

test('a card with no ingredient line is left alone', () => {
  const c = card(0, LH, false);
  run([c]);
  assert.strictEqual(c.capped(), false);
});

test('a non-numeric line-height falls back to the font size, not to 1', () => {
  // `line-height: normal` computes to a keyword in some engines. Falling back
  // to 1 would make every card report ~15 lines and cap every one of them.
  const c = card(LH * 2, NaN, true);
  run([c]);
  assert.strictEqual(c.capped(), false,
    'two real lines must not read as three via a broken line-height');
});

test('it hangs itself off HTF so the index can re-run it', () => {
  const sandbox = run([card(LH, LH, true)]);
  assert.strictEqual(typeof sandbox.HTF.cardLineBudget, 'function');
});
