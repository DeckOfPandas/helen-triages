// The two card measurement passes, running inside the real index (#1107).
//
//   node --test tests/js/*.test.js
//
// `card-name-fit.test.js` and `card-line-budget.test.js` run each script
// against a DOM built for it, which proves the arithmetic. This proves each
// survives the page: it loads in `index-harness.js` without throwing and
// leaves alone what it cannot measure.
//
// No pixels are asserted. The stub has no line breaking, no font metrics and
// no box model, so a rendered width would be a number the test invented. What
// is asserted is what each pass decides from boxes the test supplies.
'use strict';

const test = require('node:test');
const assert = require('node:assert');

const { boot, SCRIPTS, LAYOUT_SCRIPTS } = require('./index-harness.js');

// The stylesheet's numbers, which the harness also uses as its defaults:
// `_cards.scss` sets the ingredient line at 0.82rem with line-height 1.5, so
// 13.12px of type on a 19.68px line at a 16px root.
const LINE = 19.68;

/** A drink card with nothing stubbed -- the shape every other test builds. */
function plain(extra) {
  return Object.assign({
    url: '/cocktails/recipes/x/',
    name: 'x',
    title: 'X',
    moods: ['sharp'],
    ingredients: ['gin']
  }, extra || {});
}

// --- they run at all ---------------------------------------------------------

test('both card passes load in the index harness, in the layout order', () => {
  const r = boot({ drinks: [plain({ name: 'a', url: '/a/' })] });

  assert.deepStrictEqual(r.loaded, SCRIPTS,
    'a script failed to load. `thrown` names which: ' +
    (r.thrown ? r.thrown.script + ' -- ' + r.thrown.error : 'none'));
  assert.strictEqual(r.thrown, null);

  for (const name of LAYOUT_SCRIPTS) {
    assert.ok(r.loaded.indexOf(name) !== -1, name + ' did not load');
  }
  // Both hang their re-run hook off the namespace; cocktail-index.js calls
  // them on every apply(), guarded, so a missing hook fails silently on the
  // real page (#846).
  assert.strictEqual(typeof r.sandbox.HTF.fitCardNames, 'function',
    'card-name-fit.js did not register HTF.fitCardNames');
  assert.strictEqual(typeof r.sandbox.HTF.cardLineBudget, 'function',
    'card-line-budget.js did not register HTF.cardLineBudget');
});

test('a card with nothing to measure is left alone rather than crashing', () => {
  // A card that stubs no boxes is the model of an element the browser has not
  // laid out, and both passes must return quietly from it. Every other test
  // that boots the harness relies on that.
  const r = boot({ drinks: [plain(), plain({ name: 'b', url: '/b/' })] });
  const cards = r.doc.querySelectorAll('.drink-card');

  assert.strictEqual(cards.length, 2);
  for (const card of cards) {
    assert.ok(!card.classList.contains('drink-card--ingredients-3'));
    assert.ok(!card.classList.contains('drink-card--chips-clear-ship'));
    const name = card.querySelector('.drink-card-name');
    assert.ok(!name.classList.contains('drink-card-name--fitted'),
      'an unmeasurable name was marked --fitted, which releases the no-JS ' +
      'ellipsis clip on the strength of a measurement that never happened ' +
      '(#1115).');
  }
});

// --- the ingredient line's budget --------------------------------------------

test('three rendered ingredient lines cap the chips, two do not', () => {
  const r = boot({
    drinks: [
      plain({ name: 'three', url: '/three/',
              ingredients_box: { width: 200, height: LINE * 3 } }),
      plain({ name: 'two', url: '/two/',
              ingredients_box: { width: 200, height: LINE * 2 } })
    ]
  });

  const three = r.doc.querySelector('.drink-card[data-name="three"]');
  const two = r.doc.querySelector('.drink-card[data-name="two"]');

  assert.ok(three.classList.contains('drink-card--ingredients-3'),
    'a card whose ingredient line rendered three lines did not get the class ' +
    'that caps its chip rows (#776).');
  assert.ok(!two.classList.contains('drink-card--ingredients-3'),
    'a two-line card was capped. The clamp is a CEILING -- the median drink ' +
    'fits two lines, and a rule keyed on the clamp punishes every card for ' +
    'what the tiki drinks do.');
});

