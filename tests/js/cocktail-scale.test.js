// =============================================================================
// Tests for assets/js/cocktail-scale.js — the scaler's DOM half.
//
//   node --test tests/js/*.test.js
//
// WHY THIS FILE EXISTS AT ALL, when scale.test.js already covers the maths.
// Helen's bug on 2026-09-04 was not arithmetic: "I can't delete numbers in the
// target ml input field. I can add numbers, then increasing the number of
// servings causes the numbers in the target field to update." Every figure
// HTF.scale produced was right; the WIRING wrote one of them back into the box
// she was typing in. A pure test of scale.js cannot see that, and the previous
// agent checked it by hand against `tmp/smoke_scale_total.js` — a scratch file,
// gitignored, which is exactly the shape of check that stops being run.
//
// SO THE PAGE IS STUBBED, the way tests/js/stub-dom.js stubs one for
// assets.js and for the same stated reason: run the SHIPPED source byte for
// byte inside a fake `window`, and read what it did. The elements below carry
// only what cocktail-scale.js actually touches — `querySelector`, `closest`,
// `hidden`, `value`, `textContent`, attributes and one listener per event —
// because a fuller DOM would be a second browser to keep honest.
//
// `document.activeElement` IS THE WHOLE POINT and is settable here, which a
// real browser makes hard and which is why the bug survived a manual look:
// clicking into a field and pressing Backspace is the only way to reproduce it,
// and nobody does that twice.
// =============================================================================
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
  /* THE TWO STEP BUTTONS — #731 — SIT EITHER SIDE OF THE INPUT IN THE REAL
     MARKUP ("-  [1] x  +"), and are added here in that order for the same
     reason the input and mark are: the shipped source is run byte for byte,
     so a query for `.cocktail-scale-minus` or `.cocktail-scale-plus` must
     find the same element cocktail-scale.js does. */
  const minus = control.add(el('cocktail-scale-step cocktail-scale-minus'));
  const input = control.add(el('cocktail-scale-multiple'));
  const plus = control.add(el('cocktail-scale-step cocktail-scale-plus'));
  /* NO `.cocktail-scale-note` -- #1088 deleted the floor message and its
     paragraph, and this fixture has to keep matching the shipped layout. It
     matters more than an unused element usually would: that paragraph was in
     cocktail-scale.js's init guard, so a fixture still supplying one would go
     on passing even if the script still demanded it, which is the exact
     regression that would blank every drink's scaler in production. */
  const list = article.add(el('cocktail-ingredients'));

  /* THE BATCH NOTE AND THE TWO FIGURE LINES ARE OPT-IN, because in PRODUCTION
     none of them is rendered: all three are gated on `show_costs` /
     `show_units`, which exist only in _config_local.yml. A test page without
     them is therefore the production shape, not a degenerate one, and every
     pre-existing test in this file is exercising exactly that. */
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

  /* THE TOTAL LINE IS OPT-IN FOR A DIFFERENT REASON FROM THE THREE ABOVE --
     #1121. Those are missing in PRODUCTION; this one is missing on a DRINK
     whose volume would be wrong rather than rough, which is two published
     drinks (see `volume_for` in cocktail_units.rb). So a page without it is a
     real live page, not a config.

     `opts.totalMl` IS WHAT THE PLUGIN WROTE, and the span starts holding it
     because the SERVER rendered ×1 before any script ran. A test that started
     the span empty would be testing a page that never exists. */
  const total = opts.totalMl === undefined
    ? null : article.add(el('cocktail-scale-total'));
  const totalFigure = total
    ? total.add(el('cocktail-scale-total-figure', String(opts.totalMl)))
    : null;
  /* `totalAttr` SEPARATELY, so a test can put a figure on screen and rubbish in
     the attribute behind it -- which is the only way to reach the "leave what
     the server wrote alone" branch, since cocktail-scale.js reads the attribute
     once, at init, exactly as it stashes the original amounts once. */
  if (total) {
    total.setAttribute('data-total-ml',
      opts.totalAttr === undefined ? opts.totalMl : opts.totalAttr);
  }

  const spans = pours.map(([amount, name]) => {
    const li = list.add(el('cocktail-ingredient'));
    const span = li.add(el('cocktail-amount', amount));
    li.add(el('cocktail-item-name', name));
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
    sandbox, control, input, minus, plus, spans, list, batch, cost, units,
    total, totalFigure,
    wide: () => list.classList.contains('cocktail-ingredients--wide-amounts'),
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

// --- the keystroke guard, which outlived the box it was written for ----------
// The millilitre box went on 2026-09-05 (#721) and took the cross-writing with
// it, but `input` still fires on every keystroke and clearing the box to type a
// new number still passes through the empty string. Answering that with a floor
// message scolds someone for pressing Backspace.

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
  // Whole recipes only, since 2026-09-05. `1.5` used to become `1.6667` -- the
  // nearest multiple of this drink's own third-of-a-recipe step -- and now
  // becomes 2, which is a number a person can see themselves having asked for.
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
  // Aviation's 7.5 ml of creme de violette is the one that used to force a
  // third-of-a-recipe step; nothing forces anything now.
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
// "-  [1] x  +", Helen's sketch. Both buttons go through `apply()`, the exact
// function a typed value reaches (`step()` in cocktail-scale.js calls
// `apply(last ± 1)` and nothing else), so these tests are really asking one
// question: does a click land on the same code a keystroke does.

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
  // one the same way it rounds a typed zero or a negative number up -- see
  // `apply`'s own `Math.max(1, ...)` -- so the button has nothing further to
  // give and the drink stays exactly as poured.
  p.click(p.minus);
  assert.strictEqual(p.input.value, '1',
    'one fewer than the recipe as written is still the recipe as written');
  assert.deepStrictEqual(p.amounts(),
    ['52.5 ml', '15 ml', '7.5 ml', '15 ml'], 'the recipe as written');
});

