#!/usr/bin/env python3
"""Derive every drink's `mood` from taxonomy.yml's own definitions (#452, #292).

    python3 scripts/derive_cocktail_moods.py            # report differences
    python3 scripts/derive_cocktail_moods.py --write    # apply them

It defaults to a dry run; writing needs `--write`. Run it after a change to
the ingredient vocabulary or to a mood rule, and read the report first.

It reads `_data/cocktails/taxonomy.yml` (`moods`, `mood_ingredients`,
`mood_step_words`, `mood_serve_ice`, `moods_by_hand`, `mood_include`,
`mood_exclude`, `mood_suppresses`), `_data/cocktails/ingredients.yml`
(`measures`, `family_of`, `whisky_styles`) and every `.md` under
`_cocktail_recipes/` and `_cocktail_drafts/`, recursively. With `--write` it
replaces the `mood:` block of each file that differs, as text and never
through a YAML dumper.

The rules:

  - The ingredient sets are data: `mood_ingredients` in taxonomy.yml, each
    member a declared generic or character
    (`test_every_mood_ingredient_is_declared`). A set naming a renamed
    generic matches nothing and raises no error, which is why the names are
    checked.
  - Derivation is a starting point, not the authority. `mood_include` and
    `mood_exclude` carry Helen's per-drink rulings and always win. Each names
    the single mood it is about, so a corrected drink still tracks every
    later change to the rules.
  - A mood in `moods_by_hand` is kept as stored. A rule here may add one
    (`tiki`, `sugar craving`, `on fire`) and never removes one.
  - `mood_suppresses` lets one mood cancel another (#853).
  - `expected_moods` is the one function this script and
    tests/test_cocktails.py both call, so the two cannot disagree. The prose
    definitions in taxonomy.yml's `moods:` block are the spec for `derive`.
"""
from __future__ import annotations

import argparse
import re
import sys
from fractions import Fraction
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TAXONOMY = ROOT / "_data" / "cocktails" / "taxonomy.yml"
VOCAB = ROOT / "_data" / "cocktails" / "ingredients.yml"
COLLECTIONS = (ROOT / "_cocktail_recipes", ROOT / "_cocktail_drafts")

FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---", re.S)


# Quantities. A drink's volume is derived from `amount` through the `measures`
# table in ingredients.yml, the same table tests/test_cocktails.py checks
# every amount against.
AMOUNT = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(?:/\s*(\d+))?\s*(.*?)\s*$")


