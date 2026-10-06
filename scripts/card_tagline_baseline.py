"""Where does a card's tagline start, so its first baseline is the ingredients'?

REPRODUCES `$card-tagline-top` in `_sass/cocktails/_cards.scss`.

WHAT IT IS FOR. On the cocktail index a card's tagline takes the card when it
is pointed at (#1292): the ingredient line steps out and the tagline is drawn
where it was. Helen, 2026-10-06, of the candidates page: "I'd like the top line
of the tagline to align in some more convincing way with where the top line of
the ingredients list was", and, shown both ways, "Baselines match."

WHY IT IS NOT ARITHMETIC ON THE TWO FONT SIZES. The two lines are in different
faces (Selawik, Courier Prime) at different sizes and line heights, and where a
baseline sits inside its line box depends on each face's own ascent and
descent. So this asks a browser: it lays out one line of each, exactly as the
stylesheet declares them, drops a zero-size inline-block at the start of each
(whose bottom edge IS the baseline) and reads how far below the top of its box
each baseline falls. The tagline's top margin is then the ingredients' top
margin plus the difference.

    python3 scripts/card_tagline_baseline.py

Needs Playwright's Chromium, found the way tests/test_browser_smoke.py finds
it. It reads the two font files straight from assets/fonts, so it needs no
`jekyll build`. RE-RUN IT if either rule's size, line height or face changes;
the four constants below are copies of the stylesheet's and are the only thing
to keep in step.
"""
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = ROOT / "assets" / "fonts"

ROOT_PX = 16

# LAID OUT A HUNDRED TIMES TOO BIG, THEN DIVIDED. Chromium snaps a line's
# baseline to a whole pixel, so at the real 16px root both baselines come back
# as integers (14 and 13) and the answer is 9px on every run whatever the faces
# are doing underneath. At 1600px the snap is a hundredth of a real pixel.
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
