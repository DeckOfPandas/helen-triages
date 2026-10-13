#!/usr/bin/env python3
"""List every published recipe and drink the gate is currently hiding.

    python3 scripts/dark_pages.py                 # the working tree
    python3 scripts/dark_pages.py origin/main     # what is dark on the live site

The publish gate fails closed: a held file stays in the public repo and its
page stops existing, and the cards do not show the flags (#562). Nothing on
the site, in a build log or in a green test says a page has gone dark, so
counting is the only thing that does (PIPELINE.md §5).

It reads `_food_recipes/` and `_cocktail_recipes/` from the working tree, or
from the ref given, through git, and writes nothing. On a feature branch the
two differ, and the question is usually about what is live: run
`sh scripts/git-fetch-main.sh` before asking about `origin/main`, or it
answers about a stale main.

Exit status is 0 whether or not anything is dark: a held page is usually
deliberate. Use it before opening a `blocked-on-helen` batch issue
(`scripts/needs_helen.py`), and after a promotion.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# `rewritten` is a leg for drinks only (#1137, MANUAL §9.1.1); food has two.
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
