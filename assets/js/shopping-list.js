// Shopping list: what a shortlist of drinks adds up to (#546). No DOM.
//
// Pure, and loaded two ways: as a plain <script> attaching to window.HTF, and
// via require() for tests/js/shopping-list.test.js. cocktail-index.js is the
// DOM half; scale.js, food-shopping-list.js and food-scale.js reuse the
// amount parser, which is the only one in the repo.
//
// A row is one GENERIC, as the drink wrote it (never the shortened
// `card_names` form); the bottles named for it follow in brackets, as on the
// drink page. Grouping by bottle would print one line per spelling.
//
// Totals are per unit and never converted: 45 ml and 2 dashes is
// "45 ml + 2 dashes". An amount with no number is counted per drink, not
// summed, unless `top_up_ml` in costs.yml declares a volume for it (#746).

(function (root) {
  'use strict';

  /** Anything YAML gave us as scalar-or-list-or-nothing, as a list. */
  function asList(value) {
    if (value === null || value === undefined || value === '') return [];
    return Array.isArray(value) ? value : [value];
  }

  /* A generic written as a list means "either would do" (#441): one line and
     one key, joined with " or ". */
  function joined(value) {
    return asList(value).map(function (v) { return String(v).trim(); })
      .filter(Boolean).join(' or ');
  }

  /* The grouping key, never shown: case, spacing and the curly apostrophe must
     not split a group. Labels are built from an entry's own text. */
  function foldKey(text) {
    return String(text || '')
      .replace(/’/g, "'")
      .trim()
      .toLowerCase()
      .replace(/\s+/g, ' ');
  }

  /* Irregular plurals, folded to the singular so `dash` and `dashes` total as
     one. The empty unit is a bare count and stays empty. */
  var UNIT_PLURALS = { dashes: 'dash', drops: 'drop', cubes: 'cube', leaves: 'leaf' };

  /* The last word of a unit is the noun being counted (`2 heaped tbsp`,
     `2 x 400 g cans`); the words before it never change. A parenthetical is
     not a word: splitParenthetical takes it off first. */
  function lastWord(unit) {
    var parts = String(unit).split(' ');
    return parts[parts.length - 1];
  }

  function replaceLastWord(unit, word) {
    var parts = String(unit).split(' ');
    parts[parts.length - 1] = word;
    return parts.join(' ');
  }

  /* Plural unit to singular, so `1 clove` and `3 cloves` total on one line.
     Must round-trip with unitLabel, which puts the plural back for display.
     `ss` (`glass`) and short symbols are not plurals. */
  function foldUnit(unit) {
    var u = String(unit || '').trim().toLowerCase().replace(/\s+/g, ' ');
    if (UNIT_PLURALS[u]) return UNIT_PLURALS[u];

    var word = lastWord(u);
    if (UNIT_PLURALS[word]) return replaceLastWord(u, UNIT_PLURALS[word]);
    if (SYMBOL_UNITS[word] || word.length < 3) return u;
    if (/(ch|sh|s|x|z)es$/.test(word)) return replaceLastWord(u, word.slice(0, -2));
    if (/[^s]s$/.test(word)) return replaceLastWord(u, word.slice(0, -1));
    return u;
  }

  /* Units that never take a plural: symbols (`ml`, `tbsp`), `each`, the bare
     count, and the size adjectives standing in for a noun ("4 medium"). Words
     that do pluralise are absent on purpose; unitLabel's rule handles them. */
  var SYMBOL_UNITS = {
    ml: true, g: true, cl: true, l: true, oz: true, each: true, '': true,
    kg: true, tsp: true, tbsp: true, cm: true, mm: true,
    large: true, small: true, medium: true
  };

  function unitLabel(unit, quantity) {
    if (SYMBOL_UNITS[unit]) return unit;
    if (quantity === 1) return unit;

    /* Must agree with foldUnit or a unit will not survive the round trip:
       `x 400 g can` prints `x 400 g cans`, `heaped tbsp` prints unchanged. */
    var word = lastWord(unit);
    if (SYMBOL_UNITS[word]) return unit;

    // `leaf` -> `leaves`, the one unit here that does not take a suffix.
    if (/f$/.test(word)) return replaceLastWord(unit, word.replace(/f$/, 'ves'));
    if (word !== unit) return replaceLastWord(unit, pluralise(word));

    // A rule, not a list of units: a sibilant takes `es` (`dashes`).
    return pluralise(unit);
  }

  /* A count of whole fruit prints in words: `half`, `quarter`, `1½ whole`,
     never "0.5 wholes". A fraction this map does not hold falls back to the
     number rather than being rounded to one that reads nicely. */
  var FRACTIONS = { 0.25: '¼', 0.5: '½', 0.75: '¾' };

  function wholeText(quantity) {
    var n = tidy(Number(quantity));
    if (n === 0.5) return 'half';
    if (n === 0.25) return 'quarter';

    var whole = Math.floor(n);
    var fraction = FRACTIONS[tidy(n - whole)];
    var number = fraction
      ? (whole ? whole + fraction : fraction)
      : String(n);
    return number + ' whole';
  }

  /* The number as a cook writes it: `⅔ tsp`, `1½ tbsp` (#801). Notation, not
     rounding: a fraction is printed only for exactly that value (the tolerance
     is for floating point), anything else as a decimal. */
  var COOKS_FRACTIONS = [
    [1 / 8, '⅛'], [1 / 4, '¼'], [1 / 3, '⅓'], [3 / 8, '⅜'], [1 / 2, '½'],
    [5 / 8, '⅝'], [2 / 3, '⅔'], [3 / 4, '¾'], [7 / 8, '⅞']
  ];

  function fractionText(quantity, places) {
    var n = Number(quantity);
    if (!isFinite(n)) return String(quantity);

    var whole = Math.floor(n + 1e-9);
    var rest = n - whole;

    for (var i = 0; i < COOKS_FRACTIONS.length; i += 1) {
      if (Math.abs(rest - COOKS_FRACTIONS[i][0]) < 1e-6) {
        return (whole ? String(whole) : '') + COOKS_FRACTIONS[i][1];
      }
    }
    if (rest < 1e-6) return String(whole);

    var factor = Math.pow(10, typeof places === 'number' ? places : 2);
    return String(Math.round(n * factor) / factor);
  }

  /* A unit the name already says is not said twice (#1132): "1 cube" of
     "sugar cube". The unit matches when it is the name's own last word, both
     folded to singular; a one-word name never matches. The same rule is
     restated in _layouts/cocktail.html, which builds the drink page before
     any script runs: change both.

     @param {string} unit - folded, as parseAmount returns it: `cube`, `leaf`
     @param {string} name - the generic as written */
  function unitRepeatsName(unit, name) {
    if (!unit || SYMBOL_UNITS[unit]) return false;
    var words = foldKey(name).split(' ');
    if (words.length < 2) return false;
    return foldUnit(words[words.length - 1]) === foldUnit(unit);
  }

  function quietUnit(unit, name) {
    return unit === 'each' || unitRepeatsName(unit, name);
  }

  /** One quantity and its unit, as a line of the list prints them. */
  function amountText(quantity, unit) {
    if (unit === 'whole') return wholeText(quantity);
    var shown = unitLabel(unit, quantity);
    return shown ? quantity + ' ' + shown : String(quantity);
  }

  /* A total that is honestly a range (#746). The unit is pluralised off the
     top end; the dash is an en dash; the plain form is returned when the two
     ends meet. */
  function amountRangeText(low, high, unit) {
    if (low === high) return amountText(low, unit);
    if (unit === 'whole') return wholeText(low) + '–' + wholeText(high);
    var shown = unitLabel(unit, high);
    return shown
      ? low + '–' + high + ' ' + shown
      : low + '–' + high;
  }

  /* "£11.34", or "£11.34–£14.70" for a range: the same shape as `costSuffix`
     in cocktail-index.js. Always two decimal places. */
  function moneyText(low, high) {
    var lo = '£' + Number(low).toFixed(2);
    if (Math.abs(Number(high) - Number(low)) < 0.005) return lo;
    return lo + '–£' + Number(high).toFixed(2);
  }

  /* What a line costs (#820, #748): quantity times a rate resolved at build
     time by _plugins/cocktail_costs.rb. This multiplies; it does not resolve.

     Named bottles win over the generic only when every one of them is priced:
     pricing from some would report a range narrower than the truth. Pieces
     (`whole`, `each`, `cube`) and grams are always priced from the generic.
     No rate means null, never zero. */
  function linePrice(mlMin, mlMax, generic, bottleNames, rates, units) {
    if (!rates) return null;

    var low = 0;
    var high = 0;
    var priced = false;

    if (mlMax > 0) {
      var byBottle = rates.bottles || {};
      var named = asList(bottleNames);
      var rate = null;

      if (named.length) {
        var found = named.map(function (n) { return byBottle[n]; });
        if (found.every(function (r) { return typeof r === 'number'; })) {
          rate = [Math.min.apply(null, found), Math.max.apply(null, found)];
        }
      }
      if (!rate) rate = (rates.generics || {})[generic];
      if (rate && rate.length === 2) {
        low += mlMin / 1000 * Number(rate[0]);
        high += mlMax / 1000 * Number(rate[1]);
        priced = true;
      }
    }

    var totals = units || {};
    var pieces = (totals.whole || 0) + (totals.each || 0) + (totals.cube || 0);
    var perPiece = (rates.fruit || {})[generic];
    if (pieces > 0 && perPiece && perPiece.length === 2) {
      low += pieces * Number(perPiece[0]);
      high += pieces * Number(perPiece[1]);
      priced = true;
    }

    var grams = totals.g || 0;
    var perKilo = (rates.weight || {})[generic];
    if (grams > 0 && perKilo && perKilo.length === 2) {
      low += grams / 1000 * Number(perKilo[0]);
      high += grams / 1000 * Number(perKilo[1]);
      priced = true;
    }

    if (!priced) return null;
    return {
      min: low,
      max: high,
      exact: Math.abs(high - low) < 0.005,
      text: moneyText(low, high)
    };
  }

  /* What the whole list costs (#817). Summed from the rows, so the total cannot
     disagree with its own column. `unpriced` is part of the answer: a bare
     figure would claim to be the whole shop. */
  function total(rows) {
    var min = 0;
    var max = 0;
    var priced = 0;
    var unpriced = 0;
    asList(rows).forEach(function (row) {
      if (row && row.price) {
        min += row.price.min;
        max += row.price.max;
        priced += 1;
      } else if (row) {
        unpriced += 1;
      }
    });
    if (!priced) return null;
    return {
      min: min,
      max: max,
      exact: Math.abs(max - min) < 0.005,
      priced: priced,
      unpriced: unpriced,
      text: moneyText(min, max)
    };
  }

  /* Only an amount written exactly `(top)` is a top; any other unquantified
     phrase keeps the counted reading. */
  var TOP_UP = /^\(top\)$/i;

  /* Vulgar fractions are numbers: food writes `½ tsp`, `¼–½ tsp`, `1½ tbsp`
     (#801). */
  var VULGAR = {
    '½': 0.5, '⅓': 1 / 3, '⅔': 2 / 3, '¼': 0.25, '¾': 0.75,
    '⅕': 0.2, '⅖': 0.4, '⅗': 0.6, '⅘': 0.8,
    '⅙': 1 / 6, '⅚': 5 / 6, '⅐': 1 / 7, '⅛': 0.125, '⅜': 0.375,
    '⅝': 0.625, '⅞': 0.875, '⅑': 1 / 9, '⅒': 0.1
  };

  var VULGAR_CLASS = '[½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅐⅛⅜⅝⅞⅑⅒]';

  /* A number is digits, a fraction, or digits then a fraction (`1½` is one
     token). The lookahead is load-bearing: without it both halves are
     optional, the range branch matches a bare separator, and `2.5-cm piece`
     loses its hyphen. */
  var NUMBER = '(?=\\d|' + VULGAR_CLASS + ')(\\d+(?:\\.\\d+)?)?(' + VULGAR_CLASS + ')?';

  /* The range separator is a dash, a hyphen or ` to`, and only when a NUMBER
     follows it: the hyphen in `2 x 400-g tins` is part of the unit. */
  var AMOUNT = new RegExp(
    '^\\s*(~)?\\s*' + NUMBER +
    '(?:\\s*(?:–|—|-|\\s+to)\\s*' + NUMBER + ')?' +
    '\\s*(.*?)\\s*$'
  );

  function numberFrom(digits, fraction) {
    if (digits === undefined && fraction === undefined) return null;
    var n = 0;
    if (digits !== undefined && digits !== '') n += parseFloat(digits);
    if (fraction) n += VULGAR[fraction];
    return isFinite(n) ? n : null;
  }

  /**
   * Split "22.5 ml" into a number and a unit. Null when the string is not a
   * quantity at all (`(top)`, `some`); the caller counts those entries.
   * `max` and `approx` are present only when the source said so: "30–50 g"
   * gives {quantity: 30, max: 50}, "~2 tbsp" gives {approx: true}.
   * @param {string} amount
   * @returns {{quantity: number, unit: string, max?: number, approx?: boolean}|null}
   */
  function parseAmount(amount) {
    /* `half` is 0.5 of a `whole`, so scaling and totalling need no rule of
       their own; only the printing is special (wholeText). */
    if (String(amount || '').trim().toLowerCase() === 'half') {
      return { quantity: 0.5, unit: 'whole' };
    }

    var match = AMOUNT.exec(String(amount || ''));
    if (!match) return null;

    var quantity = numberFrom(match[2], match[3]);
    if (quantity === null) return null;

    var parsed = { quantity: quantity, unit: foldUnit(match[6]) };

    var max = numberFrom(match[4], match[5]);
    // A range that runs backwards is not a range: the second number goes.
    if (max !== null && max > quantity) parsed.max = max;

    if (match[1]) parsed.approx = true;
    return parsed;
  }

  /* The bracket that restates the same quantity: `1 tbsp (6 g)`. It has to
     come off the unit before grouping (`tbsp (6 g)` and `tbsp (12 g)` are one
     unit) and before scaling (both figures must move together). Returned, not
     applied: the food callers decide what to do with it.

     @param {string} unit
     @returns {{unit: string, lo: number, hi: number|null, unit2: string}|
               {unit: string}} */
  var PARENTHETICAL = new RegExp(
    '^(.*?)\\s*\\(\\s*' + NUMBER +
    '(?:\\s*(?:–|—|-)\\s*' + NUMBER + ')?' +
    '\\s*([^)]*?)\\s*\\)\\s*$'
  );

  function splitParenthetical(unit) {
    var match = PARENTHETICAL.exec(String(unit || ''));
    if (!match) return { unit: String(unit || '') };

    var lo = numberFrom(match[2], match[3]);
    if (lo === null) return { unit: String(unit || '') };
    var hi = numberFrom(match[4], match[5]);

    return {
      unit: match[1],
      lo: lo,
      hi: hi !== null && hi > lo ? hi : null,
      unit2: foldUnit(match[6])
    };
  }

  function pluralise(word) {
    if (/(s|sh|ch|x|z)$/.test(word)) return word + 'es';
    return word + 's';
  }

  /* How many whole fruits a volume of juice comes to (#546). `yields` is one
     entry of `juice_yields` in _data/cocktails/ingredients.yml. The fewest
     fruits is the total over the LARGEST yield; both ends round up, because
     part of a lemon is a lemon bought. A range that collapses prints once. */
  function fruitCount(ml, yields) {
    if (!yields || !(ml > 0)) return null;

    var low = Number(yields.ml_min);
    var high = Number(yields.ml_max);
    var fruit = String(yields.fruit || '').trim();
    if (!fruit || !isFinite(low) || !isFinite(high) || low <= 0 || high <= 0) return null;

    // Declared either way round without changing the answer.
    var smallest = Math.min(low, high);
    var largest = Math.max(low, high);

    var fewest = Math.ceil(ml / largest);
    var most = Math.ceil(ml / smallest);

    var text = fewest === most
      ? fewest + ' ' + (fewest === 1 ? fruit : pluralise(fruit))
      : fewest + ' to ' + most + ' ' + pluralise(fruit);

    return { fewest: fewest, most: most, fruit: fruit, text: text };
  }

  /* Rounds away float noise in sums of 22.5s and 7.5s: three decimals is finer
     than any written amount. */
  function tidy(n) {
    return Math.round(n * 1000) / 1000;
  }

  /** Total up a shortlist.
   * @param {Array} entries - { amount, generic, bottle, glasses? } per ingredient of every shortlisted drink
   * @param {Object} [options]
   * @param {number} [options.multiplier=1] - glasses of each drink
   * @param {string[]} [options.exclude=[]] - generics to leave out, folded as the keys are (`not_on_cards`)
   * @param {Object} [options.bottleAliases] - folded spelling -> canonical bottle name
   * @param {Object} [options.juiceYields] - generic -> {fruit, ml_min, ml_max}: `juice_yields` in ingredients.yml
   * @param {Object} [options.topUpMl] - `top_up_ml` in costs.yml; absent, a top stays a count
   * @param {Object} [options.rates] - from _plugins/cocktail_costs.rb; absent, no row carries a price
   * @param {Object} [options.shelves] - `shopping_shelves` and `shelf_of`; absent, rows sort by volume alone
   * @returns {Array} one row per ingredient, sorted by shelf, then descending millilitres, then label */
  function build(entries, options) {
    var opts = options || {};
    var multiplier = typeof opts.multiplier === 'number' && opts.multiplier > 0
      ? opts.multiplier : 1;

    var excluded = {};
    asList(opts.exclude).forEach(function (name) { excluded[foldKey(name)] = true; });

    /* One bottle however it was written (#529). The aliases are declared
       data: nothing about `ED3` says `El Dorado 3`. */
    var aliases = opts.bottleAliases || {};
    function canonicalBottle(name) {
      return aliases[foldKey(name)] || name;
    }

    // Folded like the group keys, so a yield is found whatever the drink's
    // capitalisation.
    var yields = {};
    Object.keys(opts.juiceYields || {}).forEach(function (generic) {
      yields[foldKey(generic)] = opts.juiceYields[generic];
    });

    var topUps = {};
    Object.keys(opts.topUpMl || {}).forEach(function (generic) {
      topUps[foldKey(generic)] = opts.topUpMl[generic];
    });

    /* Shelf order is the outer sort key (#848), folded to a rank up front. A
       generic with no declared shelf sorts last, where the gap is visible. */
    var shelfRank = {};
    var shelfOrder = asList(opts.shelves && opts.shelves.order);
    shelfOrder.forEach(function (name, i) { shelfRank[foldKey(name)] = i; });
    var shelfOf = {};
    var declaredShelves = (opts.shelves && opts.shelves.of) || {};
    Object.keys(declaredShelves).forEach(function (generic) {
      shelfOf[foldKey(generic)] = foldKey(declaredShelves[generic]);
    });
    var LAST_SHELF = shelfOrder.length;

    function rankOf(generic) {
      var shelf = shelfOf[foldKey(generic)];
      var rank = shelf === undefined ? undefined : shelfRank[shelf];
      return rank === undefined ? LAST_SHELF : rank;
    }

    var groups = {};
    var order = [];

    asList(entries).forEach(function (entry) {
      if (!entry) return;
      var generic = joined(entry.generic);
      if (!generic) return;
      var key = foldKey(generic);
      if (excluded[key]) return;

      if (!groups[key]) {
        groups[key] = {
          generic: generic,
          /* `bottles` holds each suggestion as written ("El Dorado 3 or Havana
             Club 3" is one entry); `bottleNames` the individual bottles,
             flattened and deduped, which the note and the price lookup need. */
          bottles: [],
          bottleKeys: {},
          bottleNames: [],
          bottleNameKeys: {},
          bare: 0,
          units: {},
          unitOrder: [],
          /* A top's declared range rides beside the fixed `ml` total, not
             inside it, so the row can report both ends (#746). */
          topUpMin: 0,
          topUpMax: 0,
          unquantified: {},
          unquantifiedOrder: []
        };
        order.push(key);
      }
      var group = groups[key];

      /* Aliases are resolved per alternative, not on the joined string: only
         the members of "Havana 3 or El Dorado 3" are names an alias can know. */
      var named = asList(entry.bottle)
        .map(function (b) { return canonicalBottle(String(b).trim()); })
        .filter(Boolean);
      var bottle = named.join(' or ');
      if (bottle) {
        var bottleKey = foldKey(bottle);
        if (!group.bottleKeys[bottleKey]) {
          group.bottleKeys[bottleKey] = true;
          group.bottles.push(bottle);
        }
        named.forEach(function (name) {
          var nameKey = foldKey(name);
          if (!group.bottleNameKeys[nameKey]) {
            group.bottleNameKeys[nameKey] = true;
            group.bottleNames.push(name);
          }
        });
      } else {
        group.bare += 1;
      }

      /* An entry's own `glasses` wins; `options.multiplier` is the fallback
         for every entry that carries none. */
      var scale = (typeof entry.glasses === 'number' && entry.glasses > 0)
        ? entry.glasses : multiplier;

      var parsed = parseAmount(entry.amount);
      if (parsed) {
        if (group.units[parsed.unit] === undefined) {
          group.units[parsed.unit] = 0;
          group.unitOrder.push(parsed.unit);
        }
        group.units[parsed.unit] += parsed.quantity * scale;
      } else {
        var text = String(entry.amount || '').trim();
        if (!text) return;

        /* A declared top becomes a volume range (#746), and both ends scale
           with the glasses. */
        var topUp = TOP_UP.test(text) ? topUps[key] : null;
        if (topUp) {
          /* A generic that is only ever topped has no parsed amount, so `ml`
             must be seeded here for the range to have a total to widen. */
          if (group.units.ml === undefined) {
            group.units.ml = 0;
            group.unitOrder.push('ml');
          }
          group.topUpMin += (Number(topUp.ml_min) || 0) * scale;
          group.topUpMax += (Number(topUp.ml_max) || 0) * scale;
          return;
        }

        if (group.unquantified[text] === undefined) {
          group.unquantified[text] = 0;
          group.unquantifiedOrder.push(text);
        }
        group.unquantified[text] += scale;
      }
    });

    return order.map(function (key) {
      var group = groups[key];

      // The generic leads; the note is the flat, deduped list of bottles.
      var label = group.generic;
      var note = group.bottleNames.join(' / ');

      // A declared top only ever widens the `ml` total.
      var mlFixed = tidy(group.units.ml || 0);
      var mlMin = tidy(mlFixed + group.topUpMin);
      var mlMax = tidy(mlFixed + group.topUpMax);

      var totals = group.unitOrder.map(function (unit) {
        var quantity = tidy(group.units[unit]);
        if (unit === 'ml' && group.topUpMax > 0) {
          return {
            quantity: mlMin,
            quantityMax: mlMax,
            unit: unit,
            text: amountRangeText(mlMin, mlMax, unit)
          };
        }
        return {
          quantity: quantity,
          quantityMax: quantity,
          unit: unit,
          /* #1132: "13 cubes sugar cube" and "3 each passion fruit" lose the
             unit the line does not need. The `unit` field keeps it. */
          text: quietUnit(unit, group.generic) ? String(quantity)
                                               : amountText(quantity, unit)
        };
      });

      /* ...and the name takes the plural the unit would have carried: "13" +
         "sugar cubes". Only when that unit is the row's one total. `generic`
         is untouched: callers look things up by it. */
      if (totals.length === 1 && !group.unquantifiedOrder.length &&
          unitRepeatsName(totals[0].unit, label)) {
        label = replaceLastWord(label, unitLabel(totals[0].unit, totals[0].quantity));
      }

      var unquantified = group.unquantifiedOrder.map(function (text) {
        return { text: text, drinks: group.unquantified[text] };
      });

      /* Fruit is counted from the fixed ml total only, never from a top or
         from another unit: yields are declared in millilitres. */
      var fruit = fruitCount(mlFixed, yields[foldKey(group.generic)]);

      /* One string for the whole amount, built here rather than in the caller,
         so the copied text and the rendered row cannot say different things. */
      var parts = totals.map(function (t) { return t.text; })
        .concat(unquantified.map(function (u) {
          return u.drinks > 1 ? u.text + ' (×' + u.drinks + ')' : u.text;
        }));

      return {
        label: label,
        note: note,
        generic: group.generic,
        bottles: group.bottles.slice(),
        totals: totals,
        unquantified: unquantified,
        fruit: fruit,
        // Priced per bottle named, not per "or" form: rates are per bottle.
        price: linePrice(mlMin, mlMax, group.generic, group.bottleNames,
                         opts.rates, group.units),
        /* The low end: the sort and the callers read this, so a topped line
           ranks by what is certain to be poured. */
        millilitres: mlMin,
        millilitresMax: mlMax,
        // For a caller to group or label by; the sort reads the rank.
        shelf: shelfOf[foldKey(group.generic)] === undefined
          ? null
          : declaredShelves[group.generic] || shelfOrder[rankOf(group.generic)],
        text: parts.join(' + ')
      };
    }).sort(function (a, b) {
      /* Shelf first (#848); with no `options.shelves` every row ranks the
         same and this falls through to volume. */
      var shelfA = rankOf(a.generic);
      var shelfB = rankOf(b.generic);
      if (shelfA !== shelfB) return shelfA - shelfB;

      /* Then descending millilitres, and only millilitres: ranking 45 ml
         against 2 dashes would need a conversion. Rows with no volume follow,
         alphabetically. */
      if (a.millilitres !== b.millilitres) return b.millilitres - a.millilitres;
      return a.label.toLowerCase().localeCompare(b.label.toLowerCase());
    });
  }

  var api = {
    build: build,
    total: total,
    moneyText: moneyText,
    parseAmount: parseAmount,
    fruitCount: fruitCount,
    foldKey: foldKey,
    foldUnit: foldUnit,
    unitLabel: unitLabel,
    wholeText: wholeText,
    amountText: amountText,
    amountRangeText: amountRangeText,
    // #1132. What build() asks before printing a unit beside a name.
    quietUnit: quietUnit,
    // Used by food-shopping-list.js and food-scale.js.
    splitParenthetical: splitParenthetical,
    fractionText: fractionText,
    tidy: tidy
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  } else {
    root.HTF = root.HTF || {};
    root.HTF.shoppingList = api;
  }
})(typeof window !== 'undefined' ? window : this);
