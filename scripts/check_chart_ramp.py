"""Sequential-ramp check for the temperature ruler.

The dataviz skill's own validate_palette.js lives outside this project, and
CLAUDE.md forbids reading or executing above the project folder -- so the
checks it would run are reimplemented here instead of skipped.

The ramp is ONE hue (the site's own violet), light -> dark, which is the
skill's non-negotiable for a sequential scale: doneness is a magnitude
(rare -> well done is "more cooked"), not an identity, so a rainbow or a
categorical set would both be wrong.

Built by compositing violet over the page background at rising alpha rather
than by picking six separate hexes: that guarantees a single hue and a
monotonic ramp by construction, and it is how every other tint on this site
is already made ($color-box-tint and friends).
"""

BG = (0xFA, 0xF7, 0xF8)      # $color-bg
VIOLET = (0x77, 0x34, 0xEA)  # $color-vibrant-violet
INK = (0x21, 0x1F, 0x20)     # $color-text

ALPHAS = [0.16, 0.30, 0.45, 0.60, 0.76, 0.92]


def composite(fg, bg, a):
    return tuple(round(f * a + b * (1 - a)) for f, b in zip(fg, bg))


def srgb_to_lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb):
    r, g, b = (srgb_to_lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def to_oklab(rgb):
    r, g, b = (srgb_to_lin(c) for c in rgb)
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (
        0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
        1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
        0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s,
    )


def chroma(rgb):
    _, a, b = to_oklab(rgb)
    return (a * a + b * b) ** 0.5


print(f"{'step':>4} {'hex':>9} {'OKLab L':>8} {'chroma':>7} "
      f"{'vs bg':>7} {'ink on it':>10}")
steps = []
for i, a in enumerate(ALPHAS, 1):
    rgb = composite(VIOLET, BG, a)
    L = to_oklab(rgb)[0]
    steps.append((rgb, L))
    print(f"{i:>4} {'#%02X%02X%02X' % rgb:>9} {L:>8.3f} {chroma(rgb):>7.3f} "
          f"{contrast(rgb, BG):>7.2f} {contrast(INK, rgb):>10.2f}")

print()
print("MONOTONIC (lightness must fall at every step):",
      all(steps[i][1] > steps[i + 1][1] for i in range(len(steps) - 1)))

gaps = [steps[i][1] - steps[i + 1][1] for i in range(len(steps) - 1)]
print("step gaps in OKLab L (x100):", [round(g * 100, 1) for g in gaps])
print("min gap:", round(min(gaps) * 100, 1),
      "-- a sequential ramp needs adjacent steps TELLABLE APART, ~5 is the "
      "usual floor for a fill of this size")

print()
print("lightest step vs background:", round(contrast(steps[0][0], BG), 2),
      "-- a fill only has to be SEEN (3:1 is the bar for a large mark), and "
      "the smallest step still has to clear the paper")
