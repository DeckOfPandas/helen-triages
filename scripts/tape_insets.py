#!/usr/bin/env python3
"""How far each tape SVG insets its black band from its own viewBox ends.

    python3 scripts/tape_insets.py

Derives `$tape-art-inset-x` in `_sass/cocktails/_cocktail.scss` (#995, MANUAL
§13.11): the modal left inset across the files in assets/img/chrome/tape/. It
reads those and writes nothing.

The number is a percentage, not a length: decorations.js stretches the tape
artwork to the tape's box (`preserveAspectRatio="none"`), so the band's inset
inside the viewBox becomes a fraction of the tape's rendered width.

The polygon's left end is slanted, so each file has two left x values; `left`
is the smaller, the band's leading corner. The stylesheet uses the modal value
because the header rolls a random tape per load (#779) and no single number is
exact for all of them.

Re-run this if a tape is added or redrawn, and move the Sass variable if the
modal value changes.
"""
import collections
import os
import re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAPES = os.path.join(HERE, "assets", "img", "chrome", "tape")


def number(name):
    found = re.findall(r"\d+", name)
    return int(found[0]) if found else 0


def main():
    lefts = []
    for name in sorted(os.listdir(TAPES), key=number):
        if not name.endswith(".svg"):
            continue
        with open(os.path.join(TAPES, name)) as fh:
            text = fh.read()
        width = float(re.search(r'viewBox="([\d.\- ]+)"', text).group(1).split()[2])
        points = re.search(r'<polygon points="([^"]+)"', text).group(1)
        xs = [float(p.split(",")[0]) for p in points.split()]
        left_pct = min(xs) / width * 100
        right_pct = (width - max(xs)) / width * 100
        lefts.append(round(left_pct, 2))
        print(f"{name:12s} left {left_pct:5.2f}%   right {right_pct:5.2f}% from the end")

    modal, count = collections.Counter(lefts).most_common(1)[0]
    print(f"\nmodal left inset: {modal}% ({count} of {len(lefts)} tapes); "
          f"range {min(lefts)}-{max(lefts)}%")


if __name__ == "__main__":
    main()
