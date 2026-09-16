// =============================================================================
// Tests for assets/js/card-name-fit.js — issues #1115 and, behind it, #971/#776.
//
//   node --test tests/js/card-name-fit.test.js
//
// WHAT THIS IS FOR. The script decides one thing per drink name: does it fit,
// does one size step reach it, or must it wrap to two lines of tape? Helen
// settled those three states by looking at a candidates page on 2026-09-04
// ("shrink when it's just one short-ish word too long, then two lines where it's
// more than that"), and until #1115 nothing held the script to them.
//
// THE BUG IT WAS WRITTEN FOR IS THE LAST ONE, AND IT IS A MEASUREMENT BUG, NOT A
// LAYOUT ONE. The cocktails index paginates by setting `card.hidden`, a hidden
// element measures ZERO in both directions, and `0 > 0 + 1` is false — which
// reads as "this name fits". So every name on page two was classified as
// fitting at load, whatever its length, and the class that released the no-JS
// ellipsis clip was added on the strength of that non-measurement. Page one was
// always right, which is why it stayed invisible. `card-line-budget.js` had the
// identical bug one file along (#776) and this is its fix arriving here.
//
// THE DOM IS STUBBED, the same way card-line-budget.test.js stubs one and for
// the reason that file states: run the SHIPPED source byte for byte inside a
// fake `window` and read what it did to the classes. The stub carries only what
// this script touches — `querySelectorAll`, `querySelector`, `classList`,
// `getClientRects`, `clientWidth` and a `createRange` that reports the width of
// the lettering.
// =============================================================================
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const SOURCE = path.resolve(__dirname, '..', '..',
  'assets', 'js', 'card-name-fit.js');

// The step, and it is deliberately restated rather than imported: the script
// holds 0.86 and so does `$card-name-step` in _sass/cocktails/_cards.scss, and
// a test that read the script's own constant could not notice the two drifting
// apart. See the pairing note at the top of the script.
const STEP = 0.86;

/**
 * One `.drink-card-name` whose lettering is `contentWidth` px inside a
 * `boxWidth` px box.
 *
 * @param {number} contentWidth what a Range over the word reports
 * @param {number} boxWidth     the word element's clientWidth
 * @param {object} [opts]       `laidOut: false` for a paginated-away card,
 *                              `stepped` for the width once the type has
 *                              actually shrunk (defaults to the linear model)
 */
function name(contentWidth, boxWidth, opts) {
  opts = opts || {};
  const classes = new Set();
  const word = {
    clientWidth: boxWidth,
    // A name on a hidden card has no client rects at all. That is the state the
    // script must refuse to answer about, and the one thing a `hidden` check
    // would model less faithfully than the browser's own answer.
    getClientRects: () => (opts.laidOut === false ? [] : [{ width: contentWidth }]),
    _width: () => {
      // Once `--step` is on, the lettering is smaller. The script's prediction
      // is linear; a real face is not, so a test can say what the browser came
      // back with independently of what was predicted.
      if (classes.has('drink-card-name--step')) {
        return opts.stepped === undefined ? contentWidth * STEP : opts.stepped;
      }
      return contentWidth;
    }
  };
  return {
    classList: {
      add: (c) => classes.add(c),
      remove: (c) => classes.delete(c),
      contains: (c) => classes.has(c)
    },
    querySelector: (sel) => (sel === '.drink-card-tape-word' ? word : null),
    _word: word,
    classes: () => Array.from(classes).sort(),
    has: (c) => classes.has('drink-card-name--' + c)
  };
}

/** Run the shipped source against these names and hand the sandbox back. */
function run(names) {
  const sandbox = {
    document: {
      querySelectorAll: () => names,
      // The Range the script measures with. `selectNodeContents` records which
      // element it was pointed at; the rect comes from that element's own
      // current width, so a re-measure after stepping reports the smaller
      // lettering exactly as a browser would.
      createRange: () => {
        let target = null;
        return {
          selectNodeContents: (el) => { target = el; },
          getBoundingClientRect: () => ({ width: target._width() }),
          detach() {}
        };
      }
    },
    setTimeout: () => 0,
    clearTimeout() {},
    addEventListener() {}
  };
  sandbox.window = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(SOURCE, 'utf8'), sandbox, { filename: SOURCE });
  return sandbox;
}

// A card's tape word is about 165px across at 1280 (measured on Cobra's Fang,
// the drink the script's own comment cites).
const BOX = 165;

test('a name that fits gets no state class', () => {
  const n = name(120, BOX);
  run([n]);
  assert.strictEqual(n.has('step'), false);
  assert.strictEqual(n.has('wrap'), false);
});

