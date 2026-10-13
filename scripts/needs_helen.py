#!/usr/bin/env python3
"""Take published recipes or drinks off the live site and tell Helen why -- ONE issue for the batch.

    python3 scripts/needs_helen.py _food_recipes/roast-beef-fillet.md \\
        --batch "the en-dash pass" --why "..."

    python3 scripts/needs_helen.py _food_recipes/a.md _cocktail_recipes/b.md \\
        --batch "#711's note sentences" --why "..." --dry-run

The engine for the "anything else" row of PIPELINE.md §5: an agent edit to a
published file that is more than a word, a number or a derived value. Pass
every file being demoted in one call. `--batch` names the cause for the issue
title, `--why` says what changed, `--dry-run` flips and writes nothing.

It validates every path before changing any; sets each `meta.proofread` to
`false` by a textual edit of the one line (a YAML round-trip would lose
comment placement and key order); finds every other file in the collection
that links to each, because those links 404 in production; writes one issue
body with a checklist to tmp/needs-helen-batch.md; and prints the one command
that opens it. It opens no issue and makes no commit.

One issue per batch, never one per file (DECISIONS §4.0). Before opening it,
check the tracker for an open `blocked-on-helen` issue naming one of the
slugs: comment there and leave that slug out of the new body.
`scripts/dark_pages.py` lists everything the gate is hiding.
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
    parser.add_argument("paths", nargs="+",
                        help="the published files, under _food_recipes/ or _cocktail_recipes/")
    parser.add_argument("--batch", required=True,
                        help="a short name for what caused the demotion, for the issue title")
    parser.add_argument("--why", required=True, help="what changed and why, in a sentence or two")
    parser.add_argument("--dry-run", action="store_true",
                        help="flip nothing, write nothing, print what would happen")
    args = parser.parse_args()

    # Resolve and validate EVERY path before flipping any, so a typo in the
    # last argument does not leave half a batch demoted with no issue.
    targets, bad = [], []
    for raw in args.paths:
        path = (ROOT / raw).resolve()
        if not path.exists():
            bad.append(f"{raw}: no such file")
            continue
        if path.parent.name not in COLLECTIONS:
            bad.append(f"{raw}: not under one of {', '.join(COLLECTIONS)} -- only a "
                       f"PUBLISHED file is demoted this way; a draft is not on the site.")
            continue
        targets.append((raw, path))
    if bad:
        sys.exit("refused, nothing flipped:\n  " + "\n  ".join(bad))

    seen = {p.stem for _, p in targets}
    if len(seen) != len(targets):
        sys.exit("refused: the same file is listed twice")

    rows = []
    for raw, path in targets:
        site, prefix = COLLECTIONS[path.parent.name]
        slug = path.stem
        rows.append({
            "raw": raw, "slug": slug, "prefix": prefix,
            "outcome": flip(path, args.dry_run),
            "links": linking_pages(path.parent, slug),
        })

    n = len(rows)
    noun = "page" if n == 1 else "pages"
    body = [
        f"**{n} {noun} {'is' if n == 1 else 'are'} off the live site** until you have "
        f"read {'it' if n == 1 else 'them'} again. An agent edited "
        f"{'it' if n == 1 else 'each of them'} and `proofread` is now `false`, so the "
        f"publish gate hides the {noun} while the {'file stays' if n == 1 else 'files stay'} "
        f"in the repo (PIPELINE.md §5).",
        "",
        "**What changed, and why**",
        "",
        args.why.strip(),
        "",
        f"**The {noun}**, on `jekyll-local` (the production build hides "
        f"{'it' if n == 1 else 'them'}):",
        "",
    ]
    for r in rows:
        body.append(f"- [ ] [`{r['slug']}`]({LOCAL}{r['prefix']}{r['slug']}/)")
        for other in r["links"]:
            body.append(f"      - links from `{r['prefix']}{other}/`, which 404s in "
                        f"production until this is back")

    body += [
        "",
        "**To close this**",
        "",
        f"Set `proofread: true` on each, in a commit whose message says "
        f"`Fixes #<this issue>`. Tick them off here as you go if it helps; the "
        f"issue is done when the list is.",
        "",
        "_Raised as one issue for the whole batch rather than one per page: "
        "one-per-page is what got the agent account flagged as spam on "
        "2026-09-14 (CLAUDE.md)._",
    ]
    body_text = "\n".join(body) + "\n"

    out = ROOT / "tmp" / "needs-helen-batch.md"
    if not args.dry_run:
        out.parent.mkdir(exist_ok=True)
        out.write_text(body_text, encoding="utf-8")

    for r in rows:
        line = f"{r['raw']}: proofread {r['outcome']}"
        if r["links"]:
            line += f"   (linked from {', '.join(r['links'])})"
        print(line + (" (dry run)" if args.dry_run else ""))

    title = f"proofread: {n} {noun} off the site -- {args.batch}"
    print(f"\nissue body: {out.relative_to(ROOT)}")
    print("open ONE issue with:")
    print(f'  sh scripts/gh-agent.sh issue create --repo {REPO} '
          f'--title "{title}" --label {LABEL} '
          f'--body-file {out.relative_to(ROOT)}')
    print("\nfirst check the tracker for an open blocked-on-helen issue naming "
          "any of these slugs -- comment on that one instead of listing it again.")
    if args.dry_run:
        print("\n--- body ---\n" + body_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
