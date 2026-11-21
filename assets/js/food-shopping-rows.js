// food-shopping-rows.js: the words and markup of a food shopping list, as
// strings, for any page that draws one (#801, #1297, #1521). No DOM: loaded as
// a <script> onto HTF.foodShoppingRows, and by require() in the tests.
//
// `create(config)` takes what the page knows: the recipe blob the build emits
// (`p`, `y`, `k`, `w`, `h`, `m`, `i`), each recipe's title and href, the
// container nouns, the build() options and an HTML escaper. A row's count is
// the caller's: portions for a `serves:` recipe, batches for a `makes:` one.

(function (root, factory) {
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = factory(require('./shopping-list.js'), require('./food-shopping-list.js'));
  } else {
    root.HTF = root.HTF || {};
    root.HTF.foodShoppingRows = factory(root.HTF.shoppingList, root.HTF.foodShoppingList);
  }
})(typeof window !== 'undefined' ? window : this, function (shoppingList, foodShoppingList) {
  'use strict';

  var foldUnit = shoppingList.foldUnit;
  var unitLabel = shoppingList.unitLabel;

  function create(config) {
    var RECIPES = config.recipes || {};
    var titles = config.titles || {};
    var hrefs = config.hrefs || {};
    var CONTAINER_NOUNS = config.containerNouns || [];
    var options = config.buildOptions || {};
    var esc = config.escape;

    function recipe(url) { return RECIPES[url] || null; }
    function title(url) { return titles[url] || url; }

    // A recipe with a portion count can be scaled by people; asked of the
    // recipe, never of a stored number.
    function hasPortions(url) {
      var r = recipe(url);
      return !!(r && r.p > 0);
    }

    // A `makes:` recipe counts batches: `w`, `h` and `m` are the recipe page's
    // own figures (#1286).
    function isBatch(url) {
      var r = recipe(url);
      return !!(r && r.w);
    }

    function halfOffered(url) {
      return isBatch(url) && !!RECIPES[url].h;
    }

    // What a recipe starts at: its own portions, or one batch.
    function defaultCount(url) {
      if (!isBatch(url) && hasPortions(url)) return RECIPES[url].p;
      return 1;
    }

    // A stored count made into one the recipe can take: a half only where the
    // build offers one, whole portions only.
    function count(url, stored) {
      var n = Number(stored);
      if (!(n > 0)) return defaultCount(url);
      if (isBatch(url)) return (n < 1 && !halfOffered(url)) ? 1 : n;
      if (!hasPortions(url)) return 1;
      return Math.max(1, Math.round(n));
    }

    function scale(url, n) {
      if (isBatch(url)) return n;
      if (!hasPortions(url)) return 1;
      return n / RECIPES[url].p;
    }

    /* A typed or stepped batch figure. The spinner moves in halves so that it
       can reach ½, which means it also lands on 1½: that goes on to the next
       whole batch in the direction it was travelling. null for nothing usable. */
    function batchCount(url, raw, previous) {
      var n = Number(raw);
      if (!isFinite(n) || n <= 0) return null;
      if (n < 1) return halfOffered(url) ? 0.5 : 1;
      if (n % 1 !== 0) return n > previous ? Math.ceil(n) : Math.floor(n);
      return Math.min(99, n);
    }

    function portionCount(raw) {
      var n = Math.round(Number(raw));
      if (!isFinite(n) || n < 1) return null;
      return Math.min(99, n);
    }

    /* Is a word of the yield already in the title? Compared in the singular
       both sides, so "pies" finds "Pie". */
    function wordInTitle(word, text) {
      var wanted = foldUnit(word);
      if (!wanted) return false;
      // A hyphened word counts whole and by its parts: "Sacher-Torte" names a torte.
      return String(text).toLowerCase().split(/[\s,()\/&]+/).some(function (w) {
        return w !== '' && (foldUnit(w) === wanted || w.split('-').some(function (part) {
          return part !== '' && foldUnit(part) === wanted;
        }));
      });
    }

    /* "Sweet Potato Chocolate Brownies" before "squares" is "Brownie": the
       last word before any " with ...", a plain plural only. */
    function singularHead(text) {
      text = String(text);
      var cut = text.search(/\s+with\s+/i);
      var head = cut === -1 ? text : text.slice(0, cut);
      var tail = cut === -1 ? '' : text.slice(cut);
      var match = /^(.*?)([A-Za-zÀ-ɏ]+)$/.exec(head);
      if (!match || !/[^su]s$/i.test(match[2])) return text;
      var single = foldUnit(match[2]);
      if (!single || single === match[2].toLowerCase()) return text;
      if (/^[A-Z]/.test(match[2])) single = single.charAt(0).toUpperCase() + single.slice(1);
      return match[1] + single + tail;
    }

    /* The thing made said after the title's own noun, so before any " with
       ...": "Potato Cake pieces with Smoked Salmon", never "... Salmon pieces". */
    function thingAfterHead(text, thing) {
      var named = singularHead(text);
      var cut = named.search(/\s+with\s+/i);
      if (cut === -1) return { title: named, post: ' ' + thing };
      return { title: named.slice(0, cut) + ' ' + thing + named.slice(cut), post: '' };
    }

    /* The words around the recipe's name: `word` is what the number counts.
         [2] batches of 18 [Peanut Butter Cookies]    title names the thing
         [1] batch of 24 [Guinness ... Cake] squares  it does not: said after
         [2] × [Lemon Meringue Pie]                   one whole thing
         [2] jars of [Peanut Sauce]                   a container holds it
         [3] [Rainbow Confetti] traybakes             one thing that is it */
    function rowWords(url, text, n) {
      var out = { word: '', pre: '', title: text, post: '' };
      if (!isBatch(url)) {
        out.word = n === 1 ? 'portion of' : 'portions of';
        return out;
      }
      out.word = n > 1 ? 'batches of' : 'batch of';
      var made = RECIPES[url].m;
      if (!(made && made.kind === 'count' && made.stem)) return out;
      // "enough marinade for 4 portions of fish" says what it is for after the name.
      if (/^enough\s/i.test(String(made.prefix || ''))) {
        out.post = ', ' + made.prefix + ' ' + made.box + ' ' + made.stem + String(made.rest || '');
        return out;
      }

      var words = String(made.stem).split(/\s+/);
      var group = made.invariable ? words.shift() : '';
      var noun = words.length ? words[words.length - 1] : '';
      var named = !noun || wordInTitle(noun, text);
      var before = words.slice(0, -1).filter(function (w) {
        return !wordInTitle(w, text);
      }).join(' ');
      var lead = (group ? group + ' ' : '') + (before ? before + ' ' : '');

      if (Number(made.base) === 1) {
        var times = made.times ? '× ' : '';
        if (!named && CONTAINER_NOUNS.indexOf(foldUnit(noun)) !== -1) {
          out.word = times + lead + (n > 1 ? unitLabel(noun, 2) : noun) + ' of';
          return out;
        }
        if (named) {
          out.word = group || '×';
          out.pre = before ? before + ' ' : '';
          return out;
        }
        out.word = (times + group).trim();
        out.pre = before ? before + ' ' : '';
        var thing = thingAfterHead(text, n > 1 ? unitLabel(noun, 2) : noun);
        out.title = thing.title;
        out.post = thing.post;
        return out;
      }

      // `makes: "3 batches (...)"` counts batches already.
      if (!made.box || /^batch/i.test(String(made.stem))) return out;
      out.pre = made.box + ' ' + (group ? group + ' ' : '');
      if (!named) {
        var said = thingAfterHead(text, words.join(' ') + String(made.rest || ''));
        out.title = said.title;
        out.post = said.post;
      }
      return out;
    }

    function recipeLink(url, text, href) {
      return '<a class="shopping-list-recipe-link" href="' +
        esc(href || hrefs[url] || url) + '">' + esc(text || title(url)) + '</a>';
    }

    // Everything after the box; the caller rewrites it in place as a number
    // is typed, so the box is never re-rendered under the caret.
    function rowInner(url, n, href) {
      var words = rowWords(url, title(url), n);
      return '<span class="shopping-list-count-word">' +
        esc(words.word) + '</span>' + (words.word ? ' ' : '') +
        esc(words.pre) + recipeLink(url, words.title, href) + esc(words.post);
    }

    // What a screen reader is told the box counts: it cannot move with the number.
    function boxLabel(url) {
      var made = RECIPES[url] && RECIPES[url].m;
      var single = made && made.kind === 'count' && Number(made.base) === 1 && made.stem;
      return single ? 'how many: ' : 'batches of ';
    }

    function yieldText(url) {
      var r = recipe(url);
      if (!r || !r.y) return '';
      return (r.k || 'serves') + ' ' + r.y;
    }

    /* The number box for a row, or '' for a recipe that cannot be scaled.
       `data` is extra attribute text, already escaped. The yield goes in the
       box's title and label, never beside the name: "7 Moules serves 4"
       reads as 7 × 4. */
    function boxHtml(url, n, data) {
      var name = title(url);
      var extra = data ? ' ' + data : '';
      if (isBatch(url)) {
        var floor = halfOffered(url) ? '0.5' : '1';
        var makes = RECIPES[url].y ? ', which makes ' + RECIPES[url].y : '';
        return '<input type="number" class="shopping-list-portions" min="' + floor +
          '" max="99" step="' + floor + '" inputmode="decimal" value="' + n + '" ' +
          'data-url="' + esc(url) + '" data-batches' + extra + ' ' +
          'title="' + esc(name + makes) + '" ' +
          'aria-label="' + esc(boxLabel(url) + name + makes) + '">';
      }
      if (!hasPortions(url)) return '';
      var yielded = yieldText(url);
      var relative = yielded ? ', which ' + yielded : '';
      return '<input type="number" class="shopping-list-portions" min="1" max="99" step="1" ' +
        'inputmode="numeric" value="' + n + '" ' +
        'data-url="' + esc(url) + '"' + extra + ' ' +
        'title="' + esc(name + relative) + '" ' +
        'aria-label="portions of ' + esc(name + relative) + '">';
    }

    // A recipe with no portion count adds its ingredients once, and says why.
    function unscalableHtml(url, href) {
      return '<span>' + recipeLink(url, title(url), href) +
        '<span class="shopping-list-yield-missing">' +
        'no serving size — open <code>serves:</code> with a number</span></span>';
    }

    /* One recipe's lines as build() takes them; `recipe` and the four marks
       are #1297's, `rate` #1458's. */
    function entries(url, factor) {
      return ((RECIPES[url] || {}).i || []).map(function (ing) {
        return {
          amount: ing.a, name: ing.n, aisle: ing.s, scale: factor,
          people: !isBatch(url) && hasPortions(url) ? RECIPES[url].p * factor : null,
          recipe: url, parts: ing.pt, fruit: ing.f, count: ing.c, pointer: ing.x,
          rate: ing.r
        };
      });
    }

    // " @ £1.80 a portion" or " @ £4.20 a batch" (#1458), from the recipe as
    // written; '' where nothing is costed.
    function costSuffix(url) {
      if (!options.costUnits) return '';
      var per = isBatch(url) ? 1 : (hasPortions(url) ? RECIPES[url].p : 0);
      var each = foodShoppingList.recipeCost(entries(url, 1), per, options);
      if (!each) return '';
      return ' @ ' + each.text + (isBatch(url) ? ' a batch' : ' a portion');
    }

    // The sentence and its price in one inline box, so the price wraps with it.
    function withCost(url, sentence) {
      var text = costSuffix(url);
      if (!text) return sentence;
      return '<span>' + sentence +
        '<span class="shopping-list-cost">' + esc(text) + '</span></span>';
    }

    function build(list) {
      return foodShoppingList.build(list, options);
    }

    // A row's breakdown: a chevron beside it, and the recipes it is for under
    // it. Its own button, since a tap on the line ticks it (#1521).
    function fromToggleHtml(row, id, open) {
      return '<button type="button" class="shopping-list-from-toggle" data-from-toggle="' + esc(row.key) +
        '" aria-expanded="' + open + '" aria-controls="' + id + '" aria-label="' +
        esc('which recipes use ' + row.label) + '"></button>';
    }

    function fromHtml(row, id, open) {
      return '<p class="shopping-list-from" id="' + id + '"' + (open ? '' : ' hidden') + '>for ' +
        row.recipes.map(function (url) { return recipeLink(url); }).join(', ') + '</p>';
    }

    /* The aisles as markup. `ticks` gives each row its box and class (#1457):
       `box(key)` and `rowClass(key)`. `from`, if given, adds each row's
       breakdown: `open(key)` says whether it starts open. */
    function aislesHtml(aisles, ticks, from) {
      var n = 0;
      return aisles.map(function (aisle) {
        return '<section class="shopping-list-aisle">' +
          '<h3 class="shopping-list-aisle-name">' + esc(aisle.label) + '</h3>' +
          '<ul class="shopping-list-items">' +
          aisle.items.map(function (row) {
            var broken = from && row.recipes && row.recipes.length;
            var id = 'shopping-from-' + (n += 1);
            var open = !!(broken && from.open(row.key));
            if (!broken) {
              return '<li class="shopping-list-row' + ticks.rowClass(row.key) + '">' +
                rowLineHtml(row, ticks, '') + unscaledHtml(row, 'span') + priceHtml(row) + '</li>';
            }
            // The bracket goes under the line here, beside the breakdown it
            // belongs with, so the line has room for its chevron on a phone.
            return '<li class="shopping-list-row shopping-list-row--from' + ticks.rowClass(row.key) + '">' +
              '<div class="shopping-list-row-main">' + rowLineHtml(row, ticks, fromToggleHtml(row, id, open)) +
              priceHtml(row) + '</div>' + unscaledHtml(row, 'p') + fromHtml(row, id, open) + '</li>';
          }).join('') +
          '</ul></section>';
      }).join('');
    }

    function rowLineHtml(row, ticks, toggle) {
      return '<label class="shopping-list-line">' + ticks.box(row.key) +
        '<span class="shopping-list-amount">' + esc(row.text) + '</span>' +
        '<span class="shopping-list-name">' + esc(row.label) + '</span>' +
        (row.aside ? '<span class="shopping-list-aside">(' + esc(row.aside) + ')</span>' : '') +
        '</label>' + toggle;
    }

    // Outside the label, so following a link never ticks the row.
    function unscaledHtml(row, tag) {
      if (!row.unscaledRecipes || !row.unscaledRecipes.length) return '';
      return '<' + tag + ' class="shopping-list-unscaled">(' +
        row.unscaledRecipes.map(function (url) { return recipeLink(url); }).join(', ') + ')</' + tag + '>';
    }

    function priceHtml(row) {
      if (!row.cost || !row.cost.text) return '';
      return '<span class="shopping-list-price">' + shoppingList.moneyHtml(row.cost.text, esc) + '</span>';
    }

    // "(Not scaled: salt, olive oil)", or '' where everything scaled.
    function unscaledNote(aisles) {
      var names = [];
      aisles.forEach(function (aisle) {
        aisle.items.forEach(function (row) {
          if (row.unquantified.length) names.push(row.label);
        });
      });
      return names.length ? '(Not scaled: ' + names.join(', ') + ')' : '';
    }

    /* What the shop comes to (#1458): `text`, and the `sum` that
       shoppingList.drawTotal names the unpriced lines from (#1523). null
       where nothing is costed. */
    function total(rows) {
      var sum = options.costUnits ? foodShoppingList.costTotal(rows) : null;
      if (!sum) return null;
      return { text: (sum.partial ? '' : 'roughly ') + sum.text, sum: sum };
    }

    return {
      has: function (url) { return Object.prototype.hasOwnProperty.call(RECIPES, url); },
      title: title,
      hasPortions: hasPortions, isBatch: isBatch, halfOffered: halfOffered,
      defaultCount: defaultCount, count: count, scale: scale,
      batchCount: batchCount, portionCount: portionCount,
      rowWords: rowWords, rowInner: rowInner, recipeLink: recipeLink,
      boxHtml: boxHtml, unscalableHtml: unscalableHtml, withCost: withCost,
      entries: entries, build: build, aislesHtml: aislesHtml,
      unscaledNote: unscaledNote, total: total
    };
  }

  return { create: create };
});
