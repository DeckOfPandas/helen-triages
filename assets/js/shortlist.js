// shortlist.js
// The shortlist's DOM half: every control that marks or unmarks one thing
// (#546). HTF.shortlist (assets.js) is the store and knows nothing about a
// page; this is the wiring and knows nothing about storage.
//
// - Every control, on either site, is `.btn-shortlist` carrying
//   `data-shortlist-key`: a new placement is markup and a stylesheet rule.
// - The controls ship `hidden` and this reveals them: the markup assumes
//   JavaScript did not run, and a control that silently fails is worse than
//   no control.
// - The word never changes; the class and aria-pressed carry the state, and
//   the stylesheet draws the mark (DECISIONS §9.13). So the control cannot
//   change width.
// - Changes are announced with a document event, `htf:shortlist-change`, so
//   each index repaints itself and this file does not know they exist.

(function () {
  'use strict';

  var HTF = window.HTF;

  // No store, no controls: a page with no site key has no shortlist at all.
  if (!HTF || !HTF.shortlist || !HTF.site) return;

  var EVENT = 'htf:shortlist-change';

  function controls() {
    return Array.prototype.slice.call(
      document.querySelectorAll('.btn-shortlist[data-shortlist-key]')
    );
  }

  /* Paint one control from the store. Class for the eye, aria-pressed for a
     screen reader. */
  function paint(btn) {
    var on = HTF.shortlist.has(btn.dataset.shortlistKey);
    btn.classList.toggle('is-on', on);
    btn.setAttribute('aria-pressed', on ? 'true' : 'false');
  }

  /* Every count on the page, from one place.

     `[data-shortlist-count]` is how many there are to SEE on this page, not
     how many the store holds (#847): a key can outlive its page (a rename, a
     promoted draft), and the index's filter can only show this page's
     controls. The store is left alone, because the key may be right on some
     other page. */
  function paintCounts() {
    var n = controls().filter(function (btn) {
      return HTF.shortlist.has(btn.dataset.shortlistKey);
    }).length;
    Array.prototype.slice.call(document.querySelectorAll('[data-shortlist-count]'))
      .forEach(function (el) { el.textContent = String(n); });

    /* `[data-shortlist-total]` is the store's own count, for the "see
       shortlist (N)" link on a recipe or drink page
       (_includes/page-actions.html): that link goes TO the index, so the
       number is everything the store holds. */
    var total = HTF.shortlist.count();
    Array.prototype.slice.call(document.querySelectorAll('[data-shortlist-total]'))
      .forEach(function (el) { el.textContent = String(total); });

    /* The link ships `hidden` and shows only while there is something to see
       (#1210). This is the one place that decides. */
    Array.prototype.slice.call(document.querySelectorAll('.btn-see-shortlist'))
      .forEach(function (link) { link.hidden = total === 0; });
  }

  /* The whole page, not the button that was clicked: painting only the
     clicked one goes stale the first time two controls share a key. */
  function repaint() {
    controls().forEach(paint);
    paintCounts();
  }

  function wire() {
    var all = controls();

    all.forEach(function (btn) {
      paint(btn);
      // The proof that JavaScript ran. See the header.
      btn.hidden = false;
    });
    paintCounts();

    /* One delegated listener on the document, so the handler does not care
       which rows or cards exist when it is attached. */
    document.addEventListener('click', function (ev) {
      var btn = ev.target.closest && ev.target.closest('.btn-shortlist[data-shortlist-key]');
      if (!btn) return;
      ev.preventDefault();

      var key = btn.dataset.shortlistKey;
      HTF.shortlist.toggle(key);
      repaint();

      document.dispatchEvent(new CustomEvent(EVENT, {
        detail: { key: key, on: HTF.shortlist.has(key) }
      }));
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wire);
  } else {
    wire();
  }
})();