test('a refusal reached by clicking − behaves exactly like a refusal reached by typing', () => {
  // Every real drink's ×1 is always allowed (scale.js's own proof — the floor
  // is capped there), so this scenario cannot arise from any amount in the
  // collection today. What is being tested is the WIRING, not the arithmetic:
  // HTF.scale.scale is the one thing cocktail-scale.js asks, per the ONE
  // PARSER rule (MANUAL §9.13), so patching its answer proves the button
  // reaches `refuse()` exactly as a keystroke would, without assuming a
  // dataset the floor can no longer produce.
  //
  // WHAT A REFUSAL IS, SINCE #1088: the box snaps back and nothing is said.
  // This test used to assert the floor message's text and the ingredient it
  // named; Helen deleted that message ("We don't go lower than the recipe
  // amounts, because the scaler is an integer and doesn't go below 1"), so
  // what is left to prove is the half that was always the point -- that a
  // click and a keystroke reach the same code and leave the box saying what
  // is actually being poured.
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


// --- the amount column's two widths ------------------------------------------
// Helen, 2026-09-05: "reduce the space between ingredient amounts and names
// again, but increase it when an amount would otherwise linebreak due to use of
// the scaler." Counted rather than measured — the amounts are set in Plex Mono,
// so a character count is a width. Nine fit in the narrow column.

test('the amount column stays narrow for a drink as written', () => {
  const p = page(AVIATION);
  assert.strictEqual(p.wide(), false,
    '"52.5 ml" is seven characters; nothing needs the room');
});

test('a scaled amount that would wrap opens the column, and closes it again', () => {
  // A count with a long unit is what actually reaches ten characters under
  // scaling: millilitre figures tend to SHORTEN as they scale, because the
  // decimal falls off ("52.5 ml" doubles to "105 ml").
  const p = page([['9 dashes', 'Angostura'], ['30 ml', 'rye']]);
  assert.strictEqual(p.wide(), false, '"9 dashes" is eight characters');

  p.type(p.input, '12');
  assert.strictEqual(p.amounts()[0], '108 dashes', 'ten characters');
  assert.strictEqual(p.wide(), true, 'so the column opens');

  p.type(p.input, '2');
  assert.strictEqual(p.amounts()[0], '18 dashes', 'nine characters');
  assert.strictEqual(p.wide(), false, 'and closes again — it is a state, not a ratchet');
});

test('an amount longer than the column holds opens it at rest', () => {
  // The Airmail's own written amount, fourteen characters, which has wrapped
  // inside its column since the column existed.
  const p = page([['Top (30-45) ml', 'champagne'], ['15 ml', 'lime juice']]);
  assert.strictEqual(p.wide(), true,
    'a drink can be born too wide for the narrow column, not only scaled into it');
});

// =============================================================================
// THE BATCH NOTE IS THE BITTERS CAVEAT AND NOTHING ELSE — #1121, 2026-09-17
// =============================================================================
// It was #713 (Helen, 2026-09-06: "Bitters text appearing next to the scaler if
// it's edited to >1. Cost and units on a note.") and it carried the batch's cost
// and units totals until she saw them under the new ml line: "I like the line.
// But the cost and units line below has come back and I don't want it to be
// there."
//
// THE TOTALS' OWN ARGUMENT IS WORTH KNOWING, because it was sound when made:
// the cost line and the units line are both PER GLASS and invariant under
// scaling, so a note repeating them would restate the footer, while "what is on
// the table" had no other answer. #1121 gave it one — `Approximately X ml`,
// directly above this note, at the multiple actually set.
//
// THE CAVEAT SURVIVED BECAUSE IT IS NOT A TOTAL. It answers what does NOT scale
// linearly. The tests below are what stop it being deleted along with the
// figures it used to sit beside.
// =============================================================================

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
    'Don’t scale bitters linearly — add to taste.',
    'the cost and units totals came off in #1121; only the caveat is left');
});

test('no price or unit count reaches the note, however loudly the page states them', () => {
  // THE REGRESSION THIS EXISTS FOR. The element still has a cost line and a
  // units line on the page beside it, both carrying data attributes the note
  // used to read. Helen asked for those figures to stop appearing here.
  const p = priced({ hasDashes: true, cost: [4, 6], units: [2.1, 4] });
  p.type(p.input, '3');
  assert.ok(!/£|unit|ingredients|×3/.test(p.batch.textContent),
    'no money, no units, no multiple: got ' + p.batch.textContent);
});

