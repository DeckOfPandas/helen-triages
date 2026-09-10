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

// -----------------------------------------------------------------------------
// THE SHIP AND THE LAST CHIP ROW, 2026-09-10. #760 took the verdict out of flow
// and masked it over the chips; Helen saw "sugar crav" and "strong brown drin"
// on the live index the same evening. The pass now measures whether a chip on
// the ship's row reaches past the ship's left edge, and only then marks the
// card so the stylesheet can pad that card's chips clear.
// -----------------------------------------------------------------------------

/**
 * A card with a ship at `ship` and chips at `chips` (each {top, bottom, left,
 * right}); the ingredient line is one line so the other rule stays quiet.
 */
function cardWithShip(ship, chips) {
  const c = card(LH, LH, true);
  const props = {};
  c.style = {
    setProperty: (k, v) => { props[k] = v; },
    removeProperty: (k) => { delete props[k]; }
  };
  c._props = props;
  const moods = {
    querySelectorAll: () => chips.map((r) => ({ getBoundingClientRect: () => r }))
  };
  const shipEl = ship ? { getBoundingClientRect: () => ship } : null;
  const base = c.querySelector;
  c.querySelector = (sel) => {
    if (sel === '.drink-card-ship') return shipEl;
    if (sel === '.drink-card-moods') return moods;
    return base(sel);
  };
  c.cleared = () => c.classList.contains('drink-card--chips-clear-ship');
  return c;
}

const SHIP = { top: 40, bottom: 56, left: 240, right: 300, width: 60 };

test('a chip on the ship\'s row that reaches the ship marks the card', () => {
  const c = cardWithShip(SHIP, [
    { top: 20, bottom: 36, left: 0, right: 290 },   // row above: not in the way
    { top: 40, bottom: 56, left: 0, right: 250 }    // last row, crosses 240
  ]);
  run([c]);
  assert.strictEqual(c.cleared(), true);
  assert.strictEqual(c._props['--ship-w'], '60px',
    'the stylesheet pads by the ship\'s own measured width');
});

test('a chip that stops short of the ship leaves the card alone', () => {
  const c = cardWithShip(SHIP, [
    { top: 40, bottom: 56, left: 0, right: 200 }
  ]);
  run([c]);
  assert.strictEqual(c.cleared(), false);
});

test('a wide chip on a row ABOVE the ship is not a collision', () => {
  // The ship sits on the last row only; a full-width first row is fine.
  const c = cardWithShip(SHIP, [
    { top: 20, bottom: 36, left: 0, right: 300 },
    { top: 40, bottom: 56, left: 0, right: 120 }
  ]);
  run([c]);
  assert.strictEqual(c.cleared(), false);
});

test('the mark comes off again when a re-run no longer earns it', () => {
  const rows = [{ top: 40, bottom: 56, left: 0, right: 250 }];
  const c = cardWithShip(SHIP, rows);
  run([c]);
  assert.strictEqual(c.cleared(), true);
  rows[0].right = 200;
  run([c]);
  assert.strictEqual(c.cleared(), false, 'a state, not a ratchet');
  assert.strictEqual(c._props['--ship-w'], undefined);
});

test('a hidden card, whose ship measures zero, is skipped', () => {
  const c = cardWithShip({ top: 0, bottom: 0, left: 0, right: 0, width: 0 }, [
    { top: 0, bottom: 0, left: 0, right: 0 }
  ]);
  run([c]);
  assert.strictEqual(c.cleared(), false);
});

test('a card with no ship is left alone', () => {
  const c = cardWithShip(null, [{ top: 40, bottom: 56, left: 0, right: 250 }]);
  run([c]);
  assert.strictEqual(c.cleared(), false);
});
