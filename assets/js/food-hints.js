// The words behind an ingredient line's tap-to-open hint (MANUAL §8.2). No DOM.
//
// Five hints, all read from _data/food/ingredient_hints.yml, passed in:
//   stockHint       a stock line with a volume: how much of each product
//   spiceHint       a ground spice by the spoon: its weight
//   wholeSpiceHint  a whole spice: its weight and the ground spoonfuls
//   vanillaHint     paste, pod or extract: the other two
//   pasteHint       fresh root, cloves or stalks: the paste, and back
// Each takes the amount AS SHOWN (scaled, or in metric) and the item's text,
// and returns { title, rows, lines } or null: rows are { amount, what } pairs,
// lines are sentences. Loaded as a plain <script> attaching
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

    /* A row is { amount, what }: "2 level tsp" and "Marigold bouillon", but
       "2½" and "Oxo cubes", so a spoon is measured and a cube is counted. */
    var rows = [];
    stock.products.forEach(function (product) {
      var per = flavour ? product.flavours[flavour]
        : product.flavours[Object.keys(product.flavours)[0]];
      if (!per) return;
      var lo = half(ml.lo / per);
      var hi = half(ml.hi / per);
      var n = hi > lo ? fractionText(lo) + '–' + fractionText(hi) : fractionText(lo);
      var unit = unitLabel(product.unit, hi);
      rows.push(SPOONS[product.unit.replace(QUALIFIER, '')]
        ? { amount: n + ' ' + unit, what: product.name }
        : { amount: n, what: product.name + ' ' + unit });
    });
    if (!rows.length) return null;
    var water = ml.hi > ml.lo && ml.hi < 1000
      ? Math.round(ml.lo) + '–' + mlText(ml.hi)
      : ml.hi > ml.lo ? mlText(ml.lo) + '–' + mlText(ml.hi) : mlText(ml.lo);
    return { title: 'In ' + water + ' of boiling water:', rows: rows, lines: [] };
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
    return { title: 'About ' + weight + '.', rows: [], lines: lines };
  }

  function span(lo, hi) {
    return hi > lo ? fractionText(lo) + '–' + fractionText(hi) : fractionText(lo);
  }

  function quarter(n) {
    return Math.max(0.25, Math.round(n * 4) / 4);
  }

  // Teaspoons, or from 6 tsp tablespoons to the nearest half.
  function spoons(lo, hi) {
    return hi >= 6 ? span(half(lo / 3), half(hi / 3)) + ' tbsp' : span(lo, hi) + ' tsp';
  }

  /* A whole spice: its weight, and the ground spoonfuls it grinds to. Seeds
     come by the spoon (`whole.g_per_tsp`), a nutmeg is counted
     (`whole.g_each`, grating to `per_whole_tsp` each). */
  function wholeSpiceHint(amount, item, data) {
    var spices = data && data.spices;
    if (!spices) return null;
    var text = words(item);
    if (has(text, 'each') || has(words(amount), 'each')) return null;
    var hits = spices.filter(function (s) {
      return s.whole && hasAny(text, s.whole.match) && !hasAny(text, s.whole.unless);
    });
    if (hits.length !== 1) return null;
    var spice = hits[0];
    var parsed = parseAmount(String(amount || ''));
    if (!parsed) return null;
    var hi = parsed.max === undefined ? parsed.quantity : parsed.max;
    var g, ground;
    if (spice.whole.g_per_tsp) {
      var spoon = SPOONS[parsed.unit.replace(QUALIFIER, '')];
      if (!spoon) return null;
      g = [parsed.quantity * spoon * spice.whole.g_per_tsp, hi * spoon * spice.whole.g_per_tsp];
      ground = [quarter(g[0] / spice.g_per_tsp), quarter(g[1] / spice.g_per_tsp)];
    } else {
      if (parsed.unit) return null;
      g = [parsed.quantity * spice.whole.g_each, hi * spice.whole.g_each];
      ground = [quarter(parsed.quantity * spice.per_whole_tsp), quarter(hi * spice.per_whole_tsp)];
    }
    var weight = g[1] > g[0] ? grams(g[0]).replace(' g', '') + '–' + grams(g[1]) : grams(g[0]);
    return {
      title: 'About ' + weight + ', or ' + spoons(ground[0], ground[1]) + ' ground ' + spice.name + '.',
      rows: [],
      lines: []
    };
  }

  var COUNTED = ['', 'small', 'medium', 'large', 'fat', 'plump', 'clove', 'cloves',
    'stalk', 'stalks', 'stick', 'sticks'];

  /* Fresh and paste, each way round, from `pastes`. Fresh root is measured
     in cm (an inch is 2.54); garlic and lemongrass are counted. */
  function pasteHint(amount, item, data) {
    var pastes = data && data.pastes;
    if (!pastes) return null;
    var text = words(item);
    var parsed = parseAmount(String(amount || ''));
    if (!parsed) return null;
    var lo = parsed.quantity;
    var hi = parsed.max === undefined ? parsed.quantity : parsed.max;
    var unit = parsed.unit.replace(/ piece$/, '');
    for (var i = 0; i < pastes.length; i += 1) {
      var p = pastes[i];
      if (hasAny(text, p.paste)) {
        // "garlic and ginger paste" is two pastes in one spoon: no figure fits.
        var named = pastes.filter(function (q) { return has(text, q.name); });
        if (named.length > 1) return null;
        var spoon = SPOONS[unit.replace(QUALIFIER, '')];
        if (!spoon) return null;
        var fLo = half(lo * spoon / p.tsp_per[1]);
        var fHi = half(hi * spoon / p.tsp_per[0]);
        if (p.fresh === 'cm') {
          return { title: 'Or a ' + span(fLo, fHi) + ' cm piece of ' + p.fresh_name + '.', rows: [], lines: [] };
        }
        return { title: 'Or ' + span(fLo, fHi) + ' ' + p.unit[fHi > 1 ? 1 : 0] + '.', rows: [], lines: [] };
      }
      if (hasAny(text, p.fresh_match) && !hasAny(text, p.fresh_unless)) {
        var n;
        if (p.fresh === 'cm') {
          var per = unit === 'cm' ? 1 : (unit === 'inch' || unit === 'inches') ? 2.54 : 0;
          if (!per) return null;
          n = [lo * per, hi * per];
        } else {
          if (COUNTED.indexOf(unit) === -1) return null;
          n = [lo, hi];
        }
        return {
          title: 'Or ' + spoons(half(n[0] * p.tsp_per[0]), half(n[1] * p.tsp_per[1])) + ' ' + p.name + ' paste.',
          rows: [],
          lines: []
        };
      }
    }
    return null;
  }

  /* The form a line is in is the first one it names: "1 vanilla pod, or 1 tsp
     paste" is a pod. A phrase inside a longer one does not count, so "vanilla
     bean paste" names paste and not "vanilla bean". */
  function vanillaForms(text, forms) {
    var found = [];
    forms.forEach(function (form) {
      form.match.forEach(function (phrase) {
        var at = text.indexOf(' ' + phrase + ' ');
        if (at !== -1) found.push({ form: form, at: at, end: at + phrase.length });
      });
    });
    found.sort(function (a, b) { return (b.end - b.at) - (a.end - a.at); });
    var kept = found.filter(function (m, i) {
      return !found.slice(0, i).some(function (k) { return m.at < k.end && k.at < m.end; });
    });
    if (!kept.length) return null;
    kept.sort(function (a, b) { return a.at - b.at; });
    var named = [];
    kept.forEach(function (m) { if (named.indexOf(m.form) === -1) named.push(m.form); });
    return { form: kept[0].form, named: named };
  }

  function vanillaText(form, pods) {
    if (form.unit === 'pod') {
      var n = half(pods * form.per_pod);
      return fractionText(n) + ' ' + form.name + (n > 1 ? 's' : '');
    }
    return fractionText(Math.round(pods * form.per_pod * 4) / 4 || 0.25) + ' tsp ' + form.name;
  }

  function vanillaHint(amount, item, data) {
    var vanilla = data && data.vanilla;
    if (!vanilla) return null;
    var text = words(item);
    // `or paste` alone would catch "tamarind concentrate or paste".
    if (!has(text, 'vanilla') || hasAny(text, vanilla.unless)) return null;
    var found = vanillaForms(text, vanilla.forms);
    if (!found) return null;
    var parsed = parseAmount(String(amount || ''));
    if (!parsed) return null;
    var hi = parsed.max === undefined ? parsed.quantity : parsed.max;
    var pods;
    if (found.form.unit === 'pod') {
      if (parsed.unit) return null;
      pods = hi / found.form.per_pod;
    } else {
      var spoon = SPOONS[parsed.unit.replace(QUALIFIER, '')];
      if (!spoon) return null;
      pods = hi * spoon / found.form.per_pod;
    }
    var others = vanilla.forms.filter(function (f) { return found.named.indexOf(f) === -1; });
    if (!others.length) return null;
    return {
      title: 'Or ' + others.map(function (f) { return vanillaText(f, pods); }).join(', or ') + '.',
      rows: [],
      lines: []
    };
  }

  return {
    stockHint: stockHint, spiceHint: spiceHint, wholeSpiceHint: wholeSpiceHint,
    pasteHint: pasteHint, vanillaHint: vanillaHint, volume: volume
  };
});
