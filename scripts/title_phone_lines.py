"""How many lines does a drink page's title take on a phone, at each size?

REPRODUCES `$title-size-phone` (1.6rem) in `_sass/cocktails/_cocktail.scss`:
the largest tenth of a rem at which no title takes four lines of tape at
either phone width and, at 390px, all but one fit in two (2026-10-10: 16 of
212 took three or four at 2rem).

THE QUESTION IS #1357. Helen, 2026-10-10: "We can reduce font size a little for
cocktail titles on mobile to reduce the linebreaking", with Haley Traub's Frozen
Margarita printed over four lines. At 2rem the tape's word box on a 390px phone
holds 12 characters, and HALEY TRAUB'S is 13.

WHY IT IS CALCULABLE: Courier Prime is monospace (0.6em advance, plus the
0.03em tracking `.drink-card-name` sets), and everything else is a token. Below
600px the tape spans the column plus the artwork's own left inset
(`$tape-art-inset-x`), and carries `$title-tape-pad-x` of bare tape either side
of the word, in em OF THE TITLE -- so a smaller title gains twice: each
character is narrower, and the padding gives width back.

THE FIT RULE IS card-name-fit.js's, restated: a name that fits stays; one that
is over by no more than 1/0.86 steps down to 0.86 and stays on one line; any
other wraps AT ITS FULL SIZE, breaking at spaces and after hyphens.

RE-RUN IT WHEN THE COLLECTION GROWS. A long new title is the thing that would
move this, and the symptom is a four-line tape on a phone.

    python3 scripts/title_phone_lines.py

It reads titles off the collections, so it needs no build. The drafts repo is
gitignored and may be absent in a fresh worktree; it says so and carries on.
"""
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COCKTAIL_SCSS = os.path.join(ROOT, "_sass", "cocktails", "_cocktail.scss")

ROOT_PX = 16
ADVANCE = 0.6 + 0.03       # em: Courier Prime's advance plus the name's tracking
STEP = 0.86                # card-name-fit.js's STEP, $card-name-step
PAGE_PAD = 24              # `main`'s $space-xl, each side
VIEWPORTS = (360, 390)
CANDIDATES = (2.0, 1.9, 1.8, 1.75, 1.7, 1.6, 1.5)


def declared(name, unit, default):
    try:
        text = open(COCKTAIL_SCSS, encoding="utf-8").read()
    except OSError:
        return default
    m = re.search(r"\$%s:\s*([\d.]+)%s" % (re.escape(name), unit), text)
    return float(m.group(1)) if m else default


def titles():
    names, missing = [], []
    for folder in ("_cocktail_recipes", "_cocktail_drafts"):
        base = os.path.join(ROOT, folder)
        if not os.path.isdir(base):
            missing.append(folder)
            continue
        for path in glob.glob(os.path.join(base, "**", "*.md"), recursive=True):
            text = open(path, encoding="utf-8", errors="replace").read()
            title = re.search(r'^title:\s*(.+)$', text, re.M)
            if title:
                names.append(title.group(1).strip().strip("\"'"))
    return names, missing


def word_box(viewport, size_px, pad_em, inset):
    """Width the lettering has: the tape, less its padding either side."""
    tape = (viewport - 2 * PAGE_PAD) * (1 + inset)
    return tape - 2 * pad_em * size_px


def lines(title, viewport, rem, pad_em, inset):
    size = rem * ROOT_PX
    box = word_box(viewport, size, pad_em, inset)
    width = len(title) * ADVANCE * size
    if width <= box + 1:
        return 1
    if width <= box / STEP:
        stepped = size * STEP
        if len(title) * ADVANCE * stepped <= word_box(viewport, stepped, pad_em, inset) + 1:
            return 1
    per_line = int((box + 1) // (ADVANCE * size))
    # Break opportunities: spaces (dropped at a break) and after a hyphen (kept).
    pieces = []   # (text, a space precedes it)
    for word in title.split():
        for i, part in enumerate(re.findall(r"[^-]+-?|-", word)):
            pieces.append((part, i == 0))
    count, used = 1, 0
    for part, spaced in pieces:
        gap = 1 if used and spaced else 0
        if used and used + gap + len(part) > per_line:
            count += 1
            used = len(part)
        else:
            used += gap + len(part)
    return count


def main():
    names, missing = titles()
    for folder in missing:
        print("NOTE: %s is not present (gitignored in a worktree); "
              "its titles are not counted." % folder)
    if not names:
        raise SystemExit("no titles found -- nothing to derive a size from.")

    pad_em = declared("title-tape-pad-x", "em", 1.6)
    inset = declared("tape-art-inset-x", "%", 4.14) / 100
    shipped = declared("title-size-phone", "rem", 2.0)

    print("\n%d titles; longest %d characters (%s)"
          % (len(names), max(len(n) for n in names), max(names, key=len)))
    print("tape padding %.2fem each side, artwork inset %.2f%%\n" % (pad_em, inset * 100))

    sizes = sorted(set(CANDIDATES) | {shipped}, reverse=True)
    for viewport in VIEWPORTS:
        print("at %dpx:" % viewport)
        print("  %-8s %5s %5s %5s %5s   %s" % ("size", "1", "2", "3", "4+", "chars/line"))
        for rem in sizes:
            tally = [0, 0, 0, 0]
            for n in names:
                tally[min(lines(n, viewport, rem, pad_em, inset), 4) - 1] += 1
            per_line = int((word_box(viewport, rem * ROOT_PX, pad_em, inset) + 1)
                           // (ADVANCE * rem * ROOT_PX))
            mark = "  <- $title-size-phone" if rem == shipped else ""
            print("  %-8s %5d %5d %5d %5d   %d%s"
                  % ("%grem" % rem, tally[0], tally[1], tally[2], tally[3], per_line, mark))
        print()

    worst = [n for n in names if lines(n, 390, shipped, pad_em, inset) > 2]
    if worst:
        print("at %grem these take more than two lines at 390px:" % shipped)
        for n in sorted(worst, key=len, reverse=True):
            print("  %d lines  %s" % (lines(n, 390, shipped, pad_em, inset), n))
    else:
        print("at %grem no title takes more than two lines at 390px." % shipped)


if __name__ == "__main__":
    main()
