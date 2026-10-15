"""Tap areas on a phone: MANUAL 13.11, one round. Ships nothing.

Build first:
  bundle exec jekyll build --config _config.yml,_config_local.yml -d tmp/site-mock
Then:
  python3 scripts/tap_target_candidates.py

Writes tmp/tapcand/index.html (the Artifact's body: the Mai Tai's page with a
bar on top), drink.html and cocktails.html (full documents of the drink page
and the cocktail index, sharing the bar's memory), and phone.html (both at
390px side by side).

The switches on the bar:

  steppers  today | 32 | 44    the − and + beside the multiple box
  toggle    today | 32 | 44    read it / the switch / make it
  doors     today | 32 | 44    the header's links to the other site and ??
  deal      today | a bit | more    "deal again": the VISIBLE size
  show      off | on           paints the tap areas so they can be judged

A tap area is an invisible ::after centred on the control, at least the
chosen size in each direction it has room for: the steppers grow both ways,
the toggle and the doors grow in height only, so neighbours never overlap.
Nothing on screen moves. 44 is Apple's guidance, 24 WCAG 2.2's floor.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mock_bundle
from reference_candidates import BAR_CSS, bar_html, switcher, document

SIZES = [("today", "today"), ("32", "32px"), ("44", "44px")]
GROUPS = [
    ("steppers", "− / +", SIZES),
    ("toggle", "read / make", SIZES),
    ("doors", "header doors", SIZES),
    ("deal", "deal again", [("today", "today"), ("bit", "a bit bigger"), ("more", "bigger")]),
    ("show", "show tap areas", [("off", "off"), ("on", "on")]),
]
DEFAULTS = {"steppers": "44", "toggle": "44", "doors": "44", "deal": "bit", "show": "on"}
KEY = "tapcand-1"

# (switch, selector, grows sideways too)
TARGETS = [
    ("steppers", ".cocktail-scale-step", True),
    ("toggle", ".cocktail-toggle-label, .cocktail-toggle-track", False),
    ("doors", ".site-nav-icon-link", False),
]


def css():
    out = ["/* the tap area: invisible unless shown */"]
    for attr, sel, wide in TARGETS:
        for size in ("32", "44"):
            hosts = ", ".join(f'html[data-{attr}="{size}"] {s.strip()}' for s in sel.split(","))
            afters = ", ".join(f'html[data-{attr}="{size}"] {s.strip()}::after' for s in sel.split(","))
            width = f"max(100%, {size}px)" if wide else "100%"
            out.append(f"{hosts} {{ position: relative; }}")
            out.append(f"{afters} {{ content: \"\"; position: absolute; left: 50%; top: 50%; "
                       f"width: {width}; height: max(100%, {size}px); transform: translate(-50%, -50%); }}")
    for attr, sel, _ in TARGETS:
        afters = ", ".join(f'html[data-show="on"] {s.strip()}::after' for s in sel.split(","))
        out.append(f"{afters} {{ background: rgba(255, 0, 200, 0.28); outline: 1px solid #ff00c8; }}")
    out.append("""
/* deal again: the visible size */
html[data-deal="bit"] .btn-universe-again { font-size: 0.92rem; padding: 0.3rem 0; }
html[data-deal="more"] .btn-universe-again { font-size: 1.02rem; padding: 0.45rem 0; }
html[data-show="on"] .btn-universe-again { outline: 1px dashed #ff00c8; }
""")
    return "\n".join(out)


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
