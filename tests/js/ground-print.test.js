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
