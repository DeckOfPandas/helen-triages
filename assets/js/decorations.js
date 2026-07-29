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
      HTF.fetchSvg(HTF.asset('/assets/img/highlighters/' + nextName() + '.svg'),
        function (svg) { slot.innerHTML = applyTexture(svg); });
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
    function inject(slot, svg) {
      slot.innerHTML = svg
        .replace(/<\?xml[^?]*\?>/g, '')
        .replace(/<!--[\s\S]*?-->/g, '')
        .replace(/(<svg [^>]*?)width="[^"]*mm"/, '$1')
        .replace(/(<svg [^>]*?)height="[^"]*mm"/, '$1')
        .replace(/preserveAspectRatio="[^"]*"/, '')
        .replace('<svg ', '<svg preserveAspectRatio="none" style="position:absolute;'
          + 'top:-4px;left:-6px;width:calc(100% + 12px);height:calc(100% + 8px);'
          + 'z-index:-1;overflow:visible;pointer-events:none;" ');
    }

    slots.forEach(function (slot) {
      var colour = slot.getAttribute('data-brush-colour');
      var file = 'background-watercolour-brush-' + colour + '-' + nextShape(colour) + '.svg';
      HTF.fetchSvg(HTF.asset('/assets/img/backgrounds-headers/' + file),
        function (svg) { inject(slot, svg); });
    });
  }

  // ---------------------------------------------------------------------------
  // Masking tape behind the logo — one of four, at random.
  // ---------------------------------------------------------------------------
  function tape() {
    var slot = document.querySelector('.tape-bg');
    if (!slot) return;

    var n = Math.floor(Math.random() * 4) + 1;
    HTF.fetchSvg(HTF.asset('/assets/img/tape/tape-food-' + n + '.svg'), function (svg) {
      slot.innerHTML = svg.replace(/<svg /, '<svg preserveAspectRatio="none" height="100%" ');
    });
  }

  // ---------------------------------------------------------------------------
  // Footer hearts
  //
  // The artwork used to be a 2,500-character path string concatenated inside
  // this file's predecessor. It is now assets/img/hearts/site-footer-hearts.svg
  // and takes its colour from `currentColor`, set on .site-footer-hearts in
  // _sass/_palette.scss — so no colour is written down here.
  // ---------------------------------------------------------------------------
  function hearts() {
    var slot = document.querySelector('.site-footer-hearts');
    if (!slot) return;

    HTF.fetchSvg(HTF.asset('/assets/img/hearts/site-footer-hearts.svg'),
      function (svg) { slot.innerHTML = svg; });
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
      HTF.fetchSvg(HTF.asset('/assets/img/doodles/' + name + '.svg'), function (svg) {
        var colour = slot.getAttribute('data-doodle-color');
        slot.innerHTML = svg.replace(/fill="black"/g, 'fill="' + colour + '"');
      });
    });
  }

  highlighters();
  brushes();
  tape();
  hearts();
  doodles();

})();
