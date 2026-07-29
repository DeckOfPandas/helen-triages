// highlighter.js
// Injects shuffled hand-drawn highlighter backgrounds into .highlighter-slot elements.
// SVGs fetched from assets/img/highlighters/. No paths inlined here.
// Shape 1 and shape 13 excluded from pool (retained in library).
// Pool: shapes 2–12 + their flips = 22 options; shuffled per load, no repeats per page.

(function () {

  // ── Pool: 22 shapes (11 originals + 11 flips, shapes 2–12) ───────────────
  var POOL = [];
  for (var n = 2; n <= 12; n++) {
    POOL.push('highlighter-' + n);
    POOL.push('highlighter-' + n + '-flip');
  }

  // ── Shuffle once per page load ────────────────────────────────────────────
  var nextName = window.HTF.makeShuffledPicker(POOL);

  // ── Texture randomisation ─────────────────────────────────────────────────
  var textureVariants = [
    { baseFrequency: '0.015 0.05', alphaRow: '0.4 0.4 0.4 0 0.25' },
    { baseFrequency: '0.02 0.06',  alphaRow: '0.3 0.3 0.3 0 0.45' },
  ];
  var tex  = textureVariants[Math.floor(Math.random() * textureVariants.length)];
  var seed = Math.floor(Math.random() * 1000);

  function applyTexture(svg) {
    return svg
      .replace(/baseFrequency="[^"]*"/, 'baseFrequency="' + tex.baseFrequency + '"')
      .replace(/seed="\d+"/, 'seed="' + seed + '"')
      .replace(/0\.4 0\.4 0\.4 0 0\.25|0\.3 0\.3 0\.3 0 0\.45/, tex.alphaRow);
  }

  // ── Inject into all slots ─────────────────────────────────────────────────
  // Fetching, caching and error reporting all live in js/assets.js.
  document.querySelectorAll('.highlighter-slot').forEach(function(slot) {
    var url = window.HTF.asset('/assets/img/highlighters/' + nextName() + '.svg');
    window.HTF.fetchSvg(url, function(svg) {
      slot.innerHTML = applyTexture(svg);
    });
  });

})();
