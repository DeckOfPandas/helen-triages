#!/usr/bin/env python3
"""Take a published recipe or drink off the live site and tell Helen why.

    python3 scripts/needs_helen.py _food_recipes/roast-beef-fillet.md --why "..."
    python3 scripts/needs_helen.py _cocktail_recipes/negroni.md --why "..." --dry-run

PIPELINE.md §5 is the procedure; this is the engine for its middle row. When an
agent edits a published file in any way bigger than a word or a number, the
file's `meta.proofread` goes to `false` in the SAME commit (MANUAL §4.0) -- the
publish gate then hides the page -- and Helen gets an issue labelled
`blocked-on-helen` so she can see that something is waiting on her without
reading a build log. Her idea, 2026-09-14: "when Claude touches a published
file in a way that flips proofread to false, raise a github issue labelled
blocked on Helen so I know I need to do something".

WHAT IT DOES. Flips the flag by a textual edit of the one line (never a YAML
round-trip, which would lose comment placement and key order); finds every
other published page that links to this one, because a demotion turns those
links into 404s in production and she should know the cost is two pages and
not one; writes the issue body to tmp/needs-helen-<slug>.md; and prints the
ONE command that opens the issue. It does not open the issue itself and does
not commit: the wrapper call is allow-listed as a direct command and a commit
is the session's to make with the rest of the change.

ONE ISSUE PER FILE, NOT PER EDIT. Search the tracker for an open
`proofread: <slug>` before running this; a second edit to a file that already
has one is a comment on that issue, not a new one.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COLLECTIONS = {
    "_food_recipes": ("food", "/food/recipes/"),
    "_cocktail_recipes": ("cocktails", "/cocktails/recipes/"),
}
REPO = "DeckOfPandas/helen-triages"
LABEL = "blocked-on-helen"
LOCAL = "http://localhost:4001/helen-triages"

PROOFREAD_TRUE = re.compile(r"^(\s*)proofread:\s*true\s*$", re.M)
PROOFREAD_ANY = re.compile(r"^(\s*)proofread:\s*(true|false)\s*$", re.M)


def flip(path: Path, dry_run: bool) -> str:
    text = path.read_text(encoding="utf-8")
    if not PROOFREAD_ANY.search(text):
        sys.exit(f"{path}: no `proofread:` line in the front matter -- this is "
                 f"not a gated file, or its meta block is not what §4.0 says.")
    if not PROOFREAD_TRUE.search(text):
        return "already false"
    new = PROOFREAD_TRUE.sub(lambda m: f"{m.group(1)}proofread: false", text, count=1)
    if not dry_run:
        path.write_text(new, encoding="utf-8")
    return "flipped"


def linking_pages(collection_dir: Path, slug: str) -> list[str]:
    """Every other file in the collection whose text links to this slug."""
    probe = re.compile(rf"(\.\./|/){re.escape(slug)}/")
    out = []
    for other in sorted(collection_dir.glob("*.md")):
        if other.stem == slug:
            continue
        if probe.search(other.read_text(encoding="utf-8")):
            out.append(other.stem)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("path", help="the published file, under _food_recipes/ or _cocktail_recipes/")
    parser.add_argument("--why", required=True, help="what changed and why, in a sentence or two")
    parser.add_argument("--dry-run", action="store_true", help="flip nothing, write nothing, print what would happen")
    args = parser.parse_args()

    path = (ROOT / args.path).resolve()
    if not path.exists():
        sys.exit(f"{args.path}: no such file")
    collection = path.parent.name
    if collection not in COLLECTIONS:
        sys.exit(f"{args.path}: not under one of {', '.join(COLLECTIONS)} -- only a "
                 f"PUBLISHED file is demoted this way; a draft is not on the site.")
    site, prefix = COLLECTIONS[collection]
    slug = path.stem

    outcome = flip(path, args.dry_run)
    links = linking_pages(path.parent, slug)

    body = [
        f"`{args.path}` was edited by an agent and `proofread` is now `false`, so the "
        f"page is off the live site until you have read it again (PIPELINE.md §5).",
        "",
        "**What changed, and why**",
        "",
        args.why.strip(),
        "",
        "**To read it**",
        "",
        f"{LOCAL}{prefix}{slug}/ on `jekyll-local` (the production build hides it).",
        "",
        "**To close this**",
        "",
        f"Set `proofread: true` in `{args.path}` in a commit whose message says "
        f"`Fixes #<this issue>`; nothing else is needed.",
    ]
    if links:
        body += [
            "",
            "**Other live pages link here and 404 in production until this is back**",
            "",
        ] + [f"- `{prefix}{other}/`" for other in links]
    body_text = "\n".join(body) + "\n"

    out = ROOT / "tmp" / f"needs-helen-{slug}.md"
    if not args.dry_run:
        out.parent.mkdir(exist_ok=True)
        out.write_text(body_text, encoding="utf-8")

    print(f"{args.path}: proofread {outcome}" + (" (dry run)" if args.dry_run else ""))
    if links:
        print(f"linked from: {', '.join(links)}")
    print(f"issue body: {out.relative_to(ROOT)}")
    print("open the issue with:")
    print(f'  sh scripts/gh-agent.sh issue create --repo {REPO} '
          f'--title "proofread: {slug}" --label {LABEL} '
          f'--body-file {out.relative_to(ROOT)}')
    if args.dry_run:
        print("\n--- body ---\n" + body_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
