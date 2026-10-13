// Tests for assets/js/card-name-fit.js (#1115, #971).
//
//   node --test tests/js/card-name-fit.test.js
//
// The script decides one thing per drink name: it fits, one size step reaches
// it, or it wraps to two lines of tape.
//
// The trap is a measurement one: the cocktails index paginates by setting
// `card.hidden`, a hidden element measures zero in both directions, and
// `0 > 0 + 1` is false, which reads as "this name fits". A name that cannot be
// measured must get no verdict and keep the no-JS ellipsis clip.
//
// The shipped source runs byte for byte inside a fake `window`; the stub
// carries only what this script touches.
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const SOURCE = path.resolve(__dirname, '..', '..',
  'assets', 'js', 'card-name-fit.js');

// Restated, not imported: the script holds the step and so does
// `$card-name-step` in _sass/cocktails/_cards.scss, and a test that read the
// script's own constant could not notice the two drifting apart.
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
    // A name on a hidden card has no client rects at all: the state the
    // script must refuse to answer about.
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

// Roughly a card's tape word at a desktop width.
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
  // One step buys a short word's worth of line.
  const n = name(BOX * 1.1, BOX);
  run([n]);
  assert.strictEqual(n.has('step'), true);
  assert.strictEqual(n.has('wrap'), false);
});

test('a name far too long wraps rather than shrinking to fit', () => {
  // No step reaches this, and shrinking would only make small type that
  // still ellipsises.
  const n = name(BOX * 1.6, BOX);
  run([n]);
  assert.strictEqual(n.has('wrap'), true);
  assert.strictEqual(n.has('step'), false);
});

test('a step that the browser does not honour is undone and wrapped instead', () => {
  // Within the linear model this name steps; the re-measure says it still
  // overflows, so it must end up wrapped, not smaller and still ellipsising.
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

// --- a name that cannot be measured, #1115 -------------------------------------

test('a name on a paginated-away card is not classified as fitting', () => {
  // A hidden card measures zero, so a name of any length answers "I fit".
  const n = name(BOX * 2, 0, { laidOut: false });
  run([n]);
  assert.strictEqual(n.has('wrap'), false, 'nothing can be concluded from zero');
  assert.strictEqual(n.has('step'), false);
});

test('a name that could not be measured keeps the no-JS fallback', () => {
  // `--fitted` releases the ellipsis clip. Added without a measurement, it
  // removes the fallback and puts nothing in its place: the name runs off its
  // tape. An unmeasurable name carries no class at all.
  const n = name(BOX * 2, 0, { laidOut: false });
  run([n]);
  assert.deepStrictEqual(n.classes(), [],
    'a name the script could not measure must be left exactly as the CSS drew it');
});

test('the same name is classified once the page turn lays it out', () => {
  // cocktail-index.js re-runs this pass on every apply(), a page turn
  // included, when the card is visible and the name measurable.
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
  // The namespace has to exist before the script runs, as it does on the page
  // (assets.js loads first): the script attaches only `if (window.HTF)`, so it
  // can never be the reason a page fails to draw.
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
