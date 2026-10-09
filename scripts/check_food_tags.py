#!/usr/bin/env python3
"""Report food recipes whose tags or star disagree with what the title says.

A REPORT. IT WRITES NOTHING AND IT IS NOT A TEST. Helen, 2026-10-08, asked
whether food tags could be derived the way cocktail moods are. Measured, they
cannot: the tags the data can see are the ones the title already states, and
the judgement tags (`virtuous`, `showstopper`, `festive`...) score at chance.
So there is no food deriver. What the reliable rules ARE good for is a list to
have open while proofreading -- "salad" in the title and no `salad` tag.

The hints are data: `tag_hints` in _data/food/taxonomy.yml, which also records
which ones held up and why the rest are absent.

    python3 scripts/check_food_tags.py              # drafts and published
    python3 scripts/check_food_tags.py --drafts     # drafts only
    python3 scripts/check_food_tags.py --published  # published only

A line here is "worth an eye", not "wrong". A chicken and chorizo stew may be
about the pork, and a savoury recipe with flour and sugar in it is not a bake.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TAXONOMY = ROOT / "_data" / "food" / "taxonomy.yml"
FOLDERS = {"published": ROOT / "_food_recipes", "drafts": ROOT / "_food_drafts"}
FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---", re.S)


def has_word(text, word):
    """`word` as a whole word in `text`, with or without a plural `s`.

    WHOLE WORDS, because `cod` is inside `codswallop` and `ham` inside
    `Graham`; and the plural because a title says "Prawns" as often as
    "Prawn". Case is ignored.
    """
    return re.search(rf"(?<![a-z]){re.escape(word.lower())}s?(?![a-z])",
                     str(text).lower()) is not None


def ingredient_text(fm):
    parts = []
    for group in fm.get("ingredient_groups") or []:
        for item in (group or {}).get("items") or []:
            if isinstance(item, dict):
                parts.append(str(item.get("item", "")))
    return " | ".join(parts)


def prose(fm):
    """Everything the recipe SAYS: tagline, every method step, every note.

    `method_groups` as well as `method` -- about half the collection writes
    its steps in named groups, and a first measurement that read `method`
    alone was blind to all of them.
    """
    parts = [str(fm.get("tagline") or "")]

    def step(s):
        if isinstance(s, dict):
            return f"{s.get('step', '')} {s.get('note', '')}"
        return str(s)

    parts += [step(s) for s in fm.get("method") or []]
    for group in fm.get("method_groups") or []:
        parts += [step(s) for s in (group or {}).get("steps") or []]
    for note in fm.get("notes") or []:
        parts.append(f"{note.get('label', '')} {note.get('text', '')}"
                     if isinstance(note, dict) else str(note))
    return " ".join(parts)


def fires(hint, fm):
    """The words that made this hint fire, or [] if it did not."""
    title = fm.get("title", "")
    found = [w for w in hint.get("title") or [] if has_word(title, w)]
    if found:
        return found
    said = prose(fm).lower()
    found = [p for p in hint.get("text_any") or [] if p.lower() in said]
    if found:
        return found[:1]
    wanted = hint.get("ingredients_all") or []
    text = ingredient_text(fm)
    if wanted and all(has_word(text, w) for w in wanted):
        return list(wanted)
    return []


def check(fm, hints):
    """(missing_tags, star_notes) for one recipe's front matter."""
    tags = [str(t) for t in fm.get("tags") or []]
    missing = []
    for tag, hint in (hints.get("tags") or {}).items():
        words = fires(hint, fm)
        if words and tag not in tags:
            where = ("title says" if hint.get("title")
                     else "the recipe says" if hint.get("text_any")
                     else "ingredients include")
            missing.append((tag, f"{where} {' and '.join(repr(w) if hint.get('text_any') else w for w in words)}"))
    star = str(fm.get("star_ingredient") or "")
    suggested = [(s, fires(h, fm)) for s, h in (hints.get("star_ingredient") or {}).items()]
    suggested = [(s, w) for s, w in suggested if w]
    star_notes = []
    if suggested and star not in [s for s, _w in suggested]:
        for s, words in suggested:
            star_notes.append((s, star, f"title says {' and '.join(words)}"))
    return missing, star_notes


def load(folder):
    for path in sorted(folder.rglob("*.md")):
        match = FRONT_MATTER.match(path.read_text(encoding="utf-8"))
        if not match:
            continue
        try:
            fm = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            continue
        if "ingredient_groups" in fm:
            yield path, fm


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    which = parser.add_mutually_exclusive_group()
    which.add_argument("--drafts", action="store_true", help="drafts only")
    which.add_argument("--published", action="store_true", help="published only")
    args = parser.parse_args(argv)

    hints = (yaml.safe_load(TAXONOMY.read_text(encoding="utf-8")) or {}).get("tag_hints") or {}
    if not hints:
        sys.exit("taxonomy.yml has no `tag_hints`; nothing to check against.")

    names = ["drafts"] if args.drafts else ["published"] if args.published else ["published", "drafts"]
    for name in names:
        folder = FOLDERS[name]
        if not folder.is_dir():
            print(f"\n{name}: {folder.name}/ is absent (a separate private repo; clone it first).")
            continue
        tag_rows, blank_rows, differ_rows, scanned = [], [], [], 0
        for path, fm in load(folder):
            scanned += 1
            missing, star_notes = check(fm, hints)
            for tag, why in missing:
                tag_rows.append((tag, path.stem, why))
            for suggested, star, why in star_notes:
                (blank_rows if not star else differ_rows).append((suggested, path.stem, star, why))
        print(f"\n{'=' * 70}\n{name}: {scanned} recipes")
        print(f"\n  A tag the recipe may be missing ({len(tag_rows)})")
        for tag, slug, why in sorted(tag_rows):
            print(f"    {tag:10s} {slug}  ({why})")
        print(f"\n  No star, and the title names one ({len(blank_rows)})")
        for suggested, slug, _star, why in sorted(blank_rows):
            print(f"    {suggested:10s} {slug}  ({why})")
        print(f"\n  A star, and the title names a different one ({len(differ_rows)})")
        for suggested, slug, star, why in sorted(differ_rows):
            print(f"    {suggested:10s} {slug}  (star is {star}; {why})")
    print("\nNothing was written. Every line is worth an eye, not a verdict.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
