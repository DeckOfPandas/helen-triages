// food-shopping-list.js
// =============================================================================
// WHAT A SHORTLIST OF RECIPES ADDS UP TO, BY AISLE. No DOM.
// =============================================================================
// GitHub issue #801, Helen: "add scaler and shopping list feature to food
// recipe shortlist page ... I would like all the same features ... no need to
// cost the portions ... Group the shopping list by grocery aisle."
//
// Pure, and loaded the two ways shopping-list.js and filter-state.js are: as a
// plain <script> attaching to window.HTF, and via require() for
// tests/js/food-shopping-list.test.js. The DOM half is filters.js, which is
// food's index script and already owns `state.shortlisted` -- the same place
// cocktail-index.js keeps its half, for the same reason.
//
// -----------------------------------------------------------------------------
// WHY THIS IS NOT shopping-list.js WITH A FLAG
// -----------------------------------------------------------------------------
// The two lists answer the same question about different data, and every
// difference is load-bearing rather than cosmetic:
//
//   - A drink groups by its `generic` and carries a BOTTLE; a recipe groups by
//     the ingredient name and carries nothing.
//   - A drink's amounts are 682 plain decimals on a 2.5 ml grid. A recipe's
//     are `½ tsp`, `30–50 g`, `~2 tbsp`, `2 x 400 g cans` and `1 tbsp (6 g)`.
//   - A drink is scaled by whole numbers of glasses and clamped at x1
//     (MANUAL 9.13). A recipe is scaled by PORTIONS WANTED over portions the
//     recipe makes, so x0.67 is ordinary.
//   - A drink list sorts by descending volume; this one groups by aisle.
//
// So the ARITHMETIC is shared and the shape is not. `parseAmount`,
// `splitParenthetical`, `foldKey`, `foldUnit`, `unitLabel` and `fractionText`
// all come from shopping-list.js, which stays the one place that knows how to
// read an amount this repo has written down (MANUAL 9.13's one-parser rule).
//
// -----------------------------------------------------------------------------
// THE SCALER IS PORTIONS, NOT BATCHES
// -----------------------------------------------------------------------------
// Helen asked for a serving-size guess for every recipe in the same breath as
// the scaler, which only earns its keep if the number on screen is people
// rather than repeats: "we are four tonight" is the question, and a recipe
// that serves six answers it at x0.67. `_plugins/food_shopping.rb` resolves
// _plugins/food_shopping.rb resolves it from `serves:` first and each recipe's
// own `serves_estimate:` second (#815); an estimate is printed with a `~`.
//
// NOTHING IS ROUNDED TO ANYTHING COARSER THAN A GRAM -- Helen, 2026-09-07,
// asked directly whether the output should be tidied: "For now, don't
// tidy/round beyond 1 g precision", and then, to be sure it had been
// understood: "I mean don't round to 10 g or 5 g, round to 1g". So two thirds
// of 200 g is 133 g and not 130 g or 150 g. Spoons and counts keep their
// fractions instead, because ⅔ tsp is a real measure and 0.67 tsp is not a
// number anyone has a spoon for -- that is notation, not rounding, and
// `fractionText` is careful to print ⅔ only for exactly two thirds.
//
// A SUB-GRAM TOTAL KEEPS A DECIMAL rather than rounding to `0 g`, which is the
// one place the gram rule has to bend: a fifth of a gram of saffron is a real
// entry on a real list and `0 g` is a lie about it.
//
// -----------------------------------------------------------------------------
// RANGES AND TILDES SURVIVE THE ARITHMETIC
// -----------------------------------------------------------------------------
// `30–50 g` doubled is `60–100 g`, and `~2 tbsp` doubled is `~4 tbsp`. Both
// ends are carried and scaled independently, and an entry with no range simply
// has both ends equal, so a group mixing "50 g" with "30–50 g" totals to
// "80–100 g" without any branch. A range that collapses prints once.
//
// AN UNQUANTIFIED ENTRY IS COUNTED, NOT SUMMED -- `some` salt, and every
// ingredient of a magic-bag entry, which carries no amounts at all by design
// (MANUAL 4.3). This is shopping-list.js's own rule and the reason it is right
// here too: "salt (x3)" says three of the shortlisted dishes want salt, which
// is all anyone can honestly be told.
// =============================================================================