test('the class comes off again when the card is re-measured narrower', () => {
  // Reset, then measure. Without the reset a card that once had three lines
  // keeps the cap for ever, even at a width where it has two.
  const r = boot({
    drinks: [plain({ ingredients_box: { width: 200, height: LINE * 3 } })]
  });
  const card = r.doc.querySelector('.drink-card');
  assert.ok(card.classList.contains('drink-card--ingredients-3'));

  card.querySelector('.drink-card-ingredients').__box =
    { width: 400, height: LINE * 2 };
  r.sandbox.HTF.cardLineBudget();

  assert.ok(!card.classList.contains('drink-card--ingredients-3'),
    'the cap survived a re-measure that found two lines, so it can never be ' +
    'taken off once given.');
});

// --- the ship collision, with a matched chip ---------------------------------
// A matched chip is an inverted block carrying its separator in a margin
// (#1099, #1100), which moves the box this pass compares against the ship's
// left edge. So the collision cases below use a matched chip.

test('a matched chip reaching the ship on its row clears the ship', () => {
  const r = boot({
    drinks: [plain({
      moods: ['sharp', 'no juicing'],
      matched_moods: ['no juicing'],
      ship_box: { width: 40, left: 160, right: 200, top: 100, bottom: 118 },
      chip_boxes: [
        // row one, well clear of the ship's row
        { width: 50, left: 0, right: 50, top: 80, bottom: 98 },
        // the ship's row, and its right edge is past the ship's left edge
        { width: 70, left: 100, right: 170, top: 100, bottom: 118 }
      ]
    })]
  });

  const card = r.doc.querySelector('.drink-card');
  assert.ok(card.classList.contains('drink-card--chips-clear-ship'),
    'a chip overlapping the ship on the ship\'s own row did not set the class ' +
    'that pads the chips clear of it. Helen, 2026-09-10, on seeing chips cut ' +
    'off mid-word: "sugar crav", "no juici".');
  assert.strictEqual(card.style.getPropertyValue('--ship-w'), '40px',
    'the stylesheet pads by the ship\'s own width, so the pass must publish ' +
    'it as a custom property on the card.');
});

test('a chip on a row above the ship is not in the way', () => {
  const r = boot({
    drinks: [plain({
      moods: ['sharp', 'no juicing'],
      matched_moods: ['no juicing'],
      ship_box: { width: 40, left: 160, right: 200, top: 100, bottom: 118 },
      chip_boxes: [
        // past the ship horizontally, but a whole row above it
        { width: 90, left: 100, right: 190, top: 80, bottom: 98 },
        { width: 50, left: 0, right: 50, top: 100, bottom: 118 }
      ]
    })]
  });

  const card = r.doc.querySelector('.drink-card');
  assert.ok(!card.classList.contains('drink-card--chips-clear-ship'),
    'a chip on a row ABOVE the ship triggered the padding. #760 took the ship ' +
    'out of flow so no chip row would pay for it; padding a row that does not ' +
    'collide is the cost that refusal was about.');
  assert.strictEqual(card.style.getPropertyValue('--ship-w'), '');
});

test('a hidden card is not measured, and keeps no collision class', () => {
  // The index paginates by setting `card.hidden`, and a hidden element
  // measures zero. Reading that zero as "no ship drawn" is right; reading it
  // as a decision is the #1115 bug.
  const r = boot({
    drinks: [plain({
      moods: ['sharp', 'no juicing'],
      matched_moods: ['no juicing'],
      ship_box: { width: 40, left: 160, right: 200, top: 100, bottom: 118 },
      chip_boxes: [{ width: 70, left: 100, right: 170, top: 100, bottom: 118 }]
    })]
  });

  const card = r.doc.querySelector('.drink-card');
  assert.ok(card.classList.contains('drink-card--chips-clear-ship'),
    'precondition: this card collides while visible');

  card.hidden = true;
  r.sandbox.HTF.cardLineBudget();

  assert.ok(!card.classList.contains('drink-card--chips-clear-ship'),
    'a hidden card kept a collision class decided when it was visible. Every ' +
    'box on it now measures zero, so there is nothing to decide from.');
});

// --- the name pass, over the same cards --------------------------------------

