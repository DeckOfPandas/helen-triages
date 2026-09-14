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
// a failure, exactly as the shopping list treats it.
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

  /**
   * One written amount at a factor.
   *
   * @param {string} amount - as the recipe wrote it: "200 g", "1½ tbsp",
   *        "30–50 g", "2 large", "1 tbsp (6 g)", "a few handfuls"
   * @param {number} factor - portions wanted over portions the recipe makes
   * @returns {{text: string, scaled: boolean}} the amount to show, and
   *        whether it moved. An unparseable amount comes back as written.
   */
  function scaleAmount(amount, factor) {
    var written = String(amount === undefined || amount === null ? '' : amount);
    var parsed = parseAmount(written);
    if (!parsed || !(factor > 0)) {
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

  return {
    scaleAmount: scaleAmount
  };
});
