#!/usr/bin/env python3
"""Every slug-keyed entry in the PUBLIC data names a drink that exists -- #1106.

    python3 scripts/check_slug_keys.py

THE MISTAKE THIS CATCHES, AND WHY IT IS FOUND TOO LATE TODAY. `mood_include`
and `mood_exclude` live in the PUBLIC `_data/cocktails/taxonomy.yml` and are
keyed by drink slug -- but most of the drinks they name are DRAFTS, which live
in a separate private repo. So the only checkout that can tell a correction
naming a real draft from one naming nothing at all is a checkout with the
drafts clone in it, and CI has never been one. `test_every_mood_correction_is_
reachable_and_needed` knows this and calls `_require_whole_collection`, which
SKIPS. The entry that names nothing therefore merges, and is found afterwards.

#855 recorded the ordering trap that produces one: a drink is promoted or
renamed on a private branch, the public correction keyed by its old slug merges
first, and nothing anywhere can see the mismatch until both halves are on one
machine. This is #855's option 3 -- the check itself, run before the merge, on
the machine that has both.

IT SKIPS RATHER THAN PASSES WITH NO DRAFTS CLONE, and says so in as many words.
A green line that verified nothing is the failure mode this whole script exists
to remove, so the exit code is 2 for "checked nothing", never 0. Every worktree
starts without the clone (MANUAL §9.1 has the command); this is not an error,
it is simply not an answer.

DISCOVERY, NOT A HARDCODED LIST, for everything past the two declared
registries. Any mapping anywhere in `_data/cocktails/` whose keys name real
drinks is treated as slug-keyed and checked, and reported as newly found so it
can be declared. A hardcoded list is exactly how `mood_ingredients` came to
hold 34 strings naming nothing (#452): the list and the data drift, and the
list is the half nobody re-reads.
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

    The path NEVER includes the filename, which is carried separately: a
    filename has a dot in it, and splitting one back off a joined string is how
    the first draft of this reported `yml.mood_include` as an undeclared
    registry and then failed to match it against DECLARED.
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
