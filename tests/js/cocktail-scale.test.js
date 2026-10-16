// Tests for assets/js/cocktail-scale.js, the scaler's DOM half.
//
//   node --test tests/js/*.test.js
//
// scale.test.js covers the maths. This covers the wiring, which a pure test of
// scale.js cannot see: what the script writes back into a box while someone is
// typing in it.
//
// The page is stubbed and the shipped source run byte for byte inside a fake
// `window`, as tests/js/stub-dom.js does for assets.js. The elements carry only
// what cocktail-scale.js touches; a fuller DOM would be a second browser to
// keep honest. `document.activeElement` is settable here, because a write-back
// bug shows only while a field has focus.
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const REPO_ROOT = path.resolve(__dirname, '..', '..');

/** One element: class, text, children, and the handful of methods used. */
function el(cls, text) {
  return {
    cls: cls,
    textContent: text || '',
    value: '',
    hidden: true,
    attrs: {},
    children: [],
    parent: null,
    on: {},
    classes: new Set((cls || '').split(' ').filter(Boolean)),
    get classList() {
      const self = this;
      return {
        contains: (name) => self.classes.has(name),
        add: (name) => self.classes.add(name),
        remove: (name) => self.classes.delete(name),
        toggle(name, on) {
          if (on === undefined) on = !self.classes.has(name);
          if (on) self.classes.add(name); else self.classes.delete(name);
          return on;
        }
      };
    },
    hasAttribute(name) { return name in this.attrs; },
    getAttribute(name) { return this.attrs[name]; },
    setAttribute(name, value) { this.attrs[name] = String(value); },
    removeAttribute(name) { delete this.attrs[name]; },
    add(child) { child.parent = this; this.children.push(child); return child; },
    descendants() {
      return this.children.reduce(
        (all, child) => all.concat([child], child.descendants()), []);
    },
    matches(selector) {
      return selector.split(',').some(
        (one) => ('.' + this.cls.split(' ').join('.')).includes(one.trim()));
    },
    querySelector(selector) { return this.querySelectorAll(selector)[0] || null; },
    querySelectorAll(selector) {
      return this.descendants().filter((node) => node.matches(selector));
    },
    closest(selector) {
      let node = this;
      while (node) {
        if (node.matches(selector)) return node;
        node = node.parent;
      }
      return null;
    },
    addEventListener(type, fn) {
      (this.on[type] = this.on[type] || []).push(fn);
    },
    fire(type) { (this.on[type] || []).forEach((fn) => fn()); }
  };
}

/**
 * A drink page with the control on it, with the real scripts run into it.
 *
 * @param {Array<[string, string]>} pours - `[amount, ingredient name]` pairs
 * @returns {Object} the pieces a test asserts against
 */
