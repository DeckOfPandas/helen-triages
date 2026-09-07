// =============================================================================
// SHOPPING LIST — what a shortlist of drinks adds up to. No DOM.
// =============================================================================
// GitHub issue #546's stretch goal, asked for directly on 2026-09-04: "each
// ingredient (bottle selection if I have one, generic if not) and its amount in
// total if I were to make 1 glass of each of those drinks", plus a scaler.
//
// Pure, and loaded the two ways filter-state.js is: as a plain <script> that
// attaches to window.HTF, and via require() for tests/js/shopping-list.test.js.
// The DOM half is cocktail-index.js, exactly as filters.js is filter-state.js's.
//
// -----------------------------------------------------------------------------
// THE GROUPING KEY IS THE GENERIC, AND THAT IS A DEPARTURE WORTH STATING
// -----------------------------------------------------------------------------
// Read literally, "bottle if I have one, generic if not" makes the BOTTLE the
// identity, and that produces a list you cannot shop from. Measured against the
// real 124 drinks before this was written (tmp/survey_identity.py, scratch):
// of 156 distinct generics, 41 appear both with a bottle named and without, and
// 20 carry more than one distinct bottle. `London dry gin` alone appears bare
// and as Beefeater, Portobello, Rutte, Tanqueray, and "Hayman's or Beefeater or
// Tanqueray". A three-gin shortlist would print three lines and three totals for
// one bottle you have to buy.
//
// The data is also noisy in ways only a grouping key notices: `Woodford's
// Reserve` and `Woodford’s Reserve` differ by an apostrophe, `Dolin Dry` and
// `Dolin dry` by a capital, and El Dorado 3 is written five ways.
//
// So the GROUP is the generic — the thing there is one of in a cupboard.
//
// THE GENERIC ALWAYS LEADS, AND THE BOTTLES FOLLOW IN BRACKETS — Helen,
// 2026-09-04, settling it after seeing the first version: "show generic first,
// with bottle on the same line in brackets, like the recipes." That is the drink
// page's own shape (`.cocktail-item-name` then `.cocktail-suggestion` in
// parentheses, _layouts/cocktail.html), so a line reads the same way in both
// places. The earlier rule — bottle leading whenever a group was unanimous —
// made a list whose left column changed KIND from row to row, which is exactly
// what a shopping list scanned down its edge cannot afford.
//
// The generic is the one a drink WROTE, never the shortened name a card shows:
// `card_names` exists to fit "moderately aged Jamaican rum" onto a 370px card
// (#501) and nothing in this file reads it. Helen, same message: "give the long
// rum names, not the shortened ones we generated for cards."
//
// -----------------------------------------------------------------------------
// AMOUNTS
// -----------------------------------------------------------------------------
// Surveyed rather than assumed. All 682 entries carry an amount; 568 are `N ml`
// and every number in the collection is a plain decimal — no fractions, no
// ranges. The rest are dashes, drops, cubes, pinches, leaves, a sprig, a strip,
// grams, bare counts, and eleven that are not quantities at all: `to top` (9)
// and `to rinse` (2).
//
// TOTALS ARE PER UNIT, NEVER CONVERTED. A group holding 45 ml and 2 dashes is
// "45 ml + 2 dashes", because 2 dashes of Angostura is not some number of
// millilitres anyone should be told by this file. Merging units would be
// inventing a conversion the source never made.
//
// AN UNQUANTIFIED ENTRY IS COUNTED, NOT SUMMED. `to top` scales with the number
// of drinks and not with a volume, so it reports as "to top (x3)" — three
// drinks want topping — and multiplying by the scaler multiplies the drinks,
// which is the only honest reading.
// =============================================================================

