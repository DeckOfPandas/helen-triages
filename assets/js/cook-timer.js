/* =============================================================================
   COOK TIMER — weight in, timings out
   =============================================================================
   Reads _data/food/cooking_methods.yml (serialised into the page as JSON by
   Liquid) and _data/food/internal_temperatures.yml, and answers two questions:

     "How long does a 2.4 kg chicken take?"      -> weight alone
     "What time do I put it in for lunch at 2?"  -> weight + a serving time

   THE SECOND ONE IS OPTIONAL, deliberately. Helen: "don't enforce giving an end
   time -- also offer total time (at each temperature) when I enter a weight."
   So the default answer is a list of every method with its own oven temperature
   and its own total, which is the shape of the question you actually ask while
   deciding HOW to cook something. Clock times are an extra layer on top, for
   when you already know when you're eating.

   -----------------------------------------------------------------------------
   THE HARD PART IS THE 21% OF ROWS THAT AREN'T A FORMULA
   -----------------------------------------------------------------------------
   52 of the 66 method rows are `rate` -- minutes per kg, sometimes plus a flat
   addition -- and multiplying is all they need. The other 14 are five different
   things, and the temptation is to coerce them into a number anyway so every
   row has an answer. That would be the worst thing this file could do: a
   confident "out at 17:05" derived from a row whose own sources disagree by 3:1
   is worse than no calculator, because it launders uncertainty into precision.

   So each shape is handled on its own terms, and two of them REFUSE:

     rate         multiply, add the flat part
     total        a fixed time; ignores the weight box and says so on screen
     staged       two rates in sequence, reported as two stages
     by_doneness  a rate per doneness level; shows the one you picked
     relative     defined against another row -- resolved, and the row it
                  borrowed from is named in the output
     disputed     shows the range and the reason, and declines to schedule it
     unparsed     shows the original wording, and declines

   A refusal is a real answer here, not a gap. Duck spatchcocked is
   "~20–60 min/kg — genuinely conflicting sources": a three-fold spread that
   nobody should turn into a serving time.
   ========================================================================== */

