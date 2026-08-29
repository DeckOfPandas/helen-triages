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
  search: {
    min_query_chars: 2,
    family_button_min_chars: 3,
    pool_cap: 8,
    // The real list, from _data/cocktails/ingredients.yml. `and` is absent on
    // purpose: `Wray and Nephew` is one bottle.
    prose_words: ['a', 'an', 'or', 'if', 'you', 'your', 'need', 'needs', 'best',
      'better', 'prefer', 'other', 'instead', 'sub', 'fine', 'use', 'using',
      'when', 'with', 'for', 'unless', 'though', 'is'],
    prose_marks: ['--', '—', '?', '!', '>', ',']
  },
  families: ['rum', 'gin', 'whisky', 'amaro'],
  family_aliases: { whiskey: 'whisky', scotch: 'whisky', rhum: 'rum' },
  family_labels: { whisky: 'whisk(e)y' },
  family_of: {
    'London dry gin': 'gin',
    'Old Tom': 'gin',
    'Plymouth': 'gin',
    'aged Demerara rum': 'rum',
    'Demerara overproof rum': 'rum',
    'moderately aged Jamaican rum': 'rum',
    'moderately aged rum': 'rum',
    'bourbon': 'whisky',
    'rye': 'whisky',
    'Campari': 'amaro',
    'Aperol': 'amaro'
  },
  // A list-valued key is a generic vocabulary — that is how the module tells a
  // name Helen chose from text someone transcribed, the same shape
  // test_cocktails.py's _declared_generics reads.
  syrups: ['ginger and lemongrass cordial', 'sugar syrup 1:1', 'sugar syrup 2:1'],
  cane_and_palm_spirits: ['coconut rum', 'moderately aged rum'],
  liqueurs: ['falernum', 'apricot liqueur', 'cherry liqueur', 'gin liqueur'],
  juices: ['lime juice', 'lime', 'lime cordial'],
  card_names: {
    'London dry gin': 'gin',
    'aged Demerara rum': 'Demerara rum',
    'Demerara overproof rum': 'Demerara overproof rum',
    'moderately aged Jamaican rum': 'Jamaican rum',
    'moderately aged rum': 'aged rum',
    'sugar syrup 1:1': 'sugar syrup',
    'sugar syrup 2:1': 'sugar syrup'
  }
};

// _data/cocktails/bottles.yml, trimmed to the keys this module reads. A bottle
// keeps ONE identity through its aliases; `unresolved_suggestions` is the file's
// own declared list of suggestion strings that are not a usable bottle name,
// each carrying its reason.
const BOTTLES = {
  bottles: {
    'Wray & Nephew': {
      generic: 'unaged overproof Jamaican rum',
      aliases: ['Wray and Nephew', 'Wray & Nephew Overproof']
    },
    'El Dorado 3': { generic: 'lightly aged and filtered rum', aliases: ['ED3', 'El Dorado 3yo'] },
    'Rum Fire': { generic: 'unaged overproof Jamaican rum' },
    // The measured collision: `coconut rum` is a DECLARED GENERIC and also a
    // declared alias of this bottle. Resolving it would put a brand back into
    // the picker, reversing #501.
    'Malibu': { generic: 'coconut rum', aliases: ['Coconut rum'] }
  },
  unresolved_suggestions: {
    'Wray & Nephew, or Rum Fire': 'Two bottles in one string; wants the list form.',
    'ED3 or Havana 3': 'Two bottles in one string; wants the list form.'
  }
};

const S = CS.create(VOCAB, BOTTLES);

// The attribute cocktails/index.html writes: entries joined and terminated with
// `|`, the whole thing downcased at build time.
const attr = (...entries) => entries.map((e) => e + '|').join('');

// Several unrelated pours, each its own group. buildPool takes one group per
// INGREDIENT — putting two pours in one group says a bottle in it belongs to
// the other one's generic, which is the pairing the whole thing turns on.
const pours = (...terms) => terms.map((t) => attr(t));

