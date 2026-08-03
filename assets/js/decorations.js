// decorations.js
// =============================================================================
// HAND-DRAWN SVG DECORATION — every slot on the site, in one place.
// =============================================================================
// Replaces js/highlighter.js and roughly a hundred lines of inline JavaScript
// that had accumulated in _layouts/default.html. All five behaviours were the
// same shape — find slots, pick an asset, fetch it, inject it — expressed five
// different ways, in two different files, one of which was a template.
//
//   .highlighter-slot          scratchy highlighter behind ingredient amounts
//   .tape-bg                   masking tape behind the site logo
//   .site-footer-hearts        footer hearts
//   .annotation-mark           hand-drawn sparkles beside a tip/note
//
// Two more lived here until 2026-08-01. `.watercolour-brush-slot` drew the
// brush washes, which the blocky rule replaced on both pages; `[data-index-doodle]`
// drew doodles beside the index filter labels and had been dead far longer —
// no template has emitted that attribute for as long as git remembers.
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
  // Annotation marks — a small hand-drawn arrow beside each ingredient/step
  // tip or note. One asset, no shuffling: unlike the highlighters, these are
  // meant to read as a consistent, recognisable "here's an aside" signal
  // rather than page-to-page variety.
  // ---------------------------------------------------------------------------
  function annotationMarks() {
    var slots = document.querySelectorAll('.annotation-mark');
    if (!slots.length) return;

    var url = HTF.siteAsset('/doodles/arrow-annotation.svg');
    if (!url) return;
    slots.forEach(function (slot) {
      HTF.fetchSvg(url, function (svg) { slot.innerHTML = svg; });
    });
  }

  highlighters();
  tape();
  footerDecoration();
  annotationMarks();

})();
