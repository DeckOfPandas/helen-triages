// The recipe page's cost line (#1458), on a local build only: _layouts/recipe.html
// loads this, and emits #recipe-cost-data, only where `site.show_costs` is set.
//
// One portion of a `serves:` recipe, or one batch of a `makes:` one, priced
// from the recipe as written through HTF.foodShoppingList.recipeCost -- the
// shortlist's own arithmetic, so the page and the list cannot disagree. The
// figure does not move with the scaler. Where nothing could be priced the
// footer stays hidden, rules and all.

(function () {
  'use strict';

  var footer = document.querySelector('[data-recipe-cost]');
  var node = document.getElementById('recipe-cost-data');
  var line = footer && footer.querySelector('.recipe-cost');
  if (!footer || !node || !line || !window.HTF || !HTF.foodShoppingList) return;

  var data;
  try {
    data = JSON.parse(node.textContent);
  } catch (e) {
    console.warn('recipe-cost.js: could not parse #recipe-cost-data — ' + e.message);
    return;
  }

  var url = location.pathname;
  var entries = (data.i || []).map(function (ing) {
    return {
      amount: ing.a, name: ing.n, aisle: ing.s, scale: 1, recipe: url,
      parts: ing.pt, fruit: ing.f, count: ing.c, pointer: ing.x, rate: ing.r
    };
  });

  var each = HTF.foodShoppingList.recipeCost(entries, Number(data.per), {
    costUnits: data.units,
    wholeMeasures: data.wholeMeasures || [],
    quarterMeasures: data.quarterMeasures || []
  });
  if (!each) return;

  // "Roughly £4.09 (£2.26–£5.91) a portion in ingredients.", the drink page's
  // sentence; "From £2.19 a portion in ingredients, not counting 2 unpriced
  // items." where some line could not be priced.
  var figure = each.text.replace(/^from /, '');
  var missing = each.partial
    ? ', not counting ' + each.unpriced + (each.unpriced === 1 ? ' unpriced item' : ' unpriced items')
    : '';
  line.textContent = '';
  line.appendChild(document.createTextNode(each.partial ? 'From ' : 'Roughly '));
  var span = document.createElement('span');
  span.className = 'recipe-cost-figure';
  span.textContent = figure;
  line.appendChild(span);
  line.appendChild(document.createTextNode(
    (data.batch ? ' a batch' : ' a portion') + ' in ingredients' + missing + '.'));
  footer.hidden = false;
})();
