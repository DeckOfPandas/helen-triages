#!/usr/bin/env python3
"""Rank recipes by how much their ingredient order seems to disagree with
the order the method actually calls for them (GitHub issue #68).

WHAT THIS IS: a DISCOVERY aid for finding recipes worth a human read, not
a source of truth. Two rounds of trying to make this fully automated
(a real test, or an auto-fix) surfaced genuine word-collision bugs --
"chicken breast" and "chicken stock" both match on "chicken", so the
matcher attributes the wrong method step to the wrong ingredient;
"onion" inside a flavourings item's own description ("onion powder")
collides with an unrelated onion ingredient earlier in the list. Matching
free-form ingredient names against free-form method prose is inherently
this fuzzy. See the commit that added test_ingredient_group_order_matches_
title in tests/test_taxonomy.py (GROUP-level ordering, a much safer
suffix-match against the title) for why that test exists instead of an
item-level one.

HOW TO USE IT: run it, read the ranked output, then for each candidate
worth a look, open the actual recipe file and read the actual method
text yourself before touching anything. Never move an ingredient because
this script said so -- only because you (or a human reading the method)
confirmed it. Many high-ranked "inversions" turn out to be one real fix
plus several word-collision artefacts once you actually read the recipe.

    python3 scripts/find_ingredient_order_candidates.py
    python3 scripts/find_ingredient_order_candidates.py --limit 30
"""
from __future__ import annotations

import argparse
import glob
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

# Words that describe an ingredient (size, prep, quality) but never appear
# as the word actually used to refer to it in method prose -- stripping
# these before matching cuts a lot of noise. Not exhaustive; add to it as
# you find more.
ADJ_STOP = {
    "large", "medium", "small", "fresh", "dried", "ground", "boneless",
    "skinless", "ripe", "finely", "roughly", "thinly", "plain", "self",
    "raising", "free", "range", "organic", "good", "quality", "extra",
    "virgin", "softened", "room", "temperature", "heaped", "level",
    "rounded", "generous", "scant", "chopped", "sliced", "diced",
    "crushed", "peeled", "zested", "juiced", "whole", "half",
}


def candidate_words(item_text: str) -> list[str]:
    """Significant words from an ingredient's name, up to the first comma."""
    head = re.split(r",", item_text)[0].strip()
    words = re.findall(r"[a-zA-Z']+", head.lower())
    return [w for w in words if w not in ADJ_STOP and len(w) > 2]


def word_variants(word: str) -> set[str]:
    """Crude singular/plural pair -- "onion" needs to match "onions" too."""
    if word.endswith("s") and not word.endswith("ss"):
        return {word, word[:-1]}
    return {word, word + "s"}


def first_mention(method_text: str, item_text: str) -> int | None:
    """Earliest position any candidate word from item_text appears in
    method_text, word-boundary matched. None if nothing matched at all --
    common and NOT a bug: seasoning-to-taste items, generic "flavourings",
    and cooking fats are often never named again after the ingredient list.
    """
    best = None
    for word in candidate_words(item_text):
        for variant in word_variants(word):
            m = re.search(rf"\b{re.escape(variant)}\b", method_text)
            if m and (best is None or m.start() < best):
                best = m.start()
    return best


def method_text_for_group(fm: dict, group_index: int) -> str:
    """The method text to check a given ingredient group against -- its
    matching method_groups entry by index if the recipe has named method
    groups, else the whole flat method (best effort; group/method-group
    indices aren't guaranteed to line up 1:1 for every recipe shape).
    """
    method_groups = fm.get("method_groups")
    if method_groups and group_index < len(method_groups):
        steps = method_groups[group_index].get("steps") or []
    else:
        steps = fm.get("method") or []
    parts = [(s.get("step") if isinstance(s, dict) else s) or "" for s in steps]
    return " ".join(parts).lower()


def find_candidates(recipes_dir: Path):
    results = []
    for path in sorted(glob.glob(str(recipes_dir / "*.md"))):
        text = Path(path).read_text(encoding="utf-8")
        parts = text.split("---", 2)
        if len(parts) < 3:
            continue
        try:
            fm = yaml.safe_load(parts[1])
        except yaml.YAMLError:
            continue
        if not fm:
            continue

        for group_index, group in enumerate(fm.get("ingredient_groups") or []):
            items = [it for it in (group.get("items") or []) if isinstance(it, dict) and it.get("item")]
            if len(items) < 3:
                continue
            method_text = method_text_for_group(fm, group_index)
            if not method_text.strip():
                continue

            positions = [first_mention(method_text, it["item"]) for it in items]
            found = [(i, p) for i, p in enumerate(positions) if p is not None]
            inversions = sum(
                1
                for a in range(len(found))
                for b in range(a + 1, len(found))
                if found[a][1] > found[b][1]
            )
            if inversions > 0:
                slug = Path(path).stem
                results.append((inversions, slug, group_index, items, positions))

    results.sort(key=lambda r: -r[0])
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--limit", type=int, default=20, help="how many ranked candidates to print")
    parser.add_argument("--recipes-dir", default=str(ROOT / "_food_recipes"))
    args = parser.parse_args()

    results = find_candidates(Path(args.recipes_dir))
    if not results:
        print("No candidates found.")
        return

    for inversions, slug, group_index, items, positions in results[: args.limit]:
        print(f"{inversions} inversions -- {slug}.md group {group_index}")
        for item, pos in zip(items, positions):
            print(f"    {pos!s:>6}  {item['item']}")
        print()


if __name__ == "__main__":
    sys.exit(main())
