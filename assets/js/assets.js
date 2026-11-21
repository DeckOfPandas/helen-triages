// assets.js
// Base URL, SVG/JSON loading, and the helpers both index pages share.
// Must be the FIRST script loaded: every other script reaches into window.HTF,
// and every URL under assets/ is built here so there is one derivation of the
// base URL and one place that warns when a fetch fails. Nothing here knows
// which site it is on beyond HTF.site (#686).

window.HTF = window.HTF || {};

(function (HTF) {

  // --- Base URL --------------------------------------------------------------
  // _layouts/default.html emits <meta name="base-url" content="{{ '/' | relative_url }}">.
  // Trailing slash stripped so callers can write HTF.asset('/assets/...').
  var meta = document.querySelector('meta[name="base-url"]');
  HTF.base = meta ? (meta.getAttribute('content') || '').replace(/\/$/, '') : '';

  if (!meta) {
    console.warn(
      'assets.js: no <meta name="base-url"> found in the page head. Asset URLs ' +
      'will be built relative to the site root, which is wrong for any ' +
      'deployment with a baseurl. Check _layouts/default.html.'
    );
  }

  /** URL for a root-relative path, e.g. '/assets/img/social/food.png'. */
  HTF.asset = function (path) {
    return HTF.base + path;
  };

  // --- Site key --------------------------------------------------------------
  // From <meta name="site-key">, emitted by _layouts/default.html. Empty is
  // legitimate: the root landing page belongs to neither site and draws no
  // site artwork, so an absent value is not warned about.
  var siteMeta = document.querySelector('meta[name="site-key"]');
  HTF.site = siteMeta ? (siteMeta.getAttribute('content') || '').trim() : '';

  /**
   * URL for a file in THIS site's artwork set:
   * siteAsset('/highlighters/highlighter-3.svg')
   *   -> '<base>/assets/img/food/highlighters/highlighter-3.svg'
   * Returns null when the page has no site key, so callers skip the fetch
   * rather than request a path with a hole in it.
   */
  HTF.siteAsset = function (path) {
    if (!HTF.site) { return null; }
    return HTF.base + '/assets/img/' + HTF.site + path;
  };

  /**
   * URL for a file in the shared chrome's artwork set (header and footer):
   * chromeAsset('/tape/tape-3.svg') -> '<base>/assets/img/chrome/tape/tape-3.svg'
   * Never null: chrome renders on every page, including one with no site.
   * Not a call to the generic asset() above:
   * test_artwork_fetches_go_through_site_asset bans every image path built
   * through that one and greps comments too, so do not spell the call out here.
   */
  HTF.chromeAsset = function (path) {
    return HTF.base + '/assets/img/chrome' + path;
  };

  // --- SVG loading -----------------------------------------------------------
  var cache = {};
  // URLs with a fetch in flight, each holding the callbacks waiting on it.
  // `cache` is written only when a fetch resolves, so without this every
  // caller that arrives before then fires its own fetch: decorations.js asks
  // once per .tag-shape slot, and a page has far more slots than SVG files.
  var pending = {};

  /**
   * Fetch an SVG's source text and hand it to cb. One network call per URL,
   * concurrent requests included. A failure warns with the URL and does not
   * throw, and cb is never called.
   */
  HTF.fetchSvg = function (url, cb) {
    if (cache[url]) { cb(cache[url]); return; }
    if (pending[url]) { pending[url].push(cb); return; }
    pending[url] = [cb];
    fetch(url)
      .then(function (response) {
        if (!response.ok) {
          throw new Error('HTTP ' + response.status + ' ' + response.statusText);
        }
        return response.text();
      })
      .then(function (text) {
        cache[url] = text;
        var waiting = pending[url];
        delete pending[url];
        waiting.forEach(function (fn) { fn(text); });
      })
      .catch(function (error) {
        delete pending[url];
        console.warn(
          'assets.js: could not load ' + url + ' — ' + error.message + '\n' +
          'If every decoration on the page is missing, the likely cause is ' +
          'baseurl in _config.yml not matching where the site is actually ' +
          'served from. Current base: "' + HTF.base + '"'
        );
      });
  };

  /**
   * Fetch a JSON file and hand the parsed value to cb (#1050, the search
   * index). Unlike fetchSvg, cb is called on failure too, with null: the
   * search box has to be told to stay a plain form.
   * test_svg_fetching_goes_through_the_shared_helper holds every other file
   * to fetching through this file.
   */
  var jsonCache = {};
  var jsonPending = {};
  HTF.fetchJson = function (url, cb) {
    if (jsonCache[url]) { cb(jsonCache[url]); return; }
    if (jsonPending[url]) { jsonPending[url].push(cb); return; }
    jsonPending[url] = [cb];
    function settle(value) {
      var waiting = jsonPending[url] || [];
      delete jsonPending[url];
      waiting.forEach(function (fn) { fn(value); });
    }
    fetch(url, { credentials: 'same-origin' })
      .then(function (response) {
        if (!response.ok) {
          throw new Error('HTTP ' + response.status + ' ' + response.statusText);
        }
        return response.json();
      })
      .then(function (data) {
        jsonCache[url] = data;
        settle(data);
      })
      .catch(function (error) {
        console.warn('assets.js: could not load ' + url + ' — ' + error.message);
        settle(null);
      });
  };

  /**
   * Deal names from a pool without repeats until it is exhausted. Shuffled
   * once per page load.
   */
  HTF.makeShuffledPicker = function (names) {
    var shuffled = names
      .map(function (n) { return { n: n, r: Math.random() }; })
      .sort(function (a, b) { return a.r - b.r; })
      .map(function (o) { return o.n; });
    var idx = 0;
    return function () { return shuffled[idx++ % shuffled.length]; };
  };

  // --- HTML escaping ---------------------------------------------------------
  /**
   * Escape a string for insertion into HTML, text position or attribute value.
   * `&` is replaced FIRST, or the other escapes would be escaped again into
   * &amp;lt;.
   */
  HTF.escapeHtml = function (text) {
    return String(text)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  };

  // --- Index memory ----------------------------------------------------------
  // Both indexes remember the order and filters they were left in, so going
  // BACK from a recipe returns to the list being read (#387). The caller
  // passes its own key and record, and decides whether to restore at all
  // (FilterState.arrivedByGoingBack).
  // Every path is wrapped: private mode throws on setItem, blocked site data
  // can make the getter throw, and a context with no sessionStorage is a
  // ReferenceError. All end as a fresh list.
  HTF.indexMemory = {
    /** Store an index's state under the caller's key. Silent on failure. */
    save: function (key, state) {
      try {
        sessionStorage.setItem(key, JSON.stringify(state));
      } catch (e) { /* nothing to be done, and nothing worth breaking for */ }
    },

    /**
     * Read back what save() stored. Null on every failure, and null means
     * "carry on as a fresh load". The caller checks the SHAPE of what comes
     * back: a record written by an older build is untrusted input.
     */
    restore: function (key) {
      try {
        return JSON.parse(sessionStorage.getItem(key)) || null;
      } catch (e) {
        return null;
      }
    }
  };

  // --- The shortlists: named lists, in this browser only. MANUAL §8.9 -------
  // - One localStorage record per site, keyed by HTF.site: both sites share
  //   one origin. Every list, with its counts and ticks, is in that record.
  // - An entry is a collection URL (`page.url` in Liquid, NOT `relative_url`):
  //   a baseurl prefix would empty every stored list the day baseurl changed.
  // - The in-memory copy is the source of truth: when setItem throws, the
  //   lists still work until the page closes. Calls without a list id act on
  //   the ACTIVE list, the one the index shows; there is always one.
  var shortlist = (function () {
    var RECORD_PREFIX = 'htf-shortlists-';
    var DEFAULT_NAME = 'Shortlist';
    var NAME_MAX = 40;
    // The most of anything a list holds: glasses, portions or batches. Equal
    // to the `max` the shopping list's boxes declare. A box's `max` is not
    // enforced on typing, and an uncapped count prints "6.2e+28 kg".
    var MAX_COUNT = 99;
    var ALL = 'all';    // SEE ALL's id: never a list's, which are `l<n>`
    var state = null;   // { active, lists: [list], all }; null until first read

    function recordKey() {
      return HTF.site ? RECORD_PREFIX + HTF.site + '-v1' : '';
    }

    /* The one-list keys this record replaced. Read only when the record is
       absent, so a reader's list from before #1521 becomes "Shortlist". */
    function legacyKey(kind) {
      var versions = { '': '-v1', 'glasses-': '-v1', 'portions-': '-v2',
        'batches-': '-v1', 'ticked-': '-v1' };
      return 'htf-shortlist-' + kind + HTF.site + versions[kind];
    }

    function getJSON(key) {
      try { return JSON.parse(localStorage.getItem(key)); } catch (e) { return undefined; }
    }

    // --- Stored state is untrusted input -----------------------------------
    // Hand-edited, left by an older build, or the wrong shape. Each part is
    // read on its own, so one bad part costs only itself.

    function stringList(raw) {
      var out = [];
      if (!Array.isArray(raw)) return out;
      raw.forEach(function (v) {
        if (typeof v === 'string' && v && out.indexOf(v) === -1) out.push(v);
      });
      return out;
    }

    function countMap(raw, keep) {
      var out = {};
      if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return out;
      Object.keys(raw).forEach(function (url) {
        var n = typeof raw[url] === 'number' && isFinite(raw[url]) ? keep(raw[url]) : null;
        if (n !== null) out[url] = n;
      });
      return out;
    }

    /* A missing glasses entry is one glass, so only counts above one are kept. */
    function glassesValue(n) {
      var value = Math.min(MAX_COUNT, Math.floor(Number(n)));
      return isFinite(value) && value > 1 ? value : null;
    }

    /* A missing portions entry is "however many this recipe makes", which only
       the build knows, so `1` is a real answer (#801). */
    function portionsValue(n) {
      var value = Math.min(MAX_COUNT, Math.floor(Number(n)));
      return isFinite(value) && value >= 1 ? value : null;
    }

    /* A `makes:` recipe counts batches (#1297): the nearest whole number, or a
       half below three quarters. Whether THIS recipe may have a half is the
       caller's question. */
    function batchesValue(n) {
      var value = Number(n);
      if (n === null || n === '' || !isFinite(value) || value <= 0) return null;
      if (value < 0.75) return 0.5;
      return Math.min(MAX_COUNT, Math.max(1, Math.round(value)));
    }

    /* A list's name: one line, no control characters, at most NAME_MAX long.
       '' when nothing is left. Names are unique, ignoring case. */
    function cleanName(raw) {
      return String(raw == null ? '' : raw)
        .replace(/[\u0000-\u001f\u007f\s]+/g, ' ')
        .trim().slice(0, NAME_MAX).trim();
    }

    function blankList(id, name) {
      return { id: id, name: name, entries: [], glasses: {}, portions: {},
        batches: {}, ticked: [] };
    }

    function fillList(list, raw) {
      list.entries = stringList(raw.entries);
      list.glasses = countMap(raw.glasses, glassesValue);
      list.portions = countMap(raw.portions, portionsValue);
      list.batches = countMap(raw.batches, batchesValue);
      list.ticked = stringList(raw.ticked);
      return list;
    }

    function fromLegacy() {
      return fillList(blankList('l1', DEFAULT_NAME), {
        entries: getJSON(legacyKey('')),
        glasses: getJSON(legacyKey('glasses-')),
        portions: getJSON(legacyKey('portions-')),
        batches: getJSON(legacyKey('batches-')),
        ticked: getJSON(legacyKey('ticked-'))
      });
    }

    function nextId(lists) {
      var most = 0;
      lists.forEach(function (l) {
        var n = Number(l.id.slice(1));
        if (n > most) most = n;
      });
      return 'l' + (most + 1);
    }

    function named(lists, name, exceptId) {
      var folded = name.toLowerCase();
      for (var i = 0; i < lists.length; i += 1) {
        if (lists[i].id !== exceptId && lists[i].name.toLowerCase() === folded) return lists[i];
      }
      return null;
    }

    function fromRecord(raw) {
      var lists = [];
      var rawLists = raw && typeof raw === 'object' && Array.isArray(raw.lists) ? raw.lists : [];
      rawLists.forEach(function (item) {
        if (!item || typeof item !== 'object') return;
        var name = cleanName(typeof item.name === 'string' ? item.name : '');
        if (!name || named(lists, name)) return;
        var taken = lists.some(function (l) { return l.id === item.id; });
        var id = typeof item.id === 'string' && /^l[0-9]+$/.test(item.id) && !taken
          ? item.id : nextId(lists);
        lists.push(fillList(blankList(id, name), item));
      });
      if (!lists.length) lists.push(blankList('l1', DEFAULT_NAME));
      var active = raw.active === ALL || lists.some(function (l) { return l.id === raw.active; })
        ? raw.active : lists[0].id;
      var all = raw.all && typeof raw.all === 'object' ? raw.all : {};
      return { active: active, lists: lists, all: fillList(blankList(ALL, ''), all) };
    }

    function read() {
      if (state) return state;
      var key = recordKey();
      var text = null;
      if (key) {
        try { text = localStorage.getItem(key); } catch (e) { text = null; }
      }
      if (text === null || text === undefined) {
        state = { active: 'l1', lists: [key ? fromLegacy() : blankList('l1', DEFAULT_NAME)],
          all: blankList(ALL, '') };
      } else {
        var raw;
        try { raw = JSON.parse(text); } catch (e) { raw = null; }
        state = fromRecord(raw || {});
      }
      return state;
    }

    function write() {
      var key = recordKey();
      if (!key) return;
      try {
        localStorage.setItem(key, JSON.stringify(state));
      } catch (e) { /* this visit still has it; tomorrow will not */ }
    }

    function find(id) {
      var lists = read().lists;
      for (var i = 0; i < lists.length; i += 1) if (lists[i].id === id) return lists[i];
      return null;
    }

    /* Every recipe on any list, once, in list order then the order added. */
    function union() {
      var seen = [];
      read().lists.forEach(function (l) {
        l.entries.forEach(function (url) { if (seen.indexOf(url) === -1) seen.push(url); });
      });
      return seen;
    }

    /* A list's counts and ticks, or SEE ALL's own, which no list shares. */
    function bucket(id) {
      return id === ALL ? read().all : find(id);
    }

    /* The list on show. SEE ALL is the union, with its own counts and ticks:
       the maps are SEE ALL's own objects, mutated in place; `entries` is a
       copy, never written to. */
    function active() {
      var s = read();
      if (s.active === ALL) {
        return { id: ALL, name: '', entries: union(), glasses: s.all.glasses,
          portions: s.all.portions, batches: s.all.batches, ticked: s.all.ticked };
      }
      return find(s.active) || s.lists[0];
    }

    function countIn(holder, kind, url) {
      var n = holder ? holder[kind][url] : null;
      return typeof n === 'number' && n > 0 ? n : null;
    }

    /* `value` is already cleaned; null forgets the entry. */
    function setCountIn(holder, kind, url, value) {
      if (!url || !holder) return null;
      if (value === null) delete holder[kind][url];
      else holder[kind][url] = value;
      write();
      return value;
    }

    /* Where an addition to "the list on show" goes: SEE ALL has no entries of
       its own, so its first list. */
    function writable() {
      return read().active === ALL ? read().lists[0] : active();
    }

    function toggleIn(id, url) {
      var list = find(id);
      if (!list || !url) return false;
      var at = list.entries.indexOf(url);
      if (at === -1) list.entries.push(url); else list.entries.splice(at, 1);
      write();
      return at === -1;
    }

    /* Add every one of these to one list and persist once. A merge: what is
       already on it keeps its place. -> how many were not already on it. */
    function addInto(list, urls) {
      var added = 0;
      (Array.isArray(urls) ? urls : []).forEach(function (url) {
        if (typeof url !== 'string' || !url) return;
        if (list.entries.indexOf(url) === -1) { list.entries.push(url); added += 1; }
      });
      if (added) write();
      return added;
    }

    /* The list a kept or restored list goes into: the one of that name, or a
       new one. A nameless link goes into the active list (#1093). */
    function listFor(name) {
      var clean = cleanName(name);
      if (!clean) return writable();
      var found = named(read().lists, clean);
      if (found) return found;
      var list = blankList(nextId(read().lists), clean);
      read().lists.push(list);
      return list;
    }

    /* A key's slug: the last non-empty path segment, lowercased.
       `/food/recipes/dal/` and `/food/drafts/dal/` both answer `dal`; "/"
       answers ''. The share link (#1093) is built from it. */
    function slugOf(key) {
      var parts = String(key).split('/');
      for (var i = parts.length - 1; i >= 0; i -= 1) {
        var part = parts[i].trim();
        if (part) return part.toLowerCase();
      }
      return '';
    }

    function resolveSlugs(slugs, liveKeys) {
      var bySlug = {};
      (Array.isArray(liveKeys) ? liveKeys : []).forEach(function (key) {
        if (typeof key !== 'string') return;
        var slug = slugOf(key);
        // First one wins.
        if (slug && !Object.prototype.hasOwnProperty.call(bySlug, slug)) bySlug[slug] = key;
      });
      var out = { keys: [], unmatched: [] };
      (Array.isArray(slugs) ? slugs : []).forEach(function (raw) {
        if (typeof raw !== 'string') return;
        var slug = raw.trim().toLowerCase();
        if (!slug) return;
        if (Object.prototype.hasOwnProperty.call(bySlug, slug)) {
          if (out.keys.indexOf(bySlug[slug]) === -1) out.keys.push(bySlug[slug]);
        } else if (out.unmatched.indexOf(slug) === -1) {
          out.unmatched.push(slug);
        }
      });
      return out;
    }

    return {
      DEFAULT_NAME: DEFAULT_NAME,
      NAME_MAX: NAME_MAX,
      cleanName: cleanName,

      // --- The lists themselves (#1521) -----------------------------------

      /** @returns {{id:string, name:string, count:number}[]} in the order made */
      lists: function () {
        return read().lists.map(function (l) {
          return { id: l.id, name: l.name, count: l.entries.length };
        });
      },

      /** @returns {string} the id of the list the index shows */
      activeId: function () { return active().id; },

      /** @returns {string} its name */
      activeName: function () { return active().name; },

      /** SEE ALL's id, for setActive and the `...In` count calls. */
      ALL: ALL,

      /** @returns {boolean} false for an id that names no list, nor SEE ALL */
      setActive: function (id) {
        if (id !== ALL && !find(id)) return false;
        read().active = id;
        write();
        return true;
      },

      /**
       * Whether a name is free to use. Clean it first.
       * @param {string} [exceptId] - the list being renamed, which may keep its own
       */
      nameFree: function (name, exceptId) {
        var clean = cleanName(name);
        return !!clean && !named(read().lists, clean, exceptId);
      },

      /** @returns {string|null} the new list's id; null for an empty or taken name */
      create: function (name) {
        var clean = cleanName(name);
        if (!clean || named(read().lists, clean)) return null;
        var list = blankList(nextId(read().lists), clean);
        read().lists.push(list);
        write();
        return list.id;
      },

      /** @returns {boolean} false for no such list, or an empty or taken name */
      rename: function (id, name) {
        var list = find(id);
        var clean = cleanName(name);
        if (!list || !clean || named(read().lists, clean, id)) return false;
        list.name = clean;
        write();
        return true;
      },

      /** Delete a list. The last one goes too, and an empty "Shortlist" takes
          its place. The active list moves to the first. @returns {boolean} */
      remove: function (id) {
        var s = read();
        var at = -1;
        s.lists.forEach(function (l, i) { if (l.id === id) at = i; });
        if (at === -1) return false;
        s.lists.splice(at, 1);
        if (!s.lists.length) s.lists.push(blankList(nextId([{ id: id }]), DEFAULT_NAME));
        if (s.active !== ALL && !find(s.active)) s.active = s.lists[0].id;
        write();
        return true;
      },

      /** @returns {boolean} */
      hasIn: function (id, url) {
        var list = find(id);
        return !!list && list.entries.indexOf(url) !== -1;
      },

      /** Flip one entry in one list. @returns {boolean} true if it is now on it */
      toggleIn: toggleIn,

      /** @returns {boolean} whether any list holds it: what a + mark shows */
      inAny: function (url) {
        return read().lists.some(function (l) { return l.entries.indexOf(url) !== -1; });
      },

      /** @returns {number} recipes on any list, each counted once */
      total: function () { return union().length; },

      /** Every list with something on it, for the export block.
          @returns {{name:string, keys:string[]}[]} */
      exportLists: function () {
        return read().lists.filter(function (l) { return l.entries.length; })
          .map(function (l) { return { name: l.name, keys: l.entries.slice() }; });
      },

      // --- The active list --------------------------------------------------

      /** @returns {string[]} the entries, oldest first. A copy — callers sort. */
      list: function () { return active().entries.slice(); },

      /** @param {string} url @returns {boolean} */
      has: function (url) { return active().entries.indexOf(url) !== -1; },

      /** @returns {number} */
      count: function () { return active().entries.length; },

      /** Flip one entry and persist. @returns {boolean} true if it is now on it */
      toggle: function (url) { return toggleIn(writable().id, url); },

      /** Empty the active list: the marks, the counts and the ticks together.
          No page control calls it; the store's tests do. */
      clear: function () {
        fillList(read().active === ALL ? read().all : active(), {});
        write();
      },

      /* --- How many glasses of each (#546) ----------------------------------
         A missing entry is one glass, so setting a count back to 1 removes
         it, and a number left behind by a dropped drink is read by nothing. */
      glasses: function (url) {
        var n = active().glasses[url];
        return typeof n === 'number' && n > 0 ? n : 1;
      },

      /**
       * @param {number} n - glasses; 1 or less removes the entry
       * @returns {number} what it ended up as
       */
      setGlasses: function (url, n) {
        if (!url) return 1;
        var value = glassesValue(n);
        if (value === null) delete active().glasses[url];
        else active().glasses[url] = value;
        write();
        return value === null ? 1 : value;
      },

      /**
       * How many portions of this recipe are wanted (#801).
       * @returns {number|null} `null` means nobody has said, and the caller
       *          substitutes the recipe's own portion count
       */
      portions: function (url) { return countIn(active(), 'portions', url); },

      /**
       * @param {number|null} n - portions; anything below 1 forgets the entry
       * @returns {number|null} what it ended up as
       */
      setPortions: function (url, n) {
        return setCountIn(active(), 'portions', url,
          n === null || n === undefined ? null : portionsValue(n));
      },

      /**
       * How many batches of this `makes:` recipe are wanted (#1297).
       * @returns {number|null} a whole number or 0.5; `null` means nobody has
       *          said, which is one batch
       */
      batches: function (url) { return countIn(active(), 'batches', url); },

      /**
       * @param {number|null} n - batches: the nearest whole number, or a half
       *        below three quarters; nothing or zero forgets the entry
       * @returns {number|null} what it ended up as
       */
      setBatches: function (url, n) {
        return setCountIn(active(), 'batches', url, batchesValue(n));
      },

      /* The same four for a named list, or SEE ALL (`ALL`): the recipe page's
         scaler reads and writes SEE ALL's numbers (#1521). */
      portionsIn: function (id, url) { return countIn(bucket(id), 'portions', url); },
      setPortionsIn: function (id, url, n) {
        return setCountIn(bucket(id), 'portions', url,
          n === null || n === undefined ? null : portionsValue(n));
      },
      batchesIn: function (id, url) { return countIn(bucket(id), 'batches', url); },
      setBatchesIn: function (id, url, n) {
        return setCountIn(bucket(id), 'batches', url, batchesValue(n));
      },

      /* --- What is already in the basket (#1457) ----------------------------
         Shopping-list row keys, as each list's build() returns them: folded
         names, so a row keeps its tick when "lemon" becomes "lemons". Kept
         until "untick all", not pruned to the rows on show. */

      /** @param {string} rowKey - a shopping-list row's `key` @returns {boolean} */
      ticked: function (rowKey) { return active().ticked.indexOf(rowKey) !== -1; },

      /**
       * @param {string} rowKey - a shopping-list row's `key`
       * @param {boolean} on
       * @returns {boolean} whether it is now ticked
       */
      setTicked: function (rowKey, on) {
        if (typeof rowKey !== 'string' || !rowKey) return false;
        var all = active().ticked;
        var at = all.indexOf(rowKey);
        if (on && at === -1) all.push(rowKey);
        if (!on && at !== -1) all.splice(at, 1);
        write();
        return !!on;
      },

      /**
       * Untick several rows and persist once.
       * @param {string[]} rowKeys
       * @returns {number} how many were ticked
       */
      untick: function (rowKeys) {
        var all = active().ticked;
        var dropped = 0;
        (Array.isArray(rowKeys) ? rowKeys : []).forEach(function (rowKey) {
          var at = all.indexOf(rowKey);
          if (at !== -1) { all.splice(at, 1); dropped += 1; }
        });
        if (dropped) write();
        return dropped;
      },

      /** Every tick, shown or not: the list starts afresh for the next shop. */
      untickAll: function () {
        active().ticked.length = 0;
        write();
      },

      /* --- A shortlist someone sent (#1093) ---------------------------------
         `?shortlist=aviation,negroni&list=Friday` names drinks by slug: the
         folders around a key move and the last segment does not. slugOf() is
         the one spelling of "a key's slug", so a link this site writes
         resolves here. */
      slugOf: slugOf,

      /**
       * Which live keys a list of slugs names. Reads nothing and writes
       * nothing: opening a shared link shows the list and saves none of it.
       * @param {string[]} slugs - as parsed from the URL, in link order
       * @param {string[]} liveKeys - every `data-shortlist-key` on the page
       * @returns {{keys:string[], unmatched:string[]}} `keys` in link order,
       *          once each; `unmatched` the slugs nothing on the page answers to
       */
      resolveSlugs: resolveSlugs,

      /** Merge these into the active list and persist once.
          @returns {number} how many were not already on it */
      addAll: function (urls) { return addInto(writable(), urls); },

      /**
       * The shared view's "keep these": into the list of that name, made if
       * there is none, or the active list for a nameless link. That list
       * becomes the active one.
       * @returns {{id:string, added:number}}
       */
      keep: function (name, urls) {
        var list = listFor(name);
        var added = addInto(list, urls);
        read().active = list.id;
        write();
        return { id: list.id, added: added };
      },

      /**
       * A pasted export block, put back: each list into the one of its name,
       * made if there is none. The active list stays as it is.
       * @param {{name:string, slugs:string[]}[]} blocks - parseShortlistBlock's
       * @param {string[]} liveKeys - every `data-shortlist-key` on the page
       * @returns {{lists:number, added:number, unmatched:string[]}}
       */
      restore: function (blocks, liveKeys) {
        var out = { lists: 0, added: 0, unmatched: [] };
        (Array.isArray(blocks) ? blocks : []).forEach(function (block) {
          var resolved = resolveSlugs(block.slugs, liveKeys);
          resolved.unmatched.forEach(function (slug) {
            if (out.unmatched.indexOf(slug) === -1) out.unmatched.push(slug);
          });
          if (!resolved.keys.length) return;
          out.added += addInto(listFor(block.name || DEFAULT_NAME), resolved.keys);
          out.lists += 1;
        });
        write();
        return out;
      },

      /* For tests only: drops the cached read so a test can stage a second
         scenario in the same page. */
      _forget: function () { state = null; }
    };
  })();

  HTF.shortlist = shortlist;

  // --- Ticking off the shopping list (#1457) ---------------------------------
  // Shared by filters.js and cocktail-index.js, whose lists are rebuilt whole
  // on every number change: a tick lives in the store and each render reads it
  // back through box() and rowClass(). The box sits inside a <label> with the
  // amount and the name, so tapping the words ticks it and the words name it.
  HTF.shoppingTicks = {
    /** The checkbox for one row. @param {string} key - the row's `key` */
    box: function (key) {
      return '<input type="checkbox" class="shopping-list-tick" data-key="' +
        HTF.escapeHtml(key) + '"' + (shortlist.ticked(key) ? ' checked' : '') + '>';
    },

    /** ' is-ticked' for a ticked row, '' otherwise: a class to append. */
    rowClass: function (key) {
      return shortlist.ticked(key) ? ' is-ticked' : '';
    },

    /**
     * Untick every row a recipe whose count has just changed stands behind:
     * its amounts are new, so what was ticked no longer covers them. Call
     * before the re-render, with the rows of the render before it.
     * @param {Array} rows - build() rows, each with `key` and `recipes`
     * @param {string[]} urls - the recipes whose count changed
     */
    recount: function (rows, urls) {
      if (!urls || !urls.length) return;
      var keys = (rows || []).filter(function (row) {
        return (row.recipes || []).some(function (url) { return urls.indexOf(url) !== -1; });
      }).map(function (row) { return row.key; });
      shortlist.untick(keys);
    },

    /**
     * Listen on a list the boxes are rendered into, and on its "untick all".
     * @param {Element} list - the element whose innerHTML holds the rows
     * @param {Element|null} untick - the button; hidden while nothing shown is ticked
     * @returns {function} call after every render, to show or hide the button
     */
    wire: function (list, untick) {
      function refresh() {
        if (!untick) return;
        untick.hidden = !list.querySelector('.shopping-list-tick:checked');
      }

      // Delegated, because the rows are replaced on every render.
      list.addEventListener('change', function (ev) {
        var box = ev.target;
        if (!box.classList || !box.classList.contains('shopping-list-tick')) return;
        shortlist.setTicked(box.dataset.key, box.checked);
        var row = box.closest ? box.closest('li') : null;
        if (row) row.classList.toggle('is-ticked', box.checked);
        refresh();
      });

      if (untick) {
        untick.addEventListener('click', function () {
          shortlist.untickAll();
          Array.prototype.forEach.call(list.querySelectorAll('.shopping-list-tick'), function (box) {
            box.checked = false;
            var row = box.closest ? box.closest('li') : null;
            if (row) row.classList.remove('is-ticked');
          });
          refresh();
          // The button has just hidden itself; focus must not fall to <body>.
          var first = list.querySelector('.shopping-list-tick');
          if (first) first.focus();
        });
      }

      return refresh;
    }
  };

})(window.HTF);