(function (root, factory) {
  /* Loaded the two ways shopping-list.js is. It is required FIRST because
     everything below is built on it, and every one of its helpers is read at
     module scope rather than on first use, so a page that loads them the wrong
     way round fails at startup instead of on the first shortlist toggle.
     tests/test_site_config.py::test_the_food_shopping_scripts_load_in_dependency_order
     guards the order in the template. */
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = factory(require('./shopping-list.js'));
  } else {
    root.HTF = root.HTF || {};
    root.HTF.foodShoppingList = factory(root.HTF.shoppingList);
  }
})(typeof window !== 'undefined' ? window : this, function (shoppingList) {
  'use strict';

  var foldKey = shoppingList.foldKey;
  var foldUnit = shoppingList.foldUnit;
  var unitLabel = shoppingList.unitLabel;
  var parseAmount = shoppingList.parseAmount;
  var splitParenthetical = shoppingList.splitParenthetical;
  var fractionText = shoppingList.fractionText;
  var tidy = shoppingList.tidy;

  /* THE UNITS THAT ARE MEASURED RATHER THAN COUNTED, and how finely each may
     be written. A gram is Helen's stated floor, so `g` and `ml` print whole;
     `kg` and `l` print to three places, which is the SAME precision expressed
     in a bigger unit rather than a looser rule. Everything absent from here --
     spoons, cloves, bunches, bare counts -- goes through `fractionText` and
     keeps its halves and thirds. */
  var DECIMALS = { g: 0, ml: 0, kg: 3, l: 3, cl: 1, oz: 1 };

  /* GRAMS AND MILLILITRES ARE THE ONLY UNITS TOTALLED IN, and the bigger ones
     are folded into them on the way in. `1½ l` of stock in one recipe and
     `500 ml` in another are 2 litres of the same stock, and without this they
     were two rows you had to add up yourself -- while a twelfth of the first
     printed as `0.125 l`, which is a real number nobody has ever shopped by.

     THIS IS NOT THE CONVERSION shopping-list.js REFUSES. That file's rule --
     "a group holding 45 ml and 2 dashes is `45 ml + 2 dashes`" -- is about
     units with no defined relationship, where a conversion would have to be
     invented: nobody can say how many millilitres a dash of Angostura is. A
     litre is a thousand millilitres by definition, on both sides of every
     recipe in the collection. Nothing is invented here, and `tbsp`, `oz`,
     `clove` and every bare count are left exactly where they were, because
     each of those WOULD need inventing.

     THE UNIT COMES BACK FOR DISPLAY. `displayUnit` below re-expresses a total
     of 1000 or more, so `1.333 kg` of beef stays kilograms and 83 g of pearl
     barley stops being 0.083 of one. */
  var CANONICAL = {
    kg: { unit: 'g', factor: 1000 },
    l: { unit: 'ml', factor: 1000 },
    litre: { unit: 'ml', factor: 1000 },
    cl: { unit: 'ml', factor: 10 }
  };

  var BIGGER = { g: { unit: 'kg', factor: 1000 }, ml: { unit: 'l', factor: 1000 } };

  /* Which unit a total should be SHOWN in, decided by its top end so that a
     range never straddles two units. Below a thousand it stays as it is. */
  function displayUnit(unit, quantity) {
    var bigger = BIGGER[unit];
    if (bigger && quantity >= bigger.factor) {
      return { unit: bigger.unit, factor: 1 / bigger.factor };
    }
    return { unit: unit, factor: 1 };
  }

  /* A PLURAL IS THE SAME SHOPPING AS ITS SINGULAR, and until this existed the
     list said so twice. Across the real collection: `onion` and `onions`,
     `carrot` and `carrots`, `lemon` and `lemons`, `garlic clove` and `garlic
     cloves`, `cinnamon stick` and `cinnamon sticks` are each two recipes
     writing one thing, and each printed two rows with two totals that you then
     had to add up yourself -- which is the one job this panel has.

     THE UNIT RULE, REUSED ON THE NAME. `foldUnit` already knows how to take a
     plural back to its singular, because `1 clove` and `3 cloves` of garlic
     had the identical problem one column to the left. Applying the same
     function rather than writing a second one means the two can never disagree
     about what `cloves` is, and it is `foldUnit(foldKey(name))` rather than
     either alone because foldKey owns the curly apostrophe ("goat's cheese")
     and foldUnit owns the plural.

     NOT `singulars` FROM _data/food/ingredient_words.yml, which is 29 declared
     words and none of the five above: that map exists so the ingredient SEARCH
     can match what you typed, and widening it to serve this would change what
     the search does to earn a fix for something else.

     A KEY, NEVER A LABEL. `hummus` folds to `hummu` and `tomatoes` to
     `tomatoe`, which are not words and are never shown to anybody -- the row
     is labelled with the first spelling an entry actually used. All a key has
     to be is the same for two things that are the same thing. */
  function foldName(name) {
    return foldUnit(foldKey(name));
  }

  function amountNumber(quantity, unit) {
    var places = DECIMALS[unit];
    if (places === undefined) return fractionText(quantity);

    var factor = Math.pow(10, places);
    var rounded = Math.round(quantity * factor) / factor;

    /* NEVER `0 g` FOR SOMETHING THAT IS THERE. A fifth of a gram of saffron
       survives as `0.2 g`; showing more precision than the floor is not the
       thing Helen ruled against, and printing zero for a real ingredient is. */
    if (rounded === 0 && quantity > 0) return String(tidy(quantity));
    return String(rounded);
  }

  /** "60–100 g", "133 g", "⅔ tsp", "~4 tbsp", "3 tbsp (18 g)".
   *
   * THE RAW SUM GOES TO `amountNumber`, NEVER `tidy()`'s version of it, and
   * that is not fussiness: `tidy` rounds to three decimals, which turns two
   * thirds into 0.667, and 0.667 is not within `fractionText`'s tolerance of
   * ⅔ -- so tidying first printed `3.33 carrots` where the answer is `3⅓`.
   * `tidy` is for the float noise in a SUM and for comparing the two ends;
   * deciding how a number is written is the other function's job, and it does
   * its own rounding.
   */
  function totalText(total) {
    var lo = tidy(total.lo);
    var hi = tidy(total.hi);

    // Chosen off the top end, so a range never straddles two units.
    var as = displayUnit(total.unit, hi);

    var number = amountNumber(total.lo * as.factor, as.unit);
    if (hi > lo) number += '–' + amountNumber(total.hi * as.factor, as.unit);

    var shown = unitLabel(as.unit, hi * as.factor);
    /* A UNIT THAT OPENS WITH PUNCTUATION IS JOINED, NOT SPACED. `2.5-cm piece`
       keeps its hyphen through the parser (see NUMBER's lookahead there), and
       "2.5 -cm piece" would be the only place that hyphen looked like a typo. */
    var text = !shown
      ? number
      : (/^[^a-z0-9]/.test(shown) ? number + shown : number + ' ' + shown);

    if (total.paren) {
      var pas = displayUnit(total.paren.unit, tidy(total.paren.hi));
      var plo = amountNumber(total.paren.lo * pas.factor, pas.unit);
      var phi = tidy(total.paren.hi);
      var pnumber = phi > tidy(total.paren.lo)
        ? plo + '–' + amountNumber(total.paren.hi * pas.factor, pas.unit)
        : plo;
      var punit = unitLabel(pas.unit, phi * pas.factor);
      text += ' (' + (punit ? pnumber + ' ' + punit : pnumber) + ')';
    }

    return total.approx ? '~' + text : text;
  }

  /**
   * Total up a shortlist of recipes, grouped by aisle.
   *
   * @param {Array} entries - one per ingredient of every shortlisted recipe:
   *        { amount: string, name: string, aisle: string, scale: number }
   *        `scale` is portions wanted over portions the recipe makes; absent
   *        or not a positive number means x1, which is also what a recipe with
   *        no resolved portion count gets.
   * @param {Object} [options]
   * @param {Array} [options.aisles] - [{key, label}] in the order they should
   *        appear. An aisle with nothing in it is not returned; an entry whose
   *        aisle is not in the list falls to the last one.
   * @returns {Array} [{ key, label, items: [{ label, text, totals,
   *        unquantified }] }]
   */
  function build(entries, options) {
    var opts = options || {};
    var aisles = opts.aisles && opts.aisles.length
      ? opts.aisles
      : [{ key: 'other', label: 'other' }];

    var known = {};
    aisles.forEach(function (a) { known[a.key] = true; });
    var fallback = aisles[aisles.length - 1].key;

    var groups = {};
    var order = [];

    (entries || []).forEach(function (entry) {
      if (!entry) return;
      var name = String(entry.name || '').trim();
      if (!name) return;

      var key = foldName(name);
      if (!groups[key]) {
        groups[key] = {
          /* THE LABEL IS THE FIRST SPELLING SEEN, the key is the folded one --
             shopping-list.js's own rule, and here it is what stops "Parma ham"
             and "parma ham", or "onion" and "onions", being two lines of the
             same shopping. Whichever recipe was shortlisted first names it. */
          label: name,
          aisle: null,
          units: {},
          unitOrder: [],
          unquantified: {},
          unquantifiedOrder: []
        };
        order.push(key);
      }
      var group = groups[key];

      /* THE FIRST AISLE WINS, and it cannot honestly be otherwise: the aisle
         is derived from the name at build time, so two entries sharing a
         folded name were given the same aisle by construction. This is here
         only so that a group formed before any aisle was seen still has one. */
      if (group.aisle === null) {
        group.aisle = known[entry.aisle] ? entry.aisle : fallback;
      }

      var scale = (typeof entry.scale === 'number' && entry.scale > 0)
        ? entry.scale : 1;

      var parsed = parseAmount(entry.amount);
      if (!parsed) {
        var text = String(entry.amount || '').trim();
        /* NO AMOUNT AT ALL IS STILL AN INGREDIENT. Every magic-bag item and
           100 of the 778 recipe items are written without one, and the line
           they earn is the name with a count beside it. `''` is the key those
           share, and it prints as nothing but the count. */
        if (group.unquantified[text] === undefined) {
          group.unquantified[text] = 0;
          group.unquantifiedOrder.push(text);
        }
        group.unquantified[text] += 1;
        return;
      }

      var split = splitParenthetical(parsed.unit);
      var written = split.lo === undefined ? parsed.unit : split.unit;

      // Kilograms and litres are totalled as grams and millilitres; see
      // CANONICAL, and note that nothing else is touched.
      var canon = CANONICAL[written];
      var unit = canon ? canon.unit : written;
      var factor = canon ? canon.factor : 1;

      if (group.units[unit] === undefined) {
        group.units[unit] = {
          unit: unit, lo: 0, hi: 0, approx: false, paren: null
        };
        group.unitOrder.push(unit);
      }
      var total = group.units[unit];

      var lo = parsed.quantity * scale * factor;
      var hi = (parsed.max === undefined ? parsed.quantity : parsed.max) * scale * factor;
      total.lo += lo;
      total.hi += hi;
      if (parsed.approx) total.approx = true;

      if (split.lo !== undefined) {
        var pcanon = CANONICAL[split.unit2];
        var punit = pcanon ? pcanon.unit : split.unit2;
        var pfactor = pcanon ? pcanon.factor : 1;
        if (!total.paren) {
          total.paren = { unit: punit, lo: 0, hi: 0 };
        }
        total.paren.lo += split.lo * scale * pfactor;
        total.paren.hi += (split.hi === null ? split.lo : split.hi) * scale * pfactor;
      }
    });

    var rows = order.map(function (key) {
      var group = groups[key];

      var totals = group.unitOrder.map(function (unit) {
        var total = group.units[unit];
        return {
          unit: unit,
          lo: tidy(total.lo),
          hi: tidy(total.hi),
          approx: total.approx,
          text: totalText(total)
        };
      });

      var unquantified = group.unquantifiedOrder.map(function (text) {
        return { text: text, recipes: group.unquantified[text] };
      });

      /* ONE STRING FOR THE WHOLE AMOUNT, built here and not in the template,
         so a row and any copy of it can never say different things -- the
         reason shopping-list.js builds its own `text` in the same place. */
      var parts = totals.map(function (t) { return t.text; })
        .concat(unquantified.map(function (u) {
          var count = u.recipes > 1 ? '×' + u.recipes : '';
          if (!u.text) return count;
          return u.recipes > 1 ? u.text + ' (×' + u.recipes + ')' : u.text;
        }).filter(Boolean));

      return {
        label: group.label,
        aisle: group.aisle || fallback,
        totals: totals,
        unquantified: unquantified,
        text: parts.join(' + ')
      };
    });

    /* ALPHABETICAL WITHIN THE AISLE, and that is a departure from the drinks
       list on purpose. There, Helen asked for descending volume: "the big
       pours are what you shop for". Here the aisle heading has already done
       that job -- you are standing in front of the vegetables -- and what is
       left is finding a name in a list of names, which wants an alphabet. It
       is also the only order available: a food aisle mixes grams, spoons,
       cloves and bare counts, and ranking 500 g against 2 cloves would need
       the conversion this codebase refuses to invent. */
    return aisles.map(function (aisle) {
      var items = rows.filter(function (row) { return row.aisle === aisle.key; })
        .sort(function (a, b) {
          return a.label.toLowerCase().localeCompare(b.label.toLowerCase());
        });
      return { key: aisle.key, label: aisle.label, items: items };
    }).filter(function (aisle) { return aisle.items.length > 0; });
  }

  return {
    build: build,
    totalText: totalText,
    amountNumber: amountNumber
  };
});
