#!/usr/bin/env python3
"""Render the wordmark images: link previews and home-screen icons.

    sh scripts/browser/build.sh
    python3 scripts/render_social_images.py --site tmp/site --chrome \\
        /opt/playwright/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell

Writes, per site, assets/img/social/<site>.png (the og:image, 1200x630 CSS
pixels at scale 2) and assets/img/favicon/<site>-180.png (the home-screen
icon). `--profile DIR` also writes an 800px wordmark profile picture, which
the site does not use. _layouts/default.html links the first two (#1086).

The image is the real wordmark: the built site's compiled stylesheet, the
`site-title-link` block lifted verbatim from its index, and one fixed tape
(`DEFAULT_TAPE`) so two runs agree. Re-run it when the wordmark changes. The
PNGs are committed and CI never runs this. Use the headless shell: the full
Chrome build does not exit in the devcontainer.
"""
from __future__ import annotations

import argparse
import base64
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_pdfs import ROOT, SCRATCH, _chrome, _serve  # noqa: E402

WIDTH, HEIGHT, SCALE = 1200, 630, 2
DEFAULT_TAPE = 7
SOCIAL_DIR = ROOT / "assets" / "img" / "social"
FAVICON_DIR = ROOT / "assets" / "img" / "favicon"

# name -> the built page whose header is lifted.
CARDS = {
    "food": "food/index.html",
    "cocktails": "cocktails/index.html",
}

# shape -> (width, height, scale, fit). An app cuts its square thumbnail
# from the middle of the wide card, so the lockup fills that middle square
# and leaves the sides empty. A home-screen icon or profile picture is cut to
# a rounded square or a circle, so the lockup's diagonal fills the circle.
# Every page is at least 900 CSS pixels wide: narrower, and the header's
# phone rules wrap HELEN TRIAGES and cap it at 92vw. The headless shell will
# not scale below 0.5, so a smaller image is shot at 900 and resized in the
# browser (RESIZE).
SHAPES = {
    "card": (WIDTH, HEIGHT, SCALE, "square"),
    "home": (900, 900, 1, "circle"),
    "profile": (900, 900, 800 / 900, "circle"),
}
RESIZE = {"home": 180}

RESIZE_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"></head><body><pre id="out"></pre>
<script>
  var img = new Image();
  img.onload = function () {{
    var c = document.createElement('canvas');
    c.width = c.height = {size};
    var ctx = c.getContext('2d');
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(img, 0, 0, {size}, {size});
    document.getElementById('out').textContent = c.toDataURL('image/png');
  }};
  img.src = '{src}';
