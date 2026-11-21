// shortlist-lists.js
// The index's list chooser (#1521): a button and its menu choosing which list
// the shortlist view shows, rename and delete beside it, and "+ new list"
// under it. One script for both indexes; it finds `[data-shortlist-lists]`
// (_includes/shortlist-lists.html). MANUAL §8.9.
//
// It changes the store and dispatches `htf:shortlist-change`; each index
// repaints from that, as it does for a + press. Whether the chooser shows is
// the index's call: it is part of your own shortlist view, so filters.js and
// cocktail-index.js unhide it in syncShortlistOnly().

(function () {
  'use strict';

  var HTF = window.HTF;
  if (!HTF || !HTF.shortlist || !HTF.site) return;

  var root = document.querySelector('[data-shortlist-lists]');
  if (!root) return;

  var store = HTF.shortlist;
  var toggle = root.querySelector('[data-shortlist-lists-toggle]');
  var current = root.querySelector('[data-shortlist-lists-current]');
  var menu = root.querySelector('[data-shortlist-lists-menu]');
  var options = root.querySelector('[data-shortlist-lists-options]');
  var form = root.querySelector('[data-shortlist-lists-form]');
  var input = root.querySelector('[data-shortlist-lists-name]');
  var error = root.querySelector('[data-shortlist-lists-error]');
  var actions = root.querySelector('[data-shortlist-lists-actions]');
  var newRow = root.querySelector('[data-shortlist-lists-new-row]');
  var mode = null;   // 'new' or 'rename' while the form is open

  function announce() {
    document.dispatchEvent(new CustomEvent('htf:shortlist-change', {
      detail: { key: null, on: false, list: store.activeId() }
    }));
  }

  function option(value, text, chosen, extra) {
    var item = document.createElement('li');
    item.className = 'shortlist-picker-list' + (extra ? ' ' + extra : '');
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'shortlist-lists-option';
    btn.dataset.shortlistListsId = value;
    if (chosen) btn.setAttribute('aria-current', 'true');
    var name = document.createElement('span');
    name.className = value === store.ALL ? 'shortlist-lists-all-name' : 'shortlist-list-name';
    name.textContent = text;
    btn.appendChild(name);
    item.appendChild(btn);
    options.appendChild(item);
    return text;
  }

  /* One row per list, "name (N)", then SEE ALL (N) under a rule: every
     recipe on any list, once. The button names the active one. Rename and
     delete have no list to act on in SEE ALL, so they hide. */
  function paint() {
    var active = store.activeId();
    options.textContent = '';
    var shown = '';
    store.lists().forEach(function (list) {
      var text = option(list.id, list.name + ' (' + list.count + ')', list.id === active);
      if (list.id === active) shown = text;
    });
    var all = option(store.ALL, 'SEE ALL (' + store.total() + ')', active === store.ALL, 'shortlist-lists-all');
    if (active === store.ALL) shown = all;
    current.textContent = shown;
    current.className = active === store.ALL ? 'shortlist-lists-all-name' : 'shortlist-list-name';
    actions.hidden = !!mode || active === store.ALL;
  }

  function rows() {
    return Array.prototype.slice.call(options.querySelectorAll('.shortlist-lists-option'));
  }

  function openMenu() {
    menu.hidden = false;
    toggle.setAttribute('aria-expanded', 'true');
    var chosen = options.querySelector('[aria-current="true"]') || rows()[0];
    if (chosen) chosen.focus();
  }

  function closeMenu(refocus) {
    if (menu.hidden) return;
    menu.hidden = true;
    toggle.setAttribute('aria-expanded', 'false');
    if (refocus) toggle.focus();
  }

  toggle.addEventListener('click', function () {
    if (menu.hidden) openMenu(); else closeMenu(true);
  });

  menu.addEventListener('click', function (ev) {
    if (ev.target.closest('[data-shortlist-lists-close]')) { closeMenu(true); return; }
    var row = ev.target.closest('.shortlist-lists-option');
    if (!row) return;
    closeMenu(true);
    if (store.setActive(row.dataset.shortlistListsId)) announce();
  });

  // Up and down walk the rows; Escape closes, back on the button.
  menu.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape') { ev.preventDefault(); closeMenu(true); return; }
    if (ev.key !== 'ArrowDown' && ev.key !== 'ArrowUp') return;
    ev.preventDefault();
    var list = rows();
    var at = list.indexOf(document.activeElement);
    var next = ev.key === 'ArrowDown' ? at + 1 : at - 1;
    list[(next + list.length) % list.length].focus();
  });

  document.addEventListener('click', function (ev) {
    if (!menu.hidden && !ev.target.closest('.shortlist-lists-choose')) closeMenu(false);
  });

  document.addEventListener('focusin', function (ev) {
    if (!menu.hidden && !ev.target.closest('.shortlist-lists-choose')) closeMenu(false);
  });

  function openForm(which) {
    mode = which;
    form.hidden = false;
    actions.hidden = true;
    newRow.hidden = true;
    error.hidden = true;
    input.value = which === 'rename' ? store.activeName() : '';
    input.setAttribute('aria-label', which === 'rename' ? 'New name for this list' : 'Name for the new list');
    input.focus();
    if (which === 'rename' && input.select) input.select();
  }

  function closeForm() {
    mode = null;
    form.hidden = true;
    actions.hidden = store.activeId() === store.ALL;
    newRow.hidden = false;
  }

  root.addEventListener('click', function (ev) {
    var btn = ev.target.closest && ev.target.closest('[data-shortlist-lists-action]');
    if (!btn) return;
    var action = btn.dataset.shortlistListsAction;
    if (action === 'new' || action === 'rename') { openForm(action); return; }
    if (action === 'cancel') { closeForm(); toggle.focus(); return; }
    if (action === 'delete') {
      var name = store.activeName();
      // Helen's ruling (#1521): deleting a list asks first.
      if (!window.confirm('Delete the list "' + name + '"? This cannot be undone.')) return;
      store.remove(store.activeId());
      announce();
      toggle.focus();
    }
  });

  form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    var name = store.cleanName(input.value);
    if (!name) { input.focus(); return; }
    var exceptId = mode === 'rename' ? store.activeId() : undefined;
    if (!store.nameFree(name, exceptId)) {
      error.textContent = 'There is already a list called ' + name + '.';
      error.hidden = false;
      input.focus();
      return;
    }
    if (mode === 'rename') {
      store.rename(store.activeId(), name);
    } else {
      store.setActive(store.create(name));
    }
    closeForm();
    announce();
    toggle.focus();
  });

  form.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape') { ev.preventDefault(); closeForm(); toggle.focus(); }
  });

  input.maxLength = store.NAME_MAX;
  paint();
  /* Again once the index has read its address: `?shortlist=all` sets SEE ALL
     in a DOMContentLoaded handler registered before this one. */
  document.addEventListener('DOMContentLoaded', paint);
  document.addEventListener('htf:shortlist-change', paint);
})();