function page(pours, opts) {
  opts = opts || {};
  const article = el('cocktail');
  const control = article.add(el('cocktail-scale-controls'));
  /* The two step buttons sit either side of the input in the real markup (#731)
     and are added here in that order: the shipped source must find the same
     `.cocktail-scale-minus` and `.cocktail-scale-plus` it finds on the page. */
  const minus = control.add(el('cocktail-scale-step cocktail-scale-minus'));
  const input = control.add(el('cocktail-scale-multiple'));
  const plus = control.add(el('cocktail-scale-step cocktail-scale-plus'));
  /* No `.cocktail-scale-note` (#1088): the shipped layout has none. A fixture
     that supplied one would go on passing if cocktail-scale.js's init guard
     demanded it again, which would blank every drink's scaler in production. */
  const list = article.add(el('cocktail-ingredients'));

  /* The batch note and the two figure lines are opt-in, because each is
     conditional in the layout: the note is rendered only for a drink with
     dashes, and the cost line only where `site.show_costs` is set. A page
     without them is a real shape, not a degenerate one. */
  const batch = opts.batch === false ? null : article.add(el('cocktail-scale-batch'));
  if (batch) {
    batch.setAttribute('data-has-dashes', opts.hasDashes ? 'true' : 'false');
  }
  const cost = opts.cost ? article.add(el('cocktail-cost')) : null;
  if (cost) {
    cost.setAttribute('data-cost-min', opts.cost[0]);
    cost.setAttribute('data-cost-max', opts.cost[1]);
  }
  const units = opts.units ? article.add(el('cocktail-units')) : null;
  if (units) {
    units.setAttribute('data-units-per-serve', opts.units[0]);
    units.setAttribute('data-serves', opts.units[1] === undefined ? 1 : opts.units[1]);
  }

  /* `opts.totalMl` is the plugin's volume, on the controls, and the script
     never reads it (#1257); the attribute is on the page for the glass-fit
     report. It is set here so a test can say the script leaves it alone. */
  if (opts.totalMl !== undefined) {
    control.setAttribute('data-total-ml', opts.totalMl);
  }

  /* A third element is a row the layout marked quiet (#1132). `written` is the
     recipe's own amount, which _layouts/cocktail.html keeps in `data-amount`
     while printing the number alone; `slot` is the unit it moved to the end of
     the name, absent for an `each` row. */
  const slots = [];
  /* A fourth element, `'dashes'`, is a row the layout marked (#1293):
     `data-dashes` on the amount and a hidden `*` beside it. */
  const stars = [];
  const spans = pours.map(([amount, name, quiet, dashes]) => {
    const li = list.add(el('cocktail-ingredient'));
    const span = li.add(el('cocktail-amount', amount));
    if (dashes) {
      span.setAttribute('data-dashes', '');
      const star = li.add(el('cocktail-amount-star', '*'));
      star.hidden = true;
      stars.push(star);
    }
    const item = li.add(el('cocktail-item-name', name));
    if (quiet) {
      span.setAttribute('data-amount', quiet.written);
      span.setAttribute('data-unit-quiet', '');
      slots.push(quiet.slot ? item.add(el('cocktail-unit-in-name', quiet.slot)) : null);
    } else {
      slots.push(null);
    }
    return span;
  });

  const sandbox = {
    document: {
      querySelector: (s) => (s === 'article.cocktail' ? article : null),
      activeElement: null
    },
    console: { warn() {}, log() {}, error() {} }
  };
  sandbox.window = sandbox;
  vm.createContext(sandbox);
  for (const file of ['assets/js/shopping-list.js', 'assets/js/scale.js',
                      'assets/js/cocktail-scale.js']) {
    vm.runInContext(fs.readFileSync(path.join(REPO_ROOT, file), 'utf8'),
                    sandbox, { filename: file });
  }

  return {
    sandbox, control, input, minus, plus, spans, list, batch, cost, units, slots, stars,
    amounts: () => spans.map((s) => s.textContent),
    /** Type into a box the way a browser does: focus it, then `input`. */
    type(box, text) {
      sandbox.document.activeElement = box;
      box.value = text;
      box.fire('input');
    },
    /** Leave the box, the way a browser does: `change`, `blur`, then focus goes. */
    leave(box) {
      box.fire('change');
      box.fire('blur');
      sandbox.document.activeElement = null;
    },
    /** Click a button the way a browser does: one `click` event, nothing else. */
    click(button) {
      button.fire('click');
    }
  };
}

/** The Aviation, so every total is checkable by eye: 52.5 + 15 + 7.5 + 15 = 90. */
const AVIATION = [
  ['52.5 ml', 'London dry gin'], ['15 ml', 'maraschino liqueur'],
  ['7.5 ml', 'crème de violette'], ['15 ml', 'lemon juice']
];

test('the control reveals itself and starts at the recipe as written', () => {
  const p = page(AVIATION);
  assert.strictEqual(p.control.hidden, false,
    'the markup ships `hidden`; revealing it is the proof the script ran');
  assert.strictEqual(p.input.value, '1');
  assert.deepStrictEqual(p.amounts(),
    ['52.5 ml', '15 ml', '7.5 ml', '15 ml'], 'the recipe as written');
});

test('typing a multiple rewrites every amount', () => {
  const p = page(AVIATION);
  p.type(p.input, '2');
  assert.deepStrictEqual(p.amounts(), ['105 ml', '30 ml', '15 ml', '30 ml']);
});

// --- #1132: "1 cube sugar cube" ----------------------------------------------
// The layout prints "1" beside "sugar cube" and marks the amount quiet. The
// scaler must go on scaling the WRITTEN amount and keep the two halves where
// the layout put them -- an unmarked write would bring the repeat straight
// back the first time anyone pressed +.

