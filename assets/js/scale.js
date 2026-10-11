// Scaling a drink: the recipe as written, times a number (#545). No DOM.
// The arithmetic only; assets/js/cocktail-scale.js is the wiring. Amounts are
// read by HTF.shoppingList.parseAmount, the one amount parser in the repo.
//
// The ratios never move: the MULTIPLE is snapped and no amount is rounded. A
// multiple is allowed only if every ml amount lands exactly on the 2.5 ml
// grid. In integer half-millilitres, with G the gcd of the gridded amounts,
// the allowed multiples are m = k × 5/G, k = 1, 2, 3, … and are carried as the
// integer k; the decimal is for display only. ×1 is always allowed, because
// only amounts already on the grid enter G.
//
// Only `ml` is a volume. Anything else is a count and simply multiplies, as
// does an ml amount written off the grid; an amount with no number passes
// through. A multiple taking a volume under 2.5 ml is refused, never rounded.
// The total is the ml only, and a range counts its lower end.

(function (root, factory) {
  /* The dependency is resolved on each side: a require under Node,
     `HTF.shoppingList` in a browser, so the page must load shopping-list.js
     first (tests/test_site_config.py guards the order). */
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

  /* The fallback step, for a drink with no gridded volume at all: there are
     no ratios to preserve, so halves. Otherwise see `stepFor`. */
  var MULTIPLE_STEP = 0.5;

  /* Everything exact is done in integer half-millilitres: 22.5 ml is 45 units
     and the 2.5 ml grid is 5. */
  var UNITS_PER_ML = 2;
  var GRID_UNITS = 5;

  /* The fractions a snapped multiple is printed with; a missing one falls
     back to `2/7`. `1½` is built from the whole part plus `½`. */
  var VULGAR = {
    '1/2': '½', '1/3': '⅓', '2/3': '⅔', '1/4': '¼', '3/4': '¾',
    '1/5': '⅕', '2/5': '⅖', '3/5': '⅗', '4/5': '⅘',
    '1/6': '⅙', '5/6': '⅚', '1/8': '⅛', '3/8': '⅜', '5/8': '⅝', '7/8': '⅞'
  };

  function gcd(a, b) {
    while (b) { var t = a % b; a = b; b = t; }
    return a;
  }

  // The units that are a volume and so answer to the floor.
  var VOLUMETRIC = { ml: true };

  /* A range keeps its shape: the separator is captured and replayed, spacing
     and dash included. `\s+to\s+` needs its spaces, or `to` matches the start
     of "5 tonic water". */
  var RANGE = /^\s*([0-9]+(?:\.[0-9]+)?)(\s+to\s+|\s*[-–—]\s*)(.+)$/;

  // Rounds away float noise: 22.5 × 1.5 has no exact binary form.
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

  // An integer prints as an integer: `40 ml`, never `40.0 ml`.
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
      /* The same numbers as integer half-millilitres, or null for a volume
         that is not on the grid: "cannot be kept exact", not "no volume". */
      lowUnits: kind === 'volume' ? toUnits(low) : null,
      highUnits: kind === 'volume' && high !== null ? toUnits(high) : null
    };
  }

  /**
   * A millilitre figure as whole half-millilitres, or null if it is not on
   * the 2.5 ml grid to begin with.
   *
   * The grid test is what keeps ×1 allowed: the allowed multiples are 5k/G,
   * so ×1 needs 5 to divide G, which holds when every number entering the gcd
   * is a whole number of 2.5 ml. An off-grid amount stays out of G and is
   * simply multiplied when scaled.
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
   * `{n, d}` is in lowest terms; `value` is the decimal, for display only.
   * Every decision is made on the integers.
   *
   * @returns {{n: number, d: number, value: number, grid: number}} `grid` is G,
   *          in half-millilitre units, and is 0 when the drink has no amount
   *          this file can keep exact.
   */
  function stepFor(entries) {
    var g = 0;
    entries.forEach(function (entry) {
      /* The lower end of a range sets the step, the same end the total
         counts. The upper end is scaled exactly where it divides by the step
         and simply multiplied where it does not. */
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
    /* The tolerance recovers the integer k from a decimal that `multipleOf`
       produced; anything not within a millionth of a whole k is refused. */
    var k = step.grid ? m * step.grid / GRID_UNITS : m / MULTIPLE_STEP;
    var whole = Math.round(k);
    if (whole < 1 || Math.abs(k - whole) > 1e-6) return null;
    return whole;
  }

  /* Deliberately not tidied: ⅓ tidied to 0.333 no longer divides back into a
     whole number of steps, so `stepsFor` would refuse it. Rounding for
     display is the caller's job. */
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
      /* Exact and integer: `lowUnits / grid` is whole because the grid is
         their gcd. */
      low = (entry.lowUnits / step.grid) * k * GRID_UNITS / UNITS_PER_ML;
      high = entry.highUnits === null
        ? null
        : (entry.highUnits % step.grid === 0
            ? (entry.highUnits / step.grid) * k * GRID_UNITS / UNITS_PER_ML
            : tidy(entry.high * multiple));
    } else {
      /* A count, or a volume written off the grid: both simply multiply, and
         neither is rounded. The 2.5 ml floor still applies to the volume. */
      low = tidy(entry.low * multiple);
      high = entry.high === null ? null : tidy(entry.high * multiple);
    }

    /* A count of whole fruit prints in words (`half`, `1½ whole`) through
       shopping-list.js's `wholeText`, so both pages say it the same way. */
    if (entry.unit === 'whole') {
      return high === null
        ? SL.wholeText(low)
        : SL.wholeText(low) + entry.sep + SL.wholeText(high);
    }

    /* The plural follows the number you end up with; for a range that is its
       top end: "1 to 2 dashes". */
    var label = SL.unitLabel(entry.unit, high === null ? low : high);

    var number = high === null ? show(low) : show(low) + entry.sep + show(high);
    return label ? number + ' ' + label : number;
  }

  /**
   * The smallest number of allowed steps this drink can be made at.
   *
   * Mostly 1: the grid divides every gridded amount, so at one step the
   * smallest is already at least 2.5 ml. An off-grid volume is outside G and
   * can still push the floor up.
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

    /* Capped at ×1: a drink written with an ingredient under 2.5 ml must
       still show as written. */
    var atOne = stepsFor(step, 1);
    if (atOne !== null && steps > atOne) steps = atOne;
    return { steps: steps, offender: offender };
  }

  /** What the volumetric half of the drink comes to, as poured. */
  function totalFor(entries, step, k) {
    var multiple = multipleOf(step, k);
    return tidy(entries.reduce(function (sum, entry) {
      if (entry.kind !== 'volume') return sum;
      // A range counts its lower end.
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
   * The multiple that gets this drink to a target volume, before snapping.
   *
   * @param {string[]} amounts
   * @param {number} millilitres
   * @returns {number|null} null when the drink has no volume to scale (nothing
   *          but dashes) or the target is not a positive number
   */
  function multipleForTotal(amounts, millilitres) {
    var target = Number(millilitres);
    if (!isFinite(target) || target <= 0) return null;
    var here = plan(amounts);
    // The base is the drink at ×1, which is always an allowed multiple.
    var atOne = stepsFor(here.step, 1);
    if (atOne === null) return null;
    var base = totalFor(here.entries, here.step, atOne);
    if (!(base > 0)) return null;
    return tidy(target / base);
  }

  /**
   * The nearest multiple this drink can actually be poured at. Nearest, not
   * next one down, and never below the floor.
   *
   * @param {string[]} amounts
   * @param {number} wanted
   * @returns {{multiple: number, steps: number, text: string, moved: boolean}|null}
   *          null when nothing was asked for
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
      // Whether the snap changed the answer, so a caller can stay quiet.
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
   * Refused two ways: a multiple below the floor (`why: 'floor'`), and one
   * that is not a whole number of allowed steps (`why: 'grid'`), so nothing
   * can quietly go back to rounding the amounts.
   *
   * @param {string[]} amounts - the strings as printed, in page order
   * @param {number} multiple - what the reader asked for
   * @returns {{ok: boolean, amounts: string[], multiple: number, text: string}|
   *           {ok: boolean, why: string, floor: number, floorText: string,
   *            offender: number|null, floorTotalMl: number, nearest: number}}
   */
  function scale(amounts, multiple) {
    var here = plan(amounts);
    var m = Number(multiple);
    var k = stepsFor(here.step, m);

    /* The floor is asked first, of the unsnapped number, so a request that is
       too small is reported as 'floor' rather than as 'grid'. */
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

  /** The volumetric total at a multiple. */
  function totalMl(amounts, multiple) {
    var here = plan(amounts);
    var k = stepsFor(here.step, multiple);
    if (k === null) {
      // An unsnapped multiple still gets an answer: the approximate total.
      var m = Number(multiple);
      return tidy(here.entries.reduce(function (sum, entry) {
        return entry.kind === 'volume' ? sum + entry.low * m : sum;
      }, 0));
    }
    return totalFor(here.entries, here.step, k);
  }

  /**
   * A printed amount, split into its number and its one-word unit (#1132).
   *
   * For the rows _layouts/cocktail.html marks `data-unit-quiet`: which rows
   * are quiet is the layout's decision. The split is at the LAST space,
   * because a range prints as "1 to 2 cubes" and the unit on a quiet row is
   * one word. An amount with no space in it is all number.
   *
   * @param {string} text - "2 cubes", "3 each", "1 to 2 cubes", "3"
   * @returns {{number: string, unit: string}}
   */
  function splitUnit(text) {
    var shown = String(text === undefined || text === null ? '' : text).trim();
    var at = shown.lastIndexOf(' ');
    if (at === -1) return { number: shown, unit: '' };
    return { number: shown.slice(0, at).trim(), unit: shown.slice(at + 1) };
  }

  return {
    scale: scale,
    splitUnit: splitUnit,
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
