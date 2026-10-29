"""The search box in the page body: MANUAL 13.11, one round. Ships nothing.

Settled: Helen picked `share`, which is now the site's own CSS
(shared/_layout.scss), so a build of today's tree shows it under the other
two switches as well. The round was built from the tree before that, when
the box was still behind a config key. Build first:
  bundle exec jekyll build --config _config.yml -d tmp/site-mock
Then:
  python3 scripts/omnisearch_candidates.py

Writes tmp/omnicand/: index.html (the food index, the Artifact's page), and
food-recipe.html, cocktails.html, cocktail-recipe.html and phone.html beside
it. default.html already renders the box as <main>'s first child; the
candidates only place it, as overrides keyed off html[data-place]:

  own     its own line at the top of the body, the page's own 2rem under the
          header's border; everything below moves down a line
  close   hung close under the border, as the door hangs under the tape; the
          page starts 1.5rem under the box
  share   the right-hand end of the page's first line, 2rem under the border;
          print . pdf drops beneath it, and cocktails' universe line moves down

page-search.js runs for real: each site's search.json is embedded and
answered from memory, so the dropdown opens.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mock_bundle
from reference_candidates import BAR_CSS, bar_html, switcher, document

GROUPS = [
    ("place", "Box", [("own", "A: own line"), ("close", "B: hung close"), ("share", "C: shares first line")]),
]
DEFAULTS = {"place": "own"}
KEY = "omnicand-place-1"

PAGES = [
    ("index.html", "food/index.html", "food.css", "food index"),
    ("food-recipe.html", "food/recipes/moules-mariniere/index.html", "food.css", "food recipe"),
    ("cocktails.html", "cocktails/index.html", "cocktails.css", "cocktails index"),
    ("cocktail-recipe.html", "cocktails/recipes/cobras-fang/index.html", "cocktails.css", "cocktail recipe"),
]

B = "main > .page-search"


def css():
    return f"""
/* Every candidate: the box at the column's right edge. */
{B} {{ width: fit-content; margin: 0 0 0 auto; }}

/* A: its own line, 2rem under the border (main's own padding), 1rem over the
   page. */
html[data-place="own"] {B} {{ margin-bottom: 1rem; }}

/* B: 0.5rem under the border, in main's top padding; 1.5rem over the page. */
html[data-place="close"] {B} {{ margin-top: -1.5rem; margin-bottom: 1.5rem; }}

/* C: out of the flow, at the top right of main's content box. */
html[data-place="share"] main {{ position: relative; }}
html[data-place="share"] {B} {{ position: absolute; top: 2rem; right: 1.5rem; z-index: 5; }}
html[data-place="share"] .page-furniture {{ flex-wrap: wrap; align-items: flex-start; }}
html[data-place="share"] .page-furniture .page-print-actions {{ margin-top: 2.2rem; }}
html[data-place="share"] .universe {{ margin-top: 2.6rem; }}
"""


def json_shim():
    data = {}
    for site in ("food", "cocktails"):
        path = os.path.join(mock_bundle.SITE, site, "search.json")
        with open(path, encoding="utf-8") as fh:
            data[mock_bundle.BASE + "/" + site + "/search.json"] = json.load(fh)
    return ("<script>(function () { var J = " + json.dumps(data) + ";"
            " var orig = window.HTF.fetchJson;"
            " window.HTF.fetchJson = function (url, cb) { if (J[url]) { cb(J[url]); return; } orig(url, cb); };"
            "})();</script>")


def picker():
    with open(os.path.join(ROOT, "assets", "js", "ingredient-search.js"), encoding="utf-8") as fh:
        return "<script>\n" + fh.read() + "\n</script>"


def page(src, css_file, links):
    html = mock_bundle._read(os.path.join(mock_bundle.SITE, src))
    extra = json_shim()
    if "ingredient-search.js" not in html and css_file == "food.css":
        extra = picker() + extra
    return mock_bundle.bundle(
        src, css_file, "Search Box Placement",
        extra_style=BAR_CSS + css(),
        body_transform=lambda body: bar_html(GROUPS, links) + body,
        extra_scripts=extra + "<script>" + switcher(DEFAULTS, KEY) + "</script>",
    )


def phone():
    rows = []
    for value, text in GROUPS[0][2]:
        frames = "".join(
            f'<figure><figcaption>{label}</figcaption>'
            f'<iframe src="{out}?place={value}" title="{text}, {label}"></iframe></figure>'
            for out, _src, _css, label in PAGES)
        rows.append(f"<h1>{text}</h1><div class=\"row\">{frames}</div>")
    return """<title>Search Box Placement</title>
<style>
  body { margin: 0; padding: 12px 16px; background: #faf7f8; color: #211f20; font: 14px/1.4 system-ui, sans-serif; }
  h1 { font-size: 15px; margin: 14px 0 8px; }
  .row { display: flex; gap: 14px; overflow-x: auto; padding-bottom: 12px; }
  figure { margin: 0; flex: 0 0 auto; }
  figcaption { font-size: 12px; color: #4f4e4a; margin: 0 0 6px 0; }
  iframe { width: 390px; height: 560px; border: 1px solid #c9c4c7; border-radius: 10px; background: #fff; }
  a { color: #c4009a; }
</style>
<p><a href="index.html">back to full size, with the switches</a></p>
""" + "\n".join(rows)


if __name__ == "__main__":
    out = os.path.join(ROOT, "tmp", "omnicand")
    os.makedirs(out, exist_ok=True)
    links = [(o, label) for o, _s, _c, label in PAGES] + [("phone.html", "all three at 390px")]
    for name, src, css_file, _label in PAGES:
        body = page(src, css_file, links)
        mock_bundle.write(os.path.join(out, name), body if name == "index.html" else document(body))
    mock_bundle.write(os.path.join(out, "phone.html"), document(phone()))