// The pool holds CHIPS now, not strings — see the note on chipForTerm in
// cocktail-search.js. Most cases below only care what the buttons SAY.
const labels = (pool) => pool.map((c) => c.value);

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
  const pool = S.buildPool(pours('lime juice', 'absinthe', 'absinthe', 'campari'));
  assert.deepStrictEqual(labels(pool), ['absinthe', 'campari', 'lime juice']);
});

test('the sort is case-insensitive, so a stray capital does not jump the list', () => {
  // The template downcases before writing the attribute, so this should not
  // arise -- but a plain .sort() puts every capital ahead of every lowercase
  // letter, which is the trap ingredient-search.js's buildMasterList records,
  // and "the values happen to arrive lowercase" is a fact about the template
  // rather than about this function.
  const pool = S.buildPool(pours('absinthe', 'Campari', 'lime juice'));
  assert.deepStrictEqual(labels(pool), ['absinthe', 'Campari', 'lime juice']);
});

// --- folding: GitHub issue #45's problem, on this site -----------------------
// Measured 2026-08-29 over all 114 drafts: 19 of the 240 pool terms carry an
// accent (crème de cassis, cachaça, bénédictine, blue curaçao) and three drink
// names do (Jägerita, Vieux Carré, Champs Elysées). Before this module none of
// them was reachable by typing ASCII, because cocktail-index.js folded nothing.

test('an unaccented query finds an accented entry', () => {
  const pool = S.buildPool(pours('crème de cassis', 'cachaça', 'bénédictine'));
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
  const pool = S.buildPool(pours('lime juice', 'apricot liqueur', 'galliano'));
  // "li": prefix `lime juice`; word-start `apricot liqueur`; substring `galliano`.
  assert.deepStrictEqual(
    S.search('li', pool).results.map((r) => r.entry),
    ['lime juice', 'apricot liqueur', 'galliano']
  );
});

test('alphabetical within a band comes free, because the pool is already sorted', () => {
  const pool = S.buildPool(pours('lime juice', 'lime cordial', 'lime'));
  assert.deepStrictEqual(
    S.search('lim', pool).results.map((r) => r.entry),
    ['lime', 'lime cordial', 'lime juice']
  );
});

test('a word match is flagged, so the picker can mark what you actually meant', () => {
  const pool = S.buildPool(pours('lime juice', 'apricot liqueur', 'galliano'));
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
  // Two letters, not one: a bare "a" is a prose word, so `liqueur a` is
  // correctly not a bottle name and the first version of this fixture built
  // twelve strings the pool was right to refuse.
  for (let i = 0; i < 12; i++) many.push('liqueur x' + String.fromCharCode(97 + i));
  const pool = S.buildPool(pours(...many));
  const result = S.search('liq', pool);
  assert.strictEqual(result.results.length, 8);
  assert.strictEqual(result.hidden, 4);
});

test('nothing hidden reports zero rather than a negative', () => {
  const pool = S.buildPool(pours('gin', 'absinthe'));
  assert.strictEqual(S.search('gin', pool).hidden, 0);
});

// --- the minimum query length ------------------------------------------------
// #549 point 4. The number lives in _data/cocktails/ingredients.yml, not here
// and not in the DOM wiring -- the same rule food's family_button_min_chars
// follows, and test_the_cocktail_search_config_is_not_hardcoded enforces it.

