"""The search box's height and the index's floating controls: MANUAL 13.11,
round three for #1447 and #1448. Ships nothing.

Build first:
  bundle exec jekyll build --config _config.yml -d tmp/site-mock
Then:
  python3 scripts/index_float_candidates.py

Writes tmp/floatcand/: index.html (the food index, the Artifact's page),
food.html (the same as a whole document, for phone frames), cocktails.html,
food-recipe.html and phone.html beside it.

Settled in rounds one and two, so in every candidate here: one rule places
the box at every width on both sites; every "× clear all" is gone; the
sticky top bar is gone; one pill in #1445's place shows "top ↑" while the
filter panel is above the screen, "N survivors ↓" while the results are
below it, and, while any filter is on, "N survivors" with no arrow in
between, so it never leaves a filtered page; it carries × whenever a filter
is on. The one switch:

  box    125 | 150 | 175   the box 1.25 / 1.5 / 1.75rem under the header's
                           border. What sits under it at the right makes
                           just enough room: cocktails' universe line and a
                           recipe's print . pdf. Food's STAR never moves.

results-bar.js is left out of the bundle and replaced by FLOAT_JS, the
pill; everything else is the deployed build's own script and CSS.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mock_bundle
from reference_candidates import BAR_CSS, bar_html, switcher, document

GROUPS = [
    ("box", "Box", [("125", "1.25rem under"), ("150", "1.5rem under"), ("175", "1.75rem under")]),
]
DEFAULTS = {"box": "150"}
KEY = "floatcand-3"

PAGES = [
    ("index.html", "food/index.html", "food.css", "food index"),
    ("cocktails.html", "cocktails/index.html", "cocktails.css", "cocktails index"),
    ("food-recipe.html", "food/recipes/moules-mariniere/index.html", "food.css", "food recipe"),
]

B = "main > .page-search"
GLASS = "1.15rem"      # $page-search-mark-size: the box is the glass's height
GAP = "0.5rem"         # clear space under the box before what it would touch
PAD = "2rem"           # main's top padding ($space-xxl)


def css():
    out = []
    for value, top in (("125", "1.25rem"), ("150", "1.5rem"), ("175", "1.75rem")):
        room = f"max(0rem, calc({top} + {GLASS} + {GAP} - {PAD}))"
        out.append(f"""
html[data-box="{value}"] {{ --cand-room: {room}; }}
html[data-box="{value}"] {B} {{
  position: absolute !important; top: {top} !important; right: 1.5rem !important;
  margin: 0 !important; width: auto !important;
}}""")
    out.append("""
/* What sits under the box at the right makes just the room it needs. */
html .universe { margin-top: max(0.3rem, var(--cand-room)) !important; }
html .page-furniture { align-items: flex-start !important; }
html .page-furniture .page-print-actions { margin-top: var(--cand-room) !important; align-self: flex-start !important; }

/* Every "× clear all" is gone: the panel's top and foot, and the one in the
   no-survivors message. The pill's × does their job. Each section's own
   "× clear", the typing boxes' and cocktails' "clear ship" stay. */
.btn-clear { display: none !important; }

/* The sticky top bar and #1445's two pills: replaced by .cand-pill. */
[data-results-bar], [data-results-jump], [data-results-top] { display: none !important; }

/* "top" lands with the whole heading and its rule on screen. */
#filter-star, #filter-chaos { scroll-margin-top: 1rem; }

/* This round's switch bar scrolls away, so it cannot cover STAR. */
.rc-bar { position: static !important; }

