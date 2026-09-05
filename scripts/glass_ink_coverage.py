"""Ink coverage per glass: which drawings read as a smudge at size?

    python3 scripts/glass_ink_coverage.py

THE MEASUREMENT #525 SET ITS REDRAW TARGET WITH. That issue found the pineapple
at 5.3x the set median and the tiki mug at 2.7x, with everything else between
0.6x and 1.6x -- and used it to say that both were dense enough to need
redrawing rather than restyling. Helen redrew the pineapple on 2026-09-05 and it
came down to 2.4x; the tiki mug is now the densest in the set at 3.6x, which is
#738.

RATIOS, NOT PERCENTAGES, ARE THE COMPARABLE THING. The absolute number depends
on the render height, the stroke and the ink threshold, so two runs made on
different settings do not agree and should not be made to. Compare within one
run: the median is printed with the table for exactly that reason.

WHY IT IS MEASURED AT DRINK-PAGE SIZE. Density shows where the drawing is large.
The same icon at card size merely looks bold; at 14rem it fills in.
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
