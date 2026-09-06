"""Open stroke ends: where does a drawing have a hole the stroke cannot cover?

    python3 scripts/glass_stroke_gaps.py

WHAT IT MEASURES. Every unclosed subpath's endpoints, against the nearest other
endpoint in the same drawing. Two ends meeting exactly is a join; two ends near
each other but not touching is a gap. `stroke-linecap: round` extends each end
by half the stroke, so a gap is covered when it is no wider than the stroke --
1px on a card, 2px on a drink page (2026-09-05; it was 3 until #650).

WHY IT REPORTS PIXELS AND NOT USER UNITS, which is the whole reason it exists
rather than a note in a commit message. Each drawing has its own viewBox and is
rendered to a fixed HEIGHT, so one user unit is worth a different number of
screen pixels in every icon: a 2-unit gap in the punch bowl's 70-unit canvas and
the same 2 units in the sling's 116 are completely different defects. The
2026-08-31 pass that found the first batch quoted user units, and that is why it
could not say which ones actually showed.

TWO LIMITS, AND THE SECOND IS THE SERIOUS ONE.

1. A flag means "two unclosed endpoints land closer together than the stroke can
   bridge". On a single-outline glass that is nearly always a broken join. On a
   drawing made of many separate strokes -- the pineapple has 21 -- it may
   equally be two tips that genuinely sit near each other. It flags; it does not
   diagnose. Look at the drawing.

2. **IT IS AN END-TO-END SCAN, AND MANUAL 9.13 RECORDS THAT THOSE MISS A WHOLE
   CLASS OF FAULT.** Its words, from the 2026-08-31 pass: *"Measure ends against
   STROKES, not against other ends. The goblet's endpoints all met within 0.26
   units; its one fault was a line stopping 1.56 units short of the MIDDLE of
   another line. An end-to-end scan reports it clean."* This is that scan. So a
   clean report here means "no end-to-end gap", NOT "no open ends" -- a line
   stopping short of the middle of another is invisible to it, and the goblet is
   the proof that such faults are real in this set.

   Closing that would mean measuring each endpoint against every other path's
   GEOMETRY rather than its endpoints -- point-to-curve distance over flattened
   paths, which `scripts/svgrender.py`'s `flatten()` already provides. Worth
   doing if a second fault ever turns up by eye that this reported clean.

Found #739 (the margarita). Read that as "the worst one an end-to-end scan
finds", which is how the issue is now worded.
"""
import glob
import io
import math
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLASSES = os.path.join(ROOT, "_includes", "icons", "glasses", "*.svg")

# The sizes the drawings are actually rendered at, from the stylesheets.
RENDER = [
    ("universe line", 1.4 * 16),
    ("card, tallest", 10.4 * 16),
    ("drink page", 14.0 * 16),
]

NUM = r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?"
TOKEN = re.compile(r"([MmZzLlHhVvCcSsQqTtAa])|(" + NUM + ")")


def parse_transform(text):
    """Return (a, b, c, d, e, f) for the composed transform of one attribute."""
    m = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]
    for name, args in re.findall(r"(translate|scale|matrix)\s*\(([^)]*)\)", text or ""):
        v = [float(x) for x in re.findall(NUM, args)]
        if name == "translate":
            t = [1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0]
        elif name == "scale":
            sx = v[0]
            sy = v[1] if len(v) > 1 else sx
            t = [sx, 0, 0, sy, 0, 0]
        else:
            t = v[:6]
        # compose m := m * t
        a, b, c, d, e, f = m
        ta, tb, tc, td, te, tf = t
        m = [a * ta + c * tb, b * ta + d * tb,
             a * tc + c * td, b * tc + d * td,
             a * te + c * tf + e, b * te + d * tf + f]
    return m


def apply(m, x, y):
    a, b, c, d, e, f = m
    return (a * x + c * y + e, b * x + d * y + f)


def subpath_ends(d_attr):
    """[(start, end, closed)] for each subpath, in the path's own coordinates."""
    toks = TOKEN.findall(d_attr)
    out, nums, cmd = [], [], None
    cur = (0.0, 0.0)
    start = (0.0, 0.0)
    sub = None   # [start, closed]

    def flush():
        if sub is not None:
            out.append((sub[0], cur, sub[1]))

    i = 0
    items = [(c, n) for c, n in toks]
    while i < len(items):
        c, n = items[i]
        if c:
            cmd = c
            i += 1
            nums = []
            # gather the numbers that follow
            while i < len(items) and not items[i][0]:
                nums.append(float(items[i][1]))
                i += 1
        else:
            i += 1
            continue

        if cmd in "Zz":
            if sub is not None:
                out.append((sub[0], start, True))
                sub = None
            cur = start
            continue

        # argument counts per command
        step = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7}[cmd.upper()]
        rel = cmd.islower()
        first = True
        for k in range(0, len(nums) - step + 1, step):
            a = nums[k:k + step]
            if cmd.upper() == "H":
                nx, ny = (cur[0] + a[0], cur[1]) if rel else (a[0], cur[1])
            elif cmd.upper() == "V":
                nx, ny = (cur[0], cur[1] + a[0]) if rel else (cur[0], a[0])
            elif cmd.upper() == "A":
                nx, ny = (cur[0] + a[5], cur[1] + a[6]) if rel else (a[5], a[6])
            else:
                dx, dy = a[-2], a[-1]
                nx, ny = (cur[0] + dx, cur[1] + dy) if rel else (dx, dy)

            if cmd.upper() == "M" and first:
                flush()
                start = (nx, ny)
                sub = [start, False]
                cmd = "L" if cmd == "M" else "l"   # subsequent pairs are lineto
            cur = (nx, ny)
            first = False
    flush()
    return out


