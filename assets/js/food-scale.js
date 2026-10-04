// food-scale.js
// =============================================================================
// ONE FOOD AMOUNT, TIMES A FACTOR. No DOM.
// =============================================================================
// GitHub issue #1005, 2026-09-14: the recipe page's portion scaler. This is
// the arithmetic and the printing; assets/js/recipe-scale.js is the wiring,
// the same split scale.js and cocktail-scale.js run on for the drink page.
//
// NOTHING HERE IS NEW, AND THAT IS THE POINT. The parser is shopping-list.js's
// `parseAmount` -- the ONE amount parser this repo has (MANUAL 9.13) -- and
// the printing is food-shopping-list.js's `totalText`, which already knows
// every rule Helen has given about how a scaled food amount is written: grams
// to the gram and never coarser ("don't round to 10 g or 5 g, round to 1 g"),
// spoons and counts in cook's fractions (⅔ tsp, 1½ tbsp), a range carried at
// both ends (30–50 g doubled is 60–100 g), a tilde kept (~2 tbsp), a bracket
// that restates the quantity scaled with it (1 tbsp (6 g) doubled is 2 tbsp
// (12 g)), and a total of a thousand grams shown as kilograms. A second
// formatter here would be a second answer to "how is 133 g written".
//
// KILOGRAMS AND LITRES ARE FOLDED DOWN FIRST, as the shopping list folds them,
// so that a kilogram halved comes back as grams rather than as `0.6 kg` --
// `totalText` promotes a total of a thousand or more back up, so 1.2 kg at x1
// is still 1.2 kg and at x0.5 is 600 g.
//
// WHAT CANNOT SCALE SAYS SO. An amount with no COUNT in it -- "a few
// handfuls", "some", "to taste" -- comes back untouched with `scaled: false`,
// and the page names it under the control (Helen: "let's add a note to
// bitters and handfuls"). `parseAmount` returning null is a real answer, not
// a failure, exactly as the shopping list treats it.
//
// A MEASURE TAKEN BY HAND SCALES IN HALF STEPS -- #1125. "1 handful" for
// three times the people is "3 handfuls", and never "1.17 handfuls": see
// `halfStep` below, the one place the rounding is decided.
//
// "2 large" SCALES, because `large` is a unit to the parser and a SYMBOL to
// the labeller (no plural), so it prints "4 large" -- Helen: "Things like
// '2 large' can scale, surely".
//
// Loaded the two ways food-shopping-list.js is: as a plain <script> attaching
// to window.HTF, and via require() for tests/js/food-scale.test.js.
// =============================================================================

