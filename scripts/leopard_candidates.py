"""Leopard candidates on the real pages: the CANDIDATES PAGE of MANUAL 13.11. Ships nothing.

REPRODUCES NO NUMBER -- it rebuilds the page Helen chose the leopard from, and
is kept so the next round does not start from a script that was in tmp/ and is
gone, which is what happened to round two's (LEOPARD.md section 4).

THIS IS ROUND FIVE'S STATE, 2026-10-06, the last round before it shipped.
LOCKED into the page: fur crinkle, the darkest ground (#060607), nap texture,
on the page ground; the footer a plain band with no print; cards not touched.
ON THE BAR: how dark the header and footer bands should be, whether the repeat
is offset, and whether the header carries the print. She chose "same as the
page", offset, plain -- then, seeing the built bands were flat where this page
has the nap on them, "darker still" (b2), and after seeing THAT live,
"darker" (b1, #111113), which is what shipped. THIS PAGE'S BANDS STILL CARRY THE
NAP AND THE LIVE ONES DO NOT; fix that before asking about a band again.
All of that is on the live site now, so a NEW round
starts by changing GROUPS and the rules below to whatever the new question is;
the overrides here sit on top of the built stylesheet.

Build first:
  bundle exec jekyll build --config _config.yml,_config_local.yml -d tmp/site-mock
Writes tmp/leopard/index.html (the Artifact's body) and tmp/leopard/drink.html
(published beside it as a supporting file). Parse tmp/leopard/switcher.js
before publishing: one bad character in it once cost a whole round.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mock_bundle
from leopard_splodge import splodge_tile, ground_tile

DRINK = "negroni"
GROUND = "#060607"

GROUPS = [
    ("band", "Header and footer", [("b0", "today"), ("b1", "darker"), ("b2", "darker still"), ("b3", "same as the page")]),
    ("repeat", "Repeat", [("offset", "offset"), ("straight", "straight (as before)")]),
    ("headprint", "Header print", [("plain", "plain"), ("leopard", "leopard")]),
]
DEFAULTS = {"band": "b1", "repeat": "offset", "headprint": "plain"}
BANDS = {"b0": "#17171a", "b1": "#111113", "b2": "#0c0c0d", "b3": GROUND}
COLUMNS = 3


def candidate_css():
    props, rules = [], []
    for key, columns in (("straight", 1), ("offset", COLUMNS)):
        uri, n, _svg, width = splodge_tile(crinkle="fur", columns=columns)
        props.append(f'--leo-{key}: url("{uri}");')
        rules.append(f'html[data-repeat="{key}"] {{ --splodge: var(--leo-{key}); --splodge-w: {width}px; }}')
        print(f"splodge {key:9} {n / 1024:.0f} KB, {width}px wide")
    uri, n, _svg = ground_tile("nap")
    props.append(f'--tex: url("{uri}");')
    for key, colour in BANDS.items():
        rules.append(f'html[data-band="{key}"] {{ --band: {colour}; }}')
    return ":root {\n" + "\n".join(props) + "\n}\n" + "\n".join(rules) + CANDIDATE_RULES.replace("GROUND", GROUND)


CANDIDATE_RULES = """
html { overflow-x: clip; --band: #17171a; }
/* LOCKED: fur on the darkest ground with nap, on the page ground */
body {
  background-color: GROUND;
  background-image: var(--splodge), var(--tex);
  background-size: var(--splodge-w, 960px) 960px, 480px 480px;
}
/* OPEN: the header band's colour, and whether it carries the print */
.site-header { background-color: var(--band); background-image: var(--tex); background-size: 480px 480px; }
html[data-headprint="leopard"] .site-header {
  background-image: var(--splodge), var(--tex); background-size: var(--splodge-w, 960px) 960px, 480px 480px;
}
/* the footer: a plain full-width band in the header's colour, no print */
.site-footer { position: relative; isolation: isolate; border-top-color: transparent; }
.site-footer::before {
  content: ""; position: absolute; top: 0; bottom: 0; left: calc(50% - 50vw); width: 100vw; z-index: -1;
  background-color: var(--band); background-image: var(--tex); background-size: 480px 480px;
  border-top: 1px solid #2c2c31;
}

/* the switcher bar: not part of the site */
.leo-bar {
  position: sticky; top: env(safe-area-inset-top, 0px); z-index: 9999;
  display: flex; flex-wrap: wrap; gap: 6px 18px; align-items: center;
  padding: 8px 16px; background: #000; border-bottom: 1px solid #44444a;
  font: 13px/1.3 system-ui, sans-serif; color: #e8e6e2; letter-spacing: 0; -webkit-text-stroke: 0;
}
.leo-group { display: flex; flex-wrap: wrap; gap: 4px; align-items: center; min-width: 0; }
.leo-group-label { color: #97959a; margin-right: 4px; }
.leo-bar button, .leo-bar a.leo-page {
  font: inherit; color: #e8e6e2; background: #1c1c20; border: 1px solid #44444a;
  padding: 3px 9px; border-radius: 3px; cursor: pointer; text-decoration: none;
}
.leo-bar button[aria-pressed="true"] { background: #e8e6e2; color: #000; border-color: #e8e6e2; }
.leo-bar button:focus-visible, .leo-bar a.leo-page:focus-visible { outline: 2px solid #ff00c8; outline-offset: 1px; }
"""


def bar_html(other_href, other_label):
    parts = ['<div class="leo-bar" role="toolbar" aria-label="Leopard candidates">']
    for attr, label, options in GROUPS:
        parts.append(f'<div class="leo-group"><span class="leo-group-label">{label}</span>')
        for value, text in options:
            parts.append(f'<button type="button" id="leo-{attr}-{value}" data-leo-attr="{attr}" data-leo-value="{value}" aria-pressed="false">{text}</button>')
        parts.append("</div>")
    parts.append(f'<div class="leo-group"><a class="leo-page" href="{other_href}">{other_label}</a></div>')
    parts.append("</div>")
    return "\n".join(parts)


SWITCHER = """
(function () {
  var DEFAULTS = %s;
  var KEY = "leopard-round-five";
  var state = {};
  try { state = JSON.parse(localStorage.getItem(KEY) || "{}") || {}; } catch (e) { state = {}; }
  var root = document.documentElement;
  function apply() {
    Object.keys(DEFAULTS).forEach(function (attr) {
      var value = state[attr] || DEFAULTS[attr];
      root.setAttribute("data-" + attr, value);
      var buttons = document.querySelectorAll('[data-leo-attr="' + attr + '"]');
      for (var i = 0; i < buttons.length; i++) {
        buttons[i].setAttribute("aria-pressed", buttons[i].getAttribute("data-leo-value") === value ? "true" : "false");
      }
    });
  }
  document.addEventListener("click", function (ev) {
    var b = ev.target.closest ? ev.target.closest("[data-leo-attr]") : null;
    if (!b) { return; }
    state[b.getAttribute("data-leo-attr")] = b.getAttribute("data-leo-value");
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
    apply();
  });
  apply();
})();
""" % json.dumps(DEFAULTS)


def page(src, other_href, other_label, css):
    return mock_bundle.bundle(
        src, "cocktails.css", "Leopard Round Two",
        extra_style=css,
        body_transform=lambda body: bar_html(other_href, other_label) + body,
        extra_scripts="<script>" + SWITCHER + "</script>",
    )


if __name__ == "__main__":
    out = os.path.join(ROOT, "tmp", "leopard")
    os.makedirs(out, exist_ok=True)
    css = candidate_css()
    with open(os.path.join(out, "switcher.js"), "w", encoding="utf-8") as fh:
        fh.write(SWITCHER)
    mock_bundle.write(os.path.join(out, "index.html"),
                      page("cocktails/index.html", "drink.html", "see a drink page", css))
    drink = page(f"cocktails/recipes/{DRINK}/index.html", "index.html", "back to the index", css)
    mock_bundle.write(os.path.join(out, "drink.html"),
                      '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
                      '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
                      "</head>\n<body>\n" + drink + "\n</body>\n</html>\n")
