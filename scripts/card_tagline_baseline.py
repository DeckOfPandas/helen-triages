"""Where does a card's tagline start, so its first baseline is the ingredients'?

    python3 scripts/card_tagline_baseline.py

Derives `$card-tagline-top` in `_sass/cocktails/_cards.scss` (#1292): on the
cocktail index a pointed-at card swaps its ingredient line for its tagline,
and the tagline's first baseline lands where the ingredients' was.

The two lines are in different faces, sizes and line heights, and where a
baseline sits in its line box depends on each face's ascent and descent, so
this asks a browser. It lays out one line of each as the stylesheet declares
them, drops a zero-size inline-block at the start of each (its bottom edge is
the baseline) and reads how far below the top of its box each falls. The
tagline's top margin is the ingredients' top margin plus the difference.

Needs Playwright's Chromium, found the way tests/test_browser_smoke.py finds
it. Reads the two font files from assets/fonts, so it needs no build, and
writes tmp/card_tagline_baseline.html. Re-run it if either rule's size, line
height or face changes; the constants below are copies of the stylesheet's.
"""
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = ROOT / "assets" / "fonts"

ROOT_PX = 16

# Laid out a hundred times too big, then divided: Chromium snaps a line's
# baseline to a whole pixel, so at the real 16px root both baselines come
# back as integers and the answer never moves.
SCALE = 100

# `.drink-card-ingredients` in _sass/cocktails/_cards.scss
ING = dict(family="Selawik", file="selawik-400.woff2", size_rem=0.82, line_height=1.5)
ING_MARGIN_TOP_REM = 0.5

# `.drink-card-tagline` in the same file
TAG = dict(family="Courier Prime", file="courier-prime-400.woff2", size_rem=0.9, line_height=1.45)

BROWSER_DIRS = (
    ROOT / "tmp" / "browser" / "ms-playwright",
    pathlib.Path("/opt/playwright/ms-playwright"),
)

PAGE = """<!doctype html><meta charset="utf-8"><style>
@font-face {{ font-family: "{ing[family]}"; src: url("{ing_url}") format("woff2"); }}
@font-face {{ font-family: "{tag[family]}"; src: url("{tag_url}") format("woff2"); }}
html {{ font-size: {root}px; }}
p {{ margin: 0; }}
i {{ display: inline-block; width: 0; height: 0; }}
#ing {{ font: {ing[size_rem]}rem/{ing[line_height]} "{ing[family]}"; }}
#tag {{ font: {tag[size_rem]}rem/{tag[line_height]} "{tag[family]}"; }}
</style>
<p id="ing"><i></i>rhum agricole vieux</p>
<p id="tag"><i></i>Also causes fog.</p>
"""

MEASURE = """
(id) => {
  const p = document.getElementById(id);
  const probe = p.querySelector('i');
  return probe.getBoundingClientRect().bottom - p.getBoundingClientRect().top;
}
"""


def main():
    from playwright.sync_api import sync_playwright

    for candidate in BROWSER_DIRS:
        if candidate.is_dir():
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(candidate)
            break

    html = PAGE.format(
        ing=ING, tag=TAG, root=ROOT_PX * SCALE,
        ing_url=(FONTS / ING["file"]).as_uri(),
        tag_url=(FONTS / TAG["file"]).as_uri(),
    )
    scratch = ROOT / "tmp" / "card_tagline_baseline.html"
    scratch.parent.mkdir(exist_ok=True)
    scratch.write_text(html, encoding="utf-8")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto(scratch.as_uri())
        page.evaluate("document.fonts.ready")
        loaded = page.evaluate("Array.from(document.fonts).filter(f => f.status === 'loaded').length")
        ing = page.evaluate(MEASURE, "ing") / SCALE
        tag = page.evaluate(MEASURE, "tag") / SCALE
        browser.close()

    if loaded != 2:
        raise SystemExit(f"only {loaded} of 2 faces loaded; the numbers would be a fallback font's")

    top_px = ING_MARGIN_TOP_REM * ROOT_PX + ing - tag
    print(f"ingredients: baseline {ing:.2f}px below the top of its line box")
    print(f"tagline:     baseline {tag:.2f}px below the top of its line box")
    print(f"ingredients' top margin: {ING_MARGIN_TOP_REM}rem = {ING_MARGIN_TOP_REM * ROOT_PX:.2f}px")
    print(f"$card-tagline-top: {top_px:.2f}px = {top_px / ROOT_PX:.3f}rem")


if __name__ == "__main__":
    main()
