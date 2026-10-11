// =============================================================================
// PAGE SEARCH — the "search for anything" box in the page header, and its
// dropdown (#1050). `create(data)` is pure and testable in Node; everything
// under "DOM wiring" is the box, the dropdown and the keyboard (MANUAL §3).
//
// _includes/page-search.html renders the box, under the `show_header_search`
// gate, as a plain GET form to this site's index carrying `q=`, which works
// with no JavaScript; this file upgrades it. Per site, never across sites.
//
// It searches a JSON file the build writes (food/search.json,
// cocktails/search.json), fetched on first focus. The JSON comes from the
// gated collections, so the dropdown only offers a page that is live.
//
// Matching is prefix only, whole words only (#1052): every word typed must
// prefix a whole word of the candidate. No substring fallback. Names are
// listed first, then the tag groups.
// =============================================================================

(function (root) {
  'use strict';

  // Fewer characters than this and the dropdown stays shut. The plain form
  // still submits at any length.
  var MIN_QUERY_CHARS = 2;

  // How many of each kind the dropdown shows before saying "+N more". The cap
  // is stated, never silent: a list that quietly stops looks complete.
  var ITEM_CAP = 6;
  var WORD_CAP = 5;

  // The same fold as ingredient-search.js, copied because a recipe page does
  // not load that module with the page. tests/js/page-search.test.js holds
  // the two equal.
  function fold(str) {
    return String(str == null ? '' : str)
      .normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/-/g, ' ');
  }

  // Fold one code unit at a time, so an index into the folded string is an
  // index into the original: the highlight is found in the folded text and
  // painted onto the real one. A character that folds to nothing keeps its
  // place as itself.
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

  // The tier of a folded display string for a folded query: 1 it starts with
  // the query outright, 2 every query word prefixes some whole word of it (in
  // any order), 0 no match. There is no substring tier (#1052).
  function tierOf(folded, query) {
    if (folded.indexOf(query) === 0) return 1;
    var qWords = words(query);
    var cWords = words(folded);
    if (qWords.length && qWords.every(function (qw) {
      return cWords.some(function (cw) { return cw.indexOf(qw) === 0; });
    })) return 2;
    return 0;
  }

  // Where the query sits in the display string, for the highlight: the run
  // that begins a word when there is one, otherwise the first occurrence.
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

  // The highlight for a word found through its merged spelling (#1289):
  // "potatoes" finds the word labelled "potato", so what was typed is not in
  // the label. The shared stem is marked instead: the longest run that begins
  // a word of the label and a word of the query. The earliest wins a tie; a
  // run shorter than MIN_QUERY_CHARS is no run.
  function stemHitOf(folded, query) {
    function starts(str) {
      var out = [];
      for (var i = 0; i < str.length; i++) {
        if (!/\s/.test(str.charAt(i)) && (i === 0 || /\s/.test(str.charAt(i - 1)))) out.push(i);
      }
      return out;
    }
    var best = null;
    starts(folded).forEach(function (p) {
      starts(query).forEach(function (q) {
        var n = 0;
        while (p + n < folded.length && q + n < query.length &&
               folded.charAt(p + n) === query.charAt(q + n)) n++;
        while (n > 0 && /\s/.test(folded.charAt(p + n - 1))) n--;
        if (n >= MIN_QUERY_CHARS && (!best || n > best[1] - best[0])) best = [p, p + n];
      });
    });
    return best;
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

    // Every group's vocabulary, counted. A declared list (`values`) keeps its
    // own order; a group without one is built from what the items carry,
    // alphabetically. A word with no item is dropped: a result leading to an
    // empty index is a promise the page cannot keep.
    //
    // A group with a `vocabulary` is read through the index's own picker
    // (#1289), because `?ing=` hands the word to that picker: each value goes
    // through buildMasterList, values sharing an entryKey are one word, and
    // the label is the entry the picker's pool would show. `id` is what a word
    // is counted and merged on; `key` stays the folded label, because the
    // highlight indexes into the label. With no vocabulary, or the picker's
    // module not loaded, every value is its own word.
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

    // A filtered link ends in `#results`, an id both indexes put just above
    // their list, so the reader lands on the answer. Badge and chip links do
    // not carry it.
    var RESULTS_FRAGMENT = '#results';

    function hrefForWord(group, label) {
      return home + '?' + encode(group.param) + '=' + encode(label) + RESULTS_FRAGMENT;
    }

    // The whole dropdown for one query: a list of groups, each with the
    // results it shows and how many it holds back. A query under the minimum
    // is `null`, which the wiring reads as "close"; a query matching nothing
    // is a result with no groups, and is shown as one.
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
        // A merged word still answers to the spelling that was merged away
        // (#1289): the query is also read as the picker reads an entry and
        // tried against the word's `id`. The better tier of the two wins.
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
              // By its label when the label matched; otherwise it was found
              // through its merged spelling, and the shared stem is marked.
              hit: tierOf(v.key, query) ? hitOf(v.key, query) : stemHitOf(v.key, query),
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

  var api = {
    MIN_QUERY_CHARS: MIN_QUERY_CHARS,
    ITEM_CAP: ITEM_CAP,
    WORD_CAP: WORD_CAP,
    fold: fold,
    foldByCharacter: foldByCharacter,
    tierOf: tierOf,
    hitOf: hitOf,
    stemHitOf: stemHitOf,
    create: create
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
    return;
  }
  root.HTF = root.HTF || {};
  root.HTF.pageSearch = api;

  // --- DOM wiring --------------------------------------------------------------
  // One box per page. The form names the JSON to fetch in `data-search-index`;
  // the include renders the dropdown element empty and hidden.

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

  // Fetched on first focus, once, through assets.js's fetchJson. A failed
  // fetch leaves `searcher` null and the box stays a plain form.
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

  // The picker's module, loaded only when the JSON asks for it (#1289): a
  // group carrying a `vocabulary` names the script that reads it in `reader`.
  // Skipped when the page has already loaded it. A script that fails to load
  // is not an error: create() then offers the words unmerged.
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

  // The label with its matched run wrapped. Built from nodes, not an HTML
  // string, so a title can carry any character.
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
      // Helen's copy (#1055).
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
        // A real link, so middle-click, open in new tab and copy link address
        // all work.
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
        // "+N more" and nothing after it (#1088).
        more.textContent = '+' + group.hidden + ' more';
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
      // A chosen result goes where its link goes; Enter with nothing chosen
      // falls through to the form, which is the name search on the index.
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