/** The Classic Champagne Cocktail's three lines, as the layout renders them. */
const CHAMPAGNE = [
  ['1', 'sugar', { written: '1 cube', slot: 'cube' }],
  ['2 dashes', 'aromatic bitters'],
  ['(top)', 'champagne']
];

test('#1132: a quiet row scales from the written amount, and the unit stays in the name', () => {
  const p = page(CHAMPAGNE);
  assert.deepStrictEqual(p.amounts(), ['1', '2 dashes', '(top)'], 'as the layout shipped it');

  p.type(p.input, '3');
  assert.deepStrictEqual(p.amounts(), ['3', '6 dashes', '(top)']);
  assert.strictEqual(p.slots[0].textContent, 'cubes', 'the plural moved into the name');

  p.type(p.input, '1');
  assert.deepStrictEqual(p.amounts(), ['1', '2 dashes', '(top)']);
  assert.strictEqual(p.slots[0].textContent, 'cube', 'and back, singular again');
});

test('#1132: an `each` row prints the number alone at every multiple', () => {
  // The Porn Star Martini's passion fruit: no slot, the unit is simply dropped.
  const p = page([['1.5', 'passion fruit', { written: '1.5 each' }], ['45 ml', 'vodka']]);
  p.type(p.input, '2');
  assert.deepStrictEqual(p.amounts(), ['3', '90 ml']);
  p.click(p.plus);
  assert.deepStrictEqual(p.amounts(), ['4.5', '135 ml']);
});

test('#1132: an unmarked row is written exactly as before', () => {
  // The same amounts beside a name that does not repeat the unit -- Arrack
  // Punch's "16 cubes raw sugar". No mark, so nothing is split.
  const p = page([['16 cubes', 'raw sugar'], ['3 leaves', 'basil']]);
  p.type(p.input, '2');
  assert.deepStrictEqual(p.amounts(), ['32 cubes', '6 leaves']);
});

// --- the keystroke guard -------------------------------------------------------
// `input` fires on every keystroke, and clearing the box to type a new number
// passes through the empty string. Neither is answered, and nothing is written
// over what is being typed.

test('the box can be emptied — nothing is written back into it', () => {
  const p = page(AVIATION);
  p.type(p.input, '2');
  const poured = p.amounts();
  for (const partial of ['', '0']) {
    p.type(p.input, partial);
    assert.strictEqual(p.input.value, partial,
      `typing "${partial}" left the box holding "${p.input.value}"`);
  }
  assert.deepStrictEqual(p.amounts(), poured, 'and the page holds still');
});

test('a decimal rounds to the nearest whole recipe', () => {
  const p = page(AVIATION);
  // Whole recipes only (#721): `1.5` becomes 2.
  p.type(p.input, '1.5');
  assert.deepStrictEqual(p.amounts(), ['105 ml', '30 ml', '15 ml', '30 ml']);
  p.leave(p.input);
  assert.strictEqual(p.input.value, '2', 'and the box says what was made');
});

test('one recipe is the floor, and a smaller ask settles there', () => {
  const p = page(AVIATION);
  // Half a drink is not a thing this page offers, and one is also what keeps
  // every pour on the 2.5 ml grid -- an integer multiple of a grid value is on
  // the grid, which is the whole reason integers were chosen.
  p.type(p.input, '0.4');
  assert.deepStrictEqual(p.amounts(),
    ['52.5 ml', '15 ml', '7.5 ml', '15 ml'], 'the recipe as written');
  p.leave(p.input);
  assert.strictEqual(p.input.value, '1');
});

test('every amount stays on the 2.5 ml grid at every multiple', () => {
  // The claim integers were chosen for, checked rather than asserted in prose.
  const p = page(AVIATION);
  for (const n of ['2', '3', '4', '7', '12']) {
    p.type(p.input, n);
    for (const amount of p.amounts()) {
      const ml = parseFloat(amount);
      assert.ok(Math.abs(ml / 2.5 - Math.round(ml / 2.5)) < 1e-9,
        `x${n} produced ${amount}, which is not on the 2.5 ml grid`);
    }
  }
});

