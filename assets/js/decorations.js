// decorations.js
// =============================================================================
// HAND-DRAWN SVG DECORATION — every slot on the site, in one place.
// =============================================================================
// Replaces js/highlighter.js and roughly a hundred lines of inline JavaScript
// that had accumulated in _layouts/default.html. All five behaviours were the
// same shape — find slots, pick an asset, fetch it, inject it — expressed five
// different ways, in two different files, one of which was a template.
//
//   .highlighter-slot          scratchy highlighter behind headings and amounts
//   .watercolour-brush-slot    brush wash behind filter labels
//   .tape-bg                   masking tape behind the site logo
//   .site-footer-hearts        footer hearts
//   [data-index-doodle]        doodles beside index filter labels
//
// Base URL, fetching, caching and error reporting all live in js/assets.js.
// Nothing here knows a URL prefix and nothing here swallows an error.
//
// Requires: assets.js (loaded first).
// =============================================================================

(function () {

  var HTF = window.HTF;

  // ---------------------------------------------------------------------------
  // Highlighters
  //
  // Shapes 1 and 13 are excluded from the pool but retained in the library.
  // Pool is shapes 2–12 plus their flips: 22 options, shuffled once per page
  // load so a page has variety and a reload gives you something different.
  // ---------------------------------------------------------------------------
  function highlighters() {
    var slots = document.querySelectorAll('.highlighter-slot');
    if (!slots.length) return;

    var pool = [];
    for (var n = 2; n <= 12; n++) {
      pool.push('highlighter-' + n);
      pool.push('highlighter-' + n + '-flip');
    }
    var nextName = HTF.makeShuffledPicker(pool);

    // Texture is randomised once per page so the whole page agrees with itself.
    var variants = [
      { baseFrequency: '0.015 0.05', alphaRow: '0.4 0.4 0.4 0 0.25' },
      { baseFrequency: '0.02 0.06',  alphaRow: '0.3 0.3 0.3 0 0.45' }
    ];
    var tex  = variants[Math.floor(Math.random() * variants.length)];
    var seed = Math.floor(Math.random() * 1000);

    function applyTexture(svg) {
      return svg
        .replace(/baseFrequency="[^"]*"/, 'baseFrequency="' + tex.baseFrequency + '"')
        .replace(/seed="\d+"/, 'seed="' + seed + '"')
        .replace(/0\.4 0\.4 0\.4 0 0\.25|0\.3 0\.3 0\.3 0 0\.45/, tex.alphaRow);
    }

    slots.forEach(function (slot) {
      var url = HTF.siteAsset('/highlighters/' + nextName() + '.svg');
      if (url) HTF.fetchSvg(url, function (svg) { slot.innerHTML = applyTexture(svg); });
    });
  }

  // ---------------------------------------------------------------------------
  // Watercolour brush washes
  //
  // Ten shapes per colour, shuffled independently for each colour so two
  // sections in the same colour do not land on the same shape.
  // ---------------------------------------------------------------------------
  function brushes() {
    var slots = document.querySelectorAll('.watercolour-brush-slot');
    if (!slots.length) return;

    var shapes = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
    var pickers = {};
    function nextShape(colour) {
      if (!pickers[colour]) pickers[colour] = HTF.makeShuffledPicker(shapes);
      return pickers[colour]();
    }

    // The source files are drawn at mm dimensions with their own aspect ratio.
    // Strip both, then stretch slightly past the element on every side so the
    // wash reads as a hand-made mark rather than a rectangle.
    //
    // MATCH `<svg` FOLLOWED BY ANY WHITESPACE, NOT THE LITERAL `"<svg "`.
    // Inkscape writes each attribute on its own line, so these files open with
    // `<svg\n   width="14.111145mm"`. Every replace below used to require a
    // SPACE after `<svg`, so on all 100 brush files not one of them matched:
    // the mm dimensions survived, no absolute positioning was added, and the
    // wash rendered as a 14mm × 4mm blob sitting inline to the LEFT of the
    // label instead of stretched behind it. Silently — a failed String.replace
    // returns the original string rather than throwing.
    //
    // Every other asset directory is space-style, which is why only the brush
    // washes were affected and why it survived so long. Do not assume the
    // formatting of a file you did not export.
    function inject(slot, svg) {
      slot.innerHTML = svg
        .replace(/<\?xml[^?]*\?>/g, '')
        .replace(/<!--[\s\S]*?-->/g, '')
        .replace(/(<svg\s[^>]*?)\s*width="[^"]*mm"/, '$1')
        .replace(/(<svg\s[^>]*?)\s*height="[^"]*mm"/, '$1')
        .replace(/preserveAspectRatio="[^"]*"/, '')
        // Insert straight after `<svg`, leaving the following whitespace alone,
        // so the tag stays well-formed whichever style the file uses.
        .replace(/<svg(?=[\s>])/, '<svg preserveAspectRatio="none" style="position:absolute;'
          + 'top:-4px;left:-6px;width:calc(100% + 12px);height:calc(100% + 8px);'
          + 'z-index:-1;overflow:visible;pointer-events:none;"');
    }

    slots.forEach(function (slot) {
      var colour = slot.getAttribute('data-brush-colour');
      var file = 'background-watercolour-brush-' + colour + '-' + nextShape(colour) + '.svg';
      var url = HTF.siteAsset('/backgrounds-headers/' + file);
      if (url) HTF.fetchSvg(url, function (svg) { inject(slot, svg); });
    });
  }

  // ---------------------------------------------------------------------------
  // Masking tape behind the wordmark — one of N, at random.
  //
  // Which directory and how many files both come from _data/sites.yml, via
  // attributes on the slot. A site with no `tape:` key gets no .tape-bg element
  // at all, so this returns at the guard below and attempts no fetch — an
  // absent decoration must be silent, not a 404 with a console warning.
  // ---------------------------------------------------------------------------
  function tape() {
    var slot = document.querySelector('.tape-bg');
    if (!slot) return;

    var dir   = slot.getAttribute('data-tape-dir');
    var count = parseInt(slot.getAttribute('data-tape-count'), 10);
    if (!dir || !count) return;

    var n = Math.floor(Math.random() * count) + 1;
    var url = HTF.siteAsset('/' + dir + '/tape-' + n + '.svg');
    if (!url) return;
    HTF.fetchSvg(url, function (svg) {
      // `<svg` + any whitespace, for the reason spelled out in brushes() above.
      // Today's tape files are space-style so the old literal worked, but
      // cocktails' artwork does not exist yet and may well come out of Inkscape.
      slot.innerHTML = svg.replace(/<svg(?=[\s>])/, '<svg preserveAspectRatio="none" height="100%"');
    });
  }

  // ---------------------------------------------------------------------------
  // Footer decoration
  //
  // The artwork used to be a 2,500-character path string concatenated inside
  // this file's predecessor. It is now a file under assets/img/<site>/ — for
  // food, hearts/site-footer-hearts.svg — and takes its colour from
  // `currentColor`, set on .site-footer-hearts in the site's palette, so no
  // colour is written down here.
  //
  // WHICH file is a per-site decision, so it comes from _data/sites.yml
  // (`footer_svg`) via a data attribute rather than being named here. A site
  // with no footer_svg gets no element, and nothing is fetched.
  // ---------------------------------------------------------------------------
  function footerDecoration() {
    var slot = document.querySelector('.site-footer-hearts');
    if (!slot) return;

    var file = slot.getAttribute('data-footer-svg');
    if (!file) return;

    var url = HTF.siteAsset('/' + file);
    if (url) HTF.fetchSvg(url, function (svg) { slot.innerHTML = svg; });
  }

  // ---------------------------------------------------------------------------
  // Index filter-label doodles
  //
  // Recoloured by string replacement, which is load-bearing: it only works
  // because the source files consistently use fill="black". A `currentColor`
  // fill in the sources plus a CSS `color` would remove the mechanism — worth
  // doing next time these assets are touched.
  // ---------------------------------------------------------------------------
  function doodles() {
    var slots = document.querySelectorAll('[data-index-doodle]');
    if (!slots.length) return;

    slots.forEach(function (slot) {
      var name = slot.getAttribute('data-index-doodle');
      var url = HTF.siteAsset('/doodles/' + name + '.svg');
      if (!url) return;
      HTF.fetchSvg(url, function (svg) {
        var colour = slot.getAttribute('data-doodle-color');
        slot.innerHTML = svg.replace(/fill="black"/g, 'fill="' + colour + '"');
      });
    });
  }

  highlighters();
  brushes();
  tape();
  footerDecoration();
  doodles();

})();
