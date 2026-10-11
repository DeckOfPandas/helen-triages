// universe.js
// "The universe says": one random pick dealt above the cocktail index's
// filter panel, with a "deal again" control.
//
// It knows nothing of the page's markup: which rows a deal is drawn from and
// which parts are copied come from the section's `data-universe-rows` and
// `data-universe-parts`. Without a `.universe` section it does nothing.
//
// The pick is a clone of the row's own elements, so it cannot drift from the
// list beneath it. Parts are copied in the order the attribute lists its
// selectors, not document order; do not merge them into one querySelectorAll.
//
// Load order matters: this runs before decorations.js's cardTapes() and
// before card-name-fit.js, both loaded by _layouts/default.html after the
// page's own scripts, so the first deal is taped and measured by their own
// load passes.
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

  // A card's mood chips are <button>s wired by a listener delegated on
  // `.drink-cards`; a copy in the pick, outside that list, would do nothing.
  // So each becomes a <span> with the same class, data-* and text.
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

    // Every match of each selector, not only the first.
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

      // On the first deal the source's tape slot is still empty and
      // cardTapes() fills the clone's with every other. On "deal again"
      // nothing will fill it, so the source's <svg> is copied across.
      var cloneTapeSlots = clone.querySelectorAll('[data-card-tape]');
      var sourceTapeSlots = source.querySelectorAll('[data-card-tape]');
      Array.prototype.forEach.call(cloneTapeSlots, function (slot, idx) {
        slot.innerHTML = sourceTapeSlots[idx] ? sourceTapeSlots[idx].innerHTML : '';
      });

      buttonsToSpans(clone);
      pick.appendChild(clone);
    }

    section.hidden = false;

    // The clone carries the source card's `drink-card-name--step` / `--wrap`,
    // which are measurements of a narrower card, so the name fit is re-run
    // after every deal. On the first deal the helper is not loaded yet and
    // its own load pass does the measuring.
    if (window.HTF && window.HTF.fitCardNames) window.HTF.fitCardNames();
  }

  if (again) again.addEventListener('click', deal);

  deal();
})();