test('a name that fits is still marked as measured', () => {
  // `--fitted` is not a state: it says the script has run, and it is what
  // releases the no-JS ellipsis clip (#971). Every name it measures gets it,
  // whatever the answer.
  const n = name(120, BOX);
  run([n]);
  assert.strictEqual(n.has('fitted'), true);
});

test('a name one short word too long steps rather than wraps', () => {
  // Helen's rule, 2026-09-04: "shrink when it's just one short-ish word too
  // long". One step of 0.86 buys about 16% of the line.
  const n = name(BOX * 1.1, BOX);
  run([n]);
  assert.strictEqual(n.has('step'), true);
  assert.strictEqual(n.has('wrap'), false);
});

test('a name far too long wraps rather than shrinking to fit', () => {
  // "...then two lines where it's more than that." No plausible step reaches
  // this, and shrinking would only make small type that still ellipsises.
  const n = name(BOX * 1.6, BOX);
  run([n]);
  assert.strictEqual(n.has('wrap'), true);
  assert.strictEqual(n.has('step'), false);
});

test('a step that the browser does not honour is undone and wrapped instead', () => {
  // THE PREDICTION IS A MODEL AND THE BROWSER IS THE FACT. Within the linear
  // model this name steps; the re-measure says it still overflows, so it must
  // end up wrapped and NOT sitting at a smaller size while still ellipsising.
  const n = name(BOX * 1.1, BOX, { stepped: BOX + 5 });
  run([n]);
  assert.strictEqual(n.has('wrap'), true);
  assert.strictEqual(n.has('step'), false);
});

test('a re-run clears a state the name no longer earns', () => {
  // Reset-before-measure. Without it a name stepped on a narrow card can never
  // step back up when the card grows, because a stepped name looks like it fits.
  const n = name(BOX * 1.1, BOX);
  run([n]);
  assert.strictEqual(n.has('step'), true);

  n._word.clientWidth = BOX * 2;
  run([n]);
  assert.strictEqual(n.has('step'), false, 'it is a state, not a ratchet');
  assert.strictEqual(n.has('wrap'), false);
});

// -----------------------------------------------------------------------------
// #1115 — the regression this file was written for.
// -----------------------------------------------------------------------------

test('a name on a paginated-away card is not classified as fitting', () => {
  // THE BUG. A hidden card measures zero, `0 > 0 + 1` is false, and a name of
  // any length answers "I fit". This name is twice its box and must not come
  // back from a pass that could not see it wearing a verdict.
  const n = name(BOX * 2, 0, { laidOut: false });
  run([n]);
  assert.strictEqual(n.has('wrap'), false, 'nothing can be concluded from zero');
  assert.strictEqual(n.has('step'), false);
});

test('a name that could not be measured keeps the no-JS fallback', () => {
  // AND THIS IS THE HALF THAT COST THE LIVE SITE. `--fitted` releases the
  // ellipsis clip on the strength of a measurement having happened. Released on
  // the strength of one that could not happen, it removes the fallback and puts
  // nothing in its place: the name runs off its tape instead of being politely
  // cut. An unmeasurable name must carry no class at all.
  const n = name(BOX * 2, 0, { laidOut: false });
  run([n]);
  assert.deepStrictEqual(n.classes(), [],
    'a name the script could not measure must be left exactly as the CSS drew it');
});

test('the same name is classified once the page turn lays it out', () => {
  // The other half of the fix is in cocktail-index.js, which re-runs this pass
  // on every apply() — a page turn included. Once the card is visible the name
  // is measurable, and this is what the re-run then concludes.
  const n = name(BOX * 2, 0, { laidOut: false });
  run([n]);
  assert.deepStrictEqual(n.classes(), []);

  n._word.clientWidth = BOX;
  n._word.getClientRects = () => [{ width: BOX * 2 }];
  run([n]);
  assert.strictEqual(n.has('wrap'), true);
  assert.strictEqual(n.has('fitted'), true);
});

test('it hangs itself off HTF so the index can re-run it', () => {
  // cocktail-index.js calls `HTF.fitCardNames()` after every apply(), guarded,
  // exactly as it calls `HTF.cardLineBudget()`.
  // The namespace has to exist BEFORE the script runs, as it does on the page
  // (assets.js loads first), because the script attaches only `if (window.HTF)`
  // — deliberately, so it can never be the reason a page fails to draw.
  const ctx = {
    document: {
      querySelectorAll: () => [],
      createRange: () => ({
        selectNodeContents() {}, getBoundingClientRect: () => ({ width: 0 }), detach() {}
      })
    },
    setTimeout: () => 0,
    clearTimeout() {},
    addEventListener() {},
    HTF: {}
  };
  ctx.window = ctx;
  vm.createContext(ctx);
  vm.runInContext(fs.readFileSync(SOURCE, 'utf8'), ctx, { filename: SOURCE });
  assert.strictEqual(typeof ctx.HTF.fitCardNames, 'function');
});
