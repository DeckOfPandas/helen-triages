// One food amount, times a factor (#1005). No DOM.
//
// The arithmetic and the printing for the recipe page's scaler;
// assets/js/recipe-scale.js is the wiring. Loaded as a plain <script>
// attaching to window.HTF, and via require() for tests/js/food-scale.test.js.
//
// Nothing here parses or formats for itself: the parser is shopping-list.js's
// `parseAmount` and the printing is food-shopping-list.js's `totalText`, so a
// scaled amount is written the same way on both pages. Kilograms and litres
// are folded down first, so a kilogram halved prints as grams.
//
// An amount with no count in it ("a few handfuls", "some") comes back
// untouched with `scaled: false`, and the page names it under the control.

(function (root, factory) {
  /* Both dependencies are read at module scope, so the wrong load order fails
     at startup; tests/test_site_config.py guards it in _layouts/recipe.html. */
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
  // The same unit fold and size words the shopping list applies.
  var CANONICAL = foodShoppingList.CANONICAL;
  var SIZE_UNITS = foodShoppingList.SIZE_UNITS;

  /* A measure taken by hand or eye scales to the nearest half, never less
     than a half (#1125): 1 pinch ×3 is 3, ×1.5 is 1½, ×2/3 is ½. Which
     measures is data, passed in as `options.halfStep` (`half_step_measures`
     and `half_step_counts` in _data/food/scaling.yml); this file names none.
     With no list given, such a measure scales like any other count. */
  function halfStep(quantity) {
    return Math.max(0.5, Math.round(quantity * 2) / 2);
  }

  /* The nearest quarter, and never below a quarter, so nothing scales to
     nothing (#1297): 1 sprig ×7/6 is 1¼, and ×1/6 is ¼.
     `quarter_step_measures` in scaling.yml, passed in as
     `options.quarterStep`. */
  function quarterStep(quantity) {
    return Math.max(0.25, Math.round(quantity * 4) / 4);
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

  /* A numbered amount in a stepped measure: "1 handful", "~2 handfuls",
     "1–2 pinches", "1 large handful each". The number is stepped, and the
     measure word, wherever it sits in the unit, takes the plural of the
     number it ends up beside. Null when the unit holds no such measure. */
  function scaleSteppedMeasure(parsed, factor, words, step) {
    if (!words) return null;
    var pattern = measurePattern(words);
    if (!pattern.test(parsed.unit)) return null;

    var lo = step(parsed.quantity * factor);
    var hi = parsed.max === undefined ? lo : step(parsed.max * factor);
    var unit = parsed.unit.replace(pattern, function (all, before, measure) {
      return before + unitLabel(measure.toLowerCase(), hi);
    });
    var number = hi > lo ? numberText(lo) + '–' + numberText(hi) : numberText(lo);
    return { text: (parsed.approx ? '~' : '') + number + ' ' + unit, scaled: true };
  }

  /* The same measure written with no number: "a handful of fresh parsley".
     `a`, `an`, `one` or nothing before a SINGULAR measure counts as one; a
     digit counts as itself; a size word may sit between and is kept. "a few",
     "some" and a bare plural are not numbers and are left alone. A result
     equal to what was written gives back the recipe's own words untouched.
     `tail` is what must follow the measure: " of " inside an item's text, or
     the end of the string for an amount that is only the measure. */
  var COUNT_OF_ONE = '(?:(an?|one|\\d+)\\s+)?';
  var SIZE_WORD = '((?:small|large|big|good|generous|little)\\s+)?';

  function scaleMeasurePhrase(text, factor, words, tail, step) {
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
    var n = (step || halfStep)(base * factor);
    if (n === base) return { text: written, scaled: true };

    return {
      text: match[1] + numberText(n) + ' ' + (match[3] || '') +
        unitLabel(match[4].toLowerCase(), n) + match[6] +
        written.slice(match[0].length),
      scaled: true
    };
  }

  /**
   * A row with no amount: "a handful of parsley" x3 is "3 handfuls of parsley".
   * @param {string} text - the item's text as the page prints it
   * @param {number} factor
   * @param {{halfStep?: string[], quarterStep?: string[]}} [options]
   * @returns {{text: string, scaled: boolean}} `scaled: false` and the text
   *          untouched when it does not open with a countable by-eye measure
   */
  function scaleLeadingMeasure(text, factor, options) {
    return eitherStep(text, factor, options, '\\s+of\\s+');
  }

  /* A measure with no number, in whichever step it takes: each list is tried
     with its own rounding, and a word belongs on one list only. */
  function eitherStep(text, factor, options, tail) {
    var halves = scaleMeasurePhrase(text, factor,
      measureWords(options && options.halfStep), tail, halfStep);
    if (halves.scaled) return halves;
    return scaleMeasurePhrase(text, factor,
      measureWords(options && options.quarterStep), tail, quarterStep);
  }

  /**
   * @param {string} amount - as the recipe wrote it: "200 g", "30–50 g", "2 large"
   * @param {number} factor - portions wanted over portions the recipe makes
   * @param {{halfStep?: string[], quarterStep?: string[]}} [options] - the
   *        `half_step_measures` and `quarter_step_measures` of scaling.yml
   * @returns {{text: string, scaled: boolean}} an amount with no count in it
   *        comes back as written with `scaled: false`
   */
  function scaleAmount(amount, factor, options) {
    var written = String(amount === undefined || amount === null ? '' : amount);
    if (!(factor > 0)) return { text: written, scaled: false };

    var words = measureWords(options && options.halfStep);
    var parsed = parseAmount(written);
    if (!parsed) {
      // "pinch", "a handful", "small handful": the measure and nothing else.
      return eitherStep(written, factor, options, '\\s*$');
    }

    var stepped = scaleSteppedMeasure(parsed, factor, words, halfStep) ||
      scaleSteppedMeasure(parsed, factor,
        measureWords(options && options.quarterStep), quarterStep);
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

    /* `one` says the noun in the ITEM must now be singular: a bare count or
       size word, written for more than one, has come down to exactly one
       ("2 large eggs" halved). "2 cloves" is not this case: its noun is the
       unit and `totalText` already prints "1 clove". */
    var bareCount = unit === '' || SIZE_UNITS[unit] === true;
    var one = bareCount && split.lo === undefined &&
      Math.abs(total.lo - 1) < 1e-9 && Math.abs(total.hi - 1) < 1e-9 &&
      hiQuantity > 1;

    return { text: totalText(total), scaled: true, one: one };
  }

  /* "1 large egg", not "1 large eggs" (#1286). Makes the item's LEADING NOUN
     singular: the last word before the first comma or bracket. Singulars come
     from the `singulars` map in _data/food/ingredient_words.yml, passed in,
     then shopping-list.js's `foldUnit`. Left as written when it cannot be
     done safely: a head naming two things, a capitalised word, an ending
     `foldUnit` would get wrong (-oes, -ies, -ss, -us, -is) that the map does
     not hold, or no plural to remove. */
  function singularItem(text, singulars) {
    var written = String(text === undefined || text === null ? '' : text);
    var match = /^(\s*)([^,(]*?)(\s*(?:[,(][\s\S]*)?)$/.exec(written);
    if (!match || match[2] === '') return written;
    /* The noun is before any "of", "in", "like" ...: "rashers of streaky
       bacon" is a rasher. The rest of the head is carried along untouched. */
    var cut = /\s(?:of|in|for|with|like|from)\s/i.exec(match[2]);
    var head = cut ? match[2].slice(0, cut.index) : match[2];
    var after = cut ? match[2].slice(cut.index) : '';
    if (/\s(?:or|and)\s|\//i.test(head)) return written;

    var words = head.split(' ');
    var noun = words[words.length - 1];
    if (noun !== noun.toLowerCase() || !/^[a-zà-ÿ'’-]+$/.test(noun)) return written;

    var map = singulars || {};
    var single;
    if (Object.prototype.hasOwnProperty.call(map, noun)) {
      single = String(map[noun]);
    } else if (/(?:oes|ies|ss|us|is)$/.test(noun) || !/s$/.test(noun)) {
      return written;
    } else {
      single = shoppingList.foldUnit(noun);
    }
    if (!single || single === noun) return written;

    words[words.length - 1] = single;
    return match[1] + words.join(' ') + after + match[3];
  }

  /* The name on the "(Not scaled: ...)" line (#1125): the ingredient, not the
     recipe's whole sentence about it. Three cuts, in order: a leading measure
     phrase ending in `of` and holding a declared measure (so "cream of
     tartar" is untouched); everything from the first comma or open bracket,
     which is what keeps the comma-joined line unambiguous; a trailing
     instruction from `trailing_phrases` in ingredient_words.yml, passed in.
     A cut that would leave nothing is not made. */
  var QUANTIFIER = '(?:(?:an?|one|two|a\\s+few|few|some|a\\s+couple\\s+of|several)\\s+)?';
  var SIZE = '(?:(?:small|large|big|good|generous|little)\\s+)?';

  function keep(candidate, fallback) {
    var trimmed = candidate.replace(/\s+/g, ' ').trim();
    return trimmed === '' ? fallback : trimmed;
  }

  /**
   * @param {string} text - the ingredient row's text, amount and note removed
   * @param {{halfStep?: string[], quarterStep?: string[], trailing?: string[]}} [options]
   * @returns {string} the ingredient's name, for the note under the control
   */
  function noteName(text, options) {
    var opts = options || {};
    var name = keep(String(text === undefined || text === null ? '' : text), '');

    // Every stepped measure, half or quarter: "a few handfuls of" goes as
    // "a few dashes of" does.
    var words = measureWords((opts.halfStep || []).concat(opts.quarterStep || []));
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

  /* The most a box can hold: 99 portions, or 99 times a `makes:` recipe. The
     shopping list stops at the same 99 (assets.js MAX_COUNT); past it a
     typed figure printed amounts like "6.2e+28 kg". */
  var MAX_MULTIPLE = 99;

  /* A MODE is what the wiring asks for; recipe-scale.js holds no arithmetic:
     `base` (the figure the recipe is written for; factor = value / base),
     `clamp(n)` (a typed or stepped value made into one the box can hold),
     `step(n, d)` (one press of minus or plus), `box(n)` (what the input
     shows), `word(n)` (what follows it, or null to leave the markup alone).
     A `makes:` recipe steps in whole recipes (#1286); a typed figure goes to
     the nearest whole multiple. Below one recipe only ×½ exists, and only
     where the build allows it (`half`, from _plugins/food_half_recipe.rb). */
  function wholeRecipes(base, box, word, half) {
    function multiple(n) {
      var m = n / base;
      if (half && m < 0.75) return 0.5;
      return Math.min(MAX_MULTIPLE, Math.max(1, Math.round(m)));
    }
    return {
      base: base,
      clamp: function (n) { return multiple(n) * base; },
      step: function (n, delta) {
        var m = multiple(n);
        if (m === 0.5) return (delta > 0 ? 1 : 0.5) * base;
        if (m === 1 && delta < 0) return (half ? 0.5 : 1) * base;
        return (m + delta) * base;
      },
      box: box,
      word: word
    };
  }

  /**
   * The mode for a control that says "portions".
   * @param {number} base - how many the recipe feeds
   * @param {boolean} [whole] - true on a `makes:` recipe whose yield has no
   *        count to show ("Some"): the box still says portions, and steps in
   *        whole recipes -- 4, 8, 12
   * @param {boolean} [half] - the build's verdict that x½ is offered
   */
  function portionsMode(base, whole, half) {
    var box = function (n) { return String(n); };
    var word = function () { return null; };       // the markup's word stands
    if (whole) return wholeRecipes(base, box, word, half);
    return {
      base: base,
      clamp: function (n) { return Math.min(MAX_MULTIPLE, Math.max(1, Math.round(n))); },
      step: function (n, delta) { return n + delta; },
      box: box,
      word: word
    };
  }

  /* A figure on a half is shown as a range of one: 5.5 reads "5–6". The
     ingredients scale by the whole multiple, so the half never reaches them.
     _plugins/food_yield.rb applies the same rule to the page as built. */
  function yieldBox(value) {
    if (value === Math.floor(value)) return String(value);
    return Math.floor(value) + '–' + Math.ceil(value);
  }

  function replaceLast(text, change) {
    var words = String(text).split(' ');
    words[words.length - 1] = change(words[words.length - 1]);
    return words.join(' ');
  }

  /* The thing made, agreeing with the number beside it: a line written for
     one takes a plural at two; one written for several loses it only at
     exactly one. The noun is the last word of the stem. `invariable` is for
     "dozen mince pies", where the dozen is counted. `× ` goes in front of a
     thing that opens with a digit: "2 × 8-inch cakes". */
  function thingText(spec, value) {
    var stem = String(spec.stem || '');
    if (!spec.invariable && spec.singular && value !== 1) {
      stem = replaceLast(stem, function (w) { return unitLabel(w, 2); });
    } else if (!spec.invariable && !spec.singular && value === 1) {
      stem = replaceLast(stem, function (w) { return shoppingList.foldUnit(w); });
    }
    return (spec.times ? '× ' : '') + stem + String(spec.rest || '');
  }

  /**
   * The scaler's mode for a recipe whose `makes:` line opens with a count.
   *
   * @param {Object} spec - `page.made`, as _plugins/food_yield.rb wrote it
   * @param {boolean} [half] - the build's verdict that x½ is offered
   * @returns {Object|null} a mode (see above), or null for a spec it cannot use
   */
  function yieldMode(spec, half) {
    if (!spec || !(Number(spec.base) > 0)) return null;
    var base = Number(spec.base);

    // A measure: 950 ml for one recipe is 1900 ml for two.
    if (spec.kind === 'measure') {
      var unit = shoppingList.foldUnit(String(spec.unit || ''));
      /* Half of an odd measure is shown as a range of one, like a count:
         125 ml halved reads "62–63 ml". */
      return wholeRecipes(base, yieldBox,
        function (n) { return unitLabel(unit, n); }, half);
    }

    // A count. The `+` of "64+" travels with the figure.
    var more = spec.plus ? '+' : '';
    return wholeRecipes(base,
      function (n) { return yieldBox(n) + more; },
      function (n) { return thingText(spec, n); }, half);
  }

  return {
    scaleAmount: scaleAmount,
    scaleLeadingMeasure: scaleLeadingMeasure,
    noteName: noteName,
    singularItem: singularItem,
    halfStep: halfStep,
    quarterStep: quarterStep,
    portionsMode: portionsMode,
    yieldMode: yieldMode,
    yieldBox: yieldBox
  };
});
