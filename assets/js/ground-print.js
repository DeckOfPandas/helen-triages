// ground-print.js
// =============================================================================
// THE PAGE GROUND'S PRINT, DRAWN ONCE ON THE DEVICE AND KEPT. #733.
// =============================================================================
// Cocktails' page ground is a black-on-black leopard (model_instructions/
// LEOPARD.md). It is an SVG, and for one afternoon it was simply a CSS
// background: the browser redrew ten thousand fur strokes, behind a mask, for
// every strip of page that scrolled into view, and Helen's phone and laptop
// both juddered. "The page is slow to load, even top to bottom, and scrolling
// is juddery even after lots of scrolling up and down."
//
// The usual fix is to ship a bitmap. This site ships no images, on purpose --
// Helen: "one of the very coolest things I wanted to achieve here was great
// styling with zero images." So the bitmap is made HERE instead: the SVG is
// drawn once into a canvas, the canvas becomes a picture in memory, and the
// stylesheet uses that picture as the background. Scrolling then moves a
// picture, which is what a browser is good at. She chose it over a slimmed-down
// vector by scrolling both on her phone ("it all looks like spiders"), and
// liked that it comes out a little soft on a dense screen.
//
// AND IT IS KEPT. "Can drawn once not be saved page to page...?" It is: the
// picture goes into IndexedDB, keyed by the artwork's version, so only the
// first visit after the artwork changes pays for the drawing. Every other page
// load reads it back.
//
// THIS FILE KNOWS NO SITE (MANUAL §3). A stylesheet opts in by declaring
// `--ground-print` on :root; one that declares nothing -- food -- gets nothing,
// and this returns at once. What it reads, all from _sass/<site>/_leopard.scss:
//
//   --ground-print           the print's file under the site's own artwork
//   --ground-nap             an optional texture laid under it
//   --ground-print-ground    the colour to draw both on
//   --ground-print-version   changes when either file does
//
// and what it sets: `--ground-picture`, a url() the same partial uses as the
// body's background-image. Until it is set the page shows the plain ground,
// which is also everything a browser with scripts off will ever show.
//
// EVERY PATH FAILS QUIET, INTO THAT PLAIN GROUND. No IndexedDB (private mode,
// blocked site data): it draws on each load instead. No canvas, no blob, a
// tile that will not load: no print. A texture is not worth breaking a page
// for.
// =============================================================================

(function (root) {
  'use strict';

  /** A custom property holding a quoted string, as getPropertyValue returns it. */
  function unquote(value) {
    return String(value == null ? '' : value).trim().replace(/^(["'])(.*)\1$/, '$2');
  }

  /**
   * The key a picture is stored under. The site is in it because both sites
   * share one origin and so one database; the version is in it so new artwork
   * is never answered with an old picture.
   */
  function keyFor(site, version) {
    return String(site) + '/' + String(version);
  }

  var api = { unquote: unquote, keyFor: keyFor };
  if (typeof module !== 'undefined' && module.exports) { module.exports = api; }
  if (!root || !root.document) { return; }

  var HTF = root.HTF = root.HTF || {};
  HTF.groundPrint = api;

  var doc = root.document;
  var style = root.getComputedStyle(doc.documentElement);
  var print = unquote(style.getPropertyValue('--ground-print'));
  if (!print || !HTF.siteAsset) { return; }
  var printUrl = HTF.siteAsset(print);
  if (!printUrl) { return; }
  var nap = unquote(style.getPropertyValue('--ground-nap'));
  var napUrl = nap ? HTF.siteAsset(nap) : null;
  // No hex here: the palette is the only place a colour is written (MANUAL §3).
  var ground = style.getPropertyValue('--ground-print-ground').trim() || 'black';
  var key = keyFor(HTF.site, unquote(style.getPropertyValue('--ground-print-version')) || '0');

  var DB = 'htf-ground-print';
  var STORE = 'pictures';

  function show(blob) {
    doc.documentElement.style.setProperty(
      '--ground-picture', 'url("' + URL.createObjectURL(blob) + '")');
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

  function recall(db, then) {
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
  function keep(db, blob) {
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
     a dense screen -- three times the pixels each way is nine times the
     memory, and Helen preferred the softer one on her phone anyway. */
  function draw(printImage, napImage, then) {
    try {
      var canvas = doc.createElement('canvas');
      canvas.width = printImage.naturalWidth;
      canvas.height = printImage.naturalHeight;
      var ctx = canvas.getContext('2d');
      ctx.fillStyle = ground;
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      if (napImage) {
        var tile = doc.createElement('canvas');
        tile.width = napImage.naturalWidth;
        tile.height = napImage.naturalHeight;
        tile.getContext('2d').drawImage(napImage, 0, 0);
        ctx.fillStyle = ctx.createPattern(tile, 'repeat');
        ctx.fillRect(0, 0, canvas.width, canvas.height);
      }
      ctx.drawImage(printImage, 0, 0);
      canvas.toBlob(function (blob) { if (blob) { then(blob); } }, 'image/png');
    } catch (e) { /* no print, and the page works */ }
  }

  function make(db) {
    HTF.fetchSvg(printUrl, function (printText) {
      image(printText, function (printImage) {
        function finish(napImage) {
          draw(printImage, napImage, function (blob) {
            show(blob);
            keep(db, blob);
          });
        }
        if (!napUrl) { finish(null); return; }
        HTF.fetchSvg(napUrl, function (napText) { image(napText, finish); });
      });
    });
  }

  open(function (db) {
    recall(db, function (blob) {
      if (blob) { show(blob); return; }
      /* THE FIRST DRAWING WAITS FOR THE PAGE. It is the one expensive thing
         here -- over a second -- and done at parse time it would be a second
         in which the page could not be read or scrolled. After `load` it is a
         second in which the ground is plain, which nobody is waiting on. */
      if (doc.readyState === 'complete') { make(db); }
      else { root.addEventListener('load', function () { make(db); }); }
    });
  });

})(typeof window !== 'undefined' ? window : null);
