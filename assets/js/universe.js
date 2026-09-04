// universe.js
// =============================================================================
// THE UNIVERSE SAYS — one random pick dealt above the index's filter panel.
// =============================================================================
// Issue from the fold mockups, 2026-09-02: both indexes opened with a
// screenful of questions and no answer, so this deals one random survivor
// above the panel before you have filtered anything, with a "deal again"
// control.
//
// COCKTAILS ONLY SINCE 2026-09-04. Food had the same section for two days
// and Helen took it off having seen it deployed: nobody opens a triage site
// to be dealt a random recipe, and the panel of choices is the fold there.
// She kept the drinks one and means to refine it. Nothing in this file
// changed for that -- it is SITE-AGNOSTIC JS, same pattern as print-link.js's
// own header: it queries `.universe` and does nothing on a page that has
// none, so it is harmless to load on every page. Which row a deal is drawn
// from, and which parts of it get copied, are read off the section's own
// `data-universe-rows` and `data-universe-parts` attributes rather than
// hardcoded here, so this file carries no knowledge of the site's markup.
// The cocktails pick is a card: its parts are a card's body and its foot.
//
// THE PICK IS A CLONE, NOT A REBUILD. `data-universe-parts` names the exact
// elements of a row/card that already carry the right classes (title, main
// ingredients, mood chips…), and cloning them is what guarantees the pick
// keeps looking like a row of the list beneath it even if that list's own
// markup changes later — there is no second copy of "what a row looks like"
// for the two to drift apart from.
//
// LOAD ORDER IS LOAD-BEARING. This script sits at the end of each index
// page's own script list, and _layouts/default.html loads decorations.js
// AFTER {{ content }} — so universe.js always runs BEFORE decorations.js's
// cardTapes(), which fills every `[data-card-tape]` slot on the page by
// `slot.innerHTML = svg`. That is what lets a freshly-cloned, still-empty
// tape slot in the pick get its tape for free on the page's first deal; see
// the comment on the tape-copying line in deal() below for the second half
// of that story, the "deal again" button.
// =============================================================================

(function () {
  var section = document.querySelector('.universe');
  if (!section) return;

  var rowsSel = section.getAttribute('data-universe-rows');
  var rows = rowsSel ? document.querySelectorAll(rowsSel) : [];
  if (!rows.length) return;

  var pick = section.querySelector('.universe-pick');
  var again = section.querySelector('.btn-universe-again');
  if (!pick) return;

  var partsSel = section.getAttribute('data-universe-parts') || '';
  var parts = partsSel.split(',');

  // THE MOOD CHIPS ON A CARD ARE REAL <button>s, filtering the index through
  // a listener delegated on `.drink-cards` — a copy of one sitting in the
  // pick, outside that list, would be a button that does nothing. So every
  // button in a clone is rewritten to a <span> carrying the same class,
  // data-* attributes and text, which keeps the look and drops the dead
  // control. Harmless on food's clones, which contain no buttons at all.
  function buttonsToSpans(root) {
    var buttons = root.querySelectorAll('button');
    Array.prototype.forEach.call(buttons, function (btn) {
      var span = document.createElement('span');
      if (btn.className) span.className = btn.className;
      Array.prototype.forEach.call(btn.attributes, function (attr) {
        if (attr.name.indexOf('data-') === 0) span.setAttribute(attr.name, attr.value);
      });
      span.textContent = btn.textContent;
      btn.parentNode.replaceChild(span, btn);
    });
  }

  function deal() {
    var row = rows[Math.floor(Math.random() * rows.length)];
    pick.innerHTML = '';

    // EVERY MATCH OF EACH SELECTOR, not the first -- since 2026-09-04, when
    // the cocktails pick became a card and its parts were briefly
    // `:scope > *`. They are named parts again now, one match each, but a
    // selector that can match several should copy several.
    var sources = [];
    for (var i = 0; i < parts.length; i++) {
      var sel = parts[i].replace(/^\s+|\s+$/g, '');
      if (!sel) continue;
      var found = row.querySelectorAll(sel);
      for (var j = 0; j < found.length; j++) sources.push(found[j]);
    }

    for (var k = 0; k < sources.length; k++) {
      var source = sources[k];
      var clone = source.cloneNode(true);

      // ONE LINE COVERS BOTH TAPE CASES. On the page's first deal (this
      // function running at load, before decorations.js) the SOURCE card's
      // own [data-card-tape] slot is itself still empty, so the clone's copy
      // is empty too — and cardTapes() fills every such slot on the whole
      // document a moment later, this clone's included, for free. On a
      // "deal again" click, cardTapes() has already run and the source's
      // slot already holds its <svg>; nothing will fill the clone's slot for
      // us a second time, so copying the (now non-empty) source is what
      // gives the fresh clone its tape immediately.
      var cloneTapeSlots = clone.querySelectorAll('[data-card-tape]');
      var sourceTapeSlots = source.querySelectorAll('[data-card-tape]');
      Array.prototype.forEach.call(cloneTapeSlots, function (slot, idx) {
        slot.innerHTML = sourceTapeSlots[idx] ? sourceTapeSlots[idx].innerHTML : '';
      });

      buttonsToSpans(clone);
      pick.appendChild(clone);
    }

    section.hidden = false;

    // THE PICK IS A WIDER CARD, SO IT NEEDS ITS OWN MEASUREMENT. Cloning
    // copies the source card's classes, and `drink-card-name--step` /
    // `--wrap` are MEASURED classes rather than facts about the drink — they
    // say "this name did not fit in a 370px card", which is not the question
    // being asked in the pick's roomier column. A cloned wrap would put a
    // two-line tape on a card with space for one line; a cloned step would
    // shrink a name that fits.
    //
    // So the pass is re-run over the whole page after every deal, which
    // re-measures the fresh clone from its base state and leaves every card in
    // the list on its own answer. Guarded twice because this file is
    // site-agnostic and loads on pages that have neither the namespace nor the
    // script: food's clones have no `.drink-card-name` in them at all.
    //
    // ON THE PAGE'S FIRST DEAL THE HELPER IS NOT THERE YET, and that is fine
    // for the same reason the tape slot above is: card-name-fit.js loads at the
    // end of default.html, below this page's own scripts, and its own load pass
    // measures the just-dealt pick along with every card. This call is what
    // covers every LATER deal, when "deal again" appends a clone long after
    // that pass has run — the same two-halves story the tape line tells.
    if (window.HTF && window.HTF.fitCardNames) window.HTF.fitCardNames();
  }

  if (again) again.addEventListener('click', deal);

  deal();
})();
