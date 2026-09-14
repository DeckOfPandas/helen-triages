#!/usr/bin/env python3
"""How far each tape SVG insets its black band from its own viewBox ends.

    python3 scripts/tape_insets.py

The derivation behind `$tape-art-inset-x` in _sass/cocktails/_cocktail.scss
(#995, 2026-09-12). Kept in `scripts/` rather than `tmp/` because MANUAL 13.11
says so -- "a number derived in `tmp/` is one nobody can reproduce" -- and it
was first written in `tmp/` and cited from two places that could not run it.

WHY THE NUMBER IS A PERCENTAGE AND NOT A LENGTH. decorations.js stretches the
tape artwork to the tape's box (`preserveAspectRatio="none"`), so the band's
inset inside the viewBox becomes a fraction of the tape's RENDERED width. A
phone tape's box can start exactly on the column while its band starts ~14px
in, and no fixed length corrects that for every drink.

WHICH COLUMN TO READ. The polygon's LEFT end is slanted, so each file has two
left x values; `left` is the smaller -- the band's leading corner. The modal
value across the fifteen is what the stylesheet uses, because #779 rolls a
random tape per load and no single number is exact for all of them.

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
