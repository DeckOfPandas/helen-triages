// =============================================================================
// Tests for HTF.escapeHtml in assets/js/assets.js — GitHub issue #686.
//
// Run from the repo root, with the local Node runtime:
//
//   .node-runtime/node/bin/node --test tests/js/*.test.js
//
// See tests/js/ingredient-search.test.js for why not the system node, and
// tests/js/stub-dom.js for why this file loads assets.js through a fake page
// instead of requiring it.
//
// WHY THIS FILE EXISTS. The function was written twice — filters.js for a
// recipe title's matched run, cocktail-index.js for a drink name's — and both
// copies were untested, because both were buried inside a file full of DOM
// wiring where the only way to ask them a question was to type into a search
// box in a browser. Escaping is exactly the kind of thing that goes wrong
// silently: get the order wrong and `<` becomes `&amp;lt;`, which does not
// throw, does not warn, and only shows up as literal `&lt;` on the page.
// =============================================================================
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
  // The ordering bug this function is most likely to acquire: replace `<`
  // before `&` and this comes out as `&amp;lt;`, which renders as the literal
  // text "&lt;" rather than as a less-than sign.
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
