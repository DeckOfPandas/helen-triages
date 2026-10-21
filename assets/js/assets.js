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

  // --- The shortlist ---------------------------------------------------------
  // Recipes and drinks marked to come back to, held in this browser only (#546).
  // - localStorage, not sessionStorage: the list must outlive the tab.
  // - One store per site, keyed by HTF.site: both sites share one origin.
  // - An entry is a collection URL (`page.url` in Liquid, NOT `relative_url`):
  //   a baseurl prefix would empty every stored list the day baseurl changed.
  // - The in-memory copy is the source of truth, not a cache: when setItem
  //   throws, the list still works until the page closes.
  var shortlist = (function () {
    var KEY_PREFIX = 'htf-shortlist-';
    var GLASSES_PREFIX = 'htf-shortlist-glasses-';
    var PORTIONS_PREFIX = 'htf-shortlist-portions-';
    var VERSION = '-v1';
    var entries = null;   // the in-memory copy; null until first read
    var counts = null;    // url -> glasses, for the entries that are not 1
    var servings = null;  // url -> portions, for the entries that have been set

    function storageKey() {
      return HTF.site ? KEY_PREFIX + HTF.site + VERSION : '';
    }

    function glassesKey() {
      return HTF.site ? GLASSES_PREFIX + HTF.site + VERSION : '';
    }

    /* Stored state is untrusted input: hand-edited, left by an older build,
       or not an array. Anything that is not a list of strings reads as an
       empty shortlist, never a half-read one. */
    function read() {
      if (entries) return entries;
      entries = [];
      var key = storageKey();
      if (!key) return entries;
      try {
        var raw = JSON.parse(localStorage.getItem(key));
        if (Array.isArray(raw)) {
          raw.forEach(function (v) {
            if (typeof v === 'string' && v && entries.indexOf(v) === -1) entries.push(v);
          });
        }
      } catch (e) { /* an empty shortlist, and the page works */ }
      return entries;
    }

    function write() {
      var key = storageKey();
      if (!key) return;
      try {
        localStorage.setItem(key, JSON.stringify(entries));
      } catch (e) { /* this visit still has it; tomorrow will not */ }
    }

    /* The glasses map: untrusted input like the list above. Only whole numbers
       above one are kept, because a missing entry already means one glass. */
    function readGlasses() {
      if (counts) return counts;
      counts = {};
      var key = glassesKey();
      if (!key) return counts;
      try {
        var raw = JSON.parse(localStorage.getItem(key));
        if (raw && typeof raw === 'object' && !Array.isArray(raw)) {
          Object.keys(raw).forEach(function (url) {
            var n = raw[url];
            if (typeof n === 'number' && isFinite(n) && n > 1) counts[url] = Math.min(MAX_COUNT, Math.floor(n));
          });
        }
      } catch (e) { /* everything is one glass, and the page works */ }
      return counts;
    }

    function writeGlasses() {
      var key = glassesKey();
      if (!key) return;
      try {
        localStorage.setItem(key, JSON.stringify(counts));
      } catch (e) { /* this visit still has it; tomorrow will not */ }
    }

    /* --- How many portions (#801) ------------------------------------------
       A key of its own, not the glasses map: a missing glasses entry is one
       glass, a missing portions entry is "however many this recipe makes",
       which only the build knows. So `1` is a real, storable answer here.
       `-v2` because `-v1` values include batch counts that cannot be told
       from portion counts; a version bump discards them, never reinterprets. */
    function portionsKey() {
      return HTF.site ? PORTIONS_PREFIX + HTF.site + '-v2' : '';
    }

    function readPortions() {
      if (servings) return servings;
      servings = {};
      var key = portionsKey();
      if (!key) return servings;
      try {
        var raw = JSON.parse(localStorage.getItem(key));
        if (raw && typeof raw === 'object' && !Array.isArray(raw)) {
          Object.keys(raw).forEach(function (url) {
            var n = raw[url];
            if (typeof n === 'number' && isFinite(n) && n > 0) {
              servings[url] = Math.min(MAX_COUNT, Math.floor(n));
            }
          });
        }
      } catch (e) { /* every recipe as written, and the page works */ }
      return servings;
    }

    function writePortions() {
      var key = portionsKey();
      if (!key) return;
      try {
        localStorage.setItem(key, JSON.stringify(servings));
      } catch (e) { /* this visit still has it; tomorrow will not */ }
    }

    /* --- How many batches (#1297) ------------------------------------------
       A key of its own, not the portions map: a `makes:` recipe counts
       BATCHES and a `serves:` recipe counts people, and a stored `6` cannot
       say which it is. A half is storable and nothing else below one; whether
       THIS recipe may have a half (page.half_recipe) is the caller's question.
       A missing entry is one batch. */
    var BATCHES_PREFIX = 'htf-shortlist-batches-';

    // The most of anything a list holds: glasses, portions or batches. Equal
    // to the `max` the shopping list's boxes declare. A box's `max` is not
    // enforced on typing, and an uncapped count prints "6.2e+28 kg".
    var MAX_COUNT = 99;
    var batchCounts = null;

    function batchesKey() {
      return HTF.site ? BATCHES_PREFIX + HTF.site + '-v1' : '';
    }

    function wholeOrHalf(n) {
      var value = Number(n);
      if (!isFinite(value) || value <= 0) return null;
      if (value < 0.75) return 0.5;
      return Math.min(MAX_COUNT, Math.max(1, Math.round(value)));
    }

    function readBatches() {
      if (batchCounts) return batchCounts;
      batchCounts = {};
      var key = batchesKey();
      if (!key) return batchCounts;
      try {
        var raw = JSON.parse(localStorage.getItem(key));
        if (raw && typeof raw === 'object' && !Array.isArray(raw)) {
          Object.keys(raw).forEach(function (url) {
            var n = typeof raw[url] === 'number' ? wholeOrHalf(raw[url]) : null;
            if (n !== null) batchCounts[url] = n;
          });
        }
      } catch (e) { /* every recipe at one batch, and the page works */ }
      return batchCounts;
    }

    function writeBatches() {
      var key = batchesKey();
      if (!key) return;
      try {
        localStorage.setItem(key, JSON.stringify(batchCounts));
      } catch (e) { /* this visit still has it; tomorrow will not */ }
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

    function keysBySlug(liveKeys) {
      var bySlug = {};
      (Array.isArray(liveKeys) ? liveKeys : []).forEach(function (key) {
        if (typeof key !== 'string') return;
        var slug = slugOf(key);
        // First one wins.
        if (slug && !Object.prototype.hasOwnProperty.call(bySlug, slug)) {
          bySlug[slug] = key;
        }
      });
      return bySlug;
    }

    return {
      /** @returns {string[]} the entries, oldest first. A copy — callers sort. */
      list: function () { return read().slice(); },

      /** @param {string} url @returns {boolean} */
      has: function (url) { return read().indexOf(url) !== -1; },

      /** @returns {number} */
      count: function () { return read().length; },

      /**
       * Flip one entry and persist.
       * @returns {boolean} true if it is now shortlisted
       */
      toggle: function (url) {
        if (!url) return false;
        var all = read();
        var at = all.indexOf(url);
        if (at === -1) all.push(url); else all.splice(at, 1);
        write();
        return at === -1;
      },

      /** Empty it — the marks and all three count maps together. No page
          control calls it (#1100); the store's tests do. */
      clear: function () {
        entries = [];
        write();
        counts = {};
        writeGlasses();
        servings = {};
        writePortions();
        batchCounts = {};
        writeBatches();
      },

      /* --- How many glasses of each (#546) ----------------------------------
         A second key, not a richer entry: an array of `{url, glasses}` would
         change the shape of every list already stored. A missing entry is one
         glass, so setting a count back to 1 removes it, and a number left
         behind by a dropped drink is read by nothing. */
      glasses: function (url) {
        var n = readGlasses()[url];
        return typeof n === 'number' && n > 0 ? n : 1;
      },

      /**
       * @param {number} n - glasses; 1 or less removes the entry
       * @returns {number} what it ended up as
       */
      setGlasses: function (url, n) {
        if (!url) return 1;
        var all = readGlasses();
        var value = Math.min(MAX_COUNT, Math.floor(Number(n)));
        if (!isFinite(value) || value <= 1) delete all[url];
        else all[url] = value;
        writeGlasses();
        return value > 1 ? value : 1;
      },

      /**
       * How many portions of this recipe are wanted (#801).
       * @returns {number|null} `null` means nobody has said, and the caller
       *          substitutes the recipe's own portion count
       */
      portions: function (url) {
        var n = readPortions()[url];
        return typeof n === 'number' && n > 0 ? n : null;
      },

      /**
       * @param {number|null} n - portions; anything below 1 forgets the entry
       * @returns {number|null} what it ended up as
       */
      setPortions: function (url, n) {
        if (!url) return null;
        var all = readPortions();
        var value = Math.min(MAX_COUNT, Math.floor(Number(n)));
        if (!isFinite(value) || value < 1) {
          delete all[url];
          writePortions();
          return null;
        }
        all[url] = value;
        writePortions();
        return value;
      },

      /**
       * How many batches of this `makes:` recipe are wanted (#1297).
       * @returns {number|null} a whole number or 0.5; `null` means nobody has
       *          said, which is one batch
       */
      batches: function (url) {
        var n = readBatches()[url];
        return typeof n === 'number' && n > 0 ? n : null;
      },

      /**
       * @param {number|null} n - batches: the nearest whole number, or a half
       *        below three quarters; nothing or zero forgets the entry
       * @returns {number|null} what it ended up as
       */
      setBatches: function (url, n) {
        if (!url) return null;
        var all = readBatches();
        var value = wholeOrHalf(n);
        if (value === null) {
          delete all[url];
          writeBatches();
          return null;
        }
        all[url] = value;
        writeBatches();
        return value;
      },

      /* --- A shortlist someone sent (#1093) ---------------------------------
         `?shortlist=aviation,negroni` names drinks by slug: the folders
         around a key move and the last segment does not. slugOf() is the one
         spelling of "a key's slug", so a link this site writes resolves here. */
      slugOf: slugOf,

      /**
       * Which live keys a list of slugs names. Reads nothing and writes
       * nothing: opening a shared link shows the list and saves none of it.
       * @param {string[]} slugs - as parsed from the URL, in link order
       * @param {string[]} liveKeys - every `data-shortlist-key` on the page
       * @returns {{keys:string[], unmatched:string[]}} `keys` in link order,
       *          once each; `unmatched` the slugs nothing on the page answers to
       */
      resolveSlugs: function (slugs, liveKeys) {
        var bySlug = keysBySlug(liveKeys);
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
      },

      /**
       * Mark every one of these and persist once: the shared view's "keep
       * these" (#1093). A merge: what is already marked keeps its place.
       * @returns {number} how many were not already marked
       */
      addAll: function (urls) {
        var all = read();
        var added = 0;
        (Array.isArray(urls) ? urls : []).forEach(function (url) {
          if (typeof url !== 'string' || !url) return;
          if (all.indexOf(url) === -1) { all.push(url); added += 1; }
        });
        if (added) write();
        return added;
      },

      /* For tests only: drops the cached reads so a test can stage a second
         scenario in the same page. */
      _forget: function () { entries = null; counts = null; servings = null; batchCounts = null; }
    };
  })();

  HTF.shortlist = shortlist;

})(window.HTF);
