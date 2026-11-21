// shortlist-export.js
// Share, save or restore the shortlists (#1093, #1100, #1521). The block is a
// line per list with something on it, "Name: link", each link this index's
// own address with `?shortlist=slug,slug&list=Name`, which both indexes show
// and do not save. Restore reads a pasted block back and saves every list in
// it, into the list of that name. MANUAL §8.9.
//
// One script for both sites: it finds `[data-shortlist-export-panel]` (the
// include _includes/shortlist-export.html), and `HTF.site` keeps the two
// stores apart. The panel ships `hidden` and this reveals it; the block part
// shows only while some list has something on it. It repaints on
// `htf:shortlist-change`.

(function () {
  'use strict';

  var HTF = window.HTF;

  // No store, no panel: a page with no site key has no shortlist at all.
  if (!HTF || !HTF.shortlist || !HTF.site || !HTF.filterState) return;

  var store = HTF.shortlist;
  var FS = HTF.filterState;

  function all(selector) {
    return Array.prototype.slice.call(document.querySelectorAll(selector));
  }

  /* Slugs, not keys: the slug is the part of a key that survives a folder
     move. Built from the page's own origin and path, so a block made on a
     local build points at the local build. '' when every list is empty. */
  function shareBlock() {
    if (!FS.shortlistBlock) return '';
    return FS.shortlistBlock(location.origin + location.pathname,
      store.exportLists().map(function (l) {
        return { name: l.name, slugs: l.keys.map(store.slugOf) };
      }));
  }

  /* The Clipboard API needs a secure context, so it is missing over plain
     http on a phone on the local network. The field is the feature; the
     button is a convenience that hides. */
  function canCopy() {
    return !!(navigator.clipboard && navigator.clipboard.writeText);
  }

  function paint() {
    var block = shareBlock();
    all('[data-shortlist-export-panel]').forEach(function (panel) { panel.hidden = false; });
    all('[data-shortlist-export-lists]').forEach(function (part) { part.hidden = !block; });
    all('[data-shortlist-share]').forEach(function (field) {
      field.value = block;
      field.rows = Math.max(2, Math.min(8, block.split('\n').length + 1));
    });
    all('[data-shortlist-share-copy]').forEach(function (btn) {
      btn.hidden = !block || !canCopy();
    });
  }

  /* Every recipe or drink this page knows, for matching a pasted slug. */
  function liveKeys() {
    return all('[data-shortlist-key]').map(function (el) {
      return el.getAttribute('data-shortlist-key');
    });
  }

  function say(el, text) {
    if (!el) return;
    el.textContent = text;
    el.hidden = !text;
  }

  function plural(n, word) {
    return n + ' ' + word + (n === 1 ? '' : 's');
  }

  /* Restore: every list in the pasted block, into the list of its name. */
  function restore(field, result) {
    var blocks = FS.parseShortlistBlock(field.value);
    if (!blocks.length) {
      say(result, 'No shortlist links found in that.');
      return;
    }
    var done = store.restore(blocks, liveKeys());
    var thing = HTF.site === 'cocktails' ? 'drink' : 'recipe';
    var text = 'Restored ' + plural(done.lists, 'list') + ': ' +
      plural(done.added, thing) + ' added.';
    if (done.unmatched.length) text += ' Not found: ' + done.unmatched.join(', ') + '.';
    say(result, text);
    field.value = '';
    document.dispatchEvent(new CustomEvent('htf:shortlist-change', {
      detail: { key: null, on: true, restored: done.lists }
    }));
  }

  /* The block selects whole on focus, so a phone with no clipboard API still
     gets it in one long-press. */
  function wire() {
    all('[data-shortlist-share]').forEach(function (field) {
      field.addEventListener('focus', function () {
        if (field.select) field.select();
      });
    });

    all('[data-shortlist-export-panel]').forEach(function (panel) {
      var go = panel.querySelector('[data-shortlist-restore-go]');
      var field = panel.querySelector('[data-shortlist-restore]');
      var result = panel.querySelector('[data-shortlist-restore-result]');
      if (go && field) go.addEventListener('click', function () { restore(field, result); });
    });

    if (!canCopy()) return;
    all('[data-shortlist-share-copy]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var block = shareBlock();
        if (!block) return;
        navigator.clipboard.writeText(block).then(function () {
          var was = btn.textContent;
          btn.textContent = 'copied';
          setTimeout(function () { btn.textContent = was; }, 1200);
        }, function () { /* the field is still there to select by hand */ });
      });
    });
  }

  if (!all('[data-shortlist-export-panel]').length) return;
  paint();
  wire();
  document.addEventListener('htf:shortlist-change', paint);
})();
