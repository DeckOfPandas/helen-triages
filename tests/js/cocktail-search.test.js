// Tests for assets/js/cocktail-search.js: the cocktail index's pool building,
// candidate ranking, declared-family umbrellas and the two matching rules
// (#579, #549). A pure module, so no DOM is needed.
//
// Run from the repo root, with the local Node runtime:
//
//   .node-runtime/node/bin/node --test
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
    // `and` is absent on purpose: `Wray and Nephew` is one bottle.
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
    'overproof Demerara rum': 'rum',
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
  syrups: ['ginger and lemongrass cordial', 'cane sugar syrup 1:1', 'cane sugar syrup 2:1'],
  // `Jamaican, moderately aged` is the one declared term here that reads as
  // prose by the comma rule. No live term does, so without it viaKind's
  // declared-before-prose ordering is a branch no test reaches.
  cane_and_palm_spirits: ['coconut rum', 'moderately aged rum', 'Jamaican, moderately aged',
    'lightly aged and filtered rum'],
  liqueurs: ['falernum', 'apricot liqueur', 'cherry liqueur', 'gin liqueur'],
  juices: ['lime juice', 'lime', 'lime cordial'],
  card_names: {
    'London dry gin': 'gin',
    'aged Demerara rum': 'Demerara rum',
    'overproof Demerara rum': 'overproof Demerara rum',
    'moderately aged Jamaican rum': 'Jamaican rum',
    // Two generics under one card name (#501) puts the comma'd spelling above
    // behind a card name, which is how it reaches viaKind as a hidden
    // declared term.
    'Jamaican, moderately aged': 'Jamaican rum',
    'moderately aged rum': 'aged rum',
    'cane sugar syrup 1:1': 'sugar syrup',
    'cane sugar syrup 2:1': 'sugar syrup'
  }
};

// _data/cocktails/bottles.yml, trimmed to the keys this module reads. A bottle
// keeps ONE identity through its aliases; `unresolved_suggestions` is the file's
// own declared list of suggestion strings that are not a usable bottle name,
// each carrying its reason.
const BOTTLES = {
  bottles: {
    'Wray & Nephew': {
      generic: 'overproof Jamaican rum, unaged',
      aliases: ['Wray and Nephew', 'Wray & Nephew Overproof']
    },
    'El Dorado 3': { generic: 'lightly aged and filtered rum', aliases: ['ED3', 'El Dorado 3yo'] },
    // Kamaniwanalaya's two: an ingredient offering two generics, whose
    // bottles each name exactly one of them.
    'Appleton Estate 8 Year Reserve': {
      generic: 'moderately aged Jamaican rum',
      aliases: ['Appleton 8']
    },
    "Chairman's Reserve": { generic: 'moderately aged rum' },
    'Rum Fire': { generic: 'overproof Jamaican rum, unaged' },
    // `coconut rum` is a declared generic and also a declared alias of this
    // bottle. Resolving it would put a brand back into the picker (#501).
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

// Several unrelated ingredients, each its own group. buildPool takes one group
// per ingredient: two in one group says a bottle in it belongs to the other
// one's generic.
const pours = (...terms) => terms.map((t) => attr(t));

// The pool holds chips, { value, terms }. Most cases below only care what the
// buttons say.
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
  // The template downcases before writing the attribute, but a plain .sort()
  // puts every capital ahead of every lowercase letter, and the values
  // arriving lowercase is a fact about the template, not about this function.
  const pool = S.buildPool(pours('absinthe', 'Campari', 'lime juice'));
  assert.deepStrictEqual(labels(pool), ['absinthe', 'Campari', 'lime juice']);
});

// --- folding (#45) -------------------------------------------------------------
// Pool terms and drink names carry accents (crème de cassis, cachaça, Vieux
// Carré) and have to be reachable by typing ASCII.

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
// The ordering rule is orderByBand in assets/js/ingredient-search.js, shared
// with food. Each site computes its own two predicates, because they are
// answered in different vocabularies.

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

