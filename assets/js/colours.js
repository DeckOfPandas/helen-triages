// colours.js
// =============================================================================
// HELEN TRIAGES FOOD - JS COLOUR CONSTANTS
// =============================================================================
// These are READ FROM CSS at runtime, not duplicated here. _sass/_palette.scss
// exposes the palette as custom properties on :root; this file just picks them
// up so JS-injected SVG elements can use the same values.
//
// To change a colour: edit _sass/_palette.scss. Nothing else.
// To use a NEW colour in JS: add it to the :root block in _palette.scss, then
// add a line below. Never paste a hex value into this file.
//
// Loaded at the end of <body>, after the stylesheet in <head> has been applied,
// so the computed values are available.
// =============================================================================

window.SITE_COLOURS = (function () {
  var root = getComputedStyle(document.documentElement);

  function swatch(name, fallback) {
    var value = root.getPropertyValue('--colour-' + name).trim();
    if (!value) {
      console.warn(
        'colours.js: --colour-' + name + ' is not defined on :root. Add it to ' +
        'the :root block in _sass/_palette.scss. Falling back to ' + fallback + '.'
      );
      return fallback;
    }
    return value;
  }

  return {
    vividRose:     swatch('vivid-rose',      '#FF0061'),
    vividRoseDark: swatch('vivid-rose-dark', '#c4004b'),
    vibrantViolet: swatch('vibrant-violet',  '#7734EA'),
    pencilGrey:    swatch('pencil-grey',     '#6b6965'),
    springGreen:   swatch('spring-green',    '#00FF9F'),
    aureolin:      swatch('aureolin',        '#FAF100'),
    vividCerulean: swatch('vivid-cerulean',  '#00A7EA'),
    hotOrange:     swatch('hot-orange',      '#FF6B00')
  };
})();
