"""Where does the universe line stop fitting on one row?

THE NUMBER THIS PRODUCED is `$universe-stack-width` (820px) in
`_sass/cocktails/_universe.scss` -- the width at which the ingredients drop below
the name. Helen, 2026-09-05: "please allow the line to stack, first line name,
second line ingredients."

WHY IT IS CALCULABLE AT ALL: Courier Prime is monospace, so a name's tape is
arithmetic rather than a measurement, and every other thing on the row is a fixed
token. The row holds, left to right: the label, the glass slot, the name on its
tape, the ingredients, and `deal again`.

THE NAME IS THE PART THAT VARIES, AND THE RELEVANT SET IS NOT EVERY DRINK. Since
#692 the universe deals only from ship `yes` and `oh gods yes`, so it is THAT
distribution that decides the breakpoint. Feeding it all 124 would overstate the
tail and push the number too high.

RE-RUN IT WHEN THE COLLECTION GROWS, and especially after a promotion batch: one
long name entering the dealable set moves the 90th percentile, and the symptom of
a stale breakpoint is silent -- an ingredient line squeezed to two words with the
brackets holding nothing, on exactly the drinks Helen rated best.

    python3 scripts/universe_line_width.py

It reads the drinks off the collections rather than off a build, so it needs no
`jekyll build` first. The drafts repo is gitignored and may be absent in a fresh
worktree; it says so and carries on with whatever it can see.
"""
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNIVERSE_SCSS = os.path.join(ROOT, "_sass", "cocktails", "_universe.scss")

COURIER_ADVANCE = 0.6      # em, monospace
ROOT_PX = 16

# The dealable rungs. Kept in step with the `data-universe-rows` selector in
# cocktails/index.html and with `chaos` in the same file.
DEALABLE = ("yes", "oh gods yes")

# The label, verbatim from cocktails/index.html.
LABEL = "the universe says..."

# An ingredient line worth showing at all: roughly two short items before the
# ellipsis. Below this the brackets are holding almost nothing, which is the
# failure the breakpoint exists to prevent rather than a matter of taste.
INGREDIENTS_MIN_CHARS = 22


def courier_px(chars, rem, tracking_em=0.0):
    return chars * (rem * ROOT_PX * COURIER_ADVANCE + tracking_em * rem * ROOT_PX)


def declared_rem(name, default):
    try:
        text = open(UNIVERSE_SCSS, encoding="utf-8").read()
    except OSError:
        return default
    m = re.search(r"\$%s:\s*([\d.]+)rem" % re.escape(name), text)
    return float(m.group(1)) if m else default


def declared_px(name, default):
    try:
        text = open(UNIVERSE_SCSS, encoding="utf-8").read()
    except OSError:
        return default
    m = re.search(r"\$%s:\s*(\d+)px" % re.escape(name), text)
    return int(m.group(1)) if m else default


def dealable_names():
    """Titles of the drinks the universe may deal, from the collections."""
    names, missing = [], []
    for folder in ("_cocktail_recipes", "_cocktail_drafts"):
        base = os.path.join(ROOT, folder)
        if not os.path.isdir(base):
            missing.append(folder)
            continue
        for path in glob.glob(os.path.join(base, "**", "*.md"), recursive=True):
            text = open(path, encoding="utf-8", errors="replace").read()
            ship = re.search(r'^\s*ship:\s*["\']?([^"\'\n]+)', text, re.M)
            title = re.search(r'^title:\s*["\']?([^"\'\n]+)', text, re.M)
            if ship and title and ship.group(1).strip() in DEALABLE:
                names.append(title.group(1).strip())
    return names, missing


def main():
    names, missing = dealable_names()
    for folder in missing:
        print("NOTE: %s is not present (gitignored in a worktree); "
              "its drinks are not counted." % folder)
    if not names:
        raise SystemExit("no dealable drinks found -- nothing to derive a breakpoint from.")

    lengths = sorted(len(n) for n in names)

    def pct(p):
        return lengths[min(len(lengths) - 1, int(len(lengths) * p))]

    glass_slot = declared_rem("universe-glass-slot", 2.3) * ROOT_PX
    declared_bp = declared_px("universe-stack-width", 820)

    # Fixed furniture, all from the stylesheet's own tokens.
    label = courier_px(len(LABEL), 0.78, 0.1)   # uppercase, 0.1em tracked
    grid_gap = 0.75 * ROOT_PX * 2               # $space-md, twice
    pick_gap = 0.45 * ROOT_PX * 2               # glass|name and name|ingredients
    button = 12 * 0.82 * ROOT_PX * 0.5          # "deal again" in Selawik, ~0.5em average
    page_pad = 1.5 * ROOT_PX * 2                # the layout's own left/right padding
    furniture = label + glass_slot + grid_gap + pick_gap + button
    ingredients_min = courier_px(INGREDIENTS_MIN_CHARS, 0.82)

    def tape(chars):
        # the word, plus 1.05em of tape padding either side, at 1rem
        return courier_px(chars, 1.0, 0.03) + 2 * 1.05 * ROOT_PX

    print("\ndealable drinks (ship %s): %d"
          % (" / ".join(DEALABLE), len(names)))
    print("name length: median %d, 75th %d, 90th %d, longest %d (%s)"
          % (pct(0.5), pct(0.75), pct(0.9), lengths[-1], max(names, key=len)))
    print("\nfixed furniture: label %.0f + glass slot %.0f + gaps %.0f + deal again %.0f"
          " = %.0f px" % (label, glass_slot, grid_gap + pick_gap, button, furniture))
    print("an ingredient line worth showing (%d chars): %.0f px"
          % (INGREDIENTS_MIN_CHARS, ingredients_min))
    print()

    needed = {}
    for p, tag in ((0.5, "median"), (0.75, "75th"), (0.9, "90th")):
        n = pct(p)
        viewport = furniture + tape(n) + ingredients_min + page_pad
        needed[tag] = viewport
        print("%-6s name (%2d chars, tape %3.0f px): needs %.0f px of viewport"
              % (tag, n, tape(n), viewport))

    print("\n_universe.scss declares $universe-stack-width: %dpx" % declared_bp)
    target = needed["90th"]
    if declared_bp + 10 < target:
        print("\nWARNING: the breakpoint is below what the 90th-percentile name needs"
              " (%.0f px)." % target)
        print("The top decile of dealable names will squeeze the ingredient line to"
              " almost nothing")
        print("before the row ever stacks. Consider raising it to about %d px."
              % (round(target / 5) * 5))
    else:
        print("\nOK: the breakpoint covers the 90th-percentile name"
              " (needs %.0f px)." % target)


if __name__ == "__main__":
    main()
