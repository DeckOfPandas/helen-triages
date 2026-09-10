/* =============================================================================
   COOK TIMER — weight in, timings out (DOM wiring only)
   =============================================================================
   Reads _data/food/cooking_methods.yml (serialised into the page as JSON by
   Liquid) and _data/food/internal_temperatures.yml, and answers ONE question:

     "How long does a 2.4 kg chicken take?"   -> a protein and a weight

   IT USED TO ANSWER TWO. "What time do I put it in for lunch at 2?" was the
   other, from an optional serving time and a rest, and it is gone with its two
   boxes (issue #244, Helen: "needs to be much clearer for a user"). Two boxes
   were optional, two were not, and four inputs asked you to decide which
   question you were asking before the page had shown you it could answer
   either. What is left is the shape of the question you actually ask while
   deciding HOW to cook something: every method, with its own oven temperature
   and its own total.

   The clock arithmetic behind the removed answer is still in cook-schedule.js,
   uncalled and deliberately kept -- read the note at the top of that file
   before tidying it away.

   -----------------------------------------------------------------------------
   THE ARITHMETIC IS NOT IN THIS FILE
   -----------------------------------------------------------------------------
   Every number — resolving a method to a range of minutes, rounding, the
   backwards-from-the-plate clock maths, the temperature and rest-time lookups —
   lives in assets/js/cook-schedule.js as HTF.cookSchedule, which touches no DOM
   and is tested directly by tests/js/cook-schedule.test.js. That file must load
   FIRST; tests/test_site_config.py has a guard.

   What stays here is the wiring: reading the two boxes, ordering the cards,
   building the markup, and the copy around a refusal.

   -----------------------------------------------------------------------------
   THE HARD PART IS THE 21% OF ROWS THAT AREN'T A FORMULA
   -----------------------------------------------------------------------------
   52 of the 66 method rows are `rate` -- minutes per kg, sometimes plus a flat
   addition -- and multiplying is all they need. The other 14 are five different
   things, and the temptation is to coerce them into a number anyway so every
   row has an answer. That would be the worst thing this page could do: a
   confident "3 hrs 20 mins" derived from a row whose own sources disagree by
   3:1 is worse than no calculator, because it launders uncertainty into
   precision.

   So each shape is handled on its own terms, and two of them REFUSE:

     rate         multiply, add the flat part
     total        a fixed time; ignores the weight box and says so on screen
     staged       two rates in sequence, reported as two stages
     by_doneness  a rate per doneness level; shows the one you picked
     relative     defined against another row -- resolved, and the row it
                  borrowed from is named in the output
     disputed     shows the range and the reason, and declines to time it
     unparsed     shows the original wording, and declines

   A refusal is a real answer here, not a gap. Duck spatchcocked is
   "~20–60 min/kg — genuinely conflicting sources": a three-fold spread that
   nobody should turn into a single figure.
   ========================================================================== */

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
    heading: root.querySelector("#ct-protein-name"),
    doneat: root.querySelector("#ct-doneat"),
    table: root.querySelector("#ct-table"),
    summary: root.querySelector("#ct-summary"),
    // The two halves the dropdown swaps between -- issue #412.
    calculator: root.querySelector("#ct-calculator"),
    fish: root.querySelector("#ct-fish-shellfish")
  };

  /* --- render -------------------------------------------------------------- */

  /* One method's time, as the table cell and the card headline both want it.
     A by_doneness method (issue #246) shows EVERY level rather than the one
     the page happens to have asked for -- see HTF.cookSchedule.resolve for why
     both figures and not a control. Everything else is a single span, exactly
     as before. */
  function timeHtml(r) {
    if (!r.ok) return null;
    if (!r.levels || r.levels.length < 2) return CS.span(r.lo, r.hi);
    return "<span class='ct-doneness'>" + r.levels.map(function (lv) {
      return "<span class='ct-doneness-level'>" +
               "<span class='ct-doneness-label'>" + lv.label + "</span>" +
               CS.span(lv.lo, lv.hi) +
             "</span>";
    }).join("") + "</span>";
  }

  function render() {
    /* THE SWAP, BEFORE ANYTHING ELSE. `protein` is undefined for the fish entry
       -- it is not in METHODS by design -- so every line below would throw on
       protein.label. Returning here is not an early-return-on-empty of the kind
       MANUAL §12 warns about: this is a different mode of the page, not an
       absent value. */
    var showingFish = els.protein.value === FISH_KEY;
    if (els.calculator) els.calculator.hidden = showingFish;
    if (els.fish) els.fish.hidden = !showingFish;
    if (showingFish) return;

    var protein = METHODS[els.protein.value];
    var kg = parseFloat(els.weight.value);
    var doneness = "rare";

    els.table.innerHTML = "";

    /* THE HEADING AND THE FINISHING TEMPERATURE ARE ABOUT THE PROTEIN, NOT THE
       WEIGHT, so both are written before the weight is even checked -- an
       emptied weight box must not blank the heading the page is sitting under.
       They are the two halves of one statement ("BEEF / done at 52-54°C"), and
       the way out to the full spectrum goes with the figure: this page shows a
       single doneness at a time and should say so where it says the number. */
    els.heading.textContent = protein.label;

    var temp = CS.finishingTemp(TEMPS, protein.internal_temp_ref);
    els.doneat.innerHTML = temp
      ? "<strong>Done at " + temp + "</strong>" +
        /* ../internal-temperatures/, renamed by issue #384. This link is BUILT
           AT RUNTIME, which is why the rename missed it and why nothing caught
           it: tests/test_page_links.py reads `<a href>` attributes out of
           templates, and the production-build scanner reads static HTML, so a
           link that does not exist until JS runs is invisible to both. It
           pointed at a deleted page for a day.

           Relative rather than root-relative, deliberately: JS has no Liquid
           and so no `relative_url`, and a literal /food/... would drop the
           /helen-triages baseurl and 404 in production while working perfectly
           on localhost -- the same trap MANUAL §4 records for front matter.
           `../` resolves against the current page's URL, baseurl included. */
        (protein.chart_anchor
          ? "<a href='../internal-temperatures/#" + protein.chart_anchor +
            "'>see other doneness</a>"
          : "")
      : "";

    if (!kg || kg <= 0) {
      els.summary.textContent = "Enter a weight to see how long each method takes.";
      return;
    }

    /* CLEARED, not written. The count -- "7 ways to cook 2.4 kg of beef" --
       went in issue #253: it sat directly above a table of exactly those
       seven, so it announced what the next element already showed, in less
       useful form. This element survives for the one thing the table cannot
       say for itself, above: that there is no usable weight yet, at the
       moment when the table is empty and silent about why.

       Clearing it here matters. Leaving the previous prompt in place after a
       weight is typed would strand "Enter a weight to see how long each
       method takes" above a filled table. */
    els.summary.textContent = "";

    /* --- the decision table ------------------------------------------------
       What you get, and what it costs you in time, at a length you can scan.
       Uses the site's existing table styles (article.recipe
       .recipe-body-content table) and the .table-scroll wrapper that already
       exists for wide tables -- no new CSS.

       THE CARDS UNDER IT ARE GONE -- #873, Helen, 2026-09-09: "I realised
       thanks to the design audit that they're not adding information beyond
       the table, and remain a little hard to read." One card per method sat
       below this table repeating its name and time with the oven setting, the
       stages of a multi-stage method, and the caveats; the table is the answer
       now. HTF.cookSchedule.resolve still returns `stages`, `aside` and `why`
       for anything that wants them; nothing on this page reads them today.

       Shortest first, decliners last -- see HTF.cookSchedule.orderMethods for
       why that order and not alphabetical. */
    var ordered = CS.orderMethods(protein.methods, kg, doneness);

    var rows = ordered.map(function (method) {
      var r = CS.resolve(method, kg, doneness, protein.methods);
      return "<tr>" +
        "<td>" + method.name + "</td>" +
        "<td>" + (method.outcome || "—") + "</td>" +
        "<td>" + (r.ok ? timeHtml(r) : "<em>won’t guess</em>") + "</td>" +
        "</tr>";
    }).join("");

    els.table.innerHTML =
      "<table><thead><tr><th>Method</th><th>What you get</th><th>Time</th>" +
      "</tr></thead><tbody>" + rows + "</tbody></table>";
  }

  /* THE REST BOX AND ITS TOOLTIP WERE HERE. The box carried the selected
     protein's own stated rest time where the data published one and a working
     20 where it didn't, with a title attribute saying which of the two you were
     looking at. All of it went with the box (#244): the only thing rest was
     ever used for on this page was subtracting it from a serving time.
     HTF.cookSchedule.restFor and statedRest survive it -- see cook-schedule.js.

     Nothing listens for a protein change here any more either. That handler
     existed to reload the rest figure; the re-render is driven by the delegated
     input/change listeners at the bottom of this file, as it always was. */

  /* FISH AND SHELLFISH ARE A DROPDOWN ENTRY, NOT A PROTEIN -- issue #412.
     Picking it puts the calculator away and shows the static section instead.

     The value is deliberately not a key in METHODS and never can be: every
     entry there carries a weight-driven rate, and these two have none. Fish is
     governed by thickness and shellfish by the moment the shell opens, so there
     is nothing for a weight box to compute. Helen: "Not cooked by time."

     It sits LAST in the list rather than alphabetically among the proteins,
     because it is a different kind of answer -- the nine above all respond to
     the weight box, and this one replaces it. */
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

  /* ?protein=beef, so the temperature charts can link to the timings for the
     protein you were just looking at rather than to whatever the dropdown
     happens to open on. Ignored silently if it names something this page
     doesn't have -- a bad query string is not worth an error message on a
     page that works perfectly well without it. */
  var wanted = (location.search.match(/[?&]protein=([a-z]+)/) || [])[1];
  if (wanted && METHODS[wanted]) els.protein.value = wanted;

  ["input", "change"].forEach(function (evt) {
    root.addEventListener(evt, render);
  });
  render();
})();