</script></body></html>
"""

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
  // The tape overhangs the lockup's box, so fit and centre the union of the
  // two. The union's box is a little larger than what it holds (the tape is
  // tilted), which is why the fit can run to the edge.
  function fit() {{
    var card = document.querySelector('.social-card');
    var r = document.querySelector('.site-logo').getBoundingClientRect();
    var t = document.querySelector('.tape-bg').getBoundingClientRect();
    var c = card.getBoundingClientRect();
    var L = Math.min(r.left, t.left), R = Math.max(r.right, t.right);
    var T = Math.min(r.top, t.top), B = Math.max(r.bottom, t.bottom);
    var side = Math.min({w}, {h});
    var s = '{fit}' === 'circle'
      ? side / Math.hypot(R - L, B - T)
      : Math.min(side * 0.99 / (R - L), side * 0.99 / (B - T));
    var dx = ((L + R) / 2 - (c.left + c.right) / 2) * s;
    var dy = ((T + B) / 2 - (c.top + c.bottom) / 2) * s;
    card.style.transform = 'translate(' + -dx + 'px,' + -dy + 'px) scale(' + s + ')';
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


def _card(site: Path, page: str, tape: int, shape: str) -> str:
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
    w, h, _scale, fit = SHAPES[shape]
    return CARD_HTML.format(css=css, header=header, w=w, h=h, fit=fit)


def _shoot(chrome: str, url: str, out: Path, shape: str) -> None:
    w, h, scale, _fit = SHAPES[shape]
    with tempfile.TemporaryDirectory(prefix="htf-social-", dir=SCRATCH) as profile:
        result = subprocess.run(
            [
                chrome, "--headless", "--disable-gpu", "--no-sandbox",
                "--disable-dev-shm-usage", f"--user-data-dir={profile}",
                "--hide-scrollbars", f"--window-size={w},{h}",
                f"--force-device-scale-factor={scale}",
                "--run-all-compositor-stages-before-draw",
                "--virtual-time-budget=8000",
                f"--screenshot={out}", url,
            ],
            capture_output=True, text=True, timeout=120,
        )
    if result.returncode != 0 or not out.exists() or out.stat().st_size == 0:
        sys.exit(f"chrome failed on {url}: {result.stderr.strip()[:300]}")


def _resize(chrome: str, stage: Path, port: int, shot: Path, out: Path, size: int) -> None:
    page = stage / "cards" / f"resize-{shot.stem}.html"
    page.write_text(RESIZE_HTML.format(size=size, src=shot.name), encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="htf-social-", dir=SCRATCH) as profile:
        result = subprocess.run(
            [
                chrome, "--headless", "--disable-gpu", "--no-sandbox",
                "--disable-dev-shm-usage", f"--user-data-dir={profile}",
                "--virtual-time-budget=8000", "--dump-dom",
                f"http://127.0.0.1:{port}/cards/{page.name}",
            ],
            capture_output=True, text=True, timeout=120,
        )
    found = re.search(r'<pre id="out">data:image/png;base64,([^<]+)</pre>', result.stdout)
    if not found:
        sys.exit(f"chrome did not resize {shot.name}: {result.stderr.strip()[:300]}")
    out.write_bytes(base64.b64decode(found.group(1)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", default="tmp/site", help="built site directory")
    parser.add_argument("--chrome", help="browser binary, if not on PATH as google-chrome/chromium")
    parser.add_argument("--tape", type=int, default=DEFAULT_TAPE, help="which tape file the cards wear")
    parser.add_argument("--profile", help="also write wordmark profile pictures here")
    args = parser.parse_args()

    site = (ROOT / args.site).resolve()
    if not site.is_dir():
        sys.exit(f"{site} does not exist -- run `sh scripts/browser/build.sh` first.")
    SCRATCH.mkdir(exist_ok=True)
    chrome = _chrome(args.chrome)

    outputs = {
        "card": lambda name: SOCIAL_DIR / f"{name}.png",
        "home": lambda name: FAVICON_DIR / f"{name}-180.png",
    }
    if args.profile:
        outputs["profile"] = lambda name: Path(args.profile) / f"{name}-profile-wordmark.png"

    baseurl = re.search(r'<meta name="base-url" content="([^"]*)"',
                        (site / "food/index.html").read_text(encoding="utf-8")).group(1).strip("/")

    # Serve the build under its baseurl, with the card pages beside it, so the
    # stylesheet's absolute URLs and the fonts it pulls resolve.
    stage = Path(tempfile.mkdtemp(prefix="htf-social-root-", dir=SCRATCH))
    (stage / baseurl).symlink_to(site)
    cards = stage / "cards"
    cards.mkdir()
    for shape in outputs:
        for name, page in CARDS.items():
            (cards / f"{name}-{shape}.html").write_text(_card(site, page, args.tape, shape), encoding="utf-8")

    httpd, port = _serve(stage)
    try:
        for shape, where in outputs.items():
            for name in CARDS:
                out = where(name)
                out.parent.mkdir(parents=True, exist_ok=True)
                url = f"http://127.0.0.1:{port}/cards/{name}-{shape}.html"
                if shape in RESIZE:
                    shot = cards / f"{name}-{shape}.png"
                    _shoot(chrome, url, shot, shape)
                    _resize(chrome, stage, port, shot, out, RESIZE[shape])
                else:
                    _shoot(chrome, url, out, shape)
                print(f"wrote {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    finally:
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
