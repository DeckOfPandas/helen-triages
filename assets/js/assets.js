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

})(window.HTF);