def compose(m, t):
    a, b, c, d, e, f = m
    ta, tb, tc, td, te, tf = t
    return [a * ta + c * tb, b * ta + d * tb,
            a * tc + c * td, b * tc + d * td,
            a * te + c * tf + e, b * te + d * tf + f]


def endpoints_of(svg):
    """Every unclosed subpath endpoint, with the transforms above it applied.

    WALKS THE TREE. An earlier version took the FIRST `<g transform>` and applied
    it to every path, which is right for a flat drawing and wrong for the six
    that nest (absinthe, goblet, nick-and-nora, old-fashioned,
    old-fashioned-double, tiki-mug): a path inside an inner group lost that
    group's transform and every distance involving it was nonsense. This is the
    same stack `_emit` keeps in scripts/normalise_glass_icons.py, and it is the
    third time in this repo that dropping a nested transform has produced a
    confident wrong answer -- see that file's "this is the absinthe bug".
    """
    pts = []
    stack = [[1.0, 0.0, 0.0, 1.0, 0.0, 0.0]]
    for m in re.finditer(r"<(/?)(g|path)\b([^>]*?)(/?)>", svg, re.S):
        close, tag, attrs, selfclose = m.groups()
        if tag == "g":
            if close:
                if len(stack) > 1:
                    stack.pop()
            else:
                t = re.search(r'transform="([^"]*)"', attrs)
                stack.append(compose(stack[-1], parse_transform(t.group(1)))
                             if t else list(stack[-1]))
                if selfclose and len(stack) > 1:
                    stack.pop()
            continue
        d = re.search(r'\sd="([^"]*)"', attrs)
        if not d:
            continue
        t = re.search(r'transform="([^"]*)"', attrs)
        m2 = compose(stack[-1], parse_transform(t.group(1))) if t else stack[-1]
        for s0, e0, closed in subpath_ends(d.group(1)):
            if closed:
                continue
            pts.append(apply(m2, *s0))
            pts.append(apply(m2, *e0))
    return pts


def gaps_for(path):
    """(worst gap in user units, viewBox height, endpoint count, locations)."""
    svg = io.open(path, encoding="utf-8").read()
    vb = re.search(r'viewBox="\s*(' + NUM + r')\s+(' + NUM + r')\s+('
                   + NUM + r')\s+(' + NUM + r')', svg)
    vx, vy, vw, vh = (float(vb.group(i)) for i in (1, 2, 3, 4))

    ends = endpoints_of(svg)

    worst, where = 0.0, None
    for i, p in enumerate(ends):
        best, at = None, None
        for j, q in enumerate(ends):
            if i == j:
                continue
            dist = math.hypot(p[0] - q[0], p[1] - q[1])
            if best is None or dist < best:
                best, at = dist, q
        # A nearest neighbour of 0 means this end is JOINED to another and is
        # not a candidate at all. A small non-zero one is a candidate; whether
        # it is a fault is a question for the eye, not for this number -- see
        # the docstring, and #739, which was a false positive of exactly this
        # kind (a designed free end 1.76 units outside a junction that itself
        # met exactly).
        if best is not None and 0 < best <= 4.0 and best > worst:
            worst, where = best, ((p[0] + at[0]) / 2, (p[1] + at[1]) / 2)

    loc = None
    if where and vw and vh:
        loc = (100 * (where[0] - vx) / vw, 100 * (where[1] - vy) / vh)
    return worst, vh, len(ends), loc


def report():
    rows = []
    for path in sorted(glob.glob(GLASSES)):
        worst, vb_h, n, loc = gaps_for(path)
        rows.append((worst / vb_h if vb_h else 0, worst, vb_h, n,
                     os.path.basename(path)[:-4], loc))

    rows.sort(reverse=True)
    print("%-22s %8s %8s %s" % ("drawing", "gap(uu)", "of vb-h", "  rendered gap in px at each size"))
    print("%-22s %8s %8s   %s" % ("", "", "", "  ".join("%-13s" % r[0] for r in RENDER)))
    shown = 0
    for frac, worst, vb_h, n, name, loc in rows:
        if worst <= 0:
            continue
        shown += 1
        px = ["%13.2f" % (frac * h) for _, h in RENDER]
        print("%-22s %8.3f %7.2f%%   %s" % (name, worst, frac * 100, "  ".join(px)))
        if loc:
            print("%-22s   at about %.0f%% across and %.0f%% down the canvas"
                  % ("", loc[0], loc[1]))

    print()
    print("%d of %d drawings have an endpoint gap under 4 user units." % (shown, len(rows)))
    print("A gap is only visible if it is wider than the stroke drawn over it,")
    print("because `stroke-linecap: round` bridges one stroke width. The stroke")
    print("is a NON-SCALING 1px on a card and 2px on a drink page (2026-09-05,")
    print("down from 3 -- #650), so compare the pixel columns against those.")


if __name__ == "__main__":
    report()