test('the ratios are exactly the recipe, multiplied', () => {
  const p = page(AVIATION);
  p.type(p.input, '4');
  assert.deepStrictEqual(p.amounts(), ['210 ml', '60 ml', '30 ml', '60 ml']);
});

// --- the − and + step buttons, #731 ------------------------------------------
// Both buttons go through `apply()`, the function a typed value reaches
// (`step()` in cocktail-scale.js calls `apply(last ± 1)` and nothing else), so
// these tests ask one question: does a click land on the same code a keystroke
// does.

test('the plus button steps the multiple up by one, through the same apply() a typed value uses', () => {
  const p = page(AVIATION);
  p.click(p.plus);
  assert.strictEqual(p.input.value, '2');
  assert.deepStrictEqual(p.amounts(), ['105 ml', '30 ml', '15 ml', '30 ml']);
  p.click(p.plus);
  assert.strictEqual(p.input.value, '3');
  assert.deepStrictEqual(p.amounts(), ['157.5 ml', '45 ml', '22.5 ml', '45 ml']);
});

test('the minus button steps the multiple down by one', () => {
  const p = page(AVIATION);
  p.type(p.input, '3');
  // Clicking a button moves focus off the input the way a real browser does;
  // `leave` is the stub's way of saying "the box is no longer being typed
  // in", which is what lets `put` write into it again (see cocktail-scale.js).
  p.leave(p.input);
  p.click(p.minus);
  assert.strictEqual(p.input.value, '2');
  assert.deepStrictEqual(p.amounts(), ['105 ml', '30 ml', '15 ml', '30 ml']);
});

test('the minus button cannot take the multiple below ×1 -- the same floor typing respects', () => {
  const p = page(AVIATION);
  // Already at the recipe as written. `apply` rounds `last - 1` (zero) up to
  // one, as it does a typed zero: its own `Math.max(1, ...)`.
  p.click(p.minus);
  assert.strictEqual(p.input.value, '1',
    'one fewer than the recipe as written is still the recipe as written');
  assert.deepStrictEqual(p.amounts(),
    ['52.5 ml', '15 ml', '7.5 ml', '15 ml'], 'the recipe as written');
});

test('a refusal reached by clicking − behaves exactly like a refusal reached by typing', () => {
  // Every real drink's ×1 is allowed, so no amount in the collection reaches
  // this. What is tested is the wiring: HTF.scale.scale is the one thing
  // cocktail-scale.js asks, so patching its answer proves the button reaches
  // `refuse()` exactly as a keystroke would. A refusal snaps the box back to
  // what is being made and says nothing (#1088).
  const p = page(AVIATION);
  p.type(p.input, '2');
  p.leave(p.input);
  const real = p.sandbox.HTF.scale.scale;
  p.sandbox.HTF.scale.scale = function (amounts, multiple) {
    if (multiple === 1) {
      return { ok: false, offender: 0, floorText: '2', floorTotalMl: 105 };
    }
    return real(amounts, multiple);
  };
  p.click(p.minus);
  assert.strictEqual(p.input.value, '2',
    'refused -- the box snaps back to what is actually being poured');
  assert.deepStrictEqual(p.amounts(), ['105 ml', '30 ml', '15 ml', '30 ml'],
    'and the amounts stay at the multiple that worked, rather than being ' +
    'redrawn from a verdict that said no');
});

// --- leaving the box ---------------------------------------------------------

test('leaving the box replaces what was typed with what was poured', () => {
  const p = page(AVIATION);
  p.type(p.input, '2.6');
  assert.strictEqual(p.input.value, '2.6', 'while typing, her number stands');
  p.leave(p.input);
  assert.strictEqual(p.input.value, '3',
    'on the way out the box says what was actually made, not what was asked');
});

test('a blank box on blur restores what is being poured rather than refusing', () => {
  const p = page(AVIATION);
  p.type(p.input, '2');
  p.type(p.input, '');
  p.leave(p.input);
  assert.strictEqual(p.input.value, '2', 'settled to what is being poured');
});