test('a drink that pours no dash gets no note at all', () => {
  // #720.1: the caveat that fired on Aperol Spritz is why this is conditional --
  // "a caveat that fires where it does not apply teaches you to stop reading
  // caveats". With the totals gone there is nothing else the note could say, so
  // such a drink now renders no element (the layout gates on `has_dashes`).
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

test('production renders none of these elements, and nothing breaks', () => {
  // show_costs and show_units live only in _config_local.yml, so the built
  // public page has no cost line, no units line and no batch note at all.
  const p = page(AVIATION, { batch: false });
  assert.strictEqual(p.batch, null);
  p.type(p.input, '3');
  assert.deepStrictEqual(p.amounts(), ['157.5 ml', '45 ml', '22.5 ml', '45 ml'],
    'the scaler itself is unaffected by the note it cannot find');
});

// =============================================================================
// THE LINE UNDER THE SCALER — #1121, Helen: "add total ml next to recipe scaler
// to help me choose the right number of glasses... This means I can vary target
// units of alcohol myself."
//
// TWO NUMBERS THAT MUST NOT BE CONFUSED, and these tests exist to hold them
// apart. The line under the scaler is the BATCH and moves; the units line is
// PER GLASS and does not (the layout's own comment says so, and #713's ruling
// before it). They are different elements carrying different attributes, which
// is the mechanism that makes the second guarantee structural rather than
// remembered.
// =============================================================================

test('the line under the scaler multiplies with the box', () => {
  // The Aviation as the plugin totals it: 52.5 + 15 + 7.5 + 15 = 90 ml.
  const p = page(AVIATION, { totalMl: 90 });
  assert.strictEqual(p.totalFigure.textContent, '90',
    'the server rendered ×1 and the script has nothing to correct');
  p.type(p.input, '4');
  assert.strictEqual(p.totalFigure.textContent, '360');
  p.type(p.input, '2');
  assert.strictEqual(p.totalFigure.textContent, '180',
    'it is a state, not a ratchet');
  p.type(p.input, '1');
  assert.strictEqual(p.totalFigure.textContent, '90', 'and back to the recipe');
});

test('an integer total prints as an integer, never 360.0', () => {
  const p = page(AVIATION, { totalMl: 82.5 });
  p.type(p.input, '2');
  assert.strictEqual(p.totalFigure.textContent, '165');
  p.type(p.input, '3');
  assert.strictEqual(p.totalFigure.textContent, '247.5',
    'and a half millilitre survives the float');
});

test('the units line does not move with the scaler, and the total does', () => {
  // THE GUARANTEE #713 AND #1001 BOTH REST ON. The units figure is per serving
  // and invariant; scaling ×6 makes six drinks, not a stronger one. Nothing in
  // cocktail-scale.js writes to `.cocktail-units`, and this is what says so.
  const p = page(AVIATION, { totalMl: 90, units: [2.4] });
  p.units.textContent = 'Roughly 2.4 units of alcohol in a serving of 90 ml.';
  p.type(p.input, '6');
  assert.strictEqual(p.units.textContent,
    'Roughly 2.4 units of alcohol in a serving of 90 ml.',
    'the per-glass sentence is untouched, figure and volume alike');
  assert.strictEqual(p.totalFigure.textContent, '540',
    'while the batch line beside the control says what is on the table');
});

test('a drink with no stated volume renders no total line, and the scaler is unaffected', () => {
  // Two published drinks have no `page.volume` — the Caipirinha and the pear
  // Bellini, where the excluded pours ARE the drink and a figure would be
  // wrong rather than rough. (A TOPPED drink is not one of them: since Helen's
  // ruling of 2026-09-17 it spends its declared range's midpoint.) The element
  // is absent, not empty.
  const p = page(AVIATION);
  assert.strictEqual(p.total, null);
  p.type(p.input, '3');
  assert.deepStrictEqual(p.amounts(), ['157.5 ml', '45 ml', '22.5 ml', '45 ml'],
    'the scaler does not care about a line it cannot find');
});

test('an unreadable volume leaves the sentence the server wrote', () => {
  // A blanked figure would be worse than a stale one, and the page was right
  // at ×1 before any script ran.
  const p = page(AVIATION, { totalMl: 90, totalAttr: 'lots' });
  p.type(p.input, '4');
  assert.strictEqual(p.totalFigure.textContent, '90');
});

test('a bitters-only drink still gets its caveat with no figures to show', () => {
  // The batch element is rendered when EITHER switch is on, so one of the two
  // halves can be missing. The note must not read as a stray fragment.
  const p = page(AVIATION, { hasDashes: true });
  p.type(p.input, '2');
  assert.strictEqual(p.batch.textContent,
    'Don’t scale bitters linearly — add to taste.',
    'no leading "×2:" with nothing after it');
});
