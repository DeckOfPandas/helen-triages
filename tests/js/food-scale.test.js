// =============================================================================
// food-scale.js — one food amount at a factor. #1005
//
// Run from the repo root with `node --test`.
// =============================================================================
// Every expectation below is a rule Helen has already given for the shopping
// list (#801), because this module prints through the same formatter: grams
// to the gram, spoons in cook's fractions, ranges carried at both ends, the
// bracket scaled with its number. The only thing new is the shape -- one
// amount in, one amount out -- and the two answers at the edges: an amount
// with no number comes back as written and says so, and a kilogram halved
// comes back as grams.
'use strict';

const test = require('node:test');
const assert = require('node:assert');

const foodScale = require('../../assets/js/food-scale.js');
const { scaleAmount } = foodScale;

function at(amount, factor) {
  return scaleAmount(amount, factor).text;
}

test('grams scale to the gram, never coarser', () => {
  assert.strictEqual(at('200 g', 2), '400 g');
  assert.strictEqual(at('200 g', 2 / 3), '133 g');
  assert.strictEqual(at('200 g', 0.5), '100 g');
});

test('a kilogram halved is grams, and a kilogram kept is a kilogram', () => {
  assert.strictEqual(at('1.2 kg', 2), '2.4 kg');
  assert.strictEqual(at('1.2 kg', 0.5), '600 g');
  assert.strictEqual(at('600 g', 2), '1.2 kg');
});

test('spoons and counts print in cook\'s fractions', () => {
  assert.strictEqual(at('½ tsp', 2), '1 tsp');
  assert.strictEqual(at('½ tsp', 3), '1½ tsp');
  assert.strictEqual(at('1 tbsp', 2 / 3), '⅔ tbsp');
  assert.strictEqual(at('2', 1.5), '3');
});

test('"2 large" scales -- Helen: "Things like 2 large can scale, surely"', () => {
  assert.strictEqual(at('2 large', 2), '4 large');
  assert.strictEqual(at('1 large', 3), '3 large');
});

test('a range is carried at both ends', () => {
  assert.strictEqual(at('30–50 g', 2), '60–100 g');
});

test('a tilde survives', () => {
  assert.strictEqual(at('~2 tbsp', 2), '~4 tbsp');
});

test('a bracket that restates the quantity scales with it', () => {
  assert.strictEqual(at('1 tbsp (6 g)', 2), '2 tbsp (12 g)');
});

test('a compound unit keeps its plural', () => {
  assert.strictEqual(at('2 x 400 g cans', 2), '4 x 400 g cans');
  assert.strictEqual(at('3 cloves', 1 / 3), '1 clove');
});

test('an amount with no number comes back as written, and says so', () => {
  // The line the note under the control is built from -- Helen: "let's add a
  // note to bitters and handfuls".
  const r = scaleAmount('a few handfuls', 2);
  assert.strictEqual(r.text, 'a few handfuls');
  assert.strictEqual(r.scaled, false);
  assert.strictEqual(scaleAmount('some', 0.5).scaled, false);
  assert.strictEqual(scaleAmount('', 2).text, '');
});

test('a scaled amount says it moved', () => {
  assert.strictEqual(scaleAmount('200 g', 2).scaled, true);
});

test('a factor that is not a positive number leaves the amount alone', () => {
  assert.strictEqual(scaleAmount('200 g', 0).text, '200 g');
  assert.strictEqual(scaleAmount('200 g', NaN).scaled, false);
});
