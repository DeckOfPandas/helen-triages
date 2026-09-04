// assets.js
// =============================================================================
// BASE URL, SVG ASSET LOADING, AND THE HELPERS BOTH INDEX PAGES SHARE.
// =============================================================================
// Must be the FIRST script loaded. Everything that reaches for a file under
// assets/ goes through here.
//
// WHY THIS FILE EXISTS
// The base-URL derivation used to be copy-pasted in four places: highlighter.js,
// section-rule.js, and twice inside _layouts/default.html. They had drifted —
// one handled a missing meta tag differently from the others. Since every
// decorative asset URL is built from this value, and the value changes when
// baseurl changes, four copies is four chances to be subtly wrong on the day
// you deploy.
//
// The five SVG fetches were also swallowing every error with an empty catch, so
// a wrong baseurl produced a site with no decoration at all and a completely
// clean console. That is the worst possible diagnostic position, and it is what
// fetchSvg below is really for.
//
// THE SAME ARGUMENT ADDED TWO NON-ASSET HELPERS, GitHub issue #686. escapeHtml
// and the sessionStorage index memory were each written twice, once in
// filters.js and once in cocktail-index.js, and were identical in both. This is
// the file every page loads first and the namespace every other script already
// reaches into, so it is where a thing that belongs to both indexes lives.
// Neither knows which site it is on; that is what makes them shareable at all.
// =============================================================================

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

  /**
   * Build a URL for a file under the site root.
   * @param {string} path - root-relative path, e.g. '/assets/img/favicon.svg'
   */
  HTF.asset = function (path) {
    return HTF.base + path;
  };

  // --- Site key --------------------------------------------------------------
  // This repo serves two sites from one build. A site's own PAGE artwork is not
  // shared between them — assets/img/food/ and assets/img/cocktails/ are
  // separate sets — so every decorative fetch inside a page needs to know which
  // site it is on. (The header and footer are the exception and do not: their
  // artwork lives in assets/img/chrome/ and goes through HTF.chromeAsset below.)
  //
  // Derived here for the same reason the base URL is: it is read from the page
  // by several scripts, it changes per page rather than per deployment, and a
  // second copy is a second thing to get wrong. _layouts/default.html emits
  // <meta name="site-key" content="{{ page.site_key }}">.
  //
  // Empty is legitimate — the root landing page belongs to neither site and
  // draws no site artwork — so an absent value is not warned about. A wrong
  // one announces itself through fetchSvg below.
  var siteMeta = document.querySelector('meta[name="site-key"]');
  HTF.site = siteMeta ? (siteMeta.getAttribute('content') || '').trim() : '';

  /**
   * Build a URL for a file in THIS site's artwork set.
   * siteAsset('/highlighters/highlighter-3.svg')
   *   -> '<base>/assets/img/food/highlighters/highlighter-3.svg'
   *
   * The example used to be the tape, which is no longer a per-site asset at
   * all -- see HTF.chromeAsset below.
   *
   * Returns null when the page has no site key, so callers can skip the fetch
   * rather than request a path with a hole in it.
   *
   * @param {string} path - path under the site's image directory, leading slash
   * @returns {string|null}
   */
  HTF.siteAsset = function (path) {
    if (!HTF.site) { return null; }
    return HTF.base + '/assets/img/' + HTF.site + path;
  };

  /**
   * Build a URL for a file in the SHARED CHROME's artwork set.
   * chromeAsset('/tape/tape-3.svg') -> '<base>/assets/img/chrome/tape/tape-3.svg'
   *
   * The header and the footer are one artefact for the whole repo, not two that
   * are kept looking alike — so their artwork is one set, named by no site and
   * needing no site key. It therefore never returns null: chrome renders on
   * every page, including one belonging to no site.
   *
   * This is deliberately a THIRD helper rather than a call to the generic
   * asset() above, so that test_artwork_fetches_go_through_site_asset can go on
   * banning any image path built through that one, with no exception carved out.
   * The ban is what stops a script hardcoding one site's directory; a shared
   * directory is a different claim, and it gets to say so in the function name.
   * (That test greps source text and cannot tell a comment from code, so this
   * paragraph deliberately does not spell the banned call out literally.)
   *
   * @param {string} path - path under assets/img/chrome/, leading slash
   * @returns {string}
   */
  HTF.chromeAsset = function (path) {
    return HTF.base + '/assets/img/chrome' + path;
  };

  // --- SVG loading -----------------------------------------------------------
  var cache = {};
  // URLs with a fetch already in flight, each holding the callbacks still
  // waiting on it. `cache` only gets written once a fetch RESOLVES, so
  // without this, N callers asking for the same not-yet-cached URL before
  // the first one resolves each saw a cache miss and fired their own
  // fetch() -- harmless for one or two callers, but decorations.js's
  // tagShapes() calls this once per .tag-shape slot, and a page can easily
  // have 100+ of those sharing a pool of ~9 SVG files (Helen, 2026-08-04:
  // the index page's ingredient pills took "up to 7 seconds" to fill in,
  // "in groups" -- the classic signature of a browser's per-host connection
  // cap queueing dozens of redundant requests for the same handful of
  // files). Now the first caller for a URL starts the one real fetch and
  // every other caller just joins its callback list.
  var pending = {};

  /**
   * Fetch an SVG's source text and hand it to cb. Responses are cached, so
   * repeated requests for the same URL cost one network call -- including
   * concurrent requests that land before the first one has resolved.
   *
   * A failure warns with the URL and points at the likely cause. It does not
   * throw: decoration is not worth breaking a page for, but it IS worth saying
   * out loud.
   *
   * @param {string} url - full URL, usually from HTF.asset()
   * @param {function(string)} cb - receives the SVG source text
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
   * Deal names from a shuffled pool without repeats until it is exhausted.
   * Shuffled once per page load, so a given page has variety and a reload
   * gives you something different.
   *
   * @param {string[]} names
   * @returns {function(): string}
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
   * Escape a string for insertion into HTML.
   *
   * Both indexes rebuild a title with a <mark> around the matched run, which
   * means building HTML from text that came out of a recipe or drink file —
   * Helen's own prose, not an attacker's, but "Bangers & Mash" is enough to
   * make the point, and the escaping is what keeps an ampersand an ampersand.
   *
   * FIVE CHARACTERS, NOT THE THREE THE TWO COPIES ESCAPED. `&`, `<` and `>` are
   * all a text position needs; the quotes cost nothing there (a browser renders
   * &quot; as ") and mean the same call is still right the first time somebody
   * builds an attribute value with it. `&` is replaced FIRST, or the escapes
   * would then be escaped again into &amp;lt;.
   *
   * @param {string} text
   * @returns {string}
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
  // GitHub issue #387, and #686 for this being one function rather than two.
  // Both indexes remember the order and filters they were left in, so that
  // going BACK from a recipe or a drink returns you to the list you were
  // reading rather than to a freshly shuffled one. Same store, same shape, same
  // two failure rules -- only the key and the record differ, so those are what
  // the caller passes, the way filter-state.js is parameterised by its spec.
  //
  // WHAT IS DELIBERATELY NOT HERE: the decision to restore at all. That is
  // FilterState.arrivedByGoingBack(), asked at each call site, and it stays
  // there because it is about the NAVIGATION rather than the storage -- a page
  // may well want to read this record for some other reason. Its own reasoning
  // (why performance navigation type and not bfcache) lives with it in
  // filter-state.js.
  //
  // EVERY PATH IS WRAPPED, and not only for the obvious throw. Private mode
  // throws on setItem; a browser with site data blocked can make even the
  // getter throw; and in a context with no sessionStorage at all the bare
  // reference is a ReferenceError. All three end the same way, because the
  // fallback -- a fresh list -- is what you had before the feature existed and
  // is not worth breaking a page for.
  HTF.indexMemory = {
    /**
     * Store an index's state under its own key. Silent on failure.
     * @param {string} key - the caller's own, e.g. 'htf-index-memory-v1'
     * @param {Object} state - anything JSON can carry
     */
    save: function (key, state) {
      try {
        sessionStorage.setItem(key, JSON.stringify(state));
      } catch (e) { /* nothing to be done, and nothing worth breaking for */ }
    },

    /**
     * Read back what save() stored, or null.
     *
     * NULL MEANS "CARRY ON AS A FRESH LOAD" and every failure returns it:
     * nothing stored, unparseable, storage unreachable. The caller checks the
     * SHAPE of what comes back -- this function knows nothing about the record
     * beyond it being JSON, and a record written by an older version of a page
     * is exactly as untrusted as any other stored input.
     *
     * @param {string} key
     * @returns {Object|null}
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
  // GitHub issue #546. Recipes and drinks you have marked to come back to, held
  // in this browser and nowhere else. Helen's brief, and it is a ceiling rather
  // than a first step: "one browser, one device, no sharing, no account etc is
  // truly all I want -- I actively don't want more."
  //
  // HERE, FOR THE REASON THIS FILE'S OWN HEADER GIVES. Both indexes need it,
  // both content layouts need it, and none of them knows which site it is on.
  // That is the same argument that moved escapeHtml and indexMemory in #686.
  //
  // localStorage, NOT sessionStorage, AND THAT IS THE WHOLE POINT OF THE
  // FEATURE. Everything else stored by this site is a within-visit convenience
  // -- which list you were reading, which method mode you had open -- and dies
  // with the tab, correctly. A shortlist that died with the tab would be a
  // shortlist you could not come back to, which is the only thing it is for.
  //
  // ONE STORE PER SITE. Both sites are served from one origin, so one
  // localStorage holds both; Helen asked for two lists rather than a mixed one
  // ("can be food rows or cocktail cards ... doesn't need to be a mixed list on
  // one page"), and HTF.site already says which page this is. A page with no
  // site-key (the root landing page) gets no store at all rather than a shared
  // one, which is what stops a stray key appearing under a third name.
  //
  // AN ENTRY IS A COLLECTION URL -- `/food/recipes/dal/`, `page.url` in Liquid,
  // NOT `relative_url`. The baseurl is deployment configuration: prefixing it
  // would make a stored list read as empty the day baseurl changed, and would
  // make the key emitted by a row and the key emitted by that recipe's own page
  // two different strings on the same site. filters.js's rowKey() uses the href
  // for its own record and is right to -- that record is one page's ordering,
  // written and read within a single visit. This one outlives the page.
  //
  // WHY THERE IS AN IN-MEMORY COPY, and why it is the source of truth rather
  // than a cache. indexMemory swallows a storage failure and carries on with a
  // fresh list, which is exactly right for it: nobody asked for that record, so
  // nobody misses it. Here somebody has just clicked a control. If private mode
  // or blocked site data makes setItem throw, the honest behaviour is that the
  // control still responds and the list still works for as long as the page is
  // open -- it simply will not be there tomorrow. Reading back through the
  // memory copy is what makes that true, and it costs one array.
  var shortlist = (function () {
    var KEY_PREFIX = 'htf-shortlist-';
    var GLASSES_PREFIX = 'htf-shortlist-glasses-';
    var VERSION = '-v1';
    var entries = null;   // the in-memory copy; null until first read
    var counts = null;    // url -> glasses, for the entries that are not 1

    function storageKey() {
      return HTF.site ? KEY_PREFIX + HTF.site + VERSION : '';
    }

    function glassesKey() {
      return HTF.site ? GLASSES_PREFIX + HTF.site + VERSION : '';
    }

    /* Stored state is UNTRUSTED INPUT, the same standing this codebase already
       gives the index-memory record: it can be hand-edited in devtools, left by
       an older build, or simply not an array. Anything that is not a list of
       strings falls back to an empty shortlist rather than to a half-read one,
       because a shortlist that is quietly missing three entries is worse than
       one that is visibly empty. */
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

    /* The glasses map, read and written exactly as the list above is, and with
       the same standing: untrusted input, and a failure to persist must not
       cost you the number you just typed. Only positive numbers survive the
       read -- anything else is a value nobody could have meant. */
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
            if (typeof n === 'number' && isFinite(n) && n > 1) counts[url] = Math.floor(n);
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

    return {
      /** @returns {string[]} the entries, oldest first. A copy — callers sort. */
      list: function () { return read().slice(); },

      /** @param {string} url @returns {boolean} */
      has: function (url) { return read().indexOf(url) !== -1; },

      /** @returns {number} */
      count: function () { return read().length; },

      /**
       * Flip one entry and persist. Returns the state it ENDED in, so a caller
       * can paint from the answer rather than asking again.
       * @param {string} url
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

      /** Empty it — the marks and the counts together. @returns {void} */
      clear: function () {
        entries = [];
        write();
        counts = {};
        writeGlasses();
      },

      /* --- HOW MANY OF EACH — GitHub issue #546, Helen 2026-09-04 ------------
         "Per drink quantities, zomg yes please!" -- two negronis and six
         daiquiris is a real weekend, and one number for the whole list cannot
         say it.

         A SECOND KEY, NOT A RICHER ENTRY. Making the shortlist an array of
         `{url, glasses}` would change the shape of everything already stored in
         every browser that has used the feature, and would put a planning
         number inside the record of what is marked -- two facts with different
         lifetimes in one place. This is a plain map beside it: the shortlist
         still says WHAT, this says HOW MANY.

         A MISSING ENTRY IS ONE GLASS, which is what makes the map sparse and
         self-healing: a drink dropped from the shortlist leaves a number behind
         that nothing reads, and setting a count back to 1 removes it rather
         than storing the default. Nothing has to tidy up after the shortlist. */
      glasses: function (url) {
        var n = readGlasses()[url];
        return typeof n === 'number' && n > 0 ? n : 1;
      },

      /**
       * @param {string} url
       * @param {number} n - glasses; 1 or less removes the entry
       * @returns {number} what it ended up as
       */
      setGlasses: function (url, n) {
        if (!url) return 1;
        var all = readGlasses();
        var value = Math.floor(Number(n));
        if (!isFinite(value) || value <= 1) delete all[url];
        else all[url] = value;
        writeGlasses();
        return value > 1 ? value : 1;
      },

      /* FOR TESTS ONLY, and named so nobody mistakes it for API. The module
         reads localStorage once and caches; a test that wants a second scenario
         in the same page needs to say so. */
      _forget: function () { entries = null; counts = null; }
    };
  })();

  HTF.shortlist = shortlist;

})(window.HTF);
