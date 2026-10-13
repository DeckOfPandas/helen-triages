// Tests for HTF.escapeHtml in assets/js/assets.js (#686).
//
// Run from the repo root, with the local Node runtime:
//
//   .node-runtime/node/bin/node --test tests/js/*.test.js
//
// tests/js/stub-dom.js says why assets.js is loaded through a fake page.
//
// Escaping goes wrong silently: get the order wrong and `<` becomes
// `&amp;lt;`, which neither throws nor warns and shows as literal `&lt;` on
// the page.
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { loadHTF } = require('./stub-dom.js');

const HTF = loadHTF();

test('text with nothing to escape comes back unchanged', () => {
  assert.strictEqual(HTF.escapeHtml('Lemony Cavolo Nero'), 'Lemony Cavolo Nero');
});

test('an ampersand — the one that actually turns up in a title', () => {
  // "Bangers & Mash", "Gin & It": the realistic case, and the reason the
  // highlight cannot just assign the raw string to innerHTML.
  assert.strictEqual(HTF.escapeHtml('Bangers & Mash'), 'Bangers &amp; Mash');
});

test('angle brackets', () => {
  assert.strictEqual(
    HTF.escapeHtml('<script>alert(1)</script>'),
    '&lt;script&gt;alert(1)&lt;/script&gt;'
  );
});

test('both quote characters, so the same call is safe in an attribute', () => {
  assert.strictEqual(HTF.escapeHtml('say "hi"'), 'say &quot;hi&quot;');
  assert.strictEqual(HTF.escapeHtml("it's"), 'it&#39;s');
});

test('the ampersand is escaped FIRST, so an escape is not escaped twice', () => {
  assert.strictEqual(HTF.escapeHtml('&amp;'), '&amp;amp;');
  assert.strictEqual(HTF.escapeHtml('a & b < c'), 'a &amp; b &lt; c');
});

test('an empty string is an empty string', () => {
  assert.strictEqual(HTF.escapeHtml(''), '');
});

test('accented and non-ASCII text is left alone', () => {
  // Vieux Carré, and the drink names #564's highlight is rebuilt from: the
  // escaping must not touch them, or the accents would come back as entities.
  assert.strictEqual(HTF.escapeHtml('Vieux Carré'), 'Vieux Carré');
});
