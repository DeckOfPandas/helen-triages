/* =============================================================================
   A LOOK-AT-IT SWITCH, not a feature. Local builds only.
   =============================================================================
   Adds `.cocktail--glass-margin` to the article when the URL carries
   `?glass=margin`, which moves the glass drawing out of the flex row and into
   the page's left margin, so the title starts on exactly the same left edge as
   a food recipe page. See _sass/cocktails/_cocktail.scss for the layout and
   for what to watch for while judging it.

   Helen is comparing this against the shipped layout and expects to keep the
   shipped one. So it is built to be deleted: one class, one query parameter,
   nothing else in the page aware of it.

   _layouts/cocktail.html emits the <script> tag for this file only when
   `site.show_drafts` is true -- a key that exists only in _config_local.yml --
   so no production page loads it.

   THE FILE ITSELF IS STILL COPIED, and saying otherwise would repeat issue
   #276's lesson exactly: Jekyll copies everything under assets/ whether or not
   anything links it, and "unlinked" is not "absent". Verified against a real
   production build rather than assumed -- the file is there, no HTML
   references it. It is inert either way, since it does nothing without the
   query parameter, but the honest description is unreferenced rather than
   absent. Delete the file when the layout question is settled.

   No state is remembered on purpose. A toggle that persists is one you forget
   you left on, and then you are comparing against a layout you think is the
   default and is not; changing the URL is unambiguous.
   ============================================================================= */
(function () {
  var article = document.querySelector('article.cocktail');
  if (!article) return;

  var wants = new URLSearchParams(window.location.search).get('glass');
  if (wants === 'margin') {
    article.classList.add('cocktail--glass-margin');
  }
})();