test('a query shorter than the declared minimum offers nothing at all', () => {
  // Two ingredients, so two groups. buildPool takes one group per INGREDIENT —
  // putting both in one would say they are the same pour, and a bottle in a
  // group is read as a bottle FOR that group's generic.
  const pool = S.buildPool([attr('gin'), attr('gin liqueur')]);
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
  const pool = S.buildPool(pours('lime', 'lime juice'));
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
  const pool = S.buildPool(pours('london dry gin', 'old tom'));
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

// --- a family answers to more than one name — Helen, 2026-08-29 --------------
// "'whiskey (all)' should return all whisky and bourbon and rye, and the same
// for 'whisky'." The family already HELD all three; the spelling found nothing.

test('an alias spelling reaches the family, whatever the button ends up called', () => {
  const pool = S.buildPool(pours('bourbon', 'rye'));
  ['whisky', 'whiskey', 'scotch'].forEach((typed) => {
    assert.strictEqual(S.search(typed, pool).familyButtons.length, 1, typed);
  });
});

test('an alias never mints a SECOND umbrella, which would lie about its width', () => {
  // The whisky family holds bourbon and rye. A button labelled "scotch (all)"
  // returning bourbon is an umbrella misdescribing itself, so one button
  // appears and it carries the family's own name -- Helen was shown that trade
  // and asked for the alias anyway.
  const pool = S.buildPool(pours('bourbon', 'rye'));
  const buttons = S.search('scotch', pool).familyButtons;
  assert.strictEqual(buttons.length, 1);
  assert.strictEqual(buttons[0], 'whisk(e)y');
});

test('the whisky umbrella takes the bourbon and the rye with it', () => {
  const bourbon = CS.splitEntries(attr('bourbon', 'lemon juice'));
  const rye = CS.splitEntries(attr('rye'));
  const gin = CS.splitEntries(attr('old tom'));
  assert.strictEqual(S.matchesInclude(bourbon, 'whisk(e)y (all)'), true);
  assert.strictEqual(S.matchesInclude(rye, 'whisk(e)y (all)'), true);
  assert.strictEqual(S.matchesInclude(gin, 'whisk(e)y (all)'), false);
});

test('an alias that names no family is still just a word', () => {
  const pool = S.buildPool([attr('bourbon')]);
  assert.deepStrictEqual(S.search('vodka', pool).familyButtons, []);
});

test('an (all) button already chosen is not offered a SECOND time', () => {
  // Helen, 2026-08-29, with a screenshot of `whisky (all)` rendered twice --
  // once filled because it was selected, once plain beside it: "If I click
  // 'whiskey (all)', I see the same button again."
  //
  // The chosen chips are drawn first, then the search's results. Pool
  // candidates were filtered against what was already chosen and FAMILY
  // BUTTONS were not, so an umbrella you had picked came back round as an
  // offer. Same class of omission as issue #390's dropped flag: the answer was
  // computed correctly and one of the two consumers ignored it.
  const pool = S.buildPool(pours('bourbon', 'rye'));
  assert.deepStrictEqual(S.search('whi', pool).familyButtons, ['whisk(e)y']);
  assert.deepStrictEqual(S.search('whi', pool, ['whisk(e)y (all)']).familyButtons, []);
});

test('choosing one family does not hide another', () => {
  const pool = S.buildPool(pours('bourbon', 'old tom'));
  assert.deepStrictEqual(S.search('gin', pool, ['whisk(e)y (all)']).familyButtons, ['gin']);
});

// --- the family's own display name -------------------------------------------
// Helen, 2026-08-29: "I think that chip should be 'whisk(e)y (all)', even though
// it's clunky, to avoid ever having to split or claim they combine."
//
// A DISPLAY LABEL, not a rename of the family. `whisky_characters` is keyed off
// the family name by test_a_declared_character_vocabulary_is_enforced (it
// strips the `_characters` suffix), so renaming the family would drag
// `whisk(e)y_characters` along with it. Same separation `card_names` already
// draws for generics: matching runs on the key, the button shows the name.

test('a family with a declared label wears it on the button', () => {
  const pool = S.buildPool(pours('bourbon', 'rye'));
  assert.deepStrictEqual(S.search('whisky', pool).familyButtons, ['whisk(e)y']);
  assert.deepStrictEqual(S.search('whiskey', pool).familyButtons, ['whisk(e)y']);
  assert.deepStrictEqual(S.search('scotch', pool).familyButtons, ['whisk(e)y']);
});

test('a family with no declared label keeps its own name', () => {
  const pool = S.buildPool([attr('old tom')]);
  assert.deepStrictEqual(S.search('gin', pool).familyButtons, ['gin']);
});

test('the labelled chip still filters by the family underneath it', () => {
  const bourbon = CS.splitEntries(attr('bourbon'));
  const gin = CS.splitEntries(attr('old tom'));
  assert.strictEqual(S.matchesInclude(bourbon, 'whisk(e)y (all)'), true);
  assert.strictEqual(S.matchesExclude(bourbon, 'whisk(e)y (all)'), true);
  assert.strictEqual(S.matchesInclude(gin, 'whisk(e)y (all)'), false);
});

test('the label is reachable by typing it, parentheses and all', () => {
  const pool = S.buildPool([attr('bourbon')]);
  assert.deepStrictEqual(S.search('whisk(e)', pool).familyButtons, ['whisk(e)y']);
});

// =============================================================================
// ONE CHIP PER CATEGORY, WEARING THE CARD'S NAME — Helen, 2026-08-29
// =============================================================================
// "we have no 'aged rum' in our dictionary", said looking at `aged rum` and
// `moderately aged rum` offered as two separate buttons. Fifteen generics in
// the real collection had their card name in the pool as a chip of its own, and
// eleven of those fifteen pairs selected exactly the same drinks.

test('a generic with a card name is not offered twice', () => {
  // The rum's own group carries both spellings, exactly as data-ing does; the
  // lime is a separate pour.
  const pool = S.buildPool([attr('moderately aged rum', 'aged rum'), attr('lime juice')]);
  assert.deepStrictEqual(labels(pool), ['aged rum', 'lime juice']);
});

test('the surviving chip wears the CARD name, so the picker and the card agree', () => {
  const pool = S.buildPool([attr('moderately aged rum')]);
  assert.deepStrictEqual(labels(pool), ['aged rum']);
});

test('the generic stays searchable -- collapsing a pair must not lose a way in', () => {
  // Typing the generic still finds the chip; it just never appears as a second
  // button. Food's display_names is the same idea: "matching still has to run
  // against the real match key, not the pretty name."
  const pool = S.buildPool([attr('moderately aged rum')]);
  assert.deepStrictEqual(S.search('moderately', pool).results.map((r) => r.entry), ['aged rum']);
  assert.deepStrictEqual(S.search('aged', pool).results.map((r) => r.entry), ['aged rum']);
});

test('a chip is ranked by its BEST term, not only by the name on its face', () => {
  // "moderately" is a band-1 prefix of the generic and appears nowhere in the
  // card name, so ranking the chip by its label alone would bury it.
  const pool = S.buildPool(pours('moderately aged rum', 'lime juice'));
  const hit = S.search('moderately', pool).results[0];
  assert.strictEqual(hit.entry, 'aged rum');
  assert.strictEqual(hit.isPrefixMatch, true);
});

test('a chip that stands for two generics selects both -- the ratios collapse', () => {
  // §9.10.1: "a ratio is a MAKING fact, not a CHOOSING fact." One `sugar syrup`
  // chip rather than a 1:1 button and a 2:1 button.
  const pool = S.buildPool([attr('sugar syrup 1:1'), attr('sugar syrup 2:1')]);
  assert.deepStrictEqual(labels(pool), ['sugar syrup']);

  const oneToOne = CS.splitEntries(attr('sugar syrup 1:1'));
  const twoToOne = CS.splitEntries(attr('sugar syrup 2:1'));
  assert.strictEqual(S.matchesInclude(oneToOne, 'sugar syrup'), true);
  assert.strictEqual(S.matchesInclude(twoToOne, 'sugar syrup'), true);
  assert.strictEqual(S.matchesExclude(oneToOne, 'sugar syrup'), true);
  assert.strictEqual(S.matchesExclude(twoToOne, 'sugar syrup'), true);
});

test('a card-name chip excludes exactly what it includes, and nothing wider', () => {
  // The collapse must not smuggle a substring rule back in: `aged rum` covers
  // `moderately aged rum` because the vocabulary SAYS so, not because one
  // string contains the other.
  const other = CS.splitEntries(attr('aged demerara rum'));
  assert.strictEqual(S.matchesExclude(other, 'aged rum'), false);
  assert.strictEqual(S.matchesExclude(other, 'Demerara rum'), true);
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

// =============================================================================
// A CHIP IS NEVER AN "X or Y" — Helen, 2026-08-29
// =============================================================================
// "I don't want any returned search chips to be an X or Y shape. Also, 'wray and
// nephew' and 'wray & nephew' should both collapse onto the latter."
//
// Both are answered by the same change, and _data/cocktails/bottles.yml had
// already declared both answers -- the search simply never read it. HANDOVER
// §9.10.1 names the gap outright: "suggestions go in raw rather than resolved
// through bottles.yml's aliases, so `Havana 3` and `Havana Club 3` can both
// appear."
//
// THE RULES APPLY TO SUGGESTIONS ONLY, never to declared vocabulary. A generic
// is a name Helen chose; a suggestion is free text typed while transcribing.
// `ginger and lemongrass cordial` is a real generic and a blanket connector ban
// would have eaten it.

test('a bottle keeps ONE identity: an alias collapses onto the canonical name', () => {
  const pool = S.buildPool([attr('wray and nephew'), attr('wray & nephew')]);
  assert.deepStrictEqual(labels(pool), ['Wray & Nephew']);
});

test('the alias is still what FINDS it -- collapsing must not lose a way in', () => {
  const pool = S.buildPool([attr('wray and nephew')]);
  assert.deepStrictEqual(S.search('nephew', pool).results.map((r) => r.entry), ['Wray & Nephew']);
  assert.deepStrictEqual(S.search('ed3', S.buildPool([attr('ed3')])).results.map((r) => r.entry),
    ['El Dorado 3']);
});

test('a chip resolved to its canonical name still filters the drink that named the alias', () => {
  const drink = CS.splitEntries(attr('wray and nephew', 'lime juice'));
  assert.strictEqual(S.matchesInclude(drink, 'Wray & Nephew'), true);
  assert.strictEqual(S.matchesExclude(drink, 'Wray & Nephew'), true);
});

test('a suggestion the bottle file calls unresolved is not offered at all', () => {
  const pool = S.buildPool([attr('wray & nephew, or rum fire'), attr('ed3 or havana 3')]);
  assert.deepStrictEqual(labels(pool), []);
});

test('an "X or Y" suggestion is dropped even when nothing has declared it', () => {
  // bottles.yml is a RUM file, so the bitters and the syrups are not in it and
  // never will be. The shape is the rule, not the declaration.
  const pool = S.buildPool(pours('or other aromatic bitters', 'Or 20g palm sugar'));
  assert.deepStrictEqual(labels(pool), []);
});

test('the ban is on the CONNECTOR, not on the letters o-r', () => {
  const pool = S.buildPool(pours('orgeat', 'orange juice', 'cointreau'));
  assert.deepStrictEqual(labels(pool), ['cointreau', 'orange juice', 'orgeat']);
});

test('a declared generic is never dropped, whatever it happens to contain', () => {
  // `ginger and lemongrass cordial` is a real generic, which is why the ban is
  // on "or" and not on connectors generally.
  const pool = S.buildPool([attr('ginger and lemongrass cordial')]);
  assert.deepStrictEqual(labels(pool), ['ginger and lemongrass cordial']);
});

test('a declared generic is never resolved into a BOTTLE, and one really collides', () => {
  // `coconut rum` is a declared generic AND a declared alias of Malibu. The one
  // collision of the 173 declared names against the 97 bottle names and
  // aliases, measured -- and without the boundary it would silently put a brand
  // back into the picker, reversing #501's "no brand appears on a card any
  // more". A guard for exactly one case, and the case is real.
  const pool = S.buildPool([attr('coconut rum')]);
  assert.deepStrictEqual(labels(pool), ['coconut rum']);
  const drink = CS.splitEntries(attr('coconut rum'));
  assert.strictEqual(S.matchesInclude(drink, 'coconut rum'), true);
});

// =============================================================================
// A BOTTLE IS NOT OFFERED WHEN ITS CATEGORY IS — Helen, 2026-08-29
// =============================================================================
// On `falernum` and `john d taylor's velvet falernum` sitting side by side:
// "the first chip being 'falernum (all)' would at least stop me worrying that
// the two sets were disjoint."
//
// They are not disjoint, measured rather than argued: the bottle matches 1
// drink and the category 14, and the 1 is inside the 14. Across all 15
// bottle/category pairs in the collection 14 are strictly nested, and the
// exception is a data bug. So the two chips were never alternatives, and a
// picker that lays them out as though they were asks a question with no answer.

test('a bottle beside a category does not get its own chip', () => {
  const pool = S.buildPool([attr('falernum', "john d taylor's velvet falernum")]);
  assert.deepStrictEqual(labels(pool), ['falernum']);
});

test('but the bottle still FINDS the category -- the way in survives', () => {
  const pool = S.buildPool([attr('falernum', "john d taylor's velvet falernum")]);
  assert.deepStrictEqual(S.search('velvet', pool).results.map((r) => r.entry), ['falernum']);
  assert.deepStrictEqual(S.search('taylor', pool).results.map((r) => r.entry), ['falernum']);
});

test('a bottle with no category beside it is still offered', () => {
  // Nothing else in the group, so the bottle is all there is to name the pour.
  const pool = S.buildPool([attr('Rutte')]);
  assert.deepStrictEqual(labels(pool), ['Rutte']);
});

test('the category a bottle folds into is the one on ITS ingredient', () => {
  // Two pours. The bottle belongs to the first and must not attach to the
  // second, which is the pairing a card-level attribute has already lost.
  const pool = S.buildPool([attr('falernum', 'velvet falernum'), attr('lime juice')]);
  assert.deepStrictEqual(labels(pool), ['falernum', 'lime juice']);
  assert.deepStrictEqual(S.search('velvet', pool).results.map((r) => r.entry), ['falernum']);
});

// --- a hidden term cannot earn a chip on a substring alone -------------------
// Helen, 2026-08-29: "'el' returns both 'aged rum' and 'jamaican rum', which is
// counterintuitive." It is worse than counterintuitive -- it is unexplainable.
// Neither LABEL contains "el". The match was band 3, a mid-word substring,
// inside the hidden generics those chips stand for: "moderat(el)y aged rum" and
// "caram(el)-forward Jamaican rum".
//
// Band 3 means "in the list for some other reason", and a card can always show
// its reason. A chip cannot show a term it does not display, so a hidden alias
// may only earn its chip a place on a REAL match -- the query starting the
// entry, or starting a word in it. Substring reach belongs to the visible label
// alone.

test('a hidden generic does not surface its chip on a mid-word substring', () => {
  const pool = S.buildPool(pours('moderately aged rum', 'moderately aged jamaican rum'));
  assert.deepStrictEqual(S.search('el', pool).results.map((r) => r.entry), []);
});

test('but a hidden generic still surfaces its chip on a real word match', () => {
  const pool = S.buildPool([attr('moderately aged rum')]);
  assert.deepStrictEqual(S.search('moderately', pool).results.map((r) => r.entry), ['aged rum']);
  assert.deepStrictEqual(S.search('mod', pool).results.map((r) => r.entry), ['aged rum']);
});

test('a hidden bottle alias behaves the same way', () => {
  const pool = S.buildPool([attr('wray and nephew')]);
  assert.deepStrictEqual(S.search('nephew', pool).results.map((r) => r.entry), ['Wray & Nephew']);
  // "nd" sits mid-word inside the alias's "and" and nowhere in the label, which
  // spells that word "&". Nothing visible would explain the chip.
  assert.deepStrictEqual(S.search('nd', pool).results.map((r) => r.entry), []);
});

// --- four bands, and the order Helen gave -------------------------------------
// "It's surprising to me that 've' returns 'falernum' before any vermouth. I
// think here it should be prefix matching of first word, prefix matching of any
// word, then prefix matching of any word in the bottle name as is this one,
// then substring."
//
// Visible beats hidden at equal strength, and any real word beats a mere
// substring. Band 3 exists only because a bottle stopped being its own chip and
// became a way IN to its category -- a way in that was outranking the thing you
// had actually typed.

test('a visible name outranks a hidden one, however strong the hidden match', () => {
  const pool = S.buildPool([
    attr('sweet vermouth'),
    attr('falernum', "john d taylor's velvet falernum"),
    attr('vermouth')
  ]);
  assert.deepStrictEqual(
    S.search('ve', pool).results.map((r) => r.entry),
    ['vermouth', 'sweet vermouth', 'falernum']
  );
});

test('the four bands land in Helen\'s order', () => {
  const pool = S.buildPool([
    attr('vermouth'),                                   // 1: own name starts
    attr('sweet vermouth'),                             // 2: word in own name
    attr('falernum', 'velvet falernum'),                // 3: word in a hidden name
    attr('salve')                                       // 4: substring of own name
  ]);
  const got = S.search('ve', pool).results;
  assert.deepStrictEqual(got.map((r) => r.entry),
    ['vermouth', 'sweet vermouth', 'falernum', 'salve']);
  assert.deepStrictEqual(got.map((r) => r.band), [1, 2, 3, 4]);
});

test('a hidden word still beats a visible substring -- a real word is a real signal', () => {
  const pool = S.buildPool([attr('salve'), attr('falernum', 'velvet falernum')]);
  assert.deepStrictEqual(S.search('ve', pool).results.map((r) => r.entry), ['falernum', 'salve']);
});

test('the VISIBLE label keeps its substring reach, which is the last band doing its job', () => {
  // `galliano` for "li" is the case the three bands exist to rank, and it is
  // fine precisely because you can see the "li" in the button.
  const pool = S.buildPool([attr('galliano')]);
  assert.deepStrictEqual(S.search('li', pool).results.map((r) => r.entry), ['galliano']);
});

// --- prose is not a bottle name ----------------------------------------------
// Helen hit three of these one at a time -- the Havana disjunction, `Tesco
// Finest`, `Avallen -- a round, fresh taste if you need to sub` -- and then
// `Jack Daniels > Bulleit`. Patching them one by one is how the fourth arrives,
// so the shape is a rule, declared in _data/cocktails/ingredients.yml.
//
// MEASURED AGAINST ALL 87 REAL SUGGESTIONS BEFORE IT WAS TRUSTED: it flags 17
// and every one of them is genuinely prose, with no bottle name caught. The
// words that fired are the whole list; `the` and `that` were dropped from a
// first draft because a bottle can carry them ("The Botanist") and neither was
// doing any work.

test('an aside, a question mark, a comparison or a comma is not a bottle name', () => {
  const pool = S.buildPool(pours(
    'Avallen -- a round, fresh taste if you need to sub',
    'Dolin Rouge?',
    'Jack Daniels > Bulleit',
    'Patron Silver, Rooster Bianco'
  ));
  assert.deepStrictEqual(labels(pool), []);
});

test('a function word marks prose even with no punctuation in sight', () => {
  const pool = S.buildPool(pours('or other aromatic bitters', 'Best with ED3'));
  assert.deepStrictEqual(labels(pool), []);
});

test('a real bottle name survives every one of those tests', () => {
  // Straight from the collection, including the awkward ones: an ampersand, an
  // apostrophe, digits, an accent, a hyphen and a lowercase word.
  const real = ['Smith & Cross', "Gosling's Black Seal", 'El Dorado 3', 'Appleton 8-year',
    'La Favourite L\'Authentique Ambré', 'Pierre Ferrand ambre', 'acacia honey', 'Rutte'];
  const pool = S.buildPool(pours(...real));
  assert.deepStrictEqual(labels(pool).length, real.length);
});

test('with no bottle file the pool still works, and still refuses an X or Y', () => {
  // The page must survive the JSON block being absent -- same stance
  // filters.js takes on a missing #ingredient-vocabulary.
  const bare = CS.create(VOCAB);
  const pool = bare.buildPool(pours('wray and nephew', 'ed3 or havana 3', 'lime juice'));
  assert.deepStrictEqual(labels(pool), ['lime juice', 'wray and nephew']);
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