(function (root, factory) {
  /* BOTH DEPENDENCIES ARE READ AT MODULE SCOPE, so a page loading them the
     wrong way round fails at startup rather than on the first keystroke --
     tests/test_site_config.py guards the order in _layouts/recipe.html. */
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = factory(require('./shopping-list.js'),
                             require('./food-shopping-list.js'));
  } else {
    root.HTF = root.HTF || {};
    root.HTF.foodScale = factory(root.HTF.shoppingList, root.HTF.foodShoppingList);
  }
})(typeof window !== 'undefined' ? window : this, function (shoppingList, foodShoppingList) {
  'use strict';

  var parseAmount = shoppingList.parseAmount;
  var splitParenthetical = shoppingList.splitParenthetical;
  var unitLabel = shoppingList.unitLabel;
  var totalText = foodShoppingList.totalText;

  /* The same fold food-shopping-list.js applies on the way in, restated here
     because that file keeps it private. Same four units, same factors. */
  var CANONICAL = {
    kg: { unit: 'g', factor: 1000 },
    l: { unit: 'ml', factor: 1000 },
    litre: { unit: 'ml', factor: 1000 },
    cl: { unit: 'ml', factor: 10 }
  };

  /* =========================================================================
     THE HALF-STEP RULE, AND THE ONE PLACE IT IS DECIDED -- #1125, 2026-10-04
     =========================================================================
     Helen, raising the issue: "Currently some recipes scale 1 handful to e.g.
     1.17 handfuls, which is obvious nonsense." Asked what should happen
     instead: 'If a recipe calls for "a handful of parsley", three orders of
     that recipe should call for "3 handfuls of parsley".' And, shown what
     whole steps did at x1.5: "Handfuls can scale in half steps."

     So a measure taken by hand or eye SCALES, but only to a figure a person
     could act on: THE NEAREST HALF, AND NEVER LESS THAN A HALF.

         1 handful  x3    -> 3 handfuls
         1 handful  x1.5  -> 1½ handfuls
         1 handful  x7/6  -> 1 handful      (not 1.17)
         1 handful  x2/3  -> ½ handfuls     (0.67 is nearer a half than one)

     THE PLURAL IS THE SITE'S EXISTING RULE, not a new one: shopping-list.js's
     `unitLabel` gives the singular for exactly one and the plural for every
     other quantity, a half included -- "½ tsp" has no plural to show it, but
     "½ pats" and "1½ sachets" are what the scaler already prints. "½
     handfuls" follows that; changing it is `unitLabel`'s business.

     HER SENTENCE NAMES HANDFULS. It is applied to the whole by-eye list as
     one rule; a measure she wants treated differently comes out of the list.

     WHICH MEASURES is data: `half_step_measures` in _data/food/scaling.yml,
     PASSED IN -- the layout emits the list, recipe-scale.js hands it over,
     and this file names no measure. With no list given, a handful scales
     like any other count, which is what every caller before #1125 gets. */
  function halfStep(quantity) {
    return Math.max(0.5, Math.round(quantity * 2) / 2);
  }

  function numberText(n) {
    return shoppingList.fractionText(n);
  }

  function escapeRegExp(text) {
    return String(text).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function measureWords(measures) {
    return (measures || [])
      .map(function (m) { return String(m).trim().toLowerCase(); })
      .filter(function (m) { return m !== ''; })
      .map(escapeRegExp)
      .join('|');
  }

  /* The measure as a WHOLE WORD, singular or plural, anywhere in a unit:
     `handful`, `handfuls`, `small handful`, `large handful each`, `pinches`.
     `handfulness`, `dashi` and `pinchos` are not caught. */
  function measurePattern(words) {
    return new RegExp('(^|[^a-z])(' + words + ')(?:e?s)?(?![a-z])', 'i');
  }

  /* A numbered amount in a half-step measure: "1 handful", "~2 handfuls",
     "1–2 pinches", "1 large handful each". The number is stepped, and the
     measure word -- wherever it sits in the unit -- takes the plural of the
     number it ends up beside. Null when the unit holds no such measure. */
  function scaleHalfStepMeasure(parsed, factor, words) {
    if (!words) return null;
    var pattern = measurePattern(words);
    if (!pattern.test(parsed.unit)) return null;

    var lo = halfStep(parsed.quantity * factor);
    var hi = parsed.max === undefined ? lo : halfStep(parsed.max * factor);
    var unit = parsed.unit.replace(pattern, function (all, before, measure) {
      return before + unitLabel(measure.toLowerCase(), hi);
    });
    var number = hi > lo ? numberText(lo) + '–' + numberText(hi) : numberText(lo);
    return { text: (parsed.approx ? '~' : '') + number + ' ' + unit, scaled: true };
  }

  /* =========================================================================
     THE SAME MEASURE WRITTEN WITH NO NUMBER -- "a handful of fresh parsley"
     =========================================================================
     Helen's own example has no `amount:` at all; the measure is the opening
     of the `item:` text. 96 items in the two collections are written that
     way (5 published), and 5 draft amounts are a bare "pinch" or "a handful".

     WHAT COUNTS AS ONE: `a`, `an`, `one`, or nothing at all before a
     SINGULAR measure ("pinch of salt"). A digit counts as itself. A size word
     may sit between ("a large handful of", "small pinch of") and is kept.

     WHAT IS NOT A NUMBER AND IS LEFT ALONE: "a few", "some", "a couple of",
     "several", and a bare plural ("handfuls of rocket"). "a few dashes of
     Tabasco sauce to taste" therefore does not scale, and is named on the
     Not-scaled line -- which is what Helen asked that line to say.

     AT ONE, THE WORDS ARE THE RECIPE'S OWN. A result that equals what was
     written gives back the text untouched -- "a handful of" stays "a handful
     of", not "1 handful of". Anything else is a number: "½ handfuls of",
     "1½ handfuls of", "3 handfuls of".

     `tail` is what must follow the measure: " of " inside an item's text, or
     the end of the string for an `amount:` that is only the measure. */
  var COUNT_OF_ONE = '(?:(an?|one|\\d+)\\s+)?';
  var SIZE_WORD = '((?:small|large|big|good|generous|little)\\s+)?';

  function scaleMeasurePhrase(text, factor, words, tail) {
    var written = String(text === undefined || text === null ? '' : text);
    var unmoved = { text: written, scaled: false };
    if (!words || !(factor > 0)) return unmoved;

    var match = new RegExp(
      '^(\\s*)' + COUNT_OF_ONE + SIZE_WORD + '(' + words + ')(e?s)?' +
      '((?:\\s+each)?' + tail + ')', 'i').exec(written);
    if (!match) return unmoved;

    var counted = /^\d+$/.test(match[2] || '');
    if (match[5] && !counted) return unmoved;        // a bare plural is no count

    var base = counted ? parseInt(match[2], 10) : 1;
    var n = halfStep(base * factor);
    if (n === base) return { text: written, scaled: true };

    return {
      text: match[1] + numberText(n) + ' ' + (match[3] || '') +
        unitLabel(match[4].toLowerCase(), n) + match[6] +
        written.slice(match[0].length),
      scaled: true
    };
  }

  /**
   * The opening of an ingredient's own text, at a factor -- for a row with no
   * amount: "a handful of fresh parsley" x3 is "3 handfuls of fresh parsley".
   *
   * @param {string} text - the item's text as the page prints it
   * @param {number} factor
   * @param {{halfStep?: string[]}} [options]
   * @returns {{text: string, scaled: boolean}} `scaled: false` and the text
   *          untouched when it does not open with a countable by-eye measure
   */
  function scaleLeadingMeasure(text, factor, options) {
    return scaleMeasurePhrase(text, factor,
      measureWords(options && options.halfStep), '\\s+of\\s+');
  }

  /**
   * One written amount at a factor.
   *
   * @param {string} amount - as the recipe wrote it: "200 g", "1½ tbsp",
   *        "30–50 g", "2 large", "1 tbsp (6 g)", "1 handful", "a few handfuls"
   * @param {number} factor - portions wanted over portions the recipe makes
   * @param {{halfStep?: string[]}} [options] - `halfStep` is
   *        _data/food/scaling.yml's `half_step_measures`
   * @returns {{text: string, scaled: boolean}} the amount to show, and
   *        whether it was scaled. An amount with no count in it comes back as
   *        written with `scaled: false`.
   */
  function scaleAmount(amount, factor, options) {
    var written = String(amount === undefined || amount === null ? '' : amount);
    if (!(factor > 0)) return { text: written, scaled: false };

    var words = measureWords(options && options.halfStep);
    var parsed = parseAmount(written);
    if (!parsed) {
      // "pinch", "a handful", "small handful": the measure and nothing else.
      return scaleMeasurePhrase(written, factor, words, '\\s*$');
    }

    var stepped = scaleHalfStepMeasure(parsed, factor, words);
    if (stepped) return stepped;

    var split = splitParenthetical(parsed.unit);
    var unitWritten = split.lo === undefined ? parsed.unit : split.unit;
    var canon = CANONICAL[unitWritten];
    var unit = canon ? canon.unit : unitWritten;
    var f = canon ? canon.factor : 1;

    var hiQuantity = parsed.max === undefined ? parsed.quantity : parsed.max;
    var total = {
      unit: unit,
      lo: parsed.quantity * factor * f,
      hi: hiQuantity * factor * f,
      approx: !!parsed.approx,
      paren: null
    };

    if (split.lo !== undefined) {
      var pcanon = CANONICAL[split.unit2];
      var pf = pcanon ? pcanon.factor : 1;
      total.paren = {
        unit: pcanon ? pcanon.unit : split.unit2,
        lo: split.lo * factor * pf,
        hi: (split.hi === null ? split.lo : split.hi) * factor * pf
      };
    }

    return { text: totalText(total), scaled: true };
  }

  /* THE NAME ON HELEN'S "(Not scaled: ...)" LINE -- #1125. Her example is the
     specification: "few dashes of Tabasco sauce to taste, unless feeding
     Helen" is listed as "Tabasco sauce". The line names the INGREDIENT, not
     the recipe's whole sentence about it. Three cuts, in this order:

     1. A LEADING MEASURE PHRASE, where the recipe wrote the quantity into
        `item:` -- "a few dashes of", "a few handfuls of". Only a phrase
        holding one of the declared measures AND ending in `of` is taken, so
        "cream of tartar" and "leg of lamb" are untouched: the trap
        _data/food/ingredient_words.yml's `measure_phrases` header names.
     2. EVERYTHING FROM THE FIRST COMMA OR OPEN BRACKET -- the preparation
        ("parsley, chopped"), the aside ("paprika, unless feeding Helen"). The
        same cut _plugins/food_shopping.rb makes for the shopping list, and it
        is what makes her comma-joined line safe: #1088 gave up the semicolon
        knowing "a name containing a comma would read as two", and after this
        cut no name contains one. THE COST: an item that is itself a list
        ("fresh parsley, thyme and sage") is named by its first member --
        accepted, Helen: "doesn't state an amount, so scaling is by common
        sense."
     3. A TRAILING INSTRUCTION -- "to taste", "to serve" -- from
        `trailing_phrases` in ingredient_words.yml, passed in like the
        measures. Only at the END, which is that list's own rule.

     Never cuts a name to nothing: if a step would leave an empty string, the
     text before that step stands. */
  var QUANTIFIER = '(?:(?:an?|one|two|a\\s+few|few|some|a\\s+couple\\s+of|several)\\s+)?';
  var SIZE = '(?:(?:small|large|big|good|generous|little)\\s+)?';

  function keep(candidate, fallback) {
    var trimmed = candidate.replace(/\s+/g, ' ').trim();
    return trimmed === '' ? fallback : trimmed;
  }

  /**
   * @param {string} text - the ingredient row's text, amount and note removed
   * @param {{halfStep?: string[], trailing?: string[]}} [options]
   * @returns {string} the ingredient's name, for the note under the control
   */
  function noteName(text, options) {
    var opts = options || {};
    var name = keep(String(text === undefined || text === null ? '' : text), '');

    var words = measureWords(opts.halfStep);
    if (words) {
      var leading = new RegExp(
        '^' + QUANTIFIER + SIZE + '(?:' + words + ')(?:e?s)?(?:\\s+each)?\\s+of\\s+', 'i');
      name = keep(name.replace(leading, ''), name);
    }

    name = keep(name.split(/[,(]/)[0], name);

    (opts.trailing || []).forEach(function (phrase) {
      var p = String(phrase).trim().toLowerCase();
      if (p === '') return;
      if (name.toLowerCase().slice(-(p.length + 1)) === ' ' + p) {
        name = keep(name.slice(0, name.length - p.length - 1), name);
      }
    });

    return name;
  }

  return {
    scaleAmount: scaleAmount,
    scaleLeadingMeasure: scaleLeadingMeasure,
    noteName: noteName,
    halfStep: halfStep
  };
});
