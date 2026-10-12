"""Open stroke ends: where does a drawing have a hole the stroke cannot cover?

    python3 scripts/glass_stroke_gaps.py

Reads every drawing in `_includes/icons/glasses/` and writes nothing (MANUAL
§9.11). For each unclosed subpath endpoint it finds the nearest other endpoint
in the same drawing: two ends meeting exactly are a join, two ends near each
other but not touching are a gap. `stroke-linecap: round` extends each end by
half the stroke, so a gap shows only when it is wider than the stroke drawn
over it: 1px on a card, 2px on a drink page.

It reports pixels, not user units: each drawing has its own viewBox and is
rendered to a fixed height, so one user unit is worth a different number of
screen pixels in every icon.

A flag is a candidate, not a diagnosis (#739 was a designed free end): on a
drawing of many separate strokes two tips may simply sit near each other. And
this is an end-to-end scan, so a clean report does not mean no open ends: a
line stopping short of the MIDDLE of another line is invisible to it. Catching
that means measuring each endpoint against the other paths' geometry, which
`scripts/svgrender.py`'s `flatten()` provides.
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

    Walks the tree keeping a transform stack, because some drawings nest
    groups: a path inside an inner group takes that group's transform too, or
    every distance involving it is nonsense.
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
        # A nearest neighbour of 0 means this end is joined to another and is
        # not a candidate. A small non-zero one is a candidate; whether it is
        # a fault is a question for the eye (#739 was a designed free end).
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
