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
  const target = control.add(el('cocktail-scale-target'));
  const totalValue = control.add(el('cocktail-scale-total-value'));
  const note = article.add(el('cocktail-scale-note'));
  const caveat = article.add(el('cocktail-scale-note cocktail-scale-caveat',
    'dashes and drops are scaled with the recipe; bitters do not really scale '
    + 'linearly, so use your judgement above ×2'));
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
    sandbox, control, input, target, totalValue, note, caveat, spans,
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
  assert.strictEqual(p.totalValue.textContent, '90 ml');
  assert.strictEqual(p.target.value, '90');
});

// --- the bug Helen reported, 2026-09-04 --------------------------------------

test('the target box can be emptied — nothing is written back into it', () => {
  const p = page(AVIATION);
  // "I can't delete numbers in the target ml input field." Backspacing through
  // 180 passes through 18 and then 1, both of which the drink's floor refuses;
  // the refusal used to write the last working total straight back in.
  p.type(p.target, '180');
  assert.strictEqual(p.totalValue.textContent, '180 ml');
  for (const partial of ['18', '1', '']) {
    p.type(p.target, partial);
    assert.strictEqual(p.target.value, partial,
      `backspacing to "${partial}" left the box holding "${p.target.value}"`);
  }
});

test('an empty or half-typed target changes nothing and says nothing', () => {
  const p = page(AVIATION);
  p.type(p.target, '180');
  const poured = p.amounts();
  p.type(p.target, '');
  assert.deepStrictEqual(p.amounts(), poured,
    'clearing the box is someone mid-type, not a request for a drink of nothing');
  assert.strictEqual(p.note.hidden, true,
    'an empty box must not flash the floor message');
  assert.strictEqual(p.input.value, '2', 'the other box still says what is poured');
});

test('the multiple box can be emptied too — the same guard, both boxes', () => {
  const p = page(AVIATION);
  p.type(p.input, '');
  assert.strictEqual(p.input.value, '');
  assert.strictEqual(p.note.hidden, true);
  assert.strictEqual(p.totalValue.textContent, '90 ml', 'the page held still');
});

test('typing in one box redraws the OTHER one', () => {
  const p = page(AVIATION);
  // "increasing the number of servings causes the numbers in the target field
  // to update" -- which is correct and wanted, as long as the target is not the
  // field being typed in.
  p.type(p.input, '2');
  assert.strictEqual(p.target.value, '180');
  assert.strictEqual(p.totalValue.textContent, '180 ml');

  // 45 ml of a 90 ml drink is ×0.5 on paper, and this drink has no half: its
  // amounts are 105/30/15/30 half-ml units, gcd 15, so it steps in thirds and
  // ×0.5 snaps up to ⅔. The typed box is still left alone while it is typed in.
  p.type(p.target, '45');
  assert.strictEqual(p.target.value, '45', 'the typed box is left alone');
  assert.strictEqual(p.input.value, '0.6667', 'the other box follows, snapped');
  assert.strictEqual(p.totalValue.textContent, '60 ml, ×⅔');
});

test('a multiple that would move a ratio snaps, and says so as a fraction', () => {
  const p = page(AVIATION);
  // ×1.5 would pour 78.75 ml of gin, which no jigger measures, so the old code
  // rounded it and the ratios moved. Helen, 2026-09-04: the ratios do not move.
  p.type(p.input, '1.5');
  assert.strictEqual(p.input.value, '1.5', 'still typeable');
  assert.deepStrictEqual(p.amounts(),
    ['87.5 ml', '25 ml', '12.5 ml', '25 ml'], 'poured at ×1⅔, all exact');
  assert.strictEqual(p.totalValue.textContent, '150 ml, ×1⅔');
  p.leave(p.input);
  assert.strictEqual(p.input.value, '1.6667', 'the box is rewritten to what was made');
});

test('the caveat about dashes is revealed with the control', () => {
  const p = page(AVIATION);
  assert.strictEqual(p.caveat.hidden, false);
  assert.match(p.caveat.textContent, /dashes and drops/);
});

test('a refused target snaps the multiple box back, never the typed box', () => {
  const p = page(AVIATION);
  p.type(p.input, '2');
  // 7.5 ml of crème de violette hits 2.5 ml at ×0.5, so ×0.5 is the floor and
  // 20 ml of a 90 ml drink (×0.222) is under it.
  p.type(p.target, '20');
  assert.strictEqual(p.target.value, '20', 'still typeable');
  assert.strictEqual(p.input.value, '2', 'the untyped box shows what is poured');
  assert.strictEqual(p.note.hidden, false);
  assert.match(p.note.textContent, /crème de violette/,
    'the note names the ingredient that set the limit, read from the page');
});

// --- leaving a box ------------------------------------------------------------

test('leaving the target replaces what was typed with what was poured', () => {
  const p = page(AVIATION);
  // Helen, 2026-09-04: the target "works the ratios out backwards within reason
  // but then updates the target ml the user has entered to something more sane".
  // 95 ml of this 90 ml drink is ×1.056; the nearest multiple it can be poured
  // at is ×1, so 90 ml is what comes out and 90 is what the box is rewritten to.
  p.type(p.target, '95');
  assert.strictEqual(p.target.value, '95', 'while typing, her number stands');
  p.leave(p.target);
  assert.strictEqual(p.totalValue.textContent, '90 ml');
  assert.strictEqual(p.target.value, '90',
    'on the way out the box says what was actually made, not what was asked');
});

test('a blank target on blur restores the current total rather than refusing', () => {
  const p = page(AVIATION);
  p.type(p.input, '2');
  p.type(p.target, '');
  p.leave(p.target);
  assert.strictEqual(p.target.value, '180', 'settled to what is being poured');
  assert.strictEqual(p.input.value, '2');
  assert.strictEqual(p.note.hidden, true, 'asking nothing is not an error');
});

test('a blank multiple on blur restores it too', () => {
  const p = page(AVIATION);
  p.type(p.input, '2');
  p.type(p.input, '');
  p.leave(p.input);
  assert.strictEqual(p.input.value, '2');
  assert.strictEqual(p.target.value, '180');
});
