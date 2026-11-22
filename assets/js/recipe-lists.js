// recipe-lists.js: a recipe page and the lists it is on (#1521). MANUAL §8.9.
//
// - Opened from a list (`?list=<id>`, the shortlists page's links): a
//   "← Christmas starters" link back to that list's page, and the scaler shows
//   and saves that list's portions, so the two pages edit one number. A
//   `makes:` recipe's list keeps batches and its scaler counts the things
//   made: HTF.listsView converts.
// - Opened any other way: the scaler changes this page only, and a note
//   under it, "in 2 lists", opens the shortlist picker.

(function () {
  'use strict';

  var HTF = window.HTF;
  if (!HTF || !HTF.lists || !HTF.listsView) return;

  var lists = HTF.lists;
  var V = HTF.listsView;
  var button = document.querySelector('.page-actions .btn-shortlist[data-shortlist-key]');
  if (!button) return;
  var key = button.getAttribute('data-shortlist-key');
  var scale = HTF.recipeScale && HTF.recipeScale.scales ? HTF.recipeScale : null;
  var note = document.querySelector('[data-recipe-lists]');

  var listId = (/[?&]list=([a-z0-9]+)/.exec(location.search) || [])[1] || '';

  // The list this page was opened from, while the recipe is still on it.
  function fromList() {
    var list = listId ? lists.get(listId) : null;
    return list && lists.listsWith(key).indexOf(list.id) !== -1 ? list : null;
  }

  function backLink() {
    var list = listId ? lists.get(listId) : null;
    var link = document.querySelector('[data-shortlists-back]');
    var furniture = document.querySelector('.page-furniture');
    if (!list || !link) return;
    link.textContent = '← ' + list.name;
    link.href = V.pageUrl(link.getAttribute('href'), list.id);
    if (furniture) furniture.appendChild(link);
    link.hidden = false;
  }

  /* Built once and rewritten in place: the button may be what the picker is
     open under. */
  var saved = null;
  var open = null;

  function buildNote() {
    saved = document.createElement('span');
    open = document.createElement('button');
    open.type = 'button';
    open.className = 'recipe-lists-open';
    open.setAttribute('aria-haspopup', 'dialog');
    open.setAttribute('aria-expanded', 'false');
    open.addEventListener('click', function () {
      if (HTF.shortlistPicker) HTF.shortlistPicker.toggle(button, open);
    });
    note.appendChild(saved);
    note.appendChild(open);
  }

  function paintNote() {
    if (!note) return;
    if (!open) buildNote();
    var list = fromList();
    saved.textContent = list ? 'Saved on ' + list.name + '.' : '';
    saved.hidden = !list;
    var text = list ? '' : V.inListsText(lists.listsWith(key).length);
    open.textContent = text;
    open.hidden = !text;
    note.hidden = !list && !text;
  }

  // The list's number into the scaler, and every change back out to the list.
  var writing = false;
  function showListNumber() {
    var list = fromList();
    if (!scale || !list) return;
    var stored = lists.portions(list.id, key);
    if (stored === null) return;
    writing = true;
    scale.set(V.scalerFromPortions(stored, scale));
    writing = false;
  }

  if (scale) {
    scale.onChange(function (n) {
      var list = fromList();
      if (writing || !list) return;
      lists.setPortions(list.id, key, V.portionsFromScaler(n, scale));
    });
  }

  backLink();
  showListNumber();
  paintNote();

  // The picker changed the lists: the note's count, or this list, may have gone.
  document.addEventListener('htf:lists-change', paintNote);

  // Back from the shortlists page, which may have changed the number.
  window.addEventListener('pageshow', function (ev) {
    if (!ev.persisted) return;
    lists.refresh();
    showListNumber();
    paintNote();
  });
})();
