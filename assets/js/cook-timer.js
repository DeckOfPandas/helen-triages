/* cook-timer.js
   The cook timer's DOM wiring: a protein and a weight in, every method's time
   out. Reads _data/food/cooking_methods.yml and
   _data/food/internal_temperatures.yml, serialised into the page as JSON.

   The arithmetic is not in this file. It lives in assets/js/cook-schedule.js
   as HTF.cookSchedule, which must load FIRST (tests/test_site_config.py
   guards the order, and that no maths moves back here).

   Not every method row is a formula, and none is coerced into a number: a
   `disputed` or `unparsed` row declines to be timed, and the page says
   "won't guess". A refusal is a real answer here, not a gap. The shapes are
   handled in HTF.cookSchedule.resolve. */

(function () {
  "use strict";

  var root = document.querySelector("[data-cook-timer]");
  if (!root) return;

  var CS = window.HTF.cookSchedule;

  var METHODS = JSON.parse(document.getElementById("ct-methods").textContent);
  var TEMPS = JSON.parse(document.getElementById("ct-temps").textContent);

  var els = {
    protein: root.querySelector("#ct-protein"),
    weight: root.querySelector("#ct-weight"),
    // Outside #ct-calculator, so it is hidden on its own when the dropdown
    // says fish.
    weightField: root.querySelector("#ct-weight-field"),
    heading: root.querySelector("#ct-protein-name"),
    doneat: root.querySelector("#ct-doneat"),
    methods: root.querySelector("#ct-method-groups"),
    summary: root.querySelector("#ct-summary"),
    // The two halves the dropdown swaps between (#412).
    calculator: root.querySelector("#ct-calculator"),
    fish: root.querySelector("#ct-fish-shellfish")
  };

  /* --- render -------------------------------------------------------------- */

  /* A range may break only at its dash: each half goes in a nowrap span so
     the time column can wrap without splitting a figure. The split string is
     the separator HTF.cookSchedule.span writes. */
  function spanHtml(lo, hi) {
    return CS.span(lo, hi).split(" – ").map(function (half) {
      return "<span class='ct-t'>" + half + "</span>";
    }).join(" – ");
  }

  /* One method's time. A by_doneness method shows EVERY level (#246);
     everything else is a single span. */
  function timeHtml(r) {
    if (!r.ok) return null;
    if (!r.levels || r.levels.length < 2) return spanHtml(r.lo, r.hi);
    return "<span class='ct-doneness'>" + r.levels.map(function (lv) {
      /* A space between the word and the figure, so a capped time column
         can break there rather than overflow. */
      return "<span class='ct-doneness-level'>" +
               "<span class='ct-doneness-label'>" + lv.label + "</span> " +
               spanHtml(lv.lo, lv.hi) +
             "</span>";
    }).join("") + "</span>";
  }

  /* One method, as a block: the outcome and the time on the first line, the
     method's name under them, then the oven setting. `oven` is a list of
     short lines, each in its own span so a stage never wraps into the next. */
  function methodHtml(method, r) {
    var oven = [].concat(method.oven).map(function (line) {
      return "<span class='ct-oven-line'>" + line + "</span>";
    }).join("");
    return "<li class='ct-method'>" +
      "<span class='ct-method-outcome'>" + method.outcome + "</span>" +
      "<span class='ct-method-time'>" + (r.ok ? timeHtml(r) : "<em>won’t guess</em>") + "</span>" +
      "<span class='ct-method-name'>" + method.name + "</span>" +
      "<span class='ct-method-oven'>" + oven + "</span>" +
    "</li>";
  }

  /* A cut group's heading. The data writes a group as "name — the cuts it
     covers", split on the dash here. The name sits in its own span because
     the rule under it is an inline background that measures the lettering
     (.ct-group-title in _sass/food/_timings.scss). */
  function groupHtml(name) {
    var bits = name.split(" — ");
    return "<h3 class='ct-group-name'><span class='ct-group-title'>" + bits[0] + "</span>" +
      (bits[1] ? "<span class='ct-group-cuts'>" + bits[1] + "</span>" : "") +
    "</h3>";
  }

  function render() {
    /* The swap, before anything else: the fish entry is not in METHODS, so
       `protein` would be undefined and every line below would throw on
       protein.label. */
    var showingFish = els.protein.value === FISH_KEY;
    if (els.calculator) els.calculator.hidden = showingFish;
    if (els.weightField) els.weightField.hidden = showingFish;
    if (els.fish) els.fish.hidden = !showingFish;
    if (showingFish) return;

    var protein = METHODS[els.protein.value];
    var kg = parseFloat(els.weight.value);
    var doneness = "rare";

    els.methods.innerHTML = "";

    /* The heading and the finishing temperature are about the protein, not
       the weight, so both are written before the weight is checked: an
       emptied weight box must not blank the heading. */
    els.heading.textContent = protein.label;

    var temp = CS.finishingTemp(TEMPS, protein.internal_temp_ref);
    els.doneat.innerHTML = temp
      ? "<strong>Done at " + temp + "</strong>" +
        /* Built at runtime, so no link test or build scanner sees this href:
           check it by hand if the charts page moves (#384). Relative, not
           root-relative: JS has no `relative_url`, and a literal /food/...
           would drop the baseurl and 404 in production only. */
        (protein.chart_anchor
          ? "<a href='../internal-temperatures/#" + protein.chart_anchor +
            "'>see other doneness</a>"
          : "")
      : "";

    if (!kg || kg <= 0) {
      els.summary.textContent = "Enter a weight to see how long each method takes.";
      return;
    }

    /* The box's own min and max are the range the data is good for; a browser
       does not enforce them on typing, and past them a time is nonsense
       ("550000000h"). PLACEHOLDER COPY, not Helen's words yet. */
    var lo = parseFloat(els.weight.min), hi = parseFloat(els.weight.max);
    if ((isFinite(lo) && kg < lo) || (isFinite(hi) && kg > hi)) {
      els.summary.textContent = "Times are worked out for " + els.weight.min +
        " to " + els.weight.max + " kg.";
      return;
    }

    /* Cleared, or the prompt above would be stranded over a filled list once
       a weight is typed. */
    els.summary.textContent = "";

    /* One section per cut group, in the data's own order, each a list of
       methods (#1329; shape in _sass/food/_timings.scss). Within a group:
       shortest first, decliners last (HTF.cookSchedule.orderMethods). */
    var ordered = CS.orderMethods(protein.methods, kg, doneness);
    var groups = [];
    protein.methods.forEach(function (method) {
      if (groups.indexOf(method.group) < 0) groups.push(method.group);
    });

    els.methods.innerHTML = groups.map(function (group) {
      var items = ordered.filter(function (method) { return method.group === group; })
        .map(function (method) {
          return methodHtml(method, CS.resolve(method, kg, doneness, protein.methods));
        }).join("");
      return "<section class='ct-group'>" + groupHtml(group) +
        "<ul class='ct-methods'>" + items + "</ul></section>";
    }).join("");
  }

  /* Fish and shellfish are a dropdown entry, not a protein (#412): picking it
     puts the calculator away and shows the static section. The value must
     never be a key in METHODS: every entry there carries a weight-driven
     rate, and fish is governed by thickness, shellfish by the shell opening.
     It sits last in the list, not alphabetically among the proteins. */
  var FISH_KEY = "fish-shellfish";
  var FISH_LABEL = "Fish and shellfish";

  function fillProteins() {
    CS.proteinOrder(METHODS).forEach(function (key) {
      var opt = document.createElement("option");
      opt.value = key;
      opt.textContent = METHODS[key].label;
      els.protein.appendChild(opt);
    });
    var fish = document.createElement("option");
    fish.value = FISH_KEY;
    fish.textContent = FISH_LABEL;
    els.protein.appendChild(fish);
  }

  fillProteins();

  /* ?protein=beef, so the temperature charts can link to the timings for one
     protein. A name this page does not have is ignored silently.
     ?protein=fish is the fish-and-shellfish entry: an anchor into that block
     cannot work, because the block is hidden until the entry is picked. */
  var wanted = (location.search.match(/[?&]protein=([a-z]+)/) || [])[1];
  if (wanted === "fish") els.protein.value = FISH_KEY;
  else if (wanted && METHODS[wanted]) els.protein.value = wanted;

  ["input", "change"].forEach(function (evt) {
    root.addEventListener(evt, render);
  });
  render();
})();
