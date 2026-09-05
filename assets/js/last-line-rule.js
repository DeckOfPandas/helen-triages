// last-line-rule.js
// =============================================================================
// THE DOUBLE RULE SITS UNDER THE LAST LINE ONLY — not once per line.
// =============================================================================
// Design audit critical #7, decided 2026-09-04 from a
// candidates page built on the real quiche recipe. Helen, having switched
// between the treatments on the page itself: "Last line only please, 10000%."
//
// THE PROBLEM. `overlapping-rule-double` (shared/_rule.scss) paints the green
// bar and the violet bar as BACKGROUNDS on an inline box, with
// `box-decoration-break: clone`. That is what makes the mark measure the
// LETTERING rather than the box — a border would draw on the box, which for a
// `text-wrap: balance`d title is as wide as its longest line, so it would
// overhang every shorter one (see the note above .recipe-title-text in
// food/_recipe-header.scss). The cost of `clone` is that every line fragment
// gets its own full copy of the background: a title that wraps to three lines
// wears three stacked double rules, and the mark stops reading as one mark.
//
// WHY THIS IS NOT A CSS FIX, checked before writing a line of JS.
// `box-decoration-break: slice` is the obvious candidate and it does not work.
// Slice treats the fragments as slices of ONE long box, so each fragment keeps
// the FULL height of that box and the background is cut horizontally, not
// vertically — bottom-anchored bars land under the first line and nowhere
// else, and every fragment still paints. There is no CSS selector for "the
// last line of a wrapped inline box" either: ::first-line has no counterpart.
// Marking the last line is a measurement, and measurement is what a script is
// for.
//
// WHAT IT DOES. For each target it splits the text into words (whitespace
// tokens kept, so the rebuilt text is byte-identical), wraps each in a
// throwaway span, reads each span's top with getBoundingClientRect, and finds
// the first word whose top matches the LAST word's — a 2px tolerance, because
// sub-pixel layout puts words on one line at tops that differ in the third
// decimal place. Then it rebuilds the element as
//
//     <span class="rule-lines">…every earlier line…</span>
//     <span class="rule-last">…the last line…</span>
//
// and puts `rule-split` on the element itself. The Sass side is the other half:
// the element keeps its own double rule as the NO-JS FALLBACK, `.rule-split`
// switches that off, and `.rule-last` wears the mark instead — so a one-line
// title looks exactly as it always did, and a wrapped one wears the mark once,
// under its last line, exactly as a one-line title wears it.
//
// A one-line title gets no `.rule-lines` at all rather than an empty one.
//
// IT RUNS THREE TIMES, and each is load-bearing. Once at load; again on
// `document.fonts.ready`, because the split is measured in the fallback face
// until the real one arrives and the line breaks move when it does; and on
// resize, debounced, because a narrower column rewraps the title. Every run
// rebuilds from the ORIGINAL text stashed on the first run — re-reading
// textContent would work too, but only until a rebuild is interrupted, and
// keeping the source of truth in one place means the element can never drift
// away from the title Jekyll rendered.
//
// TEXT ONLY, BY CONSTRUCTION. Rebuilding an element from `textContent` throws
// away any child elements inside it, so anything with element children is
// skipped rather than quietly flattened. Nothing on the recipe or reference
// pages has any today — the index's `.title-hit` <mark> lives on
// `.recipe-title` in the list, which is not a target — but a future decoration
// slot inside a heading would be, and losing it would be silent.
//
// AN ELEMENT MAY OPT OUT with `data-last-line-rule="skip"`, and exactly one
// does: the cooking-methods reference page's protein heading, whose text is
// rewritten by cook-timer.js every time you pick a different protein. That
// rewrite would blow away the spans this file put there and leave the element
// carrying `rule-split` with nothing to paint — a heading with no mark at all.
// The knowledge that the text is somebody else's lives in the markup, where a
// reader of that page will find it, rather than as a page-specific selector in
// here.
//
// Nothing in this file knows which site it is on, per the shared-JS rule and
// the same shape as print-link.js and universe.js: it queries a class list and
// does nothing on a page that has none. Cocktails has no consumer of
// `overlapping-rule-double` that wraps, so on a drink page it finds nothing and
// returns.
// =============================================================================

(function () {
  // The food elements that carry `overlapping-rule-double` AND can wrap: the
  // recipe/magic-bag title, and the section headings on recipe, about and
  // reference pages (the modifier classes --about-faq and --reference are
  // second classes on .section-heading-text, so the base selector reaches all
  // three keys). NOT the index's `.category-label-text`, which wears the same
  // mixin on a one-word filter label that never wraps.
  var TARGETS = '.recipe-title-text, .section-heading-text';

  var els = Array.prototype.filter.call(
    document.querySelectorAll(TARGETS),
    function (el) {
      if (el.getAttribute('data-last-line-rule') === 'skip') return false;
      // childElementCount, not innerHTML sniffing: an element holding only
      // text is the only thing this can safely rebuild.
      return el.childElementCount === 0;
    }
  );
  if (!els.length) return;

  // The text as Jekyll rendered it, stashed once. Every later run rebuilds
  // from this rather than from whatever the previous run left behind.
  var originals = els.map(function (el) { return el.textContent; });

  function mark(el, text) {
    // Whitespace kept as its own tokens, so joining the two halves back
    // together reproduces the original string exactly — including the space
    // that has to stay on the END of the earlier lines rather than the start
    // of the last one, or the last line would begin with a space and its rule
    // would start before its first letter.
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
    // on the new line. Stepping past it puts the space at the end of the
    // earlier lines where it belongs.
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

  var timer;
  window.addEventListener('resize', function () {
    clearTimeout(timer);
    timer = setTimeout(markAll, 120);
  });

  // The real face changes where the lines break, so the split measured against
  // the fallback is measured again once the font has actually loaded.
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(markAll);
  }
})();
