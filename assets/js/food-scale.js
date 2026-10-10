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
// `halfStep` below, the one place the rounding is decided. (The INDEX's
// shopping list takes the same measures to the nearest WHOLE one, #1297 --
// that is food-shopping-list.js's `wholeOnes`, and it never calls this.)
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
  /* A size standing in for a noun nobody writes -- shopping-list.js's own
     SYMBOL_UNITS says the same of them. "2 large" counts the item. */
  var SIZE_UNITS = { large: true, medium: true, small: true };

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

  /* A SPRIG AND A BUNCH SCALE IN QUARTERS -- #1297, Helen, 2026-10-10, shown
     "1.17 sprigs" on this page: "Sprigs: Let's round to 1/4 please, and
     express in fractions not decimals." The nearest quarter, never less than
     one: 1 sprig x7/6 is 1¼ sprigs, x2/3 is ¾ sprigs, and 4 sprigs doubled is
     still 8. `quarter_step_measures` in scaling.yml, passed in as
     `options.quarterStep` exactly as the half-step list is. */
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

  /* A numbered amount in a half-step measure: "1 handful", "~2 handfuls",
     "1–2 pinches", "1 large handful each". The number is stepped, and the
     measure word -- wherever it sits in the unit -- takes the plural of the
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
   * @param {{halfStep?: string[], quarterStep?: string[]}} [options] -
   *        _data/food/scaling.yml's `half_step_measures` and
   *        `quarter_step_measures`
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

    /* `one` SAYS THE NOUN IN THE ITEM MUST NOW BE SINGULAR. "2 large eggs" at
       half a recipe is "1 large egg": the amount holds no noun of its own (it
       is a bare count or a size word), it was written for more than one, and
       it has come down to exactly one. "2 cloves" of garlic is not this case:
       its noun is the unit and `totalText` already prints "1 clove". */
    var bareCount = unit === '' || SIZE_UNITS[unit] === true;
    var one = bareCount && split.lo === undefined &&
      Math.abs(total.lo - 1) < 1e-9 && Math.abs(total.hi - 1) < 1e-9 &&
      hiQuantity > 1;

    return { text: totalText(total), scaled: true, one: one };
  }

  /* =========================================================================
     "1 large egg", NOT "1 large eggs" -- #1286, Helen, 2026-10-04
     =========================================================================
     "Waffles: at 0.5x, that should read '1 large egg' not 'eggs'. Going from
     1x to 0.5x eggs will be the only kind of occasion where a plural reduces
     to a single. Can we fix please?"

     THE NOUN IS IN THE ITEM, not the amount, so the amount's own plural rule
     never reached it. This takes the item's text and makes its LEADING NOUN
     singular: the last word before the first comma or bracket -- "eggs,
     separated" -> "egg, separated", "egg yolks" -> "egg yolk", "free-range
     eggs" -> "free-range egg". Everything after is untouched.

     THE HOUSE'S OWN SINGULARS, not a new rule: first the `singulars` map in
     _data/food/ingredient_words.yml (potatoes -> potato, leaves -> leaf),
     passed in; then shopping-list.js's `foldUnit`, which is what
     food-shopping-list.js's `foldName` already uses to make "onions" and
     "onion" one line.

     LEFT AS WRITTEN WHEN IT CANNOT BE DONE SAFELY, because a wrong singular
     is worse than a plural: a head that names two things ("shallots or 1
     onion"), a word with a capital in it, a word ending -oes or -ies that
     the map does not hold (`foldUnit` would give "tomatoe"), and a word
     ending -ss or with no plural to remove.

     (She expected this only at half a recipe. A `serves:` recipe reaches it
     too -- two eggs for four people, shown for two -- and gets the same
     answer.) */
  function singularItem(text, singulars) {
    var written = String(text === undefined || text === null ? '' : text);
    var match = /^(\s*)([^,(]*?)(\s*(?:[,(][\s\S]*)?)$/.exec(written);
    if (!match || match[2] === '') return written;
    /* THE NOUN IS BEFORE ANY "of", "in", "like" ...: "rashers of streaky
       bacon" is a rasher, "spring onions in thin strips" a spring onion. The
       rest of the head is carried along untouched. */
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

  /* =========================================================================
     WHAT THE SCALER'S BOX COUNTS -- portions, or the thing made (#1286)
     =========================================================================
     A MODE is five small answers the wiring asks for, and recipe-scale.js
     holds no arithmetic of its own for any kind:

       base        the figure the recipe is written for; factor = value / base
       clamp(n)    a typed or stepped value, made into one the box can hold
       step(n, d)  one press of minus (-1) or plus (+1)
       box(n)      what the input shows
       word(n)     what follows the input, or null to leave the markup alone

     TWO WAYS OF STEPPING, and which one a recipe gets is the whole of #1286:

     A `serves:` RECIPE STEPS ONE PORTION AT A TIME (#1005, unchanged): four
     portions of a recipe for six is x0.67.

     EVERY `makes:` RECIPE STEPS IN WHOLE RECIPES -- x1, x2, x3 -- and the box
     shows what that many recipes make. Helen, 2026-10-04: "the buttons should
     still multiply the recipe in integers, just showing number of waffles. So
     1x is 5 waffles, 2x is 10 waffles. Otherwise we'll need to start showing
     eggs in units of 1/27 or something." And for a yield with no number: 'if
     "some" is originally guessed to be 4 portions, 2x should be 8 portions.'
     So waffles, millilitres, dozens, 8-inch cakes and guessed portions are
     ONE shape: `wholeRecipes` below. A typed figure goes to the nearest
     whole multiple (8 on the waffles is 10).

     AND ONE STEP BELOW ONE RECIPE: x½, WHERE THE BUILD ALLOWS IT. Helen:
     "Half a recipe would be great where the numbers aren't insane! Can we
     judge that?" and, on the shape, "not having half recipes in between
     integers, just between 0 and 1". So the steps are ½, 1, 2, 3 ... and
     never 1½. `half` is the build's verdict (_plugins/food_half_recipe.rb,
     `data-half-recipe`); this file does not judge. With it, minus at one
     recipe gives a half, and a typed figure under three quarters of a recipe
     is a half. Without it the floor is one recipe and minus there does
     nothing, with no message. */
  function wholeRecipes(base, box, word, half) {
    function multiple(n) {
      var m = n / base;
      if (half && m < 0.75) return 0.5;
      return Math.max(1, Math.round(m));
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
   *
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
      clamp: function (n) { return Math.max(1, Math.round(n)); },
      step: function (n, delta) { return n + delta; },
      box: box,
      word: word
    };
  }

  /* A FIGURE ON A HALF IS SHOWN AS A RANGE OF ONE -- Helen: "Midpoints that
     land on a half can become a range of one." 4–7 is 5.5 and reads "5–6";
     two recipes are 11 and read "11"; three are 16.5 and read "16–17". The
     ingredients scale by the whole multiple, so the half never reaches them.
     _plugins/food_yield.rb `box` is this rule for the page as built. */
  function yieldBox(value) {
    if (value === Math.floor(value)) return String(value);
    return Math.floor(value) + '–' + Math.ceil(value);
  }

  function replaceLast(text, change) {
    var words = String(text).split(' ');
    words[words.length - 1] = change(words[words.length - 1]);
    return words.join(' ');
  }

  /* THE THING MADE, AGREEING WITH THE NUMBER BESIDE IT. A line written for
     ONE takes a plural at two ("one 8-inch cake"); a line written for several
     loses it only at exactly one, which a half recipe can reach ("2 burgers"
     halved is "1 burger").

     THE NOUN IS THE LAST WORD OF THE STEM -- the part before any " of " --
     and the plural is shopping-list.js's `unitLabel`, the rule every amount
     on the page already uses. `dozen mince pies` is INVARIABLE: it is the
     dozen that is counted ('"1 dozen" doubled can be "two dozen"').

     `× ` IN FRONT OF A THING THAT OPENS WITH A DIGIT -- Helen: a digit
     directly before "8-inch" is unreadable. The box is a number, so the count
     cannot be spelled as a word; "2 × 8-inch cakes" is the form shown. */
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

    /* A MEASURE -- Helen: "950 ml for one order of a recipe becomes 1900 ml
       for 2". */
    if (spec.kind === 'measure') {
      var unit = shoppingList.foldUnit(String(spec.unit || ''));
      /* Half of an odd measure is shown as a range of one, like a count:
         125 ml halved reads "62–63 ml". */
      return wholeRecipes(base, yieldBox,
        function (n) { return unitLabel(unit, n); }, half);
    }

    /* A COUNT. THE `+` OF "64+" TRAVELS WITH THE FIGURE -- Helen: "64+ tiny
       macarons, 128+ tiny macarons". */
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
