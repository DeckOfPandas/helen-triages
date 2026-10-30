"""The jump pill's candidates page (#1441): MANUAL 13.11, round one. Ships nothing.

Build first:
  bundle exec jekyll build --config _config.yml,_config_local.yml -d tmp/site-mock
Then:
  python3 scripts/jump_candidates.py

Writes tmp/jumpcand/index.html (the Artifact's body: the food index),
cocktails.html (a full document, published beside it) and phone.html (both
indexes at 390px, every treatment side by side). Parse tmp/jumpcand/switcher.js
before publishing.

One switch, the pill's colour:

  ink      the built stylesheet: the site's text colour behind its page ground
  accent   the site's accent behind its text colour
  outline  the page ground, a 2px rule and the words in the text colour

Everything sits on top of the built stylesheet as overrides keyed off
html[data-pill]; nothing in _sass/ changes.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mock_bundle
from reference_candidates import BAR_CSS, bar_html, document, switcher

GROUPS = [("pill", "Pill", [("ink", "ink"), ("accent", "accent"), ("outline", "outline")])]
DEFAULTS = {"pill": "ink"}

# The site's own values, copied rather than imported: this file runs with no
# Sass. _sass/food/_palette.scss and _sass/cocktails/_palette.scss are the
# source. Magenta behind the food text colour is 4.7:1; white on it fails.
SITES = {
    "food": {"bg": "#faf7f8", "text": "#211f20", "accent": "#FF00C8"},
    "cocktails": {"bg": "#030304", "text": "#e8e6e2", "accent": "#30E88C"},
}


def pill_css(site):
    c = SITES[site]
    return f"""
html[data-pill="accent"] .results-jump {{ background: {c["accent"]}; color: {c["bg"] if site == "cocktails" else c["text"]}; }}
html[data-pill="outline"] .results-jump {{ background: {c["bg"]}; color: {c["text"]}; box-shadow: inset 0 0 0 2px {c["text"]}, 0 4px 16px rgba(0, 0, 0, 0.3); }}
"""


def page(path, css_file, site, links):
    return mock_bundle.bundle(
        path, css_file, "Jump Pill Round One",
        extra_style=BAR_CSS + pill_css(site),
        body_transform=lambda body: bar_html(GROUPS, links) + body,
        extra_scripts="<script>" + switcher(DEFAULTS, "jumpcand-1") + "</script>",
    )


def phone():
    def row(src, title):
        figs = "".join(
            f'<figure><figcaption>{v}</figcaption><iframe src="{src}?pill={v}" title="{title}, {v}"></iframe></figure>'
            for v, _ in GROUPS[0][2])
        return f'<h1>{title} at 390px</h1>\n<div class="row">{figs}</div>'
    return f"""<title>Jump Pill Round One</title>
<style>
  body {{ margin: 0; padding: 12px 16px; background: #faf7f8; color: #211f20; font: 14px/1.4 system-ui, sans-serif; }}
  h1 {{ font-size: 15px; margin: 8px 0; }}
  .row {{ display: flex; gap: 14px; overflow-x: auto; padding-bottom: 12px; }}
  figure {{ margin: 0; flex: 0 0 auto; }}
  figcaption {{ font-size: 12px; color: #4f4e4a; margin: 0 0 6px 0; }}
  iframe {{ width: 390px; height: 760px; border: 1px solid #c9c4c7; border-radius: 10px; background: #fff; }}
  a {{ color: #c4009a; }}
</style>
<p><a href="index.html">food, full size</a> · <a href="cocktails.html">cocktails, full size</a></p>
{row("food.html", "Food index")}
{row("cocktails.html", "Cocktails index")}
"""


if __name__ == "__main__":
    out = os.path.join(ROOT, "tmp", "jumpcand")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "switcher.js"), "w", encoding="utf-8") as fh:
        fh.write(switcher(DEFAULTS, "x"))
    food = page("food/index.html", "food.css", "food",
                [("cocktails.html", "the cocktails index"), ("phone.html", "both at phone width")])
    mock_bundle.write(os.path.join(out, "index.html"), food)
    mock_bundle.write(os.path.join(out, "food.html"), document(food))
    cocktails = page("cocktails/index.html", "cocktails.css", "cocktails",
                     [("index.html", "the food index"), ("phone.html", "both at phone width")])
    mock_bundle.write(os.path.join(out, "cocktails.html"), document(cocktails))
    mock_bundle.write(os.path.join(out, "phone.html"), document(phone()))
