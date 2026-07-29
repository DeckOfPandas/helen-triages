// assets.js
// =============================================================================
// BASE URL AND SVG ASSET LOADING — the single source for both.
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
   * @param {string} path - root-relative path, e.g. '/assets/img/doodles/x.svg'
   */
  HTF.asset = function (path) {
    return HTF.base + path;
  };

  // --- SVG loading -----------------------------------------------------------
  var cache = {};

  /**
   * Fetch an SVG's source text and hand it to cb. Responses are cached, so
   * repeated requests for the same URL cost one network call.
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
    fetch(url)
      .then(function (response) {
        if (!response.ok) {
          throw new Error('HTTP ' + response.status + ' ' + response.statusText);
        }
        return response.text();
      })
      .then(function (text) {
        cache[url] = text;
        cb(text);
      })
      .catch(function (error) {
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

})(window.HTF);
