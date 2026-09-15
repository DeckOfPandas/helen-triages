// =============================================================================
// PAGE SEARCH — the "search for anything" box on a recipe or drink page's
// furniture line, and its dropdown. GitHub issue #1050.
// =============================================================================
// _includes/back-to-index.html renders the box as a plain GET form to this
// site's index carrying `q=`, which is the name search the index already has
// (#1024) and works with no JavaScript at all. This file upgrades it: as you
// type, a dropdown under the box offers everything the word could mean on THIS
// site -- a recipe or drink by name, a star ingredient, a mood, a practicality,
// a hassle, an ingredient -- grouped by kind, and choosing one takes you either
// to that page or to the index already filtered by that word. Helen's brief:
//
//   "I would like to be able to search for ANYTHING -- name, ingredients
//    (included), star/mood/practicalities/hassle/whatever. Search results
//    should be shown as a dropdown below the input field, grouped by type.
//    Prefix-matched title string results first, then tags."
//
// PER SITE, NEVER ACROSS SITES. A recipe page searches food and a drink page
// searches cocktails; the index it hands a filter to is the one the back arrow
// beside it points at. Helen: "to search per site, not across sites".
//
// WHAT IT SEARCHES IS A JSON FILE THE BUILD WRITES -- food/search.json and
// cocktails/search.json, one per site, fetched the first time the box takes
// focus and never before. A recipe page carries nothing about the other four
// hundred recipes, and inlining the collection into every page would put ~30KB
// of other pages' data on each one; a file fetched once, when it is wanted, is
// the cheaper shape. The JSON is generated from the same gated collections the
// index reads (`site.food_recipes` after _plugins/publish_gate.rb has run), so
// the dropdown can only ever offer a page that is live -- the same argument
// the "if you liked this" rows make. Its shape is documented in the two JSON
// pages themselves; the module below reads it and assumes nothing about which
// site it came from.
//
// THE RANKING IS THE SITES' OWN, not a new one. Titles are tiered exactly as
// I KNOW WHAT I WANT tiers them (recipe-list.js's titleMatchTier: the title
// starts with the query, then some word does, then it is merely a substring),
// and a vocabulary word is banded exactly as the ingredient pickers band theirs
// (ingredient-search.js: prefix of the first word, prefix of any word,
// substring). What Helen ruled here is the ORDER OF THE GROUPS -- names first,
// then the tags -- and that a substring hit on a name is not a "prefix-matched
// title", so it is offered only when no prefix match exists at all.
//
// THE DECISION IS PURE, AND THE DOM WIRING IS THE REST OF THE FILE (MANUAL §3).
// `create(data)` returns a searcher a Node test can ask a question of without
// a browser; everything under "DOM wiring" is the box, the dropdown and the
// keyboard. Same split as back-link.js, filter-state.js and cocktail-search.js,
// and the same export shape so there is one convention rather than four.
// =============================================================================

