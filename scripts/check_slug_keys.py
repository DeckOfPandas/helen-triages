#!/usr/bin/env python3
"""Every slug-keyed entry in the PUBLIC data names a drink that exists -- #1106.

    python3 scripts/check_slug_keys.py

`mood_include` and `mood_exclude` in the public `_data/cocktails/taxonomy.yml`
are keyed by drink slug, and most of the drinks they name are drafts in the
private repo. Only a checkout with the drafts clone can tell an entry naming a
real draft from one naming nothing, and CI is not one: there
`test_every_mood_correction_is_reachable_and_needed` skips. So a drink renamed
or promoted on a private branch can leave a public entry keyed by its old slug
(#855). Run this before the merge, on a machine that has both.

Reads every `_data/cocktails/*.yml`, `_cocktail_recipes/` and
`_cocktail_drafts/`; writes nothing. Exit 0 when every entry resolves, 1 when
one names no drink, 2 when it checked nothing: with no drafts clone (MANUAL
§9.1) it skips and says so, and never passes.

Past the two declared registries it discovers: any mapping whose keys name
real drinks is treated as slug-keyed, checked, and reported so that it can be
added to DECLARED.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "_data" / "cocktails"
PUBLISHED = ROOT / "_cocktail_recipes"
DRAFTS = ROOT / "_cocktail_drafts"

SKIPPED = 2

# The registries that are slug-keyed BY DESIGN. Checked even when empty, so a
# registry emptied by a rename still reports rather than vanishing from the
# discovery pass along with its entries.
DECLARED = [
    ("taxonomy.yml", "mood_include"),
    ("taxonomy.yml", "mood_exclude"),
]


def collection_slugs(root):
    return {p.stem for p in root.rglob("*.md")} if root.is_dir() else set()


def mappings(node, path=""):
    """Every (dotted key path, mapping) in a loaded YAML document.

    The path never includes the filename, which is carried separately: a
    filename has a dot in it and cannot be split back off a joined string.
    """
    if isinstance(node, dict):
        if path:
            yield path, node
        for key, value in node.items():
            yield from mappings(value, f"{path}.{key}" if path else str(key))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from mappings(value, f"{path}[{i}]")


def main() -> int:
    published = collection_slugs(PUBLISHED)
    drafts = collection_slugs(DRAFTS)

    if not DRAFTS.is_dir():
        print("SKIPPED: no _cocktail_drafts/ clone, so a slug naming a real "
              "draft cannot be told from one naming nothing.")
        print("         This check verified NOTHING. Clone the drafts repo "
              "(MANUAL §9.1) and run it again before merging:")
        print("         sh scripts/git-clone-agent.sh "
              "helen-triages-cocktails-private _cocktail_drafts")
        return SKIPPED

    if not published:
        print("SKIPPED: _cocktail_recipes/ holds no drinks, so half the "
              "corpus is missing and this check verified NOTHING.")
        return SKIPPED

    known = published | drafts
    documents = {}
    for path in sorted(DATA.glob("*.yml")):
        documents[path.name] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    registries = {}          # (filename, dotted key path) -> the mapping
    for filename, document in documents.items():
        for dotted, mapping in mappings(document):
            keys = [k for k in mapping if isinstance(k, str)]
            if keys and any(k in known for k in keys):
                registries[(filename, dotted)] = mapping

    for filename, key in DECLARED:
        mapping = (documents.get(filename) or {}).get(key)
        if isinstance(mapping, dict):
            registries[(filename, key)] = mapping
        elif mapping is None:
            print(f"note: {filename} has no `{key}:` -- declared here and "
                  f"absent in the data. Renamed, or deleted?")

    undeclared = sorted(set(registries) - set(DECLARED))
    if undeclared:
        print("Slug-keyed mapping(s) not in this script's DECLARED list:")
        for filename, key in undeclared:
            print(f"  {filename}: {key}")
        print("  -- checked anyway. Add each to DECLARED so it is still "
              "checked on the day every one of its entries goes stale.\n")

    unresolved = []
    checked = 0
    for (filename, key), mapping in sorted(registries.items()):
        for slug in mapping:
            if not isinstance(slug, str):
                continue
            checked += 1
            if slug not in known:
                unresolved.append(f"{filename}: {key}.{slug}")

    print(f"{checked} slug-keyed entr(ies) across {len(registries)} registr(ies), "
          f"against {len(published)} published and {len(drafts)} draft drinks.")

    if unresolved:
        print("\nEntr(ies) naming no drink in EITHER collection:\n  "
              + "\n  ".join(unresolved))
        print("\nEach is keyed by a drink slug and no such drink exists here. "
              "The usual cause is #855's ordering trap: the drink was renamed "
              "or promoted on a private branch and this public entry still "
              "names the old slug. Fetch the drafts clone first "
              "(`sh scripts/git-fetch-agent.sh _cocktail_drafts "
              "helen-triages-cocktails-private`) -- a stale clone reports the "
              "same thing. If the drink is genuinely gone, delete the entry.")
        return 1

    print("Every slug-keyed entry resolves.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
