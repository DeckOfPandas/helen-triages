// card-line-budget.js
// =============================================================================
// A CARD IS A FIXED HEIGHT, SO ITS THREE STACKS SHARE ONE BUDGET.
// =============================================================================
// GitHub issue #776, Helen: "if cocktail card ingredients have three lines, only
// allow the chips two lines", and "if the cocktail name has two lines, only
// allow ingredients and chips two lines each".
//
// `$card-height` is 12.9rem and does not move -- the grid depends on every card
// being the same height. Three things inside it can grow: the name (one line or
// two, decided by card-name-fit.js), the ingredient line (clamped at three) and
// the chip rows (capped at three). Each cap was chosen on its own and they can
// all be spent at once, which is the overflow this closes.
//
// THE NAME HALF NEEDS NO SCRIPT and is done in the stylesheet. card-name-fit.js
// already marks a wrapped name with `.drink-card-name--wrap`, and the name, the
// ingredient line and the foot are siblings, so `~` reaches both from it. See
// `_sass/cocktails/_cards.scss`.
//
// THE INGREDIENT HALF DOES, because CSS cannot ask how many lines a clamped
// element actually rendered -- only how many it is allowed. `-webkit-line-clamp:
// 3` is a ceiling, and most cards do not reach it: the median drink has five
// ingredients and fits two lines. A rule keyed on the clamp would punish every
// card for what the tiki drinks do.
//
// SO IT MEASURES, the same way card-name-fit.js does, and for
// the same stated reason: the browser already knows. Height divided by line
// height, rounded, is the line count; three or more sets the class.
//
// ROUNDED, NOT FLOORED. `getBoundingClientRect().height` is fractional and
// `line-height: 1.5` at `font-size: 0.82rem` is not a whole pixel, so three
// lines can measure as 2.98 or 3.02 depending on zoom and font metrics.
// Flooring turns the first into two lines and silently drops the rule on a card
// that visibly has three.
//
// THE CLASS GOES ON THE CARD, not the paragraph, because what it governs lives
// in a different subtree -- the chips are inside `.drink-card-foot`. The
// stylesheet keeps every decision about what it MEANS; this file measures and
// has no opinion about chips.
//
// IT RUNS AFTER card-name-fit.js, AND IS NOW THE LAST PASS IN THE CHAIN.
// The name decides how much room the ingredients get, and the ingredients
// decide how much the chips get, so running before the name pass is not a crash
// -- it is a budget computed against a name that had not been fitted yet.
// `_layouts/default.html` fixes the order; see its script tags.
//
// A THIRD PASS USED TO FOLLOW THIS ONE. chip-rows.js measured where the chip
// rows actually broke, so the stylesheet could suppress a leading separator dot
// on a chip that began a row (#698). #846 moved the dot to a trailing `::after`
// on every chip but the last, so nothing depends on where a row breaks and the
// file was deleted.
//
// AND IT MUST RE-RUN WHEN THE VISIBLE SET CHANGES, which is why `run` hangs off
// HTF. The index paginates by setting `card.hidden`, not by removing cards, and
// A HIDDEN ELEMENT MEASURES ZERO HEIGHT -- so the load-time pass can only ever
// classify page one. cocktail-index.js calls this on every filter pass.
// =============================================================================
(function () {
  'use strict';

  var THREE_LINES = 'drink-card--ingredients-3';

  // THE SHIP AND THE LAST CHIP ROW -- 2026-09-10. #760 took the ship out of
  // flow so no chip row would pay for it, and masked it over the chips so a
  // chip reaching it reads as cut off rather than overprinted. Helen, seeing
  // it live: cut off mid-word is wrong ("sugar crav", "no juici"). CSS cannot
  // pad only the row that collides, and padding every row is the cost #760
  // refused, so this measures: if any chip on the ship's row reaches past the
  // ship's left edge, the card gets this class and `--ship-w`, and the
  // stylesheet pads the chips clear of the ship ON THAT CARD ONLY. A chip that
  // then falls to a fourth row is hidden whole by the row cap, which is the
  // lesser thing to lose.
  var CLEAR_SHIP = 'drink-card--chips-clear-ship';

  function lineCount(el) {
    var style = window.getComputedStyle(el);
    var lh = parseFloat(style.lineHeight);
    // `normal` computes to a keyword in some engines. Fall back to the font
    // size times the 1.5 the stylesheet sets, rather than guessing 1.
    if (!isFinite(lh) || lh <= 0) lh = parseFloat(style.fontSize) * 1.5;
    if (!isFinite(lh) || lh <= 0) return 0;
    return Math.round(el.getBoundingClientRect().height / lh);
  }

  // A CARD SHOWING ITS TAGLINE IS LEFT AS IT WAS -- #1292. Its ingredient line
  // is `display: none` while the tagline has the card (card-tagline.js, where
  // there is no hover), so it would measure zero lines and lose a class it had
  // earned; the chips would then get a third row back the moment the card
  // flipped. Whatever the last honest measurement said still stands.
  var TAGLINE_SHOWN = 'is-tagline-shown';

  function apply(card) {
    var line = card.querySelector('.drink-card-ingredients');
    if (!line) return;
    if (card.classList.contains(TAGLINE_SHOWN)) return;
    // Reset first, so a re-run at a new width can take the class OFF again --
    // the bug card-name-fit.js's step 1 exists to prevent.
    card.classList.remove(THREE_LINES);
    if (lineCount(line) >= 3) card.classList.add(THREE_LINES);
    clearShip(card);
  }

  // ===========================================================================
  // THE CHIPS ARE PACKED, NOT JUST WRAPPED -- #1308.
  // ===========================================================================
  // Helen, with a screenshot of the index: "it feels like there's lots of space
  // on the right-hand side of the tag block", and the title says how to spend
  // it: "allowing tags to wrap if we tweak the order rather than requiring them
  // to be alphabetical".
  //
  // ALPHABETICAL (#710) WRAPS WHEREVER THE ALPHABET HAPPENS TO BREAK, and on a
  // card that costs three separate things. A row ends short and the next chip
  // starts a row it did not need. The last row runs into the ship, so the whole
  // block is padded clear of it (the 2026-09-10 rule below) and EVERY row loses
  // the ship's width -- which is the empty right-hand side in her screenshot.
  // And the rows that spill past the cap are clipped, chips and all.
  //
  // SO THE ORDER IS CHOSEN FOR THE CARD'S WIDTH. Of every order the chips could
  // take, this keeps the ones that (1) show the most chips inside the row cap,
  // (2) in the fewest rows, (3) with the row on the ship's line stopping short
  // of the ship, so no padding is needed -- and of those takes the one closest
  // to alphabetical. A card whose alphabetical order already does all three is
  // not touched, which is most of them.
  //
  // IT IS A SEARCH, NOT A HEURISTIC, because a card has at most ten chips and
  // usually four: every state is (which chips are placed, which row, how full),
  // remembered once. It walks the chips in alphabetical order and keeps the
  // FIRST best answer, which is what "closest to alphabetical" means here.
  //
  // IT LAYS THE ROWS OUT THE WAY THE BROWSER WILL -- greedily, a chip joining
  // the current row whenever it fits -- rather than choosing sets of chips per
  // row, so what it scores is what `flex-wrap` then draws.
  //
  // A CHIP MATCHING A FILTER STAYS AT THE FRONT (#757): `pinned` leading chips
  // are placed first, in the order given, and only the rest are arranged.
  //
  //   adv[i]      the width chip i takes with another chip after it (its dot)
  //   lastAdv[i]  its width as the very last chip, which draws no dot
  //   pinned      how many leading chips keep their place
  //   o.W         the width of a row
  //   o.lastW     how far the row on the ship's line may run
  //   o.cap       how many rows the stylesheet shows
  //   o.full      also fill the upper rows as full as they will go
  //
  // Returns { order, visible } -- indices into `adv` -- or null when no order
  // keeps the ship's row short enough.
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
       -(rows in the end)], and in `full` mode the final width of this row and
       each row after it. Bigger is better, read left to right. */
    function solve(mask, placed, r, fill) {
      var key = mask + ':' + r + ':' + Math.round(fill * 10);
      if (key in memo) return memo[key];
      var best = null;
      if (mask === ALL) {
        if (fill <= o.lastW + FITS) {
          best = { s: [0, -(r + 1)], next: -1, done: true };
          if (o.full) best.s.push(fill);
        }
        memo[key] = best;
        return best;
      }
      for (var i = 0; i < n; i++) {
        var bit = Math.pow(2, i);
        if (Math.floor(mask / bit) % 2) continue;
        if (placed < pinned && i !== placed) continue;
        var w = (mask + bit === ALL) ? lastAdv[i] : adv[i];
        var stays = fill === 0 || fill + w <= o.W + FITS;
        var cand;
        if (!stays && r + 1 >= o.cap) {
          // This chip starts a row past the cap: it and everything after it
          // are clipped, and row `r` is the one on the ship's line.
          if (fill > o.lastW + FITS) continue;
          cand = { s: [0, -(r + 1)], next: i, done: true };
          if (o.full) cand.s.push(fill);
        } else {
          var sub = solve(mask + bit, placed + 1, stays ? r : r + 1, stays ? fill + w : w);
          if (!sub) continue;
          var s = [sub.s[0] + 1, sub.s[1]];
          if (o.full) {
            if (!stays) s.push(fill);
            for (var k = 2; k < sub.s.length; k++) s.push(sub.s[k]);
          }
          cand = { s: s, next: i, done: false };
        }
        if (better(cand.s, best && best.s)) best = cand;
      }
      memo[key] = best;
      return best;
    }

    var node = solve(0, 0, 0, 0);
    if (!node) return null;
    var order = [];
    var mask = 0, r = 0, fill = 0;
    var visible = node.s[0];
    while (node && !node.done) {
      var i = node.next;
      var bit = Math.pow(2, i);
      var w = (mask + bit === ALL) ? lastAdv[i] : adv[i];
      var stays = fill === 0 || fill + w <= o.W + FITS;
      order.push(i);
      mask += bit;
      if (stays) { fill += w; } else { r += 1; fill = w; }
      node = solve(mask, order.length, r, fill);
    }
    // The clipped chips: the one that broke the row first, so nothing smaller
    // slips back onto the ship's line, then the rest as they were.
    if (node && node.next >= 0) order.push(node.next);
    for (var j = 0; j < n; j++) {
      if (order.indexOf(j) < 0) order.push(j);
    }
    return { order: order, visible: visible };
  }

  /* THE CANDIDATES SWITCH -- #1308, and it goes when Helen has picked. The
     candidates page sets `data-chip-order` on <html>: `alpha` leaves the chips
     as the template sorted them, `full` also fills the upper rows. Absent, the
     chips are packed and otherwise alphabetical. */
  function chipOrderMode() {
    var root = document.documentElement;
    return (root && root.getAttribute && root.getAttribute('data-chip-order')) || 'least';
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
     the caller's own measurement decides, as it did before #1308. */
  function arrangeChips(card, moods, ship) {
    var mode = chipOrderMode();
    if (!moods.appendChild || !moods.getBoundingClientRect || !card.style) return null;
    var els = Array.prototype.slice.call(moods.querySelectorAll('.drink-card-mood'));
    if (els.length < 2 || els.length > 12) return null;
    var m = moods.getBoundingClientRect();
    if (!m.width) return null;   // hidden card

    // ALPHABETICAL IS THE BASE, read off the labels rather than the DOM, which
    // an earlier pass of this very function may have rearranged. Lowercased,
    // for `sort_natural`'s reason: `I want to faff` is capitalised.
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
    if (mode === 'alpha') {
      reorderChips(moods, els, base);
      return null;
    }

    // WHAT A CHIP COSTS depends on whether another follows it: every chip but
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

    var sig = [mode, pinned, W.toFixed(1), lastW.toFixed(1), paddedW.toFixed(1), cap,
      base.map(label).join('|'), adv.map(function (x) { return x.toFixed(1); }).join('|')].join('/');
    var plan = planned && planned.get(moods);
    if (!plan || plan.sig !== sig) {
      var opts = { W: W, lastW: lastW, cap: cap, full: mode === 'full' };
      var open = packChips(adv, lastAdv, pinned, opts);
      plan = { sig: sig, order: open && open.order, padded: false };
      if (hasShip && (!open || open.visible < base.length)) {
        // Nothing keeps the ship's row short, or something is still clipped:
        // see what the padded width shows, and take it only if it shows more.
        var shut = packChips(adv, lastAdv, pinned,
          { W: paddedW, lastW: Infinity, cap: cap, full: opts.full });
        if (shut && (!open || shut.visible > open.visible)) {
          plan.order = shut.order;
          plan.padded = true;
        }
      }
      if (planned) planned.set(moods, plan);
    }
    if (!plan.order) return null;
    reorderChips(moods, els, plan.order.map(function (i) { return base[i]; }));
    return plan.padded;
  }

  /* Moved only when the order differs, the guard cocktail-index.js keeps on
     its own chip move: most cards are already in the order this wants. */
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
     again -- the same reset-then-measure order the ingredient pass keeps. The
     ship's left edge is the line; a chip whose box crosses it AND sits on the
     ship's row (vertical overlap) is the collision. Chips on rows above the
     ship are not in the way and are not counted.

     SINCE #1308 THE CHIPS ARE ARRANGED FIRST, and usually into an order that
     stops short of the ship, so this measurement mostly finds nothing. It
     stays as the judge all the same: arrangeChips predicts a layout and this
     reads the one the browser drew. */
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
  window.addEventListener('resize', run);

  // AND AGAIN ONCE THE REAL FACE ARRIVES -- 2026-09-10, found by the ship
  // pass. At DOMContentLoaded the chips are set in the fallback Courier, which
  // is narrower than Courier Prime; the rows measured clean, then the web font
  // landed, the last row grew into the ship and nothing re-measured. Seven of
  // twenty cards on the first deal. card-name-fit.js re-runs on
  // `document.fonts.ready` for the same reason; this pass now does too, and
  // stays after it in the chain.
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(run);
  }
})();
