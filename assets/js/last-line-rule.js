// last-line-rule.js
// The double rule sits under the LAST line of a wrapped heading only.
// `overlapping-rule-double` (_sass/shared/_rule.scss) paints its bars as
// backgrounds on an inline box with `box-decoration-break: clone`, so every
// line fragment gets its own copy. No CSS selects "the last line of a wrapped
// inline box", so this measures: it finds the first word on the last line and
// rebuilds the element as `<span class="rule-lines">` (every earlier line)
// then `<span class="rule-last">` (the last), with `rule-split` on the
// element. The Sass is the other half: the element's own rule is the no-JS
// fallback, `.rule-split` switches it off and `.rule-last` wears the mark.
//
// Text only: rebuilding from `textContent` would flatten child elements, so an
// element that has any is skipped. An element whose text another script
// rewrites opts out with `data-last-line-rule="skip"`, or the rewrite would
// leave it carrying `rule-split` with nothing to paint.

(function () {
  // The elements that carry `overlapping-rule-double` AND can wrap. Each
  // selector must match the stylesheet's own: food titles and section
  // headings (the --modifier classes are second classes, so the base selector
  // reaches them), cocktails' reference pages (_sass/cocktails/_reference.scss,
  // #920), and the drink page's one sentence-length heading
  // (_sass/cocktails/_cocktail.scss).
  // Not the index's `.category-label-text`: a one-word label never wraps.
  var TARGETS = '.recipe-title-text, .section-heading-text, .ref-section-heading span, ' +
    '.cocktail-section-heading--related > span';

  var els = Array.prototype.filter.call(
    document.querySelectorAll(TARGETS),
    function (el) {
      if (el.getAttribute('data-last-line-rule') === 'skip') return false;
      // An element holding only text is the only thing this can safely
      // rebuild.
      return el.childElementCount === 0;
    }
  );
  if (!els.length) return;

  // The text as Jekyll rendered it, stashed once. Every later run rebuilds
  // from this, never from what the previous run left behind.
  var originals = els.map(function (el) { return el.textContent; });

  function mark(el, text) {
    // Whitespace kept as its own tokens, so joining the two halves reproduces
    // the original string exactly.
    var words = text.split(/(\s+)/).filter(function (w) { return w.length; });
    if (!words.length) return;

    el.innerHTML = '';
    var spans = words.map(function (w) {
      var span = document.createElement('span');
      span.textContent = w;
      el.appendChild(span);
      return span;
    });

    var tops = spans.map(function (span) {
      return span.getBoundingClientRect().top;
    });

    // Walk back from the end until a word sits on a different line; the word
    // after it is the first of the last line. 2px of tolerance, not equality:
    // words on one line differ by fractions of a pixel.
    var lastTop = tops[tops.length - 1];
    var start = 0;
    for (var i = tops.length - 1; i >= 0; i--) {
      if (Math.abs(tops[i] - lastTop) > 2) {
        start = i + 1;
        break;
      }
    }
    // A line break may fall ON a whitespace token, which measures as sitting
    // on the new line. Step past it, or the last line would begin with a space
    // and its rule would start before its first letter.
    while (start < words.length && !words[start].trim()) start++;

    var head = words.slice(0, start).join('');
    var tail = words.slice(start).join('');

    el.innerHTML = '';
    if (head) {
      var lines = document.createElement('span');
      lines.className = 'rule-lines';
      lines.textContent = head;
      el.appendChild(lines);
    }
    var last = document.createElement('span');
    last.className = 'rule-last';
    last.textContent = tail;
    el.appendChild(last);

    el.classList.add('rule-split');
  }

  function markAll() {
    for (var i = 0; i < els.length; i++) mark(els[i], originals[i]);
  }

  markAll();

  // A narrower column rewraps the title.
  var timer;
  window.addEventListener('resize', function () {
    clearTimeout(timer);
    timer = setTimeout(markAll, 120);
  });

  // The real face changes where the lines break, so the split measured against
  // the fallback is measured again once the font has loaded.
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(markAll);
  }
})();
