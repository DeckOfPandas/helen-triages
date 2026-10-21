#!/usr/bin/env python3
"""Render each site's tab icons from Courier Prime Bold, the wordmark's face.

    python3 scripts/render_favicons.py --chrome \\
        /opt/playwright/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell

Writes assets/img/favicon/<site_key>-<size>.png for every site in SITES and
every size in SIZES; _layouts/default.html links them by `page.site_key`.
The 180px home-screen icon is the wordmark itself, so
scripts/render_social_images.py writes that one. `--profile DIR` also writes
an HT-over-brackets profile picture per site, which the site does not use.

A favicon cannot load a web font, so the lettering is drawn here, in a
browser that has the font, and the PNGs are committed; CI never runs this.
Use the headless shell: the full Chrome build does not exit in the
devcontainer. `_chrome()` and `_serve()` come from scripts/generate_pdfs.py.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_pdfs import ROOT, SCRATCH, _chrome, _serve  # noqa: E402

OUT_DIR = ROOT / "assets" / "img" / "favicon"
FONT = ROOT / "assets" / "fonts" / "courier-prime-700.woff2"

BLACK_ON_WHITE = {"fg": "#000000", "bg": "#FFFFFF"}
WHITE_ON_BLACK = {"fg": "#FFFFFF", "bg": "#000000"}

# site_key -> the colours of each line of HT over brackets, top first. The
# two sites differ by colour alone, which is what survives at 16px. Food's
# tile splits; its brackets alone stay black on white, or at 16px food and
# cocktails would be the same icon.
SITES = {
    "food": {"split": [BLACK_ON_WHITE, WHITE_ON_BLACK], "alone": BLACK_ON_WHITE},
    "cocktails": {"split": [WHITE_ON_BLACK, WHITE_ON_BLACK], "alone": WHITE_ON_BLACK},
}

# size -> the lines drawn. Below 32px only the brackets fit.
SIZES = {
    16: ["[]"],
    32: ["HT", "[]"],
    48: ["HT", "[]"],
}
PROFILE_SIZE = 800

PAGE = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>@font-face {{ font-family: "Courier Prime"; font-weight: 700; src: url(font.woff2) format("woff2"); }}</style>
</head><body><pre id="out"></pre>
<script>
const JOBS = {jobs};
function roundRect(ctx, x, y, w, h, r) {{
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}}
// A "tab" tile is rounded with a hairline edge, so a white half holds its
// shape on a light tab strip and a black half on a dark one. A "circle" tile
// is square and full-bleed, with the lettering fitted to the inscribed circle.
function paint(job) {{
  const px = job.size, c = document.createElement("canvas");
  c.width = c.height = px;
  const ctx = c.getContext("2d");
  const tab = job.tile === "tab";
  const r = tab ? px * 10 / 64 : 0;

  // Measure at 100px, then scale the block to `share` of the tile.
  ctx.font = '700 100px "Courier Prime"';
  const adv = ctx.measureText("H").width;
  const cap = ctx.measureText("H").actualBoundingBoxAscent;
  const br = ctx.measureText("[");
  const brUp = br.actualBoundingBoxAscent, brDown = br.actualBoundingBoxDescent;
  const gap = 18;
  const lines = job.lines;
  const heights = lines.map(l => l.includes("[") ? brUp + brDown : cap);
  const blockH = heights.reduce((a, b) => a + b, 0) + gap * (lines.length - 1);
  const blockW = Math.max(...lines.map(l => l.length)) * adv;
  const k = tab
    ? Math.min(px * job.share / blockW, px * job.share / blockH)
    : px * job.share / Math.hypot(blockW, blockH);
  const top0 = (px - blockH * k) / 2;

  // Two lines change colour halfway through the gap between them, so each
  // line sits wholly inside its own half.
  const cut = lines.length > 1 ? top0 + (heights[0] + gap / 2) * k : px;
  const zones = lines.length > 1
    ? [{{ y0: 0, y1: cut, ...job.colours[0] }}, {{ y0: cut, y1: px, ...job.colours[1] }}]
    : [{{ y0: 0, y1: px, ...job.colours[0] }}];
  for (const z of zones) {{
    ctx.save();
    ctx.beginPath();
    ctx.rect(0, z.y0, px, z.y1 - z.y0);
    ctx.clip();
    ctx.fillStyle = z.bg;
    roundRect(ctx, 0, 0, px, px, r);
    ctx.fill();
    if (tab) {{
      const w = Math.max(1, px / 32);
      ctx.strokeStyle = z.bg === "#000000" ? "rgba(255,255,255,0.45)" : "rgba(0,0,0,0.35)";
      ctx.lineWidth = w;
      roundRect(ctx, w / 2, w / 2, px - w, px - w, Math.max(0, r - w / 2));
      ctx.stroke();
    }}
    ctx.restore();
  }}

  ctx.font = "700 " + (100 * k) + 'px "Courier Prime"';
  let top = top0;
  lines.forEach((l, i) => {{
    ctx.fillStyle = zones[i].fg;
    const up = (l.includes("[") ? brUp : cap) * k;
    const x0 = (px - l.length * adv * k) / 2;
    for (let j = 0; j < l.length; j++) ctx.fillText(l[j], x0 + j * adv * k, top + up);
    top += heights[i] * k + gap * k;
  }});
  return c.toDataURL("image/png");
}}
document.fonts.load('700 20px "Courier Prime"').then(() => {{
  const out = {{ font: document.fonts.check('700 20px "Courier Prime"'), icons: {{}} }};
  for (const job of JOBS) out.icons[job.name] = paint(job);
  document.getElementById("out").textContent = JSON.stringify(out);
}});
</script></body></html>
"""


