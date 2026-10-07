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

test('a card showing its tagline keeps the cap it had', () => {
  // #1292. While the tagline has the card the ingredient line is
  // `display: none` and measures zero. Without the guard a re-run would take
  // the cap away, and the chips would get a third row back when the card
  // flipped to ingredients again.
  const c = card(LH * 3, LH, true);
  run([c]);
  assert.strictEqual(c.capped(), true);

  c.classList.add('is-tagline-shown');
  c._line.getBoundingClientRect = () => ({ height: 0 });
  run([c]);
  assert.strictEqual(c.capped(), true, 'a hidden line is not a measurement');
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

// -----------------------------------------------------------------------------
// THE CHIPS ARE PACKED -- #1308. Helen: "it feels like there's lots of space on
// the right-hand side of the tag block", and "allowing tags to wrap if we tweak
// the order rather than requiring them to be alphabetical".
//
// `HTF.packChips` is the search with no DOM in it, so it is asked directly. The
// widths are the real ones, measured off the built index at 1280px: a chip's
// own width, and 14.5px more when another chip follows it (the dot).
// -----------------------------------------------------------------------------

const DOT = 14.5;

/** Chips from bare widths, in the alphabetical order the template gives. */
function chipWidths(bare) {
  return { adv: bare.map((w) => w + DOT), lastAdv: bare.slice() };
}

/**
 * Lay an order out the way `flex-wrap` does and say what was drawn -- the
 * test's own copy of the rule, so the search is checked against the browser's
 * behaviour rather than against itself.
 */
function draw(order, chips, W, cap, breaks) {
  // `breaks` is the search's own [chip, margin] list (#1331): a right margin
  // the browser counts as part of that chip when it decides what fits next,
  // and which is not part of how far the row's ink runs.
  const margin = {};
  (breaks || []).forEach((b) => { margin[b[0]] = b[1]; });
  const rows = [[]];
  let fill = 0;
  let taken = 0;
  order.forEach((i, at) => {
    const w = at === order.length - 1 ? chips.lastAdv[i] : chips.adv[i];
    if (taken > 0 && taken + w > W + 0.02) { rows.push([]); fill = 0; taken = 0; }
    rows[rows.length - 1].push(i);
    fill = taken + w;
    taken = fill + (margin[i] || 0);
    rows[rows.length - 1].fill = fill;
  });
  const shown = rows.slice(0, cap);
  return {
    rows: shown.map((r) => Array.from(r)),
    visible: shown.reduce((n, r) => n + r.length, 0),
    shipRow: shown[shown.length - 1].fill
  };
}

function packer() {
  return run([]).HTF.packChips;
}

test('chips that fit one row stay in alphabetical order', () => {
  // Royal Bermuda Yacht Club: sharp, sunny terrace, tiki. One row, short of
  // the ship: there is nothing to pack, and alphabetical is the tie-break.
  const chips = chipWidths([35, 91, 28]);
  const got = packer()(chips.adv, chips.lastAdv, 0,
    { W: 278.4, lastW: 216.9, cap: 3 });
  assert.deepStrictEqual(Array.from(got.order), [0, 1, 2]);
  assert.strictEqual(got.visible, 3);
});

test('an order is found that frees the rows from the ship', () => {
  // German Vacation, the shape in the issue's screenshot. Alphabetically its
  // last row reaches the ship, so the block was padded clear and drew THREE
  // short rows: festive, ice ice baby / sharp, sugar craving / sunny terrace,
  // warming. Packed, it is two rows at the card's full width.
  const chips = chipWidths([49, 84, 35, 91, 91, 49]);
  const W = 278.4, lastW = 216.9;
  const alphabetical = draw([0, 1, 2, 3, 4, 5], chips, W, 3);
  assert.ok(alphabetical.shipRow > lastW, 'alphabetical runs into the ship');

  const got = packer()(chips.adv, chips.lastAdv, 0,
    { W: W, lastW: lastW, cap: 3 });
  const drawn = draw(Array.from(got.order), chips, W, 3, got.breaks);
  assert.strictEqual(drawn.visible, 6, 'every chip is shown');
  assert.strictEqual(drawn.rows.length, 2, 'in two rows, not three');
  assert.ok(drawn.shipRow <= lastW, 'and the last row stops short of the ship');
  assert.deepStrictEqual(Array.from(got.order), [0, 1, 2, 5, 3, 4],
    'festive, ice ice baby, sharp, warming / sugar craving, sunny terrace');
});

test('the upper rows are filled as full as they will go', () => {
  // HELEN'S PICK, 2026-10-06: "Option C, chef's kiss!" Moscow Mule already
  // fitted two rows alphabetically -- ice ice baby, sharp, sugar craving /
  // sunny terrace -- and a rule that only mended broken cards left it alone.
  // This one does not: sharp, sugar craving, sunny terrace fills the first row
  // 7px further, so that is the first row, and the rows step down.
  const chips = chipWidths([84, 35, 91, 91]);
  const W = 278.4;
  const got = packer()(chips.adv, chips.lastAdv, 0,
    { W: W, lastW: 216.9, cap: 3 });
  assert.deepStrictEqual(Array.from(got.order), [1, 2, 3, 0]);
  const drawn = draw(Array.from(got.order), chips, W, 3, got.breaks);
  assert.strictEqual(drawn.rows.length, 2, 'no more rows than it had');
  // Within a row the tie is alphabetical, which is why it still reads in order.
  assert.deepStrictEqual(drawn.rows[0], [1, 2, 3]);
});

test('a chip is not clipped when another order shows it', () => {
  // Hurricane (classic), capped at two rows by its three ingredient lines.
  // brunch, fruity, I want to faff, ice ice baby, sugar craving, tiki.
  const chips = chipWidths([42, 42, 98, 84, 91, 28]);
  const W = 278.4, lastW = 209.3;
  const got = packer()(chips.adv, chips.lastAdv, 0,
    { W: W, lastW: lastW, cap: 2 });
  const drawn = draw(Array.from(got.order), chips, W, 2, got.breaks);
  assert.strictEqual(drawn.visible, 6);
  assert.ok(drawn.shipRow <= lastW);
});

test('chips matching a filter keep the front of the row', () => {
  // #757: the chip that explains why the card is here is never the one moved
  // back, whatever would pack better.
  const chips = chipWidths([91, 49, 84, 35, 91, 49]);
  const got = packer()(chips.adv, chips.lastAdv, 2,
    { W: 278.4, lastW: 216.9, cap: 3 });
  assert.deepStrictEqual(Array.from(got.order).slice(0, 2), [0, 1]);
  assert.strictEqual(Array.from(got.order).slice().sort().join(), '0,1,2,3,4,5',
    'and every chip is still in the order exactly once');
});

test('no order is offered when none keeps the ship\'s row short', () => {
  // One chip, wider than the room left of the ship: there is nothing to
  // arrange, and the caller falls back to padding the chips clear.
  const chips = chipWidths([200]);
  const got = packer()(chips.adv, chips.lastAdv, 0,
    { W: 250, lastW: 150, cap: 1 });
  assert.strictEqual(got, null);
});

// -----------------------------------------------------------------------------
// A ROW MAY BE ENDED EARLY -- #1331, 2026-10-07. Helen: "sometimes chips on
// cards don't wrap properly -- varies with screen width", seen between about
// 822px and 915px. The widths below are the real ones at 830px, where a card's
// foot is 243.4px and the ship starts 174.3px along it.
// -----------------------------------------------------------------------------

test('chips that fit one full row but not beside the ship split in two', () => {
  // Jungle Bird: aperitivo, fruity, sharp, tiki. All four fit the foot's full
  // width, so greedy wrapping draws one row -- into the ship -- whatever the
  // order. Before this the only way out was the padding, which drew
  // `aperitivo, fruity / sharp, tiki` in a block 159px wide.
  const chips = chipWidths([63, 42, 35, 28]);
  const W = 243.4, lastW = 174.3;
  const oneRow = draw([0, 1, 2, 3], chips, W, 3);
  assert.strictEqual(oneRow.rows.length, 1, 'left alone, it is one row');
  assert.ok(oneRow.shipRow > lastW, 'and that row reaches the ship');

  const got = packer()(chips.adv, chips.lastAdv, 0, { W: W, lastW: lastW, cap: 3 });
  const drawn = draw(Array.from(got.order), chips, W, 3, got.breaks);
  assert.deepStrictEqual(drawn.rows, [[0, 1, 2], [3]],
    'aperitivo, fruity, sharp / tiki: the first row as full as it will go');
  assert.ok(drawn.shipRow <= lastW);
  assert.strictEqual(got.breaks.length, 1);
  assert.strictEqual(got.breaks[0][0], 2, 'the row is closed off after sharp');
});

test('no row is ended early where wrapping alone does the job', () => {
  // German Vacation at 1280px, from #1308: its chips do not fit one row, so
  // the order is enough and nothing needs a margin.
  const chips = chipWidths([49, 84, 35, 91, 91, 49]);
  const got = packer()(chips.adv, chips.lastAdv, 0,
    { W: 278.4, lastW: 216.9, cap: 3 });
  assert.strictEqual(got.breaks.length, 0);
});

test('a chip is clipped rather than drawn into the ship on a one-row card', () => {
  // One row allowed and two chips that both fit it but not beside the ship.
  // The second is closed off, not left to be drawn under the verdict; the
  // caller then asks whether the padded width would show more.
  const chips = chipWidths([100, 100]);
  const W = 250, lastW = 150;
  const got = packer()(chips.adv, chips.lastAdv, 0, { W: W, lastW: lastW, cap: 1 });
  assert.strictEqual(got.visible, 1);
  const drawn = draw(Array.from(got.order), chips, W, 1, got.breaks);
  assert.strictEqual(drawn.visible, 1);
  assert.ok(drawn.shipRow <= lastW);
});

test('the chips past the cap are the ones that cannot come back', () => {
  // Three rows allowed and more chips than fit. The first clipped chip must
  // be one that does NOT fit on the ship's row, or the browser would draw it
  // there and push the row into the ship.
  const chips = chipWidths([35, 70, 84, 56, 70, 63, 133, 126, 28, 49]);
  const W = 278.4, lastW = 209.3;
  const got = packer()(chips.adv, chips.lastAdv, 0,
    { W: W, lastW: lastW, cap: 3 });
  const drawn = draw(Array.from(got.order), chips, W, 3, got.breaks);
  assert.strictEqual(drawn.visible, got.visible,
    'what the search counted as shown is what the browser would draw');
  assert.ok(drawn.shipRow <= lastW);
  assert.ok(got.visible >= 9, 'Better and Better shows nine of its ten');
});
