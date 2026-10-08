"""The food reference pages' candidates page: MANUAL 13.11, round one. Ships nothing.

REPRODUCES NO NUMBER -- it rebuilds the pages Helen chooses from, and is kept in
scripts/ so round two does not start from a script that was in tmp/ and is gone
(the lesson of the leopard's round two, LEOPARD.md section 4).

ROUND ONE, 2026-10-08, from Helen's three rulings that day: the oven setting
goes back on a method row ("200 fan for 10 mins then 180 fan for an hour? If
so then yes"); the charts stay one scroll "with good nav"; every tooltip is
gone (#1326, already shipped). ON THE BAR:

  charts   row    today | one line (label and figure on one line, bar under)
                        | thermometer (a vertical scale, levels as brackets)
           nav    today | sticky jump bar (the contents list sticks and scrolls
                          sideways; the "top" links go)
  methods  shape  table (with an oven column) | stacked (one block per method)
           groups flat (shortest first) | by cut (the data's own `group`)
           fish   table | list | list, no notes

Everything here sits on top of the built stylesheet as overrides keyed off
html[data-*]; nothing in _sass/ changes until she has chosen. The methods page
drops the live cook-timer.js and inlines a candidate renderer (CAND_TIMER) that
writes BOTH tables so the switch is pure CSS; the arithmetic is still the live
HTF.cookSchedule. The fish and shellfish lists are parsed out of the page's own
tables (fish_lists), so they cannot drift from them.

Build first:
  bundle exec jekyll build --config _config.yml,_config_local.yml -d tmp/site-mock
Then:
  python3 scripts/reference_candidates.py
Writes tmp/refcand/index.html (the Artifact's body: the charts page),
charts.html and methods.html (full documents, published beside it) and
phone.html (both pages at 390px, three treatments side by side, for an iPad or
a desktop where a 600px breakpoint never fires -- MANUAL 11.2.1). Parse
tmp/refcand/switcher.js before publishing.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mock_bundle

# --- the questions ----------------------------------------------------------
CHART_GROUPS = [
    ("row", "Chart row", [("today", "today"), ("line", "one line"), ("thermo", "thermometer")]),
    ("nav", "Navigation", [("today", "today"), ("sticky", "sticky jump bar")]),
]
CHART_DEFAULTS = {"row": "today", "nav": "today"}

METHOD_GROUPS = [
    ("shape", "Method rows", [("table", "table"), ("stacked", "stacked")]),
    ("groups", "Order", [("flat", "shortest first"), ("cut", "by cut")]),
    ("fish", "Fish and shellfish", [("table", "table"), ("list", "list"), ("bare", "list, no notes")]),
]
METHOD_DEFAULTS = {"shape": "table", "groups": "flat", "fish": "table"}

# The site's own values, copied rather than imported: this file runs with no
# Sass. _sass/food/_palette.scss and _sass/shared/_tokens.scss are the source.
BG, TEXT, BORDER, CLEAR, VIOLET = "#faf7f8", "#211f20", "#ebdbe0", "#4f4e4a", "#7734EA"
FONT_H = '"Courier Prime", "Courier New", Courier, monospace'
FONT_L = '"IBM Plex Mono", "Courier Prime", monospace'
FONT_B = '"Selawik", -apple-system, "Segoe UI", Roboto, sans-serif'
TMIN, TMAX = 35, 100
R = TMAX - TMIN

# --- the switcher bar (not part of the site) ---------------------------------
BAR_CSS = """
html { color-scheme: light; }
.rc-bar {
  position: sticky; top: env(safe-area-inset-top, 0px); z-index: 9999;
  display: flex; flex-wrap: wrap; gap: 6px 18px; align-items: center;
  padding: 8px 16px; background: #000; border-bottom: 1px solid #44444a;
  font: 13px/1.3 system-ui, sans-serif; color: #e8e6e2; letter-spacing: 0; -webkit-text-stroke: 0;
}
.rc-group { display: flex; flex-wrap: wrap; gap: 4px; align-items: center; min-width: 0; }
.rc-group-label { color: #97959a; margin-right: 4px; }
.rc-bar button, .rc-bar a.rc-page {
  font: inherit; color: #e8e6e2; background: #1c1c20; border: 1px solid #44444a;
  padding: 3px 9px; border-radius: 3px; cursor: pointer; text-decoration: none;
}
.rc-bar button[aria-pressed="true"] { background: #e8e6e2; color: #000; border-color: #e8e6e2; }
.rc-bar button:focus-visible, .rc-bar a.rc-page:focus-visible { outline: 2px solid #ff00c8; outline-offset: 1px; }
"""


def bar_html(groups, links):
    parts = ['<div class="rc-bar" role="toolbar" aria-label="Reference candidates">']
    for attr, label, options in groups:
        parts.append(f'<div class="rc-group"><span class="rc-group-label">{label}</span>')
        for value, text in options:
            parts.append(f'<button type="button" data-rc-attr="{attr}" data-rc-value="{value}" aria-pressed="false">{text}</button>')
        parts.append("</div>")
    parts.append('<div class="rc-group">')
    for href, text in links:
        parts.append(f'<a class="rc-page" href="{href}">{text}</a>')
    parts.append("</div></div>")
    return "\n".join(parts)


SWITCHER = """
(function () {
  var DEFAULTS = %s;
  var KEY = %s;
  var state = {};
  try { state = JSON.parse(localStorage.getItem(KEY) || "{}") || {}; } catch (e) { state = {}; }
  /* A query string wins over memory and is never saved: phone.html's iframes
     ask for one treatment each and must not overwrite the choice on the page
     Helen is actually looking at. */
  var fixed = {};
  try {
    var q = new URLSearchParams(location.search);
    Object.keys(DEFAULTS).forEach(function (attr) { if (q.get(attr)) { fixed[attr] = q.get(attr); } });
  } catch (e) {}
  var root = document.documentElement;
  function apply() {
    Object.keys(DEFAULTS).forEach(function (attr) {
      var value = fixed[attr] || state[attr] || DEFAULTS[attr];
      root.setAttribute("data-" + attr, value);
      var buttons = document.querySelectorAll('[data-rc-attr="' + attr + '"]');
      for (var i = 0; i < buttons.length; i++) {
        buttons[i].setAttribute("aria-pressed", buttons[i].getAttribute("data-rc-value") === value ? "true" : "false");
      }
    });
  }
  function barHeight() {
    var bar = document.querySelector(".rc-bar");
    root.style.setProperty("--bar-h", (bar ? bar.offsetHeight : 0) + "px");
  }
  document.addEventListener("click", function (ev) {
    var b = ev.target.closest ? ev.target.closest("[data-rc-attr]") : null;
    if (!b) { return; }
    state[b.getAttribute("data-rc-attr")] = b.getAttribute("data-rc-value");
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
    apply();
  });
  window.addEventListener("resize", barHeight);
  apply();
  barHeight();
})();
"""


def switcher(defaults, key):
    return SWITCHER % (json.dumps(defaults), json.dumps(key))


# --- the charts page ----------------------------------------------------------
L = 'html[data-row="line"] .tc'
T = 'html[data-row="thermo"] .tc:not(#all ~ .tc)'
N = 'html[data-nav="sticky"]'


def chart_css():
    css = f"""
/* ONE LINE: label left and figure right on one line, the bar under them at the
   column's full width. The label gutter goes, so the track is a fifth wider
   on a desktop and the whole width on a phone. */
{L} {{ --tc-label-w: 0px; --tc-label-gap: 0px; }}
{L} .tc-row {{
  grid-template-columns: minmax(0, 1fr) auto; grid-template-rows: auto auto;
  row-gap: 0; column-gap: 0.75rem; min-height: 0; align-items: end;
}}
{L} .tc-row-label {{ grid-row: 1; grid-column: 1; text-align: left; }}
{L} .tc-value {{
  grid-row: 1; grid-column: 2; position: static; display: block; text-align: right;
  white-space: normal; margin: 0; padding: 0; align-self: end; justify-self: end; line-height: 1.3;
}}
{L} .tc-track {{ grid-row: 2; grid-column: 1 / -1; height: 1.5rem; }}
{L} .tc-axis {{ grid-template-columns: 1fr; }}

/* THERMOMETER: one vertical scale per chart, {TMIN}–{TMAX}°C top to bottom, each
   level a bracket in its own thin column, its words to the right at the
   height of its out-at figure. Rows become display:contents so the words
   position against the plot and can wrap to the column's edge. The All chart
   stays horizontal: eleven brackets would need eleven columns. */
{T} {{
  position: relative; --th-h: 600px; --th-axis: 3rem; --th-col: 1.2rem; --th-n: 6;
  padding-left: var(--th-axis); padding-top: 0.7rem; margin-bottom: 3rem;
}}
{T} .tc-plot {{
  position: relative; height: var(--th-h); padding-top: 0;
  border-left: 1px solid {BORDER};
  background-image: repeating-linear-gradient(to bottom, {BORDER} 0, {BORDER} 1px, transparent 1px, transparent calc(100% * 10 / {R}));
  background-size: 100% 100%;
}}
{T} .tc-row {{ display: contents; }}
{T} .tc-track {{
  position: absolute; top: 0; bottom: 0; height: auto;
  left: calc(var(--th-col) * var(--th-i, 0)); width: var(--th-col);
}}
{T} .tc-out-at, {T} .tc-rested {{
  left: 0.2rem; width: 0.8rem; min-width: 0; min-height: 3px;
  top: calc((({TMAX} - var(--b)) / {R}) * 100%); height: calc(((var(--b) - var(--a)) / {R}) * 100%);
}}
{T} .tc-carry {{
  left: calc(0.6rem - 1px); width: 2px; min-width: 0;
  top: calc((({TMAX} - var(--b)) / {R}) * 100%); height: calc(((var(--b) - var(--a)) / {R}) * 100%);
  background: repeating-linear-gradient(to bottom, rgba(119, 52, 234, 0.9) 0 3px, transparent 3px 6px);
}}
{T} .tc-row-label, {T} .tc-value {{
  position: absolute; left: calc(var(--th-col) * var(--th-n) + 0.75rem); right: 0;
  top: calc((({TMAX} - var(--a)) / {R}) * 100% + var(--th-dy, 0em));
  margin: 0; padding: 0; text-align: left; white-space: normal; line-height: 1.2; font-size: 0.72rem;
}}
{T} .tc-row-label {{ transform: translateY(-100%); }}
/* Four whole birds share one figure, so their words would print on top of
   each other: each bird's pair steps down from the one before. The turkey's
   value runs to three lines, hence the uneven steps. */
html[data-row="thermo"] #poultry ~ .tc .tc-row:nth-child(2 of .tc-row) {{ --th-dy: 2.8em; }}
html[data-row="thermo"] #poultry ~ .tc .tc-row:nth-child(3 of .tc-row) {{ --th-dy: 8em; }}
html[data-row="thermo"] #poultry ~ .tc .tc-row:nth-child(4 of .tc-row) {{ --th-dy: 10.8em; }}
{T} .tc-unsafe {{
  top: calc((({TMAX} - var(--t)) / {R}) * 100%); bottom: 0; left: 0; right: 0; width: auto;
  border-right: none; border-top: 2px dashed rgba(33, 31, 32, 0.45);
}}
{T} .tc-threshold-label {{
  left: auto; right: 0; top: calc((({TMAX} - var(--t)) / {R}) * 100%);
  transform: translateY(-100%); padding: 0 0 2px 0;
}}
{T} .tc-axis {{ position: absolute; left: 0; top: 0.7rem; width: var(--th-axis); height: var(--th-h); display: block; margin: 0; }}
{T} .tc-axis > div:first-child {{ display: none; }}
{T} .tc-axis-scale {{ position: absolute; inset: 0; height: auto; border-top: none; }}
{T} .tc-tick {{ left: auto; right: 0.45rem; top: calc((({TMAX} - var(--t)) / {R}) * 100%); transform: translateY(-50%); padding: 0; }}
"""
    for i in range(1, 7):
        css += f"{T} .tc-row:nth-child({i} of .tc-row) {{ --th-i: {i - 1}; }}\n"
        css += f"{T} .tc-plot:has(.tc-row:nth-child({i} of .tc-row):nth-last-child(1 of .tc-row)) {{ --th-n: {i}; }}\n"
    css += f"""
/* STICKY JUMP BAR: the contents list sticks under the candidates bar and
   scrolls sideways as a row of chips; the "top" links are redundant then. */
{N} article.recipe .tc-contents {{
  position: sticky; top: var(--bar-h, 0px); z-index: 20;
  display: flex; gap: 0.4rem; overflow-x: auto; columns: auto; max-width: none;
  margin: 0 0 2.5rem 0; padding: 0.6rem 0; background: {BG}; border-bottom: 1px solid {BORDER};
  list-style: none; scrollbar-width: none; -webkit-overflow-scrolling: touch;
}}
{N} article.recipe .tc-contents::-webkit-scrollbar {{ display: none; }}
{N} article.recipe .tc-contents li {{ flex: 0 0 auto; margin: 0; padding: 0; }}
{N} article.recipe .tc-contents li::before {{ content: none; }}
{N} article.recipe .tc-contents a {{
  display: inline-block; font-family: {FONT_H}; font-size: 0.68rem; letter-spacing: 0.06em;
  text-transform: uppercase; text-decoration: none; color: {TEXT}; background: #fff;
  border: 1px solid {BORDER}; border-radius: 999px; padding: 0.3rem 0.65rem; white-space: nowrap;
}}
{N} .tc-totop {{ display: none; }}
{N} article.recipe .recipe-section-heading {{ scroll-margin-top: calc(var(--bar-h, 0px) + 4rem); }}
"""
    return css


# --- the methods page ---------------------------------------------------------
# A copy of assets/js/cook-timer.js's wiring that writes two tables -- shortest
# first, and grouped by the data's own `group` -- each row carrying the oven
# setting. The arithmetic is the live HTF.cookSchedule; nothing is recomputed.
CAND_TIMER = r"""
(function () {
  "use strict";
  var root = document.querySelector("[data-cook-timer]");
  if (!root) return;
  var CS = window.HTF.cookSchedule;
  var METHODS = JSON.parse(document.getElementById("ct-methods").textContent);
  var TEMPS = JSON.parse(document.getElementById("ct-temps").textContent);
  var els = {
    protein: root.querySelector("#ct-protein"), weight: root.querySelector("#ct-weight"),
    heading: root.querySelector("#ct-protein-name"), doneat: root.querySelector("#ct-doneat"),
    table: root.querySelector("#ct-table"), summary: root.querySelector("#ct-summary"),
    calculator: root.querySelector("#ct-calculator"), fish: root.querySelector("#ct-fish-shellfish")
  };
  var FISH_KEY = "fish-shellfish";
  /* A range may break only at its dash: each half is a nowrap span. */
  function span(lo, hi) {
    return CS.span(lo, hi).split(" – ").map(function (half) {
      return "<span class='ct-t'>" + half + "</span>";
    }).join(" – ");
  }
  function timeHtml(r) {
    if (!r.ok) return null;
    if (!r.levels || r.levels.length < 2) return span(r.lo, r.hi);
    return "<span class='ct-doneness'>" + r.levels.map(function (lv) {
      return "<span class='ct-doneness-level'><span class='ct-doneness-label'>" + lv.label + "</span>" + span(lv.lo, lv.hi) + "</span>";
    }).join("") + "</span>";
  }
  function rowHtml(method, r) {
    return "<tr>" +
      "<td class='ct-m-name'>" + method.name + "</td>" +
      "<td class='ct-m-oven'>" + (method.oven || "—") + "</td>" +
      "<td class='ct-m-out'>" + (method.outcome || "—") + "</td>" +
      "<td class='ct-m-time'>" + (r.ok ? timeHtml(r) : "<em>won’t guess</em>") + "</td></tr>";
  }
  function groupHtml(name) {
    var bits = name.split(" — ");
    return "<tr class='ct-group'><th colspan='4'><span class='ct-group-name'>" + bits[0] + "</span>" +
      (bits[1] ? "<span class='ct-group-cuts'>" + bits[1] + "</span>" : "") + "</th></tr>";
  }
  function table(body) {
    return "<table class='ct-cand'><thead><tr><th>Method</th><th>Oven</th><th>What you get</th><th>Time</th></tr></thead>" + body + "</table>";
  }
  function render() {
    var showingFish = els.protein.value === FISH_KEY;
    if (els.calculator) els.calculator.hidden = showingFish;
    if (els.fish) els.fish.hidden = !showingFish;
    if (showingFish) return;
    var protein = METHODS[els.protein.value];
    var kg = parseFloat(els.weight.value);
    var doneness = "rare";
    els.table.innerHTML = "";
    els.heading.textContent = protein.label;
    var temp = CS.finishingTemp(TEMPS, protein.internal_temp_ref);
    els.doneat.innerHTML = temp
      ? "<strong>Done at " + temp + "</strong>" + (protein.chart_anchor ? "<a href='#' onclick='return false'>see other doneness</a>" : "")
      : "";
    if (!kg || kg <= 0) { els.summary.textContent = "Enter a weight to see how long each method takes."; return; }
    els.summary.textContent = "";
    var ordered = CS.orderMethods(protein.methods, kg, doneness);
    var row = function (m) { return rowHtml(m, CS.resolve(m, kg, doneness, protein.methods)); };
    var flat = "<tbody>" + ordered.map(row).join("") + "</tbody>";
    var groups = [];
    protein.methods.forEach(function (m) { if (groups.indexOf(m.group) < 0) groups.push(m.group); });
    var grouped = groups.map(function (g) {
      return "<tbody>" + groupHtml(g) + ordered.filter(function (m) { return m.group === g; }).map(row).join("") + "</tbody>";
    }).join("");
    els.table.innerHTML = "<div class='ct-flat'>" + table(flat) + "</div><div class='ct-grouped'>" + table(grouped) + "</div>";
  }
  CS.proteinOrder(METHODS).forEach(function (key) {
    var opt = document.createElement("option");
    opt.value = key; opt.textContent = METHODS[key].label; els.protein.appendChild(opt);
  });
  var fish = document.createElement("option");
  fish.value = FISH_KEY; fish.textContent = "Fish and shellfish"; els.protein.appendChild(fish);
  var wanted = (location.search.match(/[?&]protein=([a-z]+)/) || [])[1];
  if (wanted && METHODS[wanted]) els.protein.value = wanted;
  ["input", "change"].forEach(function (evt) { root.addEventListener(evt, render); });
  render();
})();
"""

S = 'html[data-shape="stacked"] article.recipe .recipe-body-content'


def method_css():
    return f"""
/* The oven column, both shapes. Figures are the site's label face, as the
   time column already was. */
article.recipe .recipe-body-content .ct-cand .ct-m-time {{ font-family: {FONT_L}; font-weight: 600; white-space: nowrap; }}
article.recipe .recipe-body-content .ct-cand .ct-m-oven {{ font-size: 0.86rem; }}
article.recipe .recipe-body-content .ct-cand .ct-m-out {{ color: {CLEAR}; font-size: 0.86rem; }}
html[data-groups="flat"] .ct-grouped {{ display: none; }}
html[data-groups="cut"] .ct-flat {{ display: none; }}

/* BY CUT: a row of its own per group, in the data's words, the cut list
   trailing the name in the body face. */
article.recipe .recipe-body-content .ct-cand tr.ct-group th {{
  text-align: left; white-space: normal; padding-top: 1.6rem; border-bottom: 1px solid {BORDER};
  color: {TEXT}; font-size: 0.74rem; letter-spacing: 0.08em;
}}
article.recipe .recipe-body-content .ct-cand tbody:first-of-type tr.ct-group th {{ padding-top: 0.5rem; }}
article.recipe .recipe-body-content .ct-cand .ct-group-cuts {{
  font-family: {FONT_B}; text-transform: none; letter-spacing: 0; color: {CLEAR}; font-size: 0.8rem; margin-left: 0.6rem;
}}

/* STACKED: one block per method -- name and time on the first line, the oven
   setting under them, the outcome last and quiet. The table markup stays so
   the switch is only CSS. */
{S} .ct-cand {{ display: block; width: 100%; }}
{S} .ct-cand thead {{ display: none; }}
{S} .ct-cand tbody {{ display: block; }}
{S} .ct-cand tr {{
  display: grid; grid-template-columns: minmax(0, 1fr) auto; column-gap: 1rem; row-gap: 0.15rem;
  grid-template-areas: "name time" "oven oven" "out out";
  padding: 0.75rem 0; border-bottom: 1px solid {BORDER};
}}
{S} .ct-cand td {{ display: block; padding: 0; border: 0; min-width: 0; }}
{S} .ct-cand .ct-m-name {{ grid-area: name; font-size: 1rem; }}
{S} .ct-cand .ct-m-time {{ grid-area: time; text-align: right; white-space: normal; max-width: 10.5rem; }}
{S} .ct-cand .ct-t {{ white-space: nowrap; }}
{S} .ct-cand .ct-m-oven {{ grid-area: oven; }}
{S} .ct-cand .ct-m-out {{ grid-area: out; font-style: italic; font-size: 0.82rem; }}
{S} .ct-cand tr.ct-group {{ display: block; padding: 1.6rem 0 0.4rem 0; border-bottom: 2px solid {BORDER}; }}
{S} .ct-cand tbody:first-of-type tr.ct-group {{ padding-top: 0.25rem; }}
{S} .ct-cand tr.ct-group th {{ display: block; padding: 0; border: 0; }}
{S} .ct-cand .ct-doneness {{ align-items: flex-end; }}

/* FISH AND SHELLFISH as a list: one entry per fish, its forms as lines. */
html[data-fish="table"] .fish-list {{ display: none; }}
html[data-fish="list"] .fish-table, html[data-fish="bare"] .fish-table {{ display: none; }}
html[data-fish="bare"] .fish-list i {{ display: none; }}
article.recipe .recipe-body-content .fish-list {{ margin: 0 0 1.5rem 0; max-width: 62ch; }}
article.recipe .recipe-body-content .fish-list .fish-item {{ padding: 0.6rem 0; border-bottom: 1px solid {BORDER}; }}
article.recipe .recipe-body-content .fish-list dt {{
  font-family: {FONT_H}; font-size: 0.78rem; letter-spacing: 0.06em; text-transform: uppercase; margin: 0 0 0.2rem 0;
}}
article.recipe .recipe-body-content .fish-list dd {{ margin: 0 0 0.15rem 0; font-size: 0.92rem; line-height: 1.45; }}
article.recipe .recipe-body-content .fish-list b {{ font-weight: 600; margin-right: 0.35rem; }}
article.recipe .recipe-body-content .fish-list i {{ color: {CLEAR}; font-size: 0.84rem; }}
"""


CELL = re.compile(r"<td(?: rowspan=\"\d+\")?>(.*?)</td>", re.S)


def table_rows(table_html):
    return [CELL.findall(tr) for tr in re.findall(r"<tr>(.*?)</tr>", table_html, re.S)]


def fish_lists(body):
    """Append a <dl> after each of the two fish tables, built from the table."""
    def section(body, anchor, has_form):
        start = body.index(f'id="{anchor}"')
        t0 = body.index('<div class="table-scroll">', start)
        t1 = body.index("</div>", body.index("</table>", t0)) + len("</div>")
        table = body[t0:t1]
        rows = table_rows(table[table.index("<tbody>"):])
        items, current = [], None
        for cells in rows:
            if has_form and len(cells) == 3:
                current[1].append(cells)
                continue
            current = (cells[0], [cells[1:]])
            items.append(current)
        out = ['<dl class="fish-list">']
        for name, forms in items:
            out.append(f'<div class="fish-item"><dt>{name}</dt>')
            for cells in forms:
                if has_form:
                    form, methods, note = (cells + [""])[:3]
                    out.append(f"<dd><b>{form}</b> {methods}" + (f" <i>{note}</i>" if note else "") + "</dd>")
                else:
                    methods, note = (cells + [""])[:2]
                    out.append(f"<dd>{methods}" + (f" <i>{note}</i>" if note else "") + "</dd>")
            out.append("</div>")
        out.append("</dl>")
        wrapped = table.replace('<div class="table-scroll">', '<div class="table-scroll fish-table">', 1)
        return body[:t0] + wrapped + "\n" + "\n".join(out) + body[t1:]
    body = section(body, "fish", True)
    body = section(body, "shellfish", False)
    return body


# --- assembly ------------------------------------------------------------------
def document(inner):
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            "</head>\n<body>\n" + inner + "\n</body>\n</html>\n")


def charts_page(links):
    return mock_bundle.bundle(
        "food/reference/internal-temperatures/index.html", "food.css", "Reference Pages Round One",
        extra_style=BAR_CSS + chart_css(),
        body_transform=lambda body: bar_html(CHART_GROUPS, links) + body,
        extra_scripts="<script>" + switcher(CHART_DEFAULTS, "refcand-charts-1") + "</script>",
    )


def methods_page(links):
    return mock_bundle.bundle(
        "food/reference/cooking-methods-and-timings/index.html", "food.css", "Reference Pages Round One",
        extra_style=BAR_CSS + method_css(),
        body_transform=lambda body: bar_html(METHOD_GROUPS, links) + fish_lists(body),
        extra_scripts="<script>" + CAND_TIMER + "</script><script>" + switcher(METHOD_DEFAULTS, "refcand-methods-1") + "</script>",
        drop_scripts=("cook-timer.js",),
    )


PHONE = """<title>Reference Pages Round One</title>
<style>
  body { margin: 0; padding: 12px 16px; background: #faf7f8; color: #211f20; font: 14px/1.4 system-ui, sans-serif; }
  h1 { font-size: 15px; margin: 8px 0; }
  .row { display: flex; gap: 14px; overflow-x: auto; padding-bottom: 12px; }
  figure { margin: 0; flex: 0 0 auto; }
  figcaption { font-size: 12px; color: #4f4e4a; margin: 0 0 6px 0; }
  iframe { width: 390px; height: 760px; border: 1px solid #c9c4c7; border-radius: 10px; background: #fff; }
  a { color: #c4009a; }
</style>
<p><a href="index.html">charts, full size</a> · <a href="methods.html">methods, full size</a></p>
<h1>Internal temperatures at 390px</h1>
<div class="row">
  <figure><figcaption>today</figcaption><iframe src="charts.html?row=today&amp;nav=today" title="charts, today"></iframe></figure>
  <figure><figcaption>one line, sticky jump bar</figcaption><iframe src="charts.html?row=line&amp;nav=sticky" title="charts, one line"></iframe></figure>
  <figure><figcaption>thermometer, sticky jump bar</figcaption><iframe src="charts.html?row=thermo&amp;nav=sticky" title="charts, thermometer"></iframe></figure>
</div>
<h1>Cooking methods at 390px</h1>
<div class="row">
  <figure><figcaption>today's shape, with oven</figcaption><iframe src="methods.html?shape=table&amp;groups=flat&amp;fish=table" title="methods, table"></iframe></figure>
  <figure><figcaption>table, by cut</figcaption><iframe src="methods.html?shape=table&amp;groups=cut&amp;fish=list" title="methods, table by cut"></iframe></figure>
  <figure><figcaption>stacked, by cut</figcaption><iframe src="methods.html?shape=stacked&amp;groups=cut&amp;fish=bare" title="methods, stacked"></iframe></figure>
</div>
"""


if __name__ == "__main__":
    out = os.path.join(ROOT, "tmp", "refcand")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "switcher.js"), "w", encoding="utf-8") as fh:
        fh.write(switcher(CHART_DEFAULTS, "x") + "\n" + CAND_TIMER)
    links = [("methods.html", "the methods page"), ("phone.html", "both at phone width")]
    charts = charts_page(links)
    mock_bundle.write(os.path.join(out, "index.html"), charts)
    mock_bundle.write(os.path.join(out, "charts.html"), document(charts))
    methods = methods_page([("index.html", "the charts page"), ("phone.html", "both at phone width")])
    mock_bundle.write(os.path.join(out, "methods.html"), document(methods))
    mock_bundle.write(os.path.join(out, "phone.html"), document(PHONE))
