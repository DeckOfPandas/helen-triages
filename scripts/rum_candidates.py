"""The rum page's candidates page: MANUAL 13.11, #1379. Ships nothing.

Build first:
  bundle exec jekyll build --config _config.yml,_config_local.yml -d tmp/site-mock
Then:
  python3 scripts/rum_candidates.py

Writes tmp/rumcand/index.html (the Artifact's body) and tmp/rumcand/switcher.js
(parse it before publishing). The switches on the bar:

  paras   today | split (paragraph one a sentence each; paragraph two split
                  where it turns from where rum comes from to how it tastes)
                | every (every sentence of both its own paragraph)
  guyana  inline (in the heading) | beside (a country label after it)
                | under (a country label on its own line under it)

The sentences are cut out of the built page, so no word of Helen's is retyped.
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mock_bundle
from reference_candidates import BAR_CSS, bar_html, switcher

GROUPS = [
    ("paras", "Paragraphs", [("today", "today"), ("split", "split (my pick)"), ("every", "a sentence each")]),
    ("guyana", "Guyana", [("inline", "in the heading"), ("beside", "label beside"), ("under", "label under")]),
]
DEFAULTS = {"paras": "split", "guyana": "beside"}

CSS = """
html:not([data-paras="today"]) .rc-p-today,
html:not([data-paras="split"]) .rc-p-split,
html:not([data-paras="every"]) .rc-p-every { display: none; }
html:not([data-guyana="inline"]) .rc-g-inline,
html:not([data-guyana="beside"]) .rc-g-beside,
html:not([data-guyana="under"]) .rc-g-under { display: none; }
.rc-g-beside { display: inline; margin-left: 0.9rem; vertical-align: 0.15em; }
.rc-g-under { margin: -0.5rem 0 1rem; }
"""

# A sentence ends at ". " or "? " before a capital or a quote; "e.g." does not
# occur in these two paragraphs.
SENTENCE = re.compile(r"(?<=[.?])\s+(?=[A-Z\"])")


def paras(body):
    ps = re.findall(r'<p class="ref-prose">((?:What colour|Rum tastes like).*?)</p>', body, re.S)
    assert len(ps) == 2, ps
    one, two = (SENTENCE.split(p.strip()) for p in ps)
    wrap = lambda ss: "".join(f'<p class="ref-prose">{s}</p>' for s in ss)
    turn = next(i for i, s in enumerate(two) if s.startswith("The result"))
    today = wrap([ps[0]]) + wrap([ps[1]])
    split = wrap(one) + wrap([" ".join(two[:turn]), " ".join(two[turn:])])
    every = wrap(one) + wrap(two)
    blocks = (f'<div class="rc-p-today">{today}</div><div class="rc-p-split">{split}</div>'
              f'<div class="rc-p-every">{every}</div>')
    start = body.index(f'<p class="ref-prose">{ps[0]}')
    end = body.index("</p>", body.index(ps[1])) + len("</p>")
    # Helen's own comment between the two is a Liquid comment and is not in
    # the build, so nothing between them is lost.
    return body[:start] + blocks + body[end:]


def guyana(body):
    head = re.search(r'<h3 class="ref-section-heading" id="group-demerara-rum"><span>Demerara rum</span></h3>', body)
    assert head, "no Demerara heading"
    new = ('<h3 class="ref-section-heading rc-g-inline" id="group-demerara-rum"><span>Demerara rum (Guyana)</span></h3>'
           '<h3 class="ref-section-heading rc-g-beside-h"><span>Demerara rum</span>'
           '<small class="rum-origin-head rc-g-beside">Guyana</small></h3>'
           '<p class="rum-origin-head rc-g-under">Guyana</p>')
    return body[:head.start()] + new + body[head.end():]


EXTRA = """
html[data-guyana="inline"] .rc-g-beside-h { display: none; }
html[data-guyana="under"] .rc-g-beside-h .rc-g-beside { display: none; }
html[data-guyana="inline"] .rc-g-under, html[data-guyana="beside"] .rc-g-under { display: none; }
"""


def page():
    return mock_bundle.bundle(
        "cocktails/reference/rum-categories/index.html", "cocktails.css", "Rum Page Candidates",
        extra_style=BAR_CSS + CSS + EXTRA,
        body_transform=lambda body: bar_html(GROUPS, []) + guyana(paras(body)),
        extra_scripts="<script>" + switcher(DEFAULTS, "rumcand-1379-1") + "</script>",
    )


if __name__ == "__main__":
    out = os.path.join(ROOT, "tmp", "rumcand")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "switcher.js"), "w", encoding="utf-8") as fh:
        fh.write(switcher(DEFAULTS, "x"))
    mock_bundle.write(os.path.join(out, "index.html"), page())
