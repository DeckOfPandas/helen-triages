// cook-schedule.js
// The arithmetic behind the cook timer, no DOM. Nothing here reads the clock,
// the page or the data files: every impure thing is a parameter, which is what
// lets tests/js/cook-schedule.test.js call it directly. cook-timer.js owns
// everything DOM-shaped.
//
// One file, two loaders: a plain <script> before cook-timer.js (attaching to
// window.HTF), and require() in Node.
//
// scheduleBack, parseClock, clock, statedRest and restFor have no caller on
// any page, and are kept with their tests on purpose (#244) until it is
// decided whether working backwards from a serving time comes back. Reconnect
// them, or delete them together with their tests; do not tidy them away
// piecemeal.
(function (root) {
  'use strict';

  /* --- formatting ---------------------------------------------------------
     Minutes are the working unit throughout and only become a figure at the
     edge. */
  /* Five-minute granularity, applied here and reused by the clock arithmetic
     so a duration and the time it implies can never disagree. The underlying
     rates are ranges and estimates; finer figures would claim a precision
     they have not got. */
  function round5(mins) {
    return Math.round(mins / 5) * 5;
  }

  /* Compact on purpose: "4h50m", "2h", "10m". These are a column of figures
     read against each other, so MANUAL §5's "mins" register, which governs a
     recipe's Prep and Cook lines, does not apply here. */
  function hhmm(mins) {
    mins = round5(mins);
    var h = Math.floor(mins / 60), m = mins % 60;
    if (!h) return m + "m";
    if (!m) return h + "h";
    return h + "h" + m + "m";
  }

  function span(lo, hi) {
    /* Compared AFTER rounding: 95 and 97 minutes are one answer. An en dash
       with a space each side, which is the string cook-timer.js splits a
       range on. */
    return round5(lo) === round5(hi)
      ? hhmm(lo) : hhmm(lo) + " – " + hhmm(hi);
  }

  /* Clock arithmetic in minutes-since-midnight, wrapping backwards over
     midnight: a big turkey for lunch starts the night before. */
  function clock(minsFromMidnight) {
    /* COUNT the wraps: a long enough low-and-slow cook crosses midnight
       twice, and must not be labelled one day back. */
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
    /* A `relative` row borrows another row's timing: the first `rate` row in
       the same group. Returned, not applied silently, so the caller can name
       it in the output. */
    for (var i = 0; i < all.length; i++) {
      if (all[i].group === method.group && all[i].shape === "rate") return all[i];
    }
    return null;
  }

  /* Each shape on its own terms. Two REFUSE: `disputed` and `unparsed` return
     { ok: false } with a reason, because a confident number from a row whose
     own sources disagree is worse than no answer. See the header of
     _data/food/cooking_methods.yml. */
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
      /* Keep the flat_add fallback chain in agreement with the `rate` branch
         above (#245): flat_add_max if the level states one, else flat_add,
         else nothing. Dropping flat_add_max loses an asymmetric upper bound
         with no error. */
      var d = method.by_doneness[doneness] || method.by_doneness.rare;

      /* Every level, not just the one asked for (#246): the page has no
         doneness control, so `levels` is the only way the other rates are
         shown. Additive: lo/hi and the aside still describe the requested
         level, so orderMethods sorts on one consistent figure. In data order
         (rare before medium), not alphabetical. */
      var levels = Object.keys(method.by_doneness).map(function (name) {
        var lv = method.by_doneness[name];
        return {
          name: name,
          label: name.replace(/_/g, " "),
          lo: lv.rate_min * kg + (lv.flat_add || 0),
          hi: lv.rate_max * kg + (lv.flat_add_max || lv.flat_add || 0)
        };
      });

      return {
        ok: true,
        lo: d.rate_min * kg + (d.flat_add || 0),
        hi: d.rate_max * kg + (d.flat_add_max || d.flat_add || 0),
        levels: levels,
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

  /* Shortest first, by lower bound. Rows that decline to be timed sort last:
     an unanswerable row at the top of a table of times would read as the
     fastest. Returns a new array; the caller's list is never reordered. */
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
     From a resolved range, the rest time and serveAt (all minutes; serveAt is
     minutes from midnight): when does it go in? The LONGER estimate drives
     `inAt`: ready early and holding is recoverable, late is not. `hasRange`
     uses the same round5 as the printed duration, so a card cannot show a
     duration that disagrees with its times. Results are minutes from
     midnight, negative if they run back past it; clock() formats that. */
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
     `temps` is the parsed internal_temperatures.yml, passed in, never read
     here. */
  function lookup(temps, ref) {
    if (!ref) return null;
    var node = temps;
    ref.split(".").forEach(function (k) { node = node && node[k]; });
    return node || null;
  }

  /* The figure to actually check, from the protein's internal_temp_ref. */
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

  /* Rest time from the protein's own entry where the data states one. Where
     it does not, restFor returns the caller's fallback with `stated: false`,
     so a working default is never presented as a cited figure. */
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

  /* Alphabetical by the label you read, sorted here so the data file can keep
     its own sequence. */
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
