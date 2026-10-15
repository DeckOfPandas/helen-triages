"""The 404 page's doors: MANUAL 13.11, one round (#1382, "Tape doors?"). Ships nothing.

Build first:
  bundle exec jekyll build --config _config.yml,_config_local.yml -d tmp/site-mock
Then:
  python3 scripts/notfound_candidates.py

Writes tmp/notfoundcand/index.html (the Artifact's body: the real 404 page
with a bar on top), notfound.html (a full document) and phone.html (every
treatment at 390px side by side).

The switch on the bar:

  doors   today | tape | tape + icon | tape row

Each tape door is the cocktail cards' name tape: a `[data-card-tape]` slot
that decorations.js's cardTapes() fills with a random tape from the same
set as the wordmark, so a reload deals new tapes, as it will on the live
page. The lettering is the wordmark word's (_sass/shared/_layout.scss), at
door size. The page's words are untouched.
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mock_bundle
from reference_candidates import BAR_CSS, bar_html, switcher, document

GROUPS = [("door", "Doors", [("today", "today"), ("tape", "tape"),
                             ("icon", "tape + icon"), ("row", "tape row")])]
DEFAULTS = {"door": "tape"}

ARROW = ('<svg viewBox="0 0 20 12" class="tape-door-arrow" aria-hidden="true" focusable="false">'
         '<path d="M1 6h18M14 2l5 4-5 4" fill="none" stroke="currentColor" stroke-width="2" '
         'stroke-linecap="round" stroke-linejoin="round" /></svg>')


def icon(name):
    with open(os.path.join(ROOT, "_includes", "icons", name + ".svg"), encoding="utf-8") as fh:
        return fh.read()


def door(word, svg, n):
    return (f'<li><a href="#" onclick="return false" class="tape-door">'
            f'<span class="tape-door-icon" aria-hidden="true">{svg}</span>'
            f'<span class="tape-door-tape"><span class="tape-door-bg" data-card-tape="{n}"></span>'
            f'<span class="tape-door-word"><span class="tape-door-br">[ </span>{word}'
            f'<span class="tape-door-br"> ]</span></span></span>{ARROW}</a></li>')


TAPE_DOORS = ('<ul class="tape-doors">' + door("FOOD", icon("food-cloche-heart"), 1)
              + door("COCKTAILS", icon("glass-martini"), 2) + "</ul>")

CSS = """
/* today's list shows only on `today`; the tape list on everything else */
html:not([data-door="today"]) .not-found-ways { display: none; }
html[data-door="today"] .tape-doors { display: none; }

.tape-doors { list-style: none; padding: 0; margin: 2rem 0 3rem; display: flex; flex-direction: column; align-items: flex-start; gap: 1.1rem; }
/* the recipe body's list dash is not a door's */
.tape-doors > li { padding-left: 0 !important; }
.tape-doors > li::before { content: none !important; display: none !important; }
.tape-door { display: inline-flex; align-items: center; gap: 0.6rem; text-decoration: none !important; color: #211f20 !important; font-weight: 400 !important; }
.tape-door-tape { position: relative; display: inline-flex; align-items: center; padding: 0.55em 1.2em; font-size: 1.15rem; }
.tape-door-bg { position: absolute; left: 0; top: -1.765%; width: 100%; height: 100%; z-index: 0; pointer-events: none; }
.tape-door-bg svg { width: 100%; height: 100%; display: block; }
.tape-door-word {
  position: relative; z-index: 1; font-family: "Courier Prime", "Courier New", Courier, monospace;
  font-weight: 700; letter-spacing: 0.18em; text-transform: uppercase; line-height: 1; white-space: nowrap;
  color: #ECE9EA;
  text-shadow: -1.0px -1.0px 0 #fdfbfe, -1.8px -1.8px 0 rgba(253,251,254,0.75), 1.0px 1.0px 0 rgba(5,5,5,0.90), 1.8px 1.8px 0 rgba(5,5,5,0.45);
}
.tape-door-br { letter-spacing: 0; }
.tape-door-arrow { width: 1.3rem; height: auto; flex: none; transition: transform 0.12s ease; }
.tape-door-icon { display: none; line-height: 0; }
.tape-door-icon svg { height: 1.9rem; width: auto; }
.tape-door:hover .tape-door-arrow, .tape-door:focus-visible .tape-door-arrow { transform: translateX(4px); }
.tape-door:hover .tape-door-word, .tape-door:focus-visible .tape-door-word { color: #fff; }
.tape-door:focus-visible { outline: 2px solid #ff00c8; outline-offset: 4px; }

/* TAPE + ICON: the site's own icon outside the tape, the bare word on it */
html[data-door="icon"] .tape-door-icon { display: inline-block; }
html[data-door="icon"] .tape-door-br { display: none; }

/* TAPE ROW: both doors on one line, bigger, no arrows; they stack on a phone */
html[data-door="row"] .tape-doors { flex-direction: row; flex-wrap: wrap; gap: 1.2rem 1.6rem; }
html[data-door="row"] .tape-door-tape { font-size: 1.35rem; }
html[data-door="row"] .tape-door-arrow { display: none; }
"""


def page(links):
    def transform(body):
        body = re.sub(r'(</ul>\s*</div>\s*</article>)', r'</ul>' + TAPE_DOORS + r'</div></article>', body, count=1)
        return bar_html(GROUPS, links) + body
    return mock_bundle.bundle(
        "404.html", "food.css", "Tape Doors",
        extra_style=BAR_CSS + CSS, body_transform=transform,
        extra_scripts="<script>" + switcher(DEFAULTS, "notfoundcand-1382") + "</script>",
    )


def phone():
    figs = "\n".join(
        f'<figure><figcaption>{label}</figcaption><iframe src="notfound.html?door={v}" title="{label}"></iframe></figure>'
        for v, label in GROUPS[0][2])
    return """<title>Tape Doors at 390px</title>
<style>
  body { margin: 0; padding: 12px 16px; background: #faf7f8; color: #211f20; font: 14px/1.4 system-ui, sans-serif; }
  h1 { font-size: 15px; margin: 8px 0; }
  .row { display: flex; gap: 14px; overflow-x: auto; padding-bottom: 12px; }
  figure { margin: 0; flex: 0 0 auto; }
  figcaption { font-size: 12px; color: #4f4e4a; margin: 0 0 6px 0; }
  iframe { width: 390px; height: 760px; border: 1px solid #c9c4c7; border-radius: 10px; background: #fff; }
  a { color: #c4009a; }
</style>
<p><a href="index.html">the 404 page, full size, with the switch</a></p>
<h1>Every treatment at 390px</h1>
<div class="row">
""" + figs + "\n</div>\n"


if __name__ == "__main__":
    out = os.path.join(ROOT, "tmp", "notfoundcand")
    os.makedirs(out, exist_ok=True)
    p = page([("phone.html", "all of them at phone width")])
    if "tape-doors" not in p:
        sys.exit("the 404's door list was not found in tmp/site-mock/404.html; nothing written")
    mock_bundle.write(os.path.join(out, "index.html"), p)
    mock_bundle.write(os.path.join(out, "notfound.html"), document(p))
    mock_bundle.write(os.path.join(out, "phone.html"), document(phone()))
