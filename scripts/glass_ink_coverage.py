"""Ink coverage per glass: which drawings read as a smudge at size?

    python3 scripts/glass_ink_coverage.py

Rasterises every drawing in `_includes/icons/glasses/` with `svgrender` at
drink-page size and prints the share of the canvas that is ink, densest
first, each as a multiple of the set median (MANUAL §9.11). It writes nothing.
A drawing several times the median is dense enough to need redrawing, not
restyling (#525, #738).

Ratios, not percentages, are the comparable thing: the absolute number depends
on the render height, the stroke and the ink threshold, so compare within one
run. It measures at drink-page size because density shows where the drawing is
large: an icon that merely looks bold on a card fills in at 14rem.
"""
import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import svgrender  # noqa: E402

GLASSES = os.path.join(ROOT, "_includes", "icons", "glasses", "*.svg")
HEIGHT = 224      # 14rem, the drink page's $glass-min
STROKE = 2        # the weight Helen chose 2026-09-05, down from 3


def coverage(path):
    paths, viewbox, translate, _ = svgrender.parse_icon(path)
    W, H, gray = svgrender.render(paths, viewbox, height_px=HEIGHT,
                                  stroke=STROKE, translate=translate)
    inked = sum(1 for v in gray if v < 250)
    return 100.0 * inked / (W * H)


rows = []
for p in sorted(glob.glob(GLASSES)):
    try:
        rows.append((coverage(p), os.path.basename(p)[:-4]))
    except Exception as exc:
        print("  !! %s: %s" % (os.path.basename(p), exc))

rows.sort(reverse=True)
median = sorted(c for c, _ in rows)[len(rows) // 2]

print("at %dpx tall, stroke %s  --  set median %.1f%%\n" % (HEIGHT, STROKE, median))
print("%-22s %8s %8s" % ("drawing", "coverage", "vs median"))
for c, name in rows[:6]:
    mark = "  <-- redrawn 2026-09-05" if name in ("pineapple", "coconut") else ""
    print("%-22s %7.1f%% %7.1fx%s" % (name, c, c / median, mark))
print("%-22s %8s %8s" % ("...", "", ""))
for c, name in rows[-2:]:
    print("%-22s %7.1f%% %7.1fx" % (name, c, c / median))

print()
for name in ("pineapple", "coconut"):
    hit = [(c, n) for c, n in rows if n == name]
    if hit:
        c = hit[0][0]
        print("%-10s now %.1f%%, %.1fx the median" % (name, c, c / median))
