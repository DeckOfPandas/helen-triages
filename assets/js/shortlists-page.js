// shortlists-page.js: the DOM of food/shortlists.html (#1521). MANUAL §8.9.
// The lists are HTF.lists (shortlists-store.js), what to show for them is
// HTF.listsView (shortlists-view.js), and every shopping word and total is
// HTF.foodShoppingRows: this file draws and listens, and decides nothing a
// test could not reach through those three.
//
// The tabs are a WAI-ARIA tablist with automatic activation: arrows, Home and
// End move the selection, and only the selected tab is in the tab order. A tab
// is only ever tapped: lists move in "arrange", and a list's recipes on its own
// tab, by drag-reorder.js's grip or by each row's ↑/↓.
// Anything that re-renders closes the rename and new-list forms first, so a
// form is never left open on a list it does not belong to.

(function () {
  'use strict';

  var HTF = window.HTF;
  var root = document.querySelector('[data-shortlists]');
  if (!HTF || !HTF.lists || !HTF.listsView || !HTF.foodShoppingRows || !root) return;

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
  var tabsEl = root.querySelector('[data-shortlists-tabs]');
  var newBtn = root.querySelector('[data-shortlists-new]');
  var newForm = root.querySelector('[data-shortlists-new-form]');
  var newInput = newForm.querySelector('input');
  var newProblem = newForm.querySelector('.shortlists-name-problem');
  var panel = root.querySelector('[data-shortlists-panel]');
  var body = root.querySelector('[data-shortlists-body]');
  var aislesEl = shoppingEl.querySelector('.shopping-list-aisles');
  var noteEl = shoppingEl.querySelector('.shopping-list-note');
  var totalEl = shoppingEl.querySelector('.shopping-list-total');
  var untickBtn = shoppingEl.querySelector('.shopping-list-untick');
  var dialog = root.querySelector('[data-shortlists-delete]');
  var pill = root.querySelector('[data-shortlists-pill]');
  var pillDown = pill.querySelector('[data-shortlists-pill-down]');
  var pillUp = pill.querySelector('[data-shortlists-pill-up]');
  var live = root.querySelector('[data-shortlists-live]');

  var renaming = null;
  var deleting = null;

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

  // --- tabs ------------------------------------------------------------------

  function renderTabs(view) {
    tabsEl.innerHTML = V.tabs(lists.all(), view).map(function (tab) {
      return '<button type="button" role="tab" class="shortlists-tab' +
        (tab.selected ? ' is-selected' : '') + '" id="shortlists-tab-' + esc(tab.id) +
        '" data-tab="' + esc(tab.id) + '" data-tag-key="' + esc(tab.name) +
        '" aria-selected="' + tab.selected + '" aria-controls="shortlists-panel" tabindex="' +
        (tab.selected ? '0' : '-1') + '"><span class="tag-shape" aria-hidden="true"></span>' +
        '<span class="shortlists-tab-name">' + esc(tab.name) + '</span>' +
        '<span class="shortlists-tab-count"> · ' + tab.count + '</span></button>';
    }).join('');
    panel.setAttribute('aria-labelledby', 'shortlists-tab-' + view);
  }

  function selectedTab() {
    return tabsEl.querySelector('[aria-selected="true"]');
  }

  function select(id, focus) {
    lists.setView(id);
    closeNewForm();
    renaming = null;
    render();
    if (focus) selectedTab().focus();
  }

  tabsEl.addEventListener('click', function (ev) {
    var tab = ev.target.closest('[data-tab]');
    if (tab) select(tab.getAttribute('data-tab'), true);
  });

  tabsEl.addEventListener('keydown', function (ev) {
    var tabs = Array.prototype.slice.call(tabsEl.querySelectorAll('[data-tab]'));
    var at = tabs.indexOf(document.activeElement);
    if (at === -1) return;
    var to = { ArrowRight: at + 1, ArrowLeft: at - 1, Home: 0, End: tabs.length - 1 }[ev.key];
    if (to === undefined) return;
    ev.preventDefault();
    to = (to + tabs.length) % tabs.length;
    select(tabs[to].getAttribute('data-tab'), true);
  });

  // --- the panel -------------------------------------------------------------

  function recipeHref(url, id) {
    return V.listUrl(hrefs[url] || url, id);
  }

  // A grip to drag by (drag-reorder.js) and ↑/↓ for everyone else.
  function stepHtml(name, way, off) {
    return '<button type="button" class="reorder-step" data-move="' + way + '" aria-label="' +
      esc(V.moveLabel(name, way)) + '"' + (off ? ' disabled' : '') + '>' +
      (way === 'up' ? '↑' : '↓') + '</button>';
  }

  function handleHtml(name, at, total) {
    return '<span class="reorder-handle"><span class="reorder-grip" data-reorder-grip aria-hidden="true"></span>' +
      '<span class="reorder-steps">' + stepHtml(name, 'up', at === 0) +
      stepHtml(name, 'down', at === total - 1) + '</span></span>';
  }

  // `at` and `total` are given only where the row can be moved: a list's own tab.
  function rowHtml(row, listName, at, total) {
    var url = row.recipe;
    var title = titles[url] || url.replace(/\/$/, '').split('/').pop();
    var remove = '<button type="button" class="shortlists-text-button shortlists-remove" data-remove ' +
      'aria-label="remove ' + esc(title + ' from ' + listName) + '">remove</button>';
    var movable = total > 1;
    var attrs = 'class="shortlists-recipe" data-list="' + esc(row.list) + '" data-url="' + esc(url) + '"' +
      (movable ? ' data-reorder-item' : '');
    var handle = movable ? handleHtml(title, at, total) : '';
    if (!shop.has(url)) {
      return '<li ' + attrs + '>' + handle + '<span class="shortlists-gone">' + esc(title) +
        ' <span class="shopping-list-yield-missing">is no longer on the site</span></span>' + remove + '</li>';
    }
    var n = shop.count(url, row.portions);
    var box = shop.boxHtml(url, n, 'data-list="' + esc(row.list) + '"');
    if (!box) {
      return '<li ' + attrs.replace('class="', 'class="shopping-list-recipe--unscalable ') + '>' + handle +
        shop.unscalableHtml(url, recipeHref(url, row.list)) + remove + '</li>';
    }
    return '<li ' + attrs + '>' + handle + box +
      shop.withCost(url, '<span class="shortlists-words">' + shop.rowInner(url, n, recipeHref(url, row.list)) + '</span>') +
      remove + '</li>';
  }

  function recipesHtml(list, movable) {
    var rows = V.rows([list], list.id);
    if (!rows.length) {
      return '<p class="shortlists-empty">Nothing on ' + esc(list.name) + ' yet.</p>' +
        '<p class="shortlists-browse"><a class="shortlists-link" href="' +
        esc(V.intoUrl(indexUrl, list.id)) + '">Browse recipes to fill it</a></p>';
    }
    return '<ul class="shopping-list-recipes shortlists-recipes">' +
      rows.map(function (row, i) {
        return movable ? rowHtml(row, list.name, i, rows.length) : rowHtml(row, list.name);
      }).join('') + '</ul>';
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

  function listBody(list) {
    return '<div class="shortlists-head">' +
      '<h2 class="shortlists-heading" id="shortlists-heading" tabindex="-1">' + esc(list.name) + '</h2>' +
      '<span class="shortlists-actions">' +
      '<button type="button" class="shortlists-text-button" data-rename aria-label="rename ' + esc(list.name) + '">rename</button>' +
      '<button type="button" class="shortlists-text-button" data-delete aria-label="delete ' + esc(list.name) + '">delete</button>' +
      '</span></div>' +
      (renaming === list.id ? renameFormHtml(list) : '') +
      '<p class="shortlists-count">' + V.countText(list.items.length) + '</p>' +
      recipesHtml(list, true);
  }

  function everythingBody(all) {
    var head = '<div class="shortlists-head"><h2 class="shortlists-heading" id="shortlists-heading" tabindex="-1">Everything</h2></div>';
    if (!all.length) {
      return head + '<p class="shortlists-empty">No shortlists yet. Start one with “+ new list”.</p>';
    }
    var n = V.rows(all, EVERYTHING).length;
    return head +
      '<p class="shortlists-count">' + V.countText(n) + ' on ' + all.length + (all.length === 1 ? ' list' : ' lists') + '</p>' +
      all.map(function (list) {
        return '<section class="shortlists-section">' +
          '<h3 class="shortlists-section-name"><button type="button" class="shortlists-section-link" data-go="' +
          esc(list.id) + '">' + esc(list.name) + '</button>' +
          '<span class="shortlists-section-count">' + V.countText(list.items.length) + '</span></h3>' +
          recipesHtml(list) + '</section>';
      }).join('');
  }

  function renderBody(view) {
    var list = lists.get(view);
    body.innerHTML = list ? listBody(list) : everythingBody(lists.all());
  }

  // --- the shopping list -----------------------------------------------------

  function ticks(view) {
    var on = lists.ticked(view);
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
    var entries = V.shoppingEntries(V.rows(lists.all(), view), shop);
    shoppingEl.hidden = entries.length === 0;
    if (shoppingEl.hidden) return;
    var aisles = shop.build(entries);
    var shown = [];
    aisles.forEach(function (aisle) { shown = shown.concat(aisle.items); });
    noteEl.textContent = shop.unscaledNote(aisles);
    noteEl.hidden = !noteEl.textContent;
    aislesEl.innerHTML = shop.aislesHtml(aisles, ticks(view));
    var sum = shop.total(shown);
    totalEl.textContent = '';
    if (sum) HTF.shoppingList.drawTotal(totalEl, sum.text, sum.sum);
    totalEl.hidden = !sum;
    refreshUntick();
  }

  // A recipe's new count is a new shop for its rows, here and on everything.
  function recount(id, url) {
    var keys = [];
    shop.build(shop.entries(url, 1)).forEach(function (aisle) {
      aisle.items.forEach(function (row) { keys.push(row.key); });
    });
    lists.untick(id, keys);
    lists.untick(EVERYTHING, keys);
  }

  aislesEl.addEventListener('change', function (ev) {
    var box = ev.target;
    if (!box.classList.contains('shopping-list-tick')) return;
    lists.setTicked(lists.view(), box.getAttribute('data-key'), box.checked);
    box.closest('li').classList.toggle('is-ticked', box.checked);
    refreshUntick();
  });

  untickBtn.addEventListener('click', function () {
    lists.untick(lists.view());
    renderShopping(lists.view());
    var first = aislesEl.querySelector('.shopping-list-tick');
    if (first) first.focus();
  });

  // --- everything at once ----------------------------------------------------

  function render() {
    var view = lists.view();
    renderTabs(view);
    renderBody(view);
    renderShopping(view);
    arrangeBtn.hidden = lists.all().length < 2;
    placePill();
    if (HTF.tagShapes) HTF.tagShapes();
  }

  // --- the scalers ------------------------------------------------------------
  // Only the row's words are rewritten as a number is typed: re-rendering the
  // box under the caret loses it.

  body.addEventListener('input', function (ev) {
    var input = ev.target;
    if (!input.classList.contains('shopping-list-portions')) return;
    var row = input.closest('[data-list]');
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
    lists.setPortions(id, url, n);
    var wordsEl = row.querySelector('.shortlists-words');
    if (wordsEl) wordsEl.innerHTML = shop.rowInner(url, n, recipeHref(url, id));
    if (n !== before) recount(id, url);
    renderShopping(lists.view());
    placePill();
  });

  body.addEventListener('change', function (ev) {
    var input = ev.target;
    if (!input.classList.contains('shopping-list-portions')) return;
    var id = input.closest('[data-list]').getAttribute('data-list');
    var url = input.getAttribute('data-url');
    input.value = String(shop.count(url, lists.portions(id, url)));
  });

  // --- the small actions --------------------------------------------------------

  function focusHeading() {
    var heading = document.getElementById('shortlists-heading');
    if (heading) heading.focus();
  }

  body.addEventListener('click', function (ev) {
    var go = ev.target.closest('[data-go]');
    if (go) { select(go.getAttribute('data-go'), true); return; }

    var step = ev.target.closest('[data-move]');
    if (step) {
      var moving = step.closest('[data-list]');
      var way = step.getAttribute('data-move');
      var at = rowsOf(body).indexOf(moving);
      moveRecipe(moving, at + (way === 'up' ? -1 : 1), way);
      return;
    }

    var removeBtn = ev.target.closest('[data-remove]');
    if (removeBtn) {
      var row = removeBtn.closest('[data-list]');
      var id = row.getAttribute('data-list');
      var url = row.getAttribute('data-url');
      lists.setMember(id, url, false);
      render();
      focusHeading();
      announce('Removed ' + (titles[url] || url) + ' from ' + nameOf(id) + '.');
      return;
    }

    if (ev.target.closest('[data-rename]')) {
      renaming = lists.view();
      render();
      var input = document.getElementById('shortlists-rename-name');
      input.focus();
      input.select();
      return;
    }

    if (ev.target.closest('[data-rename-cancel]')) {
      renaming = null;
      render();
      body.querySelector('[data-rename]').focus();
      return;
    }

    if (ev.target.closest('[data-delete]')) openDelete(lists.view());
  });

  body.addEventListener('submit', function (ev) {
    var form = ev.target.closest('[data-rename-form]');
    if (!form) return;
    ev.preventDefault();
    var input = form.querySelector('input');
    var outcome = lists.rename(renaming, input.value);
    if (outcome.error) {
      form.querySelector('.shortlists-name-problem').textContent =
        problemText(outcome.error, lists.core.cleanName(input.value));
      input.focus();
      return;
    }
    renaming = null;
    render();
    focusHeading();
    announce('Renamed to ' + nameOf(lists.view()) + '.');
  });

  body.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape' && ev.target.closest('[data-rename-form]')) {
      renaming = null;
      render();
      body.querySelector('[data-rename]').focus();
    }
  });

  // --- moving rows ------------------------------------------------------------------
  // After a move the rows are redrawn, so focus goes back to the moved row's
  // arrow, or its other arrow once it reaches an end.

  function rowsOf(container) {
    return Array.prototype.slice.call(container.querySelectorAll('[data-reorder-item]'));
  }

  function focusStep(container, attribute, value, way) {
    var row = rowsOf(container).filter(function (el) { return el.getAttribute(attribute) === value; })[0];
    if (!row || !way) return;
    var btn = row.querySelector('[data-move="' + way + '"]');
    if (btn.disabled) btn = row.querySelector('[data-move="' + (way === 'up' ? 'down' : 'up') + '"]');
    btn.focus();
  }

  function moveRecipe(row, to, way) {
    var id = row.getAttribute('data-list');
    var url = row.getAttribute('data-url');
    var total = rowsOf(body).length;
    lists.moveItem(id, url, to);
    render();
    focusStep(body, 'data-url', url, way);
    announce(V.movedText(titles[url] || url, Math.max(0, Math.min(total - 1, to)), total));
  }

  var arrangeBtn = root.querySelector('[data-shortlists-arrange]');
  var arrangePanel = root.querySelector('[data-shortlists-arrange-panel]');
  var arrangeList = root.querySelector('[data-shortlists-arrange-lists]');
  var tabbar = root.querySelector('.shortlists-tabbar');
  var arranging = false;

  function renderArrange() {
    var all = lists.all();
    arrangeList.innerHTML = all.map(function (list, i) {
      return '<li class="shortlists-arrange-list" data-reorder-item data-id="' + esc(list.id) + '">' +
        handleHtml(list.name, i, all.length) +
        '<span class="shortlists-arrange-name">' + esc(list.name) + '</span>' +
        '<span class="shortlists-section-count">' + V.countText(list.items.length) + '</span></li>';
    }).join('');
  }

  function arrange(on) {
    arranging = on;
    closeNewForm();
    renaming = null;
    tabbar.hidden = on;
    panel.hidden = on;
    arrangePanel.hidden = !on;
    if (on) {
      renderArrange();
      pill.hidden = true;
      document.getElementById('shortlists-arrange-title').focus();
    } else {
      render();
      arrangeBtn.focus();
    }
  }

  function moveList(row, to, way) {
    var id = row.getAttribute('data-id');
    var total = lists.all().length;
    lists.moveList(id, to);
    renderArrange();
    focusStep(arrangeList, 'data-id', id, way);
    announce(V.movedText(nameOf(id), Math.max(0, Math.min(total - 1, to)), total));
  }

  arrangeBtn.addEventListener('click', function () { arrange(true); });
  root.querySelector('[data-shortlists-arrange-done]').addEventListener('click', function () { arrange(false); });

  arrangeList.addEventListener('click', function (ev) {
    var step = ev.target.closest('[data-move]');
    if (!step) return;
    var row = step.closest('[data-id]');
    var way = step.getAttribute('data-move');
    moveList(row, rowsOf(arrangeList).indexOf(row) + (way === 'up' ? -1 : 1), way);
  });

  if (HTF.dragReorder) {
    var dragOptions = { item: '[data-reorder-item]', grip: '[data-reorder-grip]' };
    HTF.dragReorder.attach(body, Object.assign({
      onDrop: function (row, from, to) { moveRecipe(row, to); }
    }, dragOptions));
    HTF.dragReorder.attach(arrangeList, Object.assign({
      onDrop: function (row, from, to) { moveList(row, to); }
    }, dragOptions));
  }

  // --- a new list -----------------------------------------------------------------

  function closeNewForm() {
    newForm.hidden = true;
    newBtn.setAttribute('aria-expanded', 'false');
    newProblem.textContent = '';
  }

  newBtn.addEventListener('click', function () {
    if (!newForm.hidden) { closeNewForm(); return; }
    renaming = null;
    renderBody(lists.view());
    newForm.hidden = false;
    newBtn.setAttribute('aria-expanded', 'true');
    newInput.value = '';
    newInput.focus();
  });

  newForm.addEventListener('submit', function (ev) {
    ev.preventDefault();
    var made = lists.create(newInput.value);
    if (made.error) {
      newProblem.textContent = problemText(made.error, lists.core.cleanName(newInput.value));
      newInput.focus();
      return;
    }
    newInput.value = '';
    select(made.id, true);
    announce('Made ' + nameOf(made.id) + '.');
  });

  newForm.querySelector('[data-shortlists-cancel]').addEventListener('click', function () {
    closeNewForm();
    newBtn.focus();
  });

  newForm.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape') { closeNewForm(); newBtn.focus(); }
  });

  // --- delete -----------------------------------------------------------------------

  function remove(id) {
    var name = nameOf(id);
    lists.remove(id);
    render();
    selectedTab().focus();
    announce('Deleted ' + name + '.');
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
    if (shoppingEl.hidden || arranging) { pill.hidden = true; return; }
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
    if (arranging) renderArrange();
  });

  render();
  root.hidden = false;
  placePill();
})();
