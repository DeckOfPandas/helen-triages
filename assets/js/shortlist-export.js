// shortlist-export.js
// =============================================================================
// THE SHORTLIST AS TEXT YOU CAN COPY — GitHub issue #849.
// =============================================================================
// Helen, 2026-09-08: "allow me to export my food or cocktail shortlist as a
// YAML/JSON dump -- can be just a text area at the bottom of the page."
//
// HTF.shortlist.snapshot() (assets/js/assets.js) is the STORE half and knows
// nothing about a page; this is the wiring and knows nothing about storage.
// Same split shortlist.js, filters.js and shopping-list.js already run on, and
// for the same reason: the part worth testing without a browser is the part
// that assembles the value, and that is not this file.
//
// ONE SCRIPT, BOTH SITES. It finds `[data-shortlist-export]` and does not care
// which index it is on, exactly as shortlist.js does with `.btn-shortlist`.
// `HTF.site` is already the thing that keeps food and cocktails apart, in the
// store, so there is nothing to branch on here.
//
// IT SHIPS `hidden` AND THIS REVEALS IT, which is `.btn-print`'s rule and the
// one _layouts/recipe.html states: "a control that silently fails is worse than
// no control". A textarea claiming to hold your shortlist, in a browser where
// the script did not run, would hold the empty string and look like an answer.
// So the markup assumes JavaScript did not run and this is what proves it did.
//
// READONLY, AND DELIBERATELY NOT AN IMPORT. Typing into this box would look
// exactly like it should do something, and #850 is where doing something is
// specified. A box that accepts edits and discards them is the worst of the
// three options, so it accepts none.
//
// IT REPAINTS ON `htf:shortlist-change`, the event shortlist.js dispatches --
// so shortlisting a drink with the panel open updates the text under it rather
// than leaving a dump that quietly disagrees with the page it is on. Same
// subscription both indexes already use to repaint themselves.
// =============================================================================

(function () {
  'use strict';

  var HTF = window.HTF;

  // No store, no export. The root landing page has no site key and so has no
  // shortlist at all -- see HTF.shortlist's own note on why that is a refusal
  // rather than a fallback to a shared list.
  if (!HTF || !HTF.shortlist || !HTF.site) return;

  var EVENT = 'htf:shortlist-change';

  function boxes() {
    return Array.prototype.slice.call(
      document.querySelectorAll('[data-shortlist-export]')
    );
  }

  /* TWO SPACES, because a person reads this one. The dump is for copying into
     a note or a message, not for a machine that would rather have it dense. */
  function text() {
    return JSON.stringify(HTF.shortlist.snapshot(), null, 2);
  }

  function paint() {
    var dump = text();
    var empty = HTF.shortlist.count() === 0;
    boxes().forEach(function (box) {
      box.value = dump;
      // The section around the box, so its heading and hint hide with it.
      var section = box.closest ? box.closest('[data-shortlist-export-panel]') : null;
      (section || box).hidden = false;
      var note = section && section.querySelector('[data-shortlist-export-empty]');
      if (note) note.hidden = !empty;
    });
    // #849's SECOND PLACEMENT, revealed by the same pass and for the same
    // reason: a link to a panel that never appears is a dead end.
    Array.prototype.slice.call(
      document.querySelectorAll('[data-shortlist-export-jump]')
    ).forEach(function (link) { link.hidden = false; });
  }

  /* FOLLOWING THE JUMP LINK OPENS THE PANEL, and without this it does not.
     The panel is a closed `<details>`, so the browser scrolls to it and shows
     a summary line -- which is exactly the "I could not find it" Helen
     reported, moved a few hundred pixels down the page rather than fixed.
     `<details>` gained automatic opening on fragment navigation only recently
     and not everywhere, so this does it explicitly rather than relying on it. */
  function openOnJump() {
    Array.prototype.slice.call(
      document.querySelectorAll('[data-shortlist-export-jump]')
    ).forEach(function (link) {
      link.addEventListener('click', function () {
        var panel = document.querySelector('[data-shortlist-export-panel]');
        if (panel) panel.open = true;
      });
    });
  }

  /* THE COPY BUTTON IS PROGRESSIVE, and its absence is not a failure. The
     Clipboard API needs a secure context, so it is simply missing over plain
     http on a phone on the local network -- which is exactly how Helen reads
     this site while cooking. The textarea is the feature; this is a
     convenience on top of it, so the button hides rather than erroring. */
  function wireCopy() {
    if (!navigator.clipboard || !navigator.clipboard.writeText) return;
    Array.prototype.slice.call(
      document.querySelectorAll('[data-shortlist-copy]')
    ).forEach(function (btn) {
      btn.hidden = false;
      btn.addEventListener('click', function () {
        navigator.clipboard.writeText(text()).then(function () {
          var was = btn.textContent;
          btn.textContent = 'copied';
          setTimeout(function () { btn.textContent = was; }, 1200);
        }, function () { /* the textarea is still there to select by hand */ });
      });
    });
  }

  if (!boxes().length) return;
  paint();
  wireCopy();
  openOnJump();
  document.addEventListener(EVENT, paint);
})();