(function (root) {
  'use strict';

  // Fewer characters than this and the dropdown stays shut: one letter matches
  // most of the collection and offers nothing. Two is where a word starts to
  // mean something ("ch" is already chicken, chocolate, chai, and not much
  // else). The plain form still submits at any length.
  var MIN_QUERY_CHARS = 2;

  // How many of each kind the dropdown shows before saying "+N more -- keep
  // typing". THE CAP IS STATED, NOT SILENT, which is the rule the drinks
  // index's pool already follows: a list that quietly stops at six looks like
  // a complete answer, and the one you wanted may be the seventh.
  var ITEM_CAP = 6;
  var WORD_CAP = 5;

  // The same fold ingredient-search.js uses (accents stripped, a hyphen read
  // as a space), written here rather than borrowed because a recipe page does
  // not load that module and a search box is not a reason to start. A test
  // holds the two equal, so they cannot drift apart unnoticed.
  function fold(str) {
    return String(str == null ? '' : str)
      .normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/-/g, ' ');
  }

  /* Fold ONE CODE UNIT AT A TIME, so an index into the folded string is an
     index into the original. The highlight needs that: the match is found in
     the folded text and painted onto the real one, accents intact (the rule
     filters.js and cocktail-search.js both follow -- fold to compare, never to
     display). A character that folds to nothing at all (a stray combining
     mark) keeps its place as itself, so the two strings stay the same length
     whatever the input. */
  function foldByCharacter(str) {
    var s = String(str == null ? '' : str);
    var out = '';
    for (var i = 0; i < s.length; i++) {
      var f = fold(s.charAt(i)).toLowerCase();
      out += f.length ? f.charAt(0) : s.charAt(i);
    }
    return out;
  }

  function words(folded) {
    return folded.split(/\s+/).filter(Boolean);
  }

  /* Which tier a display string falls into for an already-folded, lowercased
     query: 1 it starts with it, 2 some word does, 3 it is a substring, 0 no
     match. recipe-list.js's titleMatchTier, spelled for a string that has
     already been folded per character. */
  function tierOf(folded, query) {
    var ws = words(folded);
    if (ws.length && ws[0].indexOf(query) === 0) return 1;
    if (ws.some(function (w) { return w.indexOf(query) === 0; })) return 2;
    if (folded.indexOf(query) !== -1) return 3;
    return 0;
  }

  /* Where the query sits in the display string, for the highlight: the run
     that BEGINS A WORD when there is one, otherwise the first occurrence. So
     "li" on "apricot liqueur" marks the "li" of liqueur, not the one buried in
     "apricot" -- the marked run is the one that earned the match. */
  function hitOf(folded, query) {
    var at = -1;
    var ws = folded.split(/(\s+)/);
    var pos = 0;
    for (var i = 0; i < ws.length && at === -1; i++) {
      if (i % 2 === 0 && ws[i].indexOf(query) === 0) at = pos;
      pos += ws[i].length;
    }
    if (at === -1) at = folded.indexOf(query);
    return at === -1 ? null : [at, at + query.length];
  }

  function encode(value) {
    return encodeURIComponent(String(value));
  }

  /**
   * Build a searcher over one site's search.json.
   *
   * @param {object} data                the parsed JSON
   * @param {string} data.home           this site's index, already relative_url'd
   * @param {string} data.items_label    what the first group is called
   * @param {Array}  data.groups         the vocabulary groups, in the index's
   *                                     order: {kind, label, param, field,
   *                                     values?}
   * @param {Array}  data.items          {t, u, ...fields}
   */
  function create(data) {
    var d = data || {};
    var home = String(d.home || '');
    var items = (d.items || []).map(function (it) {
      return { item: it, title: String(it.t || ''), folded: foldByCharacter(it.t || '') };
    });

    /* EVERY GROUP'S VOCABULARY, COUNTED. A declared list (`values`) keeps the
       index's own order -- taxonomy order for food, Helen's typed order for
       the drinks' moods (#966/#967) -- and a group with no declared list is
       built from what the items actually carry, alphabetically. Either way a
       word with NO item is dropped: the index renders no button for an empty
       mood (`pudding in a glass`, taxonomy.yml), and a search result that
       leads to an empty index would be a promise the page cannot keep. */
    var groups = (d.groups || []).map(function (g) {
      var counts = Object.create(null);
      var display = Object.create(null);
      items.forEach(function (entry) {
        var raw = entry.item[g.field];
        var list = Array.isArray(raw) ? raw : (raw == null || raw === '' ? [] : [raw]);
        list.forEach(function (v) {
          var key = foldByCharacter(v);
          if (!key.trim()) return;
          counts[key] = (counts[key] || 0) + 1;
          if (!display[key]) display[key] = String(v);
        });
      });
      var order;
      if (Array.isArray(g.values)) {
        order = g.values.map(function (v) { return foldByCharacter(v); });
        g.values.forEach(function (v) {
          var key = foldByCharacter(v);
          if (!display[key]) display[key] = String(v);
        });
      } else {
        order = Object.keys(counts).sort();
      }
      var seen = Object.create(null);
      var vocab = [];
      order.forEach(function (key) {
        if (seen[key] || !counts[key]) return;
        seen[key] = true;
        vocab.push({ key: key, label: display[key], count: counts[key] });
      });
      return {
        kind: String(g.kind || ''),
        label: String(g.label || ''),
        param: String(g.param || ''),
        vocab: vocab
      };
    });

    function hrefForWord(group, label) {
      return home + '?' + encode(group.param) + '=' + encode(label);
    }

    /* The whole dropdown for one query: a list of groups, each with the
       results it shows and how many it is holding back. An empty query, or one
       under the minimum, is `null` -- "say nothing", which the wiring reads as
       "close". A query that matches nothing anywhere is a result with no
       groups, which is a different fact and is shown as one. */
    function search(rawQuery) {
      var typed = String(rawQuery == null ? '' : rawQuery).trim();
      if (typed.length < MIN_QUERY_CHARS) return null;
      var query = foldByCharacter(typed).replace(/\s+/g, ' ');
      if (!query) return null;

      var out = [];

      // --- the names, first ---------------------------------------------------
      var byTier = [[], [], [], []];
      items.forEach(function (entry) {
        var tier = tierOf(entry.folded, query);
        if (tier) byTier[tier].push(entry);
      });
      /* PREFIX FIRST, and a substring only when nothing prefixes. Helen's
         "prefix-matched title string results first": a title whose word
         starts with what you typed is what you meant; a title that happens
         to contain it mid-word ("roni" in Negroni) is a fallback for when
         there is nothing else, not a second helping under the same heading. */
      var named = byTier[1].concat(byTier[2]);
      if (!named.length) named = byTier[3];
      if (named.length) {
        out.push({
          kind: 'name',
          label: String(d.items_label || ''),
          results: named.slice(0, ITEM_CAP).map(function (entry) {
            return {
              label: entry.title,
              href: String(entry.item.u || ''),
              hit: hitOf(entry.folded, query)
            };
          }),
          hidden: Math.max(0, named.length - ITEM_CAP)
        });
      }

      // --- then the words, one group per kind, in the index's order -----------
      groups.forEach(function (g) {
        var bands = [[], [], [], []];
        g.vocab.forEach(function (v) {
          var tier = tierOf(v.key, query);
          if (tier) bands[tier].push(v);
        });
        var matched = bands[1].concat(bands[2], bands[3]);
        if (!matched.length) return;
        out.push({
          kind: g.kind,
          label: g.label,
          results: matched.slice(0, WORD_CAP).map(function (v) {
            return {
              label: v.label,
              href: hrefForWord(g, v.label),
              hit: hitOf(v.key, query),
              count: v.count
            };
          }),
          hidden: Math.max(0, matched.length - WORD_CAP)
        });
      });

      return { query: typed, groups: out };
    }

    return { search: search, groups: groups, itemCount: items.length };
  }

  // --- Exported the same way every other split module here is ------------------
  var api = {
    MIN_QUERY_CHARS: MIN_QUERY_CHARS,
    ITEM_CAP: ITEM_CAP,
    WORD_CAP: WORD_CAP,
    fold: fold,
    foldByCharacter: foldByCharacter,
    tierOf: tierOf,
    hitOf: hitOf,
    create: create
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
    return;
  }
  root.HTF = root.HTF || {};
  root.HTF.pageSearch = api;

  // --- DOM wiring --------------------------------------------------------------
  //
  // One box per page. The form is `.page-search`; it names the JSON to fetch in
  // `data-search-index`, and the dropdown is the `.page-search-results` element
  // the include already renders (empty and hidden, so the no-script page is
  // exactly the page minus this file).

  if (typeof document === 'undefined') return;

  var form = document.querySelector('.page-search');
  if (!form) return;
  var input = form.querySelector('.page-search-input');
  var panel = form.querySelector('.page-search-results');
  var indexUrl = form.getAttribute('data-search-index');
  if (!input || !panel || !indexUrl || !root.HTF.fetchJson) return;

  var searcher = null;
  var loading = false;
  var waiting = [];
  var flat = [];          // every option on screen, top to bottom, for the keys
  var active = -1;        // which of `flat` the keyboard is on

  /* FETCHED ON FOCUS, ONCE, THROUGH THE SHARED HELPER (assets.js's fetchJson,
     which caches and warns -- the same door every SVG on the site comes
     through). A reader who never touches the box costs the page nothing; the
     first focus starts the fetch and the first keystroke usually finds it
     finished. A failed fetch leaves `searcher` null and the box stays a plain
     form -- the no-script behaviour, which is correct rather than broken. */
  function load(then) {
    if (searcher) { then(); return; }
    waiting.push(then);
    if (loading) return;
    loading = true;
    root.HTF.fetchJson(indexUrl, function (json) {
      if (json) searcher = create(json);
      loading = false;
      var fns = waiting;
      waiting = [];
      fns.forEach(function (fn) { fn(); });
    });
  }

  function el(tag, cls) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    return node;
  }

  /* The label with its matched run wrapped, built from nodes rather than from
     an HTML string, so a title can carry any character it likes. */
  function labelNode(result) {
    var frag = document.createDocumentFragment();
    var text = result.label;
    if (!result.hit) {
      frag.appendChild(document.createTextNode(text));
      return frag;
    }
    var start = result.hit[0], end = result.hit[1];
    if (start > 0) frag.appendChild(document.createTextNode(text.slice(0, start)));
    var hit = el('span', 'page-search-hit');
    hit.textContent = text.slice(start, end);
    frag.appendChild(hit);
    if (end < text.length) frag.appendChild(document.createTextNode(text.slice(end)));
    return frag;
  }

  function close() {
    panel.hidden = true;
    panel.textContent = '';
    flat = [];
    active = -1;
    input.setAttribute('aria-expanded', 'false');
    input.removeAttribute('aria-activedescendant');
  }

  function paint(found) {
    panel.textContent = '';
    flat = [];
    active = -1;

    if (!found) { close(); return; }

    if (!found.groups.length) {
      // PLACEHOLDER COPY, Helen's to write (MANUAL 13.12).
      var none = el('p', 'page-search-none');
      none.textContent = 'nothing called that here';
      panel.appendChild(none);
    }

    found.groups.forEach(function (group) {
      var section = el('div', 'page-search-group page-search-group--' + group.kind);
      section.setAttribute('role', 'group');
      var heading = el('div', 'page-search-group-label');
      heading.textContent = group.label;
      section.appendChild(heading);

      group.results.forEach(function (result) {
        /* A REAL LINK, for the reason every badge and chip on this site is
           one: middle-click, open in new tab, copy link address and "where
           does this go" on hover all work, where a button plus location.href
           breaks every one of them. */
        var a = el('a', 'page-search-option');
        a.href = result.href;
        a.setAttribute('role', 'option');
        a.id = 'page-search-option-' + flat.length;
        a.appendChild(labelNode(result));
        section.appendChild(a);
        flat.push(a);
      });

      if (group.hidden > 0) {
        var more = el('p', 'page-search-more');
        more.textContent = '+' + group.hidden + ' more — keep typing';
        section.appendChild(more);
      }
      panel.appendChild(section);
    });

    panel.hidden = false;
    input.setAttribute('aria-expanded', 'true');
  }

  function setActive(n) {
    if (active >= 0 && flat[active]) flat[active].classList.remove('is-active');
    active = n;
    if (active >= 0 && flat[active]) {
      flat[active].classList.add('is-active');
      input.setAttribute('aria-activedescendant', flat[active].id);
    } else {
      input.removeAttribute('aria-activedescendant');
    }
  }

  function refresh() {
    if (!searcher) return;
    paint(searcher.search(input.value));
  }

  function whenLoaded() {
    if (document.activeElement === input) refresh();
  }

  input.addEventListener('focus', function () { load(whenLoaded); });
  input.addEventListener('input', function () { load(whenLoaded); });

  input.addEventListener('keydown', function (event) {
    if (panel.hidden || !flat.length) {
      if (event.key === 'Escape') close();
      return;                    // Enter with nothing offered submits the form
    }
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setActive((active + 1) % flat.length);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      setActive((active - 1 + flat.length) % flat.length);
    } else if (event.key === 'Escape') {
      event.preventDefault();
      close();
    } else if (event.key === 'Enter' && active >= 0) {
      /* A chosen result goes where its link goes; Enter with nothing chosen
         falls through to the form, which is the name search on the index --
         Helen's "submitting the search should be pressing Enter or clicking
         the magnifying glass". */
      event.preventDefault();
      window.location.href = flat[active].href;
    }
  });

  // Closing on blur has to wait a beat, or a click on an option blurs the box
  // and empties the panel before the click can land on the link.
  input.addEventListener('blur', function () {
    setTimeout(function () {
      if (!form.contains(document.activeElement)) close();
    }, 120);
  });

  document.addEventListener('click', function (event) {
    if (!form.contains(event.target)) close();
  });

})(typeof window !== 'undefined' ? window : this);
