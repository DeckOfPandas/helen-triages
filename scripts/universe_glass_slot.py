"""How wide must the universe line's glass slot be, if every glass is one height?

THE TWO RULES THAT PULL AGAINST EACH OTHER, both Helen's, both 2026-09-05:
"don't scale -- all the same height", and "leave a fixed width for the glass so
the name tape doesn't jump around on redeal". One height across the 27 drawings
means their WIDTHS diverge, so a slot narrower than the widest drawing would cap
it and render it shorter than the others -- breaking the first rule in order to
keep the second. The slot therefore has to clear the widest drawing at whatever
height is chosen, and this is the script that says which drawing that is and by
how much.

IT PRODUCED $universe-glass-slot IN `_sass/cocktails/_universe.scss` (2.3rem,
against $universe-glass-height's 1.4rem). Kept in the repo rather than left in
tmp/ because the answer moves whenever the artwork does: a new glass wider than
the punch bowl, or a change to the chosen height, and the slot in that file is
silently wrong -- a wide glass quietly shorter than its neighbours is exactly the
kind of thing nobody notices. Re-run it, do not re-guess it.

The height is taken from the stylesheet rather than restated here, so the two
cannot disagree about what is being measured.

    python3 scripts/universe_glass_slot.py
"""
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLASSES = os.path.join(ROOT, "_includes", "icons", "glasses", "*.svg")
UNIVERSE_SCSS = os.path.join(ROOT, "_sass", "cocktails", "_universe.scss")

# Air either side, so the widest drawing does not sit edge to edge in its slot.
SLOT_AIR_REM = 0.2


def declared(name, default):
    """Read a `$name: <n>rem;` out of _universe.scss."""
    try:
        text = open(UNIVERSE_SCSS, encoding="utf-8").read()
    except OSError:
        return default, False
    m = re.search(r"\$%s:\s*([\d.]+)rem" % re.escape(name), text)
    return (float(m.group(1)), True) if m else (default, False)


def aspects():
    """width / height for every published glass drawing, from its viewBox."""
    out = []
    for path in sorted(glob.glob(GLASSES)):
        svg = open(path, encoding="utf-8").read()
        m = re.search(r'viewBox="\s*[\d.eE+-]+\s+[\d.eE+-]+\s+([\d.eE+-]+)\s+([\d.eE+-]+)', svg)
        if not m:
            print("  !! no viewBox, skipped: %s" % os.path.basename(path))
            continue
        w, h = float(m.group(1)), float(m.group(2))
        if h <= 0:
            print("  !! zero height, skipped: %s" % os.path.basename(path))
            continue
        out.append((w / h, os.path.basename(path)[:-4], w, h))
    return sorted(out, reverse=True)


def main():
    rows = aspects()
    if not rows:
        raise SystemExit("no glass drawings found under _includes/icons/glasses/")

    height, found_h = declared("universe-glass-height", 1.4)
    slot, found_s = declared("universe-glass-slot", 2.3)
    if not (found_h and found_s):
        print("NOTE: could not read the variables out of _sass/cocktails/_universe.scss;"
              " falling back to the values that were current on 2026-09-05.\n")

    print("%d glass drawings, widest first (width / height):\n" % len(rows))
    for ratio, name, w, h in rows[:5]:
        print("  %-24s %5.3f   viewBox %g x %g" % (name, ratio, w, h))
    print("  %-24s ..." % "")
    for ratio, name, w, h in rows[-2:]:
        print("  %-24s %5.3f   viewBox %g x %g" % (name, ratio, w, h))

    widest, widest_name = rows[0][0], rows[0][1]
    narrowest = rows[-1][0]
    needed = height * widest

    print("\nat $universe-glass-height %.2frem:" % height)
    print("  widest  (%s) draws %.3frem wide" % (widest_name, needed))
    print("  narrowest (%s) draws %.3frem wide" % (rows[-1][1], height * narrowest))
    print("  the spread is %.1fx, which is what the fixed slot is paying for"
          % (widest / narrowest))
    print("\n  required slot >= %.3frem   (+%.2frem air = %.2frem)"
          % (needed, SLOT_AIR_REM, needed + SLOT_AIR_REM))
    print("  _universe.scss declares %.2frem" % slot)

    if slot < needed:
        raise SystemExit(
            "\nFAIL: the slot is NARROWER than the widest drawing. `%s` will be\n"
            "capped by the slot and render shorter than every other glass, which\n"
            "is the exact failure the fixed slot exists to avoid. Raise\n"
            "$universe-glass-slot to at least %.2frem." % (widest_name, needed + SLOT_AIR_REM))

    print("\nOK: the slot clears the widest drawing by %.3frem." % (slot - needed))


if __name__ == "__main__":
    main()
