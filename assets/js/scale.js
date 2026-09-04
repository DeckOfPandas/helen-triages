// =============================================================================
// SCALING A DRINK — the recipe as written, times a number. No DOM.
// =============================================================================
// GitHub issue #545, step one of the three that issue was split into on
// 2026-09-01: target SERVINGS today, target ml and target units of alcohol
// later (the third waits on ABV per bottle, #297). This file is the arithmetic
// only; assets/js/cocktail-scale.js is the wiring, exactly as shopping-list.js
// is to cocktail-index.js.
//
// -----------------------------------------------------------------------------
// SERVINGS MEANS MULTIPLES OF THE RECIPE AS WRITTEN — Helen, 2026-09-04
// -----------------------------------------------------------------------------
// There is no `serves:` field and this file does not want one. A drink file
// says 30 ml gin and 22.5 ml Campari; whether that is one glass or one and a
// bit is a fact about the glass, not about the recipe, and inventing a serving
// count for 124 drinks so a control could divide by it would be inventing data
// to make a number look tidier. So the control multiplies: ×2 is twice the
// recipe, ×0.5 is half of it, and ×1 is what the page already says.
//
// -----------------------------------------------------------------------------
// ROUNDING: THE NEAREST 2.5 ml, BECAUSE THAT IS WHAT A JIGGER IS MARKED IN
// -----------------------------------------------------------------------------
// Helen, 2026-09-04: a barspoon is 5 ml and a jigger is marked in 2.5s, so 2.5
// ml is the smallest anyone actually pours. `22.5 × 1.5` is 33.75 on paper and
// 32.5 in a glass, and printing 33.75 would be a precision nobody can act on
// dressed up as accuracy. ONLY THE ROUNDED FIGURE IS SHOWN — not "32.5 (33.75)"
// — because the second number is the one you cannot pour.
//
// -----------------------------------------------------------------------------
// THE FLOOR IS A REFUSAL, NOT A SILENT ROUND — Helen, 2026-09-04
// -----------------------------------------------------------------------------
// "Say you can't go below X ml if any ingredient wants to go below 2.5 ml."
// Rounding a 1.25 ml dash of absinthe up to 2.5 would quietly double it and
// hand back a drink that is no longer the recipe scaled; rounding it to zero
// would drop an ingredient. Both are the scaler making a decision that is
// Helen's. So a multiple that would take ANY volumetric ingredient under 2.5 ml
// is refused, and the answer names the smallest multiple that works, what the
// drink comes to there, and which ingredient set the limit.
//
// THE FLOOR IS CAPPED AT ×1: the recipe as written is never refused. Ten drinks
// in the collection are written with a 2.5 ml ingredient, which is exactly at
// the limit, and one written with less would still be Helen's own recipe rather
// than an error for this file to report.
//
// -----------------------------------------------------------------------------
// ONE PARSER, NOT THREE
// -----------------------------------------------------------------------------
// The amounts are the same strings the shopping list already reads, so
// `HTF.shoppingList.parseAmount` reads them here too, along with its unit
// folding (`dashes` -> `dash`) and its `unitLabel` for putting the plural back.
// A second amount parser in this repo would be a second answer to "is `2 dash`
// the same unit as `2 dashes`", and the two would drift.
//
// WHAT COUNTS AS VOLUMETRIC IS `ml` AND ONLY `ml`, because that is the only
// volume unit that reaches a page: `measures:` in _data/cocktails/ingredients.yml
// converts oz, tsp and cl at ingest (1 oz -> 30 ml, bar-standard rounding, on
// purpose), and `test_every_amount_is_readable_as_a_quantity` (#571) holds the
// line. Everything else the parser returns is a COUNT — dashes, drops, cubes,
// leaves, `each`, a bare number — and a count multiplies and re-pluralises
// rather than rounding to a pour. Grams are a mass, so they scale like a count
// and are never asked to clear the 2.5 ml floor.
//
// AN UNPARSEABLE AMOUNT PASSES THROUGH UNTOUCHED. `to top` and `to rinse` are
// the eleven real ones; twice as much of a drink still wants topping up, and
// there is no number in the string to multiply.
//
// -----------------------------------------------------------------------------
// TOTAL ML, AND A TARGET ML — Helen, 2026-09-04, step two of #545
// -----------------------------------------------------------------------------
// "Please add total ml, either set by your input box, or user-entered number of
// ml -- which you can refuse if it forces a volume to be <2.5 ml. Ignore drops
// and dashes and pinches in target ml."
//
// So the total is the ml AND ONLY THE ml, the same rule the shopping list
// applies to its own sums: a dash is not 0.8 ml in any way worth writing down,
// so it is not 0.8 ml here either, and adding it in would make the one number
// on the row the only unsourced figure on the page. Drops, dashes, pinches,
// leaves, grams and `to top` all sit outside the total, and the reader can see
// they do because they are still on the list unchanged.
//
// A RANGE COUNTS ITS LOWER END. Nothing in the collection is written as a range
// today, so this is a decision for the amount written tomorrow: the total is a
// figure you pour against, and the smaller of the two is the one you can always
// make. (It totalled at the TOP end until 2026-09-04 -- "the most the drink
// could come to" -- which is the right answer to a different question.)
//
// `multipleForTotal` IS NOT SNAPPED TO THE HALF STEP, and that is the whole
// difference between the two boxes. A MULTIPLE is a choice from a list of
// halves; a TARGET is exact by intent -- someone typing 200 ml means 200 ml, and
// rounding their number to the nearest ×0.5 would silently answer a question
// they did not ask. The AMOUNTS are still rounded to the 2.5 ml grid, so what
// comes out is still pourable and the total of the poured figures may sit a
// little either side of what was typed.
// =============================================================================

