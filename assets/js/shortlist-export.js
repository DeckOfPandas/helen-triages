// shortlist-export.js
// =============================================================================
// SHARE OR SAVE THE SHORTLIST -- one link. #1093, cut back to that by #1100.
// =============================================================================
// This file used to be the JSON export (#849), the paste-back restore (#850)
// and a two-click clear. Helen, 2026-09-15, on PR #1100: "Remove the rest of
// the apparatus: no JSON export or import, no clear." What is left is the
// link #1093 put at the top of the same panel: this index's own address with
// `?shortlist=slug,slug`, which both indexes read back as a list to SHOW and
// not save (HTF.filterState.parseShortlist, HTF.shortlist.resolveSlugs). Save
// it by bookmarking it, send it by copying it. MANUAL 8.9.
//
// ONE SCRIPT, BOTH SITES. It finds `[data-shortlist-export-panel]` and does
// not care which index it is on; `HTF.site` keeps the two stores apart.
//
// THE PANEL SHIPS `hidden` AND THIS REVEALS IT, and only while something is
// shortlisted: a control that silently fails is worse than no control, and
// there is no link to a list of nothing. It repaints on `htf:shortlist-change`,
// the event shortlist.js dispatches, so marking a drink with the panel open
// updates the link under it.
// =============================================================================

(function () {
  'use strict';

  var HTF = window.HTF;

  // No store, no link. The root landing page has no site key and so has no
  // shortlist at all.
  if (!HTF || !HTF.shortlist || !HTF.site) return;

  function all(selector) {
    return Array.prototype.slice.call(document.querySelectorAll(selector));
  }

  /* Slugs rather than keys: a link is read by people, and the slug is the part
     of a key that survives a folder move. Built from the page's own origin and
     path, so a link made on a local build points at the local build. '' when
     nothing is shortlisted. */
  function shareLink() {
    if (!HTF.filterState || !HTF.filterState.shortlistQuery) return '';
    var query = HTF.filterState.shortlistQuery(
      HTF.shortlist.list().map(HTF.shortlist.slugOf));
    if (!query) return '';
    return location.origin + location.pathname + '?' + query;
  }

  /* The Clipboard API needs a secure context, so it is missing over plain http
     on a phone on the local network -- how Helen reads this site while cooking.
     The field is the feature; the button is a convenience that hides. */
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
