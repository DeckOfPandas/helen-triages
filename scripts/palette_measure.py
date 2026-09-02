#!/usr/bin/env python3
"""Measure a palette: WCAG contrast, dichromat simulation, CIEDE2000, CIELAB L*.

WHY THIS IS IN scripts/ AND NOT tmp/
====================================
Three comments in this repo told their reader to "re-run tmp/neon_values.py" or
"tmp/greens2.py". Both were written to settle real questions -- the five-accent
separation check and the heading greens -- and both are GONE, because tmp/ is
gitignored. So three instructions pointed at nothing, and the next person asking
"is this hue still far enough from that one" had to rebuild the tool before they
could answer.

That happened again on 2026-09-01: the black-on-black work (#469) needed exactly
these measurements and rebuilt them from scratch in tmp/. This is that rebuild,
kept. HANDOVER 12's rule about instructions applies to tooling too -- an
instruction to re-run something is only as good as the something.

WHAT IT IS FOR
==============
Any question of the form "can this colour carry text there", "will these two
still read apart to Simon", or "how much lighter is this than that". It knows
nothing about this repo's palette on purpose: pass hex values in and it answers.

    python3 scripts/palette_measure.py --contrast '#FF00C8' '#0e0e10'
    python3 scripts/palette_measure.py --separation '#30E88C' '#F47E25'
    python3 scripts/palette_measure.py --lstar '#0e0e10' '#17171a' '#2c2c31'

THE BARS, AND WHERE THEY COME FROM
==================================
  4.5:1   text, WCAG AA
  3.0:1   a decorative mark, and large text
  dE 10   two colours that must stay apart under dichromacy -- HANDOVER 9.13's
          bar, and it applies ONLY where colour carries meaning alone. A heading
          sits under its own name in words, so its hue is reinforcement and may
          safely collapse. A goodness MARK and a matched ingredient may not.
  L* 1.0  roughly a just-noticeable lightness step on a good screen in a dark
          room, and several times that in daylight.
"""
import argparse
import math

# --- sRGB ---------------------------------------------------------------------


def hex2rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb2hex(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(c))) for c in rgb)


def _lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb):
    r, g, b = (_lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = luminance(hex2rgb(a)), luminance(hex2rgb(b))
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def over(fg, alpha, bg):
    """Composite fg at alpha over bg -- what the eye actually receives from a
    translucent wash, which is the only thing a contrast check may be run on."""
    f, b = hex2rgb(fg), hex2rgb(bg)
    return rgb2hex(tuple(alpha * f[i] + (1 - alpha) * b[i] for i in range(3)))


# --- CIELAB -------------------------------------------------------------------
def _xyz(rgb):
    r, g, b = (_lin(c) for c in rgb)
    return (r * 0.4124 + g * 0.3576 + b * 0.1805,
            r * 0.2126 + g * 0.7152 + b * 0.0722,
            r * 0.0193 + g * 0.1192 + b * 0.9505)


def lab(h):
    x, y, z = _xyz(hex2rgb(h))

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else (7.787 * t + 16 / 116)
    fx, fy, fz = f(x / 0.95047), f(y / 1.0), f(z / 1.08883)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def lstar(h):
    """Perceptual lightness. Equal steps LOOK equal, which equal steps in hex
    emphatically do not -- the reason the card ladder was measured in it."""
    return lab(h)[0]


def ciede2000(h1, h2):
    L1, a1, b1 = lab(h1)
    L2, a2, b2 = lab(h2)
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7))) if Cb else 0
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360 if (a1p or b1) else 0
    h2p = math.degrees(math.atan2(b2, a2p)) % 360 if (a2p or b2) else 0
    dLp, dCp = L2 - L1, C2p - C1p
    if C1p * C2p == 0:
        dhp = 0
    elif abs(h2p - h1p) <= 180:
        dhp = h2p - h1p
    elif h2p - h1p > 180:
        dhp = h2p - h1p - 360
    else:
        dhp = h2p - h1p + 360
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp) / 2)
    Lbp, Cbp = (L1 + L2) / 2, (C1p + C2p) / 2
    if C1p * C2p == 0:
        hbp = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hbp = (h1p + h2p) / 2
    elif h1p + h2p < 360:
        hbp = (h1p + h2p + 360) / 2
    else:
        hbp = (h1p + h2p - 360) / 2
    T = (1 - 0.17 * math.cos(math.radians(hbp - 30))
         + 0.24 * math.cos(math.radians(2 * hbp))
         + 0.32 * math.cos(math.radians(3 * hbp + 6))
         - 0.20 * math.cos(math.radians(4 * hbp - 63)))
    Sl = 1 + (0.015 * (Lbp - 50) ** 2) / math.sqrt(20 + (Lbp - 50) ** 2)
    Sc, Sh = 1 + 0.045 * Cbp, 1 + 0.015 * Cbp * T
    Rt = (-math.sin(math.radians(2 * (30 * math.exp(-(((hbp - 275) / 25) ** 2)))))
          * (2 * math.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7)) if Cbp else 0))
    return math.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2
                     + Rt * (dCp / Sc) * (dHp / Sh))


