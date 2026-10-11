// card-line-budget.js
// A drink card is a fixed height, so its name, ingredient line and chip rows
// share one budget (#776). A wrapped name is handled in the stylesheet
// (`.drink-card-name--wrap ~` in _sass/cocktails/_cards.scss). This file does
// what CSS cannot: count the lines the ingredient paragraph actually rendered,
// and order the chips to fit their rows (#1308).
//
// - The class goes on the CARD, because the chips it governs are in another
//   subtree; the stylesheet decides what it means.
// - Runs after card-name-fit.js (script order in _layouts/default.html): the
//   name decides how much room the ingredients get.
// - Must re-run when the visible set changes, hence HTF.cardLineBudget: the
//   index paginates with `card.hidden`, and a hidden element measures zero
//   height. cocktail-index.js calls it on every filter pass.
(function () {
  'use strict';

  var THREE_LINES = 'drink-card--ingredients-3';

  // Set, with `--ship-w`, on a card whose chips on the ship's row reach past
  // the ship's left edge; the stylesheet pads the chips clear of the ship on
  // that card only. A chip must never be cut off mid-word by the ship.
  var CLEAR_SHIP = 'drink-card--chips-clear-ship';

  // Rounded, not floored: the height is fractional and the line height is not
  // a whole pixel, so three lines can measure as 2.98.
  function lineCount(el) {
    var style = window.getComputedStyle(el);
    var lh = parseFloat(style.lineHeight);
    // `normal` computes to a keyword in some engines. Fall back to the font
    // size times the 1.5 the stylesheet sets, rather than guessing 1.
    if (!isFinite(lh) || lh <= 0) lh = parseFloat(style.fontSize) * 1.5;
    if (!isFinite(lh) || lh <= 0) return 0;
    return Math.round(el.getBoundingClientRect().height / lh);
  }

  // A card showing its tagline is left as it was (#1292): its ingredient line
  // is `display: none`, so it would measure zero lines and lose a class it had
  // earned.
  var TAGLINE_SHOWN = 'is-tagline-shown';

  function apply(card) {
    var line = card.querySelector('.drink-card-ingredients');
    if (!line) return;
    if (card.classList.contains(TAGLINE_SHOWN)) return;
    // Reset first, so a re-run at a new width can take the class OFF again.
    card.classList.remove(THREE_LINES);
    if (lineCount(line) >= 3) card.classList.add(THREE_LINES);
    clearShip(card);
  }

  // --- The chips are packed, not just wrapped (#1308) ------------------------
  // Of every order the chips could take, keep the ones that (1) show the most
  // chips inside the row cap, (2) in the fewest rows, (3) with the row on the
  // ship's line stopping short of the ship, and of those (4) fill the first
  // row as full as it will go, then the second, and so on. Ties are settled
  // alphabetically: the search walks the chips in alphabetical order and keeps
  // the FIRST best answer.
  //
  // Rows are laid out greedily, as `flex-wrap` will draw them, with one
  // exception (#1331): a row may be ended before a chip that would have
  // fitted, where the ship's row needs it. `breaks` names the chip that ends
  // such a row and the margin that closes the row off after it.
  //
  // A chip matching a filter stays at the front (#757): `pinned` leading chips
  // keep their place and only the rest are arranged.
  //
  //   adv[i]      the width chip i takes with another chip after it (its dot)
  //   lastAdv[i]  its width as the very last chip, which draws no dot
  //   pinned      how many leading chips keep their place
  //   o.W         the width of a row
  //   o.lastW     how far the row on the ship's line may run
  //   o.cap       how many rows the stylesheet shows
  //
  // Returns { order, visible, breaks } -- indices into `adv`, and for each row
  // ended early a [chip, margin] pair -- or null when no order keeps the
  // ship's row short enough.
  var FITS = 0.02;   // layout is in 1/64px; this is rounding, not slack

  function packChips(adv, lastAdv, pinned, o) {
    var n = adv.length;
    var ALL = Math.pow(2, n) - 1;
    var memo = {};

    function better(a, b) {
      if (!b) return true;
      var len = Math.max(a.length, b.length);
      for (var i = 0; i < len; i++) {
        var x = i < a.length ? a[i] : -Infinity;
        var y = i < b.length ? b[i] : -Infinity;
        if (x !== y) return x > y;
      }
      return false;
    }

    /* The score of the best finish from here: [chips still to be shown,
       -(rows in the end)], then the final width of this row and of each row
       after it. Bigger is better, read left to right. */
    function solve(mask, placed, r, fill) {
      var key = mask + ':' + r + ':' + Math.round(fill * 10);
      if (key in memo) return memo[key];
      var best = null;
      if (mask === ALL) {
        if (fill <= o.lastW + FITS) {
          best = { s: [0, -(r + 1), fill], next: -1, done: true };
        }
        memo[key] = best;
        return best;
      }
      for (var i = 0; i < n; i++) {
        var bit = Math.pow(2, i);
        if (Math.floor(mask / bit) % 2) continue;
        if (placed < pinned && i !== placed) continue;
        var w = (mask + bit === ALL) ? lastAdv[i] : adv[i];
        var fits = fill === 0 || fill + w <= o.W + FITS;
        // Twice round for a chip that fits: once joining the row, and once
        // with the row ended before it (#1331). A chip that does not fit only
        // ever starts the next row.
        for (var forced = 0; forced < (fits && fill > 0 ? 2 : 1); forced++) {
          var stays = fits && !forced;
          var cand;
          if (!stays && r + 1 >= o.cap) {
            // This chip starts a row past the cap: it and everything after it
            // are clipped, and row `r` is the one on the ship's line.
            if (fill > o.lastW + FITS) continue;
            cand = { s: [0, -(r + 1), fill], next: i, done: true, forced: !!forced };
          } else {
            var sub = solve(mask + bit, placed + 1, stays ? r : r + 1, stays ? fill + w : w);
            if (!sub) continue;
            var s = [sub.s[0] + 1, sub.s[1]];
            if (!stays) s.push(fill);
            for (var k = 2; k < sub.s.length; k++) s.push(sub.s[k]);
            cand = { s: s, next: i, done: false, forced: !!forced };
          }
          if (better(cand.s, best && best.s)) best = cand;
        }
      }
      memo[key] = best;
      return best;
    }

    var node = solve(0, 0, 0, 0);
    if (!node) return null;
    var order = [];
    var breaks = [];
    var mask = 0, r = 0, fill = 0;
    var visible = node.s[0];
    /* A row ended early is closed off after its last chip: all the room left
       but half a pixel, so that chip still fits and nothing else can. */
    function endRowHere() {
      if (order.length) breaks.push([order[order.length - 1], Math.max(0, o.W - fill - 0.5)]);
    }
    while (node && !node.done) {
      var i = node.next;
      var bit = Math.pow(2, i);
      var w = (mask + bit === ALL) ? lastAdv[i] : adv[i];
      var stays = !node.forced && (fill === 0 || fill + w <= o.W + FITS);
      if (node.forced) endRowHere();
      order.push(i);
      mask += bit;
      if (stays) { fill += w; } else { r += 1; fill = w; }
      node = solve(mask, order.length, r, fill);
    }
    // The clipped chips: the one that broke the row first, so nothing smaller
    // slips back onto the ship's line, then the rest as they were. If that
    // chip would have fitted, the row is closed off ahead of it instead.
    if (node && node.next >= 0) {
      if (node.forced) endRowHere();
      order.push(node.next);
    }
    for (var j = 0; j < n; j++) {
      if (order.indexOf(j) < 0) order.push(j);
    }
    return { order: order, visible: visible, breaks: breaks };
  }

  function px(v) {
    var n = parseFloat(v);
    return isFinite(n) ? n : 0;
  }

  var planned = typeof WeakMap === 'function' ? new WeakMap() : null;

  /* Measures the chips, asks packChips for an order, and puts the DOM in it.
     Returns true when the order it chose needs the chips padded clear of the
     ship, false when it does not, and null when it could not measure -- no
     layout to read, or a card it has no business rearranging -- in which case
     the caller's own measurement decides. */
  function arrangeChips(card, moods, ship) {
    if (!moods.appendChild || !moods.getBoundingClientRect || !card.style) return null;
    var els = Array.prototype.slice.call(moods.querySelectorAll('.drink-card-mood'));
    if (els.length < 2 || els.length > 12) return null;
    var m = moods.getBoundingClientRect();
    if (!m.width) return null;   // hidden card

    // Reset before measuring: a margin left by the last pass to end a row
    // early (#1331) is not part of the chip.
    els.forEach(function (el) { if (el.style) el.style.marginRight = ''; });

    // Alphabetical is where it starts, read off the labels, not the DOM, which
    // an earlier pass of this function has rearranged. Lowercased because
    // `I want to faff` is capitalised.
    function label(el) {
      return String((el.dataset && el.dataset.mood) || el.textContent || '').toLowerCase();
    }
    function isMatch(el) { return el.classList.contains('is-match'); }
    var base = els.slice().sort(function (a, b) {
      if (isMatch(a) !== isMatch(b)) return isMatch(a) ? -1 : 1;
      var x = label(a), y = label(b);
      return x < y ? -1 : (x > y ? 1 : 0);
    });
    var pinned = base.filter(isMatch).length;

    // What a chip costs depends on whether another follows it: every chip but
    // the last carries the separator -- a dot inside its box, or on a matched
    // chip a margin the dot hangs in -- and both are the same 0.9rem.
    var rootSize = px(window.getComputedStyle(document.documentElement).fontSize) || 16;
    var sep = 0.9 * rootSize;
    var lastEl = els[els.length - 1];
    var dotSeen = false;
    var widths = base.map(function (el) {
      var w = el.getBoundingClientRect().width;
      var mr = px(window.getComputedStyle(el).marginRight);
      return { el: el, w: w, mr: mr, last: el === lastEl };
    });
    // The plain dot's real width, off any unmatched chip that is drawing one:
    // the glyph is the font's, so 0.9rem is close and this is exact.
    widths.forEach(function (c) {
      if (!c.last && !isMatch(c.el) && !dotSeen) {
        var after = window.getComputedStyle(c.el, '::after');
        var d = after ? px(after.width) + px(after.marginLeft) + px(after.marginRight) : 0;
        if (d > 0) { sep = d; dotSeen = true; }
      }
    });
    var adv = [], lastAdv = [];
    widths.forEach(function (c) {
      var matched = isMatch(c.el);
      var own = matched ? 0.9 * rootSize : sep;
      if (c.last) { lastAdv.push(c.w); adv.push(c.w + own); }
      else if (matched) { lastAdv.push(c.w); adv.push(c.w + c.mr); }
      else { lastAdv.push(c.w - own); adv.push(c.w); }
    });

    var s = ship ? ship.getBoundingClientRect() : null;
    var hasShip = !!(s && s.width);
    var W = m.width;
    var lastW = hasShip ? s.left - m.left : W;
    var foot = card.querySelector('.drink-card-foot');
    var gutter = foot ? px(window.getComputedStyle(foot).columnGap) : 0;
    var paddedW = hasShip ? W - s.width - gutter : W;
    var cs = window.getComputedStyle(moods);
    var rowGap = px(cs.rowGap);
    var chipH = els[0].getBoundingClientRect().height;
    var cap = chipH ? Math.round((px(cs.maxHeight) + rowGap) / (chipH + rowGap)) : 0;
    if (!cap || cap < 1) return null;

    var sig = [pinned, W.toFixed(1), lastW.toFixed(1), paddedW.toFixed(1), cap,
      base.map(label).join('|'), adv.map(function (x) { return x.toFixed(1); }).join('|')].join('/');
    var plan = planned && planned.get(moods);
    if (!plan || plan.sig !== sig) {
      var open = packChips(adv, lastAdv, pinned, { W: W, lastW: lastW, cap: cap });
      plan = { sig: sig, order: open && open.order, breaks: open ? open.breaks : [], padded: false };
      if (hasShip && (!open || open.visible < base.length)) {
        // Nothing keeps the ship's row short, or something is still clipped:
        // see what the padded width shows, and take it only if it shows more.
        var shut = packChips(adv, lastAdv, pinned,
          { W: paddedW, lastW: Infinity, cap: cap });
        if (shut && (!open || shut.visible > open.visible)) {
          plan.order = shut.order;
          plan.breaks = shut.breaks;
          plan.padded = true;
        }
      }
      if (planned) planned.set(moods, plan);
    }
    if (!plan.order) return null;
    reorderChips(moods, els, plan.order.map(function (i) { return base[i]; }));
    // A matched chip already has the separator's 0.9rem as its right margin
    // (the stylesheet hangs its dot there), and that was counted in its width.
    plan.breaks.forEach(function (b) {
      var el = base[b[0]];
      if (!el.style) return;
      el.style.marginRight = ((isMatch(el) ? 0.9 * rootSize : 0) + b[1]) + 'px';
    });
    return plan.padded;
  }

  /* Moved only when the order differs: most cards are already in the order
     this wants. */
  function reorderChips(moods, now, wanted) {
    var same = true;
    for (var i = 0; i < wanted.length; i++) {
      if (now[i] !== wanted[i]) { same = false; break; }
    }
    if (same) return false;
    var frag = document.createDocumentFragment();
    wanted.forEach(function (chip) { frag.appendChild(chip); });
    moods.appendChild(frag);
    return true;
  }

  /* Measured with the class OFF, so a re-run at a new width can take it away
     again. The collision is a chip whose box crosses the ship's left edge AND
     sits on the ship's row; chips on rows above are not counted. arrangeChips
     predicts a layout and usually avoids the ship; this reads the layout the
     browser drew, and stays the judge. */
  function clearShip(card) {
    var ship = card.querySelector('.drink-card-ship');
    var moods = card.querySelector('.drink-card-moods');
    card.classList.remove(CLEAR_SHIP);
    if (card.style) card.style.removeProperty('--ship-w');
    if (!moods) return;
    var padded = arrangeChips(card, moods, ship);
    if (!ship) return;
    var s = ship.getBoundingClientRect();
    if (!s.width) return;   // hidden card, or no verdict drawn
    if (padded) {
      card.style.setProperty('--ship-w', s.width + 'px');
      card.classList.add(CLEAR_SHIP);
      return;
    }
    var chips = moods.querySelectorAll('.drink-card-mood');
    for (var i = 0; i < chips.length; i++) {
      var c = chips[i].getBoundingClientRect();
      var sameRow = c.bottom > s.top && c.top < s.bottom;
      if (sameRow && c.right > s.left) {
        if (card.style) card.style.setProperty('--ship-w', s.width + 'px');
        card.classList.add(CLEAR_SHIP);
        return;
      }
    }
  }

  function run() {
    var cards = document.querySelectorAll('.drink-card');
    for (var i = 0; i < cards.length; i++) apply(cards[i]);
  }

  window.HTF = window.HTF || {};
  window.HTF.cardLineBudget = run;
  // The search has no DOM in it, so tests/js/card-line-budget.test.js asks it
  // directly.
  window.HTF.packChips = packChips;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
  // The wait must stay longer than card-name-fit.js's own resize debounce
  // (#1308): a wrapped name takes a row from the chips, so this pass has to
  // read the cards after their names have been refitted.
  var resizeTimer;
  window.addEventListener('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(run, 160);
  });

  // And again once the web font arrives: the fallback face is narrower, so
  // rows that measured clean at DOMContentLoaded can grow into the ship.
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(run);
  }
})();
