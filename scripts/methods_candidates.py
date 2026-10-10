"""The methods page's candidates page: MANUAL 13.11, round four. Ships nothing.

Kept in scripts/ beside reference_candidates.py (round one) for the same
reason it is: a later round should not start from a tmp/ that is gone.

ROUND FOUR, 2026-10-09. Round three promoted the outcome to the second line of
a method block (violet, 600) and gave the cut-group and fish names the
heading lettering with the violet rule, and Helen's read was: "I love most
of this! It's just the 'jollier headings' request. There is a LOT going on
now. Perhaps some extra vertical space between sections (particularly above
the top rows) would help. Perhaps giving in and swapping the outcome to be
first place would help. Maybe a different font for the method (e.g.
'sugar-rubbed roast') would help?" Three perhapses, so three switches on
the real page rather than a guess:

  space   today | more        air above each group heading, between the
                               heading and its first block, between blocks
  lead    method | outcome    which of the two is the block's first line,
                               beside the time
  face    body | courier | italic   the method name's face

Everything sits on top of the built stylesheet as overrides keyed off
html[data-*]; nothing in _sass/ changes until she has chosen. The live
cook-timer.js renders the blocks; only CSS moves.

Build first:
  bundle exec jekyll build --config _config.yml,_config_local.yml -d tmp/site-mock
Then:
  python3 scripts/methods_candidates.py
Writes tmp/refcand4/index.html (the Artifact's body), methods.html (a full
document) and phone.html (three treatments at 390px side by side).
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mock_bundle
from reference_candidates import BAR_CSS, bar_html, switcher, document, FONT_H, CLEAR, TEXT

GROUPS = [
    ("space", "Spacing", [("today", "today"), ("more", "more air")]),
    ("lead", "First line", [("method", "method"), ("outcome", "outcome")]),
    ("face", "Method name", [("body", "body face"), ("courier", "courier"), ("italic", "italic")]),
]
DEFAULTS = {"space": "today", "lead": "method", "face": "body"}

B = "article.recipe .recipe-body-content"


def css():
    return f"""
/* MORE AIR: a section's worth above each group heading, a clear gap between
   the heading (and its cuts line) and the first block, and taller blocks. */
html[data-space="more"] .ct-group + .ct-group {{ margin-top: 4rem; }}
html[data-space="more"] .ct-group:first-child {{ margin-top: 1rem; }}
html[data-space="more"] {B} h3.ct-group-name {{ margin-bottom: 1.4rem; }}
html[data-space="more"] .ct-group-cuts {{ margin-top: 0.6rem; }}
html[data-space="more"] .ct-method {{ padding: 1.15rem 0; row-gap: 0.3rem; }}

/* OUTCOME FIRST: the outcome is the headline beside the time, the method's
   name is the second line. */
html[data-lead="outcome"] .ct-method {{ grid-template-areas: "outcome time" "name name" "oven oven"; }}
html[data-lead="outcome"] .ct-method-outcome {{ font-size: 1.02rem; }}
html[data-lead="outcome"] .ct-method-name {{ font-size: 0.92rem; }}

/* THE METHOD NAME'S FACE. Courier is the site's label vocabulary, lowercase
   as the filter chips and search boxes wear it; italic is the body face
   leaning, the voice of a tagline or a subtitle. */
html[data-face="courier"] .ct-method-name {{
  font-family: {FONT_H}; font-size: 0.86rem; letter-spacing: 0.02em; color: {TEXT};
}}
html[data-face="courier"][data-lead="outcome"] .ct-method-name {{ font-size: 0.8rem; color: {CLEAR}; }}
html[data-face="italic"] .ct-method-name {{ font-style: italic; }}
html[data-face="italic"][data-lead="outcome"] .ct-method-name {{ color: {CLEAR}; }}
"""


def methods_page(links):
    return mock_bundle.bundle(
        "food/reference/cooking-methods-and-timings/index.html", "food.css", "Methods Page Round Four",
        extra_style=BAR_CSS + css(),
        body_transform=lambda body: bar_html(GROUPS, links) + body,
        extra_scripts="<script>" + switcher(DEFAULTS, "refcand-methods-4") + "</script>",
    )


PHONE = """<title>Methods Page Round Four</title>
<style>
  body { margin: 0; padding: 12px 16px; background: #faf7f8; color: #211f20; font: 14px/1.4 system-ui, sans-serif; }
  h1 { font-size: 15px; margin: 8px 0; }
  .row { display: flex; gap: 14px; overflow-x: auto; padding-bottom: 12px; }
  figure { margin: 0; flex: 0 0 auto; }
  figcaption { font-size: 12px; color: #4f4e4a; margin: 0 0 6px 0; }
  iframe { width: 390px; height: 760px; border: 1px solid #c9c4c7; border-radius: 10px; background: #fff; }
  a { color: #c4009a; }
</style>
<p><a href="index.html">the methods page, full size, with the switches</a></p>
<h1>Venison at 390px</h1>
<div class="row">
  <figure><figcaption>today</figcaption><iframe src="methods.html?protein=venison&amp;space=today&amp;lead=method&amp;face=body#ct-methods" title="today"></iframe></figure>
  <figure><figcaption>more air, outcome first</figcaption><iframe src="methods.html?protein=venison&amp;space=more&amp;lead=outcome&amp;face=body#ct-methods" title="more air, outcome first"></iframe></figure>
  <figure><figcaption>more air, outcome first, courier name</figcaption><iframe src="methods.html?protein=venison&amp;space=more&amp;lead=outcome&amp;face=courier#ct-methods" title="more air, outcome first, courier"></iframe></figure>
  <figure><figcaption>more air, method first, italic name</figcaption><iframe src="methods.html?protein=venison&amp;space=more&amp;lead=method&amp;face=italic#ct-methods" title="more air, italic"></iframe></figure>
</div>
"""


if __name__ == "__main__":
    out = os.path.join(ROOT, "tmp", "refcand4")
    os.makedirs(out, exist_ok=True)
    links = [("phone.html", "four treatments at phone width")]
    page = methods_page(links)
    mock_bundle.write(os.path.join(out, "index.html"), page)
    mock_bundle.write(os.path.join(out, "methods.html"), document(page))
    mock_bundle.write(os.path.join(out, "phone.html"), document(PHONE))