// --- no cap -------------------------------------------------------------------
// Every candidate is listed; there is no "+N more".

test('every candidate is offered, however many there are', () => {
  const many = [];
  // Two letters, not one: a bare "a" is a prose word, so `liqueur a` is not a
  // bottle name and the pool refuses it.
  for (let i = 0; i < 12; i++) many.push('liqueur x' + String.fromCharCode(97 + i));
  const pool = S.buildPool(pours(...many));
  const result = S.search('liq', pool);
  assert.strictEqual(result.results.length, 12);
  assert.strictEqual('hidden' in result, false,
    'a count of what was left out has nothing to count, and a caller that reads it is stale.');
});

// --- the minimum query length ------------------------------------------------
// #549. The number lives in _data/cocktails/ingredients.yml, not here and not
// in the DOM wiring.

test('a query shorter than the declared minimum offers nothing at all', () => {
  // Two ingredients, so two groups: a bottle in a group is read as a bottle
  // for that group's generic.
  const pool = S.buildPool([attr('gin'), attr('gin liqueur')]);
  assert.deepStrictEqual(S.search('g', pool).results, []);
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

// === Declared families: `family_of` in _data/cocktails/ingredients.yml =========
// The (all) buttons and exclusion are family-level operations (#322, #549).
// Food's family derivation is not reused: an (all) button there forms where
// entries share a head word, and `Old Tom` and `London dry gin` share none,
// which is why the family is declared here.

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

// --- a family answers to more than one name -----------------------------------
// `whiskey` and `scotch` reach the whisky family, which holds bourbon and rye.

test('an alias spelling reaches the family, whatever the button ends up called', () => {
  const pool = S.buildPool(pours('bourbon', 'rye'));
  ['whisky', 'whiskey', 'scotch'].forEach((typed) => {
    assert.strictEqual(S.search(typed, pool).familyButtons.length, 1, typed);
  });
});

test('an alias never mints a SECOND umbrella, which would lie about its width', () => {
  // A button labelled "scotch (all)" returning bourbon would misdescribe
  // itself, so one button appears and it carries the family's own label.
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
  // The chosen chips are drawn first, then the search's results, so family
  // buttons are filtered against what is already chosen, as candidates are.
  const pool = S.buildPool(pours('bourbon', 'rye'));
  assert.deepStrictEqual(S.search('whi', pool).familyButtons, ['whisk(e)y']);
  assert.deepStrictEqual(S.search('whi', pool, ['whisk(e)y (all)']).familyButtons, []);
});

test('choosing one family does not hide another', () => {
  const pool = S.buildPool(pours('bourbon', 'old tom'));
  assert.deepStrictEqual(S.search('gin', pool, ['whisk(e)y (all)']).familyButtons, ['gin']);
});

// --- the family's own display name -------------------------------------------
// A display label, not a rename of the family:
// test_a_declared_character_vocabulary_is_enforced keys `whisky_characters`
// off the family name. As with `card_names`, matching runs on the key and the
// button shows the name.

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

// === One chip per category, wearing the card's name ============================
// A generic and the card name that abbreviates it (`moderately aged rum`,
// `aged rum`) are one chip, never two buttons.

test('a generic with a card name is not offered twice', () => {
  // The rum's own group carries both spellings, as data-ing does; the lime is
  // a separate ingredient.
  const pool = S.buildPool([attr('moderately aged rum', 'aged rum'), attr('lime juice')]);
  assert.deepStrictEqual(labels(pool), ['aged rum', 'lime juice']);
});

test('the surviving chip wears the CARD name, so the picker and the card agree', () => {
  const pool = S.buildPool([attr('moderately aged rum')]);
  assert.deepStrictEqual(labels(pool), ['aged rum']);
});

test('the generic stays searchable -- collapsing a pair must not lose a way in', () => {
  // Typing the generic still finds the chip; it never appears as a second
  // button.
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
  // A ratio is a making fact, not a choosing fact (MANUAL §9.10.1): one
  // `sugar syrup` chip, not a 1:1 button and a 2:1 button.
  const pool = S.buildPool([attr('cane sugar syrup 1:1'), attr('cane sugar syrup 2:1')]);
  assert.deepStrictEqual(labels(pool), ['sugar syrup']);

  const oneToOne = CS.splitEntries(attr('cane sugar syrup 1:1'));
  const twoToOne = CS.splitEntries(attr('cane sugar syrup 2:1'));
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
  // `Demerara rum` is a card name for two different rum generics (#501), and
  // both are family `rum`.
  assert.deepStrictEqual(S.familiesOf('demerara rum'), ['rum']);
  assert.deepStrictEqual(S.familiesOf('london dry gin'), ['gin']);
});

test('an entry with no declared family has none -- lime juice is not a family', () => {
  assert.deepStrictEqual(S.familiesOf('lime juice'), []);
  assert.deepStrictEqual(S.familiesOf('havana 3'), []);
});

// === The two matching rules, deliberately different ============================
// Over-including shows a drink you may not want: visible, and you can see why
// it is there. Over-excluding hides a drink you would have had, and you never
// learn it existed. So: fuzzy to find, fuzzy to include, exact or declared
// family to exclude. A substring test against the joined attribute makes `gin`
// hide the ginger and `apple juice` match pineapple juice.

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
  // A substring test against "lime|gin|" sees "e|g", which spans two entries.
  // Nothing typed may see that seam.
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
  const entries = CS.splitEntries(attr('cane sugar syrup 2:1'));
  assert.strictEqual(S.matchesInclude(entries, 'sugar syrup'), true);
  assert.strictEqual(S.matchesInclude(entries, 'honey water'), false);
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

// === A chip is never an "X or Y" ===============================================
// _data/cocktails/bottles.yml declares both answers: an alias collapses onto
// the bottle's one name, and an unresolved suggestion is not offered.
//
// The rules apply to suggestions only, never to declared vocabulary. A generic
// is a name Helen chose; a suggestion is free text typed while transcribing.
// `ginger and lemongrass cordial` is a real generic, and a blanket connector
// ban would eat it.

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
  // The shape is the rule, not the declaration: nothing has to list the string.
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
  // `coconut rum` is a declared generic and a declared alias of Malibu.
  // Without the boundary it would put a brand back into the picker (#501).
  const pool = S.buildPool([attr('coconut rum')]);
  assert.deepStrictEqual(labels(pool), ['coconut rum']);
  const drink = CS.splitEntries(attr('coconut rum'));
  assert.strictEqual(S.matchesInclude(drink, 'coconut rum'), true);
});

