// shortlist-export.js
// Share or save the shortlist: one link (#1093, #1100). This index's own
// address with `?shortlist=slug,slug`, which both indexes read back as a list
// to SHOW and not save (HTF.filterState.parseShortlist,
// HTF.shortlist.resolveSlugs). MANUAL §8.9.
//
// One script for both sites: it finds `[data-shortlist-export-panel]`, and
// `HTF.site` keeps the two stores apart. The panel ships `hidden` and this
// reveals it, only while something is shortlisted. It repaints on
// `htf:shortlist-change`, the event shortlist.js dispatches.

(function () {
  'use strict';

  var HTF = window.HTF;

  // No store, no link: a page with no site key has no shortlist at all.
  if (!HTF || !HTF.shortlist || !HTF.site) return;

  function all(selector) {
    return Array.prototype.slice.call(document.querySelectorAll(selector));
  }

  /* Slugs, not keys: the slug is the part of a key that survives a folder
     move. Built from the page's own origin and path, so a link made on a
     local build points at the local build. '' when nothing is shortlisted. */
  function shareLink() {
    if (!HTF.filterState || !HTF.filterState.shortlistQuery) return '';
    var query = HTF.filterState.shortlistQuery(
      HTF.shortlist.list().map(HTF.shortlist.slugOf));
    if (!query) return '';
    return location.origin + location.pathname + '?' + query;
  }

  /* The Clipboard API needs a secure context, so it is missing over plain
     http on a phone on the local network. The field is the feature; the
     button is a convenience that hides. */
  function canCopy() {
    return !!(navigator.clipboard && navigator.clipboard.writeText);
  }

  function paint() {
    var link = shareLink();
    all('[data-shortlist-export-panel]').forEach(function (panel) {
      panel.hidden = !link;
    });
    all('[data-shortlist-share]').forEach(function (field) { field.value = link; });
    all('[data-shortlist-share-copy]').forEach(function (btn) {
      btn.hidden = !link || !canCopy();
    });
  }

  /* The field selects whole on focus, so a phone with no clipboard API still
     gets the link in one long-press. */
  function wire() {
    all('[data-shortlist-share]').forEach(function (field) {
      field.addEventListener('focus', function () {
        if (field.select) field.select();
      });
    });
    if (!canCopy()) return;
    all('[data-shortlist-share-copy]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var link = shareLink();
        if (!link) return;
        navigator.clipboard.writeText(link).then(function () {
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