(function () {
  "use strict";

  var root = document.querySelector("[data-cook-timer]");
  if (!root) return;

  var METHODS = JSON.parse(document.getElementById("ct-methods").textContent);
  var TEMPS = JSON.parse(document.getElementById("ct-temps").textContent);

  var els = {
    protein: root.querySelector("#ct-protein"),
    weight: root.querySelector("#ct-weight"),
    serve: root.querySelector("#ct-serve"),
    rest: root.querySelector("#ct-rest"),
    table: root.querySelector("#ct-table"),
    out: root.querySelector("#ct-results"),
    summary: root.querySelector("#ct-summary")
  };

  /* --- formatting ---------------------------------------------------------
     Minutes are the working unit throughout and only ever become words at the
     edge. "2 hrs 5 min" rather than "125 min": you read this while planning a
     meal, not while timing an experiment. */
  /* FIVE-MINUTE GRANULARITY, applied once here and reused by the clock
     arithmetic below so a duration and the time it implies can never disagree.
     Helen: "let's round cooking times to the nearest 5 mins to preserve
     sanity." She's right, and not only about sanity: "1 hr 37 min" claims a
     precision the underlying figure hasn't got — most of these rates are
     themselves a range, and several are estimates by analogy. Rounding is
     honesty about the input, not just tidiness in the output. */
  function round5(mins) {
    return Math.round(mins / 5) * 5;
  }

  function hhmm(mins) {
    mins = round5(mins);
    var h = Math.floor(mins / 60), m = mins % 60;
    if (!h) return m + " min";
    if (!m) return h + " hr" + (h > 1 ? "s" : "");
    return h + " hr" + (h > 1 ? "s" : "") + " " + m + " min";
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
    var day = "";
    while (minsFromMidnight < 0) { minsFromMidnight += 1440; day = " (the day before)"; }
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

  /* --- the finishing temperature ------------------------------------------
     A schedule that ends on a clock is only half an answer; the oven doesn't
     know how big your bird is. Every protein carries an internal_temp_ref, so
     the last line of every card is the figure to actually check. */
  function finishingTemp(ref) {
    if (!ref) return null;
    var node = TEMPS;
    ref.split(".").forEach(function (k) { node = node && node[k]; });
    if (!node) return null;
    if (node.endpoint) return node.endpoint;
    if (node.target) return node.target;
    if (node.doneness) {
      var first = Object.keys(node.doneness)[0];
      return node.doneness[first].pull + " (" + first.replace(/_/g, " ") + ")";
    }
    return null;
  }

  /* --- render -------------------------------------------------------------- */

  function render() {
    var protein = METHODS[els.protein.value];
    var kg = parseFloat(els.weight.value);
    var serveAt = parseClock(els.serve.value);
    var rest = parseInt(els.rest.value, 10) || 0;
    var doneness = "rare";

    els.out.innerHTML = "";
    els.table.innerHTML = "";

    if (!kg || kg <= 0) {
      els.summary.textContent = "Enter a weight to see how long each method takes.";
      return;
    }

    var temp = finishingTemp(protein.internal_temp_ref);
    els.summary.innerHTML =
      protein.methods.length + " ways to cook " + kg + " kg of " +
      els.protein.options[els.protein.selectedIndex].text.toLowerCase() +
      (serveAt === null ? ". Add a serving time for clock times." : ".") +
      (temp ? " <strong>Done at " + temp + "</strong>." : "");

    /* --- the decision table ------------------------------------------------
       The cards below answer "how long does this method take". They do not
       answer "which method", which is the question you actually have first --
       and seven cards, each with a time and a paragraph, is not something you
       can compare at a glance. This is the same information at a length you can
       scan: what you get, and what it costs you in time.

       Table for choosing, cards for doing. Uses the site's existing table
       styles (article.recipe .recipe-body-content table) and the .table-scroll
       wrapper that already exists for wide tables -- no new CSS. */
    var rows = protein.methods.map(function (method) {
      var r = resolve(method, kg, doneness, protein.methods);
      return "<tr>" +
        "<td>" + method.name + "</td>" +
        "<td>" + (method.outcome || "—") + "</td>" +
        "<td>" + (r.ok ? span(r.lo, r.hi) : "<em>won’t guess</em>") + "</td>" +
        "</tr>";
    }).join("");

    els.table.innerHTML =
      "<table><thead><tr><th>Method</th><th>What you get</th><th>Time</th>" +
      "</tr></thead><tbody>" + rows + "</tbody></table>";

    protein.methods.forEach(function (method) {
      var r = resolve(method, kg, doneness, protein.methods);
      var card = document.createElement("div");
      card.className = "ct-card" + (r.ok ? "" : " ct-card--declined");

      /* NAME AND TIME ON ONE LINE, AT THE SAME WEIGHT. Helen: "the cooking
         method name should be as bold as the time." The card used to open with
         a small grey heading, then the oven temperature, then a large time —
         so the eye found the number first and had to travel back up for the
         thing it belonged to. They are one fact ("this method takes this
         long") and now read as one line.

         Everything under it is ordered by how often you need it: what you get,
         then the two settings you act on, then the schedule, then the caveats.
         The oven temperature moved out of its own paragraph and into that
         settings line — it was taking a full row to say four characters. */
      var html =
        "<div class='ct-card-head'>" +
          "<h3 class='ct-card-name'>" + method.name + "</h3>" +
          "<p class='ct-total'>" + (r.ok ? span(r.lo, r.hi) : "—") + "</p>" +
        "</div>";

      if (method.outcome) html += "<p class='ct-outcome'>" + method.outcome + "</p>";

      var settings = [];
      if (method.oven) settings.push(method.oven);
      if (method.covering) settings.push(method.covering.toLowerCase());
      if (settings.length) {
        html += "<p class='ct-settings'>" + settings.join(" &middot; ") + "</p>";
      }

      if (r.ok) {

        if (r.stages) {
          html += "<ul class='ct-stages'>" + r.stages.map(function (st) {
            return "<li><span>" + st.name + "</span> " + span(st.lo, st.hi) + "</li>";
          }).join("") + "</ul>";
        }

        if (serveAt !== null) {
          /* Work backwards from the plate. The LONGER estimate drives the start
             time on purpose: being ready early and holding is recoverable,
             being late is not. */
          var outAt = serveAt - rest;
          var longest = round5(r.hi), shortest = round5(r.lo);
          html += "<ul class='ct-schedule'>" +
            "<li><span>in at</span> " + clock(outAt - longest) +
              (shortest !== longest
                ? " <em>(or " + clock(outAt - shortest) + " if it runs to the quicker end)</em>" : "") +
            "</li>" +
            "<li><span>out at</span> " + clock(outAt) + "</li>" +
            (rest ? "<li><span>rest until</span> " + clock(serveAt) + "</li>" : "") +
            "</ul>";
        }

        if (r.aside) html += "<p class='ct-aside'>" + r.aside + "</p>";
      } else {
        html += "<p class='ct-declined'>Won’t guess this one.</p>" +
                "<p class='ct-aside'>" + r.why + "</p>";
      }

      if (method.notes) html += "<p class='ct-notes'>" + method.notes + "</p>";

      card.innerHTML = html;
      els.out.appendChild(card);
    });
  }

  function fillProteins() {
    /* Alphabetical by the label you actually read, not by the data file's own
       order -- sorted here rather than in the YAML so the data stays neutral
       about presentation and the reference page can keep its own sequence. */
    Object.keys(METHODS).sort(function (a, b) {
      return METHODS[a].label.localeCompare(METHODS[b].label);
    }).forEach(function (key) {
      var opt = document.createElement("option");
      opt.value = key;
      opt.textContent = METHODS[key].label;
      els.protein.appendChild(opt);
    });
  }

  fillProteins();
  ["input", "change"].forEach(function (evt) {
    root.addEventListener(evt, render);
  });
  render();
})();