# --- dichromacy (Vienot, Brettel & Mollon 1999) -------------------------------
_RGB2LMS = [[17.8824, 43.5161, 4.11935],
            [3.45565, 27.1554, 3.86714],
            [0.0299566, 0.184309, 1.46709]]
_LMS2RGB = [[0.0809444479, -0.130504409, 0.116721066],
            [-0.0102485335, 0.0540193266, -0.113614708],
            [-0.000365296938, -0.00412161469, 0.693511405]]
_SIM = {"protanopia":   [[0, 2.02344, -2.52581], [0, 1, 0], [0, 0, 1]],
        "deuteranopia": [[1, 0, 0], [0.494207, 0, 1.24827], [0, 0, 1]],
        "tritanopia":   [[1, 0, 0], [0, 1, 0], [-0.395913, 0.801109, 0]]}


def _mul(m, v):
    return [sum(m[i][j] * v[j] for j in range(3)) for i in range(3)]


def simulate(h, kind):
    v = [float(c) for c in hex2rgb(h)]
    return rgb2hex(_mul(_LMS2RGB, _mul(_SIM[kind], _mul(_RGB2LMS, v))))


# --- reports ------------------------------------------------------------------
def report_contrast(fg, bg):
    r = contrast(fg, bg)
    print(f"{fg} on {bg}:  {r:.2f}:1")
    for bar, what in ((4.5, "text (AA)"), (3.0, "a decorative mark / large text")):
        print(f"   {'PASSES' if r >= bar else 'FAILS ':6} {bar} — {what}")


def report_separation(a, b):
    print(f"{a} vs {b}\n  normal vision      dE {ciede2000(a, b):5.1f}")
    for kind in ("protanopia", "deuteranopia", "tritanopia"):
        sa, sb = simulate(a, kind), simulate(b, kind)
        d = ciede2000(sa, sb)
        print(f"  {kind:<18} dE {d:5.1f}  {'ok' if d >= 10 else 'BELOW THE BAR OF 10'}"
              f"   ({sa} vs {sb})")
    print("\n  The bar applies only where colour carries the meaning ALONE.")


def report_lstar(colours):
    print(f"{'colour':10} {'L*':>7}   steps from the first")
    base = lstar(colours[0])
    for c in colours:
        print(f"{c:10} {lstar(c):7.2f}   {lstar(c) - base:+7.2f}")
    print("\n  ~1.0 of L* is about a just-noticeable step on a good screen in the"
          "\n  dark, and several times that in daylight.")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--contrast", nargs=2, metavar=("FG", "BG"))
    g.add_argument("--separation", nargs=2, metavar=("A", "B"))
    g.add_argument("--lstar", nargs="+", metavar="HEX")
    g.add_argument("--over", nargs=3, metavar=("FG", "ALPHA", "BG"),
                   help="composite a wash, then report it")
    a = p.parse_args()
    if a.contrast:
        report_contrast(*a.contrast)
    elif a.separation:
        report_separation(*a.separation)
    elif a.lstar:
        report_lstar(a.lstar)
    else:
        fg, alpha, bg = a.over
        mixed = over(fg, float(alpha), bg)
        print(f"{fg} at {alpha} over {bg}  ->  {mixed}   (L* {lstar(mixed):.2f})")


if __name__ == "__main__":
    main()
