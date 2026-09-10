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
// THE EXPORT BOX IS READONLY, AND THE IMPORT IS A SECOND BOX -- #850, built
// 2026-09-10. Typing into the export box would look exactly like it should do
// something, and a box that accepts edits and discards them is the worst of the
// three options, so it still accepts none. Pasting a dump back IN is its own
// textarea and a `restore` button underneath, in the same panel: the store's
// `restore()` does the matching and merging, this file only carries the text
// across and prints what came back. Helen's reason for wanting it at all:
// "I just KNOW that something will go wrong and I'll lose my shortlist" --
// localStorage on a phone is exactly as durable as the browser decides it is.
//
// THE IMPORT DISPATCHES THE SAME EVENT A CLICK DOES. Both indexes repaint
// from state on `htf:shortlist-change` (cocktail-index.js re-runs apply(),
// filters.js its own pass), and the export box below repaints on it too. So
// one dispatch after a successful restore is what makes the cards, the count
// and the dump all agree with the store again. `detail.key` is null: nothing
// downstream reads it today, and a restore is not about one key.
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
  }

  /* THE JUMP LINK ABOVE THE LIST IS GONE, 2026-09-10. #849's second placement
     put "export list as JSON →" beside the `shortlisted (n)` button, and the
     `openOnJump` that used to live here opened the panel when it was followed.
     Helen agreed it read as developer furniture to anyone else looking at the
     page; the panel at the foot is the one way in now. */

  /* CLEAR, ARMED BY A FIRST CLICK -- Helen, 2026-09-10: "we also need a
     'clear shortlist' button somewhere." The store has had `clear()` since
     #546 and nothing called it. Two clicks on purpose: the list is passed
     round a table on an iPad, and one tap is how it would go. The first click
     swaps the word for the question in `data-armed-text`; a second within
     ARM_MS empties the list and repaints everything through the same event a
     toggle dispatches; doing nothing lets it disarm and the word comes back.
     No `confirm()` dialog: it is modal, it looks like an error, and on a
     phone it steals the page. */
  var ARM_MS = 4000;

  function wireClear() {
    var btn = document.querySelector('[data-shortlist-clear]');
    if (!btn) return;
    var restText = btn.textContent;
    var armedText = btn.getAttribute('data-armed-text') || restText;
    var timer = null;
    btn.hidden = false;

    function disarm() {
      clearTimeout(timer);
      timer = null;
      btn.classList.remove('is-armed');
      btn.textContent = restText;
    }

    btn.addEventListener('click', function () {
      if (!timer) {
        btn.classList.add('is-armed');
        btn.textContent = armedText;
        timer = setTimeout(disarm, ARM_MS);
        return;
      }
      disarm();
      HTF.shortlist.clear();
      document.dispatchEvent(new CustomEvent(EVENT, {
        detail: { key: null, on: null, cleared: true }
      }));
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

  /* THE RESTORE MESSAGE, one line, from the result the store hands back. The
     sentences are PLACEHOLDER COPY in the sense #713 and #753 use: the shape
     is the feature and the words are Helen's to change. Slugs are printed as
     slugs -- the page has no title for a drink it could not find, which is
     the whole reason it is being reported. */
  function message(result) {
    if (!result.ok) {
      if (result.reason === 'wrong-site') {
        return 'that is a ' + result.site + ' shortlist, not one for this site.';
      }
      return 'that does not read as a shortlist export.';
    }
    if (!result.restored && !result.unmatched.length) return 'nothing to restore.';
    var line = 'restored ' + result.restored;
    if (result.restored && !result.added) line += ' (all already here)';
    else if (result.restored && result.added < result.restored) {
      line += ' (' + (result.restored - result.added) + ' already here)';
    }
    if (result.unmatched.length) {
      line += '; not found: ' + result.unmatched.join(', ');
    }
    return line + '.';
  }

  /* THE PASTE BOX AND THE BUTTON, revealed together for the reason the whole
     panel is: a box that invites a paste and then does nothing with it is a
     control that silently fails. The live keys are read at CLICK time, from
     the same controls shortlist.js paints, so a page whose list is still
     being built at load cannot hand the store an empty set. */
  function wireImport() {
    var box = document.querySelector('[data-shortlist-import]');
    var btn = document.querySelector('[data-shortlist-restore]');
    var out = document.querySelector('[data-shortlist-import-result]');
    if (!box || !btn) return;
    box.hidden = false;
    btn.hidden = false;

    btn.addEventListener('click', function () {
      var keys = Array.prototype.slice.call(
        document.querySelectorAll('.btn-shortlist[data-shortlist-key]')
      ).map(function (el) { return el.getAttribute('data-shortlist-key'); });
      var result = HTF.shortlist.restore(box.value, keys);
      if (out) {
        out.textContent = message(result);
        out.hidden = false;
      }
      if (!result.ok) return;
      document.dispatchEvent(new CustomEvent(EVENT, {
        detail: { key: null, on: null, restored: result.restored }
      }));
    });
  }

  if (!boxes().length) return;
  paint();
  wireCopy();
  wireImport();
  wireClear();
  document.addEventListener(EVENT, paint);
})();