test('a name that fits is marked fitted and nothing else', () => {
  const r = boot({
    drinks: [plain({ name_box: { width: 100, height: 20, clientWidth: 100,
                                 contentWidth: 80 } })]
  });
  const name = r.doc.querySelector('.drink-card-name');

  assert.ok(name.classList.contains('drink-card-name--fitted'),
    'the pass ran and must say so -- that class releases the no-JS clip.');
  assert.ok(!name.classList.contains('drink-card-name--step'));
  assert.ok(!name.classList.contains('drink-card-name--wrap'));
});

test('a name one short word over steps down; the step is kept if it reaches', () => {
  // STEP is 0.86, so the step reaches a word up to clientWidth / 0.86 wide --
  // about 16% over. 110 against a 100px box is inside that, and the stepped
  // lettering then measures 95, which fits.
  const r = boot({
    drinks: [plain({ name_box: { width: 100, height: 20, clientWidth: 100,
                                 contentWidth: 110, contentWidthStepped: 95 } })]
  });
  const name = r.doc.querySelector('.drink-card-name');

  assert.ok(name.classList.contains('drink-card-name--step'),
    'Helen, 2026-09-04: "shrink when it\'s just one short-ish word too long".');
  assert.ok(!name.classList.contains('drink-card-name--wrap'));
});

test('a step that does not actually reach is undone and the name wraps', () => {
  // The prediction is a linear model and type is not quite linear. The same
  // overflow as above, but the stepped lettering still measures 104, so the
  // name wraps rather than sitting smaller and ellipsising anyway.
  const r = boot({
    drinks: [plain({ name_box: { width: 100, height: 20, clientWidth: 100,
                                 contentWidth: 110, contentWidthStepped: 104 } })]
  });
  const name = r.doc.querySelector('.drink-card-name');

  assert.ok(!name.classList.contains('drink-card-name--step'),
    'the step was kept even though the re-measure still overflowed, which is ' +
    'the worst of both treatments: small type that ellipsises.');
  assert.ok(name.classList.contains('drink-card-name--wrap'));
});

test('a name far too long goes straight to two lines', () => {
  // 200 against a 100px box is outside clientWidth / 0.86, so no plausible
  // step reaches it and the tape takes a second line instead.
  const r = boot({
    drinks: [plain({ name_box: { width: 100, height: 20, clientWidth: 100,
                                 contentWidth: 200 } })]
  });
  const name = r.doc.querySelector('.drink-card-name');

  assert.ok(!name.classList.contains('drink-card-name--step'));
  assert.ok(name.classList.contains('drink-card-name--wrap'));
});

test('a hidden card\'s name is left in its no-JS state entirely', () => {
  // #1115: a hidden element measures zero in both directions, and `0 > 0 + 1`
  // reads as "it fits". Returning before --fitted is the point: that class
  // releases the ellipsis clip, and releasing it on a measurement that could
  // not happen leaves a name running off its tape.
  const r = boot({
    drinks: [plain({ name_box: { width: 100, height: 20, clientWidth: 100,
                                 contentWidth: 400 } })]
  });
  const card = r.doc.querySelector('.drink-card');
  const name = card.querySelector('.drink-card-name');
  assert.ok(name.classList.contains('drink-card-name--wrap'),
    'precondition: this name wraps while visible');

  name.classList.remove('drink-card-name--wrap');
  name.classList.remove('drink-card-name--fitted');
  card.hidden = true;
  r.sandbox.HTF.fitCardNames();

  assert.ok(!name.classList.contains('drink-card-name--fitted'),
    'a name that could not be measured was marked --fitted, which takes away ' +
    'the no-JS fallback and puts nothing in its place (#1115).');
  assert.ok(!name.classList.contains('drink-card-name--wrap'));
  assert.ok(!name.classList.contains('drink-card-name--step'));
});

test('the name pass runs before the budget pass, as the layout loads them', () => {
  // The name decides how much room the ingredients get, and the ingredients
  // how much the chips get. The budget run first does not crash; it is
  // computed against a name that has not been fitted.
  assert.deepStrictEqual(LAYOUT_SCRIPTS,
    ['card-name-fit.js', 'card-line-budget.js']);
  assert.ok(SCRIPTS.indexOf('card-name-fit.js')
            < SCRIPTS.indexOf('card-line-budget.js'));
});
