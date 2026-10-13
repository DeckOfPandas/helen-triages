// ground-print.js
// The page ground's print, drawn once on the device and kept (#733;
// model_instructions/LEOPARD.md). The SVG is too costly to repaint as a CSS
// background while scrolling, so it is drawn once into a canvas and kept in
// IndexedDB: only the first visit after the artwork changes pays for it.
// Site-agnostic (MANUAL §3): a stylesheet opts in by declaring
// `--ground-print` on :root. What it reads, from _sass/<site>/_leopard.scss:
//   --ground-print           the print's file under the site's own artwork
//   --ground-nap             an optional texture laid under it
//   --ground-print-ground    the colour to draw both on
//   --ground-print-version   changes when either file does
//   --ground-print-strength  how strongly to draw the print; 1 if unset
//   --ground-nap-strength    the same for the nap
// What it sets: `--ground-picture`, a url() for the body's background-image.
// Every path fails quiet into the plain ground.

(function (root) {
  'use strict';

  /** A custom property holding a quoted string, as getPropertyValue returns it. */
  function unquote(value) {
    return String(value == null ? '' : value).trim().replace(/^(["'])(.*)\1$/, '$2');
  }

  /**
   * How strongly to draw the print, from `--ground-print-strength`. 1 is the
   * artwork as drawn. Unset, unreadable or silly values are 1: a stylesheet
   * typo must not blank the ground or paint it white.
   */
  function strengthOf(value) {
    var n = parseFloat(unquote(value));
    if (!isFinite(n) || n <= 0) { return 1; }
    return Math.min(n, 4);
  }

  /**
   * The alphas to draw the print at, one per pass, to reach a strength.
   * 2.5 -> [1, 1, 0.5]. Passes, not one multiplication: a canvas can only
   * draw an image FAINTER than it is, never stronger.
   */
  function passes(strength) {
    var out = [];
    var left = Math.round(strength * 100) / 100;
    while (left > 0.001) {
      out.push(Math.min(1, Math.round(left * 100) / 100));
      left -= 1;
    }
    return out;
  }

  /**
   * The key a picture is stored under: everything that changes the picture.
   * The site, because both sites share one origin and so one database; the
   * version, so new artwork is never answered with an old picture; the
   * strength and the nap, because a stylesheet can set either inside a media
   * query.
   */
  function keyFor(site, version, strength, nap, ground) {
    /* The ground colour too: it is painted INTO the picture, so a palette
       change must not leave a returning browser with the old ground. */
    return [site, version, strength == null ? 1 : strength, nap || '-', ground || '-']
      .map(String).join('/');
  }

  var api = { unquote: unquote, keyFor: keyFor, strengthOf: strengthOf, passes: passes };
  if (typeof module !== 'undefined' && module.exports) { module.exports = api; }
  if (!root || !root.document) { return; }

  var HTF = root.HTF = root.HTF || {};
  HTF.groundPrint = api;

  var doc = root.document;
  var DB = 'htf-ground-print';
  var STORE = 'pictures';

  /* What the stylesheet is asking for, read fresh each time: null if it
     declares no print at all, which is how a site opts out. */
  function wanted() {
    var style = root.getComputedStyle(doc.documentElement);
    var print = unquote(style.getPropertyValue('--ground-print'));
    if (!print || !HTF.siteAsset) { return null; }
    var printUrl = HTF.siteAsset(print);
    if (!printUrl) { return null; }
    var nap = unquote(style.getPropertyValue('--ground-nap'));
    if (nap === 'none') { nap = ''; }
    var strength = strengthOf(style.getPropertyValue('--ground-print-strength'));
    var napStrength = strengthOf(style.getPropertyValue('--ground-nap-strength'));
    // No hex here: the palette is the only place a colour is written (MANUAL §3).
    var ground = style.getPropertyValue('--ground-print-ground').trim() || 'black';
    return {
      printUrl: printUrl,
      napUrl: nap ? HTF.siteAsset(nap) : null,
      ground: ground,
      strength: strength,
      napStrength: napStrength,
      key: keyFor(HTF.site, unquote(style.getPropertyValue('--ground-print-version')) || '0',
                  strength, nap ? nap + '@' + napStrength : '', ground)
    };
  }

  var shown = null;
  function show(blob) {
    var url = URL.createObjectURL(blob);
    doc.documentElement.style.setProperty('--ground-picture', 'url("' + url + '")');
    if (shown) { URL.revokeObjectURL(shown); }
    shown = url;
  }

  /* IndexedDB, opened once. `then` gets the database or null; null is every
     way this can fail, and the caller draws without a store. */
  function open(then) {
    var done = false;
    function settle(db) { if (!done) { done = true; then(db); } }
    try {
      var request = root.indexedDB.open(DB, 1);
      request.onupgradeneeded = function () { request.result.createObjectStore(STORE); };
      request.onsuccess = function () { settle(request.result); };
      request.onerror = function () { settle(null); };
      request.onblocked = function () { settle(null); };
    } catch (e) { settle(null); }
  }

  function recall(db, key, then) {
    if (!db) { then(null); return; }
    try {
      var request = db.transaction(STORE).objectStore(STORE).get(key);
      request.onsuccess = function () {
        var found = request.result;
        then(found && typeof found.size === 'number' && found.size > 0 ? found : null);
      };
      request.onerror = function () { then(null); };
    } catch (e) { then(null); }
  }

  /* ONE picture is kept: the store is emptied before the new one goes in, so
     a change of artwork does not leave megabytes of the old one behind. */
  function keep(db, key, blob) {
    if (!db) { return; }
    try {
      var store = db.transaction(STORE, 'readwrite').objectStore(STORE);
      store.clear();
      store.put(blob, key);
    } catch (e) { /* this page has its picture; the next one draws again */ }
  }

  /* An SVG's source text as something a canvas can draw. */
  function image(text, then) {
    var url = URL.createObjectURL(new Blob([text], { type: 'image/svg+xml' }));
    var img = new Image();
    img.onload = function () { then(img); URL.revokeObjectURL(url); };
    img.onerror = function () { URL.revokeObjectURL(url); };
    img.src = url;
  }

  /* Ground, then the nap tiled across it, then the print: one opaque picture
     at the print's own size in CSS pixels. Deliberately NOT multiplied up for
     a dense screen: three times the pixels each way is nine times the
     memory, and the softer picture is the preferred one. */
  function draw(want, printImage, napImage, then) {
    try {
      var canvas = doc.createElement('canvas');
      canvas.width = printImage.naturalWidth;
      canvas.height = printImage.naturalHeight;
      var ctx = canvas.getContext('2d');
      ctx.fillStyle = want.ground;
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      if (napImage) {
        var tile = doc.createElement('canvas');
        tile.width = napImage.naturalWidth;
        tile.height = napImage.naturalHeight;
        tile.getContext('2d').drawImage(napImage, 0, 0);
        ctx.fillStyle = ctx.createPattern(tile, 'repeat');
        passes(want.napStrength).forEach(function (alpha) {
          ctx.globalAlpha = alpha;
          ctx.fillRect(0, 0, canvas.width, canvas.height);
        });
        ctx.globalAlpha = 1;
      }
      passes(want.strength).forEach(function (alpha) {
        ctx.globalAlpha = alpha;
        ctx.drawImage(printImage, 0, 0);
      });
      ctx.globalAlpha = 1;
      canvas.toBlob(function (blob) { if (blob) { then(blob); } }, 'image/png');
    } catch (e) { /* no print, and the page works */ }
  }

  function make(db, want) {
    HTF.fetchSvg(want.printUrl, function (printText) {
      image(printText, function (printImage) {
        function finish(napImage) {
          draw(want, printImage, napImage, function (blob) {
            show(blob);
            keep(db, want.key, blob);
          });
        }
        if (!want.napUrl) { finish(null); return; }
        HTF.fetchSvg(want.napUrl, function (napText) { image(napText, finish); });
      });
    });
  }

  /**
   * Put the print the stylesheet is asking for on the ground: the kept
   * picture if there is one for exactly that request, a fresh drawing if not.
   * Run once at load, below. Also callable, for a page that changes a
   * strength on the root element and wants the result drawn by this code.
   *
   * @param {boolean} [now] - draw at once rather than waiting for `load`
   */
  api.refresh = function (now) {
    var want = wanted();
    if (!want) { return; }
    open(function (db) {
      recall(db, want.key, function (blob) {
        if (blob) { show(blob); return; }
        /* The first drawing waits for `load`: it is the one expensive thing
           here, and at parse time it would block reading and scrolling. */
        if (now || doc.readyState === 'complete') { make(db, want); }
        else { root.addEventListener('load', function () { make(db, want); }); }
      });
    });
  };

  api.refresh();

})(typeof window !== 'undefined' ? window : null);