(function (root, factory) {
  /* Loaded the two ways shopping-list.js is, with one difference: it has a
     dependency, and the dependency is resolved on each side rather than
     reached for globally inside the module. Under Node that is a require; in a
     browser it is `HTF.shoppingList`, which is why _layouts/cocktail.html loads
     shopping-list.js first and tests/test_site_config.py guards the order. */
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = factory(require('./shopping-list.js'));
  } else {
    root.HTF = root.HTF || {};
    root.HTF.scale = factory(root.HTF.shoppingList);
  }
})(typeof window !== 'undefined' ? window : this, function (SL) {
  'use strict';

  /** The smallest pour anyone measures, and the grid every pour lands on. */
  var MIN_POUR = 2.5;
  var POUR_STEP = 2.5;

  /** The control's own step. Halves, so "half the recipe" is one click down. */
  var MULTIPLE_STEP = 0.5;

  /* The units that are a VOLUME and so answer to the floor. A map rather than
     a bare `=== 'ml'` so the day a second one arrives it is one line here and
     no new branch anywhere. */
  var VOLUMETRIC = { ml: true };

  /* A RANGE KEEPS ITS SHAPE. Nothing in the collection is written as one today
     (surveyed for the shopping list: no fractions, no ranges), so this exists
     for the amount that gets written tomorrow rather than for live data.
     The separator is CAPTURED AND REPLAYED, spacing and dash included, so
     "20–30 ml" comes back with its en dash and "1-2 dashes" with its hyphen.

     `\s+to\s+` needs its spaces: without them the `to` alternative matches the
     first two letters of "5 tonic water" and the amount comes back as a range
     from 5 to "nic water". */
  var RANGE = /^\s*([0-9]+(?:\.[0-9]+)?)(\s+to\s+|\s*[-–—]\s*)(.+)$/;

  /* Floating point, the same way shopping-list.js handles it and for the same
     reason: this collection is full of 22.5 and 7.5, and 22.5 × 1.5 has no
     exact binary form. Three decimals is far finer than any amount written
     down and coarse enough that nothing prints as 33.7499999. */
  function tidy(n) {
    return Math.round(n * 1000) / 1000;
  }

  function asList(value) {
    if (value === null || value === undefined) return [];
    return Array.isArray(value) ? value : [value];
  }

  /** A volume, on the 2.5 ml grid. */
  function roundPour(ml) {
    return tidy(Math.round(tidy(ml) / POUR_STEP) * POUR_STEP);
  }

  /* An integer prints as an integer: `40 ml`, never `40.0 ml`. Everything the
     2.5 grid can produce has at most one decimal, and a count keeps whatever
     its own multiplication gave it (tidied), so Number's own toString is
     already the right answer and a fixed decimal count would be wrong. */
  function show(n) {
    return String(tidy(n));
  }

  /**
   * Read one printed amount into the shape the arithmetic works on.
   *
   * @param {string} amount - the string as the page prints it
   * @returns {{kind: string, low: number, high: number|null, unit: string,
   *            sep: string, text: string}} kind is `volume`, `count` or `words`
   */
  function read(amount) {
    var text = String(amount === null || amount === undefined ? '' : amount);

    var range = RANGE.exec(text);
    if (range) {
      var top = SL.parseAmount(range[3]);
      if (top) {
        return record(kindOf(top.unit), parseFloat(range[1]), top.quantity,
                      top.unit, range[2], text);
      }
    }

    var one = SL.parseAmount(text);
    if (one) return record(kindOf(one.unit), one.quantity, null, one.unit, '', text);

    return record('words', 0, null, '', '', text);
  }

  function record(kind, low, high, unit, sep, text) {
    return { kind: kind, low: low, high: high, unit: unit, sep: sep, text: text };
  }

  function kindOf(unit) {
    return VOLUMETRIC[unit] ? 'volume' : 'count';
  }

  /** One amount, scaled and printed. */
  function format(entry, multiple) {
    if (entry.kind === 'words') return entry.text;

    var round = entry.kind === 'volume' ? roundPour : tidy;
    var low = round(entry.low * multiple);
    var high = entry.high === null ? null : round(entry.high * multiple);

    /* HALF A LIME IS PRINTED IN WORDS, NOT AS 0.5 — Helen, 2026-09-04, ruling
       on caipirinha's `amount: "0.5"`: `half` and `whole` are units now, and a
       whole fruit is COUNTED rather than measured. The arithmetic underneath is
       plain (half is 0.5 of a `whole`, so ×2 is 1 and ×3 is 1.5); only the
       printing is special, and it is shopping-list.js's `wholeText` that does
       it, so a shopping list and a drink page say "1½ whole" the same way. */
    if (entry.unit === 'whole') {
      return high === null
        ? SL.wholeText(low)
        : SL.wholeText(low) + entry.sep + SL.wholeText(high);
    }

    /* THE PLURAL FOLLOWS THE NUMBER YOU END UP WITH, and for a range that is
       its top end -- "1 to 2 dashes", never "1 to 2 dash". `unitLabel` leaves
       `ml`, `g` and a bare count alone and pluralises the words, sibilants
       included, which is the bug it was written for (`2 dashs`). */
    var label = SL.unitLabel(entry.unit, high === null ? low : high);

    var number = high === null ? show(low) : show(low) + entry.sep + show(high);
    return label ? number + ' ' + label : number;
  }

  /**
   * The smallest multiple this drink can be made at.
   *
   * The binding ingredient is the SMALLEST volume: whatever hits 2.5 ml first
   * is what stops the whole drink. The raw ratio is then rounded UP to the
   * control's own half step, because a floor the spinner cannot land on is not
   * a floor -- ×0.333 is not a value this control offers.
   *
   * @param {string[]} amounts
   * @returns {{multiple: number, offender: number|null}} offender indexes into
   *          `amounts`, and is null when nothing on the page is a volume
   */
  function floorFor(entries) {
    var smallest = null;
    var offender = null;

    entries.forEach(function (entry, index) {
      if (entry.kind !== 'volume' || !(entry.low > 0)) return;
      if (smallest === null || entry.low < smallest) {
        smallest = entry.low;
        offender = index;
      }
    });

    if (smallest === null) return { multiple: MULTIPLE_STEP, offender: null };

    var needed = MIN_POUR / smallest;
    // The epsilon is the floating-point one: 2.5 / 5 is 0.5 and must not ceil
    // to 1 because it computed as 0.5000000000000001.
    var stepped = Math.ceil(tidy(needed) / MULTIPLE_STEP - 1e-9) * MULTIPLE_STEP;

    /* CAPPED AT ×1 -- see the header. A drink written with an ingredient under
       2.5 ml is Helen's recipe, not a fault, and the page must be able to show
       it as written. Floored at one step, because ×0 is not a drink. */
    return {
      multiple: Math.min(1, Math.max(MULTIPLE_STEP, tidy(stepped))),
      offender: offender
    };
  }

  /** What the volumetric half of the drink comes to, as poured. */
  function totalFor(entries, multiple) {
    return tidy(entries.reduce(function (sum, entry) {
      if (entry.kind !== 'volume') return sum;
      /* A RANGE COUNTS ITS LOWER END -- see the header. The total is a figure
         you pour against, and the smaller end is the one you can always make. */
      return sum + roundPour(entry.low * multiple);
    }, 0));
  }

  /**
   * The multiple that gets this drink to a target volume.
   *
   * NOT SNAPPED TO THE HALF STEP -- see the header. A target is exact by
   * intent, and the amounts it produces are still rounded to the 2.5 ml grid,
   * so the poured total may land a little either side of what was asked for.
   *
   * @param {string[]} amounts
   * @param {number} millilitres - what the reader typed
   * @returns {number|null} null when the drink has no volume to scale (nothing
   *          but dashes) or the target is not a positive number
   */
  function multipleForTotal(amounts, millilitres) {
    var target = Number(millilitres);
    if (!isFinite(target) || target <= 0) return null;
    var base = totalFor(asList(amounts).map(read), 1);
    if (!(base > 0)) return null;
    return tidy(target / base);
  }

  /**
   * Scale a page's worth of amounts.
   *
   * @param {string[]} amounts - the strings as printed, in page order
   * @param {number} multiple - what the reader asked for
   * @returns {{ok: boolean, amounts: string[]}|
   *           {ok: boolean, floor: number, offender: number|null,
   *            floorTotalMl: number}}
   */
  function scale(amounts, multiple) {
    var entries = asList(amounts).map(read);
    var floor = floorFor(entries);
    var m = Number(multiple);

    /* THE REFUSAL IS AGAINST THE FLOOR, not against each ingredient at the
       moment of printing, and that is what keeps the two consistent: the floor
       is capped at ×1, so a drink written with a 1 ml ingredient still renders
       as written instead of refusing its own recipe. */
    if (!isFinite(m) || m <= 0 || m < floor.multiple - 1e-9) {
      return {
        ok: false,
        floor: floor.multiple,
        offender: floor.offender,
        floorTotalMl: totalFor(entries, floor.multiple)
      };
    }

    return {
      ok: true,
      amounts: entries.map(function (entry) { return format(entry, m); })
    };
  }

  /** The floor alone, for setting the control's `min` before anyone types. */
  function floorMultiple(amounts) {
    return floorFor(asList(amounts).map(read)).multiple;
  }

  /** The volumetric total at a multiple, for the note and for anything later. */
  function totalMl(amounts, multiple) {
    return totalFor(asList(amounts).map(read), Number(multiple));
  }

  return {
    scale: scale,
    floorMultiple: floorMultiple,
    totalMl: totalMl,
    multipleForTotal: multipleForTotal,
    roundPour: roundPour,
    MIN_POUR: MIN_POUR,
    POUR_STEP: POUR_STEP,
    MULTIPLE_STEP: MULTIPLE_STEP
  };
});
