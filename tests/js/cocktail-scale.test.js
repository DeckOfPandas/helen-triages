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
function page(pours) {
  const article = el('cocktail');
  const control = article.add(el('cocktail-scale-controls'));
  const input = control.add(el('cocktail-scale-multiple'));
  const note = article.add(el('cocktail-scale-note'));
  const list = article.add(el('cocktail-ingredients'));

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
    sandbox, control, input, note, spans, list,
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
