"""The cocktails collection's own rules. Spec: GitHub issue #322.

`tests/conftest.py` is explicitly the FOOD suite, and says so: the food schema
does not apply to a cocktail. This is the sibling it anticipated.

THE CORPUS IS BOTH COLLECTIONS -- `_cocktail_recipes/` and `_cocktail_drafts/`
-- since 2026-08-29, issue #540. This docstring described the drafts alone until
then, which matched a loader that read the drafts alone, and that was the bug:
the published collection lives in THIS repo and is present in CI, so a promoted
drink was checked by nothing anywhere. See the long note above `_load()`.

WHY THIS FILE SKIPS RATHER THAN FAILS ON AN ABSENT COLLECTION, and why that is
not the vacuity trap tests/test_suite_hygiene.py exists to catch.
`_cocktail_drafts/` is its own private git repo, gitignored from this one, and
nothing is promoted into `_cocktail_recipes/` yet, so on a clean checkout of the
public repo BOTH directories are genuinely ABSENT -- not empty, absent. That is
a legitimate state and the right response is to skip loudly saying so.

What is NOT legitimate is a directory being present and yielding nothing, which
would mean the loader has gone stale. So: skip when NEITHER collection is here,
assert non-empty when one is. "This machine has no drinks" and "I looked and
found nothing" must never produce the same green.

AND A THIRD ANSWER EXISTS, because a PARTIAL corpus is now possible: any claim
of the form "this registry has no dead entries" or "no value covers more than
half the book" is unanswerable when only some drinks are present, since a drink
that is merely absent looks exactly like one that has been fixed. Those live in
their own tests, call `_require_whole_collection`, and are listed in
WHOLE_COLLECTION_ONLY.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

import pytest
import yaml

# Suite marker, so `pytest -m cocktails` can run this half alone.
# tests/test_suite_hygiene.py asserts every module declares one --
# an unmarked file is silently missed by every filtered run.
pytestmark = pytest.mark.cocktails

ROOT = Path(__file__).resolve().parent.parent
RECIPES = ROOT / "_cocktail_recipes"
DRAFTS = ROOT / "_cocktail_drafts"
VOCAB = ROOT / "_data" / "cocktails" / "ingredients.yml"
TAXONOMY = ROOT / "_data" / "cocktails" / "taxonomy.yml"
BOTTLES = ROOT / "_data" / "cocktails" / "bottles.yml"

FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---", re.S)

# Groups in ingredients.yml that are lists of generic VALUES. Everything else at
# the top level is a mapping (family_of, family_less, retired_*) or the family
# list itself, and must not be mistaken for declared generics.
#
# `rum_characters` JOINED THIS SET ON 2026-08-26, AND ITS ABSENCE WAS A REAL
# HOLE. A character is not a generic -- separating them is the entire content of
# #441 -- but this exclusion list named only `families`, so every value in
# `rum_characters` was ALSO a permitted generic. `sherry` and `Spanish-style`
# would have passed silently on any ingredient, and Helen's #314 ruling that
# `blackstrap` is only ever a character could not be enforced while this list
# still declared it a generic. The guard meant to keep the two fields apart was
# quietly putting them back together.
# DERIVED FROM THE SUFFIX SINCE 2026-08-29, not listed by hand. `rum_characters`
# had to be added to this set by hand in the first place, four days after the
# list existed, and `whisky_characters` would have needed the same remembering.
# A `<family>_characters` list is never a generic vocabulary, so the rule can be
# stated once instead of enumerated -- the same reasoning `_retired` already
# uses for its `retired_` prefix.
# `not_on_cards` JOINED THIS SET ON 2026-08-30, AND IT WAS THE SAME HOLE AGAIN.
# It names generics that must never reach a card (#580) -- it REFERS to the
# vocabulary rather than declaring any of it, exactly as `families` does. Left
# out, every word in it became a permitted generic on its own say-so, so a typo
# there would have declared itself valid and `test_every_generic_is_declared`
# would have agreed. Found by breaking the guard that reads this list on purpose
# and watching it stay green, which is the only reason it was found at all.
NOT_GENERIC_LISTS = {"families", "not_on_cards"}


def _is_character_list(key):
    return key.endswith("_characters")


# =============================================================================
# THE CORPUS IS BOTH COLLECTIONS, AND THAT IS THE PROMOTION GATE -- issue #540
# =============================================================================
# This loader read `_cocktail_drafts/` and nothing else until 2026-08-29, and
# #540 records the consequence: the drafts are a separate private repo, CI
# checks out this one alone, so the directory is ALWAYS absent there and 24 of
# this module's tests skipped in every deploy run, reported as passes.
#
# #540 says the mask "comes off the day a cocktail is promoted". IT DID NOT, and
# that is what this change fixes. `_cocktail_recipes/` lives in THIS repo and is
# present in CI -- but the loader globbed the drafts directory, so a promoted
# drink would have been read by nothing, anywhere, ever. Promotion did not lift
# the gate; it moved a drink permanently out from under it.
#
# So the corpus is both roots. The published half is checked wherever it exists,
# including CI. The private half is checked wherever it has been cloned. Helen's
# ruling, 2026-08-29, choosing this over putting the private drinks into a
# runner: gate at promotion, and leave the drafts a local concern.
#
# WHAT THIS DOES NOT DO, said plainly so the green is not over-read: with no
# drink promoted yet, CI still checks nothing, because there is nothing there to
# check. The difference is that this is now a fact about the collection rather
# than about the loader, and it stops being true on the day the first drink
# moves rather than needing anyone to remember.

NO_DRINKS_REASON = (
    "No drinks on this machine to check. `_cocktail_recipes/` holds no promoted "
    "drinks -- it does not exist on disk at all yet, which is deliberate "
    "(HANDOVER_v26.md §9.1) -- and `_cocktail_drafts/` is a separate private "
    "repo (helen-triages-cocktails-private), gitignored here, so a clean "
    "checkout of the public repo legitimately has none either. Clone the drafts "
    "into _cocktail_drafts/ to check those; promote a drink to check it here "
    "AND in CI."
)


def _read(root):
    """Every parseable drink under one collection root. Absent root -> nothing.

    `rglob`, not `glob`. The drafts folder is flat today, but food's loader used
    `glob` and silently stopped seeing seven files the moment a staging pipeline
    appeared under it (HANDOVER §4) -- and those seven were the ones closest to
    promotion. Costs nothing to not repeat.
    """
    out = []
    if not root.is_dir():
        return out
    for path in sorted(root.rglob("*.md")):
        match = FRONT_MATTER.match(path.read_text(encoding="utf-8"))
        if match:
            out.append((path.stem, yaml.safe_load(match.group(1)) or {}))
    return out


def _load():
    """Published drinks plus draft drinks, from whichever roots are present.

    Skips ONLY when neither collection is on disk. A root that IS here and
    yields nothing is the loader-has-gone-stale case and must never be quiet:
    "this machine has no drinks" and "I looked and found nothing" are opposite
    answers, and the whole of tests/test_suite_hygiene.py exists because they
    are easy to conflate into the same green.
    """
    out = _read(RECIPES) + _read(DRAFTS)
    if out:
        return out

    present = [r.name for r in (RECIPES, DRAFTS) if r.is_dir()]
    if not present:
        pytest.skip(NO_DRINKS_REASON)
    assert False, (
        f"{', '.join(present)} exists but yielded no parseable drinks. The "
        f"directory is here, so this is not the absent-collection case -- "
        f"either every file lost its front matter, or this loader has gone "
        f"stale. Do not let it report green."
    )


def _load_published():
    """Only the drinks in `_cocktail_recipes/` -- the ones the world sees.

    A SECOND DOOR, NOT A SECOND GLOB, and the distinction is what keeps #540
    shut. `_load()` above is right for anything true of every drink; a PROMOTION
    GATE is a claim about published drinks alone, and answering it from the
    combined corpus would hold 114 drafts to a rule that is deliberately not
    theirs.

    It skips rather than passing when nothing is promoted. That is the honest
    answer here and not the one `_load()` gives: `_cocktail_recipes/` lives in
    THIS repo, so it is never missing, and an empty one is a true fact about the
    collection rather than a stale scan. Reporting "checked, all fine" over zero
    drinks would be the vacuous green tests/test_suite_hygiene.py exists to
    prevent.
    """
    out = _read(RECIPES)
    if not out:
        pytest.skip(
            "No promoted drinks. `_cocktail_recipes/` is empty, so there is "
            "nothing for a promotion gate to check -- this is a fact about the "
            "collection, not a loader that has gone stale. It starts running "
            "the day the first drink is promoted."
        )
    return out


# =============================================================================
# WHAT A PARTIAL CORPUS CANNOT ANSWER -- the other half of #540
# =============================================================================
# Making the loader read both collections is not the whole fix, and the missing
# half was found by promoting real drinks into a scratch `_cocktail_recipes/`
# with the drafts moved aside -- i.e. by building the CI shape and looking,
# rather than by reasoning about it.
#
# FIVE GUARDS FAILED ON DATA THAT WAS ENTIRELY CORRECT. All five hang on a
# SHRINK-ONLY REGISTRY -- GLASSLESS_ON_2026_08_27, KNOWN_PROSE_SUGGESTIONS,
# `card_name_joins`, methods.yml's proposals -- or on a proportion of the book.
# Each asserts the registry has no dead entries, on the principle that a
# registry with dead entries stops being read.
#
# THAT ASSERTION IS UNANSWERABLE ON A PARTIAL CORPUS, and unanswerable in the
# one direction that matters: a drink that is merely ABSENT looks exactly like
# a drink that has been fixed. In CI the drafts are always absent, so every
# such registry reads as entirely stale. Promotion day would have produced five
# false reds, on `main`, for ever -- not once.
#
# So the two halves are separated. The RATCHET half ("no NEW offender") is a
# per-drink rule, true of any drink on its own, and runs everywhere including
# CI: that is the coverage promotion is supposed to buy. The STALENESS half
# skips with a reason when the whole book is not here.
#
# The alternative considered and rejected: let promotion day produce the five
# failures and re-baseline the registries by hand. It reads as a one-off and is
# not one -- every later promotion re-runs them over a partial corpus too.

WHOLE_COLLECTION_ONLY = {
    "test_the_glassless_list_has_no_stale_entries",
    "test_the_known_prose_suggestion_list_has_no_stale_entries",
    "test_every_card_name_join_is_reachable",
    "test_every_proposal_still_matches_a_real_step",
    "test_no_mood_covers_more_than_half_the_collection",
    # The five COVERAGE claims below -- see _exercised.
    "test_the_character_vocabulary_is_exercised",
    "test_the_bottle_index_is_exercised",
    "test_the_cross_category_check_is_exercised",
    "test_the_syrup_ratio_check_is_exercised",
    "test_the_amount_table_is_exercised",
    # A correction whose drink is merely ABSENT looks exactly like one whose
    # drink is gone -- see _require_whole_collection.
    "test_every_mood_correction_is_reachable_and_needed",
}


def _require_whole_collection(what):
    """Skip unless every drink in the collection is actually on this machine.

    For anything phrased as "this registry has no dead entries" or "no value
    covers more than N% of the book". Both are claims about the WHOLE
    collection, and both quietly invert on a partial one.
    """
    if not DRAFTS.is_dir():
        pytest.skip(
            f"{what} can only be judged against the whole collection, and "
            f"`_cocktail_drafts/` is not on this machine -- it is a separate "
            f"private repo (helen-triages-cocktails-private), so CI never has "
            f"it. On a partial corpus an entry naming an ABSENT drink is "
            f"indistinguishable from one naming a FIXED drink, so this would "
            f"report every entry as stale. The ratchet half of the same rule "
            f"still runs on whatever is here. Clone the drafts to check this."
        )


def _exercised(count, what, implausible):
    """This guard's scan found something to check -- a COVERAGE claim.

    FOUR GUARDS HERE END `assert checked, "...so this check is vacuous"`, and
    they are right to: a scan that came back empty and passed is the one failure
    mode with a green symptom, and tests/test_suite_hygiene.py exists because it
    has bitten six times.

    BUT EVERY ONE OF THEM ARGUES FROM THE SIZE OF THE WHOLE BOOK -- "blackstrap
    alone is on three drinks", "around forty rum pours name a bottle", "that is
    implausible for this collection". On a partial corpus the argument simply
    does not hold: one promoted drink may legitimately contain no rum at all,
    and finding no rum suggestions in it says nothing about `family_of`.

    SO EACH IS SPLIT OUT INTO ITS OWN TEST RATHER THAN SKIPPED IN PLACE, and the
    distinction is the whole point. Skipping the original test to silence the
    coverage claim would take the OFFENDER check down with it -- and that
    offender check is exactly the coverage promotion is meant to buy (#540).
    Split, both halves keep working: the substantive rule runs on every promoted
    drink in CI, and the "is this corpus big enough to exercise me" claim is
    asked only where it can be answered.

    Helen, 2026-08-29, on the four reds this would otherwise have left for
    promotion day: "my preference is not to leave things in a state where tests
    fail and we have to remember why every time we run the suite, but the
    solution to that is not to turn off or otherwise avoid the tests."
    """
    _require_whole_collection(what)
    assert count, f"{what} found nothing to check. {implausible}"


# The loader guards below are the only tests allowed to name the corpus roots
# directly; everything else must go through `_load()`. See
# test_every_drink_reading_test_goes_through_the_loader for why.
LOADER_GUARDS = {
    "test_a_promoted_drink_is_checked_with_no_drafts_present",
    "test_no_drinks_anywhere_skips_rather_than_reporting_green",
    "test_a_present_but_empty_collection_is_never_quiet",
    "test_every_drink_reading_test_goes_through_the_loader",
}


def _drink_file(directory, slug, body="glass:\n  - \"coupe\"\n"):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{slug}.md").write_text(
        f"---\ntitle: \"{slug}\"\n{body}---\n", encoding="utf-8"
    )


def test_a_promoted_drink_is_checked_with_no_drafts_present(tmp_path, monkeypatch):
    """A drink in `_cocktail_recipes/` is read even when the drafts are absent.

    THIS IS THE GATE, and it is the assertion #540 needed. CI has this repo and
    not the private drafts one, so "absent drafts" is the shape every deploy run
    takes. Before this change the loader skipped outright in that state, which
    meant a promoted drink -- the only kind the public ever sees -- was the one
    thing no guard in this module could reach.
    """
    monkeypatch.setattr("test_cocktails.RECIPES", tmp_path / "_cocktail_recipes")
    monkeypatch.setattr("test_cocktails.DRAFTS", tmp_path / "_cocktail_drafts")
    _drink_file(tmp_path / "_cocktail_recipes", "promoted-drink")

    assert [slug for slug, _ in _load()] == ["promoted-drink"], (
        "A promoted drink was not read with the drafts absent. The deploy gate "
        "covers the cocktails collection only through this path."
    )


def test_no_drinks_anywhere_skips_rather_than_reporting_green(tmp_path, monkeypatch):
    """Neither collection on disk is a skip with a reason, never a silent pass.

    The honest answer to "there is nothing here" is to say so in the run. An
    empty corpus that returns quietly is the vacuity failure this repository
    has now been bitten by six times (tests/test_suite_hygiene.py).
    """
    monkeypatch.setattr("test_cocktails.RECIPES", tmp_path / "nope")
    monkeypatch.setattr("test_cocktails.DRAFTS", tmp_path / "also-nope")

    with pytest.raises(pytest.skip.Exception) as caught:
        _load()
    assert "promote a drink" in str(caught.value).lower(), (
        "The skip reason must tell the reader how to make this check real, not "
        "merely that it did not run."
    )


def test_a_present_but_empty_collection_is_never_quiet(tmp_path, monkeypatch):
    """A root that exists and yields nothing FAILS -- it does not skip.

    This is the half that stops the fix above from becoming a new hiding place.
    "The drafts are not cloned here" and "the drafts are cloned and I parsed
    none of them" must not produce the same outcome, or a loader that has gone
    stale looks exactly like a machine without the private repo.
    """
    monkeypatch.setattr("test_cocktails.RECIPES", tmp_path / "nope")
    monkeypatch.setattr("test_cocktails.DRAFTS", tmp_path / "_cocktail_drafts")
    (tmp_path / "_cocktail_drafts").mkdir()

    with pytest.raises(AssertionError) as caught:
        _load()
    assert "gone stale" in str(caught.value), (
        "An empty-but-present collection must fail saying why, not skip."
    )


def test_every_drink_reading_test_goes_through_the_loader():
    """No test may glob the collections itself; `_load()` is the only door.

    ONE DOOR IS WHAT MAKES THE GATE ABOVE WORTH ANYTHING. Every guard in this
    module calls `_load()`, so fixing the loader fixed all 24 at once -- and the
    same property means a single future test globbing `DRAFTS` directly would
    reintroduce exactly the #540 hole for itself, silently, in CI only.

    Generated from the source rather than from a list somebody maintains, which
    is HANDOVER §12's lesson about generating the next check from the other end.
    """
    import ast

    src = Path(__file__).read_text(encoding="utf-8")
    offenders = []
    checked = 0
    for node in ast.walk(ast.parse(src)):
        if not (isinstance(node, ast.FunctionDef) and node.name.startswith("test_")):
            continue
        checked += 1
        if node.name in LOADER_GUARDS:
            continue
        names = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
        named = sorted(names & {"RECIPES", "DRAFTS"})
        if named:
            offenders.append(f"{node.name} names {', '.join(named)} directly")

    assert checked, (
        "No tests found in this module at all -- an empty scan passes while "
        "checking nothing, which is the one failure mode with a green symptom."
    )
    assert not offenders, (
        "Test(s) read the cocktail collections without going through _load():\n  "
        + "\n  ".join(offenders)
        + "\n\nCall _load() instead. It reads BOTH `_cocktail_recipes/` and "
          "`_cocktail_drafts/`, skips only when neither is on disk, and fails "
          "loudly when one is present and empty. A test that globs a root "
          "itself gets none of that, and in CI -- where the drafts are always "
          "absent -- it scans nothing and reports green (issue #540)."
    )

    stale = LOADER_GUARDS - {
        n.name for n in ast.walk(ast.parse(src))
        if isinstance(n, ast.FunctionDef)
    }
    assert not stale, (
        f"LOADER_GUARDS names test(s) that no longer exist: {sorted(stale)}. "
        f"An exemption for a deleted test excuses nothing and hides the next "
        f"real offender behind it."
    )


def test_whole_collection_only_says_what_it_does():
    """Every test in WHOLE_COLLECTION_ONLY actually skips, and nothing else does.

    THE REGISTRY IS ONLY WORTH HAVING IF IT IS TRUE -- the same claim
    test_suite_hygiene.py makes about SKIPS_WITHOUT_DRAFTS, and the same reason.
    A test listed here but not calling `_require_whole_collection` runs in CI
    over a partial corpus and reports a stale registry that is merely absent; a
    test calling it without being listed silently stops covering the collection
    and nobody chose that.

    Asked of the syntax tree, not the text, because a docstring explaining that
    a check needs the whole collection contains every word a grep would look
    for -- HANDOVER §12, five instances of exactly that collision.
    """
    import ast

    src = Path(__file__).read_text(encoding="utf-8")
    listed, calls, seen = WHOLE_COLLECTION_ONLY, set(), set()
    for node in ast.walk(ast.parse(src)):
        if not (isinstance(node, ast.FunctionDef) and node.name.startswith("test_")):
            continue
        seen.add(node.name)
        # BOTH ENTRY POINTS, and the second was found by this guard failing on
        # four tests that plainly did skip. `_exercised` wraps
        # `_require_whole_collection` for the coverage claims, so a scan looking
        # only for the direct call classified all four as "listed but never
        # calls it". A guard that follows exactly one spelling of the thing it
        # checks is HANDOVER §11.0's lesson about the destructive-git hook, in
        # miniature: enumerate how the thing can be SPELLED, not how you happen
        # to have written it today.
        for child in ast.walk(node):
            if (isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
                    and child.func.id in ("_require_whole_collection", "_exercised")):
                calls.add(node.name)

    assert seen, (
        "No tests found in this module at all -- an empty scan passes while "
        "checking nothing."
    )
    assert not (listed - seen), (
        f"WHOLE_COLLECTION_ONLY names test(s) that no longer exist: "
        f"{sorted(listed - seen)}. A registry with dead entries stops being read."
    )
    assert listed == calls, (
        "WHOLE_COLLECTION_ONLY does not match what the tests actually do.\n"
        f"  listed but never calls _require_whole_collection: {sorted(listed - calls)}\n"
        f"  calls it but is not listed: {sorted(calls - listed)}\n\n"
        "Either add `_require_whole_collection(...)` to the test, or add the "
        "test's name to the set. A guard that needs the whole book and does not "
        "say so reports every registry entry as stale the moment the drafts are "
        "absent -- which in CI is always (#540)."
    )


def _vocab():
    if not VOCAB.exists():
        pytest.skip("_data/cocktails/ingredients.yml does not exist yet.")
    return yaml.safe_load(VOCAB.read_text(encoding="utf-8")) or {}


def _retired(vocab):
    """Every retired generic -> its reason, from every `retired_*` mapping.

    DERIVED FROM THE PREFIX, not from a list of block names, and the reason is
    the same one _declared_generics gives for deriving from the file's shape: a
    block added tomorrow is covered tomorrow. This was a hardcoded
    `retired_rum_styles` until 2026-08-26, which meant `retired_gin_styles`
    landed invisible to both retirement checks -- a drink still saying
    `flavoured` would have failed as "undeclared generic", with no reason
    attached, which is the precise failure these blocks exist to prevent.
    """
    out = {}
    for key, value in vocab.items():
        if key.startswith("retired_") and isinstance(value, dict):
            out.update(value)
    return out


def _declared_generics(vocab):
    """Every declared generic value, from every list group in the file.

    Derived from the file's own shape rather than a hardcoded list of group
    names, so a group added tomorrow is covered tomorrow -- the same reasoning
    test_every_drafts_collection_is_gitignored uses for reading _config.yml.
    """
    out = set()
    for key, value in vocab.items():
        if (key in NOT_GENERIC_LISTS or _is_character_list(key)
                or not isinstance(value, list)):
            continue
        out |= set(value)
    return out


def _ingredients():
    """(drink, item, generic) for every ingredient entry, one row per generic.

    `generic` MAY BE A LIST, and that is deliberate rather than sloppy: two
    ingredients in the collection genuinely offer alternatives in one cell --
    "Demerara or dark Muscovado sugar" and "Grand Marnier / Cointreau / Triple
    Sec". Helen, 2026-08-17: "What I have there is fine. I can do what I want on
    the spot." So the item text stays as she wrote it and the generic carries
    both, which is what `glass` and `garnish` already do for the same reason.

    Flattened here so every check below sees one generic at a time and none of
    them has to know about the list form. A list arriving somewhere that expects
    a string is exactly how the `glass` scalar bug would have gone unnoticed.
    """
    out = []
    for slug, fm in _load():
        for item in (fm.get("ingredients") or []):
            if not isinstance(item, dict):
                continue
            name, generic = item.get("item") or "", item.get("generic")
            if isinstance(generic, list):
                out += [(slug, name, g) for g in generic]
            else:
                out.append((slug, name, generic))
    return out


# =============================================================================
# 1 and 2 -- the vocabulary is closed, and retirements bite
# =============================================================================

def test_every_generic_is_declared():
    """A `generic` is a declared value or the literal `QQ`. A third thing is how
    a typo mints a category silently.

    QQ is allowed here and nowhere near a published recipe: these are drafts,
    and 70 of 594 entries genuinely need Helen's call.

    THIS CAUGHT FIVE REAL ONES when it was written -- all in the three
    hand-written schema examples, which predate the vocabulary: `Creole bitters`
    (capitalised), `chartreuse` (which of the two?), `peach liqueur` (the
    collection uses crème de pêche), `rye whiskey` (the style is `rye`) and
    `sugar syrup` (1:1 or 2:1 is the whole distinction).
    """
    vocab = _vocab()
    declared = _declared_generics(vocab)
    assert declared, (
        "_data/cocktails/ingredients.yml declares no generic values at all, so "
        "this check has nothing to enforce. Either the file changed shape or "
        "the groups were renamed -- an empty set would pass everything."
    )
    retired = set(_retired(vocab))
    bad = sorted({
        f"{slug}: {item!r} -> {generic!r}"
        for slug, item, generic in _ingredients()
        if generic and generic != "QQ" and generic not in declared
        and generic not in retired
    })
    assert not bad, (
        "Undeclared generic(s):\n  " + "\n  ".join(bad)
        + "\n\nEither it is a typo, or the value is real and belongs in "
          "_data/cocktails/ingredients.yml. Issue #322 is the spec."
    )


def test_no_drink_uses_a_retired_generic():
    """Retired values fail with their retirement REASON attached.

    Checked separately from "not declared", the same way food's
    test_star_ingredient_is_declared handles retired stars: a value that used to
    mean something must not blend into the generic not-declared pile, where
    nobody learns why it went.
    """
    retired = _retired(_vocab())
    assert retired, (
        "No retired values declared, so this enforces nothing. If the "
        "retirements were reversed, delete this test deliberately."
    )
    bad = [
        f"{slug}: {item!r} -> {generic!r} ({retired[generic]})"
        for slug, item, generic in _ingredients()
        if generic in retired
    ]
    assert not bad, (
        "Retired generic(s) still in use:\n  " + "\n  ".join(bad)
        + "\n\nRe-type against the vocabulary. Which rum a drink wants is "
          "Helen's own knowledge and is not recoverable from the spreadsheet -- "
          "use QQ, do not guess."
    )


# =============================================================================
# 3 -- the family roll-up, which serves search and exclusion (NOT browsing)
# =============================================================================

def test_every_family_is_declared_and_bases_have_one():
    """`family_of` maps base generics to a declared family, and every base
    either has a family or an explicit reason for not having one.

    NOT "every generic has a family" -- that would fail on `lime juice`, and
    correctly so: nobody excludes "all juices". Only BASES roll up. The
    distinction was a real bug in this test's own spec, caught before it was
    written.

    `family_less` is the exemption list, carrying a reason per entry, exactly as
    tests/test_reference_data.py's NO_TEMPERATURE_BECAUSE does -- so "why is
    this not groupable?" is answered in the repo rather than in someone's head.
    """
    vocab = _vocab()
    families = set(vocab.get("families") or [])
    family_of = vocab.get("family_of") or {}
    family_less = vocab.get("family_less") or {}
    declared = _declared_generics(vocab)

    assert families and family_of, "families / family_of are missing or empty."

    unknown_family = sorted({f"{g!r} -> {f!r}" for g, f in family_of.items()
                             if f not in families})
    assert not unknown_family, (
        "family_of points at families that are not declared:\n  "
        + "\n  ".join(unknown_family) + f"\n\nDeclared: {sorted(families)}."
    )

    unknown_generic = sorted(set(family_of) - declared)
    assert not unknown_generic, (
        f"family_of names generics that are not declared anywhere: "
        f"{unknown_generic}. A family mapping for a value nothing can use is "
        f"dead weight -- and probably a typo."
    )

    # Every base style must be groupable or exempted. Bases are the style lists.
    base_groups = ("rum_styles", "rum_untyped", "gin_styles", "whisky_styles",
                   "agave_styles", "brandy_styles", "cane_and_palm_spirits",
                   "other_base_spirits", "herbal_liqueurs", "amari",
                   "fortified_and_aromatised")
    bases = {g for group in base_groups for g in (vocab.get(group) or [])}
    assert bases, "no base groups found -- have they been renamed?"
    orphans = sorted(bases - set(family_of) - set(family_less))
    assert not orphans, (
        f"base generic(s) with no family and no exemption: {orphans}.\n"
        f"Either map them in family_of, or record why not in family_less with a "
        f"reason. An unexplained gap means 'no whisky tonight' silently misses "
        f"a drink."
    )


# =============================================================================
# 4 -- spelling collisions, the food test that actually fires in practice
# =============================================================================

def _fold(text):
    stripped = "".join(c for c in unicodedata.normalize("NFD", text)
                       if not unicodedata.combining(c))
    return stripped.lower()


def test_no_two_generics_differ_only_by_case_or_accent():
    """The cocktails version of test_no_main_ingredient_spelling_collisions.

    That is the food test that fires most often in real use, because two
    spellings of one thing means two filter buttons each holding half the
    drinks -- and the search layer folds accents when matching, so the collision
    is invisible until someone browses the buttons.

    Checked against the DECLARED vocabulary rather than the drinks, because the
    vocabulary is what the buttons are built from.
    """
    vocab = _vocab()
    seen = {}
    collisions = []
    for generic in sorted(_declared_generics(vocab)):
        key = _fold(generic)
        if key in seen and seen[key] != generic:
            collisions.append(f"{seen[key]!r} vs {generic!r}")
        seen[key] = generic
    assert not collisions, (
        "Declared generics differing only by case or accent:\n  "
        + "\n  ".join(collisions)
        + "\n\nPick one spelling. Two spellings of one thing means two buttons "
          "each holding half the drinks."
    )


# =============================================================================
# 5 -- coverage: an untyped ingredient must be VISIBLE, not absent
# =============================================================================

def test_every_ingredient_has_a_generic_or_a_qq():
    """No ingredient may be silently untyped.

    THIS IS THE GAP `Smith & Cross` FELL INTO. Written without the word "rum",
    it matched no pattern, so it got no generic AND no QQ -- invisible to both
    the declared-value check and the retirement check. An absent key reads as
    "nothing to see"; a QQ reads as "not done yet". Only one of those is true.
    """
    missing = sorted({f"{slug}: {item!r}" for slug, item, generic
                      in _ingredients() if item and not generic})
    assert not missing, (
        f"{len(missing)} ingredient(s) carry no `generic` key at all:\n  "
        + "\n  ".join(missing[:15])
        + "\n\nEvery ingredient needs a declared generic or the literal QQ. "
          "Absent is not the same as unfinished."
    )


# =============================================================================
# 5a -- the one generic that cannot stand on its own
# =============================================================================

# Helen, 2026-08-26: "speciality should always carry a character field."
# A pair rather than a bare string so a second such generic is one line, not a
# rewrite -- gin is simply the only family with one today.
GENERICS_REQUIRING_A_CHARACTER = ("speciality",)


def test_speciality_gin_declares_a_character():
    """`speciality` names a gin by what it is NOT (juniper-led) and stops there.

    It replaced `flavoured`, which was retired for covering sloe, rhubarb and
    cucumber alike -- three gins nobody would swap for each other. Renaming it
    fixes the label and none of the underlying problem: the word still doesn't
    say what went in the still. `character` is what carries that, so on this
    generic it is required rather than optional.

    CHARACTER IS FREE TEXT HERE, deliberately, and this test does not check its
    value -- Helen's call, 2026-08-26. Rum's characters close into a list
    because they come from a handful of production traits; a gin's is whatever
    the distiller reached for, and a closed list would mean a vocabulary edit
    per bottle. So: present and non-empty, never a declared member.

    ONE REAL CASE TODAY: Spiced Negroni's Ophir, cardamom / cubeb pepper /
    black pepper. (An earlier version of this docstring claimed the test was
    vacuous -- it was written alongside the retyping that gave it its first
    case, and was wrong the moment it was committed. Corrected 2026-08-26,
    which is exactly the §11.2 failure this repo keeps re-learning: a
    docstring is a claim about the code and rots like any other.)
    """
    bad = []
    for slug, fm in _load():
        for item in (fm.get("ingredients") or []):
            if not isinstance(item, dict):
                continue
            generic = item.get("generic")
            generics = generic if isinstance(generic, list) else [generic]
            if not any(g in GENERICS_REQUIRING_A_CHARACTER for g in generics):
                continue
            character = item.get("character")
            # A bare string is as good as a list -- Liquid iterates either, and
            # `generic`/`suggestion` already accept both shapes for this reason.
            if isinstance(character, str):
                character = [character] if character.strip() else []
            if not character:
                bad.append(f"{slug}: {item.get('item') or '?'!r}")
    assert not bad, (
        f"{len(bad)} ingredient(s) typed as a generic that requires a "
        f"`character`, without one:\n  " + "\n  ".join(bad)
        + "\n\nA `speciality` gin is defined by the botanical it pushes -- "
          "cucumber, rose, rhubarb, lemon. Without that the generic says only "
          "'not a London dry', which is what got `flavoured` retired. Free "
          "text: name the thing, no vocabulary to match."
    )


# =============================================================================
# 6 and 7 -- shape guards on the drinks themselves
# =============================================================================

def test_a_declared_character_vocabulary_is_enforced():
    """A `character` must be declared, for every family that closes its list.

    WAS RUM-ONLY UNTIL 2026-08-29, and generalising it is the point rather than
    a tidy-up. `whisky_characters` arrived with `peated` (#314, Helen: "so
    single malt whisky, character: peated ???"), and a rum-shaped guard would
    have left the new list declared and checked by nothing -- which is EXACTLY
    the failure this test was written for. `rum_characters` sat unchecked for
    four days while `sherry` and `Spanish-style` passed silently as generics.

    NOT EVERY FAMILY, AND THAT ASYMMETRY IS DELIBERATE. Only families that
    DECLARE a `<family>_characters` list are checked. Gin declares none, on
    Helen's explicit call: a rum's character comes from a handful of production
    traits and closes into a list, while a gin's is whatever went in the still,
    so Spiced Negroni's cardamom is correctly undeclared and must not fire here.
    Adding a list is what switches enforcement on, which means the vocabulary
    and its guard can no longer drift apart.

    Family-ness is derived through `family_of`, never pattern-matched on the
    item name -- 61 ingredients in this collection are named only by brand,
    which is the same reason `generic` is stored rather than computed.
    """
    _, bad, declared = _character_scan()
    assert not bad, (
        "Undeclared character(s):\n  " + "\n  ".join(sorted(bad))
        + "\n\nDeclared: "
        + "; ".join(f"{f}={sorted(v)}" for f, v in sorted(declared.items()))
        + ".\nEither it is a typo, or the value is real and belongs in that "
          "family's list. A character is not a generic -- #441 -- but it is "
          "just as much a vocabulary."
    )


def test_the_character_vocabulary_is_exercised():
    """Some ingredient in a closed-character family actually carries one.

    The family lookup is a two-step derivation (generic -> family_of -> family)
    and EITHER step going stale would leave the rule above green while checking
    nothing. Whole-collection only: see `_exercised`.
    """
    checked, _, _ = _character_scan()
    _exercised(
        checked, "the declared-character check",
        "That is implausible for the whole collection -- blackstrap alone is on "
        "three drinks. Either `family_of` no longer maps the rum styles, or a "
        "generic was renamed without this following.")


def _character_scan():
    """(how many characters were checked, offenders, the declared vocabulary).

    ONE SCAN, TWO TESTS. Re-typing the walk into the coverage test would let the
    two drift, and they must agree about what "checked" means or the coverage
    claim stops describing the rule it guards.
    """
    vocab = _vocab()
    family_of = vocab.get("family_of") or {}
    declared = {
        key[: -len("_characters")]: set(value)
        for key, value in vocab.items()
        if _is_character_list(key) and isinstance(value, list) and value
    }
    assert declared, (
        "ingredients.yml declares no `<family>_characters` list at all, so this "
        "check enforces nothing. `rum_characters` at least should be there."
    )

    bad, checked = [], 0
    for slug, fm in _load():
        for item in (fm.get("ingredients") or []):
            if not isinstance(item, dict):
                continue
            generic = item.get("generic")
            generics = generic if isinstance(generic, list) else [generic]
            families = {family_of.get(g) for g in generics} & set(declared)
            if not families:
                continue
            character = item.get("character")
            if not character:
                continue
            permitted = set().union(*(declared[f] for f in families))
            for value in (character if isinstance(character, list) else [character]):
                checked += 1
                if value not in permitted:
                    bad.append(
                        f"{slug}: {item.get('item') or '?'!r} -> {value!r} "
                        f"(family {'/'.join(sorted(families))})"
                    )
    return checked, bad, declared


def test_every_rum_generic_has_a_card_name_and_nothing_else_does():
    """`card_names` covers the rum family exactly -- issue #501.

    The card renders a rum's CATEGORY rather than the source's own words,
    because those words could not be trusted: eight item strings in this
    collection each name two or three different rums, `Overproof Navy rum`
    among them. The substitution is driven by "does this generic have a card
    name", so a rum missing from this map silently falls back to exactly the
    ambiguous item text the map exists to replace -- and nothing on the page
    would look wrong.

    BOTH DIRECTIONS, and the second is the one that catches a rename. A card
    name for a generic that no longer exists is dead weight that reads as
    live coverage; `_declared_generics` cannot see it, because this is a
    mapping rather than a list.
    """
    vocab = _vocab()
    names = vocab.get("card_names") or {}
    family_of = vocab.get("family_of") or {}
    rum_generics = {g for g, fam in family_of.items() if fam == "rum"}
    assert rum_generics, (
        "`family_of` maps no generic to `rum`, so this check has nothing to "
        "enforce. Either the family was renamed or the mapping was dropped."
    )
    missing = sorted(rum_generics - set(names))
    assert not missing, (
        "Rum generic(s) with no card name:\n  " + "\n  ".join(missing)
        + "\n\nA rum without one falls back to `item` on the index, which is "
          "the ambiguous colour vocabulary #314 retired. Add it to "
          "`card_names` in _data/cocktails/ingredients.yml."
    )
    # THE SECOND HALF LOOSENED 2026-08-27, and only by one notch. It used to
    # require the map to be EXACTLY the rum family, which was right while #501
    # scoped card names to rum. Helen then added Ceylon arrack -- "is that a
    # rum? Doesn't matter, the category list should eventually contain
    # everything" -- so the map is growing past rum on purpose. What still bites
    # is a card name for something that is not a declared generic at all, which
    # is the typo case; what no longer bites is deliberate widening.
    declared = _declared_generics(vocab)
    extra = sorted(set(names) - declared)
    assert not extra, (
        "Card name(s) for something that is not a declared generic:\n  "
        + "\n  ".join(extra)
        + "\n\nEither the generic was renamed and this entry did not follow, or "
          "it is a typo. Widening the map beyond rum is fine and expected -- "
          "the value still has to be a real generic from this file."
    )


def test_rum_card_names_are_distinct():
    """No two rums may read the same on a card -- issue #501.

    THIS IS THE WHOLE POINT OF THE MAP, not a tidiness rule. The fault being
    fixed is that `Overproof Navy rum` appeared on three cards meaning three
    different rums. A duplicate card name rebuilds that fault in the very
    mechanism introduced to remove it, and it would look completely fine on
    the page -- two drinks reading "Demerara rum" is only wrong if you know
    one of them is an overproof.

    A COLLAPSE MAY BE DELIBERATE, and then it is declared rather than
    forbidden. Helen collapsed both Jamaicans to `Jamaican rum` on 2026-08-27:
    the funk is the shared trait and the caramel is a nuance of the same rum,
    where both Demeraras and both agricoles keep their own names because proof
    and age change what you are making. So the rule is not "never" but "not by
    accident" -- `card_names_may_collide` carries the reason, the same shape
    `family_less` uses, and an undeclared duplicate still fails.

    THERE IS DELIBERATELY NO LENGTH RULE HERE. An earlier version of this test
    asserted a card name was never longer than the generic it stands for, which
    sounds obvious and was wrong within a day: Helen's names say the spirit word
    out loud wherever the style alone would not read as a rum, so `Demerara,
    overproof` -> `Demerara overproof rum` grows by three characters on purpose.
    Brevity was the means and legibility was the point.
    test_card_lines_do_not_get_longer holds the thing that actually mattered.
    """
    vocab = _vocab()
    names = vocab.get("card_names") or {}
    permitted = vocab.get("card_names_may_collide") or {}
    assert names, (
        "`card_names` is empty, so this check is vacuous."
    )
    seen = {}
    clashes = []
    for generic, name in sorted(names.items()):
        key = name.strip().lower()
        if key in seen and key not in {k.strip().lower() for k in permitted}:
            clashes.append(f"{name!r}: {seen[key]!r} and {generic!r}")
        seen[key] = generic
    assert not clashes, (
        "Two rums share a card name, and the collapse is not declared:\n  "
        + "\n  ".join(clashes)
        + "\n\nThe index would show identical words for rums that are not "
          "interchangeable, which is the exact ambiguity #501 removed. If the "
          "collapse is intended, add the NAME to `card_names_may_collide` "
          "with the reason -- a collapse loses information on the index, so it "
          "should cost a sentence."
    )
    stale = sorted(
        name for name in permitted
        if list(names.values()).count(name) < 2
    )
    assert not stale, (
        "Declared collision(s) that no longer collide:\n  " + "\n  ".join(stale)
        + "\n\nThe names diverged and this permission was left behind, where it "
          "reads as a live decision and would silently bless the NEXT accidental "
          "duplicate on the same name."
    )


def test_showing_categories_still_shortens_the_index():
    """Across the collection, card names must cost less room than items -- #501.

    AGGREGATE, NOT PER-CARD, and the difference is a correction rather than a
    convenience. The first version of this asserted no single card got longer,
    which sounds like the same thing and is not: 19 of the 62 rum-bearing cards
    DO get longer, almost all of them the nine carrying a disjunctive rum, where
    "either would do" spends a whole second name ("lightly aged rum or clear
    blended rum" against an item reading `Light rum`). Those nine are the cards
    where the category is doing the MOST work -- `White rum` concealing a choice
    between a filtered rum and an agricole blanc -- so failing them would have
    been the guard punishing the feature.

    What was actually claimed when this shipped, and what this holds: the index
    as a whole gets shorter. 39 cards shorter, 4 unchanged, 19 longer, median
    -8 characters, and the collection's median card line 98 -> 94. The card body
    clamps at two lines, so length is not cosmetic -- it is how many
    ingredients a reader can see.

    Deliberately loose: it permits any individual name, and fires only if the
    whole set drifts long enough to stop paying for itself.
    """
    vocab = _vocab()
    names = vocab.get("card_names") or {}
    assert names, "`card_names` is empty; nothing to check."
    before_total, after_total, checked = 0, 0, 0
    for slug, fm in _load():
        before, after = [], []
        touched = False
        for item in (fm.get("ingredients") or []):
            if not isinstance(item, dict) or not item.get("generic"):
                continue
            generic = item["generic"]
            generics = generic if isinstance(generic, list) else [generic]
            # THE BASELINE IS THE GENERIC, NOT `item` -- corrected with #544's
            # second move. It was `item` because that is what the card printed
            # when #501 measured this; move 1 changed the fallback to the
            # generic, so "what this card would say without card_names" has
            # been the generic since, and the old baseline was measuring a
            # counterfactual the template can no longer produce. Re-run on the
            # day of the change: the claim holds either way and holds harder on
            # the true baseline -- 8437 -> 7261 against 9956 -> 8960.
            plain = " or ".join(str(g) for g in generics)
            before.append(plain)
            labels = [names[g] for g in generics if g in names]
            if labels and len(labels) == len(generics):
                after.append(" or ".join(labels))
                touched = True
            else:
                after.append(plain)
        if not touched:
            continue
        checked += 1
        before_total += len(" · ".join(before))
        after_total += len(" · ".join(after))
    assert checked, (
        "No drink's card line uses a rum card name, so this check is vacuous. "
        "Either `family_of` no longer maps the rum styles, or the map was "
        "renamed without this following."
    )
    assert after_total <= before_total, (
        f"Showing rum categories now makes the index LONGER: {before_total} -> "
        f"{after_total} characters across {checked} cards "
        f"({after_total - before_total:+}).\n\nThe card body clamps at two "
        f"lines, so this is paid for in ingredients a reader cannot see. Either "
        f"a card name has grown well past the item text it replaces, or a lot "
        f"of rums have become disjunctive at once."
    )


def test_no_card_shows_two_different_rums_under_one_name():
    """One card, one name, one rum -- issue #501.

    TWO DIFFERENT GENERICS, NOT TWO ENTRIES, and the distinction is Helen's,
    2026-08-27: "where a recipe wants more than one kind of the same rum we
    obviously should write the display name twice." A drink calling for two
    pours of the same category genuinely prints its name twice and that is
    correct -- each ingredient entry renders on its own. The failure this
    catches is the opposite one: two ingredients that are NOT the same rum
    arriving at the same words, which is #501's original fault (`Overproof Navy
    rum` meaning three different things) rebuilt inside the fix for it.

    The first version of this test asserted no card repeats a name at all, and
    would have failed a correct drink the day one was written. Vocabulary-wide
    distinctness (above) does not cover this either: a DECLARED collapse is
    permitted there, and this is where that permission gets checked against real
    drinks -- both Jamaicans read `Jamaican rum`, so a drink calling for both
    would say one word for two rums and lose the difference silently.
    """
    vocab = _vocab()
    names = vocab.get("card_names") or {}
    joins = vocab.get("card_name_joins") or {}
    assert names, "`card_names` is empty; nothing to check."
    bad, checked = [], 0
    for slug, fm in _load():
        # card name -> the set of generic-tuples that produced it
        shown = {}
        for item in (fm.get("ingredients") or []):
            # Gated on `generic`, not `item` -- see the note in
            # test_showing_categories_still_shortens_the_index. `item` is being
            # retired (#544) and using it here would silently stop checking
            # every entry that had already lost it.
            if not isinstance(item, dict) or not item.get("generic"):
                continue
            generic = item["generic"]
            generics = generic if isinstance(generic, list) else [generic]
            labels = [names[g] for g in generics if g in names]
            # The template substitutes only when EVERY generic has a card name,
            # so a partial match falls back to the generic and shows no card
            # name.
            if not labels or len(labels) != len(generics):
                continue
            label = " or ".join(labels)
            label = joins.get(label, label)
            shown.setdefault(label, set()).add(tuple(generics))
        checked += 1
        for label, sources in sorted(shown.items()):
            if len(sources) > 1:
                bad.append(
                    f"{slug}: {label!r} <- "
                    + " and ".join(sorted(str(list(s)) for s in sources))
                )
    assert checked, "No drinks loaded, so this check is vacuous."
    assert not bad, (
        "Card(s) showing two different rums under one name:\n  "
        + "\n  ".join(bad)
        + "\n\nA reader cannot tell these apart, and the card is the place the "
          "choice gets made. Either give them distinct card names, or the two "
          "generics are close enough that this drink should not ask for both."
    )


def test_every_card_name_join_is_reachable():
    """A `card_name_joins` key must be a join some drink actually produces.

    THE SAME BARGAIN `methods.yml` STRIKES with its proposals, and for the same
    reason: this map duplicates live data -- the left-hand side is a string the
    template builds elsewhere from two card names -- so it is only safe
    alongside the check that keeps the duplicate honest.

    Two ways it rots, and neither is visible on the page. A card name changes
    and the key stops matching, so the replacement silently stops applying and
    the clunky join comes back. Or a drink's generics change and the pair no
    longer occurs, leaving an entry that reads as a live decision about how the
    index looks while doing nothing at all.
    """
    _require_whole_collection("`card_name_joins`")
    vocab = _vocab()
    names = vocab.get("card_names") or {}
    joins = vocab.get("card_name_joins") or {}
    if not joins:
        pytest.skip("`card_name_joins` is empty; no default join is "
                    "overridden, which is a legitimate state.")
    produced = set()
    for slug, fm in _load():
        for item in (fm.get("ingredients") or []):
            # Gated on `generic`, not `item` -- see the note in
            # test_showing_categories_still_shortens_the_index.
            if not isinstance(item, dict) or not item.get("generic"):
                continue
            generic = item["generic"]
            generics = generic if isinstance(generic, list) else [generic]
            labels = [names[g] for g in generics if g in names]
            if labels and len(labels) == len(generics) and len(labels) > 1:
                produced.add(" or ".join(labels))
    assert produced, (
        "No drink produces a joined rum card name at all, so this check is "
        "vacuous. Ten rum entries carry a list `generic` -- either that stopped "
        "being true, or the card names no longer resolve."
    )
    stale = sorted(set(joins) - produced)
    assert not stale, (
        "Join replacement(s) matching nothing:\n  " + "\n  ".join(stale)
        + "\n\nEither a card name changed and this key did not follow — in "
          "which case the default join is back on the index and nobody was "
          "told — or no drink asks for that pair any more and the entry should "
          "go.\nJoins actually produced today:\n  " + "\n  ".join(sorted(produced))
    )


# =============================================================================
# The bottle dictionary -- #529, and the check it unblocks, #534
# =============================================================================

def _bottles():
    if not BOTTLES.exists():
        pytest.skip("_data/cocktails/bottles.yml does not exist yet.")
    return yaml.safe_load(BOTTLES.read_text(encoding="utf-8")) or {}


def _bottle_index(data):
    """Every name a bottle answers to, lowercased -> its canonical name.

    Case-insensitive because the collection writes `Plantation OFTD` and
    `Planteray OFTD` for one bottle, and because a suggestion is prose typed by
    hand. Aliases and canonical names share one namespace on purpose: an alias
    that collides with another bottle's real name is the same bug either way.
    """
    out = {}
    for name, entry in (data.get("bottles") or {}).items():
        out[name.strip().lower()] = name
        for alias in (entry or {}).get("aliases") or []:
            out[alias.strip().lower()] = name
    return out


def test_every_bottle_names_a_declared_generic():
    """A bottle's `generic` is a real generic -- #529.

    THE WHOLE VALUE OF THIS FILE IS THAT A BOTTLE KNOWS ITS CATEGORY, so a
    generic that no longer exists makes the dictionary quietly wrong rather
    than loudly broken -- nothing on any page would look different.

    THE RUM-ONLY HALF CAME OFF ON 2026-08-30, Helen's call. This used to check
    against `family_of`'s rum members, on the reasoning that "this file does not
    cover gin or brandy, and a bottle typed `cognac` would be a scoping mistake
    rather than a typo". That was true when #529 built it as a rum reference and
    had already stopped being true: Ceylon arrack joined the card names, `Tesco
    Finest` went into `unresolved_suggestions` for a kirsch and a sloe gin, and
    the Kamaniwanalaya wanted Disaronno resolved.

    The scoping argument does not survive the widening, but the TYPO argument
    does and is the one worth keeping -- a generic that was renamed and not
    followed here is still silent. So: declared, not rum.
    """
    data = _bottles()
    vocab = _vocab()
    declared = _declared_generics(vocab)
    assert declared, "ingredients.yml declares no generics; nothing to check."
    entries = data.get("bottles") or {}
    assert entries, (
        "bottles.yml declares no bottles, so every check here is vacuous."
    )
    bad = sorted(
        f"{name!r} -> {(entry or {}).get('generic')!r}"
        for name, entry in entries.items()
        if (entry or {}).get("generic") not in declared
    )
    assert not bad, (
        "Bottle(s) whose generic is not a declared style:\n  "
        + "\n  ".join(bad)
        + "\n\nThe style was probably renamed and this did not follow. Note "
          "that a bottle no longer has to be a rum -- that restriction came off "
          "on 2026-08-30 -- but its category still has to exist."
    )


def test_no_bottle_name_or_alias_is_claimed_twice():
    """One string, one bottle -- #529.

    Aliases exist because twelve suggestion strings in the collection collapse
    to about five bottles (ED3 / El Dorado 3 / El Dorado 3yo), and because
    Planteray and Plantation are one brand renamed, which no string comparison
    recovers. That only works while a string resolves to exactly one bottle: a
    duplicate would make resolution order-dependent, and #534's cross-category
    check would then depend on dictionary ordering rather than on fact.

    Canonical names and aliases share one namespace deliberately -- an alias
    colliding with another bottle's real name is the same bug as two aliases
    colliding, and is likelier (`Planteray 3` against `El Dorado 3`).
    """
    data = _bottles()
    entries = data.get("bottles") or {}
    assert entries, "bottles.yml declares no bottles; nothing to check."
    seen, clashes = {}, []
    for name, entry in entries.items():
        for label in [name] + list((entry or {}).get("aliases") or []):
            key = label.strip().lower()
            if key in seen and seen[key] != name:
                clashes.append(f"{label!r}: {seen[key]!r} and {name!r}")
            seen[key] = name
    assert not clashes, (
        "String(s) claimed by two bottles:\n  " + "\n  ".join(clashes)
        + "\n\nA suggestion naming one of these could not be resolved to a "
          "single bottle, so #534's cross-category check would be guessing."
    )


def test_an_excluded_bottle_is_not_also_listed():
    """`not_reached_for` and `bottles` must not both claim a bottle -- #529.

    The two blocks say opposite things: `bottles` is what Helen would pour,
    `not_reached_for` is what qualifies and is deliberately out (Lemon Hart
    151). A bottle in both is a half-finished decision, and the reference page
    would list it while the reason says it should not.
    """
    data = _bottles()
    index = _bottle_index(data)
    excluded = data.get("not_reached_for") or {}
    both = sorted(
        f"{name!r} (listed as {index[name.strip().lower()]!r})"
        for name in excluded if name.strip().lower() in index
    )
    assert not both, (
        "Bottle(s) both listed and excluded:\n  " + "\n  ".join(both)
        + "\n\nDelete it from one. `bottles` means Helen would reach for it; "
          "`not_reached_for` means it qualifies and she would not."
    )


def test_every_suggested_bottle_resolves():
    """Every `suggestion` names a bottle this file knows -- #529/#534.

    THE DIRECTION THAT MATTERS. Nothing requires a bottle to be used by a drink
    -- Helen owns bottles no recipe names, and El Dorado 151 is on the shopping
    list -- but a SUGGESTION that resolves to nothing is a bottle the site
    cannot reason about, and #534's cross-category check silently skips it.
    Half a check is worse than none, because it reports a clean run.

    THE WORD "rum" CAME OUT OF THAT FIRST LINE ON 2026-08-30, and it had been
    doing a lot of quiet work: 54 of the collection's 91 distinct suggestions
    were non-rum and so were checked by nothing at all. See `_suggested_bottle_scan`.

    KNOWN FAILURES ARE DECLARED, NOT TOLERATED. What is left in
    `unresolved_suggestions` is prose, two-bottles-in-one-string, or a BRAND
    where a bottle belongs -- Briottet makes six of the things this collection
    pours, so the string names a house and the drink names the product. Each
    sits there with its reason, so this test bites on the NEXT one while those
    are being fixed. Deleting a line there is how one gets retired -- the same
    shape `methods.yml` uses for its proposals.
    """
    _, unresolved = _suggested_bottle_scan()
    assert not unresolved, (
        "Suggestion(s) naming no known bottle:\n  " + "\n  ".join(sorted(unresolved))
        + "\n\nEither add the bottle to _data/cocktails/bottles.yml, add the "
          "spelling as an alias of one already there, or -- if it is prose "
          "rather than a bottle name (#457) -- declare it in "
          "`unresolved_suggestions` with the reason, so it fails loudly for "
          "the next reader instead of quietly for this one."
    )


def test_the_bottle_index_is_exercised():
    """Some ingredient in the collection actually carries a suggestion.

    Zero would mean the loader went stale -- and the rule above would be green
    over nothing. Whole collection only: see `_exercised`.

    The word "rum" came out of this docstring on 2026-08-30 with the scoping it
    described. Leaving it would be the trap this repo keeps meeting from the
    other side: a comment that outlives the code it describes, which is how
    `cocktails/index.html` spent three commits claiming to emit `item`.
    """
    checked, _ = _suggested_bottle_scan()
    _exercised(
        checked, "the suggested-bottle check",
        "Around forty rum pours name a bottle across the whole collection, so "
        "zero means `family_of` stopped mapping the rum styles or the loader is "
        "stale.")


def _suggested_bottle_scan():
    """(how many suggestions were checked, the ones naming no known bottle).

    ONE SCAN, TWO TESTS -- see `_character_scan` for why they may not be
    re-typed apart.

    NOT RUM-ONLY SINCE 2026-08-30. It skipped any ingredient whose generic was
    not in the rum family, which was right while `bottles.yml` was a rum
    reference and left a real hole once it stopped being one: 54 of the 91
    distinct suggestions in the collection resolved to nothing and no test
    minded, because none of them was a rum. Beefeater, Cointreau, Tanqueray,
    Luxardo, Suze, Punt e Mes -- all invisible.

    Helen's call when shown that count: "are we now assuming every named bottle
    should be in it, and classified? That feels right to me." So the scan covers
    every ingredient, and the 43 whose category the collection already stated
    were declared in the same pass.
    """
    data = _bottles()
    index = _bottle_index(data)
    known = {k.strip().lower() for k in (data.get("unresolved_suggestions") or {})}
    excluded = {k.strip().lower() for k in (data.get("not_reached_for") or {})}
    assert index, "bottles.yml resolves no names; nothing to check."

    unresolved, checked = [], 0
    for slug, fm in _load():
        for item in (fm.get("ingredients") or []):
            if not isinstance(item, dict):
                continue
            suggestion = item.get("suggestion")
            for name in (suggestion if isinstance(suggestion, list)
                         else [suggestion] if suggestion else []):
                checked += 1
                key = name.strip().lower()
                if key in index or key in known or key in excluded:
                    continue
                unresolved.append(f"{slug}: {name!r}")
    return checked, unresolved


def test_a_cross_category_suggestion_carries_a_note():
    """Suggesting a bottle from another category needs a note -- #534.

    Helen: "Substituting it isn't straightforward and will vary by drink. Please
    add notes for me on recipe pages when I've substituted in a surprising way."
    A `suggestion` whose bottle sits in a different category than that
    ingredient's `generic` IS the surprising case, by definition; everything
    else is naming a bottle in the category the recipe already asked for. It
    stops being a judgement call the moment a bottle knows its own category,
    which is what _data/cocktails/bottles.yml is for.

    PERMISSIVE, AT HELEN'S DIRECTION, and the permission has a precise shape:
    the note must EXIST, and `QQ` counts. "Let's be permissive with the test,
    but given we're pre-first-human-read please add the note field with QQ in it
    if we don't have anything else." So a substitution can never ship silently
    -- there is always a visible marker on the page -- while nothing demands
    prose she has not written yet. QQ is the collection's existing idiom for
    exactly this (see test_every_ingredient_has_a_generic_or_a_qq) and these are
    drafts; a QQ is not near a published recipe.

    A DISJUNCTIVE GENERIC CROSSES ONLY IF THE BOTTLE MATCHES NONE OF ITS
    OPTIONS. A list means "either would do" (#441), so a suggestion satisfying
    either half is not a substitution at all. Swizzle is why this rule needs
    stating: it asks for two Demerara styles and suggests bottles in neither.

    An unresolvable suggestion is SKIPPED here rather than failing twice --
    test_every_suggested_bottle_resolves owns that, and reporting one fault as
    two teaches you to skim the output.
    """
    _, bad = _cross_category_scan()
    assert not bad, (
        "Cross-category substitution(s) with nothing on the page saying why:\n  "
        + "\n  ".join(sorted(bad))
        + "\n\nAdd a per-ingredient `note` (#457). `QQ` is a valid note and is "
          "the right one until Helen's first read-through -- the point is that "
          "the substitution is VISIBLE, not that the reasoning is finished."
    )


def test_the_cross_category_check_is_exercised():
    """Some rum suggestion in the collection resolves to a known bottle.

    This rule can only see substitutions among suggestions that RESOLVE, so a
    bottles.yml that stopped matching the collection's spellings would leave it
    green over nothing. Whole collection only: see `_exercised`.
    """
    checked, _ = _cross_category_scan()
    _exercised(
        checked, "the cross-category substitution check",
        "Either bottles.yml stopped matching the collection's spellings, or the "
        "loader is stale.")


def _cross_category_scan():
    """(how many resolved suggestions were checked, the unexplained ones).

    ONE SCAN, TWO TESTS -- see `_character_scan`.

    NOT RUM-ONLY SINCE 2026-08-30, and the widening has a worked example behind
    it rather than a principle. `bottles.yml` stopped being a rum file that
    morning; this scan did not follow, so a cross-category substitution outside
    rum was invisible -- and one was: Don's Mai Tai asks for `absinthe` and
    suggests Pernod, which is a pastis. The drink has carried a note saying so
    all along, so nothing was broken; nothing was CHECKING either, and the
    session that widened the bottle file nearly declared Pernod an absinthe on
    the strength of the generic beside it. That declaration would have made this
    very check agree the pair matched.

    Helen, asked whether a bottle's category may differ from the ingredient it
    is suggested for: "Yes, and the note should be required." Her own example is
    the reason it must be allowed at all -- "a recipe might call for cherry
    brandy, and I suggest Cherry Heering OR Briottet cerise even though that's a
    cherry liqueur not a brandy, leaving it to future Helen to choose."
    """
    data = _bottles()
    index = _bottle_index(data)
    entries = data.get("bottles") or {}
    assert index, "bottles.yml resolves no names; nothing to check."

    bad, checked = [], 0
    for slug, fm in _load():
        for item in (fm.get("ingredients") or []):
            if not isinstance(item, dict):
                continue
            generic = item.get("generic")
            generics = generic if isinstance(generic, list) else [generic]
            suggestion = item.get("suggestion")
            names = (suggestion if isinstance(suggestion, list)
                     else [suggestion] if suggestion else [])
            for name in names:
                canonical = index.get(name.strip().lower())
                if canonical is None:
                    continue  # owned by test_every_suggested_bottle_resolves
                checked += 1
                bottle_generic = (entries.get(canonical) or {}).get("generic")
                if bottle_generic in generics:
                    continue
                if item.get("note"):
                    continue
                bad.append(
                    f"{slug}: {item.get('item') or '?'!r} asks for "
                    f"{generics} and suggests {canonical!r} "
                    f"({bottle_generic!r}) — no note"
                )
    return checked, bad


# =============================================================================
# AMOUNTS -- one field, and a table that turns it into a number. Spec: #571
# =============================================================================
# `ml:` USED TO BE STORED BESIDE EVERY `amount:` and is gone. See the
# `measures:` block in ingredients.yml for the measurement that made the
# deletion safe and for why the conversions belong in data.

_AMOUNT_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(?:/\s*(\d+))?\s*(.*?)\s*$")


def _millilitres(amount, measures):
    """(millilitres, unit) for one `amount` string; (None, unit) if not a volume.

    Raises ValueError when the string cannot be read at all, which is the one
    outcome that matters -- see test_every_amount_is_readable_as_a_quantity.

    THE UNIT IS REQUIRED, and a bare number is deliberately an error rather
    than an assumed millilitre figure. Nineteen amounts in the collection are
    bare numbers, and they are NOT all the same unit: Port-au-Prince's ladder
    (30, 22.5, 15, 7.5, 5) is plainly millilitres and Drunken Skull's
    (0.75, 0.75, 0.5, 0.5) is just as plainly ounces. Guessing gets one of them
    wrong by a factor of 30 and looks exactly as confident either way. Every
    one of the nineteen already carries a `QQ - no unit in the source` note,
    which is the right answer and the one this check preserves.
    """
    text = str(amount)
    match = _AMOUNT_RE.match(text)
    if not match:
        raise ValueError("no leading number")
    whole, denominator, rest = match.groups()
    number = float(whole)
    if denominator:
        number /= float(denominator)
    words = [w for w in rest.lower().split()
             if w not in (measures.get("ignored_words") or [])]
    if not words:
        raise ValueError("a number with no unit")
    unit = " ".join(words)
    per_ml = measures.get("per_ml") or {}
    if unit in per_ml:
        return round(number * per_ml[unit], 3), unit
    if unit in (measures.get("non_volumetric") or []):
        return None, unit
    raise ValueError(f"undeclared unit {unit!r}")


def _amount_scan():
    """(how many amounts read cleanly, the ones that did not).

    ONE SCAN, TWO TESTS -- see `_character_scan`.
    """
    measures = _vocab().get("measures") or {}
    read = 0
    bad = []
    for slug, fm in _load():
        notes = " ".join(str(n) for n in (fm.get("notes") or []))
        for item in (fm.get("ingredients") or []):
            if not isinstance(item, dict) or item.get("amount") is None:
                continue
            try:
                _millilitres(item["amount"], measures)
            except ValueError as why:
                # THE EXEMPTION IS THE DRINK'S OWN QQ, not a registry here.
                # A hardcoded list of slugs cannot tell a gap that has been
                # filled from one that has merely been deleted, and HANDOVER 10
                # records five guards going false-red on exactly that shape.
                # A QQ note is per-drink, so it works on a partial corpus, and
                # it fails in BOTH directions that matter: fill the unit in and
                # forget the note, or drop the note without filling it in.
                if "no unit in the source" in notes or "carries no ml figure" in notes:
                    continue
                bad.append(
                    f"{slug}: amount {item['amount']!r} on "
                    f"{item.get('item') or item.get('generic')!r} -- {why}"
                )
            else:
                read += 1
    return read, bad


def test_every_amount_is_readable_as_a_quantity():
    """Every `amount` yields millilitres, or names a declared non-volume -- #571.

    THIS IS WHAT `ml:` WAS ACTUALLY FOR. The stored figure looked like the
    guarantee that a drink's quantities are computable, and it was not one: it
    could simply be absent, and on all nineteen unitless amounts it was. A
    consumer reading `.get("ml")` got `None` and had no way to tell "this is a
    dash, correctly numberless" from "this says 30 and nobody wrote the unit".

    So the number is derived from `measures:` in ingredients.yml and this check
    is the promise. #545 (scaler), #294/#297 (alcohol units) and #547 (cost)
    can all be built against it.

    AN UNDECLARED UNIT FAILS HERE RATHER THAN VANISHING. Adding a unit is one
    line in `measures:` -- `per_ml` if it is a volume, `non_volumetric` if it
    counts or weighs. Declaring it is what switches enforcement on, the same
    bargain `canonical_glasses` and the `<family>_characters` lists strike.
    """
    _, bad = _amount_scan()
    assert not bad, (
        "Amounts that cannot be read as a quantity:\n  " + "\n  ".join(bad)
        + "\n\nEither the unit is missing from `measures:` in "
          "_data/cocktails/ingredients.yml -- add it to `per_ml` with its "
          "millilitre value, or to `non_volumetric` -- or the amount really "
          "has no unit, in which case do NOT guess one: 0.75 is an ounce on "
          "Drunken Skull and 22.5 is a millilitre on Port-au-Prince, and the "
          "difference is thirtyfold. Write a `QQ - no unit in the source for "
          "<amount> <item>` note, as all nineteen existing cases do."
    )


def test_the_amount_table_is_exercised():
    """Amounts are actually being read, rather than all being exempted.

    The QQ escape in `_amount_scan` is per-drink and generous by design, so the
    failure mode this guards is the whole check quietly exempting itself -- a
    parser change that raised on everything would look identical to a clean run
    if nobody counted what got through.
    """
    read, _ = _amount_scan()
    _exercised(
        read, "the amount table",
        "Every amount in the collection failed to parse, or none was found at "
        "all -- `measures:` or the `amount` key has moved.")


def test_the_declared_measures_produce_the_figures_the_data_used_to_store():
    """The conversions still say what `ml:` said before it was deleted -- #571.

    ANCHORS, NOT A ROUND TRIP. The 521 stored figures are gone, so nothing can
    re-derive and compare them; what survives is a handful of real pairs taken
    from the collection on the day of the deletion, one per declared unit plus
    the two shapes that nearly broke the parser.

    THE FRACTION CASE IS HERE BECAUSE IT ALREADY FOOLED ME ONCE. A first pass
    at this measurement read "2/3 oz" as 2 and reported Don's Mai Tai as the
    only drink whose stored `ml` disagreed with its `amount`. The data was
    right and the parser was wrong, which is the direction that would have
    silently tripled two figures had it not been checked against what was
    actually stored.
    """
    measures = _vocab().get("measures") or {}
    cases = [
        ("25 ml", 25.0),        # the 376-entry majority
        ("0.5 oz", 15.0),       # 1 oz -> 30, the bar-standard rounding
        ("2/3 oz", 20.0),       # Don's Mai Tai -- stored 20
        ("1/3 oz", 10.0),       # Don's Mai Tai -- stored 10
        ("2 tsp", 10.0),        # 1 tsp -> 5
        ("1 heaping oz", 30.0), # Kill Devil Punch -- `heaping` is ignored
    ]
    wrong = [f"{text!r} -> {_millilitres(text, measures)[0]}, expected {want}"
             for text, want in cases
             if _millilitres(text, measures)[0] != want]
    assert not wrong, (
        "The declared conversions no longer reproduce figures the collection "
        "actually stored:\n  " + "\n  ".join(wrong)
        + "\n\nThese are real amounts from real drinks, checked against their "
          "`ml:` values before that key was deleted. If a conversion is being "
          "changed on purpose, say so here -- silently is how ratios drift."
    )
    for text in ("2 dashes", "12 cubes", "75 g"):
        assert _millilitres(text, measures)[0] is None, (
            f"{text!r} is not a volume and must yield no millilitre figure. "
            "Returning 0 instead of None is the bug that would make "
            "_syrup_ratio_scan average a dash in as if it were nothing."
        )


def test_no_ingredient_stores_a_millilitre_figure():
    """`ml:` is retired -- #571. The `amount` string is the only quantity.

    A RETURNING KEY WOULD BE READ BY NOTHING AND WOULD DRIFT IN SILENCE, which
    is the whole reason it went: 521 entries held the same fact twice, and the
    duplicate's only possible future was to disagree with the string beside it.
    An ingest session copying an older drink as a template is exactly how it
    comes back -- the same route HANDOVER 4.0 records for the hyphenated
    `awaiting-fix` spelling reappearing across 34 files.
    """
    bad = [f"{slug}: {item.get('item') or item.get('generic')!r} has ml: {item['ml']!r}"
           for slug, fm in _load()
           for item in (fm.get("ingredients") or [])
           if isinstance(item, dict) and "ml" in item]
    assert not bad, (
        "`ml:` is retired -- the quantity is `amount` alone:\n  "
        + "\n  ".join(bad)
        + "\n\nThe millilitre figure is derived from `measures:` in "
          "_data/cocktails/ingredients.yml. If an amount cannot be read, that "
          "is a missing unit to declare or a genuine QQ, not a reason to write "
          "the number down a second time."
    )


def test_every_drinks_moods_match_the_derivation():
    """Stored moods equal what taxonomy.yml's own rules produce -- #452.

    MOODS ARE STORED RATHER THAN COMPUTED AT RENDER, so that Helen can
    override one -- and the cost of storing them is that they can go stale
    against the rules while looking perfectly fine. They did, comprehensively.
    Derived once on 2026-08-17 and frozen into 114 files; by 2026-08-30 the
    derivation's ingredient sets held 34 strings naming nothing, 24 drinks
    disagreed with the rules, and **23 drinks had no mood at all** -- including
    `naked-and-famous`, which Helen rates `oh gods yes`, and
    `martinique-swizzle`, which was carrying `fruity` and `tiki` inherited from
    the drink it replaced despite containing no fruit and no tiki marker.

    A DRINK WITH NO MOOD IS INVISIBLE TO BOTH QUESTIONS THE INDEX ASKS. It can
    be reached by ingredient or by name and by nothing else, and the index --
    which is a browsing tool first -- gives no sign it is there. Nothing failed,
    because nothing compared the stored value to the rule that produced it.

    HELEN'S CORRECTIONS ARE PART OF THE EXPECTED VALUE, not an exemption from
    it: `mood_include` and `mood_exclude` in taxonomy.yml each name the single
    mood they are about, so a corrected drink still tracks every later
    improvement to the rules. The Sazerac keeps `strong brown drink` (its
    discarded rinse water drags the volume rule to 44%) and still gained
    nothing wrongly.

    RE-RUN, DO NOT HAND-EDIT: `python3 scripts/derive_cocktail_moods.py`
    reports the difference and `--write` applies it. If the derivation is
    wrong about a drink, that is a rule to fix in taxonomy.yml or a correction
    to record there -- never a mood typed into a file where the next run will
    silently revert it.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import derive_cocktail_moods as deriver
    except ImportError:  # pragma: no cover
        pytest.skip("scripts/derive_cocktail_moods.py not importable")

    taxonomy = _taxonomy()
    vocab = _vocab()
    assert taxonomy.get("mood_ingredients"), (
        "`mood_ingredients` is missing; nothing to derive from.")
    sets = deriver.load_sets(taxonomy, vocab)
    step_words = taxonomy.get("mood_step_words") or {}
    families = set(vocab.get("family_of") or {})
    include = taxonomy.get("mood_include") or {}
    exclude = taxonomy.get("mood_exclude") or {}
    order = list(taxonomy.get("moods") or {})

    bad = []
    for slug, fm in _load():
        stored = [str(m) for m in (fm.get("mood") or [])]
        # THE SCRIPT'S OWN FUNCTION, not a second copy of its four steps. The
        # copy that used to live here drifted the moment the derivation gained
        # an input, and would have drifted again over `moods_by_hand`.
        derived = deriver.expected_moods(slug, fm, stored, taxonomy, sets,
                                         step_words, families)
        if derived != stored:
            gained = [m for m in derived if m not in stored]
            lost = [m for m in stored if m not in derived]
            bad.append(f"{slug}: stored {stored}"
                       + (f", derivation adds {gained}" if gained else "")
                       + (f", derivation drops {lost}" if lost else ""))
    assert not bad, (
        "Stored moods disagree with taxonomy.yml's own rules:\n  "
        + "\n  ".join(bad)
        + "\n\nRun `python3 scripts/derive_cocktail_moods.py` to see the "
          "difference and `--write` to apply it. Do NOT hand-edit a `mood:` "
          "block -- the next run reverts it silently. If the derivation is "
          "wrong about a drink, fix the rule in `mood_ingredients` or record "
          "the correction in `mood_include`/`mood_exclude`, both in "
          "taxonomy.yml, so the reason survives."
    )


def test_every_mood_correction_is_reachable_and_needed():
    """A correction names a real drink and still changes something -- #452.

    A CORRECTION THAT SILENTLY DOES NOTHING is the failure this repo has met
    before: `EXTRA_NOTES["Sazerac"]` was written, the ingest ran cleanly, and
    the note never appeared because that drink was in SKIP. Nothing complained.

    Two ways one dies here. It can name a drink that no longer exists, in
    which case it is inert. Or the rules can improve until the drink derives
    the mood on its own -- and then the correction reads as load-bearing while
    doing nothing, which is worse, because the next reader trusts it. The
    Swizzle's entry says exactly that of itself: it was expected to become
    unnecessary once #335 typed its rums.

    Same bargain `methods.yml`'s proposals strike, and the reason it is
    WHOLE_COLLECTION_ONLY: on a partial corpus a correction whose drink is
    merely absent looks identical to one whose drink is gone.
    """
    _require_whole_collection("the mood corrections")
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import derive_cocktail_moods as deriver
    except ImportError:  # pragma: no cover
        pytest.skip("scripts/derive_cocktail_moods.py not importable")

    taxonomy = _taxonomy()
    vocab = _vocab()
    sets = deriver.load_sets(taxonomy, vocab)
    step_words = taxonomy.get("mood_step_words") or {}
    families = set(vocab.get("family_of") or {})
    drinks = dict(_load())

    bad = []
    for kind, entries in (("mood_include", taxonomy.get("mood_include") or {}),
                          ("mood_exclude", taxonomy.get("mood_exclude") or {})):
        for slug, entry in entries.items():
            if slug not in drinks:
                bad.append(f"{kind}.{slug}: names no drink in the collection")
                continue
            if not str(entry.get("why", "")).strip():
                bad.append(f"{kind}.{slug}: has no `why`")
            derived = deriver.derive(drinks[slug], sets, step_words, families)
            for mood in (entry.get("moods") or []):
                if mood not in (taxonomy.get("moods") or {}):
                    bad.append(f"{kind}.{slug}: {mood!r} is not a declared mood")
                elif kind == "mood_include" and mood in derived:
                    bad.append(
                        f"mood_include.{slug}: {mood!r} is derived anyway now "
                        "-- the rules caught up, so this entry does nothing "
                        "and should go")
                elif kind == "mood_exclude" and mood not in derived:
                    bad.append(
                        f"mood_exclude.{slug}: {mood!r} is not derived anyway "
                        "-- nothing to remove, so this entry does nothing")
    assert not bad, (
        "Mood correction(s) that do not do what they claim:\n  "
        + "\n  ".join(bad)
        + "\n\nA spent correction reads as outstanding work and as a live "
          "reason. Delete the entry, or fix what it names."
    )


def test_every_mood_ingredient_is_declared():
    """The mood derivation's ingredient sets name real vocabulary -- #452.

    THIS IS THE TEST WHOSE ABSENCE COST THE MOODS. Moods were derived once, on
    2026-08-17, from nine hardcoded sets of generic names inside the drafts
    repo's `ingest_from_csv.py`, and the output was frozen into 114 files. The
    vocabulary then moved: #335 finished typing every generic, #314
    reclassified the rums and moved `blackstrap` from a generic to a character,
    #561 renamed ten generics including every rum and both gins, #568 added
    five, the Chartreuses took their French names.

    **34 of those strings named nothing at all** by the time anyone looked --
    nine of `aged`'s 29, which is every rum and every whisky in it, so `strong
    brown drink` could no longer fire on a rum; five of `clear`'s 17; five of
    `tiki`'s 13; nine of `loud`'s 23.

    A SET INTERSECTION AGAINST A RENAMED STRING RETURNS EMPTY. It does not
    raise and it does not warn, and the derivation had already run, so the
    drift was invisible from both ends at once. §9.12's bargain, from the other
    side: duplicate live data only alongside the test that keeps the duplicate
    honest. The duplicate was in a private repo's script, so there was no test
    and could not have been one.

    GENERICS **OR** CHARACTERS, because `blackstrap` is legitimately a
    `rum_characters` value and appears in two sets. Reading generics alone was
    one of the 34.
    """
    vocab = _vocab()
    sets = _taxonomy().get("mood_ingredients") or {}
    assert sets, (
        "`mood_ingredients` is missing from taxonomy.yml. It is the "
        "derivation's whole vocabulary; without it "
        "scripts/derive_cocktail_moods.py derives nothing and this check "
        "compares nothing."
    )
    allowed = set(_declared_generics(vocab))
    for key, value in vocab.items():
        if _is_character_list(key) and isinstance(value, list):
            allowed |= set(value)

    bad = []
    for name, members in sorted(sets.items()):
        for m in members:
            if m not in allowed:
                bad.append(f"mood_ingredients.{name}: {m!r}")
    assert not bad, (
        "Mood ingredient(s) naming no declared generic or character:\n  "
        + "\n  ".join(bad)
        + "\n\nEvery member must be a real value from ingredients.yml. A "
          "string that names nothing does not fail at derivation time -- the "
          "set intersection simply comes back empty and the mood silently "
          "stops firing, which is exactly how `strong brown drink` stopped "
          "reaching any rum. If a generic was renamed, follow it here; the "
          "`retired_*` maps in ingredients.yml record every successor."
    )

    # `mood_up_glasses` USED TO BE CHECKED HERE and went with the `up` mood on
    # 2026-08-30 -- see the deriver for why that mood lost. It was the only
    # glass-valued list the moods read; if another appears, check it against
    # glasses.yml the way this did, because an unmatched glass name narrows a
    # mood silently rather than erroring.


def test_source_names_a_source_and_source_url_holds_the_url():
    """`source` is who, `source_url` is where -- #454. A SHAPE rule only.

    NOTHING HERE ASKS FOR COVERAGE, and that is the whole design. 86 of 114
    drinks have `source: ""` and Helen's ruling on 2026-08-30 is that this is
    fine: "I sort of don't care about this. You can't copyright facts, and I am
    taking no prose from anywhere. Some will be attributable to a big-name
    inventor, bar or maybe hotel, and it's nice to note that, but I'm not going
    to sweat it."

    That is the right call and it is a real difference from food, not laziness.
    `SOURCE_ATTRIBUTION_SPEC.md` and the eight `source_type` values exist
    because a food recipe is ADAPTED PROSE and the promotion gate is about
    copyright. A cocktail is a formula plus a build -- quantities and steps --
    so there is nothing to attribute in that sense, and importing that
    apparatus would be the encyclopaedia-of-drinks busywork #459 rules out.

    WHAT IS STILL WRONG RATHER THAN ABSENT is one field being used as the
    other. `witches-daiquiri` carried a raw Difford's URL in `source` with
    `source_url` empty -- so the drink page printed a URL where it prints a
    name, and the URL field it has sat unused beside it. One instance, fixed;
    this stops the next, because the shape of a mistake is what recurs and an
    empty field is not a mistake at all.
    """
    checked = 0
    bad = []
    for slug, fm in _load():
        if "source" not in fm:
            continue
        checked += 1
        source = fm.get("source")
        if not isinstance(source, str):
            bad.append(f"{slug}: source is a {type(source).__name__}")
            continue
        if re.match(r"\s*(https?://|www\.)", source):
            bad.append(f"{slug}: source holds a URL -- {source[:60]!r}")
    assert not bad, (
        "`source` is misused:\n  " + "\n  ".join(bad)
        + "\n\n`source` names WHO -- a person, a bar, a book, a site by name "
          "(\"Difford's\"). `source_url` holds the link. An empty `source` is "
          "fine and always will be; a URL in it is not."
    )
    assert checked, (
        "No drink declares `source` at all, so this compared nothing -- every "
        "drink carried the key when this was written."
    )


def test_no_drink_uses_a_generic_that_is_helens_to_apply():
    """A style listed in `hers_to_apply` may not be inferred onto a drink -- #542.

    THE FAILURE THIS EXISTS FOR IS INVISIBLE TO EVERY OTHER GUARD HERE, and
    #542 says so in its own words: "a wrong-but-declared value with no
    contradicting evidence is invisible to every guard in the suite". Every
    value involved is declared and valid. `test_every_generic_is_declared` is
    green. The suggestion that would have contradicted it was dropped, so
    #534's cross-category check is green too. Nothing was left to notice.

    What actually happened, twice: `caramel-forward Jamaican rum` has bottles
    (Blackwell, Myers) and no drink, and a session read that as a gap and
    retyped a drink into it from its own `item` text. Helen, 2026-08-30, after
    the second time: "I have discussed this at least twice... If I have to deal
    with this again I will simply delete those recipes."

    HANDOVER 9.3.2 ALREADY FORBADE IT IN PROSE -- "it is hers to apply: never
    retype a drink into it from item text" -- which is the whole argument for
    this being a test. Two hooks in `.claude/`, `meta.awaiting_fix` and
    `meta.proofread` all reached the same conclusion first: a rule that gets
    read and broken needs a mechanism.

    THE LIST IS THE ENFORCEMENT AND REMOVING A LINE IS THE GRANT. Helen deletes
    an entry in the same commit as the drink that earns the style; nobody else
    does, and never to make this go green.
    """
    reserved = _vocab().get("hers_to_apply") or {}
    assert reserved, (
        "`hers_to_apply` is empty. If a style has genuinely been released, "
        "that is Helen's call and this test should have gone with it -- an "
        "empty registry here means the check compares nothing."
    )
    declared = _declared_generics(_vocab())
    phantom = sorted(set(reserved) - declared)
    assert not phantom, (
        "`hers_to_apply` names generic(s) no group declares:\n  "
        + "\n  ".join(phantom)
        + "\n\nA reserved style must be a real one. A typo here reserves "
          "nothing and reads as though it does."
    )
    bad = []
    for slug, fm in _load():
        for item in (fm.get("ingredients") or []):
            if not isinstance(item, dict):
                continue
            generic = item.get("generic")
            for g in (generic if isinstance(generic, list) else [generic]):
                if g in reserved:
                    bad.append(f"{slug}: {g!r}\n      {reserved[g].strip()}")
    assert not bad, (
        "Drink(s) using a generic that is Helen's to apply:\n  "
        + "\n  ".join(bad)
        + "\n\nDo not infer this from `item` text or from a bottle name. If "
          "she has applied it, the line comes out of `hers_to_apply` in "
          "_data/cocktails/ingredients.yml in the same commit -- and that "
          "deletion is hers, not yours."
    )


def test_every_ingredient_entry_has_something_the_line_renders():
    """An entry with none of `amount`/`generic`/`item` prints as a raw Hash.

    `_layouts/cocktail.html` renders the structured ingredient line when the
    entry carries one of those three and otherwise falls through to a
    bare-string branch, where Liquid stringifies a dict. Tried on Aperol
    Spritz: the page printed `{"amount"=>"90 ml", "generic"=>"prosecco"}` with
    a clean build and nothing in the log.

    THE GATE USED TO NAME `item` ALONE, which #544 move 1 stopped rendering, so
    this was primed to fire on move 2's first and safest step -- dropping
    `item` from the ~283 entries whose every word already appears in the
    generic beside them. Fixed there; this is the data half.

    There are no bare-string ingredients today (619 of 619 are dicts), and that
    branch is for a genuinely unstructured one. A dict arriving there is not
    that shape, it is this one with a key missing, which is why it must never
    be reachable by omission.
    """
    checked = 0
    bad = []
    for slug, fm in _load():
        for item in (fm.get("ingredients") or []):
            if not isinstance(item, dict):
                continue
            checked += 1
            if not (item.get("amount") or item.get("generic") or item.get("item")):
                bad.append(f"{slug}: {item!r}")
    assert not bad, (
        "Ingredient entries with nothing the line can render:\n  "
        + "\n  ".join(bad)
        + "\n\nEach needs an `amount`, a `generic` or an `item`. Without one "
          "the drink page prints the YAML dict itself, on a green build."
    )
    assert checked, "No ingredient entries were scanned, so this compared nothing."


def test_no_drink_writes_plantation():
    """Planteray is the brand's name; `plantation` is only ever read -- #582.

    Helen: "'plantation' is not permitted as a kind of rum and should always be
    corrected to 'planteray'." Planteray is canonical (HANDOVER 9.3.2,
    2026-08-27) and the old spellings stay in `bottles.yml` as ALIASES, which is
    not half a finished rename but the same division `canonical_glasses` draws:
    **the rule governs what is WRITTEN, the alias map governs what can be
    READ.** Most of these drinks predate the rebrand, so a suggestion has to
    keep resolving whether or not its drink has been retyped.

    SO THIS CHECKS THE DRINKS AND NOT THE DATA FILES, and deleting the eleven
    aliases to "finish the job" would break every suggestion this rule has not
    reached. `bottles.yml` is deliberately out of scope.

    The last live case was a TITLE, which is why nothing caught it: every
    ingredient, suggestion and generic had already been retyped, and
    "Plantation Pineapple Daiquiri" was the only trace left -- on a drink whose
    own `item` reads "Planteray pineapple-infused rum" two lines below it.
    Renamed with its file on 2026-08-30.
    """
    checked = 0
    bad = []
    for slug, fm in _load():
        checked += 1
        if "plantation" in slug.lower():
            bad.append(f"{slug}: the FILENAME says plantation")
        haystack = [("title", fm.get("title"))]
        for item in (fm.get("ingredients") or []):
            if not isinstance(item, dict):
                continue
            for key in ("item", "generic", "suggestion", "note"):
                value = item.get(key)
                haystack += [(key, v) for v in
                             (value if isinstance(value, list) else [value])]
        for key, value in haystack:
            if isinstance(value, str) and "plantation" in value.lower():
                bad.append(f"{slug}: {key} = {value!r}")
    assert not bad, (
        "Drinks still writing `plantation`:\n  " + "\n  ".join(bad)
        + "\n\nWrite `Planteray` -- it is the same brand, renamed. The old "
          "spellings stay in bottles.yml as aliases on purpose, so a "
          "suggestion keeps resolving either way; this rule is about what "
          "gets WRITTEN into a drink, not what can be read."
    )
    assert checked, "No drinks were scanned at all, so this compared nothing."


def test_a_qq_note_carries_a_qq_label():
    """A drink note that is unresolved says so on its tab -- #572.

    NOTES ARE `{label, text}` OR A BARE STRING, exactly as a food recipe's are
    (HANDOVER 4) -- and `_layouts/cocktail.html` has rendered both shapes since
    the layout was written, falling back to the literal word "note". Nothing had
    ever used the labelled form, so all 170 notes rendered identically.

    THE SPLIT THAT MATTERS IS NOT TOPIC BUT AUTHORSHIP. 81 of the 170 are the
    ingest audit trail -- "QQ - `generic` values INFERRED, not confirmed", "QQ -
    method step 2 is TRUNCATED in the source" -- and they sat on the page
    labelled "note" beside Helen's own "This drink is incredibly forgiving with
    the rum". One is a remark about the drink; the other is a record that
    something is unresolved, and reading it as the first is the failure.

    ONE LABEL, NOT FIVE. The 81 sort into five kinds (inferred, no unit,
    truncated, glass, mood) and Helen's call was a single `QQ` anyway: the tab
    says "not ruled on yet", which is what `QQ` means everywhere else in this
    repo, and a five-word vocabulary would need its own guard to stop a sixth
    kind arriving untagged.

    THE TEXT KEEPS ITS OWN `QQ - ` PREFIX, which is duplication on the page and
    deliberate. HANDOVER 5's house-style exemption matches `QQ` as a PREFIX on
    the string, and every `grep -rn QQ` in this repo's history has found these
    by their text. Moving the marker into the label alone would fail in the
    direction where a future scanner silently stops seeing them.
    """
    checked = 0
    bad = []
    for slug, fm in _load():
        for note in (fm.get("notes") or []):
            checked += 1
            if isinstance(note, str):
                if note.strip().startswith("QQ"):
                    bad.append(f"{slug}: unlabelled QQ note {note[:60]!r}...")
                continue
            if not isinstance(note, dict):
                continue
            text = str(note.get("text", ""))
            label = note.get("label")
            if text.strip().startswith("QQ") and label != "QQ":
                bad.append(f"{slug}: QQ note labelled {label!r}, not 'QQ'")
            if label == "QQ" and not text.strip().startswith("QQ"):
                bad.append(f"{slug}: labelled QQ but the text does not say so: "
                           f"{text[:60]!r}")
    assert not bad, (
        "QQ notes and their labels disagree:\n  " + "\n  ".join(bad)
        + "\n\nA note whose text begins `QQ` is written as:\n"
          '  - label: "QQ"\n    text: "QQ - ..."\n\n'
          "Both halves, on purpose: the label is what the page shows, the "
          "prefix is what every QQ scanner in this repo matches on. A note "
          "that is Helen's own remark stays a bare string and renders as "
          "\"note\"."
    )
    assert checked, (
        "No drink notes were scanned at all, so this compared nothing -- the "
        "collection had 170 when this was written."
    )


def test_no_method_step_restates_to_serve_or_garnish():
    """A step that opens "Serve" or "Garnish" is another field's fact -- #573.

    THE FIELDS ALREADY EXISTED AND THE DRINKS DISAGREED WITH EACH OTHER, which
    is what #573 means by "we talked about this but it looks like we didn't
    implement it". Mastiha Mojito said `to_serve: "Straw."`; Mai Tai and Coney
    Park Swizzle said `Serve with a straw.` as a method step. One fact, two
    fields, decided per drink by which session last touched it. Don's Own Grog
    and Man o' War went further and restated their own `garnish:` verbatim.

    THE VERB IS THE TEST, NOT THE WORDS. This deliberately does not fire on a
    step that merely NAMES a garnish, and the difference is the whole rule:

        "Float the dehydrated lime slice wheel."     an ACTION -- stays
        "Express lemon zest twist and use as garnish" an ACTION -- stays
        "Garnish with grated nutmeg."                 a RESTATEMENT -- goes

    HANDOVER 9.4 settles which is which: finishing ACTIONS are method steps
    ("top with champagne", "squeeze the twist over the drink"), presentation is
    `to_serve`. An imperative "Garnish with X" instructs you to do the thing the
    `garnish:` list already states, in the way 9.12 describes for naming the
    glass inside a strain step -- variance that looks informative and is not.

    Nothing about this is caught by the build. A duplicated garnish renders
    twice on the page and reads as a page with a redundant last step; a
    presentation fragment stranded in `method` renders as an instruction and
    quietly makes `to_serve` look like a field nobody uses, which is how it sat
    empty on 111 of 114 drinks.
    """
    checked = 0
    bad = []
    for slug, fm in _load():
        method = fm.get("method")
        for step in (method if isinstance(method, list) else [method] if method else []):
            if not isinstance(step, str):
                continue
            checked += 1
            verb = re.match(r"\s*(serve|garnish)\b", step, re.I)
            if verb:
                field = "to_serve" if verb.group(1).lower() == "serve" else "garnish"
                bad.append(f"{slug}: {step!r} -> {field}")
    assert not bad, (
        "Method steps holding another field's fact:\n  " + "\n  ".join(bad)
        + "\n\nA step OPENING with \"Serve\" is presentation and belongs in "
          "`to_serve` -- one terse line, as \"Straw.\" and \"Without ice.\" "
          "already are. A step opening with \"Garnish\" restates `garnish:` "
          "and should simply go.\n\nA step that DOES something to the garnish "
          "is fine and is not what this catches -- \"Float the lime wheel\", "
          "\"Express the zest over the drink\". Lead with the real verb."
    )
    assert checked, (
        "No method steps were scanned at all, so this compared nothing. Every "
        "drink has a `method`; an empty scan means the loader or the key name "
        "has moved."
    )


def test_optional_is_a_real_boolean():
    """`optional` marks an ingredient the drink survives without -- #570.

    A REAL BOOLEAN, NEVER A QUOTED STRING. The exact lesson `meta.awaiting_fix`
    paid for in HANDOVER 4.0: `optional: "true"` is a string, and every
    truthiness test in Liquid and in Python agrees a non-empty string is true --
    so a QUOTED value happens to work here and stops working the moment anything
    compares it, while `optional: "false"` is true today and reads as false to
    every human who looks at it. There is no spelling of this field that fails
    loudly on its own, so the shape is guarded instead.

    `false` is permitted and means the same as absent. It is not written into
    any drink -- writing "this is not optional" on 617 entries is noise -- but a
    drink that has been thought about and answered no is a legitimate thing to
    record, and forbidding it would make the absence ambiguous in the other
    direction.
    """
    seen = 0
    bad = []
    for slug, fm in _load():
        for item in (fm.get("ingredients") or []):
            if not isinstance(item, dict) or "optional" not in item:
                continue
            seen += 1
            if not isinstance(item["optional"], bool):
                bad.append(
                    f"{slug}: {item.get('item') or item.get('generic')!r} has "
                    f"optional: {item['optional']!r} "
                    f"({type(item['optional']).__name__}, not bool)"
                )
    assert not bad, (
        "`optional` must be a real YAML boolean -- bare true or false, never "
        "quoted:\n  " + "\n  ".join(bad)
    )
    assert seen, (
        "No ingredient anywhere carries `optional`, so this check compared "
        "nothing. Two entries had it when the field was added (#570): Espresso "
        "Martini's cane sugar syrup and Gunmetal Blue's gentian liqueur. If the "
        "field has genuinely been retired, delete this test and its sibling "
        "test_no_ingredient_says_optional_in_prose rather than leaving both "
        "reporting green over an empty scan."
    )


def test_no_ingredient_says_optional_in_prose():
    """Optionality is the `optional` field and nothing else -- #570.

    THIS IS THE HALF THAT MAKES THE FIELD STICK, and the reason it exists is
    that the field was invented to replace exactly this: both live cases said
    `item: "Gentian liqueur (optional)"` before #570, because `item` was the
    only slot that would hold a fact no field had. #544 calls that out as the
    one parenthetical in `item` that sorted into no other field.

    A drink that writes the word back into prose renders it as part of the
    ingredient's NAME, and nothing else notices: the ingredient line prints
    whatever the generic says, so "sugar syrup (optional)" would read as a
    category, sit in the search pool as one, and never reach `optional`'s own
    rendering. Silent in every direction.

    Scoped to the ingredient fields, NOT to the drink's prose. A method step or
    a note may discuss what is optional in a sentence -- "the float is optional
    if you are out of Wray" is a reason, which is a note's whole job.
    """
    checked = 0
    bad = []
    for slug, fm in _load():
        for item in (fm.get("ingredients") or []):
            if not isinstance(item, dict):
                continue
            for key in ("item", "generic", "suggestion"):
                value = item.get(key)
                for text in (value if isinstance(value, list) else [value]):
                    if not isinstance(text, str):
                        continue
                    checked += 1
                    if re.search(r"\boptional\b", text, re.I):
                        bad.append(f"{slug}: {key} = {text!r}")
    assert not bad, (
        "An ingredient says it is optional in prose rather than in the "
        "field:\n  " + "\n  ".join(bad)
        + "\n\nWrite `optional: true` on the entry and take the word out of "
          "the text. A word inside `item`/`generic`/`suggestion` becomes part "
          "of the ingredient's name -- it reaches the card, the search pool "
          "and the recipe line as though it were the category."
    )
    assert checked, (
        "No ingredient text was scanned at all, so this check compared "
        "nothing. It reads `item`, `generic` and `suggestion` across every "
        "drink; an empty scan means the loader or the key names have moved."
    )


def test_to_serve_is_a_string():
    """`to_serve` is one line of presentation, never a list.

    NEW FIELD, NEW RISK. Not a single drink set `to_serve` until 2026-08-26,
    when #291's three fragments moved into it -- so this field went from
    documented-but-unused to live, with nothing checking its shape.

    A LIST DOES NOT FAIL LOUDLY HERE. `_layouts/cocktail.html` renders it as
    `{{ page.to_serve | markdownify | remove: '<p>' }}`, and Liquid will
    happily stringify a list into that filter chain rather than raise -- the
    same class of quiet nonsense as the `glass` scalar iterating as characters.
    `glass`, `garnish` and `mood` each have a shape guard for exactly this
    reason; this field had none because it had no data.
    """
    bad = [f"{slug}: to_serve is a {type(fm['to_serve']).__name__}"
           for slug, fm in _load()
           if "to_serve" in fm and not isinstance(fm["to_serve"], str)]
    assert not bad, (
        "to_serve must be a string:\n  " + "\n  ".join(bad)
        + "\n\nIt is ONE line of presentation -- \"over crushed ice, with a "
          "straw\" -- not an ordered list of steps. Steps are `method`."
    )


def test_glass_is_a_list():
    """`glass` became an ordered list on 2026-08-17 so a drink could name more
    than one acceptable serve. A leftover scalar still renders -- Liquid
    iterates a string's characters happily enough to produce nothing visible --
    so nothing else would catch one.
    """
    bad = [f"{slug}: glass is a {type(fm['glass']).__name__}"
           for slug, fm in _load()
           if "glass" in fm and not isinstance(fm["glass"], list)]
    assert not bad, (
        "glass must be a list, first entry preferred:\n  " + "\n  ".join(bad)
    )


def test_every_glass_value_is_in_the_vocabulary():
    """A drink naming a glass `glasses.yml` has never heard of renders NOTHING.

    #500. The glass layer is guarded thoroughly in one direction -- every
    mapped glass names a real icon, `all_icons` matches the directory both
    ways, every icon has a height. All of that guards glasses.yml against
    itself. Nothing guarded the DRINKS against glasses.yml, so a typo produced
    a drink with no glass drawing and no complaint from anywhere.

    THE SILENCE IS BY DESIGN, WHICH IS WHY IT NEEDS A TEST RATHER THAN A FIX.
    "Absent means no icon" is the correct default -- it is what stops a missing
    key becoming a broken image, and glasses.yml's own header says so -- but it
    cannot tell a deliberate gap from a mistake. That was a fair trade while
    three values were deliberately unmapped. It is a bad one now `any` is the
    last of them: an unrecognised glass is far likelier to be a typo than a
    decision.

    `any` WAS AN EXEMPTION HERE AND IS NOW RETIRED, 2026-08-27. It meant "no
    requirement", and exactly one drink ever used it -- Daisy de Santiago, as
    `[collins, any]`, i.e. "anything, but preferably a Collins". Helen: "when
    someone tells me to use an old fashioned glass I always automatically
    assume I can use any glass I like, so there's no need to have 'any' as a
    glass type."

    That is the argument that kills it. The freedom `any` encoded is one she
    applies to EVERY glass spec already, so recording it on one drink said
    nothing true about that drink and false about the other 113. Dropping it
    from Daisy left `[collins]`, which is what the source meant anyway --
    "preferably a Collins" was always the whole content.

    There is now NO exempt value: every glass a drink names must be in `icons:`.

    Passes on arrival: all 19 distinct values in the collection are known
    today. That is what makes it worth adding now -- it costs nothing to
    introduce and catches the next one for free.
    """
    g = _glasses()
    icons = g.get("icons") or {}
    assert icons, "glasses.yml has no `icons:` -- see the sibling tests."

    # No exemptions. `any` was the last one and was retired 2026-08-27 -- see
    # the docstring. A new exemption here should be argued for in an issue
    # first: the whole value of this check is that an unrecognised glass is a
    # typo rather than a decision.
    deliberately_unmapped = set()

    unknown = {}
    for slug, fm in _load():
        for value in fm.get("glass") or []:
            key = str(value).strip().lower()
            if key in icons or key in deliberately_unmapped:
                continue
            unknown.setdefault(key, []).append(slug)

    # Six icons are drawn and normalised but no spelling reaches them
    # (hot-toddy, julep-cup, margarita, pina-colada, sherry, shot -- the
    # `UNUSED ICONS` note in glasses.yml says why). For those, the generic
    # advice below is actively WRONG: it says "and artwork", and the artwork
    # already exists. Someone taking it at its word draws a second margarita,
    # or maps the value to `coupe` and never learns `margarita.svg` was there.
    # So say so, per value, at the moment it matters.
    lines = []
    for value, drinks in sorted(unknown.items()):
        line = f"{value!r} -- {', '.join(sorted(drinks))}"
        stem = value.replace(" ", "-")
        if (GLASS_ICON_DIR / f"{stem}.svg").is_file():
            line += (f"\n      ARTWORK ALREADY EXISTS: {stem}.svg. This needs "
                     f"a key in `icons:`, NOT a new drawing.")
        lines.append(line)

    assert not unknown, (
        "glass value(s) not in _data/cocktails/glasses.yml `icons:`:\n  "
        + "\n  ".join(lines)
        + "\n\nThe drink renders NO glass icon, silently. Either it is a typo "
          "and the drink should be retyped, or it is a real glass and needs a "
          "key in `icons:` (and artwork unless flagged above, and a heights_mm "
          "tests will say so). There is no longer a value meaning 'no "
          "requirement' -- `any` was retired on 2026-08-27, because every "
          "glass spec is already a suggestion."
    )


# The drinks that named no glass at all on 2026-08-27, when Helen settled that
# every recipe should have one (#491). Sixteen of 114. Listed rather than
# tolerated silently, and listed rather than fixed, because which glass a drink
# wants is her call and not derivable -- a Zombie is not a Bellini.
#
# THE LIST ONLY SHRINKS. The test fails if a drink joins it, and fails again if
# a drink on it gets a glass and is not removed, so it cannot quietly stop
# describing the collection.
#
# WHO NAMED WHAT, 2026-08-30 -- kept because each is a ruling and several
# turned on something only Helen knows.
# kamaniwanalaya came off on 2026-08-30: Helen gave it a Collins, a
# pineapple wedge, a maraschino cherry and a bouquet of mint sprigs. Fifteen
# left of the original sixteen.
#
# FIVE MORE CAME OFF THE SAME DAY, Helen ruling on each in turn:
#   anitas-attitude-adjuster  highball, "whatever we say for Long Island
#                             Iced Tea" -- it is that drink with sparkling
#                             wine in place of the cola, and says so in its
#                             own tagline
#   banana-boulevardier       double old fashioned over the ice block its
#                             method already asks for, or up in a coupe
#   biggles-sidecar           coupe
#   cobra-effect              tiki mug -- "or anything you like because
#                             it's a mad colour and you might want to see
#                             it", hence the coupe second
#   copenhagen-special        coupe, and it gained the orange zest twist
#                             she named with it
#   cynar-toronto             old fashioned
#   el-mediterraneo           collins
#   georgetown-punch          highball -- she wondered about a sling,
#                             "they're awesome and underused", and does not
#                             own one; recorded here rather than as data
#   mai-tai-diffords-recipe   double old fashioned usually, tiki mug
#                             sometimes, so both in that order
#   milliners-punch           highball. "I made this up so I can say what
#                             I like!"
#   minty-pentones            old fashioned
#   modern-zombie-makes-2     collins -- "zombie glass really", which the
#                             vocabulary does not have and she does not
#                             own, so the drink carries a note saying so
#   pear-...-bellini          flute, which its own method already said
#   tiki-max                  tiki mug
#   zombie-intoxica           tiki mug
#
# AND THAT IS ALL SIXTEEN. The set is empty and stays declared: it is what
# `test_the_glassless_list_has_no_stale_entries` reads, and that check now
# asserts the emptiness rather than trusting it -- an empty registry that
# nothing looks at is how a closed backlog quietly reopens.
#
# `set()` AND NOT `{}`: an empty pair of braces is a DICT, which is what
# this became when the last name came out. Nothing about the braces says
# so -- the tests below simply started failing with "unsupported operand
# type(s) for -: 'dict' and 'set'", which is at least a loud way to learn.
GLASSLESS_ON_2026_08_27 = set()


def test_every_drink_names_a_glass():
    """#491. Helen, 2026-08-27: "All recipes should have a glass."

    A drink with no `glass` renders no icon, and on a drink page the glass is
    the hero -- it is drawn as tall as the whole title block. So an empty
    `glass` is not a missing garnish-sized detail, it is a page with a hole
    where its main image goes, and 16 of 114 have one.

    WHY THIS IS A RATCHET AND NOT A FIX. Which glass a drink wants is Helen's
    knowledge, not something derivable from the ingredients -- and guessing
    would be worse than the gap, because a wrong glass looks exactly as
    confident as a right one. So the existing sixteen were recorded and the
    check bit on the seventeenth.

    ALL SIXTEEN ARE DONE, 2026-08-30. She named every one, in three batches,
    given the ingredients and the total volume of each -- and several answered
    themselves once the volume was in front of her: the Bellini's own method
    already said "add 25 ml syrup to a champagne flute", and Banana
    Boulevardier's said "over a large ice block". The exemption set is empty,
    so this test is now simply "every drink names a glass".

    NOTE THE TEST ABOVE NO LONGER EXEMPTS `any`. The two changes are the same
    decision from both ends: every drink names a glass, and there is no value
    meaning "it does not matter".
    """
    missing = {slug for slug, fm in _load() if not (fm.get("glass") or [])}

    new = sorted(missing - GLASSLESS_ON_2026_08_27)
    assert not new, (
        "drink(s) with no `glass`:\n  " + "\n  ".join(new)
        + "\n\nEvery recipe should have a glass (#491). On a drink page the "
          "glass is drawn as tall as the title block, so an empty one leaves a "
          "hole where the page's main image goes."
    )


def test_the_glassless_list_has_no_stale_entries():
    """GLASSLESS_ON_2026_08_27 only shrinks -- a drink that gains a glass comes off.

    SPLIT OUT OF THE RATCHET ABOVE, 2026-08-29, #540. The two halves ask
    opposite-facing questions and only one of them survives a partial corpus:
    "is there a seventeenth glassless drink" is true of each drink on its own,
    while "is every name on this list still glassless" needs the whole book. In
    CI the drafts are absent, so all sixteen names would read as fixed. See
    WHOLE_COLLECTION_ONLY at the top of this file.

    IT IS EMPTY NOW, and that is checked rather than assumed. An exemption set
    that has emptied is the moment a ratchet stops doing anything, and an
    unwatched empty set is how one gets quietly refilled -- so the assert below
    fails if a name is ever added back. Deleting both the set and this test is
    the right move only once nothing can regress; the sibling above is what
    keeps the collection honest either way.
    """
    _require_whole_collection("GLASSLESS_ON_2026_08_27")
    missing = {slug for slug, fm in _load() if not (fm.get("glass") or [])}
    fixed = sorted(GLASSLESS_ON_2026_08_27 - missing)
    assert not fixed, (
        "these now HAVE a glass and should come off GLASSLESS_ON_2026_08_27:\n  "
        + "\n  ".join(fixed)
        + "\n\nThe list only shrinks. Leaving a fixed drink on it means the "
          "list stops describing the collection, and the next real gap hides "
          "among the stale entries."
    )
    assert not GLASSLESS_ON_2026_08_27, (
        "GLASSLESS_ON_2026_08_27 has entries again:\n  "
        + "\n  ".join(sorted(GLASSLESS_ON_2026_08_27))
        + "\n\nIt emptied on 2026-08-30 when Helen named the last of the "
          "sixteen. A new drink with no glass should fail "
          "test_every_drink_names_a_glass and be given one -- not be added "
          "here. This set exists to record a backlog that is now closed."
    )


def test_every_mood_belongs_to_exactly_one_group():
    """The index asks MOOD and HASSLE as separate questions, and the split
    lives in `taxonomy.yml`'s `mood_groups` rather than in the template.

    THE FAILURE THIS CATCHES IS A DISAPPEARING BUTTON. cocktails/index.html
    renders each group by iterating its list, so a mood added to `moods:`
    without being added to a group renders NOWHERE -- no button, no error, and
    the drinks carrying it become unreachable by mood. That is the same class
    of silent gap as an unmapped glass (#500): the page is valid, the build is
    green, and a filter simply does not exist.

    Both directions, because both have a failure. An ungrouped mood vanishes
    from the page; a grouped name that is not a real mood renders a button that
    matches nothing, which is worse than no button because it looks like an
    empty collection rather than a typo.

    Overlap is checked too. A mood in both groups would render twice and toggle
    both copies from one click, since the script keys on the mood name.
    """
    tax = _taxonomy()
    moods = set(tax.get("moods") or {})
    assert moods, "taxonomy.yml declares no moods -- this check has nothing to do."

    groups = tax.get("mood_groups") or {}
    assert groups, (
        "taxonomy.yml has no `mood_groups`. The index renders its filter "
        "sections from it, so without it the page has no mood buttons at all."
    )

    seen = {}
    for group, names in groups.items():
        for name in names or []:
            seen.setdefault(name, []).append(group)

    ungrouped = sorted(moods - set(seen))
    assert not ungrouped, (
        "mood(s) in `moods:` but in no group:\n  " + "\n  ".join(ungrouped)
        + "\n\nThe index iterates the groups, so these render no button and "
          "the drinks carrying them cannot be filtered for. Add each to "
          "`mood_groups.mood` (what the drink IS) or `mood_groups.hassle` "
          "(what it COSTS)."
    )

    phantom = sorted(set(seen) - moods)
    assert not phantom, (
        "grouped name(s) that are not declared moods:\n  " + "\n  ".join(phantom)
        + "\n\nThese render a button that can never match a drink, which "
          "reads as an empty collection rather than as the typo it is."
    )

    both = sorted(n for n, gs in seen.items() if len(gs) > 1)
    assert not both, (
        "mood(s) in more than one group: " + ", ".join(both)
        + "\n\nEach would render twice, and one click would toggle both "
          "copies, since the script keys on the mood name."
    )


def test_garnish_is_a_list():
    """Same reasoning as `glass` and `mood`: a bare string iterates in Liquid as
    its own characters, which renders as nothing visible rather than as an
    error. Cobra's Fang is why `garnish` is a list at all -- a mint sprig AND a
    lime wheel -- and a leftover scalar would go unnoticed.
    """
    bad = [f"{slug}: garnish is a {type(fm['garnish']).__name__}"
           for slug, fm in _load()
           if "garnish" in fm and not isinstance(fm["garnish"], list)]
    assert not bad, "garnish must be a list:\n  " + "\n  ".join(bad)


def test_no_garnish_is_stated_as_none_and_nothing_else():
    """`["none"]` means DECIDED: this drink takes no garnish. `[]` means nobody
    has filled it in. Helen settled that convention on 2026-08-26, and the
    collection already followed it -- 15 drinks say `none` (the Sazerac among
    them, deliberately, from its own source row) against 18 genuinely empty.

    HANDOVER §9.5 SAYS THE OPPOSITE, claiming both cases are "currently
    flattened to []" and listing the choice as an open question. That was true
    once and has not been for some time; the file it describes is the authority,
    per §11.2. This test is what stops the two conventions drifting apart again.

    WHAT IT ACTUALLY GUARDS is the risk §9.5 correctly identified: that `none`
    "would pollute any future garnish vocabulary with a fake member". It cannot
    now, because it may only ever appear ALONE. A drink with `["none", "lime
    wheel"]` is a contradiction, and a drink with `["None"]` is a second
    spelling that any future vocabulary would have to carry twice.
    """
    bad = []
    for slug, fm in _load():
        garnish = fm.get("garnish")
        if not isinstance(garnish, list):
            continue          # test_garnish_is_a_list owns that failure
        lowered = [str(g).strip().lower() for g in garnish]
        if "none" not in lowered:
            continue
        if len(garnish) > 1:
            bad.append(f"{slug}: {garnish!r} -- `none` alongside a real garnish")
        elif garnish[0] != "none":
            bad.append(f"{slug}: {garnish[0]!r} -- must be exactly \"none\"")
    assert not bad, (
        "Garnish problems:\n  " + "\n  ".join(bad)
        + "\n\n`none` states a DECISION and must stand alone, lowercase. Use "
          "`[]` for a garnish nobody has chosen yet -- absent is not the same "
          "as deliberately nothing."
    )


def _glasses():
    return yaml.safe_load(
        (ROOT / "_data" / "cocktails" / "glasses.yml").read_text(encoding="utf-8")
    )


GLASS_ICON_DIR = ROOT / "_includes" / "icons" / "glasses"


def test_drinks_use_the_canonical_glass_spelling():
    """A drink must write the canonical name, not one of its aliases.

    THIS REVERSES A RULE THIS FILE USED TO STATE. glasses.yml said outright
    that "a drink is never wrong for using the other word", and for nine months
    that was the design. Helen retired it on 2026-08-26: "I decided to go with
    old fashioned rather than rocks as the canonical name, so recipes that
    still have rocks are fine to break a test."

    THE ALIAS MAP IN `icons:` IS UNAFFECTED, and keeping both is not a
    contradiction. The aliases do two jobs a rule cannot: they keep a drink
    rendering if one slips through, and they absorb the spreadsheet's own
    spellings on ingest, where the variance arrives whether or not the repo
    approves of it. This rule governs what is WRITTEN into a drink; the alias
    map governs what can be READ.

    The vocabulary comes entirely from `canonical_glasses`, so adding a pair
    there is what makes it enforced -- there is no second list here to keep in
    step. An alias absent from that map is permitted, which is why `martini` /
    `martini glass` does not fail: it is undecided, not blessed.
    """
    canonical = _glasses().get("canonical_glasses") or {}
    assert canonical, (
        "glasses.yml has no `canonical_glasses:` map, so this check enforces "
        "nothing. If the canonical vocabulary was abandoned, delete this test "
        "deliberately rather than letting it pass while checking nothing."
    )
    bad = []
    for slug, fm in _load():
        for value in (fm.get("glass") or []):
            want = canonical.get(str(value).lower())
            if want and str(value) != want:
                bad.append(f"{slug}: {value!r} -> should be {want!r}")
    assert not bad, (
        f"{len(bad)} drink(s) using a non-canonical glass spelling:\n  "
        + "\n  ".join(sorted(bad))
        + "\n\nThese all render the correct icon -- the alias map sees to "
          "that -- so this is about what the data SAYS, not what it draws. "
          "Retype the drink; do not add the alias to `canonical_glasses` to "
          "make this pass."
    )


def test_every_mapped_glass_names_an_icon_that_exists():
    """A key pointing at a missing file is worse than a missing key.

    A MISSING KEY COSTS AN ICON AND NOTHING ELSE -- the layout's
    absent-means-no-icon rule handles it, and the page renders fine without
    one. A key naming a file that is NOT THERE is the dangerous direction: it
    sets `glass_icon` to a non-empty string, so the layout takes the branch
    that builds `icons/glasses/<name>.svg` and hands it to {% include %}. That
    is a HARD BUILD FAILURE, not a blank space, and it has already happened
    once here in its empty-string form -- `glass_icon = ""` produced
    "File contains invalid characters or sequences: icons/glasses/.svg".

    Checked against the filesystem rather than against all_icons, because
    all_icons is itself a written-down list and could be wrong in the same way.
    """
    icons = _glasses()["icons"]
    assert icons, "glasses.yml has no `icons:` map -- this test would pass vacuously."
    missing = sorted(
        f"{spelling!r} -> {stem}.svg"
        for spelling, stem in icons.items()
        if not (GLASS_ICON_DIR / f"{stem}.svg").is_file()
    )
    assert not missing, (
        "glasses.yml maps a glass to an icon file that does not exist:\n  "
        + "\n  ".join(missing)
        + "\n\nThis is not a cosmetic gap. A non-empty name sends the layout "
          "down the include branch and the BUILD FAILS. Either add the SVG to "
          "_includes/icons/glasses/ or remove the key -- an unmapped glass "
          "renders no icon, which is the intended fallback."
    )


def test_all_icons_matches_the_icon_directory():
    """The written-down inventory must equal the directory, both directions.

    all_icons EXISTS ONLY BECAUSE LIQUID CANNOT READ A DIRECTORY. `_includes/`
    is never copied to the site, so it is not in `site.static_files` either,
    and a template therefore has no way to ask what artwork exists -- it can
    only look up what a key already names. That makes the most interesting
    question invisible to the swatch page: which icons are UNREACHABLE.

    Duplicating a directory listing into YAML is a rot risk taken deliberately,
    and this test is the whole reason it is acceptable. It has to fail in BOTH
    directions: an icon added without a list entry is invisible to the swatch
    page (the failure the list exists to prevent), and a list entry whose file
    has gone makes the swatch page ask {% include %} for a missing file, which
    fails the build exactly as above.
    """
    listed = _glasses().get("all_icons") or []
    assert listed, (
        "glasses.yml has no `all_icons:` list. _dev/glasses.html iterates it "
        "and would render an empty swatch page while passing every check."
    )
    on_disk = sorted(p.stem for p in GLASS_ICON_DIR.glob("*.svg"))
    assert on_disk, (
        f"No SVGs found in {GLASS_ICON_DIR.relative_to(ROOT)} -- this test "
        f"would pass while checking nothing."
    )
    undeclared = sorted(set(on_disk) - set(listed))
    phantom = sorted(set(listed) - set(on_disk))
    assert not undeclared and not phantom, (
        "glasses.yml `all_icons` has drifted from the icon directory.\n"
        + (f"  on disk but not listed: {undeclared}\n" if undeclared else "")
        + (f"  listed but not on disk: {phantom}\n" if phantom else "")
        + "\nAdd or remove the entry. Icons are regenerated wholesale by "
          "scripts/normalise_glass_icons.py from tmp/cocktail-glasses/, so a "
          "drawing whose source is deleted disappears from here silently -- "
          "which is how shot-2.svg went missing without a single test noticing."
    )


def test_every_icon_has_a_real_world_height():
    """`heights_mm` must cover every icon, and name no icon that is not there.

    THE FAILURE IS A SILENT ZERO, not an error. /dev/glasses/ sizes its
    relative-scale view by these millimetres, and Liquid resolves a missing key
    to nil; `nil | times: 1.0` is 0, so a glass with no height renders at zero
    height -- an invisible gap in a row of glasses, with nothing to say why.
    The same nil-arithmetic family as `drink.glass.size == 0` counting zero
    unglassed drinks while 28 sat unglassed.

    A phantom entry is milder but still wrong: it inflates the tallest-glass
    figure the whole row is scaled against, so every icon silently shrinks.

    These numbers are PROVISIONAL and Claude wrote them (2026-08-18). Issue #295
    -- the glasses Helen owns, with volumes -- supersedes them. This test only
    asserts coverage, never the values: a wrong height is a judgement to be
    corrected by eye, not something a test can know.
    """
    g = _glasses()
    heights = g.get("heights_mm") or {}
    listed = g.get("all_icons") or []
    assert heights, (
        "glasses.yml has no `heights_mm:`. The relative-scale view on "
        "/dev/glasses/ would render every icon at zero height."
    )
    assert listed, "glasses.yml has no `all_icons:` -- see the sibling test."
    missing = sorted(set(listed) - set(heights))
    phantom = sorted(set(heights) - set(listed))
    assert not missing and not phantom, (
        "glasses.yml `heights_mm` does not cover the icon set.\n"
        + (f"  icons with no height: {missing}\n" if missing else "")
        + (f"  heights for no icon:  {phantom}\n" if phantom else "")
        + "\nAn icon with no height renders at ZERO height on /dev/glasses/ "
          "-- an invisible gap, not an error. Add a typical height in mm; it "
          "does not need to be exact, and #295 will replace the lot."
    )
    bad = sorted(f"{k}={v!r}" for k, v in heights.items()
                 if not isinstance(v, (int, float)) or v <= 0)
    assert not bad, (
        "heights_mm values must be positive numbers, not strings:\n  "
        + "\n  ".join(bad)
        + "\n\nA quoted number is a string, and Liquid's `times` turns a "
          "non-numeric string into 0 -- the same invisible-gap failure."
    )


# `heights_mm` sizes an icon by its VIEWBOX, not by its ink, so a drawing that
# does not fill its own canvas renders smaller than one that does at the same
# declared height.
#
# NOT A UNIT: this is the fraction of the canvas HEIGHT that the ink spans.
#
# THE LIST IS EMPTY AND SHOULD STAY EMPTY. It held three entries for a few
# hours on 2026-08-27 -- goblet at 69.5%, coupe at 82.5%, old-fashioned-double
# at 85.5% -- and then `scripts/normalise_glass_icons.py` learned to fit every
# canvas to its own artwork, which fixed all three at the source instead. An
# entry appearing here again means a drawing reached _includes/ without going
# through the normaliser, which is worth knowing about in itself.
KNOWN_LOOSE_VIEWBOXES = {}
VIEWBOX_FILL_FLOOR = 92.0
VIEWBOX_FILL_TOLERANCE = 3.0


def test_no_glass_artwork_has_a_slack_viewbox():
    """#503. An icon must fill its own canvas, or it renders smaller than declared.

    `heights_mm` says how tall a glass is in the real world and the template
    scales the icon to match. But it scales the VIEWBOX, and the viewBox is
    whatever the drawing was saved with -- `scripts/normalise_glass_icons.py`
    deliberately preserves it ("the viewBox stays, so CSS decides"). So ink
    sitting in the middle of a roomy canvas renders short, by exactly the
    fraction of the canvas it leaves empty, and nothing anywhere says so.

    THIS IS NOT VISIBLE BY READING THE FILES. It was found the first time by two
    glasses looking wrong beside each other, and the viewBox numbers actively
    misled -- see the note on KNOWN_LOOSE_VIEWBOXES above. It has to be
    measured, which is why this test rasterises.

    IMPORTING THE RASTERISER IS FINE HERE, and is not the mistake
    tests/test_reference_data.py warns about when it reimplements
    build_cooking_methods.py's parser rather than sharing it. That warning is
    about a test agreeing with the generator it is checking. Nothing generates
    these SVGs from the rasteriser -- Helen draws them, and the normaliser moves
    XML around without ever rasterising -- so the measurement is independent of
    the thing being measured.

    THE TOLERANCE IS TWO-SIDED ON PURPOSE. A grandfathered icon that gets worse
    fails, and one that gets FIXED also fails, telling you to drop it from the
    list. A one-sided ratchet quietly keeps stale entries forever, which is how
    a grandfather list stops describing anything real.
    """
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import svgrender
    except ImportError:  # pragma: no cover
        pytest.skip("scripts/svgrender.py not importable")

    icons = sorted(GLASS_ICON_DIR.glob("*.svg"))
    assert icons, f"no SVGs in {GLASS_ICON_DIR.relative_to(ROOT)}"

    fills = {}
    for path in icons:
        paths, viewbox, translate, _ = svgrender.parse_icon(path)
        # A hairline stroke and no supersampling: this measures where the
        # ARTWORK is, and a fat stroke would inflate the box by its own width.
        width, height, gray = svgrender.render(
            paths, viewbox, 200, stroke=0.4, translate=translate, ss=1)
        rows = [i // width for i, v in enumerate(gray) if v < 128]
        assert rows, (
            f"{path.name} rasterised to NOTHING. Either the artwork draws "
            f"outside its own viewBox, or parse_icon missed the <g transform> "
            f"-- both of which render blank on the site too."
        )
        fills[path.stem] = (max(rows) - min(rows) + 1) / height * 100

    stale = sorted(set(KNOWN_LOOSE_VIEWBOXES) - set(fills))
    assert not stale, (
        f"KNOWN_LOOSE_VIEWBOXES names icons that no longer exist: {stale}. "
        f"Drop them."
    )

    problems = []
    for name, fill in sorted(fills.items()):
        if name in KNOWN_LOOSE_VIEWBOXES:
            was = KNOWN_LOOSE_VIEWBOXES[name]
            if abs(fill - was) > VIEWBOX_FILL_TOLERANCE:
                verb = "IMPROVED" if fill > was else "GOT WORSE"
                problems.append(
                    f"{name}: {verb} -- grandfathered at {was:.1f}%, now "
                    f"{fill:.1f}%. If it is fixed, remove it from "
                    f"KNOWN_LOOSE_VIEWBOXES; if worse, that is a regression.")
        elif fill < VIEWBOX_FILL_FLOOR:
            problems.append(
                f"{name}: ink spans only {fill:.1f}% of its viewBox height, so "
                f"it renders at {fill / 100:.2f}x its declared heights_mm.")

    assert not problems, (
        "glass artwork with a slack viewBox:\n  " + "\n  ".join(problems)
        + f"\n\nThe set median is 97.5% and the floor is "
          f"{VIEWBOX_FILL_FLOOR:.0f}%. `heights_mm` scales the VIEWBOX, so "
          f"empty canvas is lost height -- the glass renders short beside its "
          f"neighbours and its declared millimetres become a lie. Fix by "
          f"cropping the viewBox to the ink (the paths and their <g transform> "
          f"do not move), or grandfather it above with a reason."
    )


def test_the_icon_parser_applies_nested_transforms():
    """#599. A <g> inside a <g> composes, and reading only the outer one is the
    bug this whole cluster came from.

    IT IS A SYNTHETIC SVG ON PURPOSE. Asserting against a real icon would only
    say that today's drawings parse the way they parse; this states the rule,
    so it still bites if every nested drawing is later flattened away. The
    numbers are worked by hand: the inner matrix doubles x and shifts y by 10,
    the outer group then translates by (100, 1000), so (1, 2) lands at
    (2 + 100, 2 + 10 + 1000).
    """
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import svgrender
    except ImportError:  # pragma: no cover
        pytest.skip("scripts/svgrender.py not importable")

    svg = (
        '<svg viewBox="0 0 10 10">'
        '  <g transform="translate(100,1000)">'
        '    <g transform="matrix(2,0,0,1,0,10)">'
        '      <path d="M 1,2 L 1,2" />'
        '    </g>'
        '  </g>'
        '</svg>'
    )
    paths, viewbox, translate, _ = svgrender.parse_icon_text(svg, "synthetic")
    x0, y0, x1, y1 = svgrender.ink_bbox_units(paths, viewbox, translate)

    assert (round(x0, 6), round(y0, 6)) == (102.0, 1012.0), (
        f"the parser put the point at ({x0}, {y0}); composing both groups puts "
        f"it at (102.0, 1012.0). Applying only the outer <g transform> gives "
        f"(101.0, 1002.0), which is the exact fault behind issue #599: four "
        f"icons nest a matrix group holding the bowl, and every measurement "
        f"taken through this parser read those bowls in the wrong place."
    )
    assert translate == (0.0, 0.0), (
        f"parse_icon_text returned translate={translate}. It bakes every "
        f"ancestor transform into the path data and must report none left to "
        f"apply, or a caller adds the outer offset a second time."
    )


# The margin scripts/normalise_glass_icons.py pads a fitted canvas with, in
# user units. Ink is allowed to sit this far inside the frame and no distance
# at all outside it.
VIEWBOX_MARGIN = 1.4


def test_no_glass_artwork_is_drawn_outside_its_viewbox():
    """#599. A drawing must fit inside its own canvas, not merely fill it.

    THIS IS THE OTHER DIRECTION FROM test_no_glass_artwork_has_a_slack_viewbox,
    and neither substitutes for the other. That one rasterises INSIDE the
    viewBox and measures what fraction of the canvas the ink spans, so it
    catches a canvas bigger than its drawing -- and is structurally incapable of
    seeing a drawing bigger than its canvas, because ink outside the frame is
    simply not drawn into the raster it measures. Every icon scored 96-100% on
    it while four had artwork hanging outside.

    WHY IT MATTERS RATHER THAN BEING TIDINESS. `heights_mm` scales the VIEWBOX,
    so ink outside the frame is height the template never accounted for: the
    coupe was declared 150 mm and drew as if 179, the goblet 175 and drew as if
    259 -- taller than the flute, which is the tallest glass in the file. And
    because a root <svg> only clips by UA-stylesheet default, `.drink-card-glass
    svg { overflow: visible }` (added so a stroke on the frame edge is not
    sheared) meant all of it painted, hanging off the top of the panel. Helen
    reported the coupe sitting high on a card; this is what that was.

    HOW IT HAPPENS, so a red here is read correctly. Helen builds a glass by
    editing an existing drawing, and Inkscape keeps the previous canvas silently
    even when it reports the document as resized -- so the drawing arrives in a
    frame belonging to a different glass. That is not carelessness and cannot be
    fixed by remembering: the normaliser fits every canvas to its own artwork on
    the way in, and this is the check that the fitting worked.

    THE FIX IS NEVER TO EDIT THE PATH DATA. Re-run the fit (fit_viewbox rewrites
    only the viewBox attribute); the artwork does not move.
    """
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import svgrender
    except ImportError:  # pragma: no cover
        pytest.skip("scripts/svgrender.py not importable")

    icons = sorted(GLASS_ICON_DIR.glob("*.svg"))
    assert icons, f"no SVGs in {GLASS_ICON_DIR.relative_to(ROOT)}"

    problems = []
    for path in icons:
        paths, viewbox, translate, _ = svgrender.parse_icon(path)
        x0, y0, x1, y1 = svgrender.ink_bbox_units(paths, viewbox, translate)
        vx, vy, vw, vh = viewbox
        outside = {
            "left": vx - x0, "right": x1 - (vx + vw),
            "above": vy - y0, "below": y1 - (vy + vh),
        }
        worst = {k: v for k, v in outside.items() if v > 0.01}
        if worst:
            over = ", ".join(f"{v:.2f} units {k}" for k, v in sorted(worst.items()))
            grew = (max(worst.values()) + VIEWBOX_MARGIN) / vh * 100
            problems.append(
                f"{path.stem}: artwork runs outside its viewBox -- {over} "
                f"(about {grew:.0f}% of the canvas height)")

    assert not problems, (
        "glass artwork drawn outside its own canvas:\n  " + "\n  ".join(problems)
        + "\n\nThe viewBox is what heights_mm scales, so ink outside it is "
          "height nothing accounted for -- and `.drink-card-glass svg` sets "
          "overflow: visible, so it paints rather than being clipped, hanging "
          "the glass off the edge of its panel. Fix by re-running the fit "
          "(svgrender.fit_viewbox rewrites the viewBox attribute and nothing "
          "else); never by editing the path data."
    )


def test_fitting_a_canvas_never_moves_the_artwork():
    """`scripts/normalise_glass_icons.py` fits every icon's viewBox to its
    own ink, and this is the guard on that step.

    IT RUNS ON ARTWORK THAT CANNOT BE REGENERATED HERE. `SRC` is
    `tmp/cocktail-glasses`, a gitignored inbox that is empty in a fresh
    worktree, so the normaliser refuses to run and the fit step is never
    exercised by anything else. Without this, a change to `fit_viewbox` would
    be caught only the next time Helen imported a drawing -- by which point it
    would have silently reframed all 26.

    THE PROPERTY THAT MATTERS is that fitting is a reframe, never a redraw. The
    path data and the <g transform> must come out byte-identical; only the
    viewBox attribute may differ. If that holds, the step cannot distort a
    drawing however wrong its arithmetic is -- the worst case is a badly
    cropped frame, which the slack-viewBox guard above then catches.

    IDEMPOTENCE is the second half. Fitting an already-fitted icon must be a
    no-op, or every regeneration would creep the canvas -- and since the
    normaliser runs on the PUBLISHED files' ancestors rather than on the
    published files, a creep would be invisible until glasses drifted out of
    proportion with each other over several imports.
    """
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import svgrender
    except ImportError:  # pragma: no cover
        pytest.skip("scripts/svgrender.py not importable")

    icons = sorted(GLASS_ICON_DIR.glob("*.svg"))
    assert icons, f"no SVGs in {GLASS_ICON_DIR.relative_to(ROOT)}"

    moved, crept = [], []
    for path in icons:
        original = path.read_text()
        fitted, _, _ = svgrender.fit_viewbox(original, label=path.stem)

        before = svgrender.parse_icon_text(original, path.stem)
        after = svgrender.parse_icon_text(fitted, path.stem)
        if before[0] != after[0] or before[2] != after[2]:
            moved.append(path.stem)

        # fitting twice must equal fitting once
        again, _, _ = svgrender.fit_viewbox(fitted, label=path.stem)
        box_once = svgrender.parse_icon_text(fitted, path.stem)[1]
        box_twice = svgrender.parse_icon_text(again, path.stem)[1]
        if any(abs(a - b) > 0.05 for a, b in zip(box_once, box_twice)):
            crept.append(f"{path.stem}: {box_once} -> {box_twice}")

    assert not moved, (
        "fit_viewbox CHANGED THE ARTWORK on: " + ", ".join(moved)
        + "\n\nIt may only rewrite the viewBox attribute. Path data and the "
          "<g transform> must survive untouched -- that is the whole reason "
          "this step is safe to run unattended over Helen's drawings."
    )
    assert not crept, (
        "fit_viewbox is not idempotent:\n  " + "\n  ".join(crept)
        + "\n\nFitting an already-fitted icon must be a no-op, or the canvas "
          "creeps a little on every regeneration and the set slowly loses its "
          "relative proportions."
    )


def test_display_scale_names_only_real_icons():
    """`display_scale` is a per-glass cheat and a phantom key does nothing.

    Added with the cheat itself, 2026-08-26. It multiplies a glass's drawn
    height on a CARD, and the failure mode is the quiet one: a key naming a
    glass that does not exist -- a typo, or an icon later renamed -- has no
    effect at all, so the glass it was meant to shrink goes on being wrong and
    the line in the data file looks like it is handling it.

    Coverage is NOT asserted in the other direction: absent means 1, and almost
    every glass is absent on purpose. Only two glasses have ever needed this.
    """
    g = _glasses()
    scale = g.get("display_scale") or {}
    listed = g.get("all_icons") or []
    assert listed, "glasses.yml has no `all_icons:` -- see the sibling test."

    phantom = sorted(set(scale) - set(listed))
    assert not phantom, (
        f"glasses.yml `display_scale` names glasses that are not icons: "
        f"{phantom}\n\nA phantom key is silently ignored -- the glass it was "
        f"meant to shrink keeps rendering at full height and the data file "
        f"looks like it is handling it. Keys must be ICON names (the value "
        f"side of `icons:`), not the spellings a drink's front matter uses."
    )
    bad = sorted(f"{k}={v!r}" for k, v in scale.items()
                 if not isinstance(v, (int, float)) or not 0 < v <= 1)
    assert not bad, (
        "display_scale values must be numbers greater than 0 and at most 1:\n  "
        + "\n  ".join(bad)
        + "\n\nIt is a multiplier on true relative height, so above 1 is a "
          "glass drawn LARGER than its real proportions, which defeats the "
          "point of heights_mm. A quoted number is a string and Liquid's "
          "`times` turns it into 0 -- an invisible glass."
    )


def test_every_published_drink_names_a_rung_on_the_ship_scale():
    """A promoted drink has a verdict. Helen, 2026-08-30: "every cocktail we
    publish must have the ship field filled in".

    A PROMOTION GATE, deliberately, and drafts are exempt. 31 of the 114 drafts
    say `QQ` or `who knows` today and that is a legitimate state -- it is the
    shape of a drink not yet made up its mind about. What it cannot be is
    published.

    THE COLLECTION ALREADY IMPLIED THIS AND NOTHING ENFORCED IT. §9.5 records
    `meta.status` being retired because its only consumer was a "haven't tried"
    bucket, "dropped rather than redefined, since an untried drink never
    publishes". So promotion has always meant tried-and-judged; this is the
    first thing that checks it.

    IT IS ALSO NOW A RENDERING FACT, which is why it arrives with the ship. The
    card's mark is the WORD, and a drink off the scale renders the icon with no
    label beside it -- fine on a local draft, and on a published card it is a
    rating that says nothing. Helen accepted the icon shifting slightly between
    cards on the strength of every published drink having a word to shift it by.

    `who knows` and `QQ` fail this deliberately even though `ship_tints` covers
    them: tints exist so an off-scale value renders SOMETHING rather than
    erroring, which is a different question from whether it may ship.
    """
    scale = set(_taxonomy().get("ship_scale") or [])
    assert scale, "taxonomy.yml has no `ship_scale:` to check against."

    offenders = []
    for slug, front in _load_published():
        ship = (front.get("meta") or {}).get("ship")
        if ship not in scale:
            offenders.append(f"{slug}: meta.ship is {ship!r}")

    assert not offenders, (
        "Published drink(s) whose `meta.ship` is not a rung on the scale:\n  "
        + "\n  ".join(sorted(offenders))
        + f"\n\nAllowed: {sorted(scale)}. `who knows` and `QQ` are legitimate "
          "on a DRAFT and not on a published drink -- promotion means the drink "
          "has been made and judged (§9.5: an untried drink never publishes). "
          "The card's goodness mark is the word itself, so a published drink "
          "off the scale renders a ship with nothing beside it."
    )


def test_every_ship_rung_has_a_tint():
    """`ship_tints` must cover `ship_scale`, plus the two off-scale values.

    Added 2026-08-26 with the goodness mark. The mark on a cocktail card fills
    with this percentage of the second accent, and Liquid resolves a missing
    key to nil -- which the template defaults to 0, i.e. an EMPTY square. So a
    sixth rung added to `ship_scale` without a tint does not error: it renders
    as the lowest possible rating, silently, which is worse than rendering
    nothing.

    `who knows` and `QQ` are deliberately off the ship scale (see the file's
    own comment) but still reach a card, so they are checked too.
    """
    taxonomy = _taxonomy()
    scale = taxonomy.get("ship_scale") or []
    tints = taxonomy.get("ship_tints") or {}
    assert scale, "taxonomy.yml has no `ship_scale:`."
    assert tints, (
        "taxonomy.yml has no `ship_tints:`. Every goodness mark on the index "
        "would render as an empty square -- the `not really` treatment -- "
        "whatever the drink is rated."
    )

    missing = [r for r in scale if r not in tints]
    assert not missing, (
        f"`ship_tints` does not cover every rung of `ship_scale`: {missing}\n\n"
        f"A rung with no tint renders as an EMPTY square, which is the visual "
        f"for `not really`. It does not error and it does not look broken -- "
        f"it looks like a bad drink."
    )
    for off_scale in ("who knows",):
        assert off_scale in tints, (
            f"`ship_tints` has no entry for {off_scale!r}. It is deliberately "
            f"not on `ship_scale` -- it means 'I have no idea', an absence of "
            f"verdict rather than a low one -- but it still reaches a card and "
            f"still needs a value."
        )

    bad = sorted(f"{k}={v!r}" for k, v in tints.items()
                 if not isinstance(v, (int, float)) or not 0 <= v <= 100)
    assert not bad, (
        "ship_tints values are percentages: numbers from 0 to 100.\n  "
        + "\n  ".join(bad)
    )


def test_suggestion_is_a_string_or_a_list_of_strings():
    """`suggestion` was the only ingredient field with no shape guard at all.

    #499. `generic` has five checks, `character` got one, and
    `glass`/`garnish`/`mood` all have shape tests -- this had none, despite
    being rendered by the same oxford-join loop that relies on its shape.

    BOTH SHAPES ARE CORRECT AND MUST STAY correct: 116 strings and 6 lists
    today. Liquid's `for` treats a bare string as a one-item sequence, which
    HANDOVER §9.10 verified against the real `liquid` gem rather than assuming,
    and that is what lets one loop handle both with no type check in the
    template. The risk is not a string or a list; it is a MAPPING or a
    list-of-lists arriving from an ingest and rendering as `{"a"=>"b"}` or as
    nothing, which is precisely what every sibling field is protected against.
    """
    bad = []
    for slug, fm in _load():
        for ing in (fm.get("ingredients") or []):
            if not isinstance(ing, dict) or "suggestion" not in ing:
                continue
            s = ing["suggestion"]
            if isinstance(s, str):
                continue
            if isinstance(s, list) and all(isinstance(x, str) for x in s):
                continue
            bad.append(f"{slug}: suggestion is {type(s).__name__} -- {s!r}")

    assert not bad, (
        "suggestion must be a string or a list of strings:\n  "
        + "\n  ".join(bad)
        + "\n\nA list means 'either of these bottles would do', never 'and'. "
          "Anything else renders as nonsense rather than as an error."
    )


# The suggestions #457's cleanup did not reach. `suggestion` is meant to be a
# bottle NAME and nothing else -- #457 moved the reasoning out into `note` --
# and these six still read as prose. Recorded rather than fixed: they are
# Helen's words about her own drinks, and rewriting them is her call.
#
# THIS IS A RATCHET, NOT A TODO LIST. The test below asserts the flagged set
# equals this set EXACTLY, in both directions, so a new prose suggestion fails
# and a fixed one fails too until its line is deleted here. A one-directional
# check would let the list rot into a record of things that used to be true --
# the same both-ways contract `all_icons` and `heights_mm` already hold each
# other to.
KNOWN_PROSE_SUGGESTIONS = {
    ("apple-cart", "Avallen -- a round, fresh taste if you need to sub"),
    ("daisy-de-santiago", "Havana 3 year old and Clément Agricole Blanc"),
    # Milliners Punch's "the cheapest white rum to hand; sometimes JW Spicers"
    # came off this set on 2026-08-27, retired the way this contract intends:
    # the suggestion is GONE, not reworded. Helen, "never name Spicers -- if I
    # have it skulking at the back of the nonsense shelf then I'll throw it in
    # where I can." What is cheap and what needs using up are facts about the
    # shelf on the day, and the generic already says what the drink requires.
    ("sazerac", "or other Creole-style bitters"),
    ("sazerac", "or other aromatic bitters"),
    # The Swizzle's "Pusser's 151, or Planteray OFTD for a 138 Swizzle" came off
    # on 2026-08-30, and retired the way this contract intends: the drink was
    # rewritten rather than the string reworded. Helen: "Swizzle has got a bit
    # confused. It should be Martinique Swizzle" -- so it is a 60 ml unaged
    # agricole now, and neither Pusser's nor the OFTD is in it at all. The
    # suggestion that could not resolve went with the rum it was suggesting.
}


def _prose_suggestions():
    """Every (slug, suggestion) that reads as prose rather than a bottle name.

    ONE DEFINITION, TWO TESTS. The ratchet and the staleness check split in
    2026-08-29 (#540) and must keep asking the same question of the data --
    re-typing this loop into both is how a "new offender" and a "fixed entry"
    silently stop being complements of each other.
    """
    markers = re.compile(
        r"\b(or other|if you|because|rather than|instead|works|prefer|any\b|"
        r"but |though|use |avoid|ideally|would)\b", re.I)

    found = set()
    for slug, fm in _load():
        for ing in (fm.get("ingredients") or []):
            if not isinstance(ing, dict) or "suggestion" not in ing:
                continue
            s = ing["suggestion"]
            for one in (s if isinstance(s, list) else [s]):
                if not isinstance(one, str):
                    continue          # shape is the sibling test's problem
                if markers.search(one) or len(one) > 42:
                    found.add((slug, one))
    return found


def test_no_new_prose_suggestions():
    """A `suggestion` should name a bottle, not explain one -- #457, #499.

    "Appleton Estate Reserve" is a suggestion. "or other Creole-style bitters"
    is a note wearing a suggestion's clothes: the page renders suggestions as
    the ingredient HEADLINE, so prose there becomes the thing you read first
    and shop by.

    HEURISTIC, AND DELIBERATELY SO. It looks for connective words and for
    length, because there is no way to test "is this a bottle name" exactly.
    That makes it unsuitable as a bare rule and fine as a ratchet: the six it
    finds today are pinned above, and the assertion is equality, so the check
    can only ever complain about a CHANGE rather than about the status quo.

    If a new suggestion trips it and is genuinely fine, add it to the set with
    a word about why. If one gets fixed, delete its line. Both are one-line
    edits and both are the point.
    """
    new = sorted(_prose_suggestions() - KNOWN_PROSE_SUGGESTIONS)

    assert not new, (
        "suggestion(s) reading as prose rather than a bottle name:\n  "
        + "\n  ".join(f"{slug}: {text!r}" for slug, text in new)
        + "\n\nA suggestion is the ingredient HEADLINE on the drink page, so "
          "reasoning here becomes the thing you read first. Move it to `note`, "
          "which exists for exactly this (#457). If it really is a bottle "
          "name, add it to KNOWN_PROSE_SUGGESTIONS with a word about why."
    )

def test_the_known_prose_suggestion_list_has_no_stale_entries():
    """KNOWN_PROSE_SUGGESTIONS only shrinks -- a reworded suggestion comes off.

    SPLIT OUT OF THE RATCHET ABOVE, 2026-08-29, #540, for the same reason as
    test_the_glassless_list_has_no_stale_entries: "no NEW prose suggestion" is
    a per-drink claim and survives a partial corpus, while "every pinned entry
    still trips the check" needs the whole book -- a drink that is absent has
    no suggestions at all, so every entry reads as fixed.
    """
    _require_whole_collection("KNOWN_PROSE_SUGGESTIONS")
    fixed = sorted(KNOWN_PROSE_SUGGESTIONS - _prose_suggestions())
    assert not fixed, (
        "KNOWN_PROSE_SUGGESTIONS names suggestion(s) that no longer trip the "
        "check:\n  "
        + "\n  ".join(f"{slug}: {text!r}" for slug, text in fixed)
        + "\n\nGood news -- they have been fixed or reworded. Delete their "
          "lines from the set so it keeps describing the present."
    )


def test_syrup_ratio_is_plausible_for_its_generic():
    """FLAG ONLY. Never rewrite, and never fail on a deliberate choice.

    A 1:1 syrup is used at roughly twice the volume of a 2:1 for the same
    sweetness, so syrup-against-citrus carries signal. But it CANNOT classify:
    a declared 1:1 (Daisy de Santiago) and a declared 2:1 (Long Island) both sit
    at 0.50, because Helen adjusts sugar deliberately -- by weather, by company,
    and by halving it when she feels like it (HANDOVER §9.4.1: the site is canon
    and she deviates in the kitchen).

    So the bounds here are deliberately WIDE. This is looking for a
    transcription error -- a figure off by a factor, not off by taste -- and a
    test that fired on ordinary variation would be switched off, which is the
    reasoning test_notes_are_not_damaged gives for keeping its own checks exact
    rather than heuristic.
    """
    _, problems = _syrup_ratio_scan()
    assert not problems, (
        "Syrup-to-citrus ratio outside anything a recipe would use:\n  "
        + "\n  ".join(problems)
        + "\n\nThis is looking for a TRANSCRIPTION error, not a taste "
          "preference -- the bounds are wide on purpose. Check the source "
          "spreadsheet before changing the figure."
    )


def test_the_syrup_ratio_check_is_exercised():
    """Some drink has both a sugar syrup and a citrus juice with ml figures.

    Zero would mean the `sugar syrup` generic prefix or the citrus pattern had
    gone stale, leaving the ratio check green over nothing. Whole collection
    only: see `_exercised`.
    """
    checked, _ = _syrup_ratio_scan()
    _exercised(
        checked, "the syrup-to-citrus ratio check",
        "That is implausible for the whole collection -- the `sugar syrup` "
        "generic prefix or the citrus pattern has probably gone stale.")


def _syrup_ratio_scan():
    """(how many drinks had both figures, the implausible ratios).

    ONE SCAN, TWO TESTS -- see `_character_scan`.
    """
    citrus = re.compile(r"lime juice|lemon juice|grapefruit juice", re.I)
    measures = _vocab().get("measures") or {}

    def ml(entry):
        """Millilitres, or 0 for anything that is not a volume.

        DERIVED SINCE #571, where it used to be `entry.get("ml")`. Deleting
        that key without repointing this would not have failed: both halves of
        the ratio would have summed to zero, `if not (syrup and sour)` would
        have skipped every drink, and the check would have reported green over
        nothing -- HANDOVER 12's "test that cannot fail" exactly. What would
        have caught it is its own sibling, test_the_syrup_ratio_check_is
        _exercised, which is why that test exists.
        """
        try:
            return _millilitres(entry.get("amount", ""), measures)[0] or 0
        except ValueError:
            return 0

    problems = []
    checked = 0
    for slug, fm in _load():
        items = [i for i in (fm.get("ingredients") or []) if isinstance(i, dict)]
        # `generic` may be a list -- see _ingredients() for why -- so normalise
        # before matching. A bare .startswith() here raised AttributeError the
        # moment the first list-valued generic landed, which is the good failure
        # mode: loud, immediate, and at the one place that assumed a string.
        def generics(entry):
            g = entry.get("generic")
            return g if isinstance(g, list) else [g] if g else []

        syrup = sum(ml(i) for i in items
                    if any(str(g).startswith("sugar syrup") for g in generics(i)))
        # MATCHES THE GENERIC, NOT `item` -- moved with #544's second move, and
        # it had to move in the same commit: 106 of the entries that lost their
        # `item` are juices whose only contribution was the word "fresh", so
        # every one of them is citrus. Left reading `item` this scan would have
        # gone quietly blind to most of the sour side of every ratio it checks,
        # and a ratio with half its numerator missing does not fail, it looks
        # implausible or vanishes under `if not (syrup and sour)`.
        sour = sum(ml(i) for i in items
                   if any(citrus.search(str(g)) for g in generics(i)))
        if not (syrup and sour):
            continue
        checked += 1
        ratio = syrup / sour
        if not 0.05 <= ratio <= 1.60:
            problems.append(
                f"{slug}: {syrup:g} ml syrup against {sour:g} ml citrus "
                f"(ratio {ratio:.2f})"
            )
    return checked, problems


# =============================================================================
# METHOD STEPS -- the dictionary, and NOT an enforcement layer. Spec: #290
# =============================================================================
# NOTHING HERE CHECKS A DRINK'S METHOD, deliberately. Helen, 2026-08-26, asked
# for the choice to be recorded rather than taken -- "Prefer both, leaving my
# original too, then I delete whatever I don't want" -- so methods.yml carries
# her existing string beside the suggested canonical one, and a later pass
# applies whatever survives her pruning. A test that failed on a
# non-canonical step today would be enforcing a decision she has not made yet.
#
# What these DO check is that the map cannot rot into a lie: that it proposes
# only real canonical forms, and that every string it claims to have found is
# still out there. Both are the failure mode a written-down duplicate of live
# data always has -- the same reason `all_icons` comes with a test rather than
# after one.

METHODS = ROOT / "_data" / "cocktails" / "methods.yml"


def _methods():
    if not METHODS.exists():
        pytest.skip("_data/cocktails/methods.yml does not exist yet.")
    return yaml.safe_load(METHODS.read_text(encoding="utf-8")) or {}


def _canonical_steps(spec):
    """Every canonical step, flattened from the verb groups.

    Derived from the mapping's shape, not a hardcoded group list -- same
    reasoning as _declared_generics on ingredients.yml.
    """
    out = set()
    for value in (spec.get("canonical") or {}).values():
        if isinstance(value, list):
            out |= set(value)
    return out


def _all_method_steps():
    return [(slug, s) for slug, fm in _load()
            for s in (fm.get("method") or [])]


def test_every_proposal_names_a_real_canonical_step():
    """The right-hand side is a declared canonical form, or the literal QQ.

    A proposal pointing at a step that does not exist is worse than no
    proposal: it reads as a settled decision and would introduce a brand new
    variant the moment anyone applied it -- minting exactly the sprawl this
    file exists to close.
    """
    spec = _methods()
    canonical = _canonical_steps(spec)
    assert canonical, (
        "methods.yml declares no canonical steps, so this check has nothing to "
        "enforce. Either the file changed shape or `canonical` was renamed."
    )
    bad = sorted(f"{k!r} -> {v!r}" for k, v in (spec.get("proposals") or {}).items()
                 if v != "QQ" and v not in canonical)
    assert not bad, (
        "Proposal(s) pointing at a step that is not declared under "
        "`canonical`:\n  " + "\n  ".join(bad)
        + "\n\nEither it is a typo, or the target is real and belongs in the "
          "canonical list."
    )


def test_no_proposal_rewrites_a_step_that_is_already_canonical():
    """A canonical step must not also appear as something to replace.

    A string on both sides is a contradiction the file cannot resolve -- it
    would say a step is both the destination and the thing being retired. This
    is the shape a careless merge produces when two people canonicalise the
    same cluster differently.
    """
    spec = _methods()
    canonical = _canonical_steps(spec)
    overlap = sorted(set(spec.get("proposals") or {}) & canonical)
    assert not overlap, (
        "Step(s) listed as BOTH canonical and as a proposal to be replaced:\n  "
        + "\n  ".join(repr(s) for s in overlap)
        + "\n\nPick one. A canonical step is the destination, never the source."
    )


def test_every_proposal_still_matches_a_real_step():
    """The left-hand side must still exist in the collection.

    THE WHOLE FILE IS A WRITTEN-DOWN COPY OF LIVE DATA, which is a rot risk
    taken deliberately -- and this test is what makes it acceptable, exactly as
    test_all_icons_matches_the_icon_directory is for `all_icons`. Once a
    proposal is applied, or Helen rewrites the step herself, the row is spent:
    it describes a string nothing says any more. Left in place it reads as
    outstanding work that has in fact been done.

    NOT the reverse direction. A method step with no proposal is the normal
    case -- it is either already canonical or part of the informative tail that
    #290 explicitly does not touch.
    """
    _require_whole_collection("methods.yml's proposal list")
    spec = _methods()
    proposals = spec.get("proposals") or {}
    assert proposals, (
        "methods.yml lists no proposals. If every one has been applied and "
        "pruned, delete this test deliberately rather than letting it pass "
        "while checking nothing."
    )
    live = {s for _, s in _all_method_steps()}
    assert live, "no drink has a method -- the loader has gone stale."
    spent = sorted(set(proposals) - live)
    assert not spent, (
        f"{len(spent)} proposal(s) name a step no drink uses any more:\n  "
        + "\n  ".join(repr(s) for s in spent)
        + "\n\nThe work is done -- delete the row. A spent proposal reads as "
          "outstanding, which is the one thing this file must not get wrong."
    )


# =============================================================================
# MOOD -- the browsing vocabulary. Spec: _data/cocktails/taxonomy.yml, #292
# =============================================================================

def _taxonomy():
    if not TAXONOMY.exists():
        pytest.skip("_data/cocktails/taxonomy.yml does not exist yet.")
    return yaml.safe_load(TAXONOMY.read_text(encoding="utf-8")) or {}


def test_every_mood_is_declared():
    """A drink's moods come from taxonomy.yml and nowhere else.

    Moods are DERIVED at ingest and then written into the drink, so that Helen
    can override one -- a drink she thinks is tiki is tiki, whatever the
    ingredient count says. That is the point, and it is also the risk: a
    hand-edited mood is free text, and a typo mints a category that renders as
    a filter button nobody can ever match.
    """
    declared = set(_taxonomy().get("moods") or {})
    assert declared, (
        "_data/cocktails/taxonomy.yml declares no moods, so this check enforces "
        "nothing. An empty set would pass every value."
    )
    bad = sorted({f"{slug}: {m!r}" for slug, fm in _load()
                  for m in (fm.get("mood") or []) if m not in declared})
    assert not bad, (
        "Undeclared mood(s):\n  " + "\n  ".join(bad)
        + f"\n\nDeclared: {sorted(declared)}."
    )


def test_mood_is_a_list():
    """Never a bare string. A string would iterate as characters in Liquid and
    render a filter match for every letter in it, which is the same class of
    silent nonsense as the `glass` scalar.
    """
    bad = [f"{slug}: mood is a {type(fm['mood']).__name__}"
           for slug, fm in _load()
           if "mood" in fm and not isinstance(fm["mood"], list)]
    assert not bad, "mood must be a list:\n  " + "\n  ".join(bad)


def test_every_drink_carries_a_mood_key():
    """Present even when empty, so "no mood yet" is visible rather than absent.

    Same reasoning as the generic coverage check: an absent key reads as
    "nothing to see", an empty list reads as "nothing matched". 17 drinks
    currently have an empty list, mostly because their ingredients are still
    QQ -- see #335 -- and that gap should be legible, not silent.
    """
    missing = [slug for slug, fm in _load() if "mood" not in fm]
    assert not missing, (
        f"{len(missing)} drink(s) carry no `mood` key at all: {missing[:10]}.\n"
        f"Use `mood: []` for none. Absent is not the same as empty."
    )


def test_no_mood_covers_more_than_half_the_collection():
    """A mood matching most drinks is not a filter, it is noise.

    Food retired `one-pot` for exactly this -- it "would cover 57% of the
    collection honestly tagged". Two cocktail moods were caught this way before
    they were ever written down: `fruity` counting citrus reached 51%, and
    `sugar craving` defined as "has any sweetener" reached 68%.

    A guard rather than a note, because the failure mode is gradual: a mood
    stays useful until the collection grows past it, and nobody re-measures.
    """
    _require_whole_collection("a mood's share of the collection")
    drinks = _load()
    counts = {}
    for _, fm in drinks:
        for m in (fm.get("mood") or []):
            counts[m] = counts.get(m, 0) + 1
    assert counts, "no drink carries any mood -- the derivation has stopped running."
    broad = sorted(f"{m}: {n}/{len(drinks)} ({n * 100 // len(drinks)}%)"
                   for m, n in counts.items() if n > len(drinks) / 2)
    assert not broad, (
        "Mood(s) covering more than half the collection:\n  " + "\n  ".join(broad)
        + "\n\nNarrow the definition or drop the mood. A filter that matches "
          "most of the book tells you nothing -- the reasoning that retired "
          "food's `one-pot` tag."
    )


# =============================================================================
# THINGS A CARD NEVER MENTIONS -- #580
# =============================================================================


def test_nothing_on_the_not_on_cards_list_reaches_a_card_or_the_search():
    """Bare `water` is on the recipe and never on the index.

    Helen, 2026-08-29: "never write 'water' on a cocktail card and never return
    it in a search. This is bare 'water', and does not apply to 'honey water' or
    'sparkling water' or any such thing."

    A card answers "what is this drink LIKE", and the answer is never water. It
    is on the Sazerac because 60 ml of it is how that drink gets diluted, which
    is a MAKING fact -- the same distinction §9.10.1 draws when it collapses
    both syrup ratios to `sugar syrup`.

    CHECKED AGAINST THE BUILT PAGE rather than the template, because the
    suppression is written twice there -- once on the `searchable` capture and
    once on the card's own ingredient line -- and Liquid has no way to share it.
    Two copies that must agree is exactly the thing to test on the output.
    """
    vocab = _vocab()
    hidden = vocab.get("not_on_cards")
    assert hidden, (
        "_data/cocktails/ingredients.yml has no `not_on_cards` list. It is what "
        "keeps bare `water` off the index (#580); without it the template's two "
        "suppression blocks silently pass everything through."
    )

    template = (ROOT / "cocktails" / "index.html").read_text(encoding="utf-8")
    assert template.count("not_on_cards contains g") == 2, (
        "cocktails/index.html no longer applies `not_on_cards` in BOTH places. "
        "It has to be tested on the `searchable` capture (what the filter "
        "matches) and on the card's ingredient line (what a reader sees); one "
        "without the other means a word is either invisible but filterable, or "
        "printed but unsearchable."
    )


def test_a_suppressed_word_is_only_ever_suppressed_ALONE():
    """`honey water` and `soda water` are real choosing facts and must survive.

    The caveat is the whole of Helen's instruction, and it is also the shape of
    a bug this repo already had: the picker matched `water` against `honey
    water` by substring until 2026-08-29. `contains` on a Liquid list is exact
    membership, so the template cannot repeat it -- this asserts that the LIST
    itself does not name a compound, which is the other way in.
    """
    for value in _vocab().get("not_on_cards") or []:
        assert len(str(value).split()) == 1, (
            f"`not_on_cards` names {value!r}, which is more than one word. This "
            f"list exists for ingredients that are never a reason to choose a "
            f"drink; a compound like `honey water` or `soda water` is one, and "
            f"suppressing it would take a real fact off the card."
        )


def test_every_suppressed_word_is_a_declared_generic():
    """A suppression that matches nothing is a rule nobody can see failing."""
    declared = _declared_generics(_vocab())
    for value in _vocab().get("not_on_cards") or []:
        assert value in declared, (
            f"`not_on_cards` names {value!r}, which is not a declared generic. "
            f"It can therefore never match an ingredient, so the list looks "
            f"like it is doing something and is not -- and the day the generic "
            f"is spelled differently, nothing says so."
        )
