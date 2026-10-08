// =============================================================================
// Tests for assets/js/ground-print.js — the two pure pieces of the script that
// draws cocktails' leopard once on the device and keeps it (#733). The drawing
// itself needs a canvas and IndexedDB and is looked at in a browser; what can
// go quietly wrong without either is here.
//
// Run from the repo root, with the local Node runtime:
//
//   .node-runtime/node/bin/node --test tests/js/*.test.js
// =============================================================================
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const GP = require('../../assets/js/ground-print.js');

test('a quoted custom property loses its quotes, either kind', () => {
  assert.strictEqual(GP.unquote(' "/leopard-fur.svg"'), '/leopard-fur.svg');
  assert.strictEqual(GP.unquote("'/leopard-fur.svg'"), '/leopard-fur.svg');
});

test('an unset custom property is empty, which is how a site opts out', () => {
  // getPropertyValue answers '' for a property nothing declares. Food declares
  // none of these, and '' is what makes the script return before it does
  // anything at all on a food page.
  assert.strictEqual(GP.unquote(''), '');
  assert.strictEqual(GP.unquote(undefined), '');
  assert.strictEqual(GP.unquote(null), '');
});

test('an unquoted value is left alone, and a lone quote is not stripped', () => {
  assert.strictEqual(GP.unquote('/leopard-fur.svg'), '/leopard-fur.svg');
  assert.strictEqual(GP.unquote('"/leopard-fur.svg'), '"/leopard-fur.svg');
});

test('new artwork never answers to an old picture', () => {
  // The stored picture is megabytes and is only redrawn when its key misses,
  // so the version has to be part of the key or a changed leopard would show
  // the old one forever.
  assert.notStrictEqual(GP.keyFor('cocktails', 'aaa'), GP.keyFor('cocktails', 'bbb'));
});

test('two sites on one origin do not share a picture', () => {
  assert.notStrictEqual(GP.keyFor('cocktails', 'aaa'), GP.keyFor('food', 'aaa'));
});

test('a strength of 1.5 is one full pass and one at half', () => {
  // A canvas can only draw an image fainter than it is, so "stronger" is more
  // passes. This is the number Helen chose for the fur.
  assert.deepStrictEqual(GP.passes(1.5), [1, 0.5]);
  assert.deepStrictEqual(GP.passes(1), [1]);
  assert.deepStrictEqual(GP.passes(0.5), [0.5]);
  assert.deepStrictEqual(GP.passes(2.5), [1, 1, 0.5]);
});

test('a whole-number strength has no stray faint pass from rounding', () => {
  assert.deepStrictEqual(GP.passes(2), [1, 1]);
  assert.deepStrictEqual(GP.passes(3), [1, 1, 1]);
});

test('an unset or silly strength is 1, never nothing and never unbounded', () => {
  // '' is what an undeclared custom property reads as. A typo in a stylesheet
  // must not blank the ground (0, negative, not a number) or flood it white.
  assert.strictEqual(GP.strengthOf(''), 1);
  assert.strictEqual(GP.strengthOf('banana'), 1);
  assert.strictEqual(GP.strengthOf('0'), 1);
  assert.strictEqual(GP.strengthOf('-2'), 1);
  assert.strictEqual(GP.strengthOf('99'), 4);
  assert.strictEqual(GP.strengthOf(' 1.5'), 1.5);
});

test('a phone and a desktop do not share a kept picture', () => {
  // The stylesheet gives a phone half the nap. Both keep a picture in the same
  // database if a window is ever resized across the line, and each must get
  // its own back.
  const desktop = GP.keyFor('cocktails', 'v', 1.5, '/leopard-nap.svg@1', 'rgb(3, 3, 4)');
  const phone = GP.keyFor('cocktails', 'v', 1.5, '/leopard-nap.svg@0.5', 'rgb(3, 3, 4)');
  assert.notStrictEqual(desktop, phone);
});

test('a change of fur strength or of ground colour redraws', () => {
  // The ground colour is painted INTO the picture: a palette change that left
  // the key alone would leave returning browsers with the old black.
  const base = GP.keyFor('cocktails', 'v', 1.5, 'nap', 'rgb(3, 3, 4)');
  assert.notStrictEqual(base, GP.keyFor('cocktails', 'v', 2, 'nap', 'rgb(3, 3, 4)'));
  assert.notStrictEqual(base, GP.keyFor('cocktails', 'v', 1.5, 'nap', 'rgb(6, 6, 7)'));
});
