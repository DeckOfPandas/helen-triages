/* =============================================================================
   LOOK-AT-IT SWITCHES, not features. Local builds only.
   =============================================================================
   Two open questions about where the glass drawing sits, each behind its own
   query parameter so they can be judged separately or together:

     ?glass=margin   the drawing moves out into the page's left margin, so the
                     title starts on exactly the same left edge as a food
                     recipe page.
     ?align=top      a SHORT glass hangs from the top edge and stops where it
                     stops, instead of sitting centred in the block. A tall
                     glass fills the block either way, so this shows only on
                     the short ones.

   See _sass/cocktails/_cocktail.scss for both layouts and for what to watch
   for while judging them.

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

  var params = new URLSearchParams(window.location.search);

  /* Two switches, deliberately on separate parameters because they are
     independent questions: `glass` is where the drawing sits HORIZONTALLY
     (in the column, or out in the page margin), `align` is how a SHORT glass
     sits vertically (centred in the block, or hanging from its top edge). A
     tall glass fills the block either way, so `align` only shows on the short
     ones. Combine them freely: ?glass=margin&align=top. */
  if (params.get('glass') === 'margin') {
    article.classList.add('cocktail--glass-margin');
  }
  if (params.get('align') === 'top') {
    article.classList.add('cocktail--glass-top');
  }
})();
