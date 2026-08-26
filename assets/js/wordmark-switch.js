/* =============================================================================
   #477: a look-at-it switch for the wordmark's emboss. Local builds only.
   =============================================================================
   `?wordmark=match` puts HELEN TRIAGES on the shared --emboss-* values, so it
   takes the same stroke colour, offset, highlight and shadow as a page heading
   on whichever site you are looking at. Without the parameter nothing changes.

   WORKS ON BOTH SITES, and that is the point rather than a side effect: this
   is shared chrome, so the answer has to be judged on food and on cocktails
   together. The stylesheet handles the per-site part by reading custom
   properties, so each site's wordmark matches its OWN headings.

   Gated on `site.show_drafts` in _layouts/default.html -- a key that exists
   only in _config_local.yml -- so no production page loads it. The FILE is
   still copied, because Jekyll copies everything under assets/ whether linked
   or not; that is issue #276's lesson and worth restating rather than claiming
   the file is absent.

   No persistence, deliberately: a toggle you forget you left on means
   comparing against a baseline you think is the default and is not.
   ============================================================================= */
(function () {
  var mark = document.querySelector('.site-logo-top');
  if (!mark) return;

  if (new URLSearchParams(window.location.search).get('wordmark') === 'match') {
    mark.classList.add('wordmark--match');
  }
})();
