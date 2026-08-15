// =============================================================================
// COOK SCHEDULE — the arithmetic behind the cook timer, no DOM.
//
// Extracted out of cook-timer.js for the same reason ingredient-search.js and
// recipe-list.js came out of filters.js: testable directly with Node (see
// tests/js/cook-schedule.test.js) instead of only ever checked by looking at a
// live page. cook-timer.js still owns everything DOM-shaped -- reading the
// weight box, building cards, filling the protein dropdown.
//
// This is the highest-consequence arithmetic on the site: it decides what time
// a joint goes in the oven so dinner lands when you said it would. Nothing
// here reads the clock, the page, or the data files. Every impure thing is a
// parameter: the temperature table is passed to the lookups, "now" is never
// consulted at all (the module works in minutes-from-midnight and hands the
// caller a number, which is why it can be tested at all).
//
// Loaded two ways from the one file, no bundler:
//   - In the browser, as a plain <script> before cook-timer.js, attaching to
//     window.HTF (the same namespace assets.js already establishes).
//   - In Node, via require(), for tests.
// =============================================================================
(function (root) {
  'use strict';

  /* --- formatting ---------------------------------------------------------
     Minutes are the working unit throughout and only ever become words at the
     edge. "2 hrs 5 mins" rather than "125 mins": you read this while planning a
     meal, not while timing an experiment. */
  /* FIVE-MINUTE GRANULARITY, applied once here and reused by the clock
     arithmetic below so a duration and the time it implies can never disagree.
     Helen: "let's round cooking times to the nearest 5 mins to preserve
     sanity." She's right, and not only about sanity: "1 hr 37 mins" claims a
     precision the underlying figure hasn't got — most of these rates are
     themselves a range, and several are estimates by analogy. Rounding is
     honesty about the input, not just tidiness in the output. */
  function round5(mins) {
    return Math.round(mins / 5) * 5;
  }

  /* "mins", never "min" -- HANDOVER §5. A numeric quantity takes the plural
     form in both the metadata register (`mins`/`hrs`) and the prose one
     (`mins`/`hours`); only a bare English "a minute" stays singular, and
     there are none of those here. This emitted "45 min" and "2 hrs 5 min"
     until 2026-08-15. `hrs` was right all along, which is probably why the
     singular next to it never looked wrong. */
  function hhmm(mins) {
    mins = round5(mins);
    var h = Math.floor(mins / 60), m = mins % 60;
    if (!h) return m + " mins";
    if (!m) return h + " hr" + (h > 1 ? "s" : "");
    return h + " hr" + (h > 1 ? "s" : "") + " " + m + " mins";
  }

  function span(lo, hi) {
    /* Compared AFTER rounding: 95 and 97 minutes are one answer once you've
       decided five minutes is the resolution, and printing "1 hr 35 – 1 hr 35"
       would be the arithmetic showing through. */
    return round5(lo) === round5(hi)
      ? hhmm(lo) : hhmm(lo) + " – " + hhmm(hi);
  }

  /* Clock arithmetic in minutes-since-midnight, wrapping backwards over
     midnight rather than producing a negative time — a 6 kg turkey for a 1pm
     lunch genuinely does start the night before, and printing "-45:00" instead
     of "22:15 (the day before)" would be a bug you'd only notice at Christmas. */
  function clock(minsFromMidnight) {
    /* COUNT the wraps, don't just record that one happened. This loop used to
       assign " (the day before)" on every pass, so a start time two days back
       was labelled one day back -- and that is reachable from the page's own
       inputs, not a theoretical case: beef's low-and-slow brisket at 13.2 kg
       is a 29-43½ hour cook, which crosses midnight twice. Fixed 2026-08-15. */
    var daysBack = 0;
    while (minsFromMidnight < 0) { minsFromMidnight += 1440; daysBack += 1; }
    var day = "";
    if (daysBack === 1) day = " (the day before)";
    else if (daysBack > 1) day = " (" + daysBack + " days before)";
    var h = Math.floor(minsFromMidnight / 60) % 24, m = Math.round(minsFromMidnight) % 60;
    return ("0" + h).slice(-2) + ":" + ("0" + m).slice(-2) + day;
  }

  function parseClock(value) {
    var m = /^(\d{1,2}):(\d{2})$/.exec((value || "").trim());
    if (!m) return null;
    return parseInt(m[1], 10) * 60 + parseInt(m[2], 10);
  }

  /* --- resolving a method to minutes -------------------------------------- */

  function baseFor(method, all) {
    /* A `relative` row borrows another row's timing. The base is the first
       straightforward `rate` row in the same group — "plain equivalent" in the
       data's own words. Returned rather than applied silently so the caller can
       name it in the output: a number you can't trace is a number you can't
       check. */
    for (var i = 0; i < all.length; i++) {
      if (all[i].group === method.group && all[i].shape === "rate") return all[i];
    }
    return null;
  }

  /* The six shapes, each on its own terms. Two of them REFUSE: `disputed` and
     `unparsed` return { ok: false } with a reason, because a confident number
     derived from a row whose own sources disagree by 3:1 is worse than no
     answer at all. See the header of _data/food/cooking_methods.yml. */
  function resolve(method, kg, doneness, all) {
    var s = method.shape;

    if (s === "rate") {
      var lo = method.rate_min * kg + (method.flat_add || 0);
      var hi = method.rate_max * kg + (method.flat_add_max || method.flat_add || 0);
      return { ok: true, lo: lo, hi: hi };
    }

    if (s === "total") {
      return {
        ok: true, lo: method.total_min, hi: method.total_max,
        aside: "Timed by the piece, not by weight — the weight box doesn't change this one."
      };
    }

    if (s === "by_doneness") {
      var d = method.by_doneness[doneness] || method.by_doneness.rare;
      return {
        ok: true,
        lo: d.rate_min * kg + (d.flat_add || 0),
        hi: d.rate_max * kg + (d.flat_add || 0),
        aside: "Rate depends on doneness; showing " + doneness.replace(/_/g, " ") + "."
      };
    }

    if (s === "staged") {
      var stages = method.stages.map(function (st) {
        return { name: st.name, lo: st.rate_min * kg, hi: st.rate_max * kg };
      });
      return {
        ok: true,
        lo: stages.reduce(function (a, b) { return a + b.lo; }, 0),
        hi: stages.reduce(function (a, b) { return a + b.hi; }, 0),
        stages: stages
      };
    }

    if (s === "relative") {
      var base = baseFor(method, all);
      if (!base) return { ok: false, why: method.relative_to };
      var pct = /add ~?(\d+)%/i.exec(method.relative_to);
      var mult = pct ? 1 + parseInt(pct[1], 10) / 100 : 1;
      var b = resolve(base, kg, doneness, all);
      return {
        ok: true, lo: b.lo * mult, hi: b.hi * mult,
        aside: "Borrowed from “" + base.name + "”" +
               (pct ? ", plus " + pct[1] + "%" : "") + " — this row has no timing of its own."
      };
    }

    /* disputed / unparsed: the two that decline. */
    return {
      ok: false,
      why: s === "disputed"
        ? "Sources genuinely disagree on this one (" + method.timing + "), by enough " +
          "that any single number would be invented. Use a thermometer."
        : "No formula in the data — the timing is “" + method.timing + "”."
    };
  }

  /* ONE ORDER FOR BOTH VIEWS, shortest first. Helen: "either order it by time
     taken (lower bound) or alphabetically by method name, then same for the
     cards." Time wins over alphabetical because it makes the table a ranking
     rather than a list -- "what can I do in the time I have" is the question
     a sorted column answers for free, and alphabetical answers nothing.

     The two rows that decline to be timed sort last: they have no lower bound
     to rank on, and an unanswerable row at the top of a table of times would
     read as the fastest.

     Returns a new array; the caller's list is never reordered under it. */
  function orderMethods(methods, kg, doneness) {
    return methods.slice().sort(function (a, b) {
      var ra = resolve(a, kg, doneness, methods);
      var rb = resolve(b, kg, doneness, methods);
      if (ra.ok !== rb.ok) return ra.ok ? -1 : 1;
      if (!ra.ok) return a.name.localeCompare(b.name);
      return ra.lo - rb.lo;
    });
  }

  /* --- working backwards from the plate -----------------------------------
     Given a resolved range, the rest time and the clock time you're eating at
     (all in minutes; serveAt is minutes from midnight), when does it go in?

     The LONGER estimate drives `inAt` on purpose: being ready early and holding
     is recoverable, being late is not. `inAtQuicker` is the same sum against
     the shorter estimate, and `hasRange` says whether the two differ once
     five-minute rounding has been applied — the same round5 the printed
     duration uses, so a card can never show a duration that disagrees with the
     times either side of it.

     Everything comes back as minutes from midnight, negative if it runs back
     past midnight; clock() is what turns that into "22:15 (the day before)".
     Nothing here knows what time it is now, deliberately: "is that in the
     past?" is a question about the reader's clock, and this module never reads
     one. */
  function scheduleBack(lo, hi, serveAt, rest) {
    var outAt = serveAt - (rest || 0);
    var longest = round5(hi), shortest = round5(lo);
    return {
      inAt: outAt - longest,
      inAtQuicker: outAt - shortest,
      hasRange: shortest !== longest,
      outAt: outAt,
      restUntil: serveAt
    };
  }

  /* --- the temperature table ----------------------------------------------
     `temps` is the parsed internal_temperatures.yml, passed in rather than
     read: the page serialises it into the document, and this module has no
     business knowing that. */
  function lookup(temps, ref) {
    if (!ref) return null;
    var node = temps;
    ref.split(".").forEach(function (k) { node = node && node[k]; });
    return node || null;
  }

  /* A schedule that ends on a clock is only half an answer; the oven doesn't
     know how big your bird is. Every protein carries an internal_temp_ref, so
     the last line of every card is the figure to actually check. */
  function finishingTemp(temps, ref) {
    var node = lookup(temps, ref);
    if (!node) return null;
    if (node.endpoint) return node.endpoint;
    if (node.target) return node.target;
    if (node.doneness) {
      var first = Object.keys(node.doneness)[0];
      return node.doneness[first].out_at + " (" + first.replace(/_/g, " ") + ")";
    }
    return null;
  }

  /* Rest time from the selected protein's own entry rather than a round 20
     nobody wrote down. Beef, pork and lamb publish one in
     internal-temperatures.html's own table headers ("After ~15–20 min rest");
     goose states one in its note. Chicken, turkey, duck and ham publish none —
     they fall back, and `stated` is false so the caller can say as much rather
     than presenting a working default with the same confidence as a cited
     figure. The fallback is injected, not hard-coded here: what to do when the
     data is silent is a policy the page owns. */
  function statedRest(temps, ref) {
    var node = lookup(temps, ref);
    return node && node.rest_min != null ? node.rest_min : null;
  }

  function restFor(temps, ref, fallback) {
    var stated = statedRest(temps, ref);
    return stated != null
      ? { mins: stated, stated: true }
      : { mins: fallback, stated: false };
  }

  /* Alphabetical by the label you actually read, not by the data file's own
     order -- sorted here rather than in the YAML so the data stays neutral
     about presentation and the reference page can keep its own sequence. */
  function proteinOrder(methodsByKey) {
    return Object.keys(methodsByKey).sort(function (a, b) {
      return methodsByKey[a].label.localeCompare(methodsByKey[b].label);
    });
  }

  var api = {
    round5: round5,
    hhmm: hhmm,
    span: span,
    clock: clock,
    parseClock: parseClock,
    baseFor: baseFor,
    resolve: resolve,
    orderMethods: orderMethods,
    scheduleBack: scheduleBack,
    finishingTemp: finishingTemp,
    statedRest: statedRest,
    restFor: restFor,
    proteinOrder: proteinOrder
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  } else {
    root.HTF = root.HTF || {};
    root.HTF.cookSchedule = api;
  }
})(typeof window !== 'undefined' ? window : this);
