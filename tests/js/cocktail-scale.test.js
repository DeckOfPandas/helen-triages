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
  const input = control.add(el('cocktail-scale-multiple'));
  const note = article.add(el('cocktail-scale-note'));
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
    sandbox, control, input, note, spans, list, batch, cost, units,
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
  assert.strictEqual(p.note.hidden, true,
    'a half-typed number must not flash the floor message');
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
  assert.strictEqual(p.note.hidden, true, 'and it is not an error to have asked');
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
  assert.strictEqual(p.note.hidden, true, 'asking nothing is not an error');
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
// THE BATCH NOTE — #713, and Helen's request of 2026-09-06: "Bitters text
// appearing next to the scaler if it's edited to >1. Cost and units on a note."
//
// WHY IT SAYS TOTALS AND NOT THE FOOTER'S FIGURES. The cost line and the units
// line are both PER GLASS and both invariant under scaling — see the "THE COST
// LINE DOES NOT MOVE WITH THE SCALER" comment in cocktail-scale.js, and Helen's
// ruling that produced it. So a note repeating them would say what the footer
// already says. The total is the quantity that actually moves, and the alcohol
// half is the one #545 exists for: "not poisoning my friends".
// =============================================================================

/** The Aviation with a price and a strength on it. */
function priced(opts) {
  return page(AVIATION, Object.assign({ cost: [4, 6], units: [2.4] }, opts || {}));
}

test('the batch note stays hidden at the recipe as written', () => {
  const p = priced();
  assert.strictEqual(p.batch.hidden, true,
    'at ×1 the totals ARE the per-glass figures, and the footer already says them');
});

test('above ×1 the batch note gives the totals, not the per-glass figures', () => {
  const p = priced();
  p.type(p.input, '3');
  assert.strictEqual(p.batch.hidden, false);
  assert.strictEqual(p.batch.textContent,
    '×3: roughly £12.00–£18.00 in ingredients, roughly 7.2 units of alcohol in total.',
    '4–6 a glass is 12–18 for three; 2.4 units a serving is 7.2 on the table');
});

test('an exact price reads as one figure rather than a range of itself', () => {
  const p = priced({ cost: [5, 5] });
  p.type(p.input, '2');
  assert.ok(p.batch.textContent.includes('roughly £10.00 in ingredients'),
    'got: ' + p.batch.textContent);
  assert.ok(!p.batch.textContent.includes('£10.00–£10.00'));
});

test('a punch multiplies by its own servings too', () => {
  // A bowl serving 4 at 2.1 units a serving is 8.4 units; two bowls, 16.8.
  const p = priced({ units: [2.1, 4] });
  p.type(p.input, '2');
  assert.ok(p.batch.textContent.includes('roughly 16.8 units of alcohol in total'),
    'got: ' + p.batch.textContent);
});

test('the bitters line appears only on a drink that pours a dash', () => {
  const withDashes = priced({ hasDashes: true });
  withDashes.type(withDashes.input, '4');
  assert.ok(withDashes.batch.textContent.includes(
    'Don’t scale bitters linearly — add to taste.'),
    'got: ' + withDashes.batch.textContent);

  // #720.1: the caveat that fired on Aperol Spritz is why this is conditional.
  const without = priced({ hasDashes: false });
  without.type(without.input, '4');
  assert.ok(!without.batch.textContent.includes('bitters'),
    'a drink with no dash in it must not be warned about bitters; got: ' +
    without.batch.textContent);
});

test('the note goes away again on the way back down to ×1', () => {
  const p = priced();
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

test('a bitters-only drink still gets its caveat with no figures to show', () => {
  // The batch element is rendered when EITHER switch is on, so one of the two
  // halves can be missing. The note must not read as a stray fragment.
  const p = page(AVIATION, { hasDashes: true });
  p.type(p.input, '2');
  assert.strictEqual(p.batch.textContent,
    'Don’t scale bitters linearly — add to taste.',
    'no leading "×2:" with nothing after it');
});