// === A bottle is not offered when its category is ==============================
// A bottle's drinks are a subset of its category's, so the two chips are not
// alternatives: the bottle is a way in to the category's chip.

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
  // Two ingredients. The bottle belongs to the first and must not attach to
  // the second.
  const pool = S.buildPool([attr('falernum', 'velvet falernum'), attr('lime juice')]);
  assert.deepStrictEqual(labels(pool), ['falernum', 'lime juice']);
  assert.deepStrictEqual(S.search('velvet', pool).results.map((r) => r.entry), ['falernum']);
});

// --- a hidden term cannot earn a chip on a substring alone -------------------
// A chip cannot show a term it does not display, so a hidden generic or alias
// earns its chip a place only on a real match: the query starting the entry,
// or starting a word in it. "el" is mid-word in "moderately aged rum" and must
// not surface `aged rum`. Substring reach belongs to the visible label alone.

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

// --- four bands ----------------------------------------------------------------
// The chip's own name starts with the query; a word in its own name does; a
// word in a hidden name does; a substring of its own name. Visible beats
// hidden at equal strength, and any real word beats a mere substring.

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
  // `galliano` for "li" is fine because you can see the "li" in the button.
  const pool = S.buildPool([attr('galliano')]);
  assert.deepStrictEqual(S.search('li', pool).results.map((r) => r.entry), ['galliano']);
});

