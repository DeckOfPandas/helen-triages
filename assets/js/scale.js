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
// THE RATIOS ARE NOT NEGOTIABLE — Helen, 2026-09-04, and this replaced rounding
// -----------------------------------------------------------------------------
// "Order should be: recipe states single-order amount, target ml works the
// ratios out backwards within reason but then updates the target ml the user has
// entered to something more sane, that is, based on 2.5-ml increments." And:
// "The ml only matter because I love my glasses and make drinks for them
// precisely, but that isn't as important as not poisoning my friends."
//
// SO THE MULTIPLE IS SNAPPED, NEVER THE AMOUNTS. This file used to scale by
// whatever number it was handed and round each amount to the nearest 2.5 ml,
// which is where the ratios went: ×1.5 of `30 / 22.5 / 30` is `45 / 33.75 / 45`
// on paper and printed `45 / 32.5 / 45`, so the Campari quietly shrank by 4% of
// itself relative to the gin. Nobody is poisoned by a Negroni, but the same
// arithmetic runs over a drink with 5 ml of absinthe in it, and a rounding that
// is invisible on the big pours is 25% on the small one.
//
// A MULTIPLE IS ALLOWED ONLY IF EVERY ml AMOUNT LANDS EXACTLY ON THE 2.5 ml
// GRID at that multiple. Then nothing is rounded, every ratio is preserved to
// the last drop, and every figure on the page is one a jigger can pour.
//
// THE ARITHMETIC, and it is short. Work in HALF-MILLILITRE INTEGER UNITS, so
// 22.5 ml is 45 and 7.5 ml is 15 and there is no floating point anywhere that
// matters. Let G be the greatest common divisor of those units and let the grid
// be 5 units (2.5 ml). A multiple m is allowed exactly when G·m is a whole
// number of grid steps — Bézout gives both directions, since G is an integer
// combination of the amounts — so the allowed multiples are
//
//     m = k × 5/G,   k = 1, 2, 3, …
//
// `30 / 22.5 / 30` has G = 15, so the step is ⅓ and ×⅓ pours `10 / 7.5 / 10`,
// exact. `45 / 22.5 / 15 / 5` has G = 5, so the step is ×1 and there is no half
// of that drink: half of 5 ml is 2.5 ml, which is fine, but half of 45 is 22.5
// and half of 15 is 7.5 — those are fine too — while half of 5 ml of the NEXT
// such drink would not be. The step is what it is; the control walks it.
//
// THE FLOOR COMES FREE, and that is the pleasing part. G divides every gridded
// amount, so the smallest of them is at least G, so at the smallest allowed
// multiple (k = 1) it is at least 5 units — 2.5 ml, the minimum pour — without
// anything having to check. The explicit floor below survives for the amounts
// that are NOT on the grid, which are outside G and can still go under.
//
// ×1 IS ALWAYS ALLOWED, and that is not luck either: every number going into G
// is a whole number of 2.5 ml, so 5 divides G, so k = G/5 is an integer and
// gives m = 1. The recipe as written can never be refused by its own arithmetic.
//
// KEPT AS A FRACTION, NEVER AS A FLOAT COMPARED FOR EQUALITY. 5/15 is 0.333…
// and no number of decimal places makes `0.3333 × 3` equal 1. Every multiple
// this file works with is carried as the integer k, and the decimal is produced
// only for display and for the `step` attribute.
//
// ONE AMOUNT IN THE COLLECTION IS OFF THE GRID: cobra-effect's `22.75 ml`. It
// is left out of G — it could only drag the step somewhere absurd — and it is
// then simply MULTIPLIED, like a dash. It is not rounded to the grid, and that
// is the ruling applied to itself: rounding it would move a ratio, which is the
// one thing this file no longer does. ×2 of 22.75 ml is 45.5 ml, exactly as
// pourable as the 22.75 the drink already asks for. Everything else in that
// drink stays exact.
//
// (The old code rounded it, and rounded every other amount too. The visible
// cost was small and the invisible one was not: at ×1 a hypothetical 1 ml pour
// printed as `0 ml`, because 1 rounds to nothing on a 2.5 grid.)
//
// WHY THE GRID IS 2.5 ml. Helen, 2026-09-04: a barspoon is 5 ml and a jigger is
// marked in 2.5s, so 2.5 ml is the smallest anyone actually pours. It is the
// grid every allowed multiple lands on and the floor no pour may go under; it
// is no longer a rounding rule.
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
// BOTH BOXES SNAP, and the target box's answer is REWRITTEN — Helen, 2026-09-04:
// the target "works the ratios out backwards within reason but then updates the
// target ml the user has entered to something more sane". This reverses the
// paragraph that used to stand here, which said a target was exact by intent and
// must not be snapped. It was the right answer to the wrong question: the amounts
// were being rounded to honour the typed total, and that is the trade the ruling
// above refuses. So the typed total becomes the nearest ALLOWED multiple, the
// drink is poured in its own exact ratios, and the box is rewritten to the total
// that actually comes out of the shaker.
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

  /* THE CONTROL'S FALLBACK STEP, for a drink with no gridded volume in it at
     all -- nothing but dashes, or nothing but that one off-grid amount. There
     are no ratios to preserve then, so halves are as good an answer as any and
     it is the answer this control gave before the grid existed. Every real
     drink derives its own step from its own amounts; see `stepFor`. */
  var MULTIPLE_STEP = 0.5;

  /* INTEGER HALF-MILLILITRES ARE THE UNIT EVERYTHING EXACT IS DONE IN -- see
     the header. 22.5 ml is 45 units and 2.5 ml is 5, so the grid a pour must
     land on is 5 units and there is no float in the arithmetic that decides
     whether a multiple is allowed. */
  var UNITS_PER_ML = 2;
  var GRID_UNITS = 5;

  /* The vulgar fractions a snapped multiple is printed with. Denominators 3 and
     6 are the ones this collection actually produces in quantity (35 drinks
     step in thirds, 20 in sixths); the rest are here because the map costs
     nothing and a missing one falls back to `2/7`, which is uglier than it
     needs to be. `1½` is built from the whole part plus `½`. */
  var VULGAR = {
    '1/2': '½', '1/3': '⅓', '2/3': '⅔', '1/4': '¼', '3/4': '¾',
    '1/5': '⅕', '2/5': '⅖', '3/5': '⅗', '4/5': '⅘',
    '1/6': '⅙', '5/6': '⅚', '1/8': '⅛', '3/8': '⅜', '5/8': '⅝', '7/8': '⅞'
  };

  function gcd(a, b) {
    while (b) { var t = a % b; a = b; b = t; }
    return a;
  }

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
    return {
      kind: kind, low: low, high: high, unit: unit, sep: sep, text: text,
      /* THE SAME NUMBERS AS INTEGER HALF-MILLILITRES, or null where the amount
         will not sit on that grid. `null` is not "no volume" -- it is "a volume
         this file cannot keep exact", which is a different thing and is why it
         is a separate field rather than a zero. */
      lowUnits: kind === 'volume' ? toUnits(low) : null,
      highUnits: kind === 'volume' && high !== null ? toUnits(high) : null
    };
  }

  /**
   * A millilitre figure as whole half-millilitres, or null if it is not ON the
   * 2.5 ml grid to begin with.
   *
   * BOTH CONDITIONS, AND THE SECOND IS WHAT KEEPS ×1 ALLOWED. G is the gcd of
   * these numbers and the allowed multiples are 5k/G, so ×1 is allowed exactly
   * when 5 divides G -- which is guaranteed if every number going into the gcd
   * is itself a multiple of 5 units, i.e. already a whole number of 2.5 ml.
   * That is true of every millilitre amount in the collection, so ×1 is always
   * available and the recipe as written is never refused.
   *
   * An amount that is NOT on the grid (`22.75 ml`, `4 ml`) is off this path
   * entirely: it cannot be kept exact by any multiple, it must not be allowed
   * to drag the step somewhere absurd, and it is rounded to the grid when
   * scaled exactly as every amount used to be.
   */
  function toUnits(ml) {
    if (typeof ml !== 'number' || !isFinite(ml) || ml <= 0) return null;
    var exact = ml * UNITS_PER_ML;
    var whole = Math.round(exact);
    if (Math.abs(exact - whole) > 1e-9) return null;
    return whole % GRID_UNITS === 0 ? whole : null;
  }

  function kindOf(unit) {
    return VOLUMETRIC[unit] ? 'volume' : 'count';
  }

  /**
   * The step this drink's own amounts allow, as an exact fraction.
   *
   * See the header for the proof. `{n, d}` is in lowest terms and `value` is
   * the decimal, which is for the `step` attribute and for display and for
   * NOTHING ELSE -- every decision is made on the integers.
   *
   * @returns {{n: number, d: number, value: number, grid: number}} `grid` is G,
   *          in half-millilitre units, and is 0 when the drink has no amount
   *          this file can keep exact.
   */
  function stepFor(entries) {
    var g = 0;
    entries.forEach(function (entry) {
      /* THE LOWER END OF A RANGE IS WHAT SETS THE STEP, the same end the total
         counts (see the header). A range is one ingredient's own latitude --
         "30–45 ml, to taste" -- so the figure you pour against is the small
         one, and letting the upper end tighten the step would make a drink
         harder to scale because of a number nobody has to pour. The upper end
         is still scaled, exactly where it divides by the step and rounded to
         the 2.5 grid where it does not. */
      if (entry.kind !== 'volume' || entry.lowUnits === null) return;
      g = gcd(g, entry.lowUnits);
    });
    if (!g) return { n: 1, d: 2, value: MULTIPLE_STEP, grid: 0 };
    var common = gcd(GRID_UNITS, g);
    return {
      n: GRID_UNITS / common,
      d: g / common,
      value: GRID_UNITS / g,
      grid: g
    };
  }

  /** How many allowed steps a multiple is, or null when it is not a whole number of them. */
  function stepsFor(step, multiple) {
    var m = Number(multiple);
    if (!isFinite(m) || m <= 0) return null;
    /* THE TOLERANCE IS NOT AN EQUALITY TEST, it is the reverse: a caller that
       has been through `snapMultiple` hands back a decimal that came FROM an
       integer k, and this recovers the k. Anything that is not within a
       millionth of a whole k was not produced here and is refused. */
    var k = step.grid ? m * step.grid / GRID_UNITS : m / MULTIPLE_STEP;
    var whole = Math.round(k);
    if (whole < 1 || Math.abs(k - whole) > 1e-6) return null;
    return whole;
  }

  /* The multiple `k` allowed steps come to, DELIBERATELY NOT TIDIED. ⅓ is
     0.3333333333333333 and `tidy` would make it 0.333, which no longer divides
     back into a whole number of steps -- so the value this function hands out
     would be refused by `stepsFor` the moment it came back. Rounding for
     display is the caller's job and belongs at the edge; in here the float is
     the closest thing to the fraction that a double can hold, and it
     round-trips. */
  function multipleOf(step, k) {
    return step.grid ? k * GRID_UNITS / step.grid : k * MULTIPLE_STEP;
  }

  /**
   * A snapped multiple, printed the way a person writes one: `⅓`, `1½`, `2`.
   *
   * @param {{n: number, d: number}} step
   * @param {number} k - how many steps
   */
  function stepText(step, k) {
    var num = k * step.n;
    var den = step.d;
    var common = gcd(num, den);
    num /= common;
    den /= common;
    if (den === 1) return String(num);
    var whole = Math.floor(num / den);
    var rest = num - whole * den;
    var vulgar = VULGAR[rest + '/' + den] || (rest + '/' + den);
    return (whole ? String(whole) : '') + vulgar;
  }

  /** One amount, scaled and printed. */
  function format(entry, multiple, step, k) {
    if (entry.kind === 'words') return entry.text;

    var low, high;
    if (entry.kind === 'volume' && entry.lowUnits !== null && step.grid) {
      /* EXACT, AND INTEGER ALL THE WAY. `lowUnits / grid` is a whole number
         because the grid is their gcd, so this never leaves the integers until
         the divide by 2 that turns half-millilitres back into millilitres. */
      low = (entry.lowUnits / step.grid) * k * GRID_UNITS / UNITS_PER_ML;
      high = entry.highUnits === null
        ? null
        : (entry.highUnits % step.grid === 0
            ? (entry.highUnits / step.grid) * k * GRID_UNITS / UNITS_PER_ML
            : tidy(entry.high * multiple));
    } else {
      /* A COUNT, OR A VOLUME THAT WAS NEVER ON THE GRID -- see the header.
         Both simply multiply. THE OFF-GRID VOLUME IS NOT ROUNDED, and that
         changed with this ruling: rounding 22.75 ml to 22.5 moved a ratio, and
         at ×1 it printed `0 ml` for a 1 ml pour. An amount that was written off
         the grid stays off it, scaled honestly -- ×2 of 22.75 ml is 45.5 ml,
         which is exactly as pourable as the 22.75 the drink already asks for.
         The 2.5 ml FLOOR still applies to it; only the rounding is gone. */
      low = tidy(entry.low * multiple);
      high = entry.high === null ? null : tidy(entry.high * multiple);
    }

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
   * The smallest number of allowed steps this drink can be made at.
   *
   * MOSTLY 1, AND THAT IS THE POINT -- the header's proof: the grid divides
   * every gridded amount, so at one step the smallest of them is already at
   * least 2.5 ml. What survives here is the case the grid cannot answer: an
   * off-grid volume (cobra-effect's 22.75 ml) is not part of G and still has to
   * clear the floor, so it can push the floor up on its own.
   *
   * @returns {{steps: number, offender: number|null}} offender indexes into
   *          `entries`, and is null when nothing on the page is a volume
   */
  function floorFor(entries, step) {
    var smallest = null;
    var offender = null;

    entries.forEach(function (entry, index) {
      if (entry.kind !== 'volume' || !(entry.low > 0)) return;
      if (smallest === null || entry.low < smallest) {
        smallest = entry.low;
        offender = index;
      }
    });

    if (smallest === null) return { steps: 1, offender: null };

    // The epsilon is the floating-point one: at exactly 2.5 ml the ratio is 1
    // and must not ceil to 2 because it computed as 1.0000000000000002.
    var needed = MIN_POUR / smallest / multipleOf(step, 1);
    var steps = Math.max(1, Math.ceil(tidy(needed) - 1e-9));

    /* CAPPED AT ×1 -- see the header. A drink written with an ingredient under
       2.5 ml is Helen's recipe, not a fault, and the page must be able to show
       it as written. */
    var atOne = stepsFor(step, 1);
    if (atOne !== null && steps > atOne) steps = atOne;
    return { steps: steps, offender: offender };
  }

  /** What the volumetric half of the drink comes to, as poured. */
  function totalFor(entries, step, k) {
    var multiple = multipleOf(step, k);
    return tidy(entries.reduce(function (sum, entry) {
      if (entry.kind !== 'volume') return sum;
      /* A RANGE COUNTS ITS LOWER END -- see the header. The total is a figure
         you pour against, and the smaller end is the one you can always make. */
      if (entry.lowUnits !== null && step.grid) {
        return sum + (entry.lowUnits / step.grid) * k * GRID_UNITS / UNITS_PER_ML;
      }
      return sum + entry.low * multiple;
    }, 0));
  }

  /** Everything a drink's amounts settle before anyone types: parse, step, floor. */
  function plan(amounts) {
    var entries = asList(amounts).map(read);
    var step = stepFor(entries);
    var floor = floorFor(entries, step);
    return { entries: entries, step: step, floor: floor };
  }

  /**
   * The multiple that gets this drink to a target volume, BEFORE snapping.
   *
   * The ideal, in other words -- what the reader asked for expressed as a
   * multiple. `snapMultiple` is what turns it into something pourable, and the
   * two are separate so a caller can see how far the snap moved.
   *
   * @param {string[]} amounts
   * @param {number} millilitres - what the reader typed
   * @returns {number|null} null when the drink has no volume to scale (nothing
   *          but dashes) or the target is not a positive number
   */
  function multipleForTotal(amounts, millilitres) {
    var target = Number(millilitres);
    if (!isFinite(target) || target <= 0) return null;
    var here = plan(amounts);
    /* THE BASE IS THE DRINK AT ×1, and ×1 is always an allowed multiple where
       there is a grid at all -- every amount is on the 2.5 grid, so the grid
       divides them and 1 is a whole number of steps. See the header's proof. */
    var atOne = stepsFor(here.step, 1);
    if (atOne === null) return null;
    var base = totalFor(here.entries, here.step, atOne);
    if (!(base > 0)) return null;
    return tidy(target / base);
  }

  /**
   * The nearest multiple this drink can actually be poured at.
   *
   * NEAREST, NOT NEXT ONE DOWN. Helen asked for the typed number to be updated
   * "to something more sane", not to be reduced -- 100 ml of an 82.5 ml drink
   * is nearer ×1 (82.5 ml) than ×⅔ (55 ml), and a reader who typed 100 wants
   * the closer of the two.
   *
   * @param {string[]} amounts
   * @param {number} wanted
   * @returns {{multiple: number, steps: number, text: string, moved: boolean}|null}
   *          null when there is nothing to scale or nothing was asked for
   */
  function snapMultiple(amounts, wanted) {
    var m = Number(wanted);
    if (!isFinite(m) || m <= 0) return null;
    var here = plan(amounts);
    var per = multipleOf(here.step, 1);
    var k = Math.max(here.floor.steps, Math.round(m / per));
    return {
      multiple: multipleOf(here.step, k),
      steps: k,
      text: stepText(here.step, k),
      /* Whether the snap actually changed the answer, so a caller can stay
         quiet when it did not. A thousandth is finer than any multiple this
         control offers and coarser than the float error. */
      moved: Math.abs(multipleOf(here.step, k) - m) > 0.001
    };
  }

  /** The step this drink's amounts allow, as `{n, d, value}` -- see `stepFor`. */
  function allowedStep(amounts) {
    var step = stepFor(asList(amounts).map(read));
    return { n: step.n, d: step.d, value: step.value };
  }

  /** How a multiple is printed: `⅓`, `1½`, `2`. */
  function multipleText(amounts, multiple) {
    var here = plan(amounts);
    var k = stepsFor(here.step, multiple);
    return k === null ? show(Number(multiple)) : stepText(here.step, k);
  }

  /**
   * Scale a page's worth of amounts.
   *
   * TWO WAYS TO BE REFUSED NOW, and the second is new: a multiple below the
   * floor, and a multiple that is not a whole number of allowed steps. The
   * second exists so nothing can quietly go back to rounding the amounts --
   * `snapMultiple` is the only supported way to choose one, and a caller that
   * skips it is told rather than served an approximation.
   *
   * @param {string[]} amounts - the strings as printed, in page order
   * @param {number} multiple - what the reader asked for
   * @returns {{ok: boolean, amounts: string[], multiple: number, text: string}|
   *           {ok: boolean, why: string, floor: number, offender: number|null,
   *            floorTotalMl: number, nearest: number}}
   */
  function scale(amounts, multiple) {
    var here = plan(amounts);
    var m = Number(multiple);
    var k = stepsFor(here.step, m);

    /* THE FLOOR IS ASKED FIRST, and it is asked of the UNSNAPPED number. A
       target of 20 ml on a 90 ml drink is ×0.22, which is below the floor and
       is a thing to SAY -- Helen, 2026-09-04: "say you can't go below X ml".
       Asking `stepsFor` first would answer "not on the grid", which is true and
       is not the reason, and the reader would be told the wrong thing about
       their own request. */
    var ideal = isFinite(m) && m > 0 ? m / multipleOf(here.step, 1) : 0;
    if (!(ideal > 0) || ideal < here.floor.steps - 1e-9 || k === null) {
      var floorK = here.floor.steps;
      return {
        ok: false,
        why: (ideal > 0 && ideal >= here.floor.steps - 1e-9) ? 'grid' : 'floor',
        floor: multipleOf(here.step, floorK),
        floorText: stepText(here.step, floorK),
        offender: here.floor.offender,
        floorTotalMl: totalFor(here.entries, here.step, floorK),
        nearest: (snapMultiple(amounts, m) || {}).multiple
      };
    }

    return {
      ok: true,
      multiple: multipleOf(here.step, k),
      text: stepText(here.step, k),
      amounts: here.entries.map(function (entry) {
        return format(entry, multipleOf(here.step, k), here.step, k);
      })
    };
  }

  /** The floor alone, for setting the control's `min` before anyone types. */
  function floorMultiple(amounts) {
    var here = plan(amounts);
    return multipleOf(here.step, here.floor.steps);
  }

  /** The volumetric total at a multiple, for the note and for anything later. */
  function totalMl(amounts, multiple) {
    var here = plan(amounts);
    var k = stepsFor(here.step, multiple);
    if (k === null) {
      /* AN UNSNAPPED MULTIPLE STILL GETS AN ANSWER, because this is also how
         `multipleForTotal`'s caller asks "what would that come to?" about a
         number nobody has snapped yet. It is the approximate total, and the
         approximation is the caller's to resolve by snapping. */
      var m = Number(multiple);
      return tidy(here.entries.reduce(function (sum, entry) {
        return entry.kind === 'volume' ? sum + entry.low * m : sum;
      }, 0));
    }
    return totalFor(here.entries, here.step, k);
  }

  return {
    scale: scale,
    floorMultiple: floorMultiple,
    totalMl: totalMl,
    multipleForTotal: multipleForTotal,
    snapMultiple: snapMultiple,
    allowedStep: allowedStep,
    multipleText: multipleText,
    roundPour: roundPour,
    MIN_POUR: MIN_POUR,
    POUR_STEP: POUR_STEP,
    MULTIPLE_STEP: MULTIPLE_STEP
  };
});
