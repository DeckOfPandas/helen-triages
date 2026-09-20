#!/usr/bin/env python3
"""List every published recipe and drink the gate is currently hiding.

    python3 scripts/dark_pages.py                 # the working tree
    python3 scripts/dark_pages.py origin/main     # what is dark on the live site

A DARK PAGE IS INVISIBLE BY DESIGN AND THAT IS THE PROBLEM THIS SOLVES. The
publish gate fails closed: a held file stays in the public repo and its page
simply stops existing, and the cards deliberately do not show the flags (#562 --
"a work-state note on every unfinished row is a to-do list down the side of the
page you use to decide what to drink"). So nothing on the site, in a build log
or in a green test says a recipe has gone dark. Counting is the only thing that
does.

Smokestack Lightning proved it on 2026-09-19: `proofread: false` since
2026-09-16, off the live site for three days, found only because a promotion
check happened to print 65 files against 64 pages. Helen, 2026-09-20: "Are
there any other recipes currently sitting dark, on either site?" -- this is the
answer to that question, repeatably.

TAKE A REF, NOT JUST THE WORKING TREE. On a feature branch the two differ, and
the question is almost always about what is live. `origin/main` needs
`sh scripts/git-fetch-main.sh` first or it answers about a stale main -- which
it did on 2026-09-20, reporting 18 dark recipes that had been fixed by a merge
an hour earlier.

Exit status is 0 whether or not anything is dark: a held page is usually
deliberate, and this reports rather than judges. Use it before opening a
`blocked-on-helen` batch issue (`scripts/needs_helen.py`) to check the batch is
the whole story, and after a promotion to check nothing was left behind.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# `rewritten` is a leg for DRINKS only, since #1137: on `cocktail_recipes` it
# decides whether the page exists at all. Food keeps two legs, and widening it
# there is a separate ruling with its own blast radius (MANUAL §9.1.1).
COLLECTIONS = [
    ("food", "_food_recipes", ("awaiting_fix", "proofread")),
    ("drinks", "_cocktail_recipes", ("awaiting_fix", "proofread", "rewritten")),
]
OPEN = {"awaiting_fix": "false", "proofread": "true", "rewritten": "true"}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT).stdout


def files_at(ref: str | None, directory: str) -> list[str]:
    if ref is None:
        return sorted(str(p.relative_to(ROOT)) for p in (ROOT / directory).glob("*.md"))
    listing = git("ls-tree", "-r", "--name-only", ref, f"{directory}/")
    return sorted(f for f in listing.splitlines() if f.endswith(".md"))


def text_at(ref: str | None, relpath: str) -> str:
    if ref is None:
        return (ROOT / relpath).read_text(encoding="utf-8")
    return git("show", f"{ref}:{relpath}")


def main() -> int:
    ref = sys.argv[1] if len(sys.argv) > 1 else None
    print(f"ref: {ref or 'working tree'}\n")

    total_dark = 0
    for label, directory, legs in COLLECTIONS:
        files = files_at(ref, directory)
        dark = []
        for relpath in files:
            text = text_at(ref, relpath)
            held = []
            for leg in legs:
                m = re.search(rf"^  {leg}: (.+?)\s*$", text, re.M)
                got = m.group(1) if m else "MISSING"
                if got != OPEN[leg]:
                    held.append(f"{leg}={got}")
            if held:
                title = re.search(r'^title:\s*"?(.+?)"?\s*$', text, re.M)
                dark.append((Path(relpath).stem, title.group(1) if title else "?", held))

        print(f"--- {label}: {len(files)} published, {len(dark)} dark ---")
        for slug, title, held in dark:
            print(f"  {slug}")
            print(f"      {title}")
            print(f"      held by: {', '.join(held)}")
        if not dark:
            print("  (none)")
        print()
        total_dark += len(dark)

    print(f"TOTAL DARK: {total_dark}")
    if total_dark:
        print("\nEach one is off the live site. If any is waiting on Helen and has "
              "no open issue, raise ONE batch issue: scripts/needs_helen.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