// --- prose is not a bottle name ----------------------------------------------
// The shape is a rule, declared in _data/cocktails/ingredients.yml as
// `prose_words` and `prose_marks`. `the` and `that` are not prose words: a
// bottle can carry them ("The Botanist").

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
    'La Favorite L\'Authentique Ambré', 'Pierre Ferrand ambre', 'acacia honey', 'Rutte'];
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
// I KNOW WHAT I WANT is substring, not word-start: a drink name is a thing you
// already hold and are part-way through typing, so "negr" finds the Negroni.
// It folds, so an accented name is typeable.

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
// #564: the card must be able to say WHY it survived, which MANUAL §9.13
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

// --- why a chip is on screen: `via` and `viaKind` (#603) -----------------------
// A band-3 match is on a name the chip does not display. `via` is the term
// that won and `viaKind` the kind of name it was (`own`, `bottle`, `generic`),
// so the picker does not have to guess.

test('a chip matched on its own name says so, on every visible band', () => {
  const pool = S.buildPool(pours('lime juice', 'apricot liqueur'));
  const bands = {};
  S.search('li', pool, []).results.forEach((r) => { bands[r.entry] = r; });

  // Band 1: the chip's own name starts with the query.
  assert.strictEqual(bands['lime juice'].band, 1);
  assert.strictEqual(bands['lime juice'].via, 'lime juice');
  assert.strictEqual(bands['lime juice'].viaKind, 'own');

  // Band 2: a word inside the chip's own name. Still its own name.
  assert.strictEqual(bands['apricot liqueur'].band, 2);
  assert.strictEqual(bands['apricot liqueur'].viaKind, 'own');

  // Band 4: a bare substring of the chip's own name -- li-QUE-ur starts no
  // word at all -- and still its own name, which is the point here.
  const [substring] = S.search('que', pool, []).results;
  assert.strictEqual(substring.entry, 'apricot liqueur');
  assert.strictEqual(substring.band, 4);
  assert.strictEqual(substring.viaKind, 'own');
});

test('a chip found through a BOTTLE names the bottle -- the case band 3 exists for', () => {
  const pool = S.buildPool(pours(attr('moderately aged rum', 'aged rum', 'appleton 12')));
  const [hit] = S.search('appleton', pool, []).results;

  assert.strictEqual(hit.entry, 'aged rum');
  assert.strictEqual(hit.band, 3);
  assert.strictEqual(hit.via, 'appleton 12');
  assert.strictEqual(hit.viaKind, 'bottle');
});

// --- an umbrella suppresses its own bare word (#51) ----------------------------
// `gin (all)` beside `gin` makes a reader check both.

test('an (all) button takes the bare chip of the same name off the list', () => {
  const pool = S.buildPool(pours('gin', 'sloe gin', 'Old Tom'));
  const found = S.search('gin', pool, []);

  assert.deepStrictEqual(found.familyButtons, ['gin']);
  assert.strictEqual(
    found.results.some((r) => r.entry === 'gin'), false,
    'the bare `gin` chip is still offered beside `gin (all)`, which is the pair ' +
    'that makes a reader check both.'
  );
});

test('it takes ONLY the bare name -- a real multi-word chip is untouched', () => {
  const pool = S.buildPool(pours('gin', 'sloe gin', 'Old Tom'));
  const offered = S.search('gin', pool, []).results.map((r) => r.entry);

  assert.ok(offered.indexOf('sloe gin') !== -1, 'sloe gin should survive');
  assert.deepStrictEqual(offered.indexOf('gin'), -1);
});

test('with no umbrella offered, the bare chip is offered as usual', () => {
  // The suppression is a fact about the PAIR, not about the word: below the
  // family-button threshold there is no umbrella and nothing to be confused
  // with, so the chip is the answer.
  const pool = S.buildPool(pours('gin', 'sloe gin'));
  const found = S.search('gi', pool, []);

  assert.deepStrictEqual(found.familyButtons, []);
  assert.ok(found.results.some((r) => r.entry === 'gin'));
});

