// decorations.js
// Hand-drawn SVG decoration: every slot on the site, in one place.
//
//   .highlighter-slot          scratchy highlighter behind ingredient amounts
//   .tape-bg                   masking tape behind the site logo
//   [data-card-tape]           masking tape behind a cocktail card's title
//   .site-footer-hearts        footer hearts
//   .annotation-mark           hand-drawn arrows beside a note
//   .tag-shape                 torn-tape shape behind a tag pill/filter button
//
// Base URL, fetching, caching and error reporting all live in assets.js,
// which must be loaded first.

(function () {

  var HTF = window.HTF;

  // --- Highlighters ----------------------------------------------------------
  // Shapes 1 and 13 are excluded from the pool. Shapes 2–12 plus their flips,
  // shuffled once per page load.
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

  // --- Masking tape behind the wordmark --------------------------------------
  // Header chrome: one set of files for the whole repo (assets/img/chrome/tape/,
  // #223). How many there are comes from `tape_count` in _data/chrome.yml, via
  // the slot's data-tape-count.
  //
  // Both injected attributes are required. The tape files carry width="100%"
  // and no height, so without height="100%" the element keeps its intrinsic
  // ratio and letterboxes: a narrow tape draws shorter than its box.
  var TAPE_ATTRS = '<svg preserveAspectRatio="none" height="100%"';

  // `<svg` followed by whitespace OR `>`: two exporters are in use, and a
  // literal '<svg ' silently no-ops on the other kind, because a failed
  // String.replace returns its input.
  var TAPE_OPEN = /<svg(?=[\s>])/;

  // Null is the decision, not a placeholder: a fresh pick on every load
  // (#779). An integer here is all that "fixed" would need.
  var FIXED_TAPE_INDEX = null;

  function tape() {
    var slot = document.querySelector('.tape-bg');
    if (!slot) return;

    var count = parseInt(slot.getAttribute('data-tape-count'), 10);
    if (!count) return;

    var n = FIXED_TAPE_INDEX || (Math.floor(Math.random() * count) + 1);
    var url = HTF.chromeAsset('/tape/tape-' + n + '.svg');
    HTF.fetchSvg(url, function (svg) {
      slot.innerHTML = svg.replace(TAPE_OPEN, TAPE_ATTRS);
    });
  }

  // --- Card titles on tape (#469) --------------------------------------------
  // Random per slot per load, like the wordmark (#779). The value of
  // `data-card-tape` is not read here; universe.js selects the slots by the
  // attribute. The count comes from the header's own slot, so one place knows
  // how many tape files exist.
  function cardTapes() {
    var slots = document.querySelectorAll('[data-card-tape]');
    if (!slots.length) return;

    var header = document.querySelector('.tape-bg');
    var count = header ? parseInt(header.getAttribute('data-tape-count'), 10) : 0;
    if (!count) return;

    Array.prototype.forEach.call(slots, function (slot) {
      var n = Math.floor(Math.random() * count) + 1;
      HTF.fetchSvg(HTF.chromeAsset('/tape/tape-' + n + '.svg'), function (svg) {
        slot.innerHTML = svg.replace(TAPE_OPEN, TAPE_ATTRS);
      });
    });
  }

  // --- Centre the capitals on the band ---------------------------------------
  // CSS centres the line BOX; where the capitals sit inside it is a fact about
  // the face, and Canvas TextMetrics is the only thing here that knows it.
  // Must run after document.fonts.ready: measured earlier, it measures the
  // fallback face and bakes in a wrong nudge for the life of the page.
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
    // Older engines report none of these. Unset, the property falls back to a
    // translateY of 0: box-centred, close, and never broken.
    if (!ascent || !descent || !capAscent) return;

    var baseline = (size - (ascent + descent)) / 2 + ascent;
    var nudge = size / 2 - (baseline - capAscent / 2);
    document.documentElement.style.setProperty('--tape-text-nudge', nudge.toFixed(2) + 'px');
  }

  // --- Footer decoration -----------------------------------------------------
  // One footer for the whole repo, so one graphic, named here. It takes its
  // colour from `currentColor`, set on .site-footer-hearts in the stylesheet.
  function footerDecoration() {
    var slot = document.querySelector('.site-footer-hearts');
    if (!slot) return;

    var url = HTF.chromeAsset('/hearts/site-footer-hearts.svg');
    HTF.fetchSvg(url, function (svg) { slot.innerHTML = svg; });
  }

  // --- Annotation marks ------------------------------------------------------
  // A small hand-drawn arrow beside each ingredient or step note, each kind
  // dealt from its own shuffled pool: no repeats until the pool is used up.
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

  // --- Tag shapes ------------------------------------------------------------
  // The torn-tape background behind a pill or a filter button (#1219).
  // Assigned by a hash of the tag's own text, never randomly or by position:
  // a tag must wear the same shape in the filter section and in the list. A
  // host's `data-tag-shape` names its shape outright, for a chip Helen has
  // picked one for by looking (#1369); it must name a member of POOL.
  function tagShapes() {
    var slots = document.querySelectorAll('.tag-shape');
    if (!slots.length) return;

    // No mirror images, because a row mixing both disagrees about which end
    // is torn; shape 4 keeps its flip (torn at both ends). Shape 8 is out as
    // too diagonal, and shape 9 is for short text only: its diagonal turns
    // near-vertical on a narrow pill.
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

    // A title hit is whatever substring is currently typed, so it has no
    // stable identity to hash. One fixed shape, chosen for its jagged end.
    var TITLE_HIT_SHAPE = 'tag-shape-6';

    slots.forEach(function (slot) {
      // Every element that can hold a .tag-shape slot must be in this list. A
      // host missing from it makes `host` null and the slot is silently
      // skipped: no shape fetched, no fill shown.
      var host = slot.closest('.badge, .btn-tag, .btn-star, .ingredient-pill, .title-hit, .btn-chaos, .btn-mood, .btn-pool');
      var text = (host ? host.textContent : '').trim().toLowerCase();
      if (!text) return;

      // This runs again whenever a script adds a slot, so a slot is restyled
      // from scratch each time rather than keeping an earlier pass's class.
      slot.classList.remove('tag-shape--stretch');

      var shape;
      if (host.classList.contains('title-hit')) {
        shape = TITLE_HIT_SHAPE;
      } else {
        shape = host.getAttribute('data-tag-shape') || pickShape(text);
        // tag-shape-2's torn top-left corner draws the eye on a wide pill, so
        // long text on it is marked for extra stretch. Short text must never
        // get the class.
        if (shape === 'tag-shape-2' && text.length > SHORT_TEXT_MAX) {
          slot.classList.add('tag-shape--stretch');
        }
      }

      // chromeAsset, not siteAsset: both sites' chips wear these (#1219), and
      // tests/test_site_config.py pins this exact call.
      var url = HTF.chromeAsset('/tag-shapes/' + shape + '.svg');
      HTF.fetchSvg(url, function (svg) { slot.innerHTML = svg; });
    });
  }

  // Exposed so a script that builds a .tag-shape slot after this file's one
  // pass (filters.js, for the active ingredient-search tag) can ask for
  // another. Safe to call repeatedly: fetchSvg caches by URL.
  HTF.tagShapes = tagShapes;

  highlighters();
  tape();
  cardTapes();
  footerDecoration();
  annotationMarks();
  tagShapes();

  // After the fonts, not with the rest: this one measures a typeface. Guarded
  // because document.fonts is absent in older engines.
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(centreTapeCaps);
  } else {
    centreTapeCaps();
  }

})();
