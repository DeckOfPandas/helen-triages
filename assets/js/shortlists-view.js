// shortlists-view.js: what the shortlists page shows for the lists it is
// given (#1521), as HTF.listsView. No DOM and no storage: loaded as a
// <script>, and by require() in the tests. Site-agnostic. MANUAL §8.9.

(function (root, factory) {
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = factory();
  } else {
    root.HTF = root.HTF || {};
    root.HTF.listsView = factory();
  }
})(typeof window !== 'undefined' ? window : this, function () {
  'use strict';

  var EVERYTHING = 'everything';

  function find(lists, id) {
    for (var i = 0; i < lists.length; i += 1) {
      if (lists[i].id === id) return lists[i];
    }
    return null;
  }

  // One row per recipe per list: a recipe on two lists is cooked twice.
  function rows(lists, scope) {
    var chosen = scope === EVERYTHING ? lists : [find(lists, scope)].filter(Boolean);
    var out = [];
    chosen.forEach(function (list) {
      list.items.forEach(function (item) {
        out.push({ list: list.id, recipe: item.recipe, portions: item.portions });
      });
    });
    return out;
  }

  function tabs(lists, view) {
    var current = find(lists, view) ? view : EVERYTHING;
    return [{
      id: EVERYTHING, name: EVERYTHING,
      count: rows(lists, EVERYTHING).length, selected: current === EVERYTHING
    }].concat(lists.map(function (list) {
      return { id: list.id, name: list.name, count: list.items.length, selected: current === list.id };
    }));
  }

  function tabLabel(tab) {
    return tab.name + ' · ' + tab.count;
  }

  function countText(n) {
    return n + (n === 1 ? ' recipe' : ' recipes');
  }

  /* The shopping entries for some rows, through a site's shopping-rows
     instance (`has`, `count`, `scale`, `entries`). */
  function shoppingEntries(someRows, shop) {
    var out = [];
    someRows.forEach(function (row) {
      if (!shop.has(row.recipe)) return;
      var n = shop.count(row.recipe, row.portions);
      out = out.concat(shop.entries(row.recipe, shop.scale(row.recipe, n)));
    });
    return out;
  }

  /* A recipe button's word: how many lists it is on, or, filling one list
     (`into`: { name, on }), that list's name. The mark is the stylesheet's. */
  function buttonWords(count, into) {
    if (into) return { word: into.name, on: !!into.on };
    if (!count) return { word: 'shortlist', on: false };
    return { word: count + (count === 1 ? ' list' : ' lists'), on: true };
  }

  // The line under a refused name: `problem` is the store's 'empty' or 'clash'.
  function nameProblemText(problem, name, lists) {
    if (problem === 'empty') return 'Give the list a name.';
    var folded = String(name).toLowerCase();
    var clash = lists.filter(function (l) { return l.name.toLowerCase() === folded; })[0];
    return 'You already have a list called “' + (clash ? clash.name : name) + '”.';
  }

  function linkText(lists) {
    if (!lists) return 'shortlists';
    return 'your ' + lists + (lists === 1 ? ' shortlist' : ' shortlists');
  }

  /* A list keeps portions, batches for a `makes:` recipe; the recipe page's
     scaler counts portions, or the things made (`scale`: { made, base }). */
  function scalerFromPortions(portions, scale) {
    return scale.made ? portions * scale.base : portions;
  }

  function portionsFromScaler(n, scale) {
    return scale.made ? n / scale.base : n;
  }

  function inListsText(count) {
    if (!count) return '';
    return 'in ' + count + (count === 1 ? ' list' : ' lists');
  }

  // Recipes a shared link names that this site does not have.
  function missingText(n) {
    if (!n) return '';
    return n === 1 ? '1 recipe in the link is not on this site, so it is left out.'
      : n + ' recipes in the link are not on this site, so they are left out.';
  }

  // The preview's choice for a list whose name is taken: `free` is the name
  // keeping both would give it.
  function clashChoices(name, free) {
    return {
      question: 'You already have a list called “' + name + '”.',
      both: 'keep both, this one as “' + free + '”',
      merge: 'add its recipes to yours (your portions stay)',
      skip: 'leave it out'
    };
  }

  function broughtText(count, kept) {
    if (!count) return 'Nothing brought in.';
    var what = count === 1 ? 'one list' : count + ' lists';
    return (kept ? 'Kept ' : 'Brought in ') + what + '.';
  }

  // What the live region says after a move; `to` counts from 0.
  function movedText(name, to, total) {
    return name + ' moved to ' + (to + 1) + ' of ' + total + '.';
  }

  // A row's ↑ and ↓, named for what they move: "move Christmas starters up".
  function moveLabel(name, way) {
    return 'move ' + name + ' ' + way;
  }

  function withQuery(url, key, value) {
    return url + (url.indexOf('?') === -1 ? '?' : '&') + key + '=' + encodeURIComponent(value);
  }

  return {
    EVERYTHING: EVERYTHING,
    rows: rows,
    tabs: tabs,
    tabLabel: tabLabel,
    countText: countText,
    shoppingEntries: shoppingEntries,
    buttonWords: buttonWords,
    linkText: linkText,
    nameProblemText: nameProblemText,
    scalerFromPortions: scalerFromPortions,
    portionsFromScaler: portionsFromScaler,
    inListsText: inListsText,
    movedText: movedText,
    missingText: missingText,
    clashChoices: clashChoices,
    broughtText: broughtText,
    moveLabel: moveLabel,
    intoUrl: function (indexUrl, id) { return withQuery(indexUrl, 'into', id); },
    listUrl: function (recipeUrl, id) { return withQuery(recipeUrl, 'list', id); }
  };
});
