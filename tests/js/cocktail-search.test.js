// =============================================================================
// Tests for assets/js/cocktail-search.js — the cocktail index's pool building,
// candidate ranking, declared-family umbrellas and the two matching rules.
// No DOM required. GitHub issues #579 (the extraction) and #549 (what it fixes).
//
// Run from the repo root, with the local Node runtime:
//
//   .node-runtime/node/bin/node --test
//
// See tests/js/ingredient-search.test.js for why not the system node.
//
// -----------------------------------------------------------------------------
// WHY THIS FILE EXISTS AT ALL, since cocktail-index.js ran untested for weeks:
// every behaviour below was hand-rolled inside 428 lines of DOM wiring, where
// the only way to ask it a question was to open a browser and type. back-link.js
// is the argument (HANDOVER §3) and it applies exactly: "does a chip named `gin`
// exclude a drink whose only gin-shaped ingredient is ginger syrup?" is a
// question a pure function can be asked and a page cannot.
// =============================================================================
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const CS = require('../../assets/js/cocktail-search.js');

// A small stand-in for _data/cocktails/ingredients.yml, carrying only the keys
// this module reads. Real values, taken from the file, so a rename there shows
// up here rather than in a browser.
const VOCAB = {
  search: { min_query_chars: 2, family_button_min_chars: 3, pool_cap: 8 },
  families: ['rum', 'gin', 'whisky', 'amaro'],
  family_of: {
    'London dry gin': 'gin',
    'Old Tom': 'gin',
    'Plymouth': 'gin',
    'aged Demerara rum': 'rum',
    'Demerara overproof rum': 'rum',
    'moderately aged Jamaican rum': 'rum',
    'Campari': 'amaro',
    'Aperol': 'amaro'
  },
  card_names: {
    'London dry gin': 'gin',
    'aged Demerara rum': 'Demerara rum',
    'Demerara overproof rum': 'Demerara rum',
    'moderately aged Jamaican rum': 'Jamaican rum'
  }
};

const S = CS.create(VOCAB);

// The attribute cocktails/index.html writes: entries joined and terminated with
// `|`, the whole thing downcased at build time.
const attr = (...entries) => entries.map((e) => e + '|').join('');

// --- splitting the attribute -------------------------------------------------

test('an entry list round-trips out of the build-time attribute', () => {
  assert.deepStrictEqual(
    CS.splitEntries(attr('lime juice', 'gin', 'sugar syrup')),
    ['lime juice', 'gin', 'sugar syrup']
  );
});

test('an empty or missing attribute is no entries, not one empty entry', () => {
  assert.deepStrictEqual(CS.splitEntries(''), []);
  assert.deepStrictEqual(CS.splitEntries(undefined), []);
  assert.deepStrictEqual(CS.splitEntries('|'), []);
});

// --- the pool ----------------------------------------------------------------

test('the pool is every distinct entry across every card, deduplicated', () => {
  const pool = S.buildPool([attr('lime juice', 'gin'), attr('gin', 'absinthe')]);
  assert.deepStrictEqual(pool, ['absinthe', 'gin', 'lime juice']);
});

test('the sort is case-insensitive, so a stray capital does not jump the list', () => {
  // The template downcases before writing the attribute, so this should not
  // arise -- but a plain .sort() puts every capital ahead of every lowercase
  // letter, which is the trap ingredient-search.js's buildMasterList records,
  // and "the values happen to arrive lowercase" is a fact about the template
  // rather than about this function.
  const pool = S.buildPool([attr('absinthe', 'Gin', 'lime juice')]);
  assert.deepStrictEqual(pool, ['absinthe', 'Gin', 'lime juice']);
});

// --- folding: GitHub issue #45's problem, on this site -----------------------
// Measured 2026-08-29 over all 114 drafts: 19 of the 240 pool terms carry an
// accent (crème de cassis, cachaça, bénédictine, blue curaçao) and three drink
// names do (Jägerita, Vieux Carré, Champs Elysées). Before this module none of
// them was reachable by typing ASCII, because cocktail-index.js folded nothing.

test('an unaccented query finds an accented entry', () => {
  const pool = S.buildPool([attr('crème de cassis', 'cachaça', 'bénédictine')]);
  assert.deepStrictEqual(S.search('creme', pool).results.map((r) => r.entry), ['crème de cassis']);
  assert.deepStrictEqual(S.search('cachaca', pool).results.map((r) => r.entry), ['cachaça']);
  assert.deepStrictEqual(S.search('bene', pool).results.map((r) => r.entry), ['bénédictine']);
});