.cand-pill { gap: 0 !important; padding: 0 0.25rem !important; cursor: default !important; }
.cand-pill:hover { text-decoration: none !important; }
.cand-pill button {
  font: inherit; color: inherit; background: none; border: 0; cursor: pointer;
  display: inline-flex; align-items: center; gap: 0.25rem;
  height: 1.4rem; padding: 0 0.5rem; border-radius: 999px; white-space: nowrap;
}
.cand-pill button > span, .cand-pill [data-count] { text-box: trim-both cap alphabetic; }
.cand-pill [data-count] { display: inline-flex; align-items: center; height: 1.4rem; padding: 0 0.5rem; white-space: nowrap; }
.cand-pill [data-count][hidden] { display: none; }
.cand-pill button[data-up] > span { text-box: trim-both ex alphabetic; }
.cand-pill button:hover, .cand-pill button:focus-visible { background: rgba(0,0,0,0.14); outline: none; }
.cand-pill button[data-x] { border-left: 1px solid currentColor; border-radius: 0 999px 999px 0; padding: 0 0.55rem 0 0.5rem; }
.cand-pill button[hidden] { display: none; }
.cand-pill .results-jump-arrow { width: 1.1em; height: 0.66em; transform: rotate(90deg); }
.cand-pill [data-up] .results-jump-arrow { transform: rotate(-90deg); }
""")
    return "".join(out)


# The pill: one element in #1445's place and look, showing either
# "N survivors ↓" or "top ↑", with a clear button beside it when the rule
# says so. `pill` decides only when "survivors" carries the clear button.
FLOAT_JS = r"""
(function () {
  function topClear() {
    var b = document.querySelectorAll('.btn-clear');
    for (var i = 0; i < b.length; i++) if (!b[i].closest('[data-results-bar]')) return b[i];
    return null;
  }
  function anyFilter() { var t = topClear(); return !!t && t.style.visibility === 'visible'; }
  function goTo(t) {
    t.scrollIntoView({ behavior: 'smooth', block: 'start' });
    if (!t.hasAttribute('tabindex')) t.setAttribute('tabindex', '-1');
    t.focus({ preventScroll: true });
  }
  function wire() {
    var heading = document.getElementById('results');
    var panel = document.querySelector('.controls, .drink-filters');
    var upTarget = document.getElementById('filter-star') || document.getElementById('filter-chaos');
    var n = document.getElementById('recipe-count-n') || document.getElementById('drink-count-n');
    var w = document.getElementById('recipe-count-word') || document.getElementById('drink-count-word');
    var arrow = document.querySelector('[data-results-jump] svg');
    if (!heading || !panel || !upTarget || !n || !w || !arrow) return;

    var pill = document.createElement('div');
    pill.className = 'results-jump cand-pill';
    pill.hidden = true;
    pill.innerHTML =
      '<span data-count><span class="results-count-number" data-n2></span>&nbsp;<span data-w2></span></span>' +
      '<button type="button" data-down><span><span class="results-count-number" data-n></span> <span data-w></span></span>' + arrow.outerHTML + '</button>' +
      '<button type="button" data-up><span>top</span>' + arrow.outerHTML + '</button>' +
      '<button type="button" data-x aria-label="Clear all filters">&times;</button>';
    document.body.appendChild(pill);
    var count = pill.querySelector('[data-count]');
    var down = pill.querySelector('[data-down]'), up = pill.querySelector('[data-up]'), x = pill.querySelector('[data-x]');

    down.addEventListener('click', function () { goTo(heading); });
    up.addEventListener('click', function () { goTo(upTarget); });
    x.addEventListener('click', function () { var t = topClear(); if (t) t.click(); place(); });

    /* Three states, and while any filter is on the pill never goes away:
       filters above, "top ↑ ×"; results below, "N survivors ↓ ×"; the count
       line on screen, "N survivors ×", with no arrow because there is
       nowhere to go. The × shows only when there is something to clear. */
    function place() {
      var h = heading.getBoundingClientRect(), p = panel.getBoundingClientRect();
      var filtersAbove = p.bottom <= 0;
      var countBelow = !filtersAbove && h.bottom > window.innerHeight;
      var on = anyFilter();
      ['[data-n]', '[data-n2]'].forEach(function (s) { pill.querySelector(s).textContent = n.textContent; });
      ['[data-w]', '[data-w2]'].forEach(function (s) { pill.querySelector(s).textContent = w.textContent; });
      up.hidden = !filtersAbove;
      down.hidden = !countBelow;
      count.hidden = filtersAbove || countBelow;
      x.hidden = !on;
      pill.hidden = !(filtersAbove || countBelow || on);
    }
    var queued = false;
    function soon() { if (queued) return; queued = true; requestAnimationFrame(function () { queued = false; place(); }); }
    window.addEventListener('scroll', soon, { passive: true });
    window.addEventListener('resize', soon);
    document.addEventListener('click', function () { setTimeout(place, 0); });
    new MutationObserver(soon).observe(document.documentElement, { attributes: true, attributeFilter: ['data-pill'] });
    new MutationObserver(soon).observe(n, { childList: true, characterData: true, subtree: true });
    setTimeout(place, 300);
    place();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', wire); else wire();
})();
"""


def page(src, css_file, links):
    return mock_bundle.bundle(
        src, css_file, "Index Float Candidates",
        extra_style=BAR_CSS + css(),
        body_transform=lambda body: bar_html(GROUPS, links) + body,
        extra_scripts="<script>" + FLOAT_JS + "</script><script>" + switcher(DEFAULTS, KEY) + "</script>",
        drop_scripts=("assets/js/results-bar.js",),
    )


def phone():
    def frame(src, cap):
        return f'<figure><figcaption>{cap}</figcaption><iframe src="{src}" title="{cap}"></iframe></figure>'
    box_rows = []
    for v, text in GROUPS[0][2]:
        figs = "".join(
            frame(f"{f}?box={v}&amp;{q}", f"{label}, box {text}")
            for f, q, label in (("food.html", "star=beef", "food"), ("cocktails.html", "mood=tiki", "cocktails"),
                                ("food-recipe.html", "x=1", "recipe")))
        box_rows.append(f"<h1>The box {text}</h1><div class=\"row\">{figs}</div>")
    figs = "".join(frame(f"{f}?box=150&amp;{q}{h}", f"{label}, {cap}")
                   for f, q, label in (("food.html", "star=beef", "food"), ("cocktails.html", "mood=tiki", "cocktails"))
                   for h, cap in (("", "at the filters"), ("#results", "landed on the results")))
    figs += "".join(frame(f"{f}?box=150", f"{label}, no filter chosen")
                    for f, label in (("food.html", "food"), ("cocktails.html", "cocktails")))
    pill_rows = [f"<h1>The pill</h1><p>Press “top” in a results frame to come back to the filters, and × to clear them.</p><div class=\"row\">{figs}</div>"]
    return """<title>Index Float Candidates</title>
<style>
  body { margin: 0; padding: 12px 16px; background: #faf7f8; color: #211f20; font: 14px/1.4 system-ui, sans-serif; }
  h1 { font-size: 15px; margin: 16px 0 4px; }
  p { margin: 0 0 8px; color: #4f4e4a; }
  .row { display: flex; gap: 14px; overflow-x: auto; padding-bottom: 12px; }
  figure { margin: 0; flex: 0 0 auto; }
  figcaption { font-size: 12px; color: #4f4e4a; margin: 0 0 6px 0; }
  iframe { width: 390px; height: 700px; border: 1px solid #c9c4c7; border-radius: 10px; background: #fff; }
  a { color: #c4009a; }
</style>
<p><a href="index.html">back to full size, with the switches</a></p>
""" + "\n".join(box_rows) + "\n" + "\n".join(pill_rows)


if __name__ == "__main__":
    out = os.path.join(ROOT, "tmp", "floatcand")
    os.makedirs(out, exist_ok=True)
    links = [(o, label) for o, _s, _c, label in PAGES] + [("phone.html", "at 390px")]
    for name, src, css_file, _label in PAGES:
        body = page(src, css_file, links)
        mock_bundle.write(os.path.join(out, name), body if name == "index.html" else document(body))
        # The Artifact wraps index.html in a document at publish; food.html is
        # that wrapping done here, so a phone frame gets a viewport tag.
        if name == "index.html":
            mock_bundle.write(os.path.join(out, "food.html"), document(body))
    mock_bundle.write(os.path.join(out, "phone.html"), document(phone()))
