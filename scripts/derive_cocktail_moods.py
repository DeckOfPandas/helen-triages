#!/usr/bin/env python3
"""Derive every drink's `mood` from taxonomy.yml's own definitions -- #452/#292.

WHY THIS SCRIPT EXISTS RATHER THAN THE ONE THAT DID THE JOB BEFORE.
Moods were derived once, on 2026-08-17, by `ingest_from_csv.py` in the private
drafts repo, and written into the 114 files. That script carried nine hardcoded
sets of generic names. The vocabulary then moved -- #335 typed everything, #314
reclassified the rums and made `blackstrap` a character, #561 renamed ten
generics, #568 added five -- and **34 of those strings named nothing at all**.

A set intersection against a renamed string returns empty. So the derivation
kept "working", the stored moods kept looking derived, and `strong brown drink`
quietly stopped being able to fire on any rum. 23 drinks ended up with no mood
at all, including one Helen rates `oh gods yes`.

Three things follow, and all three are the point of this file:

  * THE SETS ARE DATA. `mood_ingredients` in _data/cocktails/taxonomy.yml, with
    `test_every_mood_ingredient_is_declared` requiring each member to be a real
    generic or character. The same drift cannot happen silently again.
  * THE SCRIPT IS COMMITTED, IN THE PUBLIC REPO, so re-running it after a
    vocabulary change is a thing anyone can do rather than a thing one session
    knew how to do.
  * IT DEFAULTS TO A DRY RUN. Writing needs --write. HANDOVER 12: run it once
    and diff before letting it near a tracked file.

DERIVATION IS A STARTING POINT, NOT THE AUTHORITY. A drink Helen thinks is tiki
is tiki whatever the ingredient count says. `mood_overrides` in taxonomy.yml
carries her rulings and always wins; this script never argues with one.

    python3 scripts/derive_cocktail_moods.py            # report differences
    python3 scripts/derive_cocktail_moods.py --write    # apply them
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TAXONOMY = ROOT / "_data" / "cocktails" / "taxonomy.yml"
VOCAB = ROOT / "_data" / "cocktails" / "ingredients.yml"
COLLECTIONS = (ROOT / "_cocktail_recipes", ROOT / "_cocktail_drafts")

FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---", re.S)


# -----------------------------------------------------------------------------
# Quantities. `ml:` was retired in #571, so the volume `strong brown drink`
# needs is derived from `amount` through taxonomy's measures table -- the same
# table and the same rules tests/test_cocktails.py checks every amount against.
# -----------------------------------------------------------------------------
AMOUNT = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(?:/\s*(\d+))?\s*(.*?)\s*$")


def millilitres(amount, measures):
    """Millilitres, or None where the unit is not a volume or cannot be read.

    NONE AND ZERO ARE DIFFERENT ANSWERS and the caller must keep them apart: a
    dash has no volume, which is not the same as contributing nothing to a
    ratio it should not be counted in at all.
    """
    match = AMOUNT.match(str(amount))
    if not match:
        return None
    whole, denominator, rest = match.groups()
    number = float(whole) / (float(denominator) if denominator else 1)
    words = [w for w in rest.lower().split()
             if w not in (measures.get("ignored_words") or [])]
    unit = " ".join(words)
    per_ml = measures.get("per_ml") or {}
    if unit in per_ml:
        return round(number * per_ml[unit], 3)
    return None


# -----------------------------------------------------------------------------
def derive(drink, sets, up_glasses, step_words, families):
    """The mood list for one parsed drink, in taxonomy.yml's own order.

    Every rule here is a transcription of a definition in that file's `moods:`
    block. If the two ever disagree, the prose is the spec and this is the bug.
    """
    def listed(value):
        if value is None:
            return []
        return value if isinstance(value, list) else [value]

    entries = [e for e in (drink.get("ingredients") or []) if isinstance(e, dict)]

    # GENERICS AND CHARACTERS TOGETHER. `blackstrap` is a character since #314
    # and appears in the `tiki` and `loud` sets; reading generics alone was one
    # of the 34 dead strings this script was written to fix.
    present = set()
    for entry in entries:
        present |= {str(g) for g in listed(entry.get("generic"))}
        present |= {str(c) for c in listed(entry.get("character"))}

    def has(name):
        return bool(present & set(sets.get(name) or []))

    def count(name):
        return len(present & set(sets.get(name) or []))

    steps = " ".join(str(s) for s in listed(drink.get("method")))
    glasses = [str(g) for g in listed(drink.get("glass"))]
    n_ingredients = len(entries)

    volumes = {}
    for entry in entries:
        ml = millilitres(entry.get("amount", ""), sets["_measures"])
        if ml is None:
            continue
        for g in listed(entry.get("generic")):
            volumes[str(g)] = volumes.get(str(g), 0) + ml
    total = sum(volumes.values())
    base = sum(v for k, v in volumes.items() if k in families)

    out = []

    # `strong brown drink` -- 60% base spirit by volume, and more aged than
    # clear. KNOWN FLAW, recorded in taxonomy.yml rather than fixed: the
    # fraction counts volume the drink THROWS AWAY, which is why the Sazerac's
    # discarded rinse water drags it to 44%. Rinse-and-discard drinks need an
    # override.
    if total and base / total >= 0.60 and count("aged") >= 2 \
            and count("aged") > count("clear"):
        out.append("strong brown drink")

    if has("clear") and not has("citrus"):
        out.append("clear")

    # `short and sharp` -- the shape does all the work, and there is
    # deliberately no ingredient-count bar: it excluded four drinks Helen would
    # call short and sharp while discriminating nothing.
    if has("citrus") and has("sweet") and (present & families) \
            and any(g in up_glasses for g in glasses):
        out.append("short and sharp")

    if has("fruity"):
        out.append("fruity")
    if has("pudding_flavour"):
        out.append("sugar craving")
    if has("rich"):
        out.append("pudding in a glass")

    # `tiki` -- two markers AND complexity, complexity measured two ways.
    # Helen: tiki is "a complex drink with lots of ingredients and lots of
    # taste layers which is why it's not just a jar full of sugar". Count alone
    # dropped Jungle Bird and Better and Better ("only three ingredients, but
    # they're bonkers"); intensity recovers them and drags in nothing.
    if count("tiki") >= 2 and (n_ingredients >= 6 or count("loud") >= 2):
        out.append("tiki")

    def hits(words):
        """OCCURRENCES, not distinct words -- and the difference is load-bearing.

        `I want to faff` wants two or more faff MOMENTS. Coney Park Swizzle
        swizzles twice and Mastiha Mojito churns twice; counting distinct words
        scores both at one and drops a mood each. Caught by diffing against the
        stored values rather than by reading this function.
        """
        if not words:
            return 0
        pattern = "|".join(re.escape(w) for w in words)
        return len(re.findall(pattern, steps, re.I))

    if hits(step_words.get("ice") or []):
        out.append("ice ice baby")
    if hits(step_words.get("faff") or []) >= 2 or n_ingredients >= 9:
        out.append("I want to faff")
    if not has("citrus"):
        out.append("no juicing")
    if hits(step_words.get("fire") or []):
        out.append("on fire")

    return out


# -----------------------------------------------------------------------------
def load_drinks():
    for root in COLLECTIONS:
        if not root.is_dir():
            continue
        for path in sorted(root.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            match = FRONT_MATTER.match(text)
            if not match:
                continue
            yield path, text, yaml.safe_load(match.group(1)) or {}


def rewrite_mood(text, moods):
    """Replace the `mood:` block, as TEXT.

    NEVER THROUGH A YAML DUMPER. HANDOVER 12: not one of the several hundred
    front-matter edits in this project's history has gone through one, because
    a round trip loses comment placement, key order and quoting style -- right
    in a spot check and wrong across a hundred files.
    """
    lines = text.split("\n")
    start = next((i for i, l in enumerate(lines)
                  if re.match(r"^mood:\s*(\[\s*\])?\s*$", l)), None)
    if start is None:
        return None
    end = start + 1
    while end < len(lines) and lines[end].startswith("  - "):
        end += 1
    block = ["mood: []"] if not moods else ["mood:"] + [f'  - "{m}"' for m in moods]
    return "\n".join(lines[:start] + block + lines[end:])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true",
                        help="apply the derivation (default is a dry run)")
    args = parser.parse_args(argv)

    taxonomy = yaml.safe_load(TAXONOMY.read_text(encoding="utf-8")) or {}
    vocab = yaml.safe_load(VOCAB.read_text(encoding="utf-8")) or {}

    sets = dict(taxonomy.get("mood_ingredients") or {})
    if not sets:
        sys.exit("taxonomy.yml has no `mood_ingredients`; nothing to derive from.")
    sets["_measures"] = vocab.get("measures") or {}
    up_glasses = set(taxonomy.get("mood_up_glasses") or [])
    step_words = taxonomy.get("mood_step_words") or {}
    families = set(vocab.get("family_of") or {})
    include = taxonomy.get("mood_include") or {}
    exclude = taxonomy.get("mood_exclude") or {}
    declared = list((taxonomy.get("moods") or {}))

    drinks = list(load_drinks())
    if not drinks:
        sys.exit("No drinks found. _cocktail_drafts/ is a separate private "
                 "repo and is absent from a fresh worktree -- clone it first.")

    changed, unchanged, written = [], 0, 0
    for path, text, drink in drinks:
        slug = path.stem
        stored = [str(m) for m in (drink.get("mood") or [])]
        derived = derive(drink, sets, up_glasses, step_words, families)
        # HELEN'S CORRECTIONS APPLY ON TOP, never instead: each names the one
        # mood it is about, so the drink keeps benefiting from every later
        # improvement to the rules above.
        corrected = slug in include or slug in exclude
        derived += [m for m in (include.get(slug, {}).get("moods") or [])
                    if m not in derived]
        dropped = set(exclude.get(slug, {}).get("moods") or [])
        derived = [m for m in derived if m not in dropped]
        # taxonomy.yml's own order, so a diff is about membership and never
        # about sequence.
        derived = [m for m in declared if m in derived]
        if derived == stored:
            unchanged += 1
            continue
        changed.append((slug, stored, derived, corrected))
        if args.write:
            new = rewrite_mood(text, derived)
            if new is None:
                print(f"  !! {slug}: no `mood:` key to rewrite", file=sys.stderr)
                continue
            path.write_text(new, encoding="utf-8")
            written += 1

    print(f"{len(drinks)} drinks: {unchanged} already agree, "
          f"{len(changed)} differ\n")
    for slug, stored, derived, is_override in sorted(changed):
        gained = [m for m in derived if m not in stored]
        lost = [m for m in stored if m not in derived]
        mark = " (has a correction)" if is_override else ""
        print(f"  {slug}{mark}")
        if gained:
            print(f"      + {', '.join(gained)}")
        if lost:
            print(f"      - {', '.join(lost)}")
    if args.write:
        print(f"\nwritten: {written}")
    else:
        print("\nDry run. Pass --write to apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