test('an accented query still finds its own entry -- folding cuts both ways', () => {
  const pool = S.buildPool([attr('crème de cassis')]);
  assert.deepStrictEqual(S.search('crème', pool).results.map((r) => r.entry), ['crème de cassis']);
});

test('the DISPLAY entry keeps its accents -- folding is for matching only', () => {
  const pool = S.buildPool([attr('crème de mûre')]);
  assert.strictEqual(S.search('creme', pool).results[0].entry, 'crème de mûre');
});

test('a hyphen reads as a space, so a naturally typed two-word query matches', () => {
  const pool = S.buildPool([attr('lavender-forward bitters')]);
  assert.strictEqual(S.search('lavender forward', pool).results.length, 1);
});

// --- the three bands ---------------------------------------------------------
// The ordering rule is HTF.ingredientSearch's, shared rather than re-derived --
// see assets/js/ingredient-search.js's orderByBand. What each site computes for
// itself is the two PREDICATES, because they are answered in different
// vocabularies; the ordering is what kept drifting and is what is now shared.

test('an entry starting with the query outranks a word match, which outranks a substring', () => {
  const pool = S.buildPool([attr('lime juice', 'apricot liqueur', 'galliano')]);
  // "li": prefix `lime juice`; word-start `apricot liqueur`; substring `galliano`.
  assert.deepStrictEqual(
    S.search('li', pool).results.map((r) => r.entry),
    ['lime juice', 'apricot liqueur', 'galliano']
  );
});

test('alphabetical within a band comes free, because the pool is already sorted', () => {
  const pool = S.buildPool([attr('lime juice', 'lime cordial', 'lime')]);
  assert.deepStrictEqual(
    S.search('lim', pool).results.map((r) => r.entry),
    ['lime', 'lime cordial', 'lime juice']
  );
});

test('a word match is flagged, so the picker can mark what you actually meant', () => {
  const pool = S.buildPool([attr('lime juice', 'apricot liqueur', 'galliano')]);
  const byEntry = {};
  S.search('li', pool).results.forEach((r) => { byEntry[r.entry] = r; });
  assert.strictEqual(byEntry['lime juice'].isPrefixMatch, true);
  assert.strictEqual(byEntry['lime juice'].hasWordMatch, true);
  assert.strictEqual(byEntry['apricot liqueur'].isPrefixMatch, false);
  assert.strictEqual(byEntry['apricot liqueur'].hasWordMatch, true);
  assert.strictEqual(byEntry['galliano'].hasWordMatch, false);
});

// --- the cap, and saying so --------------------------------------------------

test('the pool is capped and the remainder is COUNTED, never silently dropped', () => {
  const many = [];
  for (let i = 0; i < 12; i++) many.push('liqueur ' + String.fromCharCode(97 + i));
  const pool = S.buildPool([attr(...many)]);
  const result = S.search('liq', pool);
  assert.strictEqual(result.results.length, 8);
  assert.strictEqual(result.hidden, 4);
});

test('nothing hidden reports zero rather than a negative', () => {
  const pool = S.buildPool([attr('gin', 'absinthe')]);
  assert.strictEqual(S.search('gin', pool).hidden, 0);
});

// --- the minimum query length ------------------------------------------------
// #549 point 4. The number lives in _data/cocktails/ingredients.yml, not here
// and not in the DOM wiring -- the same rule food's family_button_min_chars
// follows, and test_the_cocktail_search_config_is_not_hardcoded enforces it.

test('a query shorter than the declared minimum offers nothing at all', () => {
  const pool = S.buildPool([attr('gin', 'gin liqueur')]);
  assert.deepStrictEqual(S.search('g', pool).results, []);
  assert.strictEqual(S.search('g', pool).hidden, 0);
  assert.strictEqual(S.search('gi', pool).results.length, 2);
});

test('an empty query is not a search', () => {
  const pool = S.buildPool([attr('gin')]);
  assert.deepStrictEqual(S.search('', pool).results, []);
  assert.deepStrictEqual(S.search('   ', pool).results, []);
});

// --- already-chosen chips ----------------------------------------------------

test('an entry already chosen is not offered again', () => {
  const pool = S.buildPool([attr('lime', 'lime juice')]);
  assert.deepStrictEqual(
    S.search('lim', pool, ['lime']).results.map((r) => r.entry),
    ['lime juice']
  );
});

