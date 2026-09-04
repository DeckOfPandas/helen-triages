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
// So the GROUP is the generic — the thing there is one of in a cupboard — and
// the LABEL still answers Helen's rule wherever the data lets it:
//
//   - every entry in the group names the same bottle  ->  the bottle leads,
//     with the generic as the quiet note. Her rule, exactly.
//   - otherwise                                       ->  the generic leads,
//     and the bottles that were named are listed beside it, so nothing she
//     wrote down is lost.
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

  function foldUnit(unit) {
    var u = String(unit || '').trim().toLowerCase();
    if (UNIT_PLURALS[u]) return UNIT_PLURALS[u];
    return u;
  }

  /* The plural again, for display, and derived rather than stored: a total is
     only pluralised when it is not exactly one, and `ml`/`g` are never
     pluralised at all because they are symbols rather than words. */
  var SYMBOL_UNITS = { ml: true, g: true, cl: true, l: true, oz: true, '': true };

  function unitLabel(unit, quantity) {
    if (SYMBOL_UNITS[unit]) return unit;
    if (quantity === 1) return unit;

    // `leaf` -> `leaves`, the one unit here that does not take a suffix.
    if (/f$/.test(unit)) return unit.replace(/f$/, 'ves');

    /* A SIBILANT TAKES `es`, EVERYTHING ELSE TAKES `s`. Written as the rule
       rather than as a list, because a list is what got this wrong: `dash` and
       `pinch` were the two the collection contains, `pinch` had a line of its
       own and `dash` fell through to the default and printed `2 dashs` -- in
       the single most common non-millilitre unit in the data (45 entries). The
       rule covers both, and covers whichever sibilant unit is written next. */
    if (/(s|sh|ch|x|z)$/.test(unit)) return unit + 'es';
    return unit + 's';
  }

  /**
   * Split "22.5 ml" into a number and a unit.
   *
   * Returns null when the string is not a quantity at all -- `to top`, `to
   * rinse` -- which is a real answer rather than a failure, and the caller
   * counts those entries instead of summing them.
   *
   * @param {string} amount
   * @returns {{quantity: number, unit: string}|null}
   */
  function parseAmount(amount) {
    var match = /^\s*([0-9]+(?:\.[0-9]+)?)\s*(.*?)\s*$/.exec(String(amount || ''));
    if (!match) return null;
    var quantity = parseFloat(match[1]);
    if (!isFinite(quantity)) return null;
    return { quantity: quantity, unit: foldUnit(match[2]) };
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

      var parsed = parseAmount(entry.amount);
      if (parsed) {
        if (group.units[parsed.unit] === undefined) {
          group.units[parsed.unit] = 0;
          group.unitOrder.push(parsed.unit);
        }
        group.units[parsed.unit] += parsed.quantity * multiplier;
      } else {
        var text = String(entry.amount || '').trim();
        if (!text) return;
        if (group.unquantified[text] === undefined) {
          group.unquantified[text] = 0;
          group.unquantifiedOrder.push(text);
        }
        group.unquantified[text] += multiplier;
      }
    });

    return order.map(function (key) {
      var group = groups[key];

      /* HELEN'S RULE, APPLIED WHERE THE DATA ALLOWS IT. One bottle named by
         every entry in the group is the case she described, and the bottle
         leads. Anything else -- a bare entry, or two bottles -- and the generic
         has to lead, because there is no single bottle for this line to be. */
      var oneBottle = group.bottles.length === 1 && group.bare === 0;
      var label = oneBottle ? group.bottles[0] : group.generic;
      // The flat, deduped names for the note — see `bottleNames` above for the
      // real line on real data that this is fixing.
      var note = oneBottle ? group.generic : group.bottleNames.join(' / ');

      var totals = group.unitOrder.map(function (unit) {
        var quantity = tidy(group.units[unit]);
        var shown = unitLabel(unit, quantity);
        return {
          quantity: quantity,
          unit: unit,
          text: shown ? quantity + ' ' + shown : String(quantity)
        };
      });

      var unquantified = group.unquantifiedOrder.map(function (text) {
        return { text: text, drinks: group.unquantified[text] };
      });

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
        text: parts.join(' + ')
      };
    }).sort(function (a, b) {
      return a.label.toLowerCase().localeCompare(b.label.toLowerCase());
    });
  }

  var api = {
    build: build,
    parseAmount: parseAmount,
    foldKey: foldKey,
    foldUnit: foldUnit,
    unitLabel: unitLabel
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  } else {
    root.HTF = root.HTF || {};
    root.HTF.shoppingList = api;
  }
})(typeof window !== 'undefined' ? window : this);