def _jobs(profile: bool) -> list[dict]:
    jobs = []
    for site, colours in SITES.items():
        for size, lines in SIZES.items():
            jobs.append({
                "name": f"{site}-{size}", "size": size, "lines": lines, "tile": "tab",
                "share": 0.78 if len(lines) > 1 else 0.8,
                "colours": colours["split"] if len(lines) > 1 else [colours["alone"]],
            })
        if profile:
            jobs.append({
                "name": f"{site}-profile-ht", "size": PROFILE_SIZE, "lines": ["HT", "[]"],
                "tile": "circle", "share": 0.94, "colours": colours["split"],
            })
    return jobs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chrome", help="browser binary, if not on PATH as google-chrome/chromium")
    parser.add_argument("--out", default=str(OUT_DIR), help="where the favicons go")
    parser.add_argument("--profile", help="also write HT-over-brackets profile pictures here")
    args = parser.parse_args()

    SCRATCH.mkdir(exist_ok=True)
    chrome = _chrome(args.chrome)
    jobs = _jobs(bool(args.profile))
    stage = Path(tempfile.mkdtemp(prefix="htf-favicon-", dir=SCRATCH))
    (stage / "font.woff2").symlink_to(FONT)
    (stage / "index.html").write_text(PAGE.format(jobs=json.dumps(jobs)), encoding="utf-8")

    httpd, port = _serve(stage)
    try:
        with tempfile.TemporaryDirectory(prefix="htf-favicon-profile-", dir=SCRATCH) as profile:
            result = subprocess.run(
                [
                    chrome, "--headless", "--disable-gpu", "--no-sandbox",
                    "--disable-dev-shm-usage", f"--user-data-dir={profile}",
                    "--virtual-time-budget=8000", "--dump-dom",
                    f"http://127.0.0.1:{port}/index.html",
                ],
                capture_output=True, text=True, timeout=120,
            )
    finally:
        httpd.shutdown()

    found = re.search(r'<pre id="out">(.*?)</pre>', result.stdout, re.S)
    if result.returncode != 0 or not found or not found.group(1):
        sys.exit(f"chrome drew nothing: {result.stderr.strip()[:300]}")
    drawn = json.loads(html.unescape(found.group(1)))
    if not drawn["font"]:
        sys.exit("Courier Prime did not load, so the icons would be in a fallback face.")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, url in drawn["icons"].items():
        out = (Path(args.profile) if "-profile-" in name else out_dir) / f"{name}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(base64.b64decode(url.split(",", 1)[1]))
        print(f"wrote {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