// --- the amount column ---------------------------------------------------
// The column is `max-content` on the list, shared down by `subgrid`: the
// browser measures it from whatever the amounts say, with a font this suite
// does not load, so there is no width to assert here (#1088). What is pinned is
// that scaling writes the amounts. "9 dashes" is the case that grows under
// scaling; millilitre figures tend to shorten ("52.5 ml" doubles to "105 ml").

test('scaling writes the amounts, which is what the column now measures', () => {
  const p = page([['9 dashes', 'Angostura'], ['30 ml', 'rye']]);
  assert.deepStrictEqual(p.amounts(), ['9 dashes', '30 ml'], 'as written');

  p.type(p.input, '12');
  assert.deepStrictEqual(p.amounts(), ['108 dashes', '360 ml'],
    'the longest amount grew by four characters, so the track grows with it');

  p.type(p.input, '2');
  assert.deepStrictEqual(p.amounts(), ['18 dashes', '60 ml'],
    'and shrinks back — the track follows the text both ways, with no state ' +
    'to get stuck on');
});

// --- the batch note is the bitters caveat and nothing else (#1121) -------------
// The cost line and the units line are per glass and do not change with
// scaling, so the note carries no totals. The caveat is not a total: it says
// what does not scale linearly, and the tests below stop it being deleted along
// with the figures.

/** The Aviation with a price and a strength on it. */
function priced(opts) {
  return page(AVIATION, Object.assign({ cost: [4, 6], units: [2.4] }, opts || {}));
}

test('the batch note stays hidden at the recipe as written', () => {
  const p = priced({ hasDashes: true });
  assert.strictEqual(p.batch.hidden, true,
    'bitters are worth a word when you are making several, not when making one');
});

test('above ×1 the note says the bitters caveat and nothing else', () => {
  const p = priced({ hasDashes: true });
  p.type(p.input, '3');
  assert.strictEqual(p.batch.hidden, false);
  assert.strictEqual(p.batch.textContent,
    '* Don’t scale bitters linearly — add to taste.',
    'the cost and units totals came off in #1121; only the caveat is left');
});

test('no price or unit count reaches the note, however loudly the page states them', () => {
  // The page has a cost line and a units line beside the note, both carrying
  // data attributes. None of their figures may appear in it (#1121).
  const p = priced({ hasDashes: true, cost: [4, 6], units: [2.1, 4] });
  p.type(p.input, '3');
  assert.ok(!/£|unit|ingredients|×3/.test(p.batch.textContent),
    'no money, no units, no multiple: got ' + p.batch.textContent);
});

test('a drink that pours no dash gets no note at all', () => {
  // A caveat that fires where it does not apply teaches people to stop reading
  // caveats (#720). The layout renders no element for such a drink: it gates on
  // `has_dashes`.
  const without = priced({ hasDashes: false });
  without.type(without.input, '4');
  assert.strictEqual(without.batch.textContent, '',
    'nothing to say; got: ' + without.batch.textContent);
  assert.strictEqual(without.batch.hidden, true);
});

test('the note goes away again on the way back down to ×1', () => {
  const p = priced({ hasDashes: true });
  p.type(p.input, '5');
  assert.strictEqual(p.batch.hidden, false);
  p.type(p.input, '1');
  assert.strictEqual(p.batch.hidden, true, 'it is a state, not a ratchet');
});

test('a page with no batch note element still scales', () => {
  // The layout renders the batch note only for a drink with dashes; on every
  // other drink page the element is absent, and the scaler must not need it.
  const p = page(AVIATION, { batch: false });
  assert.strictEqual(p.batch, null);
  p.type(p.input, '3');
  assert.deepStrictEqual(p.amounts(), ['157.5 ml', '45 ml', '22.5 ml', '45 ml'],
    'the scaler itself is unaffected by the note it cannot find');
});

// --- there is no line under the scaler (#1257) ---------------------------------
// Nothing about volume or strength moves when the box does. The recipe's volume
// is on the controls as `data-total-ml`, for the glass-fit report, and the
// script leaves it alone.