def millilitres(amount, measures):
    """Millilitres, or None where the unit is not a volume or cannot be read.

    None and zero are different answers and the caller must keep them apart:
    a dash has no volume, which is not the same as contributing nothing.
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


# Families that can be a drink's base. `fortified`, `amaro` and `herbal` are
# modifiers however aged they are: a Negroni's sweet vermouth ties with its
# gin for the largest volume.
BASE_FAMILIES = {"rum", "gin", "whisky", "brandy", "agave", "vodka", "aquavit"}

# Never counted toward a drink's volume. Water is a rinse or a dilution and
# never the drink: the Sazerac's discarded 60 ml would drag its base share down.
NOT_A_POUR = {"water"}

# `no measuring` (#1127): the most multiples of its smallest measure a drink
# may take. Uncapped, the rule covers more than half the collection and
# test_no_mood_covers_more_than_half_the_collection refuses it. taxonomy.yml's
# definition of the mood states the same number in prose; the two must agree.
MAX_POURS = 8

# A 5 ml amount is a bar spoon, not a measure (#1216): `pour_count` sets it
# aside as it does a dash. Exactly 5, not "5 or less": 2.5 ml and 7.5 ml are
# quarter- and half-jiggers.
BARSPOON_ML = 5


QQ_HINT = re.compile(r"^\s*QQ\b\s*(.*?)\s*$")


def qq_hint(name, sets):
    """What a `QQ <hint>` generic is, read through the QQ: `("generic", g)`,
    `("family", f)` or None.

    A QQ is Helen's question about which bottle, not about whether the drink
    has gin in it, so it must not withhold a mood (DECISIONS §9.1.1). Only a
    hint that is exactly a declared spirit generic or a family name (or its
    alias) counts, ignoring case; anything else reads as nothing, as an
    untyped line always has.
    """
    match = QQ_HINT.match(name)
    if not match or not match.group(1):
        return None
    hint = match.group(1).lower()
    for generic in sets["_family_of"]:
        if generic.lower() == hint:
            return ("generic", generic)
    family = sets["_family_aliases"].get(hint, hint)
    if family in sets["_families"]:
        return ("family", family)
    return None


def spirit_volumes(entries, measures, family_of, whisky, sets=None):
    """Millilitres per spirit family, not per ingredient.

    Single ingredients tie (the Sazerac takes equal cognac, rye and bourbon),
    and a tie between ingredients is decided by key order in the file. Summed
    by family, the answer does not depend on YAML ordering.
    """
    out = {}
    for entry in entries:
        millilitres_ = millilitres(entry.get("amount", ""), measures)
        if millilitres_ is None:
            continue
        for generic in _listed(entry.get("generic")):
            name = str(generic)
            if name in NOT_A_POUR:
                continue
            hint = qq_hint(name, sets) if sets else None
            if hint and hint[0] == "family":
                family = hint[1]
            else:
                name = hint[1] if hint else name
                family = "whisky" if name in whisky else family_of.get(name)
            if family:
                out[family] = out.get(family, 0) + millilitres_
    return out


def _listed(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def pour_count(entries, measures):
    """How many multiples of the smallest measured amount the drink takes.

    None where the amounts are not whole-number multiples of the smallest, and
    None where nothing is measured by volume. `no measuring` is the only
    caller (#1127).

    The arithmetic is exact, through `Fraction(str(x))`: `millilitres` returns
    a float, and `is_integer()` over float division would decide a mood by the
    binary expansion of a decimal amount.

    Nothing is set aside by ingredient. `to top`, dashes, drops, pinches and
    `to taste` drop out because `millilitres` returns None for them; prosecco
    written `90 ml` is in the ratio (DECISIONS §9).
    """
    amounts = []
    for entry in entries:
        millilitres_ = millilitres(entry.get("amount", ""), measures)
        if millilitres_ is None or millilitres_ == 0:
            continue
        # A bar spoon; see BARSPOON_ML.
        if millilitres_ == BARSPOON_ML:
            continue
        amounts.append(Fraction(str(millilitres_)))
    if not amounts:
        return None
    multiples = [a / min(amounts) for a in amounts]
    if not all(m.denominator == 1 for m in multiples):
        return None
    return sum(int(m) for m in multiples)


def hits_in(text, words):
    """Occurrences of any of `words` in `text`, not distinct words matched.

    `I want to faff` wants two or more faff moments, and a drink that swizzles
    twice has two.
    """
    if not words:
        return 0
    return len(re.findall("|".join(re.escape(w) for w in words), text, re.I))


def derive(drink, sets, step_words, families):
    """The mood list for one parsed drink, in taxonomy.yml's own order.

    Every rule here is a transcription of a definition in that file's `moods:`
    block. If the two ever disagree, the prose is the spec and this is the bug.
    """
    def listed(value):
        if value is None:
            return []
        return value if isinstance(value, list) else [value]

    # Dilution water is not an ingredient to any rule here (DECISIONS §9). It
    # is dropped once, so no rule below counts it toward a volume, a ratio,
    # the smallest measure or the number of ingredients.
    entries = [e for e in (drink.get("ingredients") or [])
               if isinstance(e, dict)
               and not ({str(g) for g in _listed(e.get("generic"))} & NOT_A_POUR)]

    # Generics and characters together: a mood set may name a character, as
    # `blackstrap` is (#314).
    # A `QQ <hint>` joins as the generic it names; a family hint has no
    # generic to join as, so it is kept apart and stands in for a base spirit.
    present = set()
    qq_families = set()
    for entry in entries:
        for g in listed(entry.get("generic")):
            hint = qq_hint(str(g), sets)
            if hint and hint[0] == "family":
                qq_families.add(hint[1])
            present.add(hint[1] if hint else str(g))
        present |= {str(c) for c in listed(entry.get("character"))}

    def has(name):
        return bool(present & set(sets.get(name) or []))

    def count(name):
        return len(present & set(sets.get(name) or []))

    # A step is a string or a `{step, note}` pair (DECISIONS §9). The rules
    # match words in the build, so a pair gives up both sentences: `str(dict)`
    # would match inside a repr, and skipping the note would change a mood
    # when a remark moves from brackets into `note:`.
    parts = []
    for s in listed(drink.get("method")):
        if isinstance(s, dict):
            parts.append(str(s.get("step", "")))
            parts.append(str(s.get("note", "")))
        else:
            parts.append(str(s))
    steps = " ".join(parts)
    n_ingredients = len(entries)

    out = []

    # `strong brown drink`: whisky leads, or another aged base spirit leads
    # and the drink is not a sour. taxonomy.yml says why each clause is here.
    by_family = spirit_volumes(entries, sets["_measures"],
                               sets["_family_of"], sets["_whisky"], sets)
    lengthened = has("lengthener")
    # `churned` disqualifies a strong brown drink. It is narrower than
    # `mood_serve_ice` on purpose: a big block of ice is how a strong brown
    # drink is served, so `large cube` and `block` are absent here.
    churned = (drink.get("serve") or {}).get("ice") in ("crushed", "cracked", "blended") \
        or bool(hits_in(steps, step_words.get("churned") or []))
    # `slushy` is `sharp`'s own disqualifier and is narrower (DECISIONS §9):
    # it asks for the action that turns a drink into a slushy, where `churned`
    # reads the ice itself. A Moscow Mule on crushed ice is still sharp.
    slushy = (drink.get("serve") or {}).get("ice") == "blended" \
        or bool(hits_in(steps, step_words.get("slushy") or []))
    if by_family and not lengthened and not churned and not has("juice"):
        top = max(by_family.values())
        leaders = [f for f, v in by_family.items() if v == top]
        if "whisky" in leaders:
            out.append("strong brown drink")
        else:
            # An aged base spirit may lead instead, but citrus makes it a sour.
            aged = set(sets.get("aged") or [])
            aged_leads = any(
                f in BASE_FAMILIES
                and any(g in aged and sets["_family_of"].get(g) == f for g in present)
                for f in leaders)
            if aged_leads and not has("citrus"):
                out.append("strong brown drink")


    # `sharp`: a base, a citrus, a sweetener, in five measured ingredients or
    # fewer, and not slushy. The cap is about how simple the build is, so it
    # counts only lines with a volume: a dash of bitters or a pinch of salt
    # does not count, and nor does a shell's rum, which sits on top of the
    # drink (#1256). Being topped up does not stop a drink being sharp.
    # `tiki` and `I want to faff` keep the full count: there the question is
    # complexity, and three dashes of bitters are another layer.
    poured = sum(1 for e in entries
                 if e.get("as") != "shell"
                 and millilitres(e.get("amount", ""), sets["_measures"]) is not None)
    if has("citrus") and has("sweet") and ((present & families) or qq_families) \
            and poured <= 5 \
            and not slushy:
        out.append("sharp")

    if has("fruity"):
        out.append("fruity")
    if has("rich"):
        out.append("pudding in a glass")

    # `tiki`: two markers and at least four ingredients, or one marker in
    # eight or more (DECISIONS §9). The mood stays in `moods_by_hand`, so
    # `expected_moods` keeps whatever a drink carries and this rule only adds:
    # a miss costs nothing, and `mood_exclude` answers a wrong tag.
    n_markers = count("tiki")
    if (n_markers >= 2 and n_ingredients >= 4) \
            or (n_markers >= 1 and n_ingredients >= 8):
        out.append("tiki")

    # `sugar craving`: two tiki markers in a drink of 90 ml or more. It also
    # stays in `moods_by_hand` and only adds. The 90 ml floor keeps short
    # two-marker drinks out.
    measured = [millilitres(e.get("amount", ""), sets["_measures"]) for e in entries]
    if n_markers >= 2 and sum(v for v in measured if v) >= 90:
        out.append("sugar craving")

    if has("warming"):
        out.append("warming")

    # `ice ice baby` reads `serve.ice` against `mood_serve_ice`, not the prose,
    # so rewording a step cannot remove it. `mood_step_words.ice` holds only
    # techniques (a swizzle is the mood's own example). That half decides no
    # drink while every swizzle has a serve value, and is kept because
    # `serve.ice` is optional on a fresh ingest (#1147).
    serve = drink.get("serve") or {}
    served_ice = serve.get("ice")
    if served_ice in set(sets.get("_serve_ice") or []) \
            or hits_in(steps, step_words.get("ice") or []):
        out.append("ice ice baby")
    if hits_in(steps, step_words.get("faff") or []) >= 2 or n_ingredients >= 9:
        out.append("I want to faff")
    if not has("citrus"):
        out.append("no juicing")

    # `no measuring` (#1127) reads amounts: whole multiples of the smallest
    # measure, MAX_POURS of it or fewer. taxonomy.yml says why there is a cap.
    pours = pour_count(entries, sets["_measures"])
    if pours is not None and pours <= MAX_POURS:
        out.append("no measuring")

    if hits_in(steps, step_words.get("fire") or []):
        out.append("on fire")

    return out


# -----------------------------------------------------------------------------
def expected_moods(slug, drink, stored, taxonomy, sets,
                   step_words, families):
    """A drink's `mood`: derived, corrected, hers preserved, and cancelled.

    One function, so the script and tests/test_cocktails.py cannot disagree.

    Whatever a drink already carries from `moods_by_hand` is kept, and
    everything else is recomputed. `mood_suppresses` (#853) runs after the
    hand-assigned moods are folded in, because the mood doing the cancelling
    is one of them, and before `mood_exclude`, the per-drink escape hatch.
    The result is in taxonomy.yml's own order.
    """
    by_hand = set(taxonomy.get("moods_by_hand") or [])
    include = (taxonomy.get("mood_include") or {}).get(slug, {}).get("moods") or []
    exclude = set((taxonomy.get("mood_exclude") or {}).get(slug, {}).get("moods") or [])

    moods = derive(drink, sets, step_words, families)
    moods += [m for m in include if m not in moods]
    moods += [m for m in stored if m in by_hand and m not in moods]

    # After the hand-assigned moods are folded in: the cancelling mood is one
    # of them (#853).
    for winner, losers in (taxonomy.get("mood_suppresses") or {}).items():
        if winner in moods:
            moods = [m for m in moods if m not in losers]

    moods = [m for m in moods if m not in exclude]
    # taxonomy.yml's own order, so a diff is about membership, never sequence
    return [m for m in (taxonomy.get("moods") or {}) if m in moods]


def load_sets(taxonomy, vocab):
    """The ingredient sets `derive()` reads, assembled in one place.

    This script and tests/test_cocktails.py both call it; a second copy of
    this setup would miss the next key `derive()` comes to need.
    """
    sets = dict(taxonomy.get("mood_ingredients") or {})
    sets["_measures"] = vocab.get("measures") or {}
    sets["_family_of"] = vocab.get("family_of") or {}
    sets["_whisky"] = set(vocab.get("whisky_styles") or [])
    # What a `QQ <hint>` may name and still count (`qq_hint`).
    sets["_families"] = set(vocab.get("families") or [])
    sets["_family_aliases"] = vocab.get("family_aliases") or {}
    # The `serve.ice` values that earn `ice ice baby`. serve.yml declares what
    # the field may say, and `test_every_icy_serve_value_is_a_real_one` keeps
    # the two in step.
    sets["_serve_ice"] = list(taxonomy.get("mood_serve_ice") or [])
    return sets


def load_drinks():
    for root in COLLECTIONS:
        if not root.is_dir():
            continue
        # rglob, not glob: drinks are staged in subfolders of
        # _cocktail_drafts/, and the suite walks the folder recursively.
        for path in sorted(root.rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            match = FRONT_MATTER.match(text)
            if not match:
                continue
            yield path, text, yaml.safe_load(match.group(1)) or {}


def rewrite_mood(text, moods):
    """Replace the `mood:` block, as text.

    Never through a YAML dumper: a round trip loses comment placement, key
    order and quoting style.
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

    sets = load_sets(taxonomy, vocab)
    if not taxonomy.get("mood_ingredients"):
        sys.exit("taxonomy.yml has no `mood_ingredients`; nothing to derive from.")
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
        corrected = slug in include or slug in exclude
        derived = expected_moods(slug, drink, stored, taxonomy, sets,
                                 step_words, families)
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
