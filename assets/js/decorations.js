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
//   .tag-shape                 torn-tape shape behind a tag pill/filter button
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
  // tip or note. Both step and ingredient marks are dealt from their own
  // shuffled pool (same mechanism as highlighters() above — no repeats until
  // every arrow in the pool has been used on the page), just with different
  // artwork: ingredients get four horizontal arrows, steps get three curved
  // ones. A single repeated glyph reads as more "system," not less; a
  // handful of slightly different hand-drawn arrows reads as one hand,
  // drawn fresh each time, which is closer to what a marginal note in a
  // paper recipe actually looks like.
  // ---------------------------------------------------------------------------
  function annotationMarks() {
    var slots = document.querySelectorAll('.annotation-mark');
    if (!slots.length) return;

    var nextStepArrow = HTF.makeShuffledPicker([
      '/doodles/arrow-annotation-1.svg',
      '/doodles/arrow-annotation-2.svg',
      '/doodles/arrow-annotation-3.svg'
    ]);
    var nextIngredientArrow = HTF.makeShuffledPicker([
      '/doodles/arrow-horizontal-1.svg',
      '/doodles/arrow-horizontal-2.svg',
      '/doodles/arrow-horizontal-3.svg',
      '/doodles/arrow-horizontal-4.svg'
    ]);

    slots.forEach(function (slot) {
      var isIngredient = !!slot.closest('.ingredient-annotation');
      var url = HTF.siteAsset(isIngredient ? nextIngredientArrow() : nextStepArrow());
      if (!url) return;
      HTF.fetchSvg(url, function (svg) { slot.innerHTML = svg; });
    });
  }

  // ---------------------------------------------------------------------------
  // Tag shapes — the torn-tape background behind a recipe-row pill or a
  // STAR/MOOD/PRACTICALITIES filter button (index page only; a no-op
  // elsewhere since .tag-shape only appears in that markup).
  //
  // Assigned by a deterministic hash of the tag's own text, not randomly and
  // not by position — the same tag gets the same shape everywhere it
  // appears (a filter button and a recipe-row pill for "greens" match),
  // which is the whole point (Helen: "this will give some visual stability
  // between the filter section and the recipe list section"). Random or
  // per-position picks would both break that.
  //
  // POOL, not all 18: with both the original and flip of every shape in
  // play, a row mixed torn-left-clean-right shapes with their mirror image
  // at random, which read as "drunken" (Helen, 2026-08-03) rather than
  // varied — most of these were evidently drawn with the same consistent
  // hand motion, so the originals mostly already agree with each other on
  // which end is torn vs clean, and flipping half of them at random is what
  // broke that agreement, not the individual shapes themselves. Kept every
  // original; shape 4 also keeps its flip, since torn evenly at both ends
  // it reads as genuinely symmetric rather than pointing either way.
  //
  // Shape 8 dropped entirely 2026-08-03 — Helen's read on "root veg" and
  // "shellfish" (both landed on it): too diagonal next to the rest of the
  // set, and with nine other options there was no need to keep it. Shape 9
  // is a wedge with a diagonal that spans the shape's FULL width, unlike
  // the others, where the torn/ragged detail is concentrated at the ends
  // and the middle stretches safely — stretched to a very narrow pill, that
  // diagonal reads as a much steeper, near-vertical cut than it does at
  // full width, so it's excluded for short tag text specifically rather
  // than dropped outright; it still gets used on longer tags where it
  // stretches fine.
  //
  // None of the unwired shapes (1, 2, 3, 5, 6, 7, 8, 9-flip) are deleted
  // from doodles/ — still real files, just not in this pool, in case any of
  // these calls needs revisiting.
  function tagShapes() {
    var slots = document.querySelectorAll('.tag-shape');
    if (!slots.length) return;

    var SHORT_TEXT_MAX = 6;
    var POOL = [
      'tag-shape-1', 'tag-shape-2', 'tag-shape-3',
      'tag-shape-4', 'tag-shape-4-flip',
      'tag-shape-5', 'tag-shape-6', 'tag-shape-7', 'tag-shape-9'
    ];

    function pickShape(text) {
      var pool = POOL;
      if (text.length <= SHORT_TEXT_MAX) {
        pool = pool.filter(function (name) { return name.indexOf('tag-shape-9') !== 0; });
      }
      var hash = 0;
      for (var i = 0; i < text.length; i++) {
        hash = (hash * 31 + text.charCodeAt(i)) | 0;
      }
      return pool[Math.abs(hash) % pool.length];
    }

    slots.forEach(function (slot) {
      var host = slot.closest('.badge, .btn-tag, .btn-star');
      var text = (host ? host.textContent : '').trim().toLowerCase();
      if (!text) return;
      var shape = pickShape(text);
      // tag-shape-2's torn top-left corner reads fine at most widths but
      // draws the eye on a wide pill -- stretched further via the
      // --stretch modifier (see .tag-shape in _layout.scss) rather than
      // dropped from the pool, since it's genuinely fine at other widths
      // (Helen: fine for "duck", not fine for "make-ahead", same shape).
      // Gated on the same SHORT_TEXT_MAX cutoff used above: duck is short
      // text and was never the problem, so it must never pick this class up
      // just because it happens to land on the same shape as make-ahead.
      if (shape === 'tag-shape-2' && text.length > SHORT_TEXT_MAX) {
        slot.classList.add('tag-shape--stretch');
      }
      var url = HTF.siteAsset('/doodles/' + shape + '.svg');
      if (!url) return;
      HTF.fetchSvg(url, function (svg) { slot.innerHTML = svg; });
    });
  }

  // Exposed so filters.js can re-run it after creating a .tag-shape slot of
  // its own — the active ingredient-search tag is built by JS, after this
  // file's own one-time pass over the page has already happened, so nothing
  // would ever fill that slot in without a way to ask for another pass.
  // Safe to call repeatedly: fetchSvg caches by URL (assets.js), so re-scanning
  // slots that already have their shape costs no extra network activity.
  HTF.tagShapes = tagShapes;

  highlighters();
  tape();
  footerDecoration();
  annotationMarks();
  tagShapes();

})();
