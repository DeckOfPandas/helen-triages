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
is tiki whatever the ingredient count says. `mood_include` and `mood_exclude` in
taxonomy.yml carry her rulings and always win; this script never argues with one.
Each names the single mood it is about, so a corrected drink still tracks every
later improvement to the rules.

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
# Families that can be a drink's BASE. `fortified`, `amaro` and `herbal` are
# modifiers however aged they are -- a Negroni's sweet vermouth ties with its
# gin for the largest pour, and that tie is the whole reason this list is
# written down rather than assumed.
BASE_FAMILIES = {"rum", "gin", "whisky", "brandy", "agave", "vodka", "aquavit"}

# Never counted toward a drink's volume. Water is a rinse or a dilution and
# never the drink; counting the Sazerac's discarded 60 ml is what used to drag
# it to 44% base spirit and force a hand-correction.
NOT_A_POUR = {"water"}


def spirit_volumes(entries, measures, family_of, whisky):
    """Millilitres per spirit FAMILY, not per ingredient.

    BY FAMILY BECAUSE SINGLE INGREDIENTS TIE. The Sazerac pours equal 20 ml of
    cognac, rye and bourbon, so "the biggest pour" was being decided by which
    key came first in the file -- and 34 of the collection's 114 drinks have
    such a tie. Summed by family, its whisky is 40 ml against cognac's 20 and
    the answer stops depending on YAML ordering.
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
            family = "whisky" if name in whisky else family_of.get(name)
            if family:
                out[family] = out.get(family, 0) + millilitres_
    return out


def _listed(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def hits_in(text, words):
    """OCCURRENCES of any of `words` in `text`, not distinct words matched.

    The difference is load-bearing: `I want to faff` wants two or more faff
    MOMENTS, and Coney Park Swizzle swizzles twice while Mastiha Mojito churns
    twice. Counting distinct words scores both at one and drops a mood each.
    Caught by diffing against the stored values, not by reading the code.
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
    n_ingredients = len(entries)

    # `clear`, `sugar craving`, `tiki` and `aperitivo` ARE NOT DERIVED HERE
    # ANY MORE -- they moved to `moods_by_hand` on 2026-08-30 after every rule
    # was scored against a full pass of Helen's. Their fit was .67, .23, .53
    # and .36; the ones that remain are .73 and above. The sets they used
    # (`tiki`, `loud`, `pudding_flavour`, `aperitivo`) stay in taxonomy.yml:
    # `tiki` and `loud` are still read by nothing, and are kept because they
    # are a good starting list if a rule is ever wanted again.
    out = []

    # `strong brown drink` -- whisky leads; or another aged BASE spirit leads
    # and the drink has not been turned into a sour. Revised 2026-08-30
    # against Helen's own rulings on 23 drinks; see taxonomy.yml for what the
    # previous rule got wrong and why each clause is here.
    by_family = spirit_volumes(entries, sets["_measures"],
                               sets["_family_of"], sets["_whisky"])
    lengthened = has("lengthener")
    churned = bool(hits_in(steps, step_words.get("churned") or []))
    if by_family and not lengthened and not churned and not has("juice"):
        top = max(by_family.values())
        leaders = [f for f, v in by_family.items() if v == top]
        if "whisky" in leaders:
            out.append("strong brown drink")
        else:
            # An aged base spirit may lead instead -- but citrus makes it a
            # sour, which is the line Helen drew between Art de Vivre and the
            # Sidecar.
            aged = set(sets.get("aged") or [])
            aged_leads = any(
                f in BASE_FAMILIES
                and any(g in aged and sets["_family_of"].get(g) == f for g in present)
                for f in leaders)
            if aged_leads and not has("citrus"):
                out.append("strong brown drink")


    # `sharp` -- a base, a citrus, a sweetener, in five ingredients or fewer.
    # The count replaced an UP-GLASS requirement on 2026-08-30: that bar cost
    # drinks their mood for want of a `glass:` value, and five is Helen's own
    # number from this mood's definition. With no bar at all it catches 72 of
    # 114 and narrows nothing.
    # POURED ingredients, not every line. Between the Sheets is rum, cognac,
    # triple sec, lemon and syrup -- a textbook short sour -- plus half a pinch
    # of salt, and the salt took it over five and cost it the mood outright. A
    # dash of bitters or a pinch of seasoning does not make a drink less
    # simple, and this cap is about simplicity.
    #
    # `tiki` and `I want to faff` deliberately keep the FULL count below: there
    # the question is complexity, and three dashes of tiki bitters genuinely
    # are another layer to taste.
    # NOT CHURNED, BUT LENGTH IS FINE. Helen, 2026-08-30: "I think a Tom
    # Collins is sharp, so is Airmail and Green Flash." All three are topped up
    # -- soda for the Collins, champagne for the other two -- and excluding
    # them was the last of the "short" smuggling itself back into a mood no
    # longer called that. Being long does not stop a drink being sharp.
    #
    # Blending and swizzling still do, and that is not the same clause wearing
    # a disguise: those turn a drink into a slushy iced one where the ice is
    # the point, which is what `ice ice baby` is for. Allowing them too takes
    # this from 42 of 114 to 51, at which point it stops narrowing anything.
    poured = sum(1 for e in entries
                 if millilitres(e.get("amount", ""), sets["_measures"]) is not None)
    if has("citrus") and has("sweet") and (present & families) and poured <= 5 \
            and not churned:
        out.append("sharp")

    if has("fruity"):
        out.append("fruity")
    if has("rich"):
        out.append("pudding in a glass")

    # `tiki` -- two markers AND complexity, complexity measured two ways.
    # Helen: tiki is "a complex drink with lots of ingredients and lots of
    # taste layers which is why it's not just a jar full of sugar". Count alone
    # dropped Jungle Bird and Better and Better ("only three ingredients, but
    # they're bonkers"); intensity recovers them and drags in nothing.

    if has("warming"):
        out.append("warming")

    # `up` IS GONE, 2026-08-30, and the reason is worth more than the mood.
    # Read straight off the glass it covered 58 of 114 -- 51% --  and
    # test_no_mood_covers_more_than_half_the_collection refused it: the guard
    # that retired food's `one-pot` at 57% and caught `fruity` at 51% before it
    # was ever written down. Helen had said "I'm not sold on up, let's retain
    # it but with suspicion" an hour earlier, and the suite reached her
    # conclusion independently. Narrowing was not available: the coupe alone is
    # 40 drinks, so any version without it is not `up`.
    if has("warming"):
        out.append("warming")

    # `up` -- PARKED, NOT DELETED, 2026-08-30. Read straight off the glass, and
    # possible only because #491 closed: 15 drinks named none until that day.
    #
    # IT MEASURES 58 OF 114, WHICH IS 51%, and
    # test_no_mood_covers_more_than_half_the_collection refuses it -- the guard
    # that retired food's `one-pot` at 57% and caught `fruity` at 51% before it
    # was ever written down. Helen said "I'm not sold on up. Let's retain it,
    # but with suspicion", and the suite reached her conclusion independently
    # an hour later, which is about as good a reason to believe an instinct as
    # this repo produces.
    #
    # Narrowing it does not help: the coupe alone is 40 drinks, so any version
    # that excludes the coupe is not `up` any more. Half of what she makes is
    # served up, which is a true fact about the collection and exactly why the
    # tag cannot narrow anything.
    #
    # The mood stays DECLARED in taxonomy.yml with zero members, which renders
    # no button (`pudding in a glass` precedent), so reinstating it is
    # uncommenting these two lines. Hers to call.
    #

    # `aperitivo` -- an amaro or an aromatised wine, and not a strong brown
    # drink. That second clause is what keeps a Boulevardier out: same
    # Campari, entirely different moment in the evening.

    if hits_in(steps, step_words.get("ice") or []):
        out.append("ice ice baby")
    if hits_in(steps, step_words.get("faff") or []) >= 2 or n_ingredients >= 9:
        out.append("I want to faff")
    if not has("citrus"):
        out.append("no juicing")
    if hits_in(steps, step_words.get("fire") or []):
        out.append("on fire")

    return out


