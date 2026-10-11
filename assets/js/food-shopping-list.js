// What a shortlist of recipes adds up to, by aisle (#801). No DOM.
//
// Pure, and loaded two ways: as a plain <script> attaching to window.HTF, and
// via require() for tests/js/food-shopping-list.test.js. filters.js is the
// DOM half. The amount parsing is shopping-list.js's: there is one parser.
//
// Each entry arrives with a `scale` (portions wanted over portions made, or
// whole batches); filters.js chooses it and this file only multiplies.
//
// Nothing is rounded coarser than a gram: two thirds of 200 g is 133 g.
// Spoons and counts keep cook's fractions. A sub-gram total keeps a decimal
// rather than printing `0 g`. Ranges and tildes survive the arithmetic:
// `30–50 g` doubled is `60–100 g`. An entry with no amount is counted, not
// summed.

(function (root, factory) {
  /* shopping-list.js must load first: its helpers are read at module scope, so
     the wrong order fails at startup rather than on the first toggle
     (test_the_food_shopping_scripts_load_in_dependency_order). */
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

  /* Decimal places for the measured units: `g` and `ml` print whole, `kg` and
     `l` to three places (the same precision in a bigger unit). Any unit absent
     from here goes through `fractionText`. */
  var DECIMALS = { g: 0, ml: 0, kg: 3, l: 3, cl: 1, oz: 1 };

  /* Grams and millilitres are the only units totalled in; kilograms, litres
     and centilitres fold into them by definition, so `1½ l` and `500 ml` of
     stock are one row. Nothing else is converted. `displayUnit` re-expresses
     a total of a thousand or more. */
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

  /* The grouping key for a name: `onion` and `onions` are one row. foldKey
     owns the curly apostrophe and foldUnit the plural. A key, never a label:
     `hummus` folds to `hummu`, which is never shown. */
  function foldName(name) {
    return foldUnit(foldKey(name));
  }

  function amountNumber(quantity, unit) {
    var places = DECIMALS[unit];
    if (places === undefined) return fractionText(quantity);

    var factor = Math.pow(10, places);
    var rounded = Math.round(quantity * factor) / factor;

    // Never `0 g` for something that is there: 0.2 g of saffron prints so.
    if (rounded === 0 && quantity > 0) return String(tidy(quantity));
    return String(rounded);
  }

  /** "60–100 g", "133 g", "⅔ tsp", "~4 tbsp", "3 tbsp (18 g)".
   *
   * The raw sum goes to `amountNumber`, never `tidy()`'s version of it: tidy
   * turns two thirds into 0.667, which is outside `fractionText`'s tolerance
   * of ⅔. `tidy` is only for comparing the two ends.
   */
  function totalText(total) {
    var lo = tidy(total.lo);
    var hi = tidy(total.hi);

    // Chosen off the top end, so a range never straddles two units.
    var as = displayUnit(total.unit, hi);

    var number = amountNumber(total.lo * as.factor, as.unit);
    if (hi > lo) number += '–' + amountNumber(total.hi * as.factor, as.unit);

    var shown = unitLabel(as.unit, hi * as.factor);
    /* A unit that opens with punctuation is joined, not spaced: `2.5-cm
       piece` keeps its hyphen through the parser. */
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

  /* A stepped measure (handful, sprig, pinch) is bought in whole ones, rounded
     up (#1297). Where that differs from what the recipes ask for, the row
     carries an aside giving the asked-for amount to the nearest quarter, as a
     fraction: "2 handfuls (1¼ in the recipes)". The TOTAL is stepped, once,
     never each recipe's share. `options.wholeMeasures` and
     `options.quarterMeasures` are treated alike here; with neither, nothing
     is rounded. */
  function wholeMeasurePattern(measures) {
    var words = (measures || [])
      .map(function (m) { return String(m).trim().toLowerCase(); })
      .filter(function (m) { return m !== ''; })
      .map(function (m) { return m.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); })
      .join('|');
    // A WHOLE WORD, singular or plural, anywhere in the unit: `handful`,
    // `small handfuls`, `pinches`. `dashi` and `handfulness` are not caught.
    return words ? new RegExp('(^|[^a-z])(' + words + ')(?:e?s)?(?![a-z])', 'i') : null;
  }

  function inQuarters(quantity) {
    return Math.max(0.25, Math.round(tidy(quantity) * 4) / 4);
  }

  /* Lines that belong together inside ONE recipe, never across two (#1297);
     _plugins/food_shopping.rb marks them. A count written inside an item
     ("juice of 1 lemon") arrives as `fruit` and `count`. Different parts of
     one fruit are the same fruit: each part is summed, the part needing the
     most decides, and lines not using it are dropped; a line naming no part
     is always added. A `pointer` line ("the rest of the oil above") is
     dropped when another line of that name stands beside it. An entry with
     no `recipe` is never merged. */
  function reunite(entries) {
    var list = [];
    var byRecipe = {};

    (entries || []).forEach(function (entry) {
      if (!entry) return;
      var name = String(entry.fruit || entry.name || '').trim();
      if (!name) return;
      var item = {
        amount: entry.fruit ? entry.count : entry.amount,
        name: name,
        aisle: entry.aisle,
        scale: entry.scale,
        // Carried through for build(), which names it beside an unscaled row.
        recipe: entry.recipe,
        parts: Array.isArray(entry.parts) ? entry.parts : [],
        pointer: !!entry.pointer,
        drop: false
      };
      list.push(item);
      if (entry.recipe === undefined || entry.recipe === null) return;
      var key = String(entry.recipe) + '\u0000' + foldName(name);
      (byRecipe[key] = byRecipe[key] || []).push(item);
    });

    Object.keys(byRecipe).forEach(function (key) {
      var lines = byRecipe[key];

      var pointed = lines.filter(function (l) { return !l.pointer; });
      if (pointed.length) {
        lines.forEach(function (l) { if (l.pointer) l.drop = true; });
      }

      var counted = pointed.filter(function (l) {
        if (!l.parts.length) return false;
        l.parsed = parseAmount(l.amount);
        return !!l.parsed;
      });
      if (counted.length < 2) return;

      var needs = {};
      var order = [];
      counted.forEach(function (l) {
        var most = l.parsed.max === undefined ? l.parsed.quantity : l.parsed.max;
        l.parts.forEach(function (part) {
          if (needs[part] === undefined) { needs[part] = 0; order.push(part); }
          needs[part] += most;
        });
      });
      // The first part named wins a tie, so the row keeps the first line's words.
      var deciding = order.reduce(function (best, part) {
        return needs[part] > needs[best] + 1e-9 ? part : best;
      }, order[0]);
      counted.forEach(function (l) {
        if (l.parts.indexOf(deciding) === -1) l.drop = true;
      });
    });

    return list.filter(function (l) { return !l.drop; });
  }

  /* The row label agrees with a bare count: "2 lemons", "½ lemon" (#1297).
     Only a row that is one bare or size-only count, with nothing unquantified
     beside it. A spelling a recipe used is tried first; a form no recipe
     wrote is made only for a noun in `options.countNouns` (`count_nouns` in
     _data/food/scaling.yml), because the last word of a name is often not
     the counted noun. Left as written otherwise, and where the name is a
     choice or a phrase. */
  var SIZE_UNITS = { large: true, medium: true, small: true };

  function isPluralName(name) {
    var key = foldKey(name);
    return foldUnit(key) !== key;
  }

  function countedLabel(group, totals, unquantified, countNouns, byEye) {
    var label = group.label;
    if (totals.length !== 1 || unquantified.length) return label;
    // "pinch cayenne chilli pepper": the count is of pinches, not of peppers.
    if (byEye && byEye.test(label.split(' ')[0])) return label;
    var total = totals[0];
    if (total.unit !== '' && !SIZE_UNITS[total.unit]) return label;
    if (/\s(?:or|and|of|in|for|with)\s|\//i.test(label)) return label;

    var many = total.hi > 1;
    if (isPluralName(label) === many) return label;

    var used = group.spellings.filter(function (s) {
      return isPluralName(s) === many;
    })[0];
    if (used) return used;

    var words = label.split(' ');
    var noun = words[words.length - 1];
    var single = many ? noun : foldUnit(noun);
    if (!countNouns[single]) return label;
    if (many) return unitLabel(label, 2);
    words[words.length - 1] = single;
    return words.join(' ');
  }

  /**
   * Total up a shortlist of recipes, grouped by aisle.
   *
   * @param {Array} entries - one per ingredient of every shortlisted recipe:
   *        { amount: string, name: string, aisle: string, scale: number,
   *          recipe?: string, parts?: string[], fruit?: string,
   *          count?: string, pointer?: boolean }
   *        `scale` is portions wanted over portions the recipe makes; absent
   *        or not a positive number means x1, which is also what a recipe with
   *        no resolved portion count gets. `recipe` says which lines share a
   *        recipe, and the last four are _plugins/food_shopping.rb's marks --
   *        see `reunite` above.
   * @param {Object} [options]
   * @param {Array} [options.wholeMeasures] - half-step measures, bought in
   *        whole ones: `half_step_measures` and `half_step_counts`.
   * @param {Array} [options.quarterMeasures] - quarter-step measures, bought
   *        in whole ones too: `quarter_step_measures`.
   * @param {Array} [options.countNouns] - nouns bought by count, whose row
   *        label may be made plural or singular: `count_nouns` in scaling.yml.
   * @param {Array} [options.aisles] - [{key, label}] in the order they should
   *        appear. An aisle with nothing in it is not returned; an entry whose
   *        aisle is not in the list falls to the last one.
   * @returns {Array} [{ key, label, items: [{ label, text, aside, totals,
   *        unquantified }] }] -- `aside` is "1¼ in the recipes" where the
   *        amount was rounded up to a whole one, and '' otherwise
   */
  function build(entries, options) {
    var opts = options || {};
    var aisles = opts.aisles && opts.aisles.length
      ? opts.aisles
      : [{ key: 'other', label: 'other' }];

    var known = {};
    aisles.forEach(function (a) { known[a.key] = true; });
    var fallback = aisles[aisles.length - 1].key;

    var byEye = wholeMeasurePattern(opts.wholeMeasures);
    var byQuarter = wholeMeasurePattern(opts.quarterMeasures);
    var countNouns = {};
    (opts.countNouns || []).forEach(function (noun) {
      countNouns[String(noun).trim().toLowerCase()] = true;
    });

    var groups = {};
    var order = [];

    reunite(entries).forEach(function (entry) {
      var name = entry.name;

      var key = foldName(name);
      if (!groups[key]) {
        groups[key] = {
          // The label is the first spelling seen; the key is the folded one.
          label: name,
          // Every spelling used, for `countedLabel`: "lemon", then "lemons".
          spellings: [],
          aisle: null,
          units: {},
          unitOrder: [],
          unquantified: {},
          unquantifiedOrder: [],
          unscaledRecipes: []
        };
        order.push(key);
      }
      var group = groups[key];
      if (group.spellings.indexOf(name) === -1) group.spellings.push(name);

      /* The first aisle wins: the aisle is derived from the name at build
         time, so entries sharing a folded name share an aisle. */
      if (group.aisle === null) {
        group.aisle = known[entry.aisle] ? entry.aisle : fallback;
      }

      var scale = (typeof entry.scale === 'number' && entry.scale > 0)
        ? entry.scale : 1;

      var parsed = parseAmount(entry.amount);
      if (!parsed) {
        var text = String(entry.amount || '').trim();
        /* No amount at all is still an ingredient: counted under `''`, which
           prints as nothing but the count. */
        if (group.unquantified[text] === undefined) {
          group.unquantified[text] = 0;
          group.unquantifiedOrder.push(text);
        }
        group.unquantified[text] += 1;
        // Which recipes the unscaled line came from, each once, in order met.
        if (entry.recipe && group.unscaledRecipes.indexOf(entry.recipe) === -1) {
          group.unscaledRecipes.push(entry.recipe);
        }
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

      var usedUnit = {};
      var totals = group.unitOrder.map(function (unit) {
        var total = group.units[unit];
        // A stepped measure is bought in whole ones, rounded up from what
        // the recipes ask for; see the note above `wholeMeasurePattern`.
        var step = ((byEye && byEye.test(unit)) ||
          (byQuarter && byQuarter.test(unit))) ? inQuarters : null;
        var used = null;
        if (step) {
          var usedLo = step(total.lo);
          var usedHi = step(total.hi);
          total.lo = Math.ceil(usedLo);
          total.hi = Math.ceil(usedHi);
          if (usedLo !== total.lo || usedHi !== total.hi) {
            used = fractionText(usedLo) +
              (usedHi > usedLo ? '–' + fractionText(usedHi) : '');
            usedUnit[unit] = unitLabel(unit, usedHi);
          }
        }
        return {
          used: used,
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

      /* One string for the whole amount, built here and not in the caller, so
         a row and any copy of it cannot say different things. */
      var parts = totals.map(function (t) { return t.text; })
        .concat(unquantified.map(function (u) {
          var count = u.recipes > 1 ? '×' + u.recipes : '';
          if (!u.text) return count;
          return u.recipes > 1 ? u.text + ' (×' + u.recipes + ')' : u.text;
        }).filter(Boolean));

      /* "(1¼ in the recipes)". The unit is said only when the row has more
         than one total to tell apart: "2 sprigs + 10 g thyme (1¼ sprigs in the
         recipes)". */
      var asides = totals.filter(function (t) { return t.used; })
        .map(function (t) {
          return totals.length > 1 ? t.used + ' ' + usedUnit[t.unit] : t.used;
        });

      return {
        aside: asides.length ? asides.join(' + ') + ' in the recipes' : '',
        label: countedLabel(group, totals, unquantified, countNouns, byEye),
        aisle: group.aisle || fallback,
        totals: totals,
        unquantified: unquantified,
        // The `recipe` keys of the entries behind `unquantified`, for the
        // page to name beside the row.
        unscaledRecipes: group.unscaledRecipes,
        text: parts.join(' + ')
      };
    });

    /* Alphabetical within the aisle: an aisle mixes grams, spoons and counts,
       and ranking across them would need a conversion. */
    return aisles.map(function (aisle) {
      // Sorted on the FOLDED name, so "lemon" becoming "lemons" moves nothing.
      var items = rows.filter(function (row) { return row.aisle === aisle.key; })
        .sort(function (a, b) {
          return foldName(a.label).localeCompare(foldName(b.label));
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