test('the volume attribute on the controls is not touched by the scaler', () => {
  // The Aviation as the plugin totals it: 52.5 + 15 + 7.5 + 15 = 90 ml.
  const p = page(AVIATION, { totalMl: 90 });
  p.type(p.input, '4');
  assert.strictEqual(p.control.getAttribute('data-total-ml'), '90',
    'the attribute is the recipe as written, at any multiple');
  assert.deepStrictEqual(p.amounts(), ['210 ml', '60 ml', '30 ml', '60 ml'],
    'and the amounts are what scale');
});

test('the units line does not move with the scaler', () => {
  // The units figure is per serving: scaling ×6 makes six drinks, not a
  // stronger one. Nothing in cocktail-scale.js writes to `.cocktail-units`
  // (#713, #1001).
  const p = page(AVIATION, { totalMl: 90, units: [2.4] });
  p.units.textContent = 'Roughly 2.4 units of alcohol in a serving of 90 ml.';
  p.type(p.input, '6');
  assert.strictEqual(p.units.textContent,
    'Roughly 2.4 units of alcohol in a serving of 90 ml.',
    'the per-glass sentence is untouched, figure and volume alike');
});

test('a drink with no stated volume scales like any other', () => {
  // A drink with no `page.volume` has no `data-total-ml` on its controls.
  const p = page(AVIATION);
  assert.strictEqual(p.control.getAttribute('data-total-ml'), undefined);
  p.type(p.input, '3');
  assert.deepStrictEqual(p.amounts(), ['157.5 ml', '45 ml', '22.5 ml', '45 ml']);
});

test('a bitters-only drink still gets its caveat with no figures to show', () => {
  // No cost or units line on the page: the note must not read as a stray
  // fragment.
  const p = page(AVIATION, { hasDashes: true });
  p.type(p.input, '2');
  assert.strictEqual(p.batch.textContent,
    '* Don’t scale bitters linearly — add to taste.',
    'no leading "×2:" with nothing after it');
});

// --- the line the note is about says so too (#1293) ----------------------------
// Above ×1 an amount in dashes has its scaled figure struck through with a star
// beside it, and the note opens with the same star. The amount still scales:
// the struck figure is the multiplied one.

const OLD_FASHIONED = [
  ['60 ml', 'bourbon'],
  ['5 ml', 'sugar syrup'],
  ['2 dashes', 'aromatic bitters', null, 'dashes'],
];

/** The amount spans the fixture built, and the stars beside the dashed ones. */
function marks(p) {
  return { spans: p.spans, stars: p.stars };
}

test('at the recipe as written nothing is struck and no star shows', () => {
  const p = page(OLD_FASHIONED, { hasDashes: true });
  const { spans, stars } = marks(p);
  assert.strictEqual(stars.length, 1, 'the fixture marked one pour');
  assert.ok(spans.every((s) => !s.hasAttribute('data-struck')));
  assert.strictEqual(stars[0].hidden, true);
});

test('above ×1 the dashes are struck and starred, and only the dashes', () => {
  const p = page(OLD_FASHIONED, { hasDashes: true });
  p.type(p.input, '4');
  const { spans, stars } = marks(p);
  assert.deepStrictEqual(spans.map((s) => s.hasAttribute('data-struck')),
    [false, false, true], 'the millilitre pours are not struck');
  assert.strictEqual(stars[0].hidden, false);
  assert.deepStrictEqual(p.amounts(), ['240 ml', '20 ml', '8 dashes'],
    'the struck figure is still the multiplied one');
  assert.ok(p.batch.textContent.startsWith('* '),
    'the note opens with the star the amount carries: ' + p.batch.textContent);
});

test('the strike and the star come off again at ×1', () => {
  const p = page(OLD_FASHIONED, { hasDashes: true });
  p.type(p.input, '3');
  p.type(p.input, '1');
  const { spans, stars } = marks(p);
  assert.ok(spans.every((s) => !s.hasAttribute('data-struck')), 'a state, not a ratchet');
  assert.strictEqual(stars[0].hidden, true);
});

test('a page with no batch note still strikes and stars its dashes', () => {
  // The note is one element and the marks are others; losing the first must
  // not silently lose the second.
  const p = page(OLD_FASHIONED, { batch: false });
  p.type(p.input, '2');
  const { spans, stars } = marks(p);
  assert.strictEqual(spans[2].hasAttribute('data-struck'), true);
  assert.strictEqual(stars[0].hidden, false);
});
