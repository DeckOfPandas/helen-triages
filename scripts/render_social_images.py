#!/usr/bin/env python3
"""Render the link-preview images (og:image) from the site's own wordmark.

Design review 2026-09-15, #1086; Helen: "The wordmark is fine for a start --
I don't think we have anything else that feels like branding anyway."

    sh scripts/browser/build.sh
    python3 scripts/render_social_images.py --site tmp/site \\
        --chrome tmp/browser/ms-playwright/chromium-1134/chrome-linux/chrome

Writes assets/img/social/food.png, cocktails.png and neutral.png -- one per
site plus one for the pages that belong to neither (/about/, /404.html) --
each 1200x630 CSS pixels at a device scale of 2, which is the shape every
preview renderer (WhatsApp, Slack, Signal, iMessage, Facebook) asks for.
_layouts/default.html points at them through `social_image` in
_data/sites.yml and _config.yml.

THE IMAGE IS THE REAL WORDMARK, NOT A REDRAWING. Each card is a page made
from the BUILT site: the site's own compiled stylesheet, the `<a
class="site-title-link">` block lifted verbatim from that site's built index
(so HELEN TRIAGES, the tape, the bracketed word and the `--wordmark-chars`
custom property are exactly what the header renders), and one tape SVG
inlined with the two attributes decorations.js injects at runtime. The card
scales the lockup up to fill the frame and screenshots it. If the wordmark's
lettering, tape or palette ever change, re-run this and the previews follow;
nothing here restates a colour or a size.

ONE TAPE, FIXED, ON PURPOSE. The header rolls a random tape per load (#779,
"random each page load please"), which is a decision about a live page. A
preview image is a file, so it wears one tape and the same one every run --
`--tape` picks it and the default is written here so two runs agree.

The PNGs are committed, so CI never runs this: a preview renderer fetches the
image from the live site, and a deploy that failed to produce it would be a
link with no picture, which is what the site had before.

Headless Chrome, like scripts/generate_pdfs.py and for the same reasons; its
_chrome() and _serve() are imported rather than copied.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_pdfs import ROOT, SCRATCH, _chrome, _serve  # noqa: E402

WIDTH, HEIGHT, SCALE = 1200, 630, 2
DEFAULT_TAPE = 7
OUT_DIR = ROOT / "assets" / "img" / "social"

# name -> the built page whose header is lifted. /about/ carries the [ ?? ]
# tape (its own wordmark_word) and food's stylesheet, which is what a page
# belonging to neither site looks like.
CARDS = {
    "food": "food/index.html",
    "cocktails": "cocktails/index.html",
    "neutral": "about/index.html",
}

# decorations.js's TAPE_ATTRS and TAPE_OPEN, kept in step by hand: the tape
# files carry width="100%" and no height, and without height="100%" the SVG
# letterboxes inside its box instead of filling it.
TAPE_OPEN = re.compile(r"<svg(?=[\s>])")
TAPE_ATTRS = '<svg preserveAspectRatio="none" height="100%"'

CARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<link rel="stylesheet" href="{css}">
<style>
  html, body {{ margin: 0; width: {w}px; height: {h}px; overflow: hidden; }}
  body {{ display: grid; place-items: center; }}
  /* The header's own chrome (border, padding, grid) is not the wordmark. */
  .social-card .site-header {{ border: 0; padding: 0; margin: 0; background: transparent; }}
  .social-card .site-header-inner {{ display: block; }}
  .social-card {{ display: inline-block; transform-origin: center center; }}
  .social-card .site-title-link {{ display: inline-block; text-decoration: none; }}
</style>
</head>
<body>
<div class="social-card"><header class="site-header"><div class="site-header-inner">
{header}
</div></header></div>
<script>
  // Fill the frame: scale the lockup so the wider of its two rows spans about
  // four fifths of the width, capped so a short word does not become a poster.
  function fit() {{
    var card = document.querySelector('.social-card');
    var logo = document.querySelector('.site-logo');
    var r = logo.getBoundingClientRect();
    var s = Math.min(2.8, ({w} * 0.8) / r.width);
    card.style.transform = 'scale(' + s + ')';
  }}
  document.fonts.ready.then(fit);
</script>
</body>
</html>
"""


