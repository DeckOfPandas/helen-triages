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
// WHAT CANNOT SCALE SAYS SO. An amount with no number in it -- "a few
// handfuls", "some", "to taste" -- comes back untouched with `scaled: false`,
// and the page names it under the control (Helen: "let's add a note to
// bitters and handfuls"). `parseAmount` returning null is a real answer, not
// a failure, exactly as the shopping list treats it. SO DOES A NUMBERED
// AMOUNT IN A MEASURE TAKEN BY HAND -- "1 handful", "1 pinch" -- since #1125:
// see `isUnscaledMeasure` below, and `noteName` for what the page calls it.
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
  var totalText = foodShoppingList.totalText;

  /* The same fold food-shopping-list.js applies on the way in, restated here
     because that file keeps it private. Same four units, same factors. */
  var CANONICAL = {
    kg: { unit: 'g', factor: 1000 },
    l: { unit: 'ml', factor: 1000 },
    litre: { unit: 'ml', factor: 1000 },
    cl: { unit: 'ml', factor: 10 }
  };

  /* A MEASURE TAKEN BY HAND OR EYE HAS NO FRACTION -- #1125, 2026-10-04.
     Helen: "Currently some recipes scale 1 handful to e.g. 1.17 handfuls,
     which is obvious nonsense." `1 handful` has a number in it, so the parser
     reads it and, before this, the arithmetic ran.

     THE WORDS ARE DATA, `unscaled_measures` in _data/food/scaling.yml, and
     are PASSED IN -- the layout emits them, recipe-scale.js hands them over,
     and this file names none of them. With no list given nothing is held
     back, which is what every caller before #1125 gets.

     MATCHED AS A WHOLE WORD ANYWHERE IN THE AMOUNT, singular or plural, so
     `1 small handful`, `2 handfuls`, `1 large handful each` and `2 pinches`
     are all caught and `1 handfulness` is not. */
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

  function isUnscaledMeasure(amount, measures) {
    var words = measureWords(measures);
    if (!words) return false;
    return new RegExp('(^|[^a-z])(?:' + words + ')(?:e?s)?(?![a-z])', 'i')
      .test(String(amount || ''));
  }

  /**
   * One written amount at a factor.
   *
   * @param {string} amount - as the recipe wrote it: "200 g", "1½ tbsp",
   *        "30–50 g", "2 large", "1 tbsp (6 g)", "a few handfuls"
   * @param {number} factor - portions wanted over portions the recipe makes
   * @param {{unscaled?: string[]}} [options] - `unscaled` is
   *        _data/food/scaling.yml's `unscaled_measures`
   * @returns {{text: string, scaled: boolean}} the amount to show, and
   *        whether it moved. An unparseable amount, and one in a measure that
   *        does not scale, come back as written.
   */
  function scaleAmount(amount, factor, options) {
    var written = String(amount === undefined || amount === null ? '' : amount);
    var parsed = parseAmount(written);
    if (!parsed || !(factor > 0)) {
      return { text: written, scaled: false };
    }
    if (isUnscaledMeasure(written, options && options.unscaled)) {
      return { text: written, scaled: false };
    }

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

  /* THE NAME ON HELEN'S "(Not scaled: ...)" LINE -- #1125. Her two examples
     are the specification: "few dashes of Tabasco sauce to taste, unless
     feeding Helen" is listed as "Tabasco sauce", and "a handful of fresh
     parsley" as "fresh parsley". The line names the INGREDIENT, not the
     recipe's whole sentence about it. Three cuts, in this order:

     1. A LEADING MEASURE PHRASE, where the recipe wrote the quantity into
        `item:` -- "a few dashes of", "A large handful of", "a good pinch of".
        Only a phrase holding one of the declared measures AND ending in `of`
        is taken, so "cream of tartar" and "leg of lamb" are untouched: the
        trap _data/food/ingredient_words.yml's `measure_phrases` header names.
     2. EVERYTHING FROM THE FIRST COMMA OR OPEN BRACKET -- the preparation
        ("parsley, chopped"), the aside ("paprika, unless feeding Helen"). The
        same cut _plugins/food_shopping.rb makes for the shopping list, and it
        is what makes her comma-joined line safe: #1088 gave up the semicolon
        knowing "a name containing a comma would read as two", and after this
        cut no name contains one. THE COST: an item that is itself a list
        ("fresh parsley, thyme and sage") is named by its first member.
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
   * @param {{unscaled?: string[], trailing?: string[]}} [options]
   * @returns {string} the ingredient's name, for the note under the control
   */
  function noteName(text, options) {
    var opts = options || {};
    var name = keep(String(text === undefined || text === null ? '' : text), '');

    var words = measureWords(opts.unscaled);
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
    noteName: noteName
  };
});
