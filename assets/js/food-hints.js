// The words behind an ingredient line's tap-to-open hint (MANUAL §8.2). No DOM.
//
// Two hints, both read from _data/food/ingredient_hints.yml, passed in:
//   stockHint  a stock line with a volume: how much of each product makes it
//   spiceHint  a ground spice in tsp or tbsp: its weight, to grind your own
// Each takes the amount AS SHOWN (scaled, or in metric) and the item's text,
// and returns { title, lines } or null. Loaded as a plain <script> attaching
// to window.HTF, and via require() for tests/js/food-hints.test.js.
(function (root, factory) {
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = factory(require('./shopping-list.js'),
                             require('./food-shopping-list.js'));
  } else {
    root.HTF = root.HTF || {};
    root.HTF.foodHints = factory(root.HTF.shoppingList, root.HTF.foodShoppingList);
  }
})(typeof window !== 'undefined' ? window : this, function (shoppingList, foodShoppingList) {
  'use strict';

  var parseAmount = shoppingList.parseAmount;
  var fractionText = shoppingList.fractionText;
  var unitLabel = shoppingList.unitLabel;
  var CANONICAL = foodShoppingList.CANONICAL;
  var METRIC = foodShoppingList.METRIC;

  function words(text) {
    return ' ' + String(text || '').toLowerCase().replace(/[^a-z&' ]+/g, ' ')
      .replace(/\s+/g, ' ').trim() + ' ';
  }

  function has(text, phrase) {
    return text.indexOf(' ' + phrase + ' ') !== -1;
  }

  function hasAny(text, phrases) {
    return (phrases || []).some(function (p) { return has(text, p); });
  }

  // A count of cubes, pots or spoons: the nearest half, never below a half.
  function half(n) {
    return Math.max(0.5, Math.round(n * 2) / 2);
  }

  function counted(n, unit) {
    return fractionText(n) + ' ' + unitLabel(unit, n);
  }

  /* The line's volume in ml, low and high, or null: ml, l, cl and the
     imperial volumes, which the shopping list's tables convert. */
  function volume(amount) {
    var parsed = parseAmount(String(amount || ''));
    if (!parsed) return null;
    var fold = CANONICAL[parsed.unit] || METRIC[parsed.unit] ||
      (parsed.unit === 'ml' ? { unit: 'ml', factor: 1 } : null);
    if (!fold || fold.unit !== 'ml') return null;
    var hi = parsed.max === undefined ? parsed.quantity : parsed.max;
    return { lo: parsed.quantity * fold.factor, hi: hi * fold.factor };
  }

  function mlText(ml) {
    return ml >= 1000 ? fractionText(Math.round(ml / 10) / 100) + ' litres'
      : Math.round(ml) + ' ml';
  }

  var SPOONS = { tsp: 1, tbsp: 3 };
  var QUALIFIER = /^(?:level|heaped|rounded|slightly rounded|good|generous|scant) /;

  function stockHint(amount, item, data) {
    var stock = data && data.stock;
    if (!stock) return null;
    var text = words(item);
    if (!has(text, 'stock') || hasAny(text, stock.not_stock)) return null;
    var ml = volume(amount);
    if (!ml) return null;

    var flavour = null;
    var first = text.length;
    stock.flavours.forEach(function (f) {
      var at = text.indexOf(' ' + f + ' ');
      if (at !== -1 && at < first) { first = at; flavour = f; }
    });
    // "beef or venison stock" is beef; "lamb stock" alone has no product.
    if (!flavour && hasAny(text, stock.other_flavours)) return null;

    var lines = [];
    stock.products.forEach(function (product) {
      var per = flavour ? product.flavours[flavour]
        : product.flavours[Object.keys(product.flavours)[0]];
      if (!per) return;
      var lo = half(ml.lo / per);
      var hi = half(ml.hi / per);
      var n = hi > lo ? fractionText(lo) + '–' + fractionText(hi) : fractionText(lo);
      var unit = unitLabel(product.unit, hi);
      // "2 tsp Marigold bouillon", but "2½ Oxo cubes".
      lines.push(SPOONS[product.unit.replace(QUALIFIER, '')]
        ? n + ' ' + unit + ' ' + product.name
        : n + ' ' + product.name + ' ' + unit);
    });
    if (!lines.length) return null;
    var water = ml.hi > ml.lo && ml.hi < 1000
      ? Math.round(ml.lo) + '–' + mlText(ml.hi)
      : ml.hi > ml.lo ? mlText(ml.lo) + '–' + mlText(ml.hi) : mlText(ml.lo);
    return { title: 'In ' + water + ' of boiling water:', lines: lines };
  }

  function spiceFor(text, spices) {
    for (var i = 0; i < spices.length; i += 1) {
      var spice = spices[i];
      if (hasAny(text, spice.match) && !hasAny(text, spice.unless)) return spice;
    }
    return null;
  }

  function grams(g) {
    return (g < 10 ? Math.round(g * 10) / 10 : Math.round(g)) + ' g';
  }

  function spiceHint(amount, item, data) {
    var spices = data && data.spices;
    if (!spices) return null;
    var parsed = parseAmount(String(amount || ''));
    if (!parsed) return null;
    var spoon = SPOONS[parsed.unit.replace(QUALIFIER, '')];
    if (!spoon) return null;
    var text = words(item);
    // "1 tsp each cumin and turmeric": the amount is not one spice's.
    if (has(text, 'each') || has(words(amount), 'each')) return null;
    var spice = spiceFor(text, spices);
    if (!spice) return null;
    var others = spices.filter(function (s) {
      return s !== spice && hasAny(text, s.match) && !hasAny(text, s.unless);
    });
    if (others.length) return null;

    var hi = parsed.max === undefined ? parsed.quantity : parsed.max;
    var tspLo = parsed.quantity * spoon;
    var tspHi = hi * spoon;
    var weight = tspHi > tspLo
      ? grams(tspLo * spice.g_per_tsp).replace(' g', '') + '–' + grams(tspHi * spice.g_per_tsp)
      : grams(tspLo * spice.g_per_tsp);
    var lines = [];
    if (spice.whole) lines.push('Grinding your own? Weigh ' + weight + ' of ' + spice.whole + '.');
    if (spice.per_whole_tsp) {
      var part = Math.max(0.25, Math.round(tspHi / spice.per_whole_tsp * 4) / 4);
      var nutmegs = part < 1 ? fractionText(part) + ' a nutmeg'
        : part === 1 ? 'a whole nutmeg' : fractionText(part) + ' nutmegs';
      lines.push('That is about ' + nutmegs + ', grated.');
    }
    if (spice.fresh_tbsp_per_tsp) {
      lines.push('Or ' + counted(half(tspHi * spice.fresh_tbsp_per_tsp), 'tbsp') +
        ' finely grated fresh ginger.');
    }
    return { title: 'About ' + weight + '.', lines: lines };
  }

  return { stockHint: stockHint, spiceHint: spiceHint, volume: volume };
});