# -----------------------------------------------------------------------------
def expected_moods(slug, drink, stored, taxonomy, sets,
                   step_words, families):
    """What a drink's `mood` should be: derived, corrected, and hers preserved.

    ONE FUNCTION SO THE SCRIPT AND THE TEST CANNOT DISAGREE. They ran the same
    four steps separately until 2026-08-30, and the copies drifted the first
    time the derivation gained an input.

    HAND-ASSIGNED MOODS ARE PRESERVED, NEVER DERIVED. `moods_by_hand` in
    taxonomy.yml names the ones that describe an occasion rather than the
    liquid -- `nightcap`, `so wrong it's right` -- and no rule produces them.
    Whatever a drink already carries for those is kept as-is; everything else
    is recomputed. So the guarantee that stored moods match their rules stays
    exactly as strong for the moods that HAVE rules, and Helen's own judgement
    is never argued with or overwritten by a re-run.
    """
    by_hand = set(taxonomy.get("moods_by_hand") or [])
    include = (taxonomy.get("mood_include") or {}).get(slug, {}).get("moods") or []
    exclude = set((taxonomy.get("mood_exclude") or {}).get(slug, {}).get("moods") or [])

    moods = derive(drink, sets, step_words, families)
    moods += [m for m in include if m not in moods]
    moods += [m for m in stored if m in by_hand and m not in moods]
    moods = [m for m in moods if m not in exclude]
    # taxonomy.yml's own order, so a diff is about membership, never sequence
    return [m for m in (taxonomy.get("moods") or {}) if m in moods]


def load_sets(taxonomy, vocab):
    """The ingredient sets `derive()` reads, assembled in ONE place.

    Both this script and tests/test_cocktails.py need them, and building them
    twice is how they drift: adding `_family_of` and `_whisky` for the revised
    `strong brown drink` rule broke the tests instantly, because their copy of
    this setup did not know about them. Same argument as `mood_ingredients`
    living in data rather than in a script, one level down.

    NOTE ON THE WORD "REVISED" ABOVE, which is not fussiness. `scripts/` is on
    the render surface that test_invisible_keys_are_really_invisible scans, and
    that guard keeps string literals deliberately, because a string literal is
    exactly how front matter gets read. One of the keys it protects is named
    with an ordinary English past participle meaning "written again". Using that
    word anywhere in this file -- in a docstring, in prose, describing this rule
    rather than any key -- reports the key as rendered and fails the suite.

    It happened twice while this file was being written, the second time in a
    paragraph explaining the first. HANDOVER 12 lists five prior instances of
    prose defeating a source-scanning guard, the very first of which is a hook
    refusing the commit that introduced it. Say "revised".
    """
    sets = dict(taxonomy.get("mood_ingredients") or {})
    sets["_measures"] = vocab.get("measures") or {}
    sets["_family_of"] = vocab.get("family_of") or {}
    sets["_whisky"] = set(vocab.get("whisky_styles") or [])
    return sets


def load_drinks():
    for root in COLLECTIONS:
        if not root.is_dir():
            continue
        # rglob, not glob, since 2026-09-04: Helen stages drinks for publication
        # in _cocktail_drafts/to-promote/, and the suite (which walks the folder
        # recursively) was disputing moods this script could not even see.
        for path in sorted(root.rglob("*.md")):
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
