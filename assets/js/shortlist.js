// shortlist.js
// The shortlist's DOM half: every control that puts one thing on a list, and
// the picker it opens (#546, #1521). HTF.shortlist (assets.js) is the store
// and knows nothing about a page; this is the wiring and knows nothing about
// storage. MANUAL §8.9.
//
// - Every control, on either site, is `.btn-shortlist` carrying
//   `data-shortlist-key`. A press opens the picker: a tick box per list, and
//   "new list…", which makes a list with this recipe already on it.
// - The controls ship `hidden` and this reveals them: a control that silently
//   fails is worse than no control.
// - The word never changes; `is-on` and aria-pressed say "on some list", and
//   the stylesheet draws the mark (DECISIONS §9.13).
// - Changes are announced with `htf:shortlist-change` on the document, so
//   each index repaints itself and this file does not know they exist.

(function () {
  'use strict';

  var HTF = window.HTF;

  // No store, no controls: a page with no site key has no shortlist at all.
  if (!HTF || !HTF.shortlist || !HTF.site) return;

  var EVENT = 'htf:shortlist-change';
  var store = HTF.shortlist;

  function all(selector, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(selector));
  }

  function controls() {
    return all('.btn-shortlist[data-shortlist-key]');
  }

  function announce(key) {
    document.dispatchEvent(new CustomEvent(EVENT, {
      detail: { key: key, on: key ? store.inAny(key) : false }
    }));
  }

  /* Paint one control from the store. Class for the eye, aria-pressed for a
     screen reader. */
  function paint(btn) {
    var on = store.inAny(btn.dataset.shortlistKey);
    btn.classList.toggle('is-on', on);
    btn.setAttribute('aria-pressed', on ? 'true' : 'false');
  }

  /* Every count on the page, from one place. Both count each recipe once,
     however many lists it is on.

     `[data-shortlist-count]` is how many there are to see on this page, not
     how many the store holds (#847): a key can outlive its page, and the
     index can only show this page's rows. `[data-shortlist-total]` is the
     store's own count, for the "see shortlists (N)" link
     (_includes/page-actions.html), shown only while it is above 0 (#1210). */
  function paintCounts() {
    var seen = [];
    controls().forEach(function (btn) {
      var key = btn.dataset.shortlistKey;
      if (seen.indexOf(key) === -1 && store.inAny(key)) seen.push(key);
    });
    all('[data-shortlist-count]').forEach(function (el) { el.textContent = String(seen.length); });

    var total = store.total();
    all('[data-shortlist-total]').forEach(function (el) { el.textContent = String(total); });
    all('.btn-see-shortlist').forEach(function (link) { link.hidden = total === 0; });
  }

  /* The whole page, not the button that was pressed: two controls can share
     a key, and a list renamed elsewhere changes every count. */
  function repaint() {
    controls().forEach(paint);
    paintCounts();
  }

  // --- The picker ------------------------------------------------------------
  // One element for the page, cloned from _includes/shortlist-picker.html's
  // <template> and moved under whichever control opened it.

  var picker = null;
  var openFor = null;   // the control it is open under

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text) node.textContent = text;
    return node;
  }

  /* @returns {boolean} false where the page carries no template */
  function buildPicker() {
    var template = document.getElementById('shortlist-picker-template');
    if (!template || !template.content) return false;
    picker = template.content.firstElementChild.cloneNode(true);
    picker.hidden = true;

    var lists = picker.querySelector('.shortlist-picker-lists');
    var newBtn = picker.querySelector('.shortlist-picker-new');
    var form = picker.querySelector('.shortlist-picker-form');
    var input = picker.querySelector('.shortlist-picker-name');
    var error = picker.querySelector('.shortlist-picker-error');
    input.maxLength = store.NAME_MAX;

    picker.querySelector('.shortlist-picker-close').addEventListener('click', function () {
      closePicker(true);
    });

    picker.querySelector('.shortlist-picker-cancel').addEventListener('click', function () {
      form.hidden = true;
      error.hidden = true;
      newBtn.hidden = false;
      newBtn.focus();
    });

    lists.addEventListener('change', function (ev) {
      var box = ev.target;
      if (!openFor || !box.dataset || !box.dataset.listId) return;
      var key = openFor.dataset.shortlistKey;
      if (store.hasIn(box.dataset.listId, key) !== box.checked) {
        store.toggleIn(box.dataset.listId, key);
      }
      announce(key);
    });

    newBtn.addEventListener('click', function () {
      newBtn.hidden = true;
      form.hidden = false;
      error.hidden = true;
      input.value = '';
      input.focus();
    });

    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      if (!openFor) return;
      var name = store.cleanName(input.value);
      if (!name) { input.focus(); return; }
      var id = store.create(name);
      if (!id) {
        error.textContent = 'There is already a list called ' + name + '.';
        error.hidden = false;
        input.focus();
        return;
      }
      var key = openFor.dataset.shortlistKey;
      store.toggleIn(id, key);
      fillPicker();
      announce(key);
      var box = picker.querySelector('input[data-list-id="' + id + '"]');
      if (box) box.focus();
    });

    picker.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape') { ev.preventDefault(); closePicker(true); }
    });

    document.body.appendChild(picker);
    return true;
  }

  /* The lists, as tick boxes, for the control it is open under. */
  function fillPicker() {
    var key = openFor.dataset.shortlistKey;
    var lists = picker.querySelector('.shortlist-picker-lists');
    lists.textContent = '';
    store.lists().forEach(function (list) {
      var li = el('li', 'shortlist-picker-list');
      var label = el('label');
      var box = el('input');
      box.type = 'checkbox';
      box.dataset.listId = list.id;
      box.checked = store.hasIn(list.id, key);
      label.appendChild(box);
      label.appendChild(el('span', 'shortlist-list-name', list.name));
      li.appendChild(label);
      lists.appendChild(li);
    });
    picker.querySelector('.shortlist-picker-new').hidden = false;
    picker.querySelector('.shortlist-picker-form').hidden = true;
    picker.querySelector('.shortlist-picker-error').hidden = true;
  }

  /* Under the control, its right edge on the control's, kept on screen. */
  function place() {
    var rect = openFor.getBoundingClientRect();
    var width = picker.offsetWidth;
    var gutter = 8;
    var left = rect.right - width;
    left = Math.max(gutter, Math.min(left, document.documentElement.clientWidth - width - gutter));
    picker.style.left = (left + window.pageXOffset) + 'px';
    picker.style.top = (rect.bottom + window.pageYOffset + 6) + 'px';
  }

  function openPicker(btn) {
    if (!picker && !buildPicker()) return;
    if (openFor) openFor.setAttribute('aria-expanded', 'false');
    openFor = btn;
    btn.setAttribute('aria-expanded', 'true');
    picker.setAttribute('aria-label', btn.getAttribute('aria-label') || 'shortlist');
    fillPicker();
    picker.hidden = false;
    place();
    var first = picker.querySelector('input[type="checkbox"]');
    if (first) first.focus();
  }

  /* @param {boolean} refocus - put focus back on the control (Escape) */
  function closePicker(refocus) {
    if (!picker || picker.hidden) return;
    picker.hidden = true;
    var btn = openFor;
    openFor = null;
    if (btn) {
      btn.setAttribute('aria-expanded', 'false');
      if (refocus) btn.focus();
    }
  }

  function wire() {
    controls().forEach(function (btn) {
      paint(btn);
      btn.setAttribute('aria-haspopup', 'dialog');
      btn.setAttribute('aria-expanded', 'false');
      // The proof that JavaScript ran. See the header.
      btn.hidden = false;
    });
    paintCounts();

    /* One delegated listener on the document, so the handler does not care
       which rows or cards exist when it is attached. A press outside the
       picker closes it; a press on the control it is open under too. */
    document.addEventListener('click', function (ev) {
      var target = ev.target;
      var btn = target.closest && target.closest('.btn-shortlist[data-shortlist-key]');
      if (btn) {
        ev.preventDefault();
        if (openFor === btn) closePicker(false);
        else openPicker(btn);
        return;
      }
      if (picker && !picker.hidden && !(target.closest && target.closest('.shortlist-picker'))) {
        closePicker(false);
      }
    });

    /* Focus leaving the picker for somewhere else on the page closes it. */
    document.addEventListener('focusin', function (ev) {
      if (!picker || picker.hidden) return;
      if (picker.contains(ev.target) || ev.target === openFor) return;
      closePicker(false);
    });

    window.addEventListener('resize', function () {
      if (picker && !picker.hidden) place();
    });

    /* Every change, here or from the index's chooser, keep these or restore,
       repaints every control. A control the index has just hidden (a recipe
       taken off the list on show) takes its picker with it. */
    document.addEventListener(EVENT, function () {
      repaint();
      if (openFor && !openFor.offsetParent) closePicker(false);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wire);
  } else {
    wire();
  }
})();
