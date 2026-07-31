// section-rule.js
// All SVG assets loaded from this site's set under assets/img/<site>/, resolved
// by HTF.siteAsset. No paths inlined here.
// To change a colour, update colours.js only.

(function () {

  var C = window.SITE_COLOURS;
  var COLOURS = {
    sectionRule:    { fill: C.pencilGrey, opacity: 0.4  },
    groupHeading:   { fill: C.pencilGrey, opacity: 0.55 },
    titleBox:       { fill: C.vividRose },
    sectionHeading: { fill: C.vividRose },
  };

  // ── Helpers ───────────────────────────────────────────────────────────────
  // Base URL, fetching, caching, shuffling and error reporting all live in
  // js/assets.js.
  function makePicker(names, pathPrefix) {
    var nextName = window.HTF.makeShuffledPicker(names);
    return function(cb) {
      var url = window.HTF.siteAsset(pathPrefix + nextName() + '.svg');
      if (url) window.HTF.fetchSvg(url, cb);
    };
  }

  function recolour(svg, map) {
    for (var k in map) svg = svg.split(k).join(map[k]);
    return svg;
  }

  function insertAfter(el, cls, html) {
    if (!el) return;
    var w = document.createElement('div');
    w.className = cls; w.innerHTML = html;
    el.parentNode.insertBefore(w, el.nextSibling);
  }

  function insertBefore(el, cls, html) {
    if (!el) return;
    var w = document.createElement('div');
    w.className = cls; w.innerHTML = html;
    el.parentNode.insertBefore(w, el);
  }

  // ── Section rules ─────────────────────────────────────────────────────────
  // SVGs in assets/img/<site>/section-rules/ use SECTION_COLOUR + SECTION_OPACITY placeholders.
  var sectionRuleNames = [
    'section-rule-line-1',      'section-rule-line-1-flip',
    'section-rule-line-2',      'section-rule-line-2-flip',
    'section-rule-line-3',      'section-rule-line-3-flip',
    'section-rule-line-4',      'section-rule-line-4-flip',
  ];
  var pickSection = makePicker(sectionRuleNames, '/section-rules/');

  function sectionRule(cb) {
    pickSection(function(svg) {
      cb(recolour(svg, {
        'SECTION_COLOUR':  COLOURS.sectionRule.fill,
        'SECTION_OPACITY': String(COLOURS.sectionRule.opacity),
      }));
    });
  }

  var badgesEl = document.querySelector('.recipe-badges');
  var ingredientsEndEl = document.querySelector('.ingredients-end');
  var notesEl = document.querySelector('#recipe-section-notes');
  var bodyEl  = document.querySelector('.recipe-body-content');

  if (badgesEl)        sectionRule(function(h) { insertAfter(badgesEl, 'section-rule', h); });
  if (ingredientsEndEl) sectionRule(function(h) { insertAfter(ingredientsEndEl, 'section-rule', h); });
  if (notesEl)         sectionRule(function(h) { insertBefore(notesEl, 'section-rule', h); });
  if (bodyEl && bodyEl.children.length > 0)
                       sectionRule(function(h) { insertBefore(bodyEl, 'section-rule', h); });

  // ── Title box ─────────────────────────────────────────────────────────────
  // Title underline removed from recipe page.
  // SVG files retained in assets/img/<site>/title-box/ for future use.


  // ── Group heading underlines ──────────────────────────────────────────────
  var underlineNames = [
    'underline-multiple-1',      'underline-multiple-1-flip',
    'underline-multiple-6',      'underline-multiple-6-flip',
    'underline-multiple-7',      'underline-multiple-7-flip',
    'underline-multiple-8',      'underline-multiple-8-flip',
  ];
  var pickHeading = makePicker(underlineNames, '/underlines/');

  document.querySelectorAll('[data-group-heading]').forEach(function(h3) {
    var textEl = h3.querySelector('.group-heading-text');
    var slot   = h3.querySelector('.group-heading-underline');
    if (!textEl || !slot) return;
    var w = textEl.getBoundingClientRect().width;
    pickHeading(function(svg) {
      slot.innerHTML = recolour(svg, { 'HEADING_COLOUR': COLOURS.groupHeading.fill });
      var svgEl = slot.querySelector('svg');
      if (svgEl) {
        svgEl.style.width   = w + 'px';
        svgEl.style.height  = '10px';
        svgEl.style.opacity = String(COLOURS.groupHeading.opacity);
      }
    });
  });

  // ── Meta label underlines ─────────────────────────────────────────────────
  var pickMetaLabel = makePicker(underlineNames, '/underlines/');

  document.querySelectorAll('[data-meta-label]').forEach(function(label) {
    var slot = label.nextElementSibling;
    if (!slot || !slot.classList.contains('meta-label-underline')) return;
    var range = document.createRange();
    range.selectNodeContents(label);
    var rects = range.getClientRects();
    var w = 0;
    for (var i = 0; i < rects.length; i++) w += rects[i].width;
    if (!w) w = label.getBoundingClientRect().width;
    pickMetaLabel(function(svg) {
      slot.innerHTML = recolour(svg, { 'HEADING_COLOUR': C.vibrantViolet });
      var svgEl = slot.querySelector('svg');
      if (svgEl) { svgEl.style.width = w + 'px'; svgEl.style.height = '7px'; }
    });
  });

  // ── Doodle injection helper ───────────────────────────────────────────────
  // All doodle SVGs use fill="black" as a neutral placeholder.
  // Colour is always passed explicitly — never hardcoded in the SVG file.
  function injectDoodle(svgText, colour) {
    var vb = (svgText.match(/viewBox="([^"]+)"/) || ['','0 0 100 100'])[1];
    var inner = svgText
      .replace(/<svg[^>]*>/, '')
      .replace(/<\/svg>\s*$/, '')
      .replace(/fill="black"/g, 'fill="' + colour + '"');
    return { vb: vb, inner: inner };
  }

  // ── Ingredient bullets ────────────────────────────────────────────────────
  // siteAsset returns null on a page belonging to no site, so the URL is
  // checked before fetching rather than requesting a path with a hole in it.
  var bulletUrl = window.HTF.siteAsset('/doodles/doodle-asterisk.svg');
  if (bulletUrl) window.HTF.fetchSvg(bulletUrl, function(svgText) {
    var d = injectDoodle(svgText, C.vibrantViolet);
    var steps = [-157.5,-135,-112.5,-90,-67.5,-45,-22.5,0,22.5,45,67.5,90,112.5,135,157.5];
    for (var j = steps.length - 1; j > 0; j--) {
      var k = Math.floor(Math.random() * (j + 1));
      var tmp = steps[j]; steps[j] = steps[k]; steps[k] = tmp;
    }
    var bullets = document.querySelectorAll('.ingredient-bullet');
    bullets.forEach(function(bullet, idx) {
      bullet.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="' + d.vb + '" '
        + 'style="display:block;width:100%;height:100%;transform:rotate(' + steps[idx % steps.length] + 'deg);">'
        + d.inner + '</svg>';
    });
  });

  // ── Section heading doodles ───────────────────────────────────────────────
  var DOODLE_MAP = {
    ingredients: { file: 'doodle-sparkles.svg',                w: 29, h: 32, colour: C.vividRose },
    method:      { file: 'doodle-sparkly-asterisk.svg',        w: 22, h: 32, colour: C.vividRose },
    notes:       { file: 'doodle-three-exclamation-marks.svg', w: 18, h: 32, colour: C.vividRose },
  };

  document.querySelectorAll('[data-section-heading]').forEach(function(h2) {
    var section = h2.getAttribute('data-section-heading');
    var def = DOODLE_MAP[section];
    if (!def) return;
    var left  = h2.querySelector('.section-heading-sparkle--left');
    var right = h2.querySelector('.section-heading-sparkle--right');
    if (!left && !right) return;
    var doodleUrl = window.HTF.siteAsset('/doodles/' + def.file);
    if (!doodleUrl) return;
    window.HTF.fetchSvg(doodleUrl, function(svg) {
      var d = injectDoodle(svg, def.colour);
      var out = '<svg viewBox="' + d.vb + '" xmlns="http://www.w3.org/2000/svg" '
              + 'preserveAspectRatio="xMidYMid meet" aria-hidden="true" '
              + 'style="display:block;width:' + def.w + 'px;height:' + def.h + 'px;">'
              + d.inner + '</svg>';
      if (left)  left.innerHTML  = out;
      if (right) right.innerHTML = out;
    });
  });

})();
