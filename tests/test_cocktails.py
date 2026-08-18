"""The cocktails collection's own rules. Spec: GitHub issue #322.

`tests/conftest.py` is explicitly the FOOD suite, and says so: the food schema
does not apply to a cocktail. This is the sibling it anticipated.

WHY THIS FILE SKIPS RATHER THAN FAILS ON AN ABSENT COLLECTION, and why that is
not the vacuity trap tests/test_suite_hygiene.py exists to catch.
`_cocktail_drafts/` is its own private git repo, gitignored from this one, so on
a clean checkout of the public repo the directory is genuinely ABSENT -- not
empty, absent. That is a legitimate state and the right response is to skip
loudly saying so.

What is NOT legitimate is the directory being present and yielding nothing,
which would mean the loader has gone stale. So: skip when the collection is not
here, assert non-empty when it is. "This machine has no drinks" and "I looked
and found nothing" must never produce the same green.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pytest
import yaml

# Suite marker, so `pytest -m cocktails` can run this half alone.
# tests/test_suite_hygiene.py asserts every module declares one --
# an unmarked file is silently missed by every filtered run.
pytestmark = pytest.mark.cocktails

ROOT = Path(__file__).resolve().parent.parent
DRAFTS = ROOT / "_cocktail_drafts"
VOCAB = ROOT / "_data" / "cocktails" / "ingredients.yml"
TAXONOMY = ROOT / "_data" / "cocktails" / "taxonomy.yml"

FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---", re.S)

# Groups in ingredients.yml that are lists of generic VALUES. Everything else at
# the top level is a mapping (family_of, family_less, retired_*) or the family
# list itself, and must not be mistaken for declared generics.
NOT_GENERIC_LISTS = {"families"}


def _load():
    if not DRAFTS.is_dir():
        pytest.skip(
            "_cocktail_drafts/ is not present. It is a separate private repo "
            "(helen-triages-cocktails-private), gitignored here, so a clean "
            "checkout of the public repo legitimately has no drinks to check. "
            "Clone it into _cocktail_drafts/ to run these."
        )
    out = []
    for path in sorted(DRAFTS.glob("*.md")):
        match = FRONT_MATTER.match(path.read_text(encoding="utf-8"))
        if match:
            out.append((path.stem, yaml.safe_load(match.group(1)) or {}))
    assert out, (
        f"{DRAFTS.name}/ exists but yielded no parseable drinks. The directory "
        f"is here, so this is not the absent-collection case -- either every "
        f"file lost its front matter, or this loader has gone stale. Do not let "
        f"it report green."
    )
    return out


def _vocab():
    if not VOCAB.exists():
        pytest.skip("_data/cocktails/ingredients.yml does not exist yet.")
    return yaml.safe_load(VOCAB.read_text(encoding="utf-8")) or {}


def _declared_generics(vocab):
    """Every declared generic value, from every list group in the file.

    Derived from the file's own shape rather than a hardcoded list of group
    names, so a group added tomorrow is covered tomorrow -- the same reasoning
    test_every_drafts_collection_is_gitignored uses for reading _config.yml.
    """
    out = set()
    for key, value in vocab.items():
        if key in NOT_GENERIC_LISTS or not isinstance(value, list):
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
    retired = set(vocab.get("retired_rum_styles") or {})
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
    retired = _vocab().get("retired_rum_styles") or {}
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
# 6 and 7 -- shape guards on the drinks themselves
# =============================================================================

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


def _glasses():
    return yaml.safe_load(
        (ROOT / "_data" / "cocktails" / "glasses.yml").read_text(encoding="utf-8")
    )


GLASS_ICON_DIR = ROOT / "_includes" / "icons" / "glasses"


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
    citrus = re.compile(r"lime juice|lemon juice|grapefruit juice", re.I)
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

        syrup = sum(i.get("ml") or 0 for i in items
                    if any(str(g).startswith("sugar syrup") for g in generics(i)))
        sour = sum(i.get("ml") or 0 for i in items if citrus.search(i.get("item", "")))
        if not (syrup and sour):
            continue
        checked += 1
        ratio = syrup / sour
        if not 0.05 <= ratio <= 1.60:
            problems.append(
                f"{slug}: {syrup:g} ml syrup against {sour:g} ml citrus "
                f"(ratio {ratio:.2f})"
            )
    assert checked, (
        "No drink has both a sugar syrup and a citrus juice with ml figures, so "
        "this check is vacuous. That is implausible for this collection -- the "
        "generic prefix or the citrus pattern has probably gone stale."
    )
    assert not problems, (
        "Syrup-to-citrus ratio outside anything a recipe would use:\n  "
        + "\n  ".join(problems)
        + "\n\nThis is looking for a TRANSCRIPTION error, not a taste "
          "preference -- the bounds are wide on purpose. Check the source "
          "spreadsheet before changing the figure."
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
