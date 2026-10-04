// =============================================================================
// PAGE SEARCH — the "search for anything" box in the header of every page of
// a site on a LOCAL BUILD, and its dropdown. GitHub issue #1050; in the header
// and local-only since #1210 (2026-09-30), when it was a recipe or drink
// page's furniture line and live.
// =============================================================================
// _includes/page-search.html renders the box as a plain GET form to this
// site's index carrying `q=`, which is the name search the index already has
// (#1024) and works with no JavaScript at all, and loads this file beside it
// under the same `show_header_search` gate. This file upgrades it: as you
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
// THE RANKING STARTED AS THE SITES' OWN (list-view.js's titleMatchTier,
// ingredient-search.js's banding) AND #1052 THEN NARROWED IT. Helen: "omnisearch
// should prefix match only, and whole words only." A result matches only when
// every word typed is a PREFIX of a whole word in the candidate, at a word
// boundary -- never mid-word. There is no substring fallback any more: "roni"
// no longer finds Negroni, because "roni" prefixes no word in it. Tier 1 is the
// candidate starting with the query outright (which is also, trivially, its
// first word being prefixed); tier 2 is every other case where each query word
// prefixes some word in the candidate. What Helen ruled beyond that here is the
// ORDER OF THE GROUPS -- names first, then the tags.
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
  // not load that module with the page and the names have to be searchable
  // without it (since #1289 it arrives on first focus, for food's ingredient
  // words only -- withPicker below). A test holds the two equal, so they
  // cannot drift apart unnoticed.
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
     query: 1 the candidate starts with the query outright, 2 every word the
     query is made of prefixes some whole word in the candidate (word boundary
     only -- never mid-word), 0 no match. #1052: there is no substring tier any
     more. A multi-word query ("duck a") matches word for word, in any order,
     against the candidate's words -- it need not read as a run. */
  function tierOf(folded, query) {
    if (folded.indexOf(query) === 0) return 1;
    var qWords = words(query);
    var cWords = words(folded);
    if (qWords.length && qWords.every(function (qw) {
      return cWords.some(function (cw) { return cw.indexOf(qw) === 0; });
    })) return 2;
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
   * @param {object} [ingredientSearch]  ingredient-search.js's api, for a group
   *                                     that carries a `vocabulary`; defaults
   *                                     to HTF.ingredientSearch when loaded
   */
  function create(data, ingredientSearch) {
    var d = data || {};
    var pickerApi = ingredientSearch || (root.HTF && root.HTF.ingredientSearch) || null;
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
       leads to an empty index would be a promise the page cannot keep.

       A GROUP WITH A `vocabulary` IS READ THROUGH THE INDEX'S OWN PICKER --
       #1289. Food's HAS TO HAVE words are main_ingredients as the recipes
       wrote them, and the picker they are handed to (`?ing=`) does not offer
       those: it strips a modifier, applies an alias and folds a plural, so
       "sweet potatoes" is "sweet potato" there and "fresh garlic cloves" is
       "garlic". Offering the raw text showed one ingredient two or three
       times (56 of them, measured over every recipe and draft), and a click on
       the form the picker had renamed landed on a half-finished search. So
       each value goes through ingredient-search.js's buildMasterList, values
       sharing an entryKey are ONE word, and the label is the first of them in
       the picker's own alphabetical order -- the entry its pool would show.
       `id` is what a word is counted and merged on; `key` stays the folded
       LABEL, because the highlight indexes into the label.

       IT FAILS OPEN. No vocabulary (cocktails, whose words are already a
       declared list), or the picker's module not loaded: every value is its
       own word, which is exactly what this did before. */
    var groups = (d.groups || []).map(function (g) {
      var picker = (g.vocabulary && pickerApi) ? pickerApi.create(g.vocabulary) : null;

      function entriesOf(v) {
        if (!picker) return [{ id: foldByCharacter(v), label: String(v) }];
        return picker.buildMasterList([String(v)]).map(function (entry) {
          return { id: picker.entryKey(entry), label: entry };
        });
      }

      var counts = Object.create(null);
      var labels = Object.create(null);
      items.forEach(function (entry) {
        var raw = entry.item[g.field];
        var list = Array.isArray(raw) ? raw : (raw == null || raw === '' ? [] : [raw]);
        var counted = Object.create(null);   // a page listing "egg" AND "eggs" is one page
        list.forEach(function (v) {
          entriesOf(v).forEach(function (e) {
            if (!e.id.trim()) return;
            if (!labels[e.id]) labels[e.id] = [];
            if (labels[e.id].indexOf(e.label) === -1) labels[e.id].push(e.label);
            if (counted[e.id]) return;
            counted[e.id] = true;
            counts[e.id] = (counts[e.id] || 0) + 1;
          });
        });
      });
      var display = Object.create(null);
      Object.keys(labels).forEach(function (id) {
        // buildMasterList's own comparator, so the label is the entry the
        // picker's pool keeps when it meets the same two.
        display[id] = picker ? labels[id].slice().sort(function (a, b) {
          return a.toLowerCase().localeCompare(b.toLowerCase());
        })[0] : labels[id][0];
      });
      var order;
      if (Array.isArray(g.values)) {
        order = g.values.map(function (v) { return foldByCharacter(v); });
        g.values.forEach(function (v) {
          var id = foldByCharacter(v);
          if (!display[id]) display[id] = String(v);
        });
      } else {
        order = Object.keys(counts).sort(function (a, b) {
          var ka = foldByCharacter(display[a]), kb = foldByCharacter(display[b]);
          return ka < kb ? -1 : (ka > kb ? 1 : 0);
        });
      }
      var seen = Object.create(null);
      var vocab = [];
      order.forEach(function (id) {
        if (seen[id] || !counts[id]) return;
        seen[id] = true;
        vocab.push({ id: id, key: foldByCharacter(display[id]), label: display[id], count: counts[id] });
      });
      return {
        kind: String(g.kind || ''),
        label: String(g.label || ''),
        param: String(g.param || ''),
        picker: picker,
        vocab: vocab
      };
    });

    /* A filtered link ENDS IN `#results` -- Helen, 2026-09-15: "load the index
       page filtered as appropriate, with the screen snapped to the returned
       recipes (so don't have to scroll down)." Both indexes put that id on
       their count line, just above the list, so the browser lands the reader
       on the answer rather than on the panel of questions above it (and each
       index scrolls there again once its list is revealed). A badge or chip
       link on a page does not carry it: those have landed at the top since
       #40 and this is a change to what a SEARCH result does. */
    var RESULTS_FRAGMENT = '#results';

    function hrefForWord(group, label) {
      return home + '?' + encode(group.param) + '=' + encode(label) + RESULTS_FRAGMENT;
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
      var byTier = [[], [], []];
      items.forEach(function (entry) {
        var tier = tierOf(entry.folded, query);
        if (tier) byTier[tier].push(entry);
      });
      /* PREFIX ONLY, WHOLE WORDS ONLY -- #1052. Helen's "prefix-matched title
         string results first" used to fall back to a mid-word substring when
         nothing prefixed ("roni" finding Negroni); that fallback is gone, so a
         query that prefixes no word anywhere in the title is simply not a
         name match. */
      var named = byTier[1].concat(byTier[2]);
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
        /* A MERGED WORD STILL ANSWERS TO THE FORM THAT WAS MERGED AWAY --
           #1289. "cherries" and "cherry" are one word labelled "cherries", and
           "potatoes" is labelled "potato"; typing either spelling in full has
           to find it. So the query is also read exactly as the picker reads an
           entry -- the same rename, then each word to its singular -- and
           tried against the word's `id`. The label is tried first and wins the
           tier when both match. */
        var pickerQueries = !g.picker ? [] : g.picker.buildMasterList([query])
          .map(function (entry) { return g.picker.entryKey(entry); })
          .filter(Boolean);
        var bands = [[], [], []];
        g.vocab.forEach(function (v) {
          var tier = tierOf(v.key, query);
          pickerQueries.forEach(function (pq) {
            var t = tierOf(v.id, pq);
            if (t && (!tier || t < tier)) tier = t;
          });
          if (tier) bands[tier].push(v);
        });
        var matched = bands[1].concat(bands[2]);
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

    return { search: search, groups: groups, itemCount: items.length, RESULTS_FRAGMENT: RESULTS_FRAGMENT };
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
      withPicker(json, function () {
        if (json) searcher = create(json);
        loading = false;
        var fns = waiting;
        waiting = [];
        fns.forEach(function (fn) { fn(); });
      });
    });
  }

  /* THE PICKER'S MODULE, FETCHED ONLY WHEN THE JSON ASKS FOR IT -- #1289. A
     group that carries a `vocabulary` names the script that reads it
     (`reader`, food's ingredient-search.js). The food index has already loaded
     that for its own picker; a recipe page has not and gets it here, on first
     focus, beside the JSON -- so no page pays for it until the box is used and
     none loads it twice. A script that fails to load is not an error: create()
     then offers the words unmerged, as it did before. */
  function withPicker(json, then) {
    var src = null;
    ((json && json.groups) || []).forEach(function (g) {
      if (g.vocabulary && g.reader) src = String(g.reader);
    });
    if (!src || root.HTF.ingredientSearch) { then(); return; }
    var script = document.createElement('script');
    script.src = src;
    script.onload = then;
    script.onerror = then;
    document.head.appendChild(script);
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
      // Helen's copy, #1055: "nothing to see here."
      var none = el('p', 'page-search-none');
      none.textContent = 'nothing to see here';
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