test('a bare word its umbrella suppresses is not offered beside it', () => {
  const pool = S.buildPool(pours('gin', 'sloe gin', 'Old Tom'));
  const found = S.search('gin', pool, []);
  assert.strictEqual(found.results.some((r) => r.entry === 'gin'), false);
  assert.ok(found.results.some((r) => r.entry === 'sloe gin'));
});

test('a multi-word query matches a hidden name from its start', () => {
  // `hasWordMatch` asks whether one word begins with the whole query, so it
  // is never true of a query containing a space. A multi-word query matches a
  // hidden name from its start instead.
  const pool = S.buildPool(pours(attr('lightly aged and filtered rum', 'el dorado 3')));

  ['el d', 'el dorado', 'el dorado 3'].forEach((q) => {
    const [hit] = S.search(q, pool, []).results;
    assert.ok(hit, `"${q}" found nothing`);
    assert.strictEqual(hit.entry, 'lightly aged and filtered rum');
    assert.strictEqual(hit.band, 3);
  });
});

test('a multi-word query still may not begin mid-word, or on a connector', () => {
  // "orado" is inside El Dorado and starts no word of it.
  const dorado = S.buildPool(pours(attr('lightly aged and filtered rum', 'el dorado 3')));
  assert.deepStrictEqual(S.search('orado', dorado, []).results, []);
  // A whole-string prefix is a prefix, not a substring: "dorado 3" appears in
  // "el dorado 3" and does not start it.
  assert.deepStrictEqual(S.search('dorado 3', dorado, []).results, []);

  /* The connector rule refuses a hidden match only when the matched word is
     itself in the prose list, and `and` is deliberately absent from that list
     (`Wray and Nephew` is one bottle). So "and" is a band-3 hit, and the
     bracket shows the spelling carrying the query. */
  const wray = S.buildPool(pours(
    attr('moderately aged jamaican rum', 'jamaican rum', 'Wray and Nephew')));
  const [connector] = S.search('and', wray, []).results;
  assert.strictEqual(connector.band, 3);
  assert.strictEqual(connector.via, 'Wray and Nephew');

  // What the rule DOES refuse: the matched word is a prose word in its own
  // right. `with` heads nothing and means nothing on a bottle.
  const prose = S.buildPool(pours(attr('falernum', 'Something with Spice')));
  assert.deepStrictEqual(S.search('with', prose, []).results, []);
});

test('the bracket shows the spelling that carries the query, not always the canonical', () => {
  // `Wray and Nephew` is an alias of the bottle `Wray & Nephew`. Typing "and"
  // matches the alias, and the canonical name has not one letter of the query
  // in it, so the bracket shows the alias as written. The canonical name is
  // shown wherever it carries the query (#603).
  const pool = S.buildPool(pours(
    attr('moderately aged jamaican rum', 'jamaican rum', 'Wray and Nephew')));

  assert.strictEqual(S.search('and', pool, []).results[0].via, 'Wray and Nephew');
  assert.strictEqual(S.search('wray', pool, []).results[0].via, 'Wray & Nephew');
});

test('a chip found through the GENERIC its card name abbreviates says which', () => {
  // The "mu" case in miniature: the card name is what the chip shows, so the
  // words the generic carries are invisible on the very button they matched.
  const pool = S.buildPool(pours(attr('moderately aged rum', 'aged rum')));
  const [hit] = S.search('moderat', pool, []).results;

  assert.strictEqual(hit.entry, 'aged rum');
  assert.strictEqual(hit.band, 3);
  assert.strictEqual(hit.via, 'moderately aged rum');
  assert.strictEqual(hit.viaKind, 'generic');
});

