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
  var DECIMALS = { g: 0, ml: 0, kg: 3, l: 3, cl: 1, oz: 1, cm: 1 };

  /* Kilograms, litres and centilitres fold into grams and millilitres by
     definition, so `1½ l` and `500 ml` of stock are one row. `displayUnit`
     re-expresses a total of a thousand or more. food-scale.js folds with this
     same table, so imperial measures are METRIC's, below, not this one's. */
  var CANONICAL = {
    kg: { unit: 'g', factor: 1000 },
    l: { unit: 'ml', factor: 1000 },
    litre: { unit: 'ml', factor: 1000 },
    cl: { unit: 'ml', factor: 10 }
  };

  /* Metric on the shopping list (#1462 D2): imperial measures total in
     grams, millilitres and centimetres, so 3 oz and 100 g of butter are one
     row. A table of its own, not CANONICAL, which the recipe page shares:
     a recipe keeps the unit it was written in. British measures, as the
     books are, except the cup, which only American recipes write. */
  var METRIC = {
    oz: { unit: 'g', factor: 28.3495 },
    lb: { unit: 'g', factor: 453.592 },
    'fl oz': { unit: 'ml', factor: 28.4131 },
    pint: { unit: 'ml', factor: 568.261 },
    cup: { unit: 'ml', factor: 240 },
    inch: { unit: 'cm', factor: 2.54 }
  };

  /* One spelling per unit on the shopping list (#1462 D3): how full a spoon
     is goes, so a heaped and a level tablespoon of flour are one row; a can
     is a tin; `×` is `x`, the form packUnit reads. */
  var SPOON_QUALIFIER = /^(?:slightly rounded|rounded|heaped|level|good|generous|large) (tsp|tbsp)$/;

  function shoppingUnit(unit) {
    return String(unit || '')
      .replace(/×/g, 'x')
      .replace(/(\d)-(g|ml)\b/g, '$1 $2')
      .replace(/^(tsp|tbsp), slightly rounded$/, '$1')
      .replace(SPOON_QUALIFIER, '$1')
      .replace(/(^| )can$/, '$1tin');
  }

  // A size standing in for a noun nobody writes: "2 large" counts the item.
  var SIZE_UNITS = { large: true, medium: true, small: true };

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

  // ⅛ tsp, the smallest spoon; tolerant of floating point, so ⅛ itself is a spoon.
  var PINCH_BELOW = 0.125 - 1e-9;

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

    /* Under ⅛ tsp is "a pinch" (#1462 C5): no spoon in the drawer measures
       it, and "0.06 tsp" is the arithmetic showing. */
    if (as.unit === 'tsp' && lo < PINCH_BELOW) {
      return hi < PINCH_BELOW ? 'a pinch' : 'a pinch to ' + amountNumber(total.hi, 'tsp') + ' tsp';
    }

    var number = amountNumber(total.lo * as.factor, as.unit);
    if (hi > lo) number += '–' + amountNumber(total.hi * as.factor, as.unit);

    var shown = unitLabel(as.unit, hi * as.factor);
    /* A unit that opens with punctuation is joined, not spaced: `2.5-cm
       piece` keeps its hyphen through the parser. */
    var text = !shown
      ? number
      : (/^[^a-z0-9]/.test(shown) ? number + shown : number + ' ' + shown);

    if (total.paren) text += ' ' + parenText(total.paren);

    return total.approx ? '~' + text : text;
  }

  /* The restating bracket, `{unit, lo, hi, about?}`, as "(about 12.5 g)". */
  function parenText(paren) {
    var pas = displayUnit(paren.unit, tidy(paren.hi));
    var plo = amountNumber(paren.lo * pas.factor, pas.unit);
    var phi = tidy(paren.hi);
    var pnumber = phi > tidy(paren.lo)
      ? plo + '–' + amountNumber(paren.hi * pas.factor, pas.unit)
      : plo;
    var punit = unitLabel(pas.unit, phi * pas.factor);
    return '(' + (paren.about ? 'about ' : '') +
      (punit ? pnumber + ' ' + punit : pnumber) + ')';
  }

  /* A stepped measure (handful, sprig, pinch) is bought in whole ones, rounded
     up (#1297). Where that differs from what the recipes ask for, the row
     carries an aside giving the asked-for amount as a fraction: "2 handfuls
     (1¼ in the recipes)". The asked-for amount is stepped as the recipe page
     steps it: `options.quarterMeasures` to the nearest quarter,
     `options.wholeMeasures` to the nearest half (half a pinch makes no sense
     in smaller parts). The TOTAL is stepped, once, never each recipe's share.
     With neither option, nothing is rounded. */
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

  function inHalves(quantity) {
    return Math.max(0.5, Math.round(tidy(quantity) * 2) / 2);
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
        // #1458. Resolved at build by _plugins/food_costs.rb; absent when
        // the page carries no costs.
        rate: entry.rate,
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

  /* "£11.34", or "£12.02 (£9.34–£14.70)" for a range: the midpoint, then the
     ends, as shopping-list.js prints a drink's. "from £3.10" where something
     is unpriced (#1458): the low end of what is known, since the rest costs
     more, so a midpoint would mislead. */
  function moneyText(cost) {
    var lo = '£' + Number(cost.min).toFixed(2);
    if (cost.partial) return 'from ' + lo;
    if (Math.abs(cost.max - cost.min) < 0.005) return lo;
    return '£' + ((Number(cost.min) + Number(cost.max)) / 2).toFixed(2) +
      ' (' + lo + '–£' + Number(cost.max).toFixed(2) + ')';
  }

  /* "2 x 400 g cans" totals as 2 of the unit `x 400 g can`: that is 400 g
     apiece, whatever the container is called. Read off the unit's own words
     so no can, tin or pack size needs a row in costs.yml. */
  var PACKED = /^x\s*(\d+(?:\.\d+)?)\s*(g|kg|ml|l)(?:\s|$)/;
  var PACKED_BASE = { g: ['g', 1], kg: ['g', 1000], ml: ['ml', 1], l: ['ml', 1000] };

  function packUnit(unit) {
    var m = PACKED.exec(String(unit || ''));
    if (!m) return null;
    var base = PACKED_BASE[m[2]];
    return [base[0], Number(m[1]) * base[1]];
  }

  /* What one row's totals cost (#1458). `rate` is GBP per base unit; `units`
     maps a unit to [family, factor] (_data/food/costs.yml). A unit the rate
     names itself wins; otherwise its family's rate, a weight and a volume
     standing in for each other at 1 g to 1 ml. Unquantified lines cost
     nothing, as on the cocktail list. Returns null where nothing could be
     priced, with `unpriced` saying whether something should have been. */
  function rowCost(totals, rate, units) {
    var min = 0;
    var max = 0;
    var priced = false;
    var unpriced = false;
    if (rate && rate.free) return { min: 0, max: 0, partial: false, free: true };

    totals.forEach(function (t) {
      var spec = units[t.unit] || packUnit(t.unit);
      var family = spec ? spec[0] : null;
      if (family === 'free') return;
      var per = null;
      var factor = 1;
      if (rate && rate[t.unit]) {
        per = rate[t.unit];
      } else if (rate && family) {
        per = rate[family] ||
          (family === 'g' ? rate.ml : null) ||
          (family === 'ml' ? rate.g : null);
        factor = spec[1];
      }
      if (!per) { unpriced = true; return; }
      min += t.lo * factor * per[0];
      max += t.hi * factor * per[1];
      priced = true;
    });

    if (!priced) return unpriced ? { unpriced: true } : null;
    return { min: min, max: max, partial: unpriced };
  }

  /** What a list of rows comes to (#1458): the priced rows summed, and how
   * many rows could not be priced, wholly or in part. null where no row was
   * priced at all. */
  function costTotal(rows) {
    var min = 0;
    var max = 0;
    var priced = 0;
    var unpriced = 0;
    (rows || []).forEach(function (row) {
      var cost = row && row.cost;
      if (!cost) return;
      if (cost.unpriced) { unpriced += 1; return; }
      min += cost.min;
      max += cost.max;
      priced += 1;
      if (cost.partial) unpriced += 1;
    });
    if (!priced) return null;
    var sum = { min: min, max: max, partial: unpriced > 0, unpriced: unpriced };
    sum.text = moneyText(sum);
    return sum;
  }

  /** One portion or one batch of a recipe as written (#1458): its own lines
   * at x1, costed and divided by `per` (its portions, or 1 for a batch). The
   * shortlist's line and the recipe page's cost line both call this, so the
   * two cannot disagree. null where nothing could be priced.
   * @param {Array} entries - the recipe's lines, as for build(), each with `rate`
   * @param {number} per - how many the recipe as written is divided into
   * @param {Object} options - as for build(); `costUnits` is required */
  function recipeCost(entries, per, options) {
    if (!options || !options.costUnits || !(per > 0)) return null;
    var rows = [];
    build(entries, options).forEach(function (aisle) { rows = rows.concat(aisle.items); });
    var sum = costTotal(rows);
    if (!sum) return null;
    var each = {
      min: sum.min / per, max: sum.max / per, partial: sum.partial, unpriced: sum.unpriced
    };
    each.text = moneyText(each);
    return each;
  }

  /** Total up a shortlist of recipes, grouped by aisle.
   * @param {Array} entries - { amount, name, aisle, scale, recipe? } per ingredient, plus the marks `reunite` reads
   * @param {Object} [options]
   * @param {Array} [options.wholeMeasures] - `half_step_measures` and `half_step_counts`, bought in whole ones
   * @param {Array} [options.quarterMeasures] - `quarter_step_measures`, bought in whole ones too
   * @param {Array} [options.countNouns] - `count_nouns` in scaling.yml: a row label may change number
   * @param {Array} [options.aisles] - [{key, label}] in display order; an unknown aisle falls to the last
   * @param {Object} [options.costUnits] - `units` from _data/food/costs.yml; absent, no row is costed
   * @returns {Array} [{ key, label, items: [{ key, label, text, aside, totals, unquantified, recipes, cost? }] }] */
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
          unscaledRecipes: [],
          recipes: [],
          // One name, one keyword, one rate: the first one met stands.
          rate: entry.rate || null
        };
        order.push(key);
      }
      var group = groups[key];
      if (group.spellings.indexOf(name) === -1) group.spellings.push(name);
      if (!group.rate && entry.rate) group.rate = entry.rate;
      if (entry.recipe !== undefined && entry.recipe !== null &&
          group.recipes.indexOf(entry.recipe) === -1) {
        group.recipes.push(entry.recipe);
      }

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
      var written = shoppingUnit(split.lo === undefined ? parsed.unit : split.unit);

      /* "400 g tin" is one 400 g tin: counted as `x 400 g tin`, the form
         "2 x 400 g tins" takes, so the two total together and packUnit can
         price them. A single noun only: "250 g per person" is a weight. */
      var pack = /^(g|ml) ([a-z]+)$/.exec(written);
      if (pack && parsed.max === undefined && split.lo === undefined) {
        written = 'x ' + tidy(parsed.quantity) + ' ' + pack[1] + ' ' + pack[2];
        parsed = { quantity: 1, unit: written, approx: parsed.approx };
      }

      // Kilograms and litres total as grams and millilitres (CANONICAL), and
      // imperial measures as metric (METRIC); nothing else is converted.
      var canon = CANONICAL[written] || METRIC[written];
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
        var pcanon = CANONICAL[split.unit2] || METRIC[split.unit2];
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
        // A unit on both lists steps in quarters.
        var step = (byQuarter && byQuarter.test(unit)) ? inQuarters
          : (byEye && byEye.test(unit)) ? inHalves : null;
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

      var row = {
        // The folded name: what a tick is stored under (#1457), and unlike the
        // label it does not change with the count.
        key: key,
        aside: asides.length ? asides.join(' + ') + ' in the recipes' : '',
        label: countedLabel(group, totals, unquantified, countNouns, byEye),
        aisle: group.aisle || fallback,
        totals: totals,
        unquantified: unquantified,
        // The `recipe` keys of the entries behind `unquantified`, for the
        // page to name beside the row.
        unscaledRecipes: group.unscaledRecipes,
        // Every `recipe` behind the row: a count change unticks it (#1457).
        recipes: group.recipes,
        text: parts.join(' + ')
      };
      if (opts.costUnits) {
        row.cost = rowCost(totals, group.rate, opts.costUnits);
        if (row.cost && !row.cost.unpriced && !row.cost.free) {
          row.cost.text = moneyText(row.cost);
        }
      }
      return row;
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
    costTotal: costTotal,
    moneyText: moneyText,
    recipeCost: recipeCost,
    totalText: totalText,
    parenText: parenText,
    amountNumber: amountNumber,
    CANONICAL: CANONICAL,
    METRIC: METRIC,
    shoppingUnit: shoppingUnit,
    SIZE_UNITS: SIZE_UNITS
  };
});