def _lift(page_html: str, what: str, pattern: str) -> str:
    match = re.search(pattern, page_html, re.S)
    if not match:
        sys.exit(f"could not find {what} in the built page -- _layouts/default.html "
                 f"has changed shape and this script needs to follow.")
    return match.group(1)


def _card(site: Path, page: str, tape: int) -> str:
    html = (site / page).read_text(encoding="utf-8")
    css = _lift(html, "the stylesheet link", r'<link rel="stylesheet" href="([^"]+)">')
    header = _lift(html, "the wordmark link", r'(<a href="[^"]*" class="site-title-link">.*?</a>)')
    tape_svg = (site / "assets" / "img" / "chrome" / "tape" / f"tape-{tape}.svg").read_text(encoding="utf-8")
    tape_svg = TAPE_OPEN.sub(TAPE_ATTRS, tape_svg, count=1)
    header, n = re.subn(
        r'<span class="tape-bg" aria-hidden="true"\s+data-tape-count="\d+"></span>',
        lambda _m: f'<span class="tape-bg" aria-hidden="true">{tape_svg}</span>',
        header,
    )
    if n != 1:
        sys.exit("the tape slot in the lifted header did not match -- see decorations.js's tape().")
    return CARD_HTML.format(css=css, header=header, w=WIDTH, h=HEIGHT)


def _shoot(chrome: str, url: str, out: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="htf-social-", dir=SCRATCH) as profile:
        result = subprocess.run(
            [
                chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
                "--disable-dev-shm-usage", f"--user-data-dir={profile}",
                "--hide-scrollbars", f"--window-size={WIDTH},{HEIGHT}",
                f"--force-device-scale-factor={SCALE}",
                "--run-all-compositor-stages-before-draw",
                "--virtual-time-budget=8000",
                f"--screenshot={out}", url,
            ],
            capture_output=True, text=True, timeout=120,
        )
    if result.returncode != 0 or not out.exists() or out.stat().st_size == 0:
        sys.exit(f"chrome failed on {url}: {result.stderr.strip()[:300]}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", default="tmp/site", help="built site directory")
    parser.add_argument("--chrome", help="browser binary, if not on PATH as google-chrome/chromium")
    parser.add_argument("--tape", type=int, default=DEFAULT_TAPE, help="which tape file the cards wear")
    parser.add_argument("--out", default=str(OUT_DIR), help="where the PNGs go")
    args = parser.parse_args()

    site = (ROOT / args.site).resolve()
    if not site.is_dir():
        sys.exit(f"{site} does not exist -- run `sh scripts/browser/build.sh` first.")
    SCRATCH.mkdir(exist_ok=True)
    chrome = _chrome(args.chrome)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    baseurl = re.search(r'<meta name="base-url" content="([^"]*)"',
                        (site / "food/index.html").read_text(encoding="utf-8")).group(1).strip("/")

    # Serve the build under its baseurl, with the card pages beside it, so the
    # stylesheet's absolute URLs and the fonts it pulls resolve.
    stage = Path(tempfile.mkdtemp(prefix="htf-social-root-", dir=SCRATCH))
    (stage / baseurl).symlink_to(site)
    cards = stage / "cards"
    cards.mkdir()
    for name, page in CARDS.items():
        (cards / f"{name}.html").write_text(_card(site, page, args.tape), encoding="utf-8")

    httpd, port = _serve(stage)
    try:
        for name in CARDS:
            out = out_dir / f"{name}.png"
            _shoot(chrome, f"http://127.0.0.1:{port}/cards/{name}.html", out)
            print(f"wrote {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    finally:
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
