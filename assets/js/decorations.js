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
//   .annotation-mark           hand-drawn sparkles beside a note
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
  // The tape is HEADER CHROME, so there is one set of files for the whole repo
  // (assets/img/chrome/tape/) rather than a copy per site. It used to be a copy
  // per site, and keeping the two in step was a manual chore policed by a note
  // in the handover: food's redesign shipped seven new files on 2026-08-10 and
  // cocktails sat on the old four for five days before anyone noticed, which is
  // issue #223. One directory cannot drift from itself.
  //
  // How many files there are still has to be told to this script — a directory
  // listing is not a thing a browser can ask for — and it now comes from
  // _data/chrome.yml, which is chrome config rather than site identity.
  // ---------------------------------------------------------------------------
  // BOTH INJECTED ATTRIBUTES ARE REQUIRED and neither is optional decoration.
  // The tape files carry `width="100%"` and NO height, so without `height="100%"`
  // the element keeps its intrinsic 1400x170 ratio and LETTERBOXES -- scaling to
  // fit its box entirely rather than stretching to fill it. A narrow tape then
  // draws far shorter than its box while a wide one fills it, so two tapes on
  // one page disagree with each other. That cost a round of Helen's time on
  // 2026-09-01, from a hand-copied version of this line that dropped the height.
  // It is a named constant now so there is one copy of it to get right.
  var TAPE_ATTRS = '<svg preserveAspectRatio="none" height="100%"';

  // `<svg` + any whitespace OR `>`, for the reason spelled out in brushes()
  // above: two exporters are in use and a literal '<svg ' silently no-ops on
  // the other kind, because a failed String.replace returns its input.
  var TAPE_OPEN = /<svg(?=[\s>])/;

  function tape() {
    var slot = document.querySelector('.tape-bg');
    if (!slot) return;

    var count = parseInt(slot.getAttribute('data-tape-count'), 10);
    if (!count) return;

    var n = Math.floor(Math.random() * count) + 1;
    var url = HTF.chromeAsset('/tape/tape-' + n + '.svg');
    HTF.fetchSvg(url, function (svg) {
      slot.innerHTML = svg.replace(TAPE_OPEN, TAPE_ATTRS);
    });
  }

  // ---------------------------------------------------------------------------
  // Card titles on tape — issue #469, the cocktails index.
  //
  // A SECOND FUNCTION RATHER THAN A WIDENED tape(), because the two want
  // opposite things and saying so is cheaper than a flag. The wordmark's tape is
  // ONE slot chosen at RANDOM per page load; these are ~124 slots that must be
  // STABLE, so a card wears the same shape on every visit and a reload is a
  // comparison rather than a lottery. They share the artwork, the fetch and the
  // two attributes above, which is where the duplication actually mattered.
  //
  // The count comes from the header's own slot, so there is still exactly one
  // place that knows how many tape files exist (_data/chrome.yml).
  // ---------------------------------------------------------------------------
  function cardTapes() {
    var slots = document.querySelectorAll('[data-card-tape]');
    if (!slots.length) return;

    var header = document.querySelector('.tape-bg');
    var count = header ? parseInt(header.getAttribute('data-tape-count'), 10) : 0;
    if (!count) return;

    Array.prototype.forEach.call(slots, function (slot) {
      var i = parseInt(slot.getAttribute('data-card-tape'), 10) || 1;
      var n = ((i - 1) % count) + 1;
      HTF.fetchSvg(HTF.chromeAsset('/tape/tape-' + n + '.svg'), function (svg) {
        slot.innerHTML = svg.replace(TAPE_OPEN, TAPE_ATTRS);
      });
    });
  }

  // ---------------------------------------------------------------------------
  // Centre the capitals on the band.
  //
  // Everything in CSS centres BOXES, which it does correctly and which is not
  // what the eye judges. What is left is where capitals sit inside their own
  // line box: with line-height 1 the baseline lands at half-leading plus the
  // font's ascent, that leading is negative, and the caps hang off the baseline
  // by their cap height. So it is a fact about the FACE.
  //
  // ESTIMATING IT FAILED THREE TIMES. Courier Prime ships here as woff2 only and
  // there is no font parser in the build environment; across plausible metric
  // sets the required nudge ranges from -1.5px to +2.2px and does not even have
  // a reliable sign. Canvas TextMetrics knows it exactly, so ask.
  //
  // After document.fonts.ready, because measuring before Courier Prime has
  // loaded measures the FALLBACK -- a different face, different metrics, and a
  // confidently wrong constant baked in for the life of the page.
  // ---------------------------------------------------------------------------
  function centreTapeCaps() {
    var probe = document.querySelector('.drink-card-tape-word');
    if (!probe || !window.CanvasRenderingContext2D) return;

    var cs = window.getComputedStyle(probe);
    var size = parseFloat(cs.fontSize);
    var ctx = document.createElement('canvas').getContext('2d');
    ctx.font = cs.fontStyle + ' ' + cs.fontWeight + ' ' + cs.fontSize + ' ' + cs.fontFamily;

    var m = ctx.measureText('H');
    var ascent = m.fontBoundingBoxAscent;
    var descent = m.fontBoundingBoxDescent;
    var capAscent = m.actualBoundingBoxAscent;
    // Older engines report none of these. Leaving the property unset falls back
    // to a translateY of 0, which is the box-centred version -- close, and never
    // broken.
    if (!ascent || !descent || !capAscent) return;

    var baseline = (size - (ascent + descent)) / 2 + ascent;
    var nudge = size / 2 - (baseline - capAscent / 2);
    document.documentElement.style.setProperty('--tape-text-nudge', nudge.toFixed(2) + 'px');
  }

  // ---------------------------------------------------------------------------
  // Footer decoration
  //
  // The artwork used to be a 2,500-character path string concatenated inside
  // this file's predecessor. It is now assets/img/chrome/hearts/
  // site-footer-hearts.svg, and takes its colour from `currentColor`, set on
  // .site-footer-hearts in _sass/shared/_footer.scss, so no colour is written
  // down here.
  //
  // WHICH file used to be a per-site decision, carried on a `data-footer-svg`
  // attribute fed by _data/sites.yml. It is not a decision any more: there is
  // one footer for the whole repo, so there is one graphic, named here. A site
  // that wants a different one is asking for a second footer, which is the
  // thing this shape exists to prevent.
  // ---------------------------------------------------------------------------
  function footerDecoration() {
    var slot = document.querySelector('.site-footer-hearts');
    if (!slot) return;

    var url = HTF.chromeAsset('/hearts/site-footer-hearts.svg');
    HTF.fetchSvg(url, function (svg) { slot.innerHTML = svg; });
  }

  // ---------------------------------------------------------------------------
  // Annotation marks — a small hand-drawn arrow beside each ingredient/step
  // note. Both step and ingredient marks are dealt from their own
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

    // A title hit is an arbitrary substring of whatever's currently typed —
    // it changes every keystroke, so the hash-based pool's whole point
    // (the SAME tag always gets the SAME shape everywhere it appears) has
    // no meaning here; there's no stable "tag identity" to be consistent
    // about. One fixed shape instead, chosen deliberately rather than left
    // to the hash — Helen, 2026-08-04, assumed it already had been ("I
    // expect you chose the highlighter shape deliberately") and asked for
    // one "slightly less square at the ends." It hadn't been picked at
    // all; rendered every candidate in the pool to a PNG at this exact
    // narrow width to actually look before choosing. tag-shape-6 has a
    // genuinely jagged, organic tear at one end rather than a straight or
    // notched-rectangular cut, which reads least "square" of the set —
    // tag-shape-5 was the opposite extreme, essentially a flat rectangle.
    var TITLE_HIT_SHAPE = 'tag-shape-6';

    slots.forEach(function (slot) {
      // .ingredient-pill and .title-hit added 2026-08-04 -- both got a
      // .tag-shape slot the same way badges and buttons do, but this list
      // was never updated to match, so `host` came back null and the guard
      // below silently skipped them: no shape ever fetched, no fill ever
      // shown (Helen: "There's no fill though, just the scratched,
      // capitalised font"). Same bug for both, just more obvious on
      // .title-hit sitting on the plain page background than on
      // .ingredient-pill's already-busier row.
      var host = slot.closest('.badge, .btn-tag, .btn-star, .ingredient-pill, .title-hit');
      var text = (host ? host.textContent : '').trim().toLowerCase();
      if (!text) return;

      var shape;
      if (host.classList.contains('title-hit')) {
        shape = TITLE_HIT_SHAPE;
      } else {
        shape = pickShape(text);
        // tag-shape-2's torn top-left corner reads fine at most widths but
        // draws the eye on a wide pill -- stretched further via the
        // --stretch modifier (see .tag-shape in _layout.scss) rather than
        // dropped from the pool, since it's genuinely fine at other widths
        // (Helen: fine for "duck", not fine for "make-ahead", same shape).
        // Gated on the same SHORT_TEXT_MAX cutoff used above: duck is short
        // text and was never the problem, so it must never pick this class
        // up just because it happens to land on the same shape as
        // make-ahead.
        if (shape === 'tag-shape-2' && text.length > SHORT_TEXT_MAX) {
          slot.classList.add('tag-shape--stretch');
        }
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
  cardTapes();
  footerDecoration();
  annotationMarks();
  tagShapes();

  // AFTER THE FONTS, not with the rest. Everything above fetches artwork and
  // does not care what has loaded; this one MEASURES a typeface, and measuring
  // before Courier Prime arrives measures the fallback. Guarded because
  // document.fonts is absent in older engines, where the untouched property
  // leaves the lettering centred on its box -- close, and never broken.
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(centreTapeCaps);
  } else {
    centreTapeCaps();
  }

})();
