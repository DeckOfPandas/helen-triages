"""The "I'm open to chaos" chip's tape: MANUAL 13.11, one round (#1369). Ships nothing.

Build first:
  bundle exec jekyll build --config _config.yml,_config_local.yml -d tmp/site-mock
Then:
  python3 scripts/chaos_chip_candidates.py

Writes tmp/chaoscand/index.html (the Artifact's body: the real cocktail index
with a bar on top) and phone.html (every candidate at 390px side by side).

The switches on the bar:

  tape    today | 1 | 2 | 6 | 7 | 9   the chip's `data-tag-shape`
  chip    resting | chosen            the chip clicked on, as a reader sees it

The candidates are POOL in assets/js/decorations.js less the two shapes its
neighbours wear ("no chaos please" and "chaos only", computed by the same
hash) and less 4, the mirror of today's 4-flip. Setting the attribute and
calling the live HTF.tagShapes() is exactly what shipping a pick does.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mock_bundle
from reference_candidates import BAR_CSS, bar_html, switcher, document

CANDIDATES = ["1", "2", "6", "7", "9"]
GROUPS = [
    ("tape", "Open to chaos: tape", [("today", "today (4-flip)")] + [(c, f"shape {c}") for c in CANDIDATES]),
    ("chip", "Chip", [("resting", "resting"), ("chosen", "chosen")]),
]
DEFAULTS = {"tape": "today", "chip": "resting"}

APPLY = """
(function () {
  var root = document.documentElement;
  var chip = document.querySelector('.btn-chaos[data-chaos="open"]');
  if (!chip) { return; }
  function sync() {
    var tape = root.getAttribute('data-tape');
    if (tape === 'today') { chip.removeAttribute('data-tag-shape'); }
    else { chip.setAttribute('data-tag-shape', 'tag-shape-' + tape); }
    if (window.HTF && HTF.tagShapes) { HTF.tagShapes(); }
    var want = root.getAttribute('data-chip') === 'chosen';
    if ((chip.getAttribute('aria-pressed') === 'true') !== want) { chip.click(); }
  }
  new MutationObserver(sync).observe(root, { attributes: true, attributeFilter: ['data-tape', 'data-chip'] });
  sync();
  /* Open on the chaos row, not the masthead. */
  var row = document.querySelector('.drink-filter--chaos');
  if (row && !location.hash) { row.scrollIntoView({ block: 'center' }); }
})();
"""


def index_page(links):
    return mock_bundle.bundle(
        "cocktails/index.html", "cocktails.css", "Chaos Chip Tape",
        extra_style=BAR_CSS,
        body_transform=lambda body: bar_html(GROUPS, links) + body,
        extra_scripts="<script>" + switcher(DEFAULTS, "chaoscand-1369") + "</script><script>" + APPLY + "</script>",
    )


def phone_page():
    figures = []
    for tape, label in [("today", "today (4-flip)")] + [(c, f"shape {c}") for c in CANDIDATES]:
        for chip in ("resting", "chosen"):
            src = f"cocktails.html?tape={tape}&amp;chip={chip}"
            figures.append(f'<figure><figcaption>{label}, {chip}</figcaption>'
                           f'<iframe src="{src}" title={json.dumps(label + ", " + chip)}></iframe></figure>')
    return """<title>Chaos Chip Tape at 390px</title>
<style>
  body { margin: 0; padding: 12px 16px; background: #0c0c0e; color: #e8e6e2; font: 14px/1.4 system-ui, sans-serif; }
  h1 { font-size: 15px; margin: 8px 0; }
  .row { display: flex; gap: 14px; overflow-x: auto; padding-bottom: 12px; }
  figure { margin: 0; flex: 0 0 auto; }
  figcaption { font-size: 12px; color: #97959a; margin: 0 0 6px 0; }
  iframe { width: 390px; height: 420px; border: 1px solid #44444a; border-radius: 10px; background: #000; }
  a { color: #ff00c8; }
</style>
<p><a href="index.html">the cocktail index, full size, with the switches</a></p>
<h1>Every candidate at 390px, resting and chosen</h1>
<div class="row">
""" + "\n".join(figures) + "\n</div>\n"


if __name__ == "__main__":
    out = os.path.join(ROOT, "tmp", "chaoscand")
    os.makedirs(out, exist_ok=True)
    page = index_page([("phone.html", "all of them at phone width")])
    mock_bundle.write(os.path.join(out, "index.html"), page)
    mock_bundle.write(os.path.join(out, "cocktails.html"), document(page))
    mock_bundle.write(os.path.join(out, "phone.html"), document(phone_page()))