(function (root) {
  'use strict';

  /* `water` IS EXCLUDED, and the list of what to exclude is NOT this file's.
     _data/cocktails/ingredients.yml declares `not_on_cards: ['water']` and the
     index template already honours it when drawing a card's ingredient line.
     Passing it in rather than restating it here is what stops the shopping list
     and the cards from ever disagreeing about what an ingredient is. */

  /** Anything YAML gave us as scalar-or-list-or-nothing, as a list. */
  function asList(value) {
    if (value === null || value === undefined || value === '') return [];
    return Array.isArray(value) ? value : [value];
  }

  /* THE JOIN IS " or " BECAUSE THAT IS WHAT A LIST MEANS HERE — issue #441, and
     the index template's own wording. A generic written as a list is "either
     would do", not two ingredients, so it is one line on a shopping list and
     one key in this map. */
  function joined(value) {
    return asList(value).map(function (v) { return String(v).trim(); })
      .filter(Boolean).join(' or ');
  }

  /* THE KEY, NOT THE LABEL. Case and the two apostrophes are the noise the
     survey found, and they must not split a group; the LABEL is always built
     from a real entry's own text, so nothing here is ever shown to anybody.
     U+2019 folds to U+0027 rather than the other way round because either is
     arbitrary and one of them has to win. */
  function foldKey(text) {
    return String(text || '')
      .replace(/’/g, "'")
      .trim()
      .toLowerCase()
      .replace(/\s+/g, ' ');
  }

  /* UNITS ARE FOLDED TO THEIR SINGULAR, so `dash` and `dashes` are one total
     rather than two lines of the same bitters. Only the plurals the collection
     actually contains are handled -- `dashes`, `drops`, `cubes`, `leaves` --
     plus a general trailing `s` for anything that appears later, which is safe
     because a unit that does not end in `s` is untouched and one that does is
     already the plural of the one before it.

     The empty unit is a bare count (`1` orange wedge) and stays empty: it has
     no name, and giving it one would be inventing a word for it. */
  var UNIT_PLURALS = { dashes: 'dash', drops: 'drop', cubes: 'cube', leaves: 'leaf' };

  /* THE LAST WORD CARRIES THE NUMBER, and that is what makes a compound unit
     work. Food writes `2 heaped tbsp`, `1 large head`, `2 x 400 g cans` and
     `1 small stick (8 g)`; the noun being counted is always the last word, and
     the words in front of it are adjectives that never change. Splitting here
     rather than special-casing each phrase is what keeps `dash` -> `dashes`
     (every cocktail unit is one word, so the last word IS the word) working
     unchanged while `x 400 g can` -> `x 400 g cans` starts working at all.

     A PARENTHETICAL IS NOT A WORD. `tbsp (8 g)` counts `tbsp` -- the bracket
     restates the same quantity in grams and is handled by splitParenthetical
     below, which the food shopping list calls before it ever gets here. */
  function lastWord(unit) {
    var parts = String(unit).split(' ');
    return parts[parts.length - 1];
  }

  function replaceLastWord(unit, word) {
    var parts = String(unit).split(' ');
    parts[parts.length - 1] = word;
    return parts.join(' ');
  }

  /* A PLURAL UNIT IS FOLDED TO ITS SINGULAR so that two recipes writing
     `1 clove` and `3 cloves` of garlic total onto one line rather than two.
     The declared map above is checked first, for the four irregulars the
     cocktails collection contains; everything else follows the ordinary
     English rule read backwards -- `bunches` -> `bunch`, `cloves` -> `clove`,
     `handfuls` -> `handful`.

     `ss` IS NEVER A PLURAL (`glass`), and neither is a two-letter symbol that
     happens to end in one. Both are left alone, and `unitLabel` puts whatever
     this removed back for display, so a unit that round-trips wrongly here
     shows wrongly on the page rather than silently splitting a total -- which
     is the failure that is at least visible. */
  function foldUnit(unit) {
    var u = String(unit || '').trim().toLowerCase().replace(/\s+/g, ' ');
    if (UNIT_PLURALS[u]) return UNIT_PLURALS[u];

    var word = lastWord(u);
    if (UNIT_PLURALS[word]) return replaceLastWord(u, UNIT_PLURALS[word]);
    if (SYMBOL_UNITS[word] || word.length < 3) return u;
    if (/(ch|sh|s|x|z)es$/.test(word)) return replaceLastWord(u, word.slice(0, -2));
    if (/[^s]s$/.test(word)) return replaceLastWord(u, word.slice(0, -1));
    return u;
  }

  /* The plural again, for display, and derived rather than stored: a total is
     only pluralised when it is not exactly one, and `ml`/`g` are never
     pluralised at all because they are symbols rather than words.

     `each` JOINED THEM ON 2026-09-04. It is a word rather than a symbol, but it
     is one that has no plural, and the sibilant rule below turns it into
     `eaches` -- `9 each` cucumber wheels doubled printed `18 eaches`. Three
     drinks are written with it (east river underground, la fee noir punch, porn
     star martini), and the drink page's scaler (#545) multiplies exactly these
     strings, so the wart showed up on a page rather than only in a total.

     THE FOOD UNITS JOINED THEM FOR #801, and every one is here for the same
     reason the originals were: `2 tbsps` and `8 mediums` are not English.
     `tsp`, `tbsp`, `kg`, `cm` and `mm` are symbols like `ml`; `large`, `small`
     and `medium` are adjectives standing in for a noun nobody writes ("4
     medium bay leaves"), so they have no plural either. Words that DO
     pluralise -- `litre`, `clove`, `bunch`, `slice`, `sprig` -- are
     deliberately absent, because the rule below gets those right. */
  var SYMBOL_UNITS = {
    ml: true, g: true, cl: true, l: true, oz: true, each: true, '': true,
    kg: true, tsp: true, tbsp: true, cm: true, mm: true,
    large: true, small: true, medium: true
  };

  function unitLabel(unit, quantity) {
    if (SYMBOL_UNITS[unit]) return unit;
    if (quantity === 1) return unit;

    /* THE LAST WORD AGAIN, and it must agree with foldUnit or a unit will not
       survive the round trip: `x 400 g can` has to print as `x 400 g cans`,
       and `heaped tbsp` has to print unchanged because `tbsp` is a symbol. */
    var word = lastWord(unit);
    if (SYMBOL_UNITS[word]) return unit;

    // `leaf` -> `leaves`, the one unit here that does not take a suffix.
    if (/f$/.test(word)) return replaceLastWord(unit, word.replace(/f$/, 'ves'));
    if (word !== unit) return replaceLastWord(unit, pluralise(word));

    /* A SIBILANT TAKES `es`, EVERYTHING ELSE TAKES `s` -- pluralise() above.
       Written as a rule rather than a list, because a list is what got this
       wrong: `dash` and `pinch` are the two the collection contains, `pinch`
       had a line of its own and `dash` fell through to the default and printed
       `2 dashs` -- in the single most common non-millilitre unit in the data
       (45 entries). The rule covers both, and whichever sibilant unit is
       written next. */
    return pluralise(unit);
  }

  /* HOW MANY WHOLE FRUITS, IN WORDS -- Helen, 2026-09-04: `amount: "half"` on
     caipirinha's lime, with `half` and `whole` added to `measures:`.

     "0.5 whole" IS THE THING THIS EXISTS TO PREVENT. Nobody halves a lime by
     writing 0.5 of one, and `unitLabel` would go further and print "0.5 wholes".
     So a count in this unit prints as Helen writes it: `half`, `1 whole`,
     `1½ whole`, `2 whole` -- and `quarter` and `¾ whole`, because ×0.5 of half a
     lime is a real thing this control can produce and a decimal there would be
     the same wart one line further down.

     ANYTHING THE FRACTIONS DO NOT COVER FALLS BACK TO THE NUMBER, rather than
     being rounded to one that reads nicely: a third of a lime is not a half. */
  var FRACTIONS = { 0.25: '¼', 0.5: '½', 0.75: '¾' };

  function wholeText(quantity) {
    var n = tidy(Number(quantity));
    if (n === 0.5) return 'half';
    if (n === 0.25) return 'quarter';

    var whole = Math.floor(n);
    var fraction = FRACTIONS[tidy(n - whole)];
    var number = fraction
      ? (whole ? whole + fraction : fraction)
      : String(n);
    return number + ' whole';
  }

  /* THE NUMBER, WRITTEN THE WAY A COOK WRITES IT -- #801. `⅔ tsp` rather than
     `0.667 tsp`, and `1½ tbsp` rather than `1.5 tbsp`.

     THIS IS NOTATION AND NOT ROUNDING, which is the distinction Helen drew on
     2026-09-07 when she was asked whether the food scaler should tidy its
     output: "don't round to 10 g or 5 g, round to 1 g". So ⅔ is printed for
     exactly two thirds and never for 0.7, and a number that is not one of
     these fractions prints as a decimal rather than being nudged onto one that
     reads more nicely. The tolerance is there for floating point -- 2/3 of 1
     is 0.6666666666666666, and that IS two thirds -- and is far tighter than
     any difference a spoon could show.

     `wholeText` above stays as it is. It answers a different question (how
     many whole limes, in Helen's own words `half` and `quarter`) and #545's
     scaler prints its answers on a drink page. */
  var COOKS_FRACTIONS = [
    [1 / 8, '⅛'], [1 / 4, '¼'], [1 / 3, '⅓'], [3 / 8, '⅜'], [1 / 2, '½'],
    [5 / 8, '⅝'], [2 / 3, '⅔'], [3 / 4, '¾'], [7 / 8, '⅞']
  ];

  function fractionText(quantity, places) {
    var n = Number(quantity);
    if (!isFinite(n)) return String(quantity);

    var whole = Math.floor(n + 1e-9);
    var rest = n - whole;

    for (var i = 0; i < COOKS_FRACTIONS.length; i += 1) {
      if (Math.abs(rest - COOKS_FRACTIONS[i][0]) < 1e-6) {
        return (whole ? String(whole) : '') + COOKS_FRACTIONS[i][1];
      }
    }
    if (rest < 1e-6) return String(whole);

    var factor = Math.pow(10, typeof places === 'number' ? places : 2);
    return String(Math.round(n * factor) / factor);
  }

  /** One quantity and its unit, as a line of the list prints them. */
  function amountText(quantity, unit) {
    if (unit === 'whole') return wholeText(quantity);
    var shown = unitLabel(unit, quantity);
    return shown ? quantity + ' ' + shown : String(quantity);
  }

  /* VULGAR FRACTIONS ARE NUMBERS, and food writes a great many of them --
     `½ tsp`, `¼–½ tsp`, `1½ tbsp`, `1¾ cups`, `⅛ tsp`. Every one of these
     returned null before #801 and was counted as an unquantified phrase, so
     "½ tsp salt" and "¼ tsp salt" appeared as two lines saying `(×1)` instead
     of adding up to ¾ tsp.

     NOT ONE OF THEM APPEARS IN THE COCKTAILS COLLECTION -- 682 pours, every
     number a plain decimal on the 2.5 ml grid (see AMOUNTS above) -- so this
     widens what parses without changing a single existing answer, which is
     what lets one parser serve both sites. tests/js/shopping-list.test.js
     holds that claim. */
  var VULGAR = {
    '½': 0.5, '⅓': 1 / 3, '⅔': 2 / 3, '¼': 0.25, '¾': 0.75,
    '⅕': 0.2, '⅖': 0.4, '⅗': 0.6, '⅘': 0.8,
    '⅙': 1 / 6, '⅚': 5 / 6, '⅐': 1 / 7, '⅛': 0.125, '⅜': 0.375,
    '⅝': 0.625, '⅞': 0.875, '⅑': 1 / 9, '⅒': 0.1
  };

  var VULGAR_CLASS = '[½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅐⅛⅜⅝⅞⅑⅒]';

  /* A NUMBER IS DIGITS, A FRACTION, OR DIGITS FOLLOWED BY A FRACTION. `1½` is
     one token and not two, which is the whole reason this is built up from
     pieces rather than written as one regex with a `\d+` in it.

     THE LOOKAHEAD IS LOAD-BEARING, and it is what stops both halves being
     optional from meaning "matches nothing, successfully". Without it the
     range branch below happily matches a bare separator followed by no number
     at all, and `2.5-cm piece` loses its hyphen to a range that is not there.
     With it, a separator that is really part of a unit is simply not a
     separator. */
  var NUMBER = '(?=\\d|' + VULGAR_CLASS + ')(\\d+(?:\\.\\d+)?)?(' + VULGAR_CLASS + ')?';

  /* THE RANGE SEPARATOR IS AN EN DASH, A HYPHEN OR THE WORD `to`, and it only
     counts as one when a NUMBER follows it. That is not fussiness: `2.5-cm
     piece` and `2 x 400-g tins` both carry a hyphen that is part of the unit,
     and both would lose their unit to a looser rule. */
  var AMOUNT = new RegExp(
    '^\\s*(~)?\\s*' + NUMBER +
    '(?:\\s*(?:–|—|-|\\s+to)\\s*' + NUMBER + ')?' +
    '\\s*(.*?)\\s*$'
  );

  function numberFrom(digits, fraction) {
    if (digits === undefined && fraction === undefined) return null;
    var n = 0;
    if (digits !== undefined && digits !== '') n += parseFloat(digits);
    if (fraction) n += VULGAR[fraction];
    return isFinite(n) ? n : null;
  }

  /**
   * Split "22.5 ml" into a number and a unit.
   *
   * Returns null when the string is not a quantity at all -- `to top`, `to
   * rinse`, `some` -- which is a real answer rather than a failure, and the
   * caller counts those entries instead of summing them.
   *
   * `max` and `approx` are present only when the source said so: "30–50 g"
   * gives {quantity: 30, max: 50}, "~2 tbsp" gives {approx: true}. A reader
   * that ignores both fields gets the low end and no tilde, which is why
   * adding them broke nothing that already read this.
   *
   * @param {string} amount
   * @returns {{quantity: number, unit: string, max?: number,
   *            approx?: boolean}|null}
   */
  function parseAmount(amount) {
    /* `half` IS A NUMBER WITH NO DIGITS IN IT -- Helen, 2026-09-04, ruling on
       caipirinha's lime: `amount: "half"`, with `half` and `whole` declared as
       units in `measures.non_volumetric`. A whole fruit is COUNTED, never
       measured, so it has no millilitre figure and does not want one.

       IT READS AS 0.5 OF A `whole` so that the arithmetic is ordinary: half a
       lime doubled is one lime, tripled is one and a half, and neither the
       scaler nor the shopping list needs a rule of its own to say so. Only the
       PRINTING is special -- `wholeText` below. */
    if (String(amount || '').trim().toLowerCase() === 'half') {
      return { quantity: 0.5, unit: 'whole' };
    }

    var match = AMOUNT.exec(String(amount || ''));
    if (!match) return null;

    var quantity = numberFrom(match[2], match[3]);
    if (quantity === null) return null;

    var parsed = { quantity: quantity, unit: foldUnit(match[6]) };

    var max = numberFrom(match[4], match[5]);
    /* A RANGE THAT RUNS BACKWARDS IS NOT A RANGE. Nothing in either collection
       writes one, and treating "5–2" as a range would have the totals for the
       two ends cross over; dropping the second number leaves the first, which
       is the same answer this function has always given for text it cannot
       read past. */
    if (max !== null && max > quantity) parsed.max = max;

    if (match[1]) parsed.approx = true;
    return parsed;
  }

  /* THE BRACKET THAT RESTATES THE SAME QUANTITY -- `1 tbsp (6 g)` of whole
     cloves, `4 medium (1 g)` of bay leaves, `1 tbsp (9–10 g)` of peppercorns.
     Two of Helen's spice-blend recipes are written this way throughout, and it
     is a genuinely useful thing to have written down: the tablespoon is how
     you measure it and the gram is how you check it.

     IT HAS TO COME OFF THE UNIT BEFORE ANYTHING ELSE HAPPENS, for two reasons.
     Grouping: `tbsp (6 g)` and `tbsp (12 g)` are the same unit written twice,
     and left alone they make two totals of one spice. Scaling: the bracket is
     the same quantity as the number in front of it, so doubling one without
     the other prints a contradiction.

     RETURNED, NOT APPLIED. This says what the bracket is; the food shopping
     list decides what to do with it, and cocktails -- which has no brackets in
     any of its 682 amounts -- never calls it. That is why the change to
     parseAmount above could be additive and this could not.

     @param {string} unit
     @returns {{unit: string, lo: number, hi: number|null, unit2: string}|
               {unit: string}} */
  var PARENTHETICAL = new RegExp(
    '^(.*?)\\s*\\(\\s*' + NUMBER +
    '(?:\\s*(?:–|—|-)\\s*' + NUMBER + ')?' +
    '\\s*([^)]*?)\\s*\\)\\s*$'
  );

  function splitParenthetical(unit) {
    var match = PARENTHETICAL.exec(String(unit || ''));
    if (!match) return { unit: String(unit || '') };

    var lo = numberFrom(match[2], match[3]);
    if (lo === null) return { unit: String(unit || '') };
    var hi = numberFrom(match[4], match[5]);

    return {
      unit: match[1],
      lo: lo,
      hi: hi !== null && hi > lo ? hi : null,
      unit2: foldUnit(match[6])
    };
  }

  /* HOW MANY WHOLE FRUITS A VOLUME OF JUICE COMES TO — #546, Helen 2026-09-04:
     "Please give the range of whole fruits needed, like this '375 ml lemon juice
     (X to Y lemons)'."

     THE YIELDS ARE DATA, in _data/cocktails/ingredients.yml under `juice_yields`,
     and are passed in. Only four juices have them, and only the four you squeeze
     yourself: pineapple, cranberry and apple arrive in a carton, so "how many
     whole fruits" is not a question anyone is asking in the shop.

     THE DIVISION RUNS THE OTHER WAY ROUND FROM THE INSTINCT, which is the one
     thing here worth getting wrong slowly rather than quickly: the FEWEST fruits
     is the total over the LARGEST yield. More juice per lemon means fewer
     lemons. Both ends round UP, because three quarters of a lemon is a lemon you
     had to buy.

     A RANGE THAT COLLAPSES IS PRINTED ONCE. 60 ml of lime is 2 to 3 limes; 20 ml
     is 1 to 1, and "1 to 1 limes" is a worse sentence than "1 lime". */
  function pluralise(word) {
    if (/(s|sh|ch|x|z)$/.test(word)) return word + 'es';
    return word + 's';
  }

  function fruitCount(ml, yields) {
    if (!yields || !(ml > 0)) return null;

    var low = Number(yields.ml_min);
    var high = Number(yields.ml_max);
    var fruit = String(yields.fruit || '').trim();
    if (!fruit || !isFinite(low) || !isFinite(high) || low <= 0 || high <= 0) return null;

    // Declared either way round without changing the answer.
    var smallest = Math.min(low, high);
    var largest = Math.max(low, high);

    var fewest = Math.ceil(ml / largest);
    var most = Math.ceil(ml / smallest);

    var text = fewest === most
      ? fewest + ' ' + (fewest === 1 ? fruit : pluralise(fruit))
      : fewest + ' to ' + most + ' ' + pluralise(fruit);

    return { fewest: fewest, most: most, fruit: fruit, text: text };
  }

  /* FLOATING POINT, AND IT SHOWS UP IMMEDIATELY HERE: the collection is full of
     22.5 and 7.5, so three drinks make 67.5 and 0.1 + 0.2 arithmetic is one
     addition away. Rounded to three decimals -- far finer than any amount
     written down, and coarse enough that a sum cannot print as 67.49999999. */
  function tidy(n) {
    return Math.round(n * 1000) / 1000;
  }

  /**
   * Total up a shortlist.
   *
   * @param {Array} entries - one per ingredient of every shortlisted drink:
   *        { amount: string, generic: string|string[], bottle: string|string[] }
   * @param {Object} [options]
   * @param {number} [options.multiplier=1] - glasses of each drink
   * @param {string[]} [options.exclude=[]] - generics to leave out, folded the
   *        same way the keys are (pass `not_on_cards`)
   * @param {Object} [options.bottleAliases] - folded spelling -> canonical
   *        bottle name, so one bottle written several ways is one bottle
   * @param {Object} [options.juiceYields] - generic -> {fruit, ml_min, ml_max},
   *        `juice_yields` from _data/cocktails/ingredients.yml
   * @returns {Array} one row per ingredient, sorted by label:
   *        { label, note, generic, bottles: string[],
   *          totals: [{quantity, unit, text}], unquantified: [{text, drinks}],
   *          text }
   */
  function build(entries, options) {
    var opts = options || {};
    var multiplier = typeof opts.multiplier === 'number' && opts.multiplier > 0
      ? opts.multiplier : 1;

    var excluded = {};
    asList(opts.exclude).forEach(function (name) { excluded[foldKey(name)] = true; });

    /* ONE BOTTLE, HOWEVER IT WAS WRITTEN DOWN. bottles.yml has declared aliases
       for exactly this -- Helen, #529: "'wray and nephew' and 'wray & nephew'
       should both collapse onto the latter" -- and the ingredient search already
       resolves suggestions through them. Without it a shopping list prints
       `El Dorado 3 / ED3 / El Dorado 3yo / Havana 3` beside one line, which is
       four spellings of two bottles.

       Case-folding alone does not reach these, which is why this is a declared
       map rather than more string cleverness: nothing about `ED3` says
       `El Dorado 3` except that Helen wrote it down in bottles.yml. Absent, the
       fold below is the whole answer and the list still works. */
    var aliases = opts.bottleAliases || {};
    function canonicalBottle(name) {
      return aliases[foldKey(name)] || name;
    }

    /* Keyed the same way the groups are, so a yield declared as `lemon juice`
       is found however the drink capitalised it. Absent, no line gets a fruit
       count and every total is still right. */
    var yields = {};
    Object.keys(opts.juiceYields || {}).forEach(function (generic) {
      yields[foldKey(generic)] = opts.juiceYields[generic];
    });

    var groups = {};
    var order = [];

    asList(entries).forEach(function (entry) {
      if (!entry) return;
      var generic = joined(entry.generic);
      if (!generic) return;
      var key = foldKey(generic);
      if (excluded[key]) return;

      if (!groups[key]) {
        groups[key] = {
          generic: generic,
          /* TWO VIEWS OF THE SAME BOTTLES, and they answer different questions.

             `bottles` holds each SUGGESTION AS WRITTEN, so "El Dorado 3 or
             Havana Club 3" is one entry -- that is the form the label needs when
             a group is unanimous, because the "or" is Helen's own wording for a
             choice she is happy with (#441).

             `bottleNames` holds the individual bottles, flattened and deduped,
             which is the form the NOTE needs. Without it a group carrying both
             `Havana Club 3` and `El Dorado 3 or Havana Club 3` prints
             "Havana Club 3 / El Dorado 3 or Havana Club 3 / El Dorado 3" --
             three entries, two bottles, one of them twice. Seen on the real
             data for `lightly aged and filtered rum`, which is why this is two
             lists rather than one. */
          bottles: [],
          bottleKeys: {},
          bottleNames: [],
          bottleNameKeys: {},
          /* HOW MANY ENTRIES NAMED NO BOTTLE. This is the whole test for
             whether Helen's bottle-first rule can apply to a group: it can
             only when every entry agreed on one bottle, and one bare entry
             means the group is really "the generic, sometimes as this". */
          bare: 0,
          units: {},
          unitOrder: [],
          unquantified: {},
          unquantifiedOrder: []
        };
        order.push(key);
      }
      var group = groups[key];

      /* Resolved PER ALTERNATIVE, not on the joined string: a suggestion
         written as a list is "Havana 3 or El Dorado 3", and only its members
         are names bottles.yml could know. */
      var named = asList(entry.bottle)
        .map(function (b) { return canonicalBottle(String(b).trim()); })
        .filter(Boolean);
      var bottle = named.join(' or ');
      if (bottle) {
        var bottleKey = foldKey(bottle);
        if (!group.bottleKeys[bottleKey]) {
          group.bottleKeys[bottleKey] = true;
          group.bottles.push(bottle);
        }
        named.forEach(function (name) {
          var nameKey = foldKey(name);
          if (!group.bottleNameKeys[nameKey]) {
            group.bottleNameKeys[nameKey] = true;
            group.bottleNames.push(name);
          }
        });
      } else {
        group.bare += 1;
      }

      /* PER-DRINK QUANTITIES — Helen, 2026-09-04, asked for after the global
         scaler: two negronis and six daiquiris is a real weekend, and one
         number for everything cannot say it.

         An entry's own `glasses` wins; `options.multiplier` is the fallback for
         everything that does not carry one. So the global scaler is simply the
         case where no entry has an opinion, which is why it needed no second
         code path and why every existing test still describes what it did. */
      var scale = (typeof entry.glasses === 'number' && entry.glasses > 0)
        ? entry.glasses : multiplier;

      var parsed = parseAmount(entry.amount);
      if (parsed) {
        if (group.units[parsed.unit] === undefined) {
          group.units[parsed.unit] = 0;
          group.unitOrder.push(parsed.unit);
        }
        group.units[parsed.unit] += parsed.quantity * scale;
      } else {
        var text = String(entry.amount || '').trim();
        if (!text) return;
        if (group.unquantified[text] === undefined) {
          group.unquantified[text] = 0;
          group.unquantifiedOrder.push(text);
        }
        group.unquantified[text] += scale;
      }
    });

    return order.map(function (key) {
      var group = groups[key];

      /* THE GENERIC LEADS, ALWAYS. See the header: Helen settled this after
         looking at the first version, and it matches the drink page's own
         `name (bottle)` shape.

         The bracketed part is the flat, deduped list of individual bottles --
         see `bottleNames` above for the real line this shape is fixing. The
         group's bottles AS WRITTEN are still on the row for a caller that wants
         the "or" form back. */
      var label = group.generic;
      var note = group.bottleNames.join(' / ');

      var totals = group.unitOrder.map(function (unit) {
        var quantity = tidy(group.units[unit]);
        return {
          quantity: quantity,
          unit: unit,
          text: amountText(quantity, unit)
        };
      });

      var unquantified = group.unquantifiedOrder.map(function (text) {
        return { text: text, drinks: group.unquantified[text] };
      });

      /* HOW MANY LEMONS. Only ever from the ml total: the yields are declared in
         millilitres, and "2 dashes of lemon juice" is not a fruit. */
      var millilitres = group.units.ml || 0;
      var fruit = fruitCount(tidy(millilitres), yields[foldKey(group.generic)]);

      /* ONE STRING FOR THE WHOLE AMOUNT, built here rather than in the template,
         so that the copy-to-clipboard text and the rendered row can never say
         different things. */
      var parts = totals.map(function (t) { return t.text; })
        .concat(unquantified.map(function (u) {
          return u.drinks > 1 ? u.text + ' (×' + u.drinks + ')' : u.text;
        }));

      return {
        label: label,
        note: note,
        generic: group.generic,
        bottles: group.bottles.slice(),
        totals: totals,
        unquantified: unquantified,
        fruit: fruit,
        millilitres: tidy(millilitres),
        text: parts.join(' + ')
      };
    }).sort(function (a, b) {
      /* DESCENDING BY VOLUME — Helen, 2026-09-04: "order by descending volume
         required." The big pours are what you shop for and what you might not
         have; two dashes of bitters is a bottle you almost certainly own.

         MILLILITRES DECIDE, AND ONLY MILLILITRES. Sorting across units would
         mean ranking 45 ml against 2 dashes, which needs the conversion this
         file refuses to invent everywhere else. So everything with a volume
         sorts first, largest to smallest; everything without one (bitters by
         the dash, mint by the leaf, a `to top`) follows in a block of its own,
         alphabetically, which is the only order left that means anything. */
      if (a.millilitres !== b.millilitres) return b.millilitres - a.millilitres;
      return a.label.toLowerCase().localeCompare(b.label.toLowerCase());
    });
  }

  var api = {
    build: build,
    parseAmount: parseAmount,
    fruitCount: fruitCount,
    foldKey: foldKey,
    foldUnit: foldUnit,
    unitLabel: unitLabel,
    wholeText: wholeText,
    amountText: amountText,
    // #801. Used by food-shopping-list.js only; see their own headers.
    splitParenthetical: splitParenthetical,
    fractionText: fractionText,
    tidy: tidy
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  } else {
    root.HTF = root.HTF || {};
    root.HTF.shoppingList = api;
  }
})(typeof window !== 'undefined' ? window : this);