// =============================================================================
// DECLARED FAMILIES — _data/cocktails/ingredients.yml's `family_of`
// =============================================================================
// The file has said since #322 what these are for: "the ingredient search's
// `(all)` buttons ... and exclusion. 'I don't like Scotch' is a family-level
// operation." 68 generics are mapped across 10 families and the index read none
// of them until now, which is what #549 point 1 is actually asking for.
//
// FOOD'S FAMILY DERIVATION IS NOT REUSED AND MUST NOT BE. An (all) button on
// the food site forms where entries share a head word after normalisation.
// These styles share no word at all -- "aged Demerara rum" and "moderately aged
// Jamaican rum" have nothing textually in common -- which is exactly why the
// family is DECLARED here. What is shared with food is the CONSUMPTION of a
// declared family, which is what `synonyms` in ingredient_words.yml already is.

test('a family whose name starts the query earns an (all) button', () => {
  const pool = S.buildPool([attr('london dry gin', 'old tom')]);
  assert.deepStrictEqual(S.search('gin', pool).familyButtons, ['gin']);
});

test('a family button forms from a prefix, not only from the whole word', () => {
  const pool = S.buildPool([attr('aged demerara rum')]);
  assert.deepStrictEqual(S.search('rum', pool).familyButtons, ['rum']);
  assert.deepStrictEqual(S.search('ru', pool).familyButtons, []); // under the min
});

test('a family with no member anywhere in the pool offers no button', () => {
  // `whisky` is declared in `families` but no pool entry belongs to it here.
  const pool = S.buildPool([attr('gin')]);
  assert.deepStrictEqual(S.search('whi', pool).familyButtons, []);
});

test('the (all) button carries the suffix filter-state.js already spells', () => {
  assert.strictEqual(CS.FAMILY_SUFFIX, ' (all)');
});

test('a card name resolves to the family of the generic it abbreviates', () => {
  // `Demerara rum` is a card name for two different rum generics (#501's
  // deliberate, declared collapse), and both are family `rum`.
  assert.deepStrictEqual(S.familiesOf('demerara rum'), ['rum']);
  assert.deepStrictEqual(S.familiesOf('london dry gin'), ['gin']);
});

test('an entry with no declared family has none -- lime juice is not a family', () => {
  assert.deepStrictEqual(S.familiesOf('lime juice'), []);
  assert.deepStrictEqual(S.familiesOf('havana 3'), []);
});

// =============================================================================
// THE TWO MATCHING RULES, AND THEY ARE DELIBERATELY DIFFERENT
// =============================================================================
// Food's rule, and the reason for the asymmetry is the cost of being wrong in
// each direction. Over-including shows you a drink you may not want: visible,
// and you can see why it is there. Over-EXCLUDING hides a drink you would have
// had: invisible, and you never learn it existed. So: fuzzy to find, fuzzy to
// include, exact-or-declared-family to exclude.
//
// WHAT THIS REPLACES. cocktail-index.js matched both directions with a raw
// substring test against the whole concatenated attribute -- exactly what
// filter-state.js's excludesRow() forbids on the food side ("excluding peas
// would silently lose the peanut butter cookies and the pearl barley
// casserole"). Measured over 114 drinks, 26 of 240 pool terms over-matched:
// `gin` hid 12 drinks whose only gin-shaped ingredient was ginger, `water` hid
// 13 whose only water was honey water, and `apple juice` matched 15 drinks that
// have pineapple juice.

test('EXCLUDE is exact: a gin chip does not take the ginger with it', () => {
  const ginger = CS.splitEntries(attr('ginger syrup', 'lime juice'));
  const gin = CS.splitEntries(attr('gin', 'lime juice'));
  assert.strictEqual(S.matchesExclude(ginger, 'gin'), false);
  assert.strictEqual(S.matchesExclude(gin, 'gin'), true);
});

test('EXCLUDE is exact: honey water is not water, and pineapple juice is not apple juice', () => {
  const honey = CS.splitEntries(attr('honey water 2:1'));
  assert.strictEqual(S.matchesExclude(honey, 'water'), false);
  const pineapple = CS.splitEntries(attr('pineapple juice'));
  assert.strictEqual(S.matchesExclude(pineapple, 'apple juice'), false);
});

test('EXCLUDE never matches across an entry boundary', () => {
  // The old substring test ran against "lime|gin|", where "e|g" spans two
  // entries. Nothing typed should ever be able to see that seam.
  const entries = CS.splitEntries(attr('lime', 'gin'));
  assert.strictEqual(S.matchesExclude(entries, 'e|g'), false);
  assert.strictEqual(S.matchesExclude(entries, 'megi'), false);
});

test('EXCLUDE widens only through a declared family, which says so on its face', () => {
  const demerara = CS.splitEntries(attr('aged demerara rum', 'lime juice'));
  assert.strictEqual(S.matchesExclude(demerara, 'rum'), false);
  assert.strictEqual(S.matchesExclude(demerara, 'rum (all)'), true);
  assert.strictEqual(S.matchesExclude(demerara, 'gin (all)'), false);
});

