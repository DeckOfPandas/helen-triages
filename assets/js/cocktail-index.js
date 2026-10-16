/* Cocktails index: DOM wiring only (#579). Everything is already in the DOM,
   so this toggles [hidden] and reorders the list in place. No fetch.

   The pure parts live elsewhere and are tested there: cocktail-search.js (the
   pool, ranking, families, the two matching rules), filter-state.js
   (COCKTAIL_FIELDS) and ingredient-search.js (fold, orderByBand).

   Nothing is parsed out of rendered markup: every fact a filter needs is a
   data- attribute written by cocktails/index.html, so restyling a card cannot
   break a filter (#501).

   How the axes combine (#478, #479): moods are OR, ranked by how many match;
   include chips are AND; sections are ANDed with each other. Each card gets a
   random sort key once per page load and filtering re-ranks against it, so
   cards do not jump while you type. */
(function () {
  /* The list's own items, not everything wearing a card class. */
  var cards = Array.prototype.slice.call(document.querySelectorAll('.drink-cards > li'));
  if (!cards.length) return;

  /* Pagination (#694). The arithmetic is HTF.listView.paginate, shared with
     filters.js, so the two indexes agree on what a page is. */
  var PAGE_SIZE = 20;
  var currentPage = 1;
  var showAll = false;

  var pagination = document.querySelector('.drink-pagination');
  var pagePrevBtn = document.getElementById('drink-page-prev');
  var pageNextBtn = document.getElementById('drink-page-next');
  var pageStatusEl = document.getElementById('drink-page-status');
  var pageSeeAllBtn = document.getElementById('drink-page-see-all');

  var CS = HTF.cocktailSearch;
  var FAMILY_SUFFIX = CS.FAMILY_SUFFIX;
  // The same fold the search compares with, so picker and matcher agree on
  // accents.
  var fold = HTF.ingredientSearch.fold;

  /* The vocabulary is _data/cocktails/ingredients.yml, emitted as JSON by
     cocktails/index.html; families and thresholds are edited there. Without
     the block the page still searches, it just offers no (all) buttons. */
  function readJson(id, what, fallback) {
    var node = document.getElementById(id);
    if (!node) {
      console.warn(
        'cocktail-index.js: no #' + id + ' block found. cocktails/index.html ' +
        'should emit ' + what + ' as JSON before loading this script.'
      );
      return fallback;
    }
    try {
      return JSON.parse(node.textContent);
    } catch (e) {
      console.warn('cocktail-index.js: could not parse #' + id + ' — ' + e.message);
      return fallback;
    }
  }

  var VOCABULARY = (function () {
    var fallback = { search: { min_query_chars: 2, family_button_min_chars: 3 },
                     families: [], family_of: {}, card_names: {} };
    var parsed = readJson('drink-vocabulary', '_data/cocktails/ingredients.yml', fallback);
    parsed.search = parsed.search || fallback.search;
    parsed.families = parsed.families || [];
    parsed.family_of = parsed.family_of || {};
    parsed.card_names = parsed.card_names || {};
    return parsed;
  })();

  /* The bottle dictionary (#529). Absent, the pool still works but two
     spellings of one bottle stop collapsing. */
  var BOTTLES = readJson('drink-bottles', '_data/cocktails/bottles.yml',
                         { bottles: {}, unresolved_suggestions: {} });

  var Search = CS.create(VOCABULARY, BOTTLES);

  /* What each drink is made of, for the shopping list (#546). Keyed by the
     `drink.url` the cards carry as `data-url` and the shortlist stores. */
  var INGREDIENTS = readJson('drink-ingredients', 'the drinks’ own front matter', {});

  /* `top_up_ml` from costs.yml (#746): how much a `to top` is. Absent, every
     `to top` is counted rather than measured. */
  var TOP_UPS = readJson('drink-top-ups', '_data/cocktails/costs.yml', {});

  /* What each drink costs a glass. Emitted only behind `site.show_costs`
     (local builds), so absent is the normal state: read without `readJson`,
     which would warn on every production page load. */
  var COSTS = (function () {
    var node = document.getElementById('drink-costs');
    if (!node) return {};
    try {
      return JSON.parse(node.textContent);
    } catch (e) {
      console.warn('cocktail-index.js: could not parse #drink-costs — ' + e.message);
      return {};
    }
  })();

  /* GBP per litre per generic and per bottle (#820). Local-only like COSTS;
     `null` rather than `{}` so shopping-list.js can tell "no table" from an
     empty one. */
  var RATES = (function () {
    var node = document.getElementById('drink-rates');
    if (!node) return null;
    try {
      return JSON.parse(node.textContent);
    } catch (e) {
      console.warn('cocktail-index.js: could not parse #drink-rates — ' + e.message);
      return null;
    }
  })();

  /* Which bottle is picked for which ingredient, per drink (#818): url ->
     generic -> bottle name. In memory only, on purpose: a stored choice
     outlives the bottle it names. */
  var CHOSEN = {};

  function chosenBottle(url, generic) {
    return (CHOSEN[url] || {})[generic] || null;
  }

  /* What one glass costs after any choice (#818). Each choosable entry carries
     what it contributes to the range (`lo`, `hi`) and what each candidate
     bottle costs, so a choice is total - contribution + bottle price. Unchosen
     entries keep the full range. */
  function costFor(url) {
    var c = COSTS[url];
    if (!c) return null;
    var lo = Number(c.lo);
    var hi = Number(c.hi);
    (c.choices || []).forEach(function (choice) {
      var bottle = chosenBottle(url, choice.generic);
      if (!bottle) return;
      var price = choice.bottles[bottle];
      if (typeof price !== 'number') return;
      lo = lo - Number(choice.lo) + price;
      hi = hi - Number(choice.hi) + price;
    });
    return { lo: lo, hi: hi };
  }

  /* " @ £2.34", or a range, or nothing. Per glass, never multiplied by the
     count: it is the figure the drink's own page shows. */
  function costSuffix(url) {
    var c = costFor(url);
    if (!c) return '';
    var lo = '£' + Number(c.lo).toFixed(2);
    if (Math.abs(c.hi - c.lo) < 0.005) return ' @ ' + lo;
    return ' @ ' + lo + '–£' + Number(c.hi).toFixed(2);
  }

  /* One row of radios per ingredient that has a choice (#818). The group
     `name` must include the URL, or two shortlisted drinks wanting the same
     generic share one group and choosing for one unchooses the other. */
  function choiceRows(url) {
    var c = COSTS[url];
    if (!c || !c.choices || !c.choices.length) return '';
    return c.choices.map(function (choice, i) {
      var group = 'bottle-' + i + '-' + url;
      var options = Object.keys(choice.bottles).map(function (bottle) {
        var id = group + '-' + bottle;
        return '<label class="shopping-list-bottle-choice">' +
          '<input type="radio" name="' + HTF.escapeHtml(group) + '"' +
          ' value="' + HTF.escapeHtml(bottle) + '"' +
          ' data-url="' + HTF.escapeHtml(url) + '"' +
          ' data-generic="' + HTF.escapeHtml(choice.generic) + '"' +
          (chosenBottle(url, choice.generic) === bottle ? ' checked' : '') +
          ' aria-label="' + HTF.escapeHtml(bottle) + '">' +
          '<span>' + HTF.escapeHtml(bottle) + '</span>' +
          '</label>';
      }).join('');
      return '<span class="shopping-list-choice">' +
        '<span class="shopping-list-choice-name">' +
        HTF.escapeHtml(choice.generic) + '</span>' +
        options +
        '</span>';
    }).join('');
  }

  /* Every declared bottle name maps to itself and every alias to its bottle,
     so the shopping list prints one line per bottle however it was written. */
  var BOTTLE_ALIASES = (function () {
    var map = {};
    var declared = (BOTTLES && BOTTLES.bottles) || {};
    var names = Object.keys(declared);
    function fold(name) { return HTF.shoppingList.foldKey(name); }

    /* Aliases first, then declared names over the top: a declared bottle name
       must always win over another bottle's alias. */
    names.forEach(function (name) {
      ((declared[name] || {}).aliases || []).forEach(function (alias) {
        if (!map[fold(alias)]) map[fold(alias)] = name;
      });
    });
    names.forEach(function (name) { map[fold(name)] = name; });
    return map;
  })();

  /* One state object (#579). Fields, cleared values and "is anything set" all
     come from COCKTAIL_FIELDS in filter-state.js. clearAll() reassigns it
     whole, which is why controls are painted from state in apply(). */
  var FilterState = HTF.filterState.create(HTF.filterState.COCKTAIL_FIELDS);
  var state = FilterState.emptyState();

  /* Off the module, not the FilterState binding: `create(spec)` returns only
     the spec-bound functions, so `FilterState.arrivedByGoingBack` is undefined
     and calling it kills the rest of startup.
     test_a_filter_state_binding_is_only_asked_for_what_it_has checks this. */
  var arrivedByGoingBack = HTF.filterState.arrivedByGoingBack;

  var moodBtns  = Array.prototype.slice.call(document.querySelectorAll('.btn-mood'));
  var chaosBtns = Array.prototype.slice.call(document.querySelectorAll('.btn-chaos'));
  var incInput  = document.getElementById('drink-include');
  var excInput  = document.getElementById('drink-exclude');
  var incPool   = document.getElementById('drink-include-pool');
  var excPool   = document.getElementById('drink-exclude-pool');
  var countEl   = document.getElementById('drink-count-n');
  var wordEl    = document.getElementById('drink-count-word');
  var noneEl    = document.querySelector('.drink-none');
  var nameInput = document.getElementById('drink-name');
  var filters   = document.querySelector('.drink-filters');
  var list      = cards[0].parentNode;

  /* The shortlisted-only button (#546) sits on the count line, not in
     `.drink-filters`: it is about this browser, not about what a drink is. */
  var shortlistOnlyBtn = document.getElementById('shortlist-only');

  /* Hide drafts (#1358). The button exists only on a `show_drafts` build, so
     on the deployed index this is null. Not a field of `state`: clear-all does
     not reset it and nothing remembers it across a load. */
  var draftsBtn = document.getElementById('drafts-toggle');
  var hideDrafts = false;

  /* A shortlist someone sent (#1093, `?shortlist=slug,slug`): shown through
     the ordinary shortlist view, saved nowhere until "keep these", and
     dropped by apply() the moment the view goes. null when none is showing. */
  var sharedKeys = null;
  var sharedUnmatched = [];
  var sharedNote = document.querySelector('[data-shared-shortlist]');

  // Declared here rather than beside the code that builds them, so apply() can
  // never read them before they exist. Populated further down.
  var clearAllButtons = [];
  var redrawPool = {};

  /* Mood and hassle are one filter with two headings: both render .btn-mood
     and write into `state.moods`. Only the clear links are per-section, told
     apart by which block a button sits in. */
  function inHassle(btn) {
    return !!btn.closest('.drink-filter--hassle');
  }

  function moodBtnsIn(hassle) {
    return moodBtns.filter(function (b) { return inHassle(b) === hassle; });
  }

  /* Everything each card needs, read once. Ingredients are split here, so a
     query can never match across the `|` between two of them. */
  var model = cards.map(function (card) {
    var nameEl = card.querySelector('.drink-card-name a');
    return {
      card: card,
      entries: CS.splitEntries(card.dataset.ingredients),
      moods: (card.dataset.moods || '').split('|').filter(Boolean),
      name: card.dataset.name || '',
      chaos: card.dataset.chaos || '',
      /* A string, not a boolean (#732): `dataset` gives 'false', which is
         truthy. matches() compares against 'false'. */
      madeBefore: card.dataset.madeBefore || '',
      draft: card.classList.contains('drink-card--draft'),
      /* The shortlist's key (#546). Whether it is shortlisted is asked in
         matches(), because that can change under the page. */
      url: card.dataset.url || '',
      key: Math.random(),
      nameEl: nameEl,
      /* The unmarked title. The highlight rebuilds from this, never from the
         link's current text, so repainting does not compound. */
      title: nameEl ? nameEl.textContent : '',
      moodEls: Array.prototype.slice.call(card.querySelectorAll('.drink-card-mood')),
      ingEls: Array.prototype.slice.call(card.querySelectorAll('.drink-card-ing')).map(function (el) {
        return { el: el, entries: CS.splitEntries(el.dataset.ing) };
      })
    };
  });

  /* One group per ingredient, from data-ing: only that keeps a suggested
     bottle paired with its generic, which buildPool needs. */
  var pool = Search.buildPool(model.reduce(function (groups, d) {
    d.ingEls.forEach(function (ing) { groups.push(ing.el.dataset.ing); });
    return groups;
  }, []));

  function chosen(field) {
    var out = [];
    state[field].forEach(function (v) { out.push(v); });
    return out;
  }

  /* The two chip lists, flattened once per pass; apply() refreshes them. */
  var activeInclude = [];
  var activeExclude = [];

  /* How many of the selected moods this drink has; 0 when none is selected. */
  function moodScore(d) {
    if (!state.moods.size) return 0;
    var n = 0;
    d.moods.forEach(function (m) { if (state.moods.has(m)) n++; });
    return n;
  }

  /* Which mood values belong to which section (#695), read once from the
     buttons. `state.moods` holds both sections' selections, so moodScore alone
     cannot tell "answers both questions" from "answers one twice". */
  var MOOD_VALUES = null;
  var HASSLE_VALUES = null;

  function sectionValues() {
    if (MOOD_VALUES) return;
    MOOD_VALUES = {};
    HASSLE_VALUES = {};
    moodBtnsIn(false).forEach(function (b) { MOOD_VALUES[b.dataset.mood] = true; });
    moodBtnsIn(true).forEach(function (b) { HASSLE_VALUES[b.dataset.mood] = true; });
  }

  /* How many of the two mood sections this drink answers (#695). It changes
     the order only when both sections are asked. The other filters all narrow,
     so every survivor scores the same on them and they are not counted. */
  function sectionScore(d) {
    if (!state.moods.size) return 0;
    sectionValues();
    var mood = false;
    var hassle = false;
    d.moods.forEach(function (m) {
      if (!state.moods.has(m)) return;
      if (HASSLE_VALUES[m]) hassle = true;
      else if (MOOD_VALUES[m]) mood = true;
    });
    return (mood ? 1 : 0) + (hassle ? 1 : 0);
  }

  function matches(d) {
    if (hideDrafts && d.draft) return false;

    /* Asked of the store, not the model (#546): the shortlist lives in
       localStorage and can change between two calls. */
    if (state.shortlisted && !(sharedKeys
      ? sharedKeys.indexOf(d.url) !== -1
      : HTF.shortlist.has(d.url))) return false;

    /* Moods are OR, ranked below. If this becomes AND, the ranking is
       redundant (#478). */
    if (state.moods.size && moodScore(d) === 0) return false;

    /* `open` is a state, not a filter: it shows every drink. Only `good`
       and `unmade` narrow. */
    if (state.chaos === 'good' && d.chaos !== 'good') return false;

    /* `unmade` (#732) reads `madeBefore`, not `chaos`: `made_before` flips
       when a drink is made, while `ship` stays `who knows` until it is rated. */
    if (state.chaos === 'unmade' && d.madeBefore !== 'false') return false;

    /* Include chips are AND: each one narrows. */
    var i;
    for (i = 0; i < activeInclude.length; i++) {
      if (!Search.matchesInclude(d.entries, activeInclude[i])) return false;
    }
    for (i = 0; i < activeExclude.length; i++) {
      if (Search.matchesExclude(d.entries, activeExclude[i])) return false;
    }

    return Search.matchesName(d.name, state.nameQuery);
  }

  /* Rank order, hidden cards last. Rewritten only when it changes: moving
     every node per keystroke would scroll the page under the reader. */
  function reorder(order) {
    var same = true;
    var kids = list.children;
    for (var i = 0; i < order.length; i++) {
      if (kids[i] !== order[i]) { same = false; break; }
    }
    if (same) return;
    var frag = document.createDocumentFragment();
    order.forEach(function (card) { frag.appendChild(card); });
    list.appendChild(frag);
  }

  /* The matched run of a drink name (#564). Offsets index the original title,
     so a name keeps its accents while an unaccented query still finds it. */
  function paintNameHighlight(d) {
    if (!d.nameEl) return;
    var at = state.nameQuery ? Search.nameHighlight(d.title, state.nameQuery) : null;
    var mark = at ? (at.start + ':' + at.end) : '';
    // Only when it changes, so unhighlighted names are not rewritten on
    // every keystroke.
    if (d.painted === mark) return;
    d.painted = mark;
    if (!at) {
      d.nameEl.textContent = d.title;
      return;
    }
    d.nameEl.innerHTML =
      HTF.escapeHtml(d.title.slice(0, at.start)) +
      '<mark class="drink-name-hit">' + HTF.escapeHtml(d.title.slice(at.start, at.end)) + '</mark>' +
      HTF.escapeHtml(d.title.slice(at.end));
  }

  function showClear(id, active) {
    var el = document.getElementById(id);
    if (el) el.hidden = !active;
  }

  /* --- the shopping list (#546) ---------------------------------------------
     The arithmetic is shopping-list.js. Shown only while the shortlisted
     filter is on, and it reads the store, not the visible cards: a second
     filter narrows the cards, not what you shop for. */
  var shoppingEl = document.getElementById('shopping-list');
  var shoppingItems = shoppingEl && shoppingEl.querySelector('.shopping-list-items');
  // #817. Absent is normal: the paragraph is only useful where prices are.
  var shoppingTotal = shoppingEl && shoppingEl.querySelector('.shopping-list-total');
  var shoppingDrinks = shoppingEl && shoppingEl.querySelector('.shopping-list-drinks');
  var shoppingEmpty = shoppingEl && shoppingEl.querySelector('.shopping-list-empty');
  var setAllInput = document.getElementById('shopping-list-setall');

  /* The card's own unmarked title, so a drink found by a name search still
     lists under its real name. */
  var titleByUrl = (function () {
    var map = {};
    model.forEach(function (d) { if (d.url) map[d.url] = d.title || d.url; });
    return map;
  })();

  /* In the order they were shortlisted, which is the store's insertion order.
     Drinks no longer on the page are dropped. */
  function shortlistedDrinks() {
    return HTF.shortlist.list().filter(function (url) {
      return Object.prototype.hasOwnProperty.call(INGREDIENTS, url);
    });
  }

  function renderShoppingList() {
    if (!shoppingEl) return;
    // Hidden over a shared list (#1093): its numbers write to this browser's
    // store, and a list you were sent is not yours until you keep it.
    shoppingEl.hidden = !state.shortlisted || !!sharedKeys;
    if (shoppingEl.hidden) return;

    var urls = shortlistedDrinks();

    if (shoppingEmpty) shoppingEmpty.hidden = urls.length > 0;

    /* Rebuilt whole. Never call this while one of its own inputs has focus:
       replacing the node loses the caret. Those handlers call renderTotals(). */
    if (shoppingDrinks) {
      shoppingDrinks.innerHTML = urls.map(function (url) {
        return '<li>' +
          '<input type="number" class="shopping-list-glasses" min="1" max="99" step="1" ' +
          'inputmode="numeric" value="' + HTF.shortlist.glasses(url) + '" ' +
          'data-url="' + HTF.escapeHtml(url) + '" ' +
          'aria-label="glasses of ' + HTF.escapeHtml(titleByUrl[url] || url) + '">' +
          '<span>' + HTF.escapeHtml(titleByUrl[url] || url) +
          /* Inside the title span so the price wraps with the name. */
          '<span class="shopping-list-cost">' + costSuffix(url) + '</span>' +
          '</span>' +
          // #818. After the name, indented, one row per pour with a choice.
          choiceRows(url) +
          '</li>';
      }).join('');
    }

    renderTotals(urls);
  }

  function renderTotals(urls) {
    if (!shoppingItems) return;

    var entries = [];
    (urls || shortlistedDrinks()).forEach(function (url) {
      var glasses = HTF.shortlist.glasses(url);
      (INGREDIENTS[url] || []).forEach(function (ing) {
        /* A chosen bottle replaces the suggestion on the entry (#818), which
           fixes both the price and the bracketed note downstream. The generic
           is joined as the plugin joins a list generic (#441), so the key
           matches on both sides. */
        var generic = Array.isArray(ing.g) ? ing.g.join(' or ') : ing.g;
        var picked = chosenBottle(url, generic);
        entries.push({
          amount: ing.a,
          generic: ing.g,
          bottle: picked || ing.b,
          glasses: glasses
        });
      });
    });

    var rows = HTF.shoppingList.build(entries, {
      // The cards' own list, not a second copy -- `not_on_cards: ['water']`.
      exclude: VOCABULARY.not_on_cards || [],
      bottleAliases: BOTTLE_ALIASES,
      // Declared in the same file, for the four juices you squeeze yourself.
      juiceYields: VOCABULARY.juice_yields || {},
      // #746: champagne, prosecco and soda water declare what a top pours, so
      // the list can say a volume instead of counting tops.
      topUpMl: TOP_UPS,
      // #820. Absent on the deployed site, where no row carries a price.
      rates: RATES,
      // #848: shelf order first, then volume within a shelf. Both halves come
      // from the vocabulary already on the page, so this needs no new block.
      shelves: {
        order: VOCABULARY.shopping_shelves || [],
        of: VOCABULARY.shelf_of || {}
      }
    });

    shoppingItems.innerHTML = rows.map(function (row) {
      /* Bottle and fruit count share one bracket, as two spans: only the
         bottle is coloured (`.shopping-list-bottle`). */
      var suffix = '';
      if (row.note || row.fruit) {
        var inner = [];
        if (row.note) {
          inner.push('<span class="shopping-list-bottle">' +
            HTF.escapeHtml(row.note) + '</span>');
        }
        if (row.fruit) {
          inner.push('<span class="shopping-list-fruit">' +
            HTF.escapeHtml(row.fruit.text) + '</span>');
        }
        suffix = ' <span class="shopping-list-note">(' + inner.join(', ') + ')</span>';
      }
      /* The price (#820) is its own span because it is absent on the deployed
         site. A row with no rate prints nothing, never a zero. */
      var price = row.price
        ? '<span class="shopping-list-price">' + HTF.escapeHtml(row.price.text) + '</span>'
        : '';

      return '<li>' +
        '<span class="shopping-list-amount">' + HTF.escapeHtml(row.text) + '</span>' +
        '<span class="shopping-list-name">' + HTF.escapeHtml(row.label) + suffix + '</span>' +
        price +
        '</li>';
    }).join('');

    renderShoppingTotal(rows);
  }

  /* What the shop comes to (#817), summed from the rows just rendered, and it
     says how many lines it could not price. */
  function renderShoppingTotal(rows) {
    if (!shoppingTotal) return;
    var sum = HTF.shoppingList.total(rows);
    if (!sum) {
      shoppingTotal.hidden = true;
      shoppingTotal.textContent = '';
      return;
    }
    var text = 'roughly ' + sum.text;
    if (sum.unpriced) {
      text += ' — ' + sum.unpriced +
        (sum.unpriced === 1 ? ' line has no price' : ' lines have no price');
    }
    shoppingTotal.textContent = text;
    shoppingTotal.hidden = false;
  }

  if (shoppingDrinks) {
    // Delegated, because the inputs are replaced on every shortlist change.
    shoppingDrinks.addEventListener('input', function (ev) {
      var input = ev.target;
      if (!input.classList || !input.classList.contains('shopping-list-glasses')) return;
      HTF.shortlist.setGlasses(input.dataset.url, input.value);
      // Totals only. Re-rendering the drinks list would replace the very input
      // being typed into and take the caret with it.
      renderTotals();
    });

    /* Choosing a bottle (#818). The row is patched in place, not re-rendered,
       so the radio just chosen keeps its focus. */
    shoppingDrinks.addEventListener('change', function (ev) {
      var input = ev.target;
      // A glasses box shows what it was taken as: "2.5" is 2, "500" is 99.
      if (input.classList && input.classList.contains('shopping-list-glasses')) {
        input.value = String(HTF.shortlist.glasses(input.dataset.url));
        return;
      }
      if (!input.dataset || !input.dataset.generic) return;
      var url = input.dataset.url;
      CHOSEN[url] = CHOSEN[url] || {};
      CHOSEN[url][input.dataset.generic] = input.value;

      var row = input.closest ? input.closest('li') : null;
      var cost = row && row.querySelector('.shopping-list-cost');
      if (cost) cost.textContent = costSuffix(url);

      renderTotals();
    });
  }

  if (setAllInput) {
    /* Set all writes every drink's own count; there is no global factor.
       Number(), not parseInt, which reads "1e9" as 1 (food's twin in
       filters.js does the same). */
    function setAllValue() {
      var n = Number(setAllInput.value);
      return isFinite(n) && n >= 1 ? Math.min(99, Math.floor(n)) : null;
    }

    setAllInput.addEventListener('input', function () {
      var n = setAllValue();
      if (n === null) return;
      shortlistedDrinks().forEach(function (url) { HTF.shortlist.setGlasses(url, n); });
      renderShoppingList();
    });

    /* On `change` the box shows what was applied, or empties if nothing was. */
    setAllInput.addEventListener('change', function () {
      var n = setAllValue();
      setAllInput.value = n === null ? '' : String(n);
    });
  }

  /* Matched chips to the front of the row (#757): `.drink-card-moods` clips
     past its row cap, and the chip that explains why the card is here must not
     be the one cut off. The DOM moves, not flex `order`, because the separator
     dot is a DOM-order selector. card-line-budget.js then packs the rest and
     keeps every `is-match` chip leading (#1308). Reordered only on change. */
  function moveMatchedChipsFirst(d, matched, others) {
    /* No early exit when nothing matched: `wanted` is then the original
       order, which is what restores a row after a mood is cleared. */
    var wanted = matched.concat(others);
    if (!wanted.length) return;
    var parent = wanted[0].parentNode;
    if (!parent) return;

    var kids = parent.children;
    var same = true;
    for (var i = 0; i < wanted.length; i++) {
      if (kids[i] !== wanted[i]) { same = false; break; }
    }
    if (same) return;

    var frag = document.createDocumentFragment();
    wanted.forEach(function (chip) { frag.appendChild(chip); });
    parent.appendChild(frag);
  }

  /* The note over a shared list, and its "keep these" (#1093). */
  function syncSharedNote() {
    if (!sharedNote) return;
    sharedNote.hidden = !sharedKeys;
    if (!sharedKeys) return;
    var text = sharedNote.querySelector('[data-shared-shortlist-text]');
    if (text) {
      text.textContent = 'a shared shortlist (' + sharedKeys.length + ')' +
        (sharedUnmatched.length ? '; not found: ' + sharedUnmatched.join(', ') : '');
    }
    var keep = sharedNote.querySelector('[data-shared-shortlist-keep]');
    if (keep) keep.hidden = sharedKeys.length === 0;
  }

  /* `preservePage` is true only from the pager. Every other caller has
     changed what the results are, so it goes back to page one. */
  function apply(preservePage) {
    if (!preservePage) { currentPage = 1; showAll = false; }
    /* The shortlist view gives way to any other filter (#918). Every handler
       ends in apply(), so this line is the whole of that rule here. */
    FilterState.reconcileShortlistView(state);
    if (!state.shortlisted) { sharedKeys = null; sharedUnmatched = []; }
    var shown = 0;
    var ranked = [];
    activeInclude = chosen('include');
    activeExclude = chosen('exclude');

    model.forEach(function (d) {
      var ok = matches(d);
      d.card.hidden = !ok;
      if (ok) shown++;
      ranked.push({
        card: d.card,
        ok: ok,
        /* Coarse first (#695): `sections` then `score`. -1 keeps a hidden card
           below every visible one. */
        sections: ok ? sectionScore(d) : -1,
        score: ok ? moodScore(d) : -1,
        key: d.key
      });

      /* Cleared and re-applied on every pass rather than tracked. */
      var matchedChips = [];
      var otherChips = [];
      d.moodEls.forEach(function (chip) {
        var on = state.moods.has(chip.dataset.mood);
        chip.classList.toggle('is-match', on);
        (on ? matchedChips : otherChips).push(chip);
        /* Announced as well as painted: a screen reader cannot see a class. */
        chip.setAttribute('aria-pressed', on ? 'true' : 'false');
      });
      moveMatchedChipsFirst(d, matchedChips, otherChips);

      /* Matched against data-ing, not the rendered text (#501): a card found
         by a bottle name prints no such words. Search.entryIsHit is the rule
         the filter used, so a lit ingredient and a surviving card agree. */
      d.ingEls.forEach(function (ing) {
        ing.el.classList.toggle('drink-card-hit', Search.entryIsHit(ing.entries, activeInclude));
      });

      paintNameHighlight(d);
    });

    /* Visible first; then mood sections answered (#695); then moods matched;
       then the card's fixed random key. */
    ranked.sort(function (a, b) {
      if (a.ok !== b.ok) return a.ok ? -1 : 1;
      if (a.sections !== b.sections) return b.sections - a.sections;
      if (a.score !== b.score) return b.score - a.score;
      return a.key - b.key;
    });
    reorder(ranked.map(function (r) { return r.card; }));

    /* Paging after the reorder: "the first page" means nothing until the
       ranking has decided which cards those are. `currentPage` takes paginate's
       answer, since a filter can narrow the results out from under a page. */
    var visible = ranked.filter(function (r) { return r.ok; });
    var pageInfo = HTF.listView.paginate(visible.length, currentPage, PAGE_SIZE, showAll);
    currentPage = pageInfo.currentPage;
    visible.forEach(function (r, i) {
      r.card.hidden = !(i >= pageInfo.start && i < pageInfo.end);
    });
    syncPagination(pageInfo.totalPages, visible.length);

    /* Both redone on every pass, not only when chips moved (#776, #1115): a
       paginated-away card is `hidden` and measures zero, so a card first shown
       by a page turn has never been measured. Name fit first, then the line
       budget, which packs chips for the row cap the name's wrap decides
       (#1308). Guarded so a page loaded without either script still filters. */
    if (HTF.fitCardNames) HTF.fitCardNames();
    if (HTF.cardLineBudget) HTF.cardLineBudget();

    /* Each clear shows only when its own section has something to clear. */
    showClear('clear-mood', moodBtnsIn(false).some(function (b) { return state.moods.has(b.dataset.mood); }));
    showClear('clear-hassle', moodBtnsIn(true).some(function (b) { return state.moods.has(b.dataset.mood); }));
    showClear('clear-chaos', state.chaos !== null);
    showClear('clear-name', state.nameQuery !== '');
    showClear('clear-include', state.include.size > 0 || state.isIncludeSearching);
    showClear('clear-exclude', state.exclude.size > 0 || state.isExcludeSearching);

    /* Clear-all visibility is FilterState's answer (#541), so it agrees with
       what clearAll() clears: both walk the same table. */
    var clearVisibility = FilterState.hasAnythingToClear(state) ? 'visible' : 'hidden';
    clearAllButtons.forEach(function (btn) { btn.style.visibility = clearVisibility; });

    /* Painted from state, not at click time (#546): clear-all reassigns the
       state without touching markup. */
    if (shortlistOnlyBtn) {
      // A shared list is not YOUR shortlist, so the button that counts yours
      // does not claim to be what is showing (#1093).
      var ownView = !!state.shortlisted && !sharedKeys;
      shortlistOnlyBtn.classList.toggle('is-on', ownView);
      shortlistOnlyBtn.setAttribute('aria-pressed', ownView ? 'true' : 'false');
    }
    syncSharedNote();

    renderShoppingList();

    if (countEl) countEl.textContent = shown;
    /* The word moves with the number; the template does the first render. */
    if (wordEl) wordEl.textContent = 'survivor' + (shown === 1 ? '' : 's');
    if (noneEl) noneEl.hidden = shown > 0;
  }

  /* --- mood and chaos ----------------------------------------------------- */
  moodBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var name = btn.dataset.mood;
      if (state.moods.has(name)) state.moods.delete(name);
      else state.moods.add(name);
      syncMoodButtons();
      apply();
    });
  });

  /* Hidden entirely, not disabled, when there is nothing to page or after
     `(see all)`. */
  function syncPagination(totalPages, visibleCount) {
    if (pagination) {
      pagination.style.display =
        (totalPages > 1 && !showAll && visibleCount > 0) ? 'grid' : 'none';
    }
    if (pagePrevBtn) pagePrevBtn.disabled = currentPage <= 1;
    if (pageNextBtn) pageNextBtn.disabled = currentPage >= totalPages;
    if (pageStatusEl) {
      pageStatusEl.textContent = 'page ' + currentPage + ' of ' + totalPages;
    }
  }

  /* The pager. `apply(true)` preserves the page. */
  if (pagePrevBtn) {
    pagePrevBtn.addEventListener('click', function () {
      if (currentPage <= 1) return;
      currentPage -= 1;
      apply(true);
    });
  }
  if (pageNextBtn) {
    pageNextBtn.addEventListener('click', function () {
      currentPage += 1;
      apply(true);
    });
  }
  if (pageSeeAllBtn) {
    pageSeeAllBtn.addEventListener('click', function () {
      showAll = true;
      apply(true);
    });
  }

  /* --- the same moods, clicked on a card -----------------------------------
     Delegated on the list, because apply() reorders the nodes. It does what a
     mood button does; `is-match` is painted from state in apply(), not here. */
  var cardList = document.querySelector('.drink-cards');
  if (cardList) {
    cardList.addEventListener('click', function (ev) {
      var chip = ev.target.closest ? ev.target.closest('.drink-card-mood') : null;
      if (!chip || !cardList.contains(chip)) return;
      var name = chip.dataset.mood;
      if (!name) return;
      /* The chip sits inside the card, and the card's title is a link. Without
         this a click would filter AND navigate. */
      ev.preventDefault();
      if (state.moods.has(name)) state.moods.delete(name);
      else state.moods.add(name);
      syncMoodButtons();
      apply();
    });
  }

  /* Painted from state, not where state changes: clear-all reassigns the whole
     state object and never touches this markup. */
  function syncMoodButtons() {
    moodBtns.forEach(function (b) {
      var on = state.moods.has(b.dataset.mood);
      b.classList.toggle('is-on', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
  }

  function syncChaosButtons() {
    chaosBtns.forEach(function (b) {
      var on = b.dataset.chaos === state.chaos;
      b.classList.toggle('is-on', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
  }

  chaosBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var want = btn.dataset.chaos;
      state.chaos = (state.chaos === want) ? null : want;
      syncChaosButtons();
      apply();
    });
  });

  /* --- the shortlist (#546, #918) -------------------------------------------
     A view, not a facet: on clears every other filter and shows the whole
     shortlist; any filter set while it is on takes it off again, in apply().
     Revealed here, not by shortlist.js, which owns the per-card toggles. */
  if (shortlistOnlyBtn) {
    shortlistOnlyBtn.hidden = false;
    shortlistOnlyBtn.addEventListener('click', function () {
      if (sharedKeys) {
        // Over a shared list the button is not on, so a press means what it
        // means when off: show MY shortlist (#1093).
        sharedKeys = null;
        sharedUnmatched = [];
      } else if (state.shortlisted) {
        state.shortlisted = false;
      } else {
        state = FilterState.enterShortlistView();
        resetControls();
      }
      apply();
    });
  }

  /* #1358. The label names what a press will do. */
  if (draftsBtn) {
    draftsBtn.hidden = false;
    draftsBtn.addEventListener('click', function () {
      hideDrafts = !hideDrafts;
      draftsBtn.textContent = hideDrafts ? 'show drafts' : 'hide drafts';
      draftsBtn.classList.toggle('is-on', hideDrafts);
      draftsBtn.setAttribute('aria-pressed', hideDrafts ? 'true' : 'false');
      apply();
    });
  }

  /* Dispatched by shortlist.js when a card's own toggle changes. */
  document.addEventListener('htf:shortlist-change', apply);

  /* Keep these (#1093): merges the shared list into this browser's shortlist
     and shows it; the change event repaints the toggles. */
  var sharedKeep = sharedNote && sharedNote.querySelector('[data-shared-shortlist-keep]');
  if (sharedKeep) {
    sharedKeep.addEventListener('click', function () {
      if (!sharedKeys) return;
      var keys = sharedKeys;
      sharedKeys = null;
      sharedUnmatched = [];
      HTF.shortlist.addAll(keys);
      document.dispatchEvent(new CustomEvent('htf:shortlist-change', {
        detail: { key: null, on: true, kept: keys.length }
      }));
    });
  }

  /* --- the two ingredient fields ------------------------------------------ */
  /* One builder for both fields. The matching rules differ and live in
     cocktail-search.js: fuzzy to include, exact or declared-family to exclude. */
  /* What a chosen chip's × undoes, for its aria-label. */
  var STOP_DOING = { include: 'stop requiring ', exclude: 'stop leaving out ' };

  function wireSearch(input, poolEl, field, searchingField) {
    if (!input || !poolEl) return;

    function redraw() {
      poolEl.textContent = '';

      /* Text in the box counts towards the clear button (#274) but narrows
         nothing: COCKTAIL_FIELDS declares it `narrows: false`. */
      state[searchingField] = !!input.value.trim();

      state[field].forEach(function (word) {
        poolEl.appendChild(chip(word, true, false));
      });

      /* "hiding lime juice" (#1088), after the chosen chips and before the
         candidates. A family's "(all)" suffix comes off. */
      if (field === 'exclude' && state[field].size) {
        var hidingNames = [];
        state[field].forEach(function (word) {
          hidingNames.push(CS.isFamilyValue(word)
            ? word.slice(0, -FAMILY_SUFFIX.length) : word);
        });
        var hiding = document.createElement('span');
        hiding.className = 'drink-pool-hiding';
        hiding.textContent = 'hiding ' + hidingNames.join(' and ');
        poolEl.appendChild(hiding);
        // Ends the row, so the candidates start below the sentence
        // (_filters.scss hides it when nothing follows).
        var rowBreak = document.createElement('span');
        rowBreak.className = 'drink-pool-break';
        rowBreak.setAttribute('aria-hidden', 'true');
        poolEl.appendChild(rowBreak);
      }

      var result = Search.search(input.value, pool, chosen(field));

      /* The (all) buttons come first (#549), from ingredients.yml's
         `family_of`. */
      result.familyButtons.forEach(function (family) {
        poolEl.appendChild(chip(family + FAMILY_SUFFIX, false, true));
      });

      /* A chip found through a name it does not show says which (#603). Only
         the label moves; the value handed to the state is always `r.entry`:
           - matched on its own name             -> the chip
           - on a name that contains the chip's  -> that name, alone
           - on a genuinely other name           -> the chip, name in brackets */
      result.results.forEach(function (r) {
        var explains = r.band === 3 && r.via;
        poolEl.appendChild(chip(
          explains && r.viaReplacesName ? r.via : r.entry,
          false,
          r.hasWordMatch,
          explains && !r.viaReplacesName ? r.via : null,
          r.entry
        ));
      });

      // Fill any tape slot chip() just made. Cached by URL, so a redraw
      // that made none costs nothing.
      if (state[field].size && window.HTF && HTF.tagShapes) HTF.tagShapes();
    }

    /* `wordMatch` marks a word-prefix hit (#549), not a substring one. A chosen
       chip's × sits outside `.btn-pool-label`, so LEAVE OUT's strike-through
       covers the name only. `value` is what is stored and compared (#603);
       `word` is only what the chip says. */
    function chip(word, on, wordMatch, via, value) {
      var stored = value === undefined ? word : value;
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'btn-pool' + (on ? ' is-on' : '') + (wordMatch ? ' btn-pool--word-match' : '');
      b.setAttribute('aria-pressed', on ? 'true' : 'false');

      if (on) {
        /* A chosen HAS TO HAVE chip gets a tape slot, filled by tagShapes() at
           the end of redraw(). LEAVE OUT's chosen chip gets none. */
        if (field === 'include') {
          var shape = document.createElement('span');
          shape.className = 'tag-shape';
          shape.setAttribute('aria-hidden', 'true');
          b.appendChild(shape);
        }
        var label = document.createElement('span');
        label.className = 'btn-pool-label';
        label.textContent = word;
        b.appendChild(label);
        b.appendChild(document.createTextNode(' \u00d7'));
        b.setAttribute('aria-label', STOP_DOING[field] + word);
      } else if (via) {
        // Only while it is an offer: a chosen chip does not explain itself.
        b.textContent = word + ' ';
        var reason = document.createElement('span');
        reason.className = 'btn-pool-via';
        reason.textContent = '(' + via + ')';
        b.appendChild(reason);
      } else {
        b.textContent = word;
      }

      b.addEventListener('click', function () {
        if (state[field].has(stored)) {
          state[field].delete(stored);
        } else {
          state[field].add(stored);
          /* Choosing one clears the search, on add only. redraw() reads the
             empty input, so the pool returns holding just the chosen chips. */
          input.value = '';
        }
        redraw();
        apply();
      });
      return b;
    }

    input.addEventListener('input', function () { redraw(); apply(); });
    redrawPool[field] = redraw;
    redraw();
  }

  wireSearch(incInput, incPool, 'include', 'isIncludeSearching');
  wireSearch(excInput, excPool, 'exclude', 'isExcludeSearching');

  /* The name box has no candidate pool: a name is typed, not picked. */
  if (nameInput) {
    nameInput.addEventListener('input', function () {
      state.nameQuery = nameInput.value.trim().toLowerCase();
      apply();
    });
  }

  /* --- the clears ---------------------------------------------------------- */
  /* Each per-section clear resets one section and nothing else. */
  function wireClear(id, reset) {
    var btn = document.getElementById(id);
    if (btn) btn.addEventListener('click', function () { reset(); apply(); });
  }

  /* MOOD and HASSLE clear independently even though they share `state.moods`.
     Clearing one must not drop the other. */
  function clearGroup(hassle) {
    moodBtnsIn(hassle).forEach(function (b) { state.moods.delete(b.dataset.mood); });
    syncMoodButtons();
  }

  wireClear('clear-mood', function () { clearGroup(false); });
  wireClear('clear-hassle', function () { clearGroup(true); });

  wireClear('clear-chaos', function () {
    state.chaos = null;
    syncChaosButtons();
  });

  wireClear('clear-name', function () {
    state.nameQuery = '';
    if (nameInput) nameInput.value = '';
  });

  /* The input is cleared with the chips, or its pool would redraw on the next
     keystroke. */
  function clearField(field, input) {
    state[field].clear();
    if (input) input.value = '';
    if (redrawPool[field]) redrawPool[field]();
  }

  wireClear('clear-include', function () { clearField('include', incInput); });
  wireClear('clear-exclude', function () { clearField('exclude', excInput); });

  /* --- clear all, top and bottom — #541 ------------------------------------ */
  /* Two buttons, one action, top and bottom. Built here, not in the template:
     a control that only works with script must not render without it. */
  if (filters) {
    ['btn-clear', 'btn-clear btn-clear--bottom'].forEach(function (cls, i) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = cls;
      btn.textContent = '× clear all';
      if (i === 0) filters.insertBefore(btn, filters.firstChild);
      else filters.appendChild(btn);
      clearAllButtons.push(btn);
    });
  }

  /* A third, inside the "nothing found" line (#1093), so it hides with it.
     One more entry in clearAllButtons, so all three always agree. */
  if (noneEl) {
    var noneClear = document.createElement('button');
    noneClear.type = 'button';
    noneClear.className = 'btn-clear btn-clear--empty';
    noneClear.textContent = '× clear all';
    noneEl.appendChild(noneClear);
    clearAllButtons.push(noneClear);
  }

  /* The boxes, pools and buttons that are not state. Shared by clear-all and
     by the shortlist view turning on (#918). */
  function resetControls() {
    [incInput, excInput, nameInput].forEach(function (input) {
      if (input) input.value = '';
    });
    Object.keys(redrawPool).forEach(function (field) { redrawPool[field](); });
    syncMoodButtons();
    syncChaosButtons();
  }

  function clearAll() {
    /* One assignment, not field by field: emptyState() walks the same table
       hasAnythingToClear() does. */
    state = FilterState.emptyState();
    resetControls();
    apply();
  }

  clearAllButtons.forEach(function (btn) { btn.addEventListener('click', clearAll); });

  /* --- going back returns the list you left (#595) -------------------------
     The order is derived from each card's sort key on every pass, so the keys
     are what is restored: each card takes its index in the saved order, and an
     unseen drink sorts after them all. A half-typed picker is not restored; a
     chosen chip is. The storage itself is HTF.indexMemory (assets.js). */
  var MEMORY_KEY = 'htf-drinks-memory-v1';

  /* Cards carry no id; the drink link's href is unique and stable, and
     `data-name` is not. */
  function cardKey(d) {
    return d.nameEl ? d.nameEl.getAttribute('href') : '';
  }

  function saveDrinksMemory() {
    var order = model.slice().sort(function (a, b) { return a.key - b.key; });
    HTF.indexMemory.save(MEMORY_KEY, {
      order: order.map(cardKey),
      filters: FilterState.serialise(state),
      /* #694: the page too, or going back lands on page one. */
      page: currentPage,
      showAll: showAll,
      scrollY: window.scrollY || 0
    });
  }

  /* Returns the record when it restored, or null for "carry on as a fresh
     load". Stored state is untrusted input. */
  function restoreDrinksMemory() {
    if (!arrivedByGoingBack()) return null;

    var saved = HTF.indexMemory.restore(MEMORY_KEY);
    if (!saved || !Array.isArray(saved.order)) return null;

    var position = Object.create(null);
    saved.order.forEach(function (key, i) { position[key] = i; });
    var unseen = saved.order.length;
    model.forEach(function (d) {
      var at = position[cardKey(d)];
      d.key = (typeof at === 'number') ? at : unseen++;
    });

    /* Untrusted: adopted only if a positive number; `paginate` clamps it. */
    currentPage = (typeof saved.page === 'number' && saved.page > 0) ? saved.page : 1;
    showAll = !!saved.showAll;

    state = FilterState.deserialise(saved.filters);
    state.isIncludeSearching = false;
    state.isExcludeSearching = false;

    if (nameInput) nameInput.value = state.nameQuery || '';
    [incInput, excInput].forEach(function (input) { if (input) input.value = ''; });
    Object.keys(redrawPool).forEach(function (field) { redrawPool[field](); });
    syncMoodButtons();
    syncChaosButtons();
    return saved;
  }

  var restored = restoreDrinksMemory();

  /* `?mood=`, from a drink page's mood chip. A value matching no button is
     dropped in silence: a filter nothing on screen can turn off is one the
     page is stuck in. Runs after the restore and adds to it. */
  (function applyQueryString() {
    if (!moodBtns.length) return;
    /* The query grammar is on the module, not the create() binding. */
    var wanted = HTF.filterState.parseQuery(location.search);
    var changed = false;
    wanted.mood.forEach(function (value) {
      var offered = moodBtns.some(function (b) { return b.dataset.mood === value; });
      if (offered && !state.moods.has(value)) {
        state.moods.add(value);
        changed = true;
      }
    });
    if (changed) syncMoodButtons();
  })();

  /* `?ing=`, from the search box (#1050). Matched against the pool whole and
     case-folded, never as a substring, and added to `include`; dropped in
     silence otherwise. Its own block, because a page with no mood buttons
     must still read it. */
  (function applyIngredientQuery() {
    var wantedIng = HTF.filterState.parseQuery(location.search).ing;
    var added = false;
    wantedIng.forEach(function (value) {
      var key = value.trim().toLowerCase();
      var hit = null;
      pool.forEach(function (chip) {
        if (!hit && String(chip.value).trim().toLowerCase() === key) hit = chip;
      });
      if (hit && !state.include.has(hit.value)) {
        state.include.add(hit.value);
        added = true;
      }
    });
    if (added && redrawPool.include) redrawPool.include();
  })();

  /* `?shortlist=1` (#994) or `?shortlist=slug,slug` (#1093). It does exactly
     what pressing the shortlist button does, and runs last because it
     replaces the restored memory and any mood in the same URL. Not
     `parseQuery`: `shortlisted` is a view, not a field a URL may set. */
  var arrivedShortlist = HTF.filterState.parseShortlist(location.search);
  if (arrivedShortlist.own || arrivedShortlist.slugs.length) {
    state = FilterState.enterShortlistView();
    resetControls();
    if (arrivedShortlist.slugs.length) {
      var resolvedShared = HTF.shortlist.resolveSlugs(arrivedShortlist.slugs,
        model.map(function (d) { return d.url || ''; }));
      sharedKeys = resolvedShared.keys;
      sharedUnmatched = resolvedShared.unmatched;
    }
    /* A different list from the one left, so the remembered scroll goes. */
    restored = null;
  }

  /* `?q=` (#1024): exactly what typing into the name box does. A fresh
     instruction, so the remembered scroll goes. */
  var arrivedName = HTF.filterState.parseName(location.search);
  if (arrivedName && nameInput) {
    nameInput.value = arrivedName;
    state.nameQuery = arrivedName.toLowerCase();
    restored = null;
  }

  apply();

  /* After apply(): the page is not its real height until cards are hidden. */
  if (restored && typeof restored.scrollY === 'number') {
    window.scrollTo(0, restored.scrollY);
  }

  /* Any fragment (#1050, #1057, #1059). The browser landed on it once already,
     before apply() gave the page its real height; this lands on it again. Not
     on a back navigation, where the remembered scroll wins. */
  if (!restored && location.hash && location.hash.length > 1) {
    var target = document.getElementById(location.hash.slice(1));
    if (target && typeof target.scrollIntoView === 'function') {
      target.scrollIntoView({ block: 'start' });
    }
  }

  /* pagehide, not unload: it fires on the way into bfcache and does not
     disqualify the page from it. */
  window.addEventListener('pagehide', saveDrinksMemory);
})();
