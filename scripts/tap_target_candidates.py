"""Tap areas on a phone: MANUAL 13.11, round two. Ships nothing.

Build first:
  bundle exec jekyll build --config _config.yml,_config_local.yml -d tmp/site-mock
Then:
  python3 scripts/tap_target_candidates.py

Writes tmp/tapcand/index.html (the Artifact's body: the Mai Tai's page with a
bar on top), drink.html and cocktails.html (full documents of the drink page
and the cocktail index, sharing the bar's memory), and phone.html (both at
390px side by side).

Round one settled three (Helen): read it / make it and the header doors
take a 44px tap area, and "deal again" is a bit bigger. Those are base CSS
here. The switches left on the bar:

  steppers  today | 32 | big   the − and + beside the multiple box: a 32px
                               tap area, or BIG -- 32x32 buttons with a
                               larger glyph, 12px gaps, and a 44px tap area
                               that stops short of the multiple box
  show      off | on           paints the tap areas so they can be judged

A tap area is an invisible ::after centred on the control: the steppers grow
both ways, the toggle and the doors in height only, so neighbours never
overlap. At today's 5px gaps a 44px stepper area would cover 3.5px of the
box, which is why 44 needs the bigger buttons. 44 is Apple's guidance.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mock_bundle
from reference_candidates import BAR_CSS, bar_html, switcher, document

GROUPS = [
    ("steppers", "− / +", [("today", "today"), ("32", "32px area"), ("big", "bigger buttons, 44px area")]),
    ("show", "show tap areas", [("off", "off"), ("on", "on")]),
]
DEFAULTS = {"steppers": "big", "show": "on"}
KEY = "tapcand-2"

AREA = ('content: ""; position: absolute; left: 50%; top: 50%; '
        'transform: translate(-50%, -50%);')

DECIDED = f"""
/* decided in round one: 44px tall areas, and deal again a bit bigger */
.cocktail-toggle-label, .cocktail-toggle-track, .site-nav-icon-link {{ position: relative; }}
.cocktail-toggle-label::after, .cocktail-toggle-track::after, .site-nav-icon-link::after {{
  {AREA} width: 100%; height: max(100%, 44px);
}}
.btn-universe-again {{ font-size: 0.92rem; padding: 0.3rem 0; }}
"""

STEPPERS = f"""
html[data-steppers="32"] .cocktail-scale-step,
html[data-steppers="big"] .cocktail-scale-step {{ position: relative; }}
html[data-steppers="32"] .cocktail-scale-step::after {{
  {AREA} width: max(100%, 32px); height: max(100%, 32px);
}}
/* BIG: a 2rem square button, the glyph up a third, the row's gaps to 12px,
   so a 44px area reaches 6px past the button and stops short of the box. */
html[data-steppers="big"] .cocktail-scale-controls {{ gap: 0.75rem; }}
html[data-steppers="big"] .cocktail-scale-step {{
  width: 2rem; height: 2rem; padding: 0; font-size: 1.25rem; line-height: 1;
}}
html[data-steppers="big"] .cocktail-scale-step::after {{ {AREA} width: 44px; height: 44px; }}
"""

SHOW = """
html[data-show="on"] .cocktail-scale-step::after,
html[data-show="on"] .cocktail-toggle-label::after,
html[data-show="on"] .cocktail-toggle-track::after,
html[data-show="on"] .site-nav-icon-link::after {
  background: rgba(255, 0, 200, 0.28); outline: 1px solid #ff00c8;
}
html[data-show="on"] .btn-universe-again { outline: 1px dashed #ff00c8; }
"""


def css():
    return DECIDED + STEPPERS + SHOW


def page(path, title, links):
    return mock_bundle.bundle(
        path, "cocktails.css", title,
        extra_style=BAR_CSS + css(),
        body_transform=lambda body: bar_html(GROUPS, links) + body,
        extra_scripts="<script>" + switcher(DEFAULTS, KEY) + "</script>",
    )


PHONE = """<title>Tap Areas at 390px</title>
<style>
  body { margin: 0; padding: 12px 16px; background: #0c0c0e; color: #e8e6e2; font: 14px/1.4 system-ui, sans-serif; }
  .row { display: flex; gap: 14px; overflow-x: auto; padding-bottom: 12px; }
  figure { margin: 0; flex: 0 0 auto; }
  figcaption { font-size: 12px; color: #97959a; margin: 0 0 6px 0; }
  iframe { width: 390px; height: 760px; border: 1px solid #44444a; border-radius: 10px; background: #000; }
  a { color: #ff00c8; }
</style>
<p><a href="index.html">the drink page, full size, with the switches</a> · the phone frames below follow the switches you last chose there</p>
<div class="row">
  <figure><figcaption>the Mai Tai</figcaption><iframe src="drink.html" title="drink page"></iframe></figure>
  <figure><figcaption>the cocktail index</figcaption><iframe src="cocktails.html" title="cocktail index"></iframe></figure>
</div>
"""

if __name__ == "__main__":
    out = os.path.join(ROOT, "tmp", "tapcand")
    os.makedirs(out, exist_ok=True)
    links = [("cocktails.html", "the index (deal again)"), ("phone.html", "both at phone width")]
    drink = page("cocktails/recipes/mai-tai/index.html", "Tap Areas", links)
    index = page("cocktails/index.html", "Tap Areas: Index",
                 [("drink.html", "the drink page"), ("phone.html", "both at phone width")])
    mock_bundle.write(os.path.join(out, "index.html"), drink)
    mock_bundle.write(os.path.join(out, "drink.html"), document(drink))
    mock_bundle.write(os.path.join(out, "cocktails.html"), document(index))
    mock_bundle.write(os.path.join(out, "phone.html"), document(PHONE))
