// shortlist-lists.js
// The index's list chooser (#1521): which list the shortlist view shows,
// rename and delete beside it, and "+ new list" under it. One script for both indexes; it finds
// `[data-shortlist-lists]` (_includes/shortlist-lists.html). MANUAL §8.9.
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
  var select = root.querySelector('[data-shortlist-lists-select]');
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

  /* The options, each "name (N)", and the active one chosen. */
  function paint() {
    var active = store.activeId();
    select.textContent = '';
    store.lists().forEach(function (list) {
      var option = document.createElement('option');
      option.value = list.id;
      option.textContent = list.name + ' (' + list.count + ')';
      option.selected = list.id === active;
      select.appendChild(option);
    });
  }

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
    actions.hidden = false;
    newRow.hidden = false;
  }

  select.addEventListener('change', function () {
    if (store.setActive(select.value)) announce();
  });

  root.addEventListener('click', function (ev) {
    var btn = ev.target.closest && ev.target.closest('[data-shortlist-lists-action]');
    if (!btn) return;
    var action = btn.dataset.shortlistListsAction;
    if (action === 'new' || action === 'rename') { openForm(action); return; }
    if (action === 'cancel') { closeForm(); select.focus(); return; }
    if (action === 'delete') {
      var name = store.activeName();
      // Helen's ruling (#1521): deleting a list asks first.
      if (!window.confirm('Delete the list "' + name + '"? This cannot be undone.')) return;
      store.remove(store.activeId());
      announce();
      select.focus();
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
    select.focus();
  });

  form.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape') { ev.preventDefault(); closeForm(); select.focus(); }
  });

  input.maxLength = store.NAME_MAX;
  paint();
  document.addEventListener('htf:shortlist-change', paint);
})();
