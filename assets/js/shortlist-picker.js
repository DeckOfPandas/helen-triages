// shortlist-picker.js: every `.btn-shortlist`, the picker it opens and the
// "adding to" mode (#1521). MANUAL §8.9. The lists are HTF.lists; the words
// are HTF.listsView's; the markup is _includes/shortlist-picker.html's.
//
// - A button reads "+ shortlist", or "✓ 2 lists", and opens the picker: a
//   tick box per list, "+ new list" (made with this recipe on it) and the
//   way to the shortlists page. With no lists yet, one tap makes "Shortlist"
//   with the recipe on it, so the first shortlisting is as quick as ever.
// - `?into=<list id>`: a bar says which list is being filled, each button
//   ticks the recipe on or off that list in one tap, a chevron beside it
//   still opens the picker, and recipe links carry the mode on.
// - Buttons ship `hidden` and are revealed here: a control that silently
//   fails is worse than none. Site-agnostic: `data-portions` on a button is
//   what a recipe starts at on a list.

(function () {
  'use strict';

  var HTF = window.HTF;
  if (!HTF || !HTF.lists || !HTF.listsView) return;

  var lists = HTF.lists;
  var V = HTF.listsView;
  var FIRST_LIST = 'Shortlist';

  function all(selector, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(selector));
  }

  function controls() {
    return all('.btn-shortlist[data-shortlist-key]');
  }

  var live = document.querySelector('[data-shortlist-live]');
  function announce(text) {
    if (!live) return;
    live.textContent = '';
    setTimeout(function () { live.textContent = text; }, 50);
  }

  function titleOf(btn) {
    return btn.getAttribute('data-shortlist-title') || 'this recipe';
  }

  function portionsOf(btn) {
    return Number(btn.getAttribute('data-portions')) || 1;
  }

  // --- adding to one list ----------------------------------------------------

  var intoId = (/[?&]into=([a-z0-9]+)/.exec(location.search) || [])[1] || '';
  function intoList() {
    return intoId ? lists.get(intoId) : null;
  }

  // --- painting ------------------------------------------------------------------

  function paint(btn) {
    var key = btn.getAttribute('data-shortlist-key');
    var on = lists.listsWith(key);
    var into = intoList();
    var words = V.buttonWords(on.length, into && { name: into.name, on: on.indexOf(into.id) !== -1 });
    btn.textContent = '';
    var word = document.createElement('span');
    word.className = 'btn-shortlist-word';
    word.textContent = words.word;
    btn.appendChild(word);
    btn.classList.toggle('is-on', words.on);
    var title = titleOf(btn);
    if (into) {
      btn.setAttribute('aria-pressed', words.on ? 'true' : 'false');
      btn.setAttribute('aria-label', 'on ' + into.name + ': ' + title);
      btn.removeAttribute('aria-haspopup');
      btn.removeAttribute('aria-expanded');
    } else {
      btn.removeAttribute('aria-pressed');
      btn.setAttribute('aria-label', on.length
        ? title + ', on ' + words.word + ': choose lists' : 'shortlist ' + title);
      btn.setAttribute('aria-haspopup', 'dialog');
      if (!btn.hasAttribute('aria-expanded')) btn.setAttribute('aria-expanded', 'false');
    }
  }

  function paintLinks() {
    var count = lists.all().length;
    all('[data-shortlists-link]').forEach(function (link) {
      link.textContent = V.linkText(count);
    });
  }

  // Every list change ends here; `htf:lists-change` tells the rest of the page.
  function repaint() {
    controls().forEach(paint);
    paintLinks();
    if (picker && !picker.hidden) fillPicker();
    document.dispatchEvent(new CustomEvent('htf:lists-change'));
  }

  // --- the picker ------------------------------------------------------------------
  // One element for the page, cloned from the template and placed under
  // whichever control opened it.

  var template = document.getElementById('shortlist-picker-template');
  var picker = null;
  var openFor = null;
  var opener = null;
  var form, input, problem, newBtn;

  function buildPicker() {
    if (!template || !template.content) return false;
    picker = template.content.firstElementChild.cloneNode(true);
    picker.hidden = true;
    form = picker.querySelector('.shortlist-picker-form');
    input = picker.querySelector('.shortlist-picker-name');
    problem = picker.querySelector('.shortlists-name-problem');
    newBtn = picker.querySelector('.shortlist-picker-new');
    input.maxLength = lists.NAME_MAX;

    picker.querySelector('.shortlist-picker-close').addEventListener('click', function () {
      closePicker(true);
    });

    picker.querySelector('.shortlist-picker-lists').addEventListener('change', function (ev) {
      var box = ev.target;
      var id = box.getAttribute('data-list');
      if (!openFor || !id) return;
      lists.setMember(id, openFor.getAttribute('data-shortlist-key'), box.checked, portionsOf(openFor));
      announce((box.checked ? 'Added to ' : 'Taken off ') + lists.get(id).name + '.');
      repaint();
    });

    newBtn.addEventListener('click', function () {
      showForm(true);
      input.value = '';
      input.focus();
    });

    picker.querySelector('.shortlist-picker-cancel').addEventListener('click', function () {
      showForm(false);
      newBtn.focus();
    });

    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      if (!openFor) return;
      var made = lists.create(input.value);
      if (made.error) {
        problem.textContent = V.nameProblemText(made.error, lists.core.cleanName(input.value), lists.all());
        input.focus();
        return;
      }
      lists.setMember(made.id, openFor.getAttribute('data-shortlist-key'), true, portionsOf(openFor));
      showForm(false);
      repaint();
      announce('Made ' + lists.get(made.id).name + ', with ' + titleOf(openFor) + ' on it.');
      var box = picker.querySelector('input[data-list="' + made.id + '"]');
      if (box) box.focus();
    });

    // On the document: Safari leaves focus on the page when a label is tapped.
    document.addEventListener('keydown', function (ev) {
      if (ev.key !== 'Escape' || picker.hidden) return;
      ev.preventDefault();
      if (!form.hidden) { showForm(false); newBtn.focus(); return; }
      closePicker(true);
    });

    document.body.appendChild(picker);
    return true;
  }

  function showForm(on) {
    form.hidden = !on;
    newBtn.hidden = on;
    newBtn.setAttribute('aria-expanded', on ? 'true' : 'false');
    problem.textContent = '';
  }

  // Redrawn whole, so a box that had focus gets it back.
  function fillPicker() {
    var key = openFor.getAttribute('data-shortlist-key');
    var on = lists.listsWith(key);
    var ul = picker.querySelector('.shortlist-picker-lists');
    var focused = ul.contains(document.activeElement) ? document.activeElement.getAttribute('data-list') : '';
    ul.textContent = '';
    lists.all().forEach(function (list) {
      var li = document.createElement('li');
      li.className = 'shortlist-picker-list';
      var label = document.createElement('label');
      var box = document.createElement('input');
      box.type = 'checkbox';
      box.setAttribute('data-list', list.id);
      box.checked = on.indexOf(list.id) !== -1;
      var name = document.createElement('span');
      name.className = 'shortlist-list-name';
      name.textContent = list.name;
      label.appendChild(box);
      label.appendChild(name);
      li.appendChild(label);
      ul.appendChild(li);
      if (list.id === focused) box.focus();
    });
  }

  // Under what opened it (the button, or its chevron), right edges level,
  // kept on screen.
  function place() {
    var rect = opener.getBoundingClientRect();
    var width = picker.offsetWidth;
    var gutter = 8;
    var left = Math.max(gutter, Math.min(rect.right - width, document.documentElement.clientWidth - width - gutter));
    picker.style.left = (left + window.pageXOffset) + 'px';
    picker.style.top = (rect.bottom + window.pageYOffset + 6) + 'px';
  }

  // `btn` is the recipe's button; `anchor` what was pressed, if its chevron.
  function openPicker(btn, anchor) {
    if (!picker && !buildPicker()) return;
    if (openFor) closePicker(false);
    openFor = btn;
    opener = anchor || btn;
    opener.setAttribute('aria-expanded', 'true');
    var title = titleOf(btn);
    picker.setAttribute('aria-label', 'Lists for ' + title);
    picker.querySelector('.shortlist-picker-title').textContent = title;
    showForm(false);
    fillPicker();
    picker.hidden = false;
    place();
    (picker.querySelector('input[type="checkbox"]') || newBtn).focus();
  }

  function closePicker(refocus) {
    if (!picker || picker.hidden) return;
    picker.hidden = true;
    openFor = null;
    if (opener) {
      opener.setAttribute('aria-expanded', 'false');
      if (refocus) opener.focus();
    }
    opener = null;
  }

  // --- a press --------------------------------------------------------------------

  function press(btn) {
    var key = btn.getAttribute('data-shortlist-key');
    var into = intoList();
    if (into) {
      var on = lists.listsWith(key).indexOf(into.id) === -1;
      lists.setMember(into.id, key, on, portionsOf(btn));
      repaint();
      announce((on ? 'Added to ' : 'Taken off ') + into.name + '.');
      return;
    }
    if (!lists.all().length) {
      var made = lists.create(FIRST_LIST);
      lists.setMember(made.id, key, true, portionsOf(btn));
      repaint();
      announce('Added to a new list, ' + FIRST_LIST + '.');
      return;
    }
    if (opener === btn) closePicker(false);
    else openPicker(btn);
  }

  // --- the "adding to" bar and its chevrons ------------------------------------------

  function wireInto() {
    var into = intoList();
    if (!into) return;
    var barTemplate = document.getElementById('shortlist-into-template');
    var main = document.querySelector('main');
    if (barTemplate && barTemplate.content && main) {
      var bar = barTemplate.content.firstElementChild.cloneNode(true);
      bar.querySelector('.shortlist-into-name').textContent = into.name;
      bar.querySelector('.shortlist-into-done').addEventListener('click', function () {
        lists.setView(into.id);
      });
      main.insertBefore(bar, main.firstChild);
    }
    controls().forEach(function (btn) {
      var more = document.createElement('button');
      more.type = 'button';
      more.className = 'btn-shortlist-more';
      more.setAttribute('aria-label', 'choose lists for ' + titleOf(btn));
      more.setAttribute('aria-haspopup', 'dialog');
      more.setAttribute('aria-expanded', 'false');
      btn.parentNode.insertBefore(more, btn.nextSibling);
    });
    all('a.recipe-title-link').forEach(function (link) {
      var href = link.getAttribute('href') || '';
      if (href && !/[?&]into=/.test(href)) {
        link.setAttribute('href', href.replace(/(#.*)?$/, V.intoUrl('', into.id) + '$1'));
      }
    });
  }

  // For another control that opens and closes a button's picker (recipe-lists.js).
  HTF.shortlistPicker = {
    toggle: function (btn, anchor) {
      if (opener === anchor) closePicker(false);
      else openPicker(btn, anchor);
    }
  };

  function wire() {
    wireInto();
    controls().forEach(function (btn) {
      paint(btn);
      btn.hidden = false;
    });
    paintLinks();

    document.addEventListener('click', function (ev) {
      var target = ev.target;
      var more = target.closest && target.closest('.btn-shortlist-more');
      if (more) {
        ev.preventDefault();
        var owner = more.previousElementSibling;
        if (opener === more) closePicker(false);
        else openPicker(owner, more);
        return;
      }
      var btn = target.closest && target.closest('.btn-shortlist[data-shortlist-key]');
      if (btn) {
        ev.preventDefault();
        press(btn);
        return;
      }
      if (picker && !picker.hidden && !picker.contains(target) &&
          !(opener && opener.contains(target))) closePicker(false);
    });

    document.addEventListener('focusin', function (ev) {
      if (!picker || picker.hidden) return;
      if (picker.contains(ev.target) || ev.target === opener) return;
      closePicker(false);
    });

    window.addEventListener('resize', function () {
      if (picker && !picker.hidden) place();
    });

    // Back from another page, which may have changed the lists.
    window.addEventListener('pageshow', function (ev) {
      if (!ev.persisted) return;
      lists.refresh();
      repaint();
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wire);
  } else {
    wire();
  }
})();
