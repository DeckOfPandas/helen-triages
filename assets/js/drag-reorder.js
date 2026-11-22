// drag-reorder.js: drag a row up or down a list by its grip (#1521), as
// HTF.dragReorder. MANUAL §8.9. Pointer events, so a finger, a mouse and an
// Apple Pencil all drag; the grip has `touch-action: none` in the stylesheet,
// or iPad Safari scrolls the page instead. This file is the pointer's half:
// the keyboard moves a row with the arrow keys on the same grip, which the
// page handles. Nothing moves in the DOM until the drop; the rows are slid
// with transforms, and Escape or a cancelled pointer puts them back.

(function (root, factory) {
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = factory();
  } else {
    root.HTF = root.HTF || {};
    root.HTF.dragReorder = factory();
  }
})(typeof window !== 'undefined' ? window : this, function () {
  'use strict';

  var EDGE = 48;
  var SCROLL_STEP = 12;

  /* Where a row lands with the pointer at `y`: one place for every other row
     whose middle is above the pointer. The pointer, not the row's own middle,
     since a tall row's grip is near its top. `mids` are every row's middles,
     from where the drag began. */
  function targetIndex(y, mids, from) {
    var to = 0;
    mids.forEach(function (mid, i) {
      if (i !== from && y > mid) to += 1;
    });
    return to;
  }

  /* `root` holds the lists (it may be redrawn under the page, so the work is
     delegated); `onDrop(item, from, to)` is called only for a real move. */
  function attach(root, options) {
    var drag = null;

    function pageY(ev) { return ev.clientY + window.pageYOffset; }

    function slide(to) {
      drag.items.forEach(function (item, i) {
        if (i === drag.from) return;
        var shift = 0;
        if (drag.from < to && i > drag.from && i <= to) shift = -drag.room;
        if (drag.from > to && i >= to && i < drag.from) shift = drag.room;
        item.style.transform = shift ? 'translateY(' + shift + 'px)' : '';
      });
    }

    function follow() {
      var dy = drag.y - drag.startY;
      drag.item.style.transform = 'translateY(' + dy + 'px)';
      drag.to = targetIndex(drag.y, drag.mids, drag.from);
      slide(drag.to);
    }

    // Near the top or bottom of the screen the page scrolls, so a long list
    // can be crossed in one drag.
    function scroll() {
      if (!drag) return;
      var y = drag.clientY;
      var step = y < EDGE ? -SCROLL_STEP : (y > window.innerHeight - EDGE ? SCROLL_STEP : 0);
      if (step) {
        var before = window.pageYOffset;
        window.scrollBy(0, step);
        drag.y += window.pageYOffset - before;
        follow();
      }
      drag.frame = window.requestAnimationFrame(scroll);
    }

    function end(drop) {
      if (!drag) return;
      var done = drag;
      drag = null;
      window.cancelAnimationFrame(done.frame);
      done.list.classList.remove('is-reordering');
      done.item.classList.remove('is-dragging');
      done.items.forEach(function (item) { item.style.transform = ''; });
      if (done.grip.hasPointerCapture && done.grip.hasPointerCapture(done.pointer)) {
        done.grip.releasePointerCapture(done.pointer);
      }
      if (drop && done.to !== done.from) options.onDrop(done.item, done.from, done.to);
    }

    root.addEventListener('pointerdown', function (ev) {
      var grip = ev.target.closest && ev.target.closest(options.grip);
      if (!grip || !root.contains(grip) || drag) return;
      if (ev.pointerType === 'mouse' && ev.button !== 0) return;
      var item = grip.closest(options.item);
      var list = item && item.parentNode;
      if (!list) return;
      var items = Array.prototype.filter.call(list.children, function (el) { return el.matches(options.item); });
      if (items.length < 2) return;
      ev.preventDefault();
      var rects = items.map(function (el) { return el.getBoundingClientRect(); });
      var from = items.indexOf(item);
      var gap = parseFloat(window.getComputedStyle(list).rowGap) || 0;
      drag = {
        grip: grip, item: item, list: list, items: items, from: from, to: from,
        pointer: ev.pointerId, startY: pageY(ev), y: pageY(ev), clientY: ev.clientY,
        room: rects[from].height + gap,
        mids: rects.map(function (r) { return r.top + window.pageYOffset + r.height / 2; })
      };
      if (grip.setPointerCapture) grip.setPointerCapture(ev.pointerId);
      list.classList.add('is-reordering');
      item.classList.add('is-dragging');
      drag.frame = window.requestAnimationFrame(scroll);
    });

    root.addEventListener('pointermove', function (ev) {
      if (!drag || ev.pointerId !== drag.pointer) return;
      ev.preventDefault();
      drag.y = pageY(ev);
      drag.clientY = ev.clientY;
      follow();
    });

    root.addEventListener('pointerup', function (ev) {
      if (drag && ev.pointerId === drag.pointer) end(true);
    });

    root.addEventListener('pointercancel', function (ev) {
      if (drag && ev.pointerId === drag.pointer) end(false);
    });

    document.addEventListener('keydown', function (ev) {
      if (drag && ev.key === 'Escape') { ev.preventDefault(); end(false); }
    });
  }

  return { targetIndex: targetIndex, attach: attach };
});
