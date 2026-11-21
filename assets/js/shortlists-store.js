// shortlists-store.js: named shortlists (#1521), as HTF.lists. MANUAL §8.9.
// `core` is pure: every function takes a state and returns a new one, so the
// tests need no browser. The rest reads and writes the site's one key.
// localStorage only, one browser, no account (DECISIONS §8.3). Keys are only
// ever removed by name: every deckofpandas.github.io site shares the origin.

(function () {
  'use strict';

  var HTF = window.HTF;
  if (!HTF || !HTF.site) return;

  var EVERYTHING = 'everything';
  var NAME_MAX = 40;
  var MAX_PORTIONS = 99;

  // --- core ------------------------------------------------------------------

  function empty() {
    return { lists: [], next: 1, view: EVERYTHING, ticked: [] };
  }

  function copy(state) {
    return {
      lists: state.lists.map(function (list) {
        return {
          id: list.id, name: list.name,
          items: list.items.map(function (item) { return { recipe: item.recipe, portions: item.portions }; }),
          ticked: list.ticked.slice()
        };
      }),
      next: state.next, view: state.view, ticked: state.ticked.slice()
    };
  }

  function cleanName(name) {
    return String(name == null ? '' : name).replace(/\s+/g, ' ').trim().slice(0, NAME_MAX);
  }

  function find(state, id) {
    for (var i = 0; i < state.lists.length; i += 1) {
      if (state.lists[i].id === id) return state.lists[i];
    }
    return null;
  }

  // 'empty', 'clash' or '' for a name that may be used (exceptId: a rename).
  function nameProblem(state, name, exceptId) {
    if (!name) return 'empty';
    var folded = name.toLowerCase();
    var clash = state.lists.some(function (list) {
      return list.id !== exceptId && list.name.toLowerCase() === folded;
    });
    return clash ? 'clash' : '';
  }

  function create(state, rawName) {
    var name = cleanName(rawName);
    var problem = nameProblem(state, name);
    if (problem) return { state: state, error: problem };
    var next = copy(state);
    var id = 'l' + next.next;
    next.next += 1;
    next.lists.push({ id: id, name: name, items: [], ticked: [] });
    return { state: next, id: id };
  }

  function rename(state, id, rawName) {
    var name = cleanName(rawName);
    var problem = nameProblem(state, name, id);
    if (problem) return { state: state, error: problem };
    var next = copy(state);
    var list = find(next, id);
    if (list) list.name = name;
    return { state: next };
  }

  function remove(state, id) {
    var next = copy(state);
    next.lists = next.lists.filter(function (list) { return list.id !== id; });
    if (next.view === id) next.view = EVERYTHING;
    return next;
  }

  function clampPortions(value) {
    var n = Number(value);
    if (!isFinite(n)) return 1;
    n = Math.ceil(n * 2) / 2;
    return Math.min(MAX_PORTIONS, Math.max(0.5, n));
  }

  function setMember(state, id, recipe, on, defaultPortions) {
    var next = copy(state);
    var list = find(next, id);
    if (!list || !recipe) return next;
    var at = indexOfRecipe(list, recipe);
    if (on && at === -1) list.items.push({ recipe: recipe, portions: clampPortions(defaultPortions) });
    if (!on && at !== -1) list.items.splice(at, 1);
    return next;
  }

  function indexOfRecipe(list, recipe) {
    for (var i = 0; i < list.items.length; i += 1) {
      if (list.items[i].recipe === recipe) return i;
    }
    return -1;
  }

  function setPortions(state, id, recipe, value) {
    var next = copy(state);
    var list = find(next, id);
    var at = list ? indexOfRecipe(list, recipe) : -1;
    if (at !== -1) list.items[at].portions = clampPortions(value);
    return next;
  }

  function portions(state, id, recipe) {
    var list = find(state, id);
    var at = list ? indexOfRecipe(list, recipe) : -1;
    return at === -1 ? null : list.items[at].portions;
  }

  function listsWith(state, recipe) {
    return state.lists.filter(function (list) { return indexOfRecipe(list, recipe) !== -1; })
      .map(function (list) { return list.id; });
  }

  function moveInArray(array, from, to) {
    var target = Math.max(0, Math.min(array.length - 1, to));
    var moved = array.splice(from, 1)[0];
    array.splice(target, 0, moved);
  }

  function moveList(state, id, to) {
    var next = copy(state);
    var from = next.lists.indexOf(find(next, id));
    if (from !== -1) moveInArray(next.lists, from, to);
    return next;
  }

  function moveItem(state, id, recipe, to) {
    var next = copy(state);
    var list = find(next, id);
    var from = list ? indexOfRecipe(list, recipe) : -1;
    if (from !== -1) moveInArray(list.items, from, to);
    return next;
  }

  function setView(state, view) {
    var next = copy(state);
    next.view = find(next, view) ? view : EVERYTHING;
    return next;
  }

  // Shopping ticks: a list's own, or EVERYTHING's for the merged list.
  function tickedArray(state, scope) {
    if (scope === EVERYTHING) return state.ticked;
    var list = find(state, scope);
    return list ? list.ticked : null;
  }

  function setTicked(state, scope, rowKey, on) {
    var next = copy(state);
    var ticks = tickedArray(next, scope);
    if (!ticks || !rowKey) return next;
    var at = ticks.indexOf(rowKey);
    if (on && at === -1) ticks.push(rowKey);
    if (!on && at !== -1) ticks.splice(at, 1);
    return next;
  }

  function ticked(state, scope) {
    return (tickedArray(state, scope) || []).slice();
  }

  // The named rows, or with no names every row, in one scope.
  function untick(state, scope, rowKeys) {
    var next = copy(state);
    var ticks = tickedArray(next, scope);
    if (!ticks) return next;
    var keep = rowKeys ? ticks.filter(function (key) { return rowKeys.indexOf(key) === -1; }) : [];
    ticks.length = 0;
    keep.forEach(function (key) { ticks.push(key); });
    return next;
  }

  // --- bringing lists in ---------------------------------------------------------

  // `name`, or "name (2)", "name (3)"... clashing with no list; the name is
  // cut to make room for the number, never the number dropped. A link with
  // no name brings in "Shared list".
  var UNNAMED = 'Shared list';
  function freeName(state, rawName) {
    var name = cleanName(rawName) || UNNAMED;
    if (!nameProblem(state, name)) return name;
    for (var n = 2; ; n += 1) {
      var tail = ' (' + n + ')';
      var tried = cleanName(name.slice(0, NAME_MAX - tail.length)) + tail;
      if (!nameProblem(state, tried)) return tried;
    }
  }

  /* Imported or kept lists, in one write. Each plan is { action, name, into,
     items: [{ recipe, portions }] }: 'new' adds a list at the end under a
     free name; 'merge' adds to list `into` the recipes it lacks, its own
     portions winning; 'skip' does nothing. */
  function bringIn(state, plans) {
    var next = copy(state);
    var ids = [];
    plans.forEach(function (plan) {
      var list = null;
      if (plan.action === 'new') {
        list = { id: 'l' + next.next, name: freeName(next, plan.name), items: [], ticked: [] };
        next.next += 1;
        next.lists.push(list);
      } else if (plan.action === 'merge') {
        list = find(next, plan.into);
      }
      if (!list) return;
      ids.push(list.id);
      (plan.items || []).forEach(function (item) {
        if (item && item.recipe && indexOfRecipe(list, item.recipe) === -1) {
          list.items.push({ recipe: item.recipe, portions: clampPortions(item.portions) });
        }
      });
    });
    return { state: next, ids: ids };
  }

  // --- a stored record is untrusted input -------------------------------------
  // Each list is read on its own, so one bad list costs only itself.

  function fromRecord(raw) {
    var state = empty();
    if (!raw || typeof raw !== 'object' || !Array.isArray(raw.lists)) return state;
    var biggest = 0;
    raw.lists.forEach(function (rawList) {
      if (!rawList || typeof rawList !== 'object') return;
      var id = typeof rawList.id === 'string' && /^l\d+$/.test(rawList.id) ? rawList.id : '';
      var name = cleanName(rawList.name);
      if (!id || find(state, id) || nameProblem(state, name)) return;
      var list = { id: id, name: name, items: [], ticked: [] };
      (Array.isArray(rawList.items) ? rawList.items : []).forEach(function (item) {
        if (item && typeof item.recipe === 'string' && item.recipe &&
            indexOfRecipe(list, item.recipe) === -1) {
          list.items.push({ recipe: item.recipe, portions: clampPortions(item.portions) });
        }
      });
      list.ticked = strings(rawList.ticked);
      state.lists.push(list);
      biggest = Math.max(biggest, Number(id.slice(1)));
    });
    state.next = Math.max(biggest + 1, Number(raw.next) || 0);
    state.ticked = strings(raw.ticked);
    state.view = find(state, raw.view) ? raw.view : EVERYTHING;
    return state;
  }

  function strings(raw) {
    var out = [];
    (Array.isArray(raw) ? raw : []).forEach(function (v) {
      if (typeof v === 'string' && v && out.indexOf(v) === -1) out.push(v);
    });
    return out;
  }

  var core = {
    EVERYTHING: EVERYTHING, NAME_MAX: NAME_MAX,
    empty: empty, fromRecord: fromRecord, cleanName: cleanName,
    create: create, rename: rename, remove: remove,
    setMember: setMember, setPortions: setPortions, portions: portions, listsWith: listsWith,
    moveList: moveList, moveItem: moveItem, setView: setView,
    setTicked: setTicked, ticked: ticked, untick: untick,
    freeName: freeName, bringIn: bringIn
  };

  // --- storage: the one place the key is named ----------------------------------

  var KEY = 'htf-lists-' + HTF.site + '-v1';

  // Removed by name on load (#1521): the keys this store replaced. Food only:
  // cocktails' single list is live until its own move.
  var OLD_KEYS = {
    food: [
      'htf-shortlist-food-v1', 'htf-shortlist-glasses-food-v1',
      'htf-shortlist-portions-food-v1', 'htf-shortlist-portions-food-v2',
      'htf-shortlist-batches-food-v1', 'htf-shortlist-ticked-food-v1',
      'htf-shortlists-food-v1'
    ]
  };

  var state = null;

  function load() {
    if (state) return state;
    var raw = null;
    try {
      (OLD_KEYS[HTF.site] || []).forEach(function (key) { localStorage.removeItem(key); });
      raw = JSON.parse(localStorage.getItem(KEY));
    } catch (e) { /* no lists, and the page works */ }
    state = fromRecord(raw);
    return state;
  }

  function save(next) {
    state = next;
    try {
      localStorage.setItem(KEY, JSON.stringify(state));
    } catch (e) { /* this visit still has it; tomorrow will not */ }
    return state;
  }

  function result(outcome) {
    if (!outcome.error) save(outcome.state);
    return { id: outcome.id, error: outcome.error };
  }

  HTF.lists = {
    core: core,
    KEY: KEY,
    EVERYTHING: EVERYTHING,
    NAME_MAX: NAME_MAX,
    UNNAMED: UNNAMED,
    // Forget what was read, so the next call reads the key again.
    refresh: function () { state = null; },
    all: function () { return copy(load()).lists; },
    get: function (id) { return find(copy(load()), id); },
    view: function () { return load().view; },
    nameProblem: function (name, exceptId) { return nameProblem(load(), cleanName(name), exceptId); },
    create: function (name) { return result(create(load(), name)); },
    rename: function (id, name) { return result(rename(load(), id, name)); },
    remove: function (id) { save(remove(load(), id)); },
    setMember: function (id, recipe, on, defaultPortions) { save(setMember(load(), id, recipe, on, defaultPortions)); },
    setPortions: function (id, recipe, value) { save(setPortions(load(), id, recipe, value)); },
    portions: function (id, recipe) { return portions(load(), id, recipe); },
    listsWith: function (recipe) { return listsWith(load(), recipe); },
    moveList: function (id, to) { save(moveList(load(), id, to)); },
    moveItem: function (id, recipe, to) { save(moveItem(load(), id, recipe, to)); },
    setView: function (view) { save(setView(load(), view)); },
    setTicked: function (scope, rowKey, on) { save(setTicked(load(), scope, rowKey, on)); },
    ticked: function (scope) { return ticked(load(), scope); },
    untick: function (scope, rowKeys) { save(untick(load(), scope, rowKeys)); },
    freeName: function (name) { return freeName(load(), name); },
    // The ids written to, in the plans' order.
    bringIn: function (plans) {
      var outcome = bringIn(load(), plans);
      save(outcome.state);
      return outcome.ids;
    }
  };
})();