test('EXCLUDE by family reaches an entry named only by its card name', () => {
  const carded = CS.splitEntries(attr('demerara rum'));
  assert.strictEqual(S.matchesExclude(carded, 'rum (all)'), true);
});

test('INCLUDE is fuzzy: a lime chip finds the lime juice', () => {
  const entries = CS.splitEntries(attr('lime juice', 'gin'));
  assert.strictEqual(S.matchesInclude(entries, 'lime'), true);
});

test('INCLUDE is a word PREFIX, not a substring -- apple juice is not pineapple juice', () => {
  const pineapple = CS.splitEntries(attr('pineapple juice'));
  assert.strictEqual(S.matchesInclude(pineapple, 'apple juice'), false);
  assert.strictEqual(S.matchesInclude(pineapple, 'pineapple'), true);
});

test('INCLUDE needs EVERY word of the chip to land somewhere in the entry', () => {
  const entries = CS.splitEntries(attr('sugar syrup 2:1'));
  assert.strictEqual(S.matchesInclude(entries, 'sugar syrup'), true);
  assert.strictEqual(S.matchesInclude(entries, 'honey syrup'), false);
});

test('INCLUDE also honours a declared family', () => {
  const entries = CS.splitEntries(attr('old tom', 'lime juice'));
  assert.strictEqual(S.matchesInclude(entries, 'gin (all)'), true);
  assert.strictEqual(S.matchesInclude(entries, 'rum (all)'), false);
});

test('both rules fold, so an accented ingredient is filterable at all', () => {
  const entries = CS.splitEntries(attr('crème de cassis'));
  assert.strictEqual(S.matchesInclude(entries, 'creme de cassis'), true);
  assert.strictEqual(S.matchesExclude(entries, 'creme de cassis'), true);
});

// --- the name search ---------------------------------------------------------
// I KNOW WHAT I WANT is substring rather than word-start, and deliberately: a
// drink name is a thing you already hold and are part-way through typing, so
// "negr" should find the Negroni. What it was missing is folding -- three drink
// names carry an accent and none was typeable.

test('a drink name matches part-way through typing', () => {
  assert.strictEqual(S.matchesName('Negroni', 'negr'), true);
  assert.strictEqual(S.matchesName('Negroni', 'groni'), true);
  assert.strictEqual(S.matchesName('Negroni', 'daiquiri'), false);
});

test('an unaccented query finds an accented drink name', () => {
  assert.strictEqual(S.matchesName('Vieux Carré', 'vieux carre'), true);
  assert.strictEqual(S.matchesName('Jägerita', 'jagerita'), true);
  assert.strictEqual(S.matchesName('Champs Elysées', 'elysees'), true);
});

test('an empty name query matches everything, rather than nothing', () => {
  assert.strictEqual(S.matchesName('Negroni', ''), true);
});

// --- the highlight -----------------------------------------------------------
// #564: the card must be able to say WHY it survived, which HANDOVER §9.13
// makes the card's one job. The drink page equivalent is filters.js's
// updateTitleHighlights().

test('the matched run of a title is located in the ORIGINAL string, accents intact', () => {
  assert.deepStrictEqual(S.nameHighlight('Vieux Carré', 'carre'), { start: 6, end: 11 });
  assert.deepStrictEqual(S.nameHighlight('Negroni', 'negr'), { start: 0, end: 4 });
});

test('no query and no match both highlight nothing', () => {
  assert.strictEqual(S.nameHighlight('Negroni', ''), null);
  assert.strictEqual(S.nameHighlight('Negroni', 'zzz'), null);
});

test('a matched ingredient on a card is found by the same rule the filter used', () => {
  // The card's data-ing carries generic + card name + suggestion for ONE
  // ingredient. A card found by typing "el dorado" prints no such words (#501),
  // so this must read the attribute and not the rendered text.
  const rum = CS.splitEntries(attr('aged demerara rum', 'demerara rum', 'el dorado 12'));
  assert.strictEqual(S.entryIsHit(rum, ['rum (all)']), true);
  assert.strictEqual(S.entryIsHit(rum, ['el dorado']), true);
  assert.strictEqual(S.entryIsHit(CS.splitEntries(attr('lime juice')), ['lime']), true);
  assert.strictEqual(S.entryIsHit(CS.splitEntries(attr('ginger syrup')), ['gin']), true);
  assert.strictEqual(S.entryIsHit(CS.splitEntries(attr('ginger syrup')), []), false);
});
