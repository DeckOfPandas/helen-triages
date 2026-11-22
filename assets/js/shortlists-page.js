// shortlists-page.js: the DOM of food/shortlists.html (#1521). MANUAL §8.9.
// The lists are HTF.lists (shortlists-store.js), what to show for them is
// HTF.listsView (shortlists-view.js), every shopping word and total is
// HTF.foodShoppingRows, and links are HTF.listsShare (shortlists-share.js):
// this file draws and listens, and decides nothing a test could not reach
// through those four.
//
// The address decides the page: the overview (every list, and the plan made
// from them all), a list's own page at `?list=<id>`, or a shared link's
// `?shortlist=…` as a list page that keeps nothing until asked. Moving
// between them is following a link, so each survives a reload.

(function () {
  'use strict';

  var HTF = window.HTF;
  var root = document.querySelector('[data-shortlists]');
  if (!HTF || !HTF.lists || !HTF.listsView || !HTF.foodShoppingRows || !HTF.listsShare || !root) return;

  var lists = HTF.lists;
  var V = HTF.listsView;
  var EVERYTHING = V.EVERYTHING;
  var esc = HTF.escapeHtml;

  function readJson(id, fallback) {
    var node = document.getElementById(id);
    if (!node) return fallback;
    try {
      return JSON.parse(node.textContent) || fallback;
    } catch (e) {
      console.warn('shortlists-page.js: could not parse #' + id + ' — ' + e.message);
      return fallback;
    }
  }

  var RECIPES = readJson('recipe-ingredients', {});
  var shoppingEl = root.querySelector('#shopping-list');

  function words(name) {
    return String((shoppingEl && shoppingEl.getAttribute(name)) || '').split(',').filter(Boolean);
  }

  var titles = {};
  var hrefs = {};
  Object.keys(RECIPES).forEach(function (url) {
    titles[url] = RECIPES[url].t || url;
    hrefs[url] = RECIPES[url].u || url;
  });

  var shop = HTF.foodShoppingRows.create({
    recipes: RECIPES, titles: titles, hrefs: hrefs, escape: esc,
    containerNouns: words('data-container-nouns'),
    buildOptions: {
      aisles: readJson('recipe-aisles', []),
      wholeMeasures: words('data-whole-measures'),
      quarterMeasures: words('data-quarter-measures'),
      countNouns: words('data-count-nouns'),
      costUnits: readJson('food-cost-units', null)
    }
  });

  var indexUrl = root.getAttribute('data-index-url') || '';
  var overviewUrl = location.pathname;
  var crumbsEl = root.querySelector('[data-shortlists-crumbs]');
  var headEl = root.querySelector('[data-shortlists-head]');
  var summaryEl = root.querySelector('[data-shortlists-summary]');
  var overviewEl = root.querySelector('[data-shortlists-overview]');
  var contentsEl = root.querySelector('[data-shortlists-contents]');
  var newBtn = root.querySelector('[data-shortlists-new]');
  var arrangeBtn = root.querySelector('[data-shortlists-arrange]');
  var newProblem = root.querySelector('[data-shortlists-new-problem]');
  var body = root.querySelector('[data-shortlists-body]');
  var pagerEl = root.querySelector('[data-shortlists-pager]');
  var shareEl = root.querySelector('[data-shortlists-share]');
  var aislesEl = shoppingEl.querySelector('.shopping-list-aisles');
  var noteEl = shoppingEl.querySelector('.shopping-list-note');
  var totalEl = shoppingEl.querySelector('.shopping-list-total');
  var untickBtn = shoppingEl.querySelector('.shopping-list-untick');
  var dialog = root.querySelector('[data-shortlists-delete]');
  var pill = root.querySelector('[data-shortlists-pill]');
  var pillDown = pill.querySelector('[data-shortlists-pill-down]');
  var pillUp = pill.querySelector('[data-shortlists-pill-up]');
  var live = root.querySelector('[data-shortlists-live]');
  var pageTitle = document.title;

  var renaming = false;
  var adding = false;
  var arranging = false;

  function announce(text) {
    live.textContent = '';
    setTimeout(function () { live.textContent = text; }, 50);
  }

  function nameOf(id) {
    var list = lists.get(id);
    return list ? list.name : '';
  }

  function problemText(problem, name) {
    return V.nameProblemText(problem, name, lists.all());
  }

  function listHref(id) {
    return V.pageUrl(overviewUrl, id);
  }

  function recipeHref(url, id) {
    return V.listUrl(hrefs[url] || url, id);
  }

  // A list's colour is a class, `list-hue-N`; the stylesheet holds the hues.
  function hueClass(hue) {
    return hue < 0 ? '' : ' list-hue-' + hue;
  }

  // --- which page --------------------------------------------------------------

  var share = HTF.listsShare;
  var SHARED = 'shared';
  var bySlug = {};
  Object.keys(RECIPES).forEach(function (url) { bySlug[share.slugOf(url)] = url; });

  // A read link's slugs as this site's recipes, at the link's portions or
  // each recipe's own; `missing` counts the slugs the site lacks.
  function resolve(read) {
    var items = [];
    var missing = 0;
    read.items.forEach(function (item) {
      var url = bySlug[item.slug];
      if (!url) { missing += 1; return; }
      items.push({ recipe: url, portions: item.portions || shop.defaultCount(url) });
    });
    return { name: read.name, items: items, missing: missing };
  }

  var fromLink = share.read(location.search);
  var shared = fromLink ? resolve(fromLink) : null;
  var sharedTicks = [];
  var listId = shared ? '' : ((/[?&]list=([a-z0-9]+)/.exec(location.search) || [])[1] || '');

  function sharedName() {
    return shared.name || lists.UNNAMED;
  }

  // The scope of the rows, the shopping list and its ticks.
  function scope() {
    return shared ? SHARED : (listId || EVERYTHING);
  }

  function rowsFor(view) {
    if (view !== SHARED) return V.rows(lists.all(), view);
    return shared.items.map(function (item) {
      return { list: SHARED, recipe: item.recipe, portions: item.portions };
    });
  }

  // --- the rows -------------------------------------------------------------------

  // A row moves by its grip: dragged (drag-reorder.js), or focused and moved
  // with the up and down arrows.
  function gripHtml(name) {
    return '<button type="button" class="reorder-grip" data-reorder-grip aria-label="' +
      esc('move ' + name) + '" aria-describedby="shortlists-move-help"></button>';
  }

  // The recipe page's − box +, the same shape (shared/_rule.scss's scale-step).
  function stepperHtml(url, n, list) {
    var name = titles[url] || url;
    return '<span class="shortlists-stepper">' +
      '<button type="button" class="shortlists-step" data-step="-1" aria-label="' + esc('one fewer: ' + name) + '"' +
      (shop.stepCount(url, n, -1) === n ? ' disabled' : '') + '>&minus;</button>' +
      shop.boxHtml(url, n, 'data-list="' + esc(list) + '"') +
      '<button type="button" class="shortlists-step" data-step="1" aria-label="' + esc('one more: ' + name) + '"' +
      (shop.stepCount(url, n, 1) === n ? ' disabled' : '') + '>+</button></span>';
  }

  // "£10.24", and under it the range, small and grey; '' where nothing is costed.
  function priceHtml(cost) {
    if (!cost) return '';
    var cut = cost.text.indexOf(' (');
    if (cut < 0) return '<span class="shortlists-price-mean">' + esc(cost.text) + '</span>';
    return '<span class="shortlists-price-mean">' + esc(cost.text.slice(0, cut)) + '</span>' +
      '<span class="shortlists-price-range">' + esc(cost.text.slice(cut + 1)) + '</span>';
  }

  function rowCost(row) {
    return shop.has(row.recipe) && shop.boxHtml(row.recipe, 1) ?
      shop.rowCost(row.recipe, shop.count(row.recipe, row.portions)) : null;
  }

  // What some rows cost: a list's subtotal, or every list's added.
  function costOf(someRows) {
    return shop.sumCosts(someRows.map(rowCost));
  }

  function costText(someRows) {
    var cost = costOf(someRows);
    return cost ? cost.text.split(' (')[0] : '';
  }

  /* One recipe in columns: grip, − n +, unit, name, price, ×. `movable` only
     on a list's own page, with two rows or more; a shared link's rows show
     their count and nothing to change. */
  function rowHtml(row, listName, movable) {
    var url = row.recipe;
    var title = titles[url] || url.replace(/\/$/, '').split('/').pop();
    var editable = row.list !== SHARED;
    var remove = editable ? '<button type="button" class="shortlists-remove" data-remove ' +
      'aria-label="remove ' + esc(title + ' from ' + listName) + '"></button>' : '<span></span>';
    var attrs = 'class="shortlists-recipe" data-list="' + esc(row.list) + '" data-url="' + esc(url) + '"' +
      (movable ? ' data-reorder-item' : '');
    var grip = movable ? gripHtml(title) : '<span></span>';
    if (!shop.has(url)) {
      return '<li ' + attrs + '>' + grip + '<span></span><span></span><span class="shortlists-name shortlists-gone">' +
        esc(title) + ' <span class="shopping-list-yield-missing">is no longer on the site</span></span><span></span>' +
        remove + '</li>';
    }
    var n = shop.count(url, row.portions);
    var href = editable ? recipeHref(url, row.list) : hrefs[url];
    if (!shop.boxHtml(url, n)) {
      return '<li ' + attrs.replace('class="', 'class="shopping-list-recipe--unscalable ') + '>' + grip +
        '<span></span><span></span><span class="shortlists-name">' + shop.unscalableHtml(url, href) + '</span>' +
        '<span></span>' + remove + '</li>';
    }
    var count = editable ? stepperHtml(url, n, row.list) :
      '<span class="shortlists-stepper"><span class="shortlists-shared-count">' + n + '</span></span>';
    return '<li ' + attrs + '>' + grip + count +
      '<span class="shortlists-unit">' + esc(shop.unitText(url, n)) + '</span>' +
      '<span class="shortlists-name">' + shop.nameHtml(url, n, href) + '</span>' +
      '<span class="shortlists-price">' + priceHtml(shop.rowCost(url, n)) + '</span>' + remove + '</li>';
  }

  function totalHtml(label, cost, attr) {
    if (!cost) return '';
    return '<p class="shortlists-subtotal" ' + attr + '><span class="shortlists-subtotal-label">' + esc(label) +
      '</span><span class="shortlists-price">' + priceHtml(cost) + '</span></p>';
  }

  function rowsHtml(rows, listName, movable) {
    return '<ul class="shortlists-rows">' + rows.map(function (row) {
      return rowHtml(row, listName, movable && rows.length > 1);
    }).join('') + '</ul>';
  }

  function recipesHtml(list, movable) {
    var rows = V.rows([list], list.id);
    if (!rows.length) {
      return '<p class="shortlists-empty">Nothing on ' + esc(list.name) + ' yet.</p>' +
        '<p class="shortlists-browse"><a class="shortlists-link" href="' +
        esc(V.intoUrl(indexUrl, list.id)) + '">Browse recipes to fill it</a></p>';
    }
    return rowsHtml(rows, list.name, movable) +
      totalHtml('subtotal', costOf(rows), 'data-subtotal="' + esc(list.id) + '"');
  }

  // --- the cards -----------------------------------------------------------------
  // The index's rows, cloned once each from the page's <template> and kept, so
  // a redraw moves a card rather than making a new one under an open picker.

  var cardTemplate = document.querySelector('template[data-shortlists-cards]');
  var cards = {};
  if (cardTemplate) {
    Array.prototype.forEach.call(cardTemplate.content.querySelectorAll('li[data-url]'), function (li) {
      cards[li.getAttribute('data-url')] = li;
    });
  }

  function cardFor(url) {
    var card = cards[url];
    if (card && card.ownerDocument !== document) {
      card = cards[url] = document.importNode(card, true);
      card.removeAttribute('data-url');
      card.setAttribute('data-card', url);
    }
    return card || null;
  }

  function placeCards(list) {
    var slot = body.querySelector('[data-cards]');
    if (!slot) return;
    list.items.forEach(function (item) {
      var card = cardFor(item.recipe);
      if (card) slot.appendChild(card);
    });
    if (HTF.shortlistPicker) HTF.shortlistPicker.paint(slot);
  }

  // --- the heading -----------------------------------------------------------------
  // A list's name over the site's ruled underline, the list's colour first
  // (the stylesheet's); everything's over the band of every list's colour.

  function markedName(name) {
    return '<span class="shortlists-marked">' + esc(name) + '</span>';
  }

  function bandHtml(hues) {
    return '<span class="shortlists-band" aria-hidden="true">' +
      hues.map(function (hue) { return '<span class="' + hueClass(hue).trim() + '"></span>'; }).join('') +
      '</span>';
  }

  function headingHtml(classes, inner) {
    return '<h1 class="shortlists-heading' + classes + '" id="shortlists-heading" tabindex="-1">' + inner + '</h1>';
  }

  function renameFormHtml(list) {
    return '<form class="shortlists-name-form" data-rename-form>' +
      '<label class="shortlists-name-label" for="shortlists-rename-name">Rename ' + esc(list.name) + '</label>' +
      '<span class="shortlists-name-row">' +
      '<input type="text" id="shortlists-rename-name" class="shortlists-name-input" maxlength="' +
      lists.NAME_MAX + '" value="' + esc(list.name) + '" autocomplete="off" spellcheck="false" ' +
      'aria-describedby="shortlists-rename-problem">' +
      '<button type="submit" class="shortlists-text-button">save</button>' +
      '<button type="button" class="shortlists-text-button" data-rename-cancel>cancel</button>' +
      '</span><span class="shortlists-name-problem" id="shortlists-rename-problem" aria-live="polite"></span>' +
      '</form>';
  }

  // "shortlists / <name> ▾": the ▾ shows every list as a link, this one marked.
  function crumbsHtml(current, currentId) {
    return '<a class="shortlists-crumb" href="' + esc(overviewUrl) + '">shortlists</a>' +
      '<span class="shortlists-crumb-sep" aria-hidden="true">/</span>' +
      '<span class="shortlists-crumb-current">' + esc(current) + '</span>' +
      '<button type="button" class="shortlists-crumb-more" aria-expanded="false" aria-controls="shortlists-menu" ' +
      'aria-label="your lists" data-crumb-more></button>' +
      '<ul class="shortlists-menu" id="shortlists-menu" hidden>' +
      lists.all().map(function (list) {
        return '<li class="' + hueClass(V.hueOf(list.id)).trim() + '"><a href="' + esc(listHref(list.id)) + '"' +
          (list.id === currentId ? ' aria-current="page"' : '') + '>' + esc(list.name) + '</a></li>';
      }).join('') + '</ul>';
  }

  function closeMenu(refocus) {
    var more = crumbsEl.querySelector('[data-crumb-more]');
    if (!more || more.getAttribute('aria-expanded') !== 'true') return;
    more.setAttribute('aria-expanded', 'false');
    crumbsEl.querySelector('.shortlists-menu').hidden = true;
    if (refocus) more.focus();
  }

  crumbsEl.addEventListener('click', function (ev) {
    var more = ev.target.closest('[data-crumb-more]');
    if (!more) return;
    var open = more.getAttribute('aria-expanded') !== 'true';
    more.setAttribute('aria-expanded', String(open));
    crumbsEl.querySelector('.shortlists-menu').hidden = !open;
    if (open) {
      var first = crumbsEl.querySelector('.shortlists-menu a');
      if (first) first.focus();
    }
  });

  crumbsEl.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape') closeMenu(true);
  });

  document.addEventListener('click', function (ev) {
    if (!crumbsEl.contains(ev.target)) closeMenu(false);
  });

  // --- the overview's list of lists --------------------------------------------------

  function lineHtml(list) {
    var rows = V.rows([list], list.id);
    return '<li class="shortlists-line' + hueClass(V.hueOf(list.id)) + '" data-id="' + esc(list.id) + '"' +
      (arranging ? ' data-reorder-item' : '') + '>' +
      (arranging ? gripHtml(list.name) : '<span></span>') +
      '<span class="shortlists-mark" aria-hidden="true"></span>' +
      '<a class="shortlists-line-name" href="' + esc(listHref(list.id)) + '">' + esc(list.name) + '</a>' +
      '<span class="shortlists-line-count">' + V.countText(list.items.length) + '</span>' +
      '<span class="shortlists-price">' + priceHtml(costOf(rows)) + '</span></li>';
  }

  // The blank line "+ new list" adds, typed on directly.
  function newLineHtml() {
    return '<li class="shortlists-line shortlists-line--new"><span></span>' +
      '<span class="shortlists-mark" aria-hidden="true"></span>' +
      '<span class="shortlists-line-name">' +
      '<label class="visually-hidden" for="shortlists-new-name">Name your new list, then press Enter</label>' +
      '<input type="text" id="shortlists-new-name" class="shortlists-new-input" maxlength="' + lists.NAME_MAX +
      '" placeholder="name your new list" autocomplete="off" spellcheck="false" enterkeyhint="done" ' +
      'aria-describedby="shortlists-new-problem"></span><span></span><span></span></li>';
  }

  function renderContents() {
    var all = lists.all();
    contentsEl.innerHTML = all.map(lineHtml).join('') + (adding ? newLineHtml() : '');
    contentsEl.classList.toggle('is-arranging', arranging);
    arrangeBtn.hidden = all.length < 2;
    arrangeBtn.textContent = arranging ? 'done' : 'arrange';
    arrangeBtn.setAttribute('aria-pressed', String(arranging));
    newBtn.hidden = arranging;
  }

  // --- the three pages ---------------------------------------------------------------

  function renderOverview() {
    var all = lists.all();
    document.title = pageTitle;
    crumbsEl.hidden = true;
    headEl.innerHTML = headingHtml(' shortlists-heading--everything',
      '<span class="shortlists-marked shortlists-marked--band">everything' +
      (all.length ? bandHtml(all.map(function (list) { return V.hueOf(list.id); })) : '') + '</span>');
    summaryEl.textContent = all.length ? V.overviewText(all, costText(V.rows(all, EVERYTHING))) : '';
    summaryEl.hidden = !all.length;
    overviewEl.hidden = false;
    renderContents();
    var full = all.filter(function (list) { return list.items.length; });
    body.innerHTML = !all.length ? '<p class="shortlists-empty">No shortlists yet. Start one with “+ new list”.</p>' :
      full.map(function (list) {
        return '<section class="shortlists-section">' +
          '<h2 class="shortlists-section-name' + hueClass(V.hueOf(list.id)) + '">' +
          '<a class="shortlists-section-link" href="' + esc(listHref(list.id)) + '">' + markedName(list.name) + '</a>' +
          '<span class="shortlists-section-count">' + V.countText(list.items.length) + '</span></h2>' +
          recipesHtml(list) + '</section>';
      }).join('') +
      totalHtml('all lists', costOf(V.rows(all, EVERYTHING)), 'data-total');
    pagerEl.hidden = true;
    shareEl.hidden = false;
    renderShare();
  }

  function renderList(list) {
    document.title = list.name + ' · ' + pageTitle;
    crumbsEl.innerHTML = crumbsHtml(list.name, list.id);
    crumbsEl.hidden = false;
    headEl.innerHTML = headingHtml(hueClass(V.hueOf(list.id)), markedName(list.name)) +
      '<span class="shortlists-actions">' +
      '<button type="button" class="shortlists-text-button" data-rename aria-label="rename ' + esc(list.name) + '">rename</button>' +
      '<button type="button" class="shortlists-text-button" data-delete aria-label="delete ' + esc(list.name) + '">delete</button>' +
      '<button type="button" class="shortlists-text-button" data-share-list aria-label="copy a link to ' + esc(list.name) + '">share</button>' +
      '</span>' + (renaming ? renameFormHtml(list) : '');
    summaryEl.textContent = V.listText(list, costText(V.rows([list], list.id)));
    summaryEl.hidden = false;
    overviewEl.hidden = true;
    body.innerHTML = (list.items.length ? '<ul class="recipe-list recipe-related shortlists-cards" data-cards></ul>' +
      '<h2 class="shortlists-subheading">how much</h2>' : '') + recipesHtml(list, true);
    placeCards(list);
    var near = V.neighbours(lists.all(), list.id);
    pagerEl.innerHTML = (near.previous ? '<a class="shortlists-pager-link" rel="prev" href="' + esc(listHref(near.previous.id)) +
      '">← ' + esc(near.previous.name) + '</a>' : '<span></span>') +
      (near.next ? '<a class="shortlists-pager-link shortlists-pager-link--next" rel="next" href="' +
        esc(listHref(near.next.id)) + '">' + esc(near.next.name) + ' →</a>' : '');
    pagerEl.hidden = !near.previous && !near.next;
    shareEl.hidden = true;
  }

  function renderShared() {
    var rows = rowsFor(SHARED);
    document.title = sharedName() + ' · ' + pageTitle;
    crumbsEl.innerHTML = crumbsHtml('shared: ' + sharedName(), '');
    crumbsEl.hidden = false;
    headEl.innerHTML = headingHtml('', markedName(sharedName()));
    summaryEl.textContent = V.listText(shared, costText(rows));
    summaryEl.hidden = false;
    overviewEl.hidden = true;
    body.innerHTML = '<p class="shortlists-shared-note">Sent to you as a link. Nothing here is kept until you keep it.</p>' +
      '<p class="shortlists-shared-actions">' +
      '<button type="button" class="shortlists-text-button" data-keep-shared>keep these</button>' +
      '<button type="button" class="shortlists-text-button" data-drop-shared>not now</button></p>' +
      (shared.missing ? '<p class="shortlists-count">' + esc(V.missingText(shared.missing)) + '</p>' : '') +
      (rows.length ? rowsHtml(rows, sharedName(), false) + totalHtml('subtotal', costOf(rows), '') : '');
    pagerEl.hidden = true;
    shareEl.hidden = true;
  }

  function render() {
    var list = listId ? lists.get(listId) : null;
    if (listId && !list) {
      // Gone, from this page or another: the overview, at its own address.
      listId = '';
      if (window.history && history.replaceState) history.replaceState(null, '', overviewUrl);
    }
    if (shared) renderShared();
    else if (list) renderList(list);
    else renderOverview();
    renderShopping(scope());
    placePill();
    if (HTF.tagShapes) HTF.tagShapes();
  }

  // After a typed number: the subtotals, the total and the summary, in place.
  function refreshTotals() {
    Array.prototype.forEach.call(body.querySelectorAll('[data-subtotal]'), function (el) {
      var list = lists.get(el.getAttribute('data-subtotal'));
      el.querySelector('.shortlists-price').innerHTML = priceHtml(list && costOf(V.rows([list], list.id)));
    });
    var total = body.querySelector('[data-total]');
    if (total) total.querySelector('.shortlists-price').innerHTML = priceHtml(costOf(V.rows(lists.all(), EVERYTHING)));
    var list = listId ? lists.get(listId) : null;
    if (list) summaryEl.textContent = V.listText(list, costText(V.rows([list], list.id)));
    else if (!shared) {
      summaryEl.textContent = V.overviewText(lists.all(), costText(V.rows(lists.all(), EVERYTHING)));
      renderContents();
    }
  }

  // --- the shopping list -----------------------------------------------------
  // A shared list's ticks are this page's alone, like the list.

  function tickedFor(view) {
    return view === SHARED ? sharedTicks.slice() : lists.ticked(view);
  }

  function setTickedFor(view, key, on) {
    if (view !== SHARED) { lists.setTicked(view, key, on); return; }
    sharedTicks = sharedTicks.filter(function (k) { return k !== key; });
    if (on) sharedTicks.push(key);
  }

  function untickFor(view) {
    if (view === SHARED) sharedTicks = [];
    else lists.untick(view);
  }

  function ticks(view) {
    var on = tickedFor(view);
    return {
      box: function (key) {
        return '<input type="checkbox" class="shopping-list-tick" data-key="' + esc(key) + '"' +
          (on.indexOf(key) !== -1 ? ' checked' : '') + '>';
      },
      rowClass: function (key) { return on.indexOf(key) !== -1 ? ' is-ticked' : ''; }
    };
  }

  function refreshUntick() {
    untickBtn.hidden = !aislesEl.querySelector('.shopping-list-tick:checked');
  }

  function renderShopping(view) {
    var entries = V.shoppingEntries(rowsFor(view), shop);
    shoppingEl.hidden = entries.length === 0;
    if (shoppingEl.hidden) return;
    var aisles = shop.build(entries);
    var shown = [];
    aisles.forEach(function (aisle) { shown = shown.concat(aisle.items); });
    noteEl.textContent = shop.unscaledNote(aisles);
    noteEl.hidden = !noteEl.textContent;
    aislesEl.innerHTML = shop.aislesHtml(aisles, ticks(view), {
      open: function (key) { return !!opened[key]; }
    });
    var sum = shop.total(shown);
    totalEl.textContent = '';
    if (sum) HTF.shoppingList.drawTotal(totalEl, sum.text, sum.sum);
    totalEl.hidden = !sum;
    refreshUntick();
  }

  // A recipe's new count is a new shop for its rows, on its list and overall.
  function recount(id, url) {
    var keys = [];
    shop.build(shop.entries(url, 1)).forEach(function (aisle) {
      aisle.items.forEach(function (row) { keys.push(row.key); });
    });
    lists.untick(id, keys);
    lists.untick(EVERYTHING, keys);
  }

  // A line's breakdown stays open through redraws, for this visit only.
  var opened = {};

  aislesEl.addEventListener('click', function (ev) {
    var toggle = ev.target.closest('[data-from-toggle]');
    if (!toggle) return;
    var open = toggle.getAttribute('aria-expanded') !== 'true';
    opened[toggle.getAttribute('data-from-toggle')] = open;
    toggle.setAttribute('aria-expanded', String(open));
    document.getElementById(toggle.getAttribute('aria-controls')).hidden = !open;
    placePill();
  });

  aislesEl.addEventListener('change', function (ev) {
    var box = ev.target;
    if (!box.classList.contains('shopping-list-tick')) return;
    setTickedFor(scope(), box.getAttribute('data-key'), box.checked);
    box.closest('li').classList.toggle('is-ticked', box.checked);
    refreshUntick();
  });

  untickBtn.addEventListener('click', function () {
    untickFor(scope());
    renderShopping(scope());
    var first = aislesEl.querySelector('.shopping-list-tick');
    if (first) first.focus();
  });

  // A card's own button (shortlist-picker.js) can put its recipe on or off
  // any list, this one included.
  document.addEventListener('htf:lists-change', render);

  // --- the scalers ------------------------------------------------------------
  // Only the row's cells are rewritten as a number is typed: re-rendering the
  // box under the caret loses it.

  body.addEventListener('input', function (ev) {
    var input = ev.target;
    if (!input.classList.contains('shopping-list-portions')) return;
    var row = input.closest('li[data-list]');
    var id = row.getAttribute('data-list');
    var url = input.getAttribute('data-url');
    var before = shop.count(url, lists.portions(id, url));
    var n;
    if (shop.isBatch(url)) {
      var typed = Number(input.value);
      n = shop.batchCount(url, input.value, before);
      if (n && !ev.inputType && typed > 1 && typed % 1 !== 0) input.value = String(n);
    } else {
      n = shop.portionCount(input.value);
    }
    if (!n) return;
    setCount(row, id, url, n, before);
  });

  function setCount(row, id, url, n, before) {
    lists.setPortions(id, url, n);
    row.querySelector('.shortlists-unit').textContent = shop.unitText(url, n);
    row.querySelector('.shortlists-name').innerHTML = shop.nameHtml(url, n, recipeHref(url, id));
    row.querySelector('.shortlists-price').innerHTML = priceHtml(shop.rowCost(url, n));
    row.querySelector('[data-step="-1"]').disabled = shop.stepCount(url, n, -1) === n;
    row.querySelector('[data-step="1"]').disabled = shop.stepCount(url, n, 1) === n;
    refreshTotals();
    if (n !== before) recount(id, url);
    renderShopping(scope());
    placePill();
  }

  // − and +: the box shows the new count, and focus stays on the button
  // unless it has reached its end.
  body.addEventListener('click', function (ev) {
    var step = ev.target.closest('[data-step]');
    if (!step) return;
    var row = step.closest('li[data-list]');
    var id = row.getAttribute('data-list');
    var url = row.getAttribute('data-url');
    var before = shop.count(url, lists.portions(id, url));
    var n = shop.stepCount(url, before, Number(step.getAttribute('data-step')));
    if (n === before) return;
    row.querySelector('.shopping-list-portions').value = String(n);
    setCount(row, id, url, n, before);
    if (step.disabled) row.querySelector('.shopping-list-portions').focus();
  });

  body.addEventListener('change', function (ev) {
    var input = ev.target;
    if (!input.classList.contains('shopping-list-portions')) return;
    var id = input.closest('li[data-list]').getAttribute('data-list');
    var url = input.getAttribute('data-url');
    input.value = String(shop.count(url, lists.portions(id, url)));
  });

  // --- a list's own actions ---------------------------------------------------------

  function focusHeading() {
    var heading = document.getElementById('shortlists-heading');
    if (heading) heading.focus();
  }

  body.addEventListener('click', function (ev) {
    var removeBtn = ev.target.closest('[data-remove]');
    if (!removeBtn) return;
    var row = removeBtn.closest('li[data-list]');
    var id = row.getAttribute('data-list');
    var url = row.getAttribute('data-url');
    lists.setMember(id, url, false);
    render();
    focusHeading();
    announce('Removed ' + (titles[url] || url) + ' from ' + nameOf(id) + '.');
  });

  headEl.addEventListener('click', function (ev) {
    if (ev.target.closest('[data-rename]')) {
      renaming = true;
      render();
      var input = document.getElementById('shortlists-rename-name');
      input.focus();
      input.select();
      return;
    }
    if (ev.target.closest('[data-rename-cancel]')) {
      renaming = false;
      render();
      headEl.querySelector('[data-rename]').focus();
      return;
    }
    if (ev.target.closest('[data-delete]')) { openDelete(listId); return; }
    var shareBtn = ev.target.closest('[data-share-list]');
    if (shareBtn) copyLink(shareBtn, share.link(location.origin + overviewUrl, lists.get(listId)));
  });

  headEl.addEventListener('submit', function (ev) {
    var form = ev.target.closest('[data-rename-form]');
    if (!form) return;
    ev.preventDefault();
    var input = form.querySelector('input');
    var outcome = lists.rename(listId, input.value);
    if (outcome.error) {
      form.querySelector('.shortlists-name-problem').textContent =
        problemText(outcome.error, lists.core.cleanName(input.value));
      input.focus();
      return;
    }
    renaming = false;
    render();
    focusHeading();
    announce('Renamed to ' + nameOf(listId) + '.');
  });

  headEl.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape' && ev.target.closest('[data-rename-form]')) {
      renaming = false;
      render();
      headEl.querySelector('[data-rename]').focus();
    }
  });

  // "share" copies the list's link, and says so; with no clipboard, the link
  // is offered to copy by hand.
  function copyLink(button, link) {
    var said = button.textContent;
    function done() {
      button.textContent = 'copied ✓';
      announce('Link copied.');
      setTimeout(function () { button.textContent = said; }, 1500);
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(link).then(done, function () { window.prompt('Copy this link:', link); });
    } else {
      window.prompt('Copy this link:', link);
    }
  }

  // --- moving rows and lists -----------------------------------------------------------
  // A grip with focus moves its row with the up and down arrows, Home and End.
  // After a move the rows are redrawn, so focus goes back to the moved grip.

  function rowsOf(container) {
    return Array.prototype.slice.call(container.querySelectorAll('[data-reorder-item]'));
  }

  function focusGrip(container, attribute, value) {
    var row = rowsOf(container).filter(function (el) { return el.getAttribute(attribute) === value; })[0];
    if (row) row.querySelector('[data-reorder-grip]').focus();
  }

  // Where a key sends the row at `at` of `total`, or null for a key that
  // does not move it.
  function keyTarget(key, at, total) {
    var to = { ArrowUp: at - 1, ArrowDown: at + 1, Home: 0, End: total - 1 }[key];
    if (to === undefined) return null;
    return Math.max(0, Math.min(total - 1, to));
  }

  function onGripKey(container, move) {
    container.addEventListener('keydown', function (ev) {
      var grip = ev.target.closest('[data-reorder-grip]');
      if (!grip) return;
      var row = grip.closest('[data-reorder-item]');
      var all = rowsOf(container);
      var to = keyTarget(ev.key, all.indexOf(row), all.length);
      if (to === null) return;
      ev.preventDefault();
      if (to !== all.indexOf(row)) move(row, to, true);
    });
  }

  function moveRecipe(row, to, refocus) {
    var id = row.getAttribute('data-list');
    var url = row.getAttribute('data-url');
    var total = rowsOf(body).length;
    lists.moveItem(id, url, to);
    render();
    if (refocus) focusGrip(body, 'data-url', url);
    announce(V.movedText(titles[url] || url, Math.max(0, Math.min(total - 1, to)), total));
  }

  function moveList(row, to, refocus) {
    var id = row.getAttribute('data-id');
    var total = lists.all().length;
    lists.moveList(id, to);
    render();
    if (refocus) focusGrip(contentsEl, 'data-id', id);
    announce(V.movedText(nameOf(id), Math.max(0, Math.min(total - 1, to)), total));
  }

  onGripKey(body, moveRecipe);
  onGripKey(contentsEl, moveList);

  if (HTF.dragReorder) {
    var dragOptions = { item: '[data-reorder-item]', grip: '[data-reorder-grip]' };
    HTF.dragReorder.attach(body, Object.assign({
      onDrop: function (row, from, to) { moveRecipe(row, to); }
    }, dragOptions));
    HTF.dragReorder.attach(contentsEl, Object.assign({
      onDrop: function (row, from, to) { moveList(row, to); }
    }, dragOptions));
  }

  // "arrange" puts a grip on every line of the overview's list; "done" takes
  // them off.
  arrangeBtn.addEventListener('click', function () {
    arranging = !arranging;
    adding = false;
    newProblem.textContent = '';
    renderContents();
    var grip = contentsEl.querySelector('[data-reorder-grip]');
    if (arranging && grip) grip.focus();
    announce(arranging ? 'Arranging: move a list by its handle.' : 'Done arranging.');
  });

  // --- a new list --------------------------------------------------------------------
  // A blank line at the end of the overview's list, typed on directly: Enter
  // makes the list and opens another blank line, so several can be made in a
  // row; Escape, or leaving it empty, takes it away. A refused name says why
  // under the list and keeps the typing.

  function newInput() {
    return contentsEl.querySelector('#shortlists-new-name');
  }

  function stopAdding(refocus) {
    adding = false;
    newProblem.textContent = '';
    renderContents();
    if (refocus) newBtn.focus();
  }

  newBtn.addEventListener('click', function () {
    adding = true;
    renderContents();
    newInput().focus();
  });

  contentsEl.addEventListener('input', function (ev) {
    if (ev.target.id !== 'shortlists-new-name') return;
    ev.target.removeAttribute('aria-invalid');
    newProblem.textContent = '';
  });

  contentsEl.addEventListener('keydown', function (ev) {
    var input = ev.target;
    if (input.id !== 'shortlists-new-name') return;
    if (ev.key === 'Escape') { stopAdding(true); return; }
    if (ev.key !== 'Enter') return;
    ev.preventDefault();
    var made = lists.create(input.value);
    if (made.error) {
      input.setAttribute('aria-invalid', 'true');
      newProblem.textContent = problemText(made.error, lists.core.cleanName(input.value));
      return;
    }
    render();
    newInput().focus();
    announce('Made ' + nameOf(made.id) + '.');
  });

  contentsEl.addEventListener('focusout', function (ev) {
    var input = ev.target;
    if (input.id === 'shortlists-new-name' && !input.value.trim()) {
      // After the click that moved focus, so a press on "+ new list" or a
      // link still lands.
      setTimeout(function () { if (adding && !newInput().value.trim() && document.activeElement !== newInput()) stopAdding(false); }, 0);
    }
  });

  // --- sharing and bringing in --------------------------------------------------------
  // Both ways in, the import box and "keep these", go through one preview,
  // which asks about each name already in use: keep both (the default),
  // merge, or leave it out.

  var shareOut = root.querySelector('[data-shortlists-share-out]');
  var exportEl = root.querySelector('[data-shortlists-export]');
  var copyBtn = root.querySelector('[data-shortlists-copy]');
  var importEl = root.querySelector('[data-shortlists-import]');
  var importProblem = root.querySelector('[data-shortlists-import-problem]');
  var previewEl = root.querySelector('[data-shortlists-preview-panel]');
  var pageBase = location.origin + overviewUrl;
  var incoming = null;
  var keeping = false;

  function renderShare() {
    var all = lists.all();
    shareOut.hidden = !all.length;
    exportEl.value = share.block(pageBase, all);
    copyBtn.hidden = !all.length || !(navigator.clipboard && navigator.clipboard.writeText);
  }

  exportEl.addEventListener('focus', function () { exportEl.select(); });

  copyBtn.addEventListener('click', function () {
    navigator.clipboard.writeText(exportEl.value).then(function () {
      copyBtn.textContent = 'copied';
      announce('Copied.');
      setTimeout(function () { copyBtn.textContent = 'copy'; }, 1200);
    }, function () { /* the box is still there to select by hand */ });
  });

  function clashOf(name) {
    var folded = lists.core.cleanName(name || lists.UNNAMED).toLowerCase();
    return lists.all().filter(function (list) { return list.name.toLowerCase() === folded; })[0] || null;
  }

  function choiceHtml(i, value, text, checked) {
    return '<label class="shortlists-preview-choice"><input type="radio" name="shortlists-preview-' + i +
      '" value="' + value + '"' + (checked ? ' checked' : '') + '> ' + esc(text) + '</label>';
  }

  function previewHtml() {
    return '<h2 class="shortlists-preview-title">' + (keeping ? 'Keeping ' : 'Bringing in ') +
      (incoming.length === 1 ? 'one list' : incoming.length + ' lists') + '</h2>' +
      incoming.map(function (list, i) {
        var name = list.name || lists.UNNAMED;
        var clash = clashOf(name);
        var html = '<fieldset class="shortlists-preview-list"><legend>' + esc(name) + ' · ' +
          V.countText(list.items.length) + '</legend>' +
          (list.missing ? '<p class="shortlists-preview-note">' + esc(V.missingText(list.missing)) + '</p>' : '');
        if (!clash) return html + '<p class="shortlists-preview-note">A new list, after yours.</p></fieldset>';
        var words = V.clashChoices(clash.name, lists.freeName(name));
        return html + '<p class="shortlists-preview-note">' + esc(words.question) + '</p>' +
          choiceHtml(i, 'new', words.both, true) + choiceHtml(i, 'merge', words.merge) +
          choiceHtml(i, 'skip', words.skip) + '</fieldset>';
      }).join('') +
      '<p class="shortlists-share-actions">' +
      '<button type="button" class="shortlists-text-button" data-preview-go>keep these</button>' +
      '<button type="button" class="shortlists-text-button" data-preview-cancel>cancel</button></p>';
  }

  function openPreview(list, fromShared) {
    incoming = list;
    keeping = fromShared;
    importProblem.textContent = '';
    previewEl.innerHTML = previewHtml();
    previewEl.hidden = false;
    goTo(previewEl);
  }

  function closePreview() {
    incoming = null;
    previewEl.hidden = true;
    previewEl.innerHTML = '';
  }

  root.querySelector('[data-shortlists-preview]').addEventListener('click', function () {
    var read = share.readBlock(importEl.value).map(resolve);
    if (!read.length) {
      closePreview();
      importProblem.textContent = 'There is no shortlist link in that. Paste what “Share or back up” gives you.';
      importEl.focus();
      return;
    }
    openPreview(read, false);
  });

  previewEl.addEventListener('click', function (ev) {
    if (ev.target.closest('[data-preview-cancel]')) {
      var back = keeping ? body.querySelector('[data-keep-shared]') : importEl;
      closePreview();
      if (back) back.focus();
      return;
    }
    if (!ev.target.closest('[data-preview-go]')) return;
    var plans = incoming.map(function (list, i) {
      var chosen = previewEl.querySelector('input[name="shortlists-preview-' + i + '"]:checked');
      var clash = clashOf(list.name);
      return { action: chosen ? chosen.value : 'new', name: list.name, into: clash && clash.id, items: list.items };
    });
    var ids = lists.bringIn(plans);
    var kept = keeping;
    closePreview();
    // A kept link goes to the list it made, or back to the overview.
    if (kept) { location.replace(ids.length ? listHref(ids[0]) : overviewUrl); return; }
    importEl.value = '';
    render();
    focusHeading();
    announce(V.broughtText(ids.length, kept));
  });

  body.addEventListener('click', function (ev) {
    if (!shared) return;
    if (ev.target.closest('[data-keep-shared]')) { openPreview([shared], true); return; }
    if (ev.target.closest('[data-drop-shared]')) location.replace(overviewUrl);
  });

  // --- delete -----------------------------------------------------------------------
  // Confirmed, then the overview.

  var deleting = null;

  function remove(id) {
    lists.remove(id);
    location.assign(overviewUrl);
  }

  function openDelete(id) {
    deleting = id;
    if (!dialog || typeof dialog.showModal !== 'function') {
      if (window.confirm('Delete ' + nameOf(id) + '?')) remove(id);
      return;
    }
    dialog.querySelector('[data-shortlists-delete-name]').textContent = nameOf(id);
    dialog.returnValue = '';
    dialog.showModal();
  }

  if (dialog) {
    dialog.addEventListener('close', function () {
      if (dialog.returnValue === 'delete' && deleting) remove(deleting);
      deleting = null;
    });
  }

  // --- the jump pill ----------------------------------------------------------------
  // "↓ shopping list" while its top is below the screen, "↑ recipes" once the
  // reader is in it with the recipes scrolled away; otherwise nothing.

  function reduceMotion() {
    return typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  function goTo(target) {
    target.scrollIntoView({ behavior: reduceMotion() ? 'auto' : 'smooth', block: 'start' });
    if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
    target.focus({ preventScroll: true });
  }

  function placePill() {
    if (shoppingEl.hidden) { pill.hidden = true; return; }
    var list = shoppingEl.getBoundingClientRect();
    var recipes = body.getBoundingClientRect();
    var below = list.top > window.innerHeight;
    var inIt = list.top < window.innerHeight / 2 && recipes.top < 0;
    pillDown.hidden = !below;
    pillUp.hidden = below || !inIt;
    pill.hidden = pillDown.hidden && pillUp.hidden;
  }

  pillDown.addEventListener('click', function () { goTo(shoppingEl); });
  pillUp.addEventListener('click', function () { goTo(body); });

  var queued = false;
  function soon() {
    if (queued) return;
    queued = true;
    window.requestAnimationFrame(function () { queued = false; placePill(); });
  }
  window.addEventListener('scroll', soon, { passive: true });
  window.addEventListener('resize', soon);

  // Back from a recipe, which may have changed the lists.
  window.addEventListener('pageshow', function (ev) {
    if (!ev.persisted) return;
    lists.refresh();
    render();
  });

  render();
  root.hidden = false;
  placePill();
})();
