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
    out: root.querySelector("#ct-results"),
    summary: root.querySelector("#ct-summary")
  };

  /* --- render -------------------------------------------------------------- */

  function render() {
    var protein = METHODS[els.protein.value];
    var kg = parseFloat(els.weight.value);
    var doneness = "rare";

    els.out.innerHTML = "";
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
        (protein.chart_anchor
          ? "<a href='../temperatures/#" + protein.chart_anchor +
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
       The cards below answer "how long does this method take". They do not
       answer "which method", which is the question you actually have first --
       and seven cards, each with a time and a paragraph, is not something you
       can compare at a glance. This is the same information at a length you can
       scan: what you get, and what it costs you in time.

       Table for choosing, cards for doing. Uses the site's existing table
       styles (article.recipe .recipe-body-content table) and the .table-scroll
       wrapper that already exists for wide tables -- no new CSS.

       Shortest first, decliners last -- see HTF.cookSchedule.orderMethods for
       why that order and not alphabetical. */
    var ordered = CS.orderMethods(protein.methods, kg, doneness);

    var rows = ordered.map(function (method) {
      var r = CS.resolve(method, kg, doneness, protein.methods);
      return "<tr>" +
        "<td>" + method.name + "</td>" +
        "<td>" + (method.outcome || "—") + "</td>" +
        "<td>" + (r.ok ? CS.span(r.lo, r.hi) : "<em>won’t guess</em>") + "</td>" +
        "</tr>";
    }).join("");

    els.table.innerHTML =
      "<table><thead><tr><th>Method</th><th>What you get</th><th>Time</th>" +
      "</tr></thead><tbody>" + rows + "</tbody></table>";

    ordered.forEach(function (method) {
      var r = CS.resolve(method, kg, doneness, protein.methods);
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
          "<p class='ct-total'>" + (r.ok ? CS.span(r.lo, r.hi) : "—") + "</p>" +
        "</div>";

      /* NO `outcome` LINE ON THE CARD. It was here to "confirm" the choice you
         made in the table above -- but the table already says it, three
         paragraphs up, and repeating it made the card open with two
         near-identical sentences ("Reliable default" then "Reliable, even
         results; use a thermometer"). Helen: "below that it's still a bit of a
         clutter." The table is where you choose; the card is where you get the
         things the table has no room for. */
      var settings = [];
      if (method.oven) settings.push(method.oven);
      if (method.covering) settings.push(method.covering.toLowerCase());
      if (settings.length) {
        html += "<p class='ct-settings'>" + settings.join(" &middot; ") + "</p>";
      }

      var asides = [];

      if (r.ok) {

        if (r.stages) {
          html += "<ul class='ct-stages'>" + r.stages.map(function (st) {
            return "<li><span>" + st.name + "</span> " + CS.span(st.lo, st.hi) + "</li>";
          }).join("") + "</ul>";
        }

        /* THE IN-AT / OUT-AT / REST-UNTIL LIST WAS HERE, and went with the two
           boxes that fed it (#244). It was the only part of a card that needed
           to know what time you were eating. */

        if (r.aside) asides.push(r.aside);
      } else {
        html += "<p class='ct-declined'>Won’t guess this one.</p>" +
                "<p class='ct-aside'>" + r.why + "</p>";
      }

      /* Caveats and notes end the card as ONE quiet block. They were two
         paragraphs at full spacing, which gave a footnote the same presence as
         the answer above it. */
      if (method.notes) asides.push(method.notes);
      if (asides.length) {
        html += "<p class='ct-notes'>" + asides.join(" ") + "</p>";
      }

      card.innerHTML = html;
      els.out.appendChild(card);
    });
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

  function fillProteins() {
    CS.proteinOrder(METHODS).forEach(function (key) {
      var opt = document.createElement("option");
      opt.value = key;
      opt.textContent = METHODS[key].label;
      els.protein.appendChild(opt);
    });
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