test('PROSE beside a generic is not searchable at all, so it can explain nothing', () => {
  // "Wray & Nephew, or Rum Fire" is two bottles in one string, listed in
  // bottles.yml's `unresolved_suggestions`. It is not a chip (#585) and must
  // not be searchable either, or "wray" reaches a category through it and
  // #603's bracket prints it as the reason.
  const pool = S.buildPool(pours(
    attr('moderately aged jamaican rum', 'jamaican rum', 'wray & nephew, or rum fire')));

  assert.deepStrictEqual(S.search('wray', pool, []).results, []);
  // The chip itself is untouched -- only the way in through prose has gone.
  assert.strictEqual(S.search('jamaic', pool, []).results[0].entry, 'Jamaican rum');
});

test('a DECLARED name that reads as prose is still searchable', () => {
  // resolveHiddenTerm asks "is this declared?" before "is this prose?": a
  // generic dropped as prose takes a real chip's own search term with it. No
  // live term needs it, so the fixture pins it with a comma'd spelling.
  const pool = S.buildPool(pours(attr('jamaican, moderately aged', 'jamaican rum')));
  const [hit] = S.search('moderat', pool, []).results;

  assert.strictEqual(hit.band, 3);
  assert.strictEqual(hit.viaKind, 'generic');
});

test('a bottle belongs to the option it names, not to every option on the pour', () => {
  // Kamaniwanalaya's shape. Chairman's Reserve is declared `moderately aged
  // rum` and nothing else, so "chairman" offers that category only. A
  // disjunctive generic means "either would do" (#441), not either bottle.
  const pool = S.buildPool(pours(attr(
    'moderately aged jamaican rum', 'jamaican rum',
    'moderately aged rum', 'aged rum',
    'appleton 8', "chairman's reserve")));

  const jamaican = S.search('appleton', pool, []).results;
  assert.deepStrictEqual(jamaican.map((r) => r.entry), ['Jamaican rum']);
  assert.strictEqual(jamaican[0].via, 'Appleton Estate 8 Year Reserve');

  const aged = S.search('chairman', pool, []).results;
  assert.deepStrictEqual(aged.map((r) => r.entry), ['aged rum']);
});

test('a bottle from ANOTHER category still reaches a pour offering only one', () => {
  // #534's case, and the one the rule above must not break: a cherry brandy
  // may suggest Cherry Heering, which is a liqueur, on purpose and with a
  // note. Nothing on that pour contradicts it, so nothing may filter it out.
  const pool = S.buildPool(pours(attr('falernum', "chairman's reserve")));
  const [hit] = S.search('chairman', pool, []).results;

  assert.strictEqual(hit.entry, 'falernum');
  assert.strictEqual(hit.viaKind, 'bottle');
});

test('an alias keeps finding its bottle, and the bracket prints the real name', () => {
  // ED3 contains not one letter of "El Dorado 3", so both spellings stay
  // searchable.
  const pool = S.buildPool(pours(attr('lightly aged and filtered rum', 'ed3')));

  const short = S.search('ed3', pool, []).results[0];
  const long = S.search('dorado', pool, []).results[0];

  assert.strictEqual(short.entry, 'lightly aged and filtered rum');
  // "El Dorado 3" cannot explain a search for "ed3" -- it shares no letters
  // with it -- so the bracket shows the alias that does. The canonical name is
  // right whenever it carries the query, which is the far commoner case.
  assert.strictEqual(short.via, 'ED3');
  assert.strictEqual(long.via, 'El Dorado 3');
});

test('the winning band decides which term is reported, not the first one seen', () => {
  // One chip reachable two ways at once: `falernum` shows its own name AND
  // hides the bottle. "falernum" must report the visible match, because that is
  // the one that won -- annotating it with the bottle would be explaining a
  // chip that needs no explanation.
  //
  // Not `gin`: a family name's bare chip is suppressed by its umbrella (#51).
  const pool = S.buildPool(pours(attr('falernum', "john d taylor's velvet falernum")));
  const [hit] = S.search('falernum', pool, []).results;

  assert.strictEqual(hit.band, 1);
  assert.strictEqual(hit.via, 'falernum');
  assert.strictEqual(hit.viaKind, 'own');
});
