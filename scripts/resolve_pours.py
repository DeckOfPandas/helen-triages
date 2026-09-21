#!/usr/bin/env python3
"""Resolve what `bottles.yml` and `ingredients.yml` settle outright, and PROPOSE
nothing else.

    python3 scripts/resolve_pours.py                 # report, write nothing
    python3 scripts/resolve_pours.py --apply         # write the resolutions
    python3 scripts/resolve_pours.py --only rum-cow  # one drink

WHY THIS EXISTS. Of 77 `QQ` notes across both drafts collections, 42 -- 55% --
ask Helen either "which category is this?" or "which bottle is this?". Both are
dictionary reads when the source names something the repo declares, and both
were being done BY HAND, from recall, one drink at a time. The batch of
2026-09-20 resolved nine bottles that way (Gosling's, Smith & Cross, Suze,
Fernet Branca, Angostura, Cointreau, Hayman's London Dry, Monin Pure Cane
Sugar, El Dorado 5 Year Old). Nine correct answers looked up by a model that
could equally have produced nine confident wrong ones.

HELEN'S RULE, 2026-09-21, IS THE WHOLE SPECIFICATION:

    "If the source says 'Gosling's' then the correct thing for Claude to do is
     give 'moderately aged rum, character: blackstrap'. But if a recipe gives
     'blackstrap' Claude shouldn't suggest anything."

So there are exactly three outcomes for a pour whose `generic` is still a QQ:

  TIER 1  the source's words name a DECLARED BOTTLE
          -> write `generic` and `suggestion` from bottles.yml. A dictionary
             read; no judgement; the QQ goes.
  TIER 2  the source's words ARE a declared generic, exactly
          -> write `generic`. Also a dictionary read.
  TIER 3  anything else
          -> leave `generic: "QQ <the source's words>"` exactly as it is.

AND THE ONE INFERENCE IT WILL MAKE, ONLY AS A PROPOSAL. `bottles.yml` has no
character column, deliberately -- its own note against Gosling's Black Seal says
the bottle is "reached for FOR its blackstrap, which is a `character` on the
recipe and never a generic". So resolving a bottle gives a generic and a
suggestion and NO character, and Helen's 2026-09-14 ruling says why: "We don't
name characters on bottles. We name characters on recipe lines ... having a
character is only in a context." Where a resolved bottle has a character
recorded in `bottle_characters` below, this writes `character_claude` -- a
PROPOSAL, beside the pour, for her to accept or reject. Never `character`.

WHAT IT WILL NEVER DO. It will not match loosely, stem, fuzzy-match or guess.
Every lookup is an exact read of a folded string against a declared name or
alias. "blackstrap rum" names no bottle and is not a declared generic, so it is
Tier 3 and this script leaves it alone -- which is the case Helen raised, and
the reason the matching is exact rather than clever.

REPORTS BY DEFAULT, exactly as scripts/tidy_drafts.py does, so the resolutions
can be read before they are written.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys
import unicodedata

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "_data" / "cocktails"
DRAFTS = ROOT / "_cocktail_drafts"

FRONT_MATTER = re.compile(r"\A(---\s*\n)(.*?\n)(---\s*\n)", re.S)

# A pour's `generic` line, quoted, at the indent an ingredient entry uses.
GENERIC_LINE = re.compile(r'^(?P<indent>\s*)generic:\s*"QQ (?P<words>.+)"\s*$')

# The characters a BOTTLE is reached for, which bottles.yml deliberately does
# not record. Proposals only -- see the module docstring. Keep this short: a
# character is a property of a RECIPE's use of a bottle, so an entry here is
# only ever "this is usually why", never "this is what it is".
BOTTLE_CHARACTERS = {
    "gosling's black seal": ["blackstrap"],
}


def fold(text: str) -> str:
    """Lowercase, accents flattened, runs of space collapsed."""
    plain = unicodedata.normalize("NFKD", str(text))
    plain = "".join(c for c in plain if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", plain).strip().lower()


def _data(name: str) -> dict:
    return yaml.safe_load((DATA / name).read_text(encoding="utf-8")) or {}


def bottle_index() -> dict:
    """Every declared bottle NAME and ALIAS -> (canonical name, its generic).

    `not_reached_for` is deliberately absent. Those are bottles Helen has ruled
    she does not buy, so resolving a pour onto one would be proposing a drink
    she cannot make -- Ron del Barrilito Three Stars is the live case, named by
    `away-colour` and sitting on that list.
    """
    out = {}
    for name, entry in (_data("bottles.yml").get("bottles") or {}).items():
        if not isinstance(entry, dict) or not entry.get("generic"):
            continue
        out[fold(name)] = (name, entry["generic"])
        for alias in (entry.get("aliases") or []):
            out[fold(alias)] = (name, entry["generic"])
    return out


def declared_generics() -> dict:
    """Folded generic -> the generic as the vocabulary spells it."""
    sys.path.insert(0, str(ROOT / "tests"))
    from test_cocktails import NOT_GENERIC_LISTS, _is_character_list

    vocab = _data("ingredients.yml")
    reserved = set(vocab.get("hers_to_apply") or {})
    out = {}
    for key, value in vocab.items():
        if (key in NOT_GENERIC_LISTS or _is_character_list(key)
                or key.startswith("retired_") or not isinstance(value, list)):
            continue
        for member in value:
            if member not in reserved:
                out[fold(member)] = member
    return out


def resolve(words: str, bottles: dict, generics: dict) -> dict | None:
    """Tier 1, Tier 2, or None for Tier 3. Exact reads only."""
    key = fold(words)
    if key in bottles:
        name, generic = bottles[key]
        got = {"tier": 1, "generic": generic, "suggestion": [name]}
        character = BOTTLE_CHARACTERS.get(fold(name))
        if character:
            got["character_claude"] = character
        return got
    if key in generics:
        return {"tier": 2, "generic": generics[key], "suggestion": []}
    return None


def rewrite(text: str, found: list) -> str:
    """Replace each resolved `generic:` line, and the `suggestion:` under it.

    TEXTUAL, NOT A YAML ROUND TRIP -- the same reason scripts/needs_helen.py
    edits its one line by hand: a round trip loses comment placement and key
    order, and a drafts file is something Helen reads.
    """
    lines = text.split("\n")
    for hit in sorted(found, key=lambda h: -h["line"]):
        i = hit["line"]
        indent = hit["indent"]
        block = [f'{indent}generic: "{hit["generic"]}"']
        if hit.get("character_claude"):
            joined = ", ".join(f'"{c}"' for c in hit["character_claude"])
            block.append(f"{indent}character_claude: [{joined}]")
            # THE PROPOSAL NEEDS AN OPEN QUESTION TO SIT BESIDE. Tier 1 answers
            # the generic outright, so no QQ survives there -- and a `_claude`
            # key on a pour with nothing open is refused by
            # `test_a_claude_proposal_only_sits_beside_an_open_question`.
            # The question this pour still has is the character, so it says so.
            words = ", ".join(hit["character_claude"])
            block.append(
                f'{indent}note: "QQ - {hit["suggestion"][0]} is usually '
                f'reached for FOR its {words}, so `character_claude` proposes '
                f'it. A character is what THIS recipe wants from the pour, '
                f'which no dictionary knows -- accept it or delete it."')
        # The `suggestion:` belonging to this pour, if the next lines carry one.
        end = i + 1
        replaced_suggestion = False
        while end < len(lines) and lines[end].startswith(indent) \
                and not lines[end].strip().startswith("- "):
            if re.match(rf"^{re.escape(indent)}suggestion:", lines[end]):
                joined = ", ".join(f'"{s}"' for s in hit["suggestion"])
                block.append(f"{indent}suggestion: [{joined}]")
                replaced_suggestion = True
                end += 1
                break
            end += 1
        if not replaced_suggestion:
            joined = ", ".join(f'"{s}"' for s in hit["suggestion"])
            block.append(f"{indent}suggestion: [{joined}]")
            end = i + 1
        lines[i:end] = block
    return "\n".join(lines)


def scan(path: pathlib.Path, bottles: dict, generics: dict) -> tuple[list, list]:
    text = path.read_text(encoding="utf-8")
    m = FRONT_MATTER.match(text)
    if not m:
        return [], []
    found, left = [], []
    for n, line in enumerate(text.split("\n")):
        hit = GENERIC_LINE.match(line)
        if not hit:
            continue
        words = hit.group("words")
        got = resolve(words, bottles, generics)
        if got:
            got.update(line=n, indent=hit.group("indent"), words=words)
            found.append(got)
        else:
            left.append(words)
    return found, left


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--apply", action="store_true",
                    help="write the resolutions; without it, only report")
    ap.add_argument("--only", help="one drink's slug")
    args = ap.parse_args(argv)

    if not DRAFTS.is_dir():
        print(f"{DRAFTS.name}/ is not here -- clone it first "
              f"(CLAUDE.md, Normal workflow).")
        return 2

    bottles, generics = bottle_index(), declared_generics()
    paths = sorted(DRAFTS.rglob("*.md"))
    if args.only:
        paths = [p for p in paths if p.stem == args.only]
        if not paths:
            print(f"no draft called {args.only!r}")
            return 2

    resolved = unresolved = touched = 0
    for path in paths:
        if path.name == "README.md":
            continue
        found, left = scan(path, bottles, generics)
        if not found and not left:
            continue
        print(f"\n{path.relative_to(DRAFTS)}")
        for hit in found:
            print(f"  TIER {hit['tier']}  {hit['words']!r}")
            print(f"       -> generic: {hit['generic']!r}")
            if hit["suggestion"]:
                print(f"          suggestion: {hit['suggestion']}")
            if hit.get("character_claude"):
                print(f"          character_claude: {hit['character_claude']}"
                      f"   (a PROPOSAL -- bottles.yml records no character)")
        for words in left:
            print(f"  TIER 3  {words!r}  -- left alone, this one is Helen's")
        resolved += len(found)
        unresolved += len(left)
        if args.apply and found:
            path.write_text(rewrite(path.read_text(encoding="utf-8"), found),
                            encoding="utf-8")
            touched += 1

    print(f"\n{resolved} pour(s) the dictionaries settle, "
          f"{unresolved} left for Helen.")
    if args.apply:
        print(f"Written to {touched} file(s). Re-derive moods: "
              f"python3 scripts/derive_cocktail_moods.py --write")
    elif resolved:
        print("Nothing was written. Re-run with --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
