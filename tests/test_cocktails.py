"""The cocktails collection's own rules (#322); `tests/conftest.py` is the food suite.

The corpus is both collections, `_cocktail_recipes/` and `_cocktail_drafts/`
(#540). The drafts are a private repo, gitignored here and absent in CI, so CI
checks the published drinks alone.

Neither collection on disk is a skip with a reason; a collection that is
present and yields nothing fails, because that is a stale loader. A claim about
the whole book ("this registry has no dead entries") cannot be judged on a
partial corpus: those tests call `_require_whole_collection` and are listed in
WHOLE_COLLECTION_ONLY.

Run this half alone with `pytest -m cocktails`.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

import pytest
import yaml

# The house-style predicates are shared with the food suite through conftest.py
# (#670); the asserts, messages and field lists below are this collection's own.
import drafts_schema
from conftest import (
    SHARED_TYPOGRAPHY, accent_problems, accented_words, checkable_text,
    degreeless_temperatures, is_qq, note_is_a_sentence, note_problems, notes_of,
    number_range_hits, spelling_problems, unquoted_scalars,
)

pytestmark = pytest.mark.cocktails

ROOT = Path(__file__).resolve().parent.parent
RECIPES = ROOT / "_cocktail_recipes"
DRAFTS = ROOT / "_cocktail_drafts"
# The staging folders. A drink in either is finished writing and waits only on
# Helen, so the rules that bite at promotion bite here too (`_load_staged`). A
# folder left off this tuple silently drops out of those rules. PIPELINE.md §3.
STAGED_DIRS = (DRAFTS / "4-promote", DRAFTS / "5-final-proofread")
# The folder names as prose, for failure messages: a test may not name
# `STAGED_DIRS` itself (`test_every_drink_reading_test_goes_through_the_loader`).
STAGED_NAMES = ", ".join(f"`{d.name}/`" for d in STAGED_DIRS)
# The collections as they are on disk, fixed at import: `_scan` reads each of
# these once per run. A test that monkeypatches RECIPES or DRAFTS points them
# somewhere that is not in this tuple, and so is always read afresh.
_REAL_ROOTS = (RECIPES, DRAFTS) + STAGED_DIRS
VOCAB = ROOT / "_data" / "cocktails" / "ingredients.yml"
TAXONOMY = ROOT / "_data" / "cocktails" / "taxonomy.yml"
BOTTLES = ROOT / "_data" / "cocktails" / "bottles.yml"

FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---", re.S)


# --- One parse per data file per run (#1271) ---
# Every test shares one object per file, so a test that edits what a loader
# returned changes the data for every test after it. Copy before changing one;
# `_the_shared_data_is_as_parsed` fails the module if a shared copy has drifted.
_PARSED = {}
_SCANNED = {}       # the drink collections themselves -- see `_scan`


def _parsed(path):
    if path not in _PARSED:
        _PARSED[path] = yaml.safe_load(path.read_text(encoding="utf-8"))
    return _PARSED[path]


def _shared_data_that_changed():
    """Every shared file whose in-memory copy no longer matches the disk.

    Walks the caches themselves rather than a second list of paths: a list
    kept by hand is one a new loader would be missing from.
    """
    changed = [
        str(path.relative_to(ROOT)) for path, held in _PARSED.items()
        if held != yaml.safe_load(path.read_text(encoding="utf-8"))
    ]
    for root, held in _SCANNED.items():
        fresh = {d.path: d.fm for d in _scan_afresh(root)}
        changed += [str(d.path.relative_to(ROOT)) for d in held
                    if d.fm != fresh.get(d.path)]
    return changed


@pytest.fixture(scope="module", autouse=True)
def _the_shared_data_is_as_parsed():
    yield
    changed = _shared_data_that_changed()
    assert not changed, (
        f"A test changed the shared parsed copy of {', '.join(changed)} in "
        "place. `_parsed` hands every test the same object (#1271), so every "
        "test that ran after it read the edited data. Find the test that "
        "mutates what a loader returned and make it copy first."
    )

# --- The drink schema (#669): what a drink file may and must contain ---
# A closed set: an undeclared key is a silent no-op that nothing reads or
# renders, so a new key is one line here.

# In page order, and the order is a rule for drafts, not for published drinks
# (#1213): `scripts/tidy_drafts.py --only order` writes it. The order is read
# off `_layouts/cocktail.html`, and
# `test_the_declared_key_order_is_the_order_the_page_prints` fails when the two
# disagree. `meta` follows `garnish` because the head prints `meta.ship` there.
TOP_LEVEL_KEYS_IN_ORDER = [
    "title", "tagline", "snippet", "glass", "garnish", "meta", "mood",
    "ingredients", "serve", "serves", "method", "to_serve", "notes", "source",
    "source_url",
]

# A key the layout never names has its place declared here, with the reason.
# The derivation test refuses an entry the layout has started to name.
KEYS_THE_LAYOUT_NEVER_NAMES = {
    "snippet":
        "read by `_layouts/default.html` for the meta description and the "
        "link preview, never by the drink's own layout (#1089). OPTIONAL, and "
        "on one drink: it is the tagline rewritten for a search result. "
        "Placed directly after `tagline`, the line it stands in for.",
    "serves":
        "read by `_plugins/cocktail_units.rb`, which hands the page "
        "`page.units.serves`; the layout never says `page.serves`. Placed "
        "directly after `serve`, where MANUAL 9.3's example has always had it: "
        "it is the last fact about the pour before the build starts.",
}

TOP_LEVEL_KEYS = set(TOP_LEVEL_KEYS_IN_ORDER)

# `serves` is optional and absent means one (#297): the unit count divides by
# it, and the scaler does not read it.
#
# `serve` holds what happens in the glass; `to_serve` is the serveware and is a
# separate field. An absent `serve` means nobody has decided, and `ice: "none"`
# means served up. There is no `chill` key: a chilled glass is implied. A
# quantity of ice goes in `fill`, never in `ice`. MANUAL §9.10a.
SERVE_KEYS = {"ice", "rim", "fill"}

# `to_serve`, `serve`, `serves` and `snippet` are optional. Every other key is
# written even when empty (`source: ""`): "nobody has recorded a source" and
# "the key is missing" must not look alike.
REQUIRED_TOP_LEVEL = TOP_LEVEL_KEYS - {"to_serve", "serve", "serves", "snippet"}

# `suggestion` is written even when empty, as `suggestion: []`. `as` says how
# an ingredient is used and `card_order` names a card tier outright (#754);
# `_plugins/cocktail_card_ingredients.rb` reads both. The three `_claude` keys
# hold a proposal beside a `QQ <the source's words>` in the field itself, for
# Helen to collapse by ruling. A declared bottle needs none, and a bare
# category word nobody can resolve gets the QQ alone. A character is always an
# inference about this recipe: `bottles.yml` has no character column (#314).
INGREDIENT_KEYS = {
    "generic", "amount", "suggestion", "note", "character", "optional",
    "as", "card_order",
    "generic_claude", "suggestion_claude", "character_claude",
}

# The proposal keys, and the field each one proposes a value for.
CLAUDE_PROPOSALS = {
    "generic_claude": "generic",
    "suggestion_claude": "suggestion",
    "character_claude": "character",
}

# `amount` is not required HERE because it has its own test with its own
# explanation -- see test_every_ingredient_has_an_amount below.
REQUIRED_INGREDIENT = {"generic"}

# The order is the assertion. `made_before` and `ship` are the drink's own
# (#722); the three gate flags follow in food's `META_ORDER` order
# (test_front_matter.py). `_plugins/publish_gate.rb` reads all three on a
# promoted drink (DECISIONS §4.0).
META_KEYS_IN_ORDER = ["made_before", "ship", "rewritten", "awaiting_fix",
                      "proofread"]

# The flags the publish gate reads: booleans, all with the same quoting trap.
GATE_FLAGS = ["rewritten", "awaiting_fix", "proofread"]

# A tagline nobody has written yet. It must not reach the live site: see
# test_no_published_drink_carries_a_qq.
PLACEHOLDER = "QQ"


def _is_qq(value):
    """`QQ`, or `QQ` followed by whatever the source said.

    `generic: "QQ aged Jamaican rum"` is still an unanswered question: the page
    reads `generic`, so the source's words go there to be seen. The space stops
    a real generic that merely starts with those letters from matching.
    """
    if value is None:
        return False
    text = str(value).strip()
    return text == PLACEHOLDER or text.startswith(PLACEHOLDER + " ")


def _unanswered(values):
    """True where every name given is the `QQ` placeholder.

    A QQ is a declared absence, not a name (#335, #1108). A check that looks
    one up in a vocabulary finds nothing and reports a stale vocabulary, which
    fails on any machine with the drafts and never in CI. A real name missing
    from the vocabulary still fails.
    """
    names = [str(v).strip() for v in values if v is not None and str(v).strip()]
    return bool(names) and all(_is_qq(n) for n in names)

# Top-level lists in ingredients.yml that are NOT generic vocabularies. A list
# left off this set silently mints every member as a permitted generic, so
# every new top-level list is either a vocabulary or goes here.
# `<family>_characters` lists are excluded by suffix; a mapping needs no entry.
NOT_GENERIC_LISTS = {"families", "not_on_cards", "rum_groups", "ingredient_as",
                     "bottle_origins", "shopping_shelves", "always_fresh"}


def _is_character_list(key):
    return key.endswith("_characters")


# --- The corpus is both collections, and that is the promotion gate (#540) ---
# The published half is in this repo and is checked wherever it exists, CI
# included; the private drafts are checked wherever they are cloned. A loader
# that reads the drafts alone leaves a promoted drink checked by nothing.

NO_DRINKS_REASON = (
    "No drinks on this machine to check: neither `_cocktail_recipes/` nor "
    "`_cocktail_drafts/` holds one here. `_cocktail_drafts/` is a separate "
    "private repo (helen-triages-cocktails-private), gitignored here, so CI and "
    "a fresh worktree never have it. Clone the drafts into _cocktail_drafts/ to "
    "check those; promote a drink to check it here AND in CI."
)


class DrinkFile:
    """One drink file: its slug, its path, its raw text and its front matter.

    The raw text is here because quoting and a `QQ` line are properties of how
    the file is written, not of what it parses to (#670).
    """

    __slots__ = ("path", "slug", "raw", "fm")

    def __init__(self, path, raw, fm):
        self.path = path
        self.slug = path.stem
        self.raw = raw
        self.fm = fm

    def __repr__(self):                 # what pytest prints in the test id
        return self.slug


def _scan(root):
    """Every parseable drink under one collection root. Absent root -> nothing.

    `rglob`, not `glob`: the drafts have staging subfolders, and a flat glob
    stops seeing exactly the drinks closest to promotion.

    The roots in `_REAL_ROOTS` are scanned once per run (#1271); any other root
    is read afresh. The caller gets its own list but the drinks in it are
    shared, so copy a front matter before changing it.
    """
    if root in _REAL_ROOTS:
        if root not in _SCANNED:
            _SCANNED[root] = _scan_afresh(root)
        return list(_SCANNED[root])
    return _scan_afresh(root)


def _scan_afresh(root):
    out = []
    if not root.is_dir():
        return out
    for path in sorted(root.rglob("*.md")):
        raw = path.read_text(encoding="utf-8")
        match = FRONT_MATTER.match(raw)
        if match:
            out.append(DrinkFile(path, raw, yaml.safe_load(match.group(1)) or {}))
    return out


def _read(root):
    """`_scan`, as the `(slug, front matter)` pairs every other test reads."""
    return [(drink.slug, drink.fm) for drink in _scan(root)]


def _load_files():
    """Published drinks plus draft drinks, whole, from whichever roots are here.

    Skips only when neither collection is on disk. A root that is here and
    yields nothing is a stale loader and fails: "this machine has no drinks"
    and "I looked and found nothing" must never be the same green.
    """
    out = _scan(RECIPES) + _scan(DRAFTS)
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


def _load():
    """The same corpus as `_load_files`, as `(slug, front matter)` pairs.

    Not a second door: both go through `_scan` and skip and fail in the same
    places. See test_every_drink_reading_test_goes_through_the_loader.
    """
    return [(drink.slug, drink.fm) for drink in _load_files()]


def _load_published():
    """Only the drinks in `_cocktail_recipes/` -- the ones the world sees.

    For a promotion gate, which is a claim about published drinks alone; the
    combined corpus would hold drafts to a rule that is not theirs. Skips
    rather than passes when nothing is promoted: green over zero drinks is
    vacuous.
    """
    return [(drink.slug, drink.fm) for drink in _load_published_files()]


def _load_published_files():
    """`_load_published`, with the raw text left on.

    For a rule about the whole file rather than a parsed field
    (`test_no_published_drink_carries_a_qq`). The alternative is a test
    globbing `RECIPES` itself, which the loader guard refuses.
    """
    out = _scan(RECIPES)
    if not out:
        pytest.skip(
            "No promoted drinks. `_cocktail_recipes/` is empty, so there is "
            "nothing for a promotion gate to check -- this is a fact about the "
            "collection, not a loader that has gone stale. It starts running "
            "the day the first drink is promoted."
        )
    return out


def _load_draft_files():
    """Only the drinks in `_cocktail_drafts/`, whole.

    For a rule that is true of a draft and deliberately not of a published
    drink (#1258). It filters `_load_files()` rather than scanning the root, so
    the skip and the loud failure are that door's. Absent drafts skip: that is
    the ordinary state of CI.
    """
    out = [d for d in _load_files() if DRAFTS in d.path.parents]
    if not out and DRAFTS.is_dir():
        pytest.fail("`_cocktail_drafts/` exists but yielded no parseable drafts, "
                    "so this loader has gone stale. Do not let it report green.")
    if not out:
        pytest.skip(
            "`_cocktail_drafts/` is not on this machine, so there is no draft "
            "for a draft-only rule to check. It is a separate private repo "
            "(helen-triages-cocktails-private), so CI never has it; clone it "
            "into _cocktail_drafts/ to run this."
        )
    return out


def _load_staged():
    """The published tense: `_cocktail_recipes/` plus every staging folder in STAGED_DIRS.

    A drink in a staging folder is finished prose waiting on Helen, so the
    fields the site publishes are already in their published form there; a
    rule that first fires on the day a file is moved is too late.

    Skips when no directory is on disk, and when none holds a drink. The
    staging folders are in the private drafts repo, so CI never has them.
    """
    out = _read(RECIPES)
    for staged in STAGED_DIRS:
        out += _read(staged)
    if out:
        return out
    if not (RECIPES.is_dir() or any(d.is_dir() for d in STAGED_DIRS)):
        pytest.skip(
            "Neither `_cocktail_recipes/` nor any staging folder "
            f"({', '.join(d.name for d in STAGED_DIRS)}) is on this machine, so "
            "there is no staged drink to check. The staging folders are in the "
            "private drafts repo (gitignored here); `_cocktail_recipes/` is in "
            "this repo, so its absence means the checkout is incomplete."
        )
    pytest.skip(
        "No drinks are staged for publication. `_cocktail_recipes/` is empty "
        f"and the staging folders ({', '.join(d.name for d in STAGED_DIRS)}) "
        "hold nothing, which is a fact about where Helen is rather than a "
        "stale loader: these rules start running the moment she moves the "
        "first file into any of them."
    )


# --- Per-drink parametrisation (#670) ---
# A house-style rule is a claim about a file, so its failure names the file.
# An empty corpus yields one parameter, `None`, which `_require_drink` hands
# back to `_load_files` for the right skip or the right loud failure: a bare
# parametrise over nothing reports "skipped" for both.

def pytest_generate_tests(metafunc):
    if "drink_file" not in metafunc.fixturenames:
        return
    drinks = _scan(RECIPES) + _scan(DRAFTS)
    if drinks:
        metafunc.parametrize("drink_file", drinks, ids=[d.slug for d in drinks])
    else:
        metafunc.parametrize("drink_file", [None], ids=["no-drinks"])


def _require_drink(drink_file):
    """Never returns for a placeholder: it skips, or it fails loudly."""
    if drink_file is None:
        _load_files()
        raise AssertionError(
            "The drink corpus is empty but `_load_files()` neither skipped nor "
            "failed. That is the one outcome it must never have -- see its "
            "docstring and issue #540."
        )


def _drink_where(drink, detail=""):
    """The file's real path from the repo root, as food's `where()` gives."""
    path = drink.path.resolve().relative_to(ROOT).as_posix()
    return path + (f" -- {detail}" if detail else "")


# --- What a partial corpus cannot answer (#540) ---
# "This registry has no dead entries" and "no value covers more than half the
# book" are unanswerable when only some drinks are present: an absent drink
# looks exactly like a fixed one, and in CI the drafts are always absent. So
# the ratchet half of such a rule ("no new offender") runs everywhere, and the
# staleness half is its own test, calls `_require_whole_collection` and is
# listed here. `test_whole_collection_only_says_what_it_does` pins the list.

WHOLE_COLLECTION_ONLY = {
    "test_the_glassless_list_has_no_stale_entries",
    "test_the_known_prose_suggestion_list_has_no_stale_entries",
    "test_unresolved_suggestions_has_no_stale_entries",
    "test_every_card_name_join_is_reachable",
    "test_every_proposal_still_matches_a_real_step",
    "test_every_garnish_proposal_still_matches_a_real_string",
    "test_no_mood_covers_more_than_half_the_collection",
    # The coverage claims -- see _exercised.
    "test_the_character_vocabulary_is_exercised",
    "test_the_bottle_index_is_exercised",
    "test_the_cross_category_check_is_exercised",
    "test_the_syrup_ratio_check_is_exercised",
    "test_the_amount_table_is_exercised",
    "test_the_plural_unit_rule_is_exercised",
    "test_every_mood_correction_is_reachable_and_needed",
    "test_no_drink_note_exception_is_stale",
    "test_no_as_exception_is_stale",
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
    """This guard's scan found something to check -- a coverage claim.

    The claim argues from the size of the whole book, so it holds only on the
    whole collection: one promoted drink may contain no rum at all. It is its
    own test rather than a skip inside the offender check, which must keep
    running on every promoted drink in CI (#540).
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

    CI has this repo and not the private drafts, so absent drafts is the shape
    of every deploy run; a loader that skips there checks no published drink
    (#540).
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

    The reason must say how to make the check real.
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
    """A root that exists and yields nothing fails -- it does not skip.

    "The drafts are not cloned here" and "the drafts are cloned and I parsed
    none of them" must not produce the same outcome, or a stale loader looks
    like a machine without the private repo.
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
    """No test may glob the collections itself; the loaders are the only door.

    A test naming `RECIPES` or `DRAFTS` directly gets none of the loader's
    skip-or-fail and, in CI, scans nothing and reports green (#540). Read from
    the syntax tree, not from a list somebody maintains.
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
        # Rename a root constant and the new name must join this set in the
        # same commit, or the guard stops seeing direct access to it.
        named = sorted(names & {"RECIPES", "DRAFTS", "STAGED", "STAGED_DIRS"})
        if named:
            offenders.append(f"{node.name} names {', '.join(named)} directly")

    assert checked, (
        "No tests found in this module at all -- an empty scan passes while "
        "checking nothing, which is the one failure mode with a green symptom."
    )
    assert not offenders, (
        "Test(s) read the cocktail collections without going through _load():\n  "
        + "\n  ".join(offenders)
        + "\n\nCall _load(), _load_published() or _load_staged() instead -- "
          "whichever scope the rule is actually about. _load() reads BOTH "
          "`_cocktail_recipes/` and "
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

    A test listed but not calling `_require_whole_collection` reports absent
    entries as stale in CI; one calling it unlisted silently stops covering
    the collection. Read from the syntax tree: a docstring explaining the rule
    contains every word a grep would look for (MANUAL §12).
    """
    import ast

    src = Path(__file__).read_text(encoding="utf-8")
    listed, calls, seen = WHOLE_COLLECTION_ONLY, set(), set()
    for node in ast.walk(ast.parse(src)):
        if not (isinstance(node, ast.FunctionDef) and node.name.startswith("test_")):
            continue
        seen.add(node.name)
        # Both entry points: `_exercised` wraps `_require_whole_collection`.
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


# --- The schema guard (#669): a drink cannot gain or lose a key in silence ---
# Every check below reads the constants at the top of this file and names no
# field of its own.


def test_no_unknown_top_level_keys():
    """A drink's front matter holds only the keys the schema declares.

    An undeclared key is a silent no-op: no template reads it, no test sees it,
    and a misspelling of a real one reads exactly like a new idea.
    """
    bad = []
    for slug, fm in _load():
        for key in sorted(set(fm) - TOP_LEVEL_KEYS):
            bad.append(f"{slug}: {key!r}")
    assert not bad, (
        "Undeclared top-level key(s):\n  " + "\n  ".join(bad)
        + "\n\nEither it is a typo for a declared key -- in which case nothing "
          "has been reading it -- or it is real, and belongs in "
          "TOP_LEVEL_KEYS_IN_ORDER at the top of this file, at the place "
          "_layouts/cocktail.html renders it, with a note saying what that is."
    )


def test_required_top_level_keys_present():
    """Every drink carries every key in REQUIRED_TOP_LEVEL.

    A missing key and an empty one are different facts: `source: ""` says
    nobody has found the source yet; no `source` at all says nothing.
    """
    bad = []
    for slug, fm in _load():
        missing = sorted(REQUIRED_TOP_LEVEL - set(fm))
        if missing:
            bad.append(f"{slug}: missing {missing}")
    assert not bad, (
        "Drink(s) missing required front matter:\n  " + "\n  ".join(bad)
        + "\n\nWrite the key with an empty value rather than leaving it out: "
          "`notes: []`, `garnish: []`, `source: \"\"`. `to_serve` is the one "
          "genuinely optional key and is not asked for here."
    )


# --- Key order (#1213): a draft is written in the order the page prints it ---
# Two tests. The first asks whether the declared order is still the page's and
# runs everywhere; the second reads the private drafts only, because the rule
# is not applied to published drinks.

COCKTAIL_LAYOUT = ROOT / "_layouts" / "cocktail.html"
_LIQUID_COMMENT = re.compile(
    r"\{%-?\s*comment\s*-?%\}.*?\{%-?\s*endcomment\s*-?%\}", re.S)
_PAGE_FIELD = re.compile(r"\bpage\.([a-z_]+)")
# Where the page's words begin. Above this the layout looks the glass icon up
# from `page.glass`, which would put `glass` above `title`; the order is the
# order of the words.
_WORDS_BEGIN = 'class="cocktail-head-words"'


def page_order_from_the_layout():
    """Top-level keys in the order `_layouts/cocktail.html` first names them.

    Comments are removed first: a Liquid comment that says `page.glass` in
    prose is not the page printing a glass. What is left is read from
    `_WORDS_BEGIN` down, and each declared key is placed at its FIRST mention.
    `page.url`, `page.units`, `page.cost` and the like are not front matter and
    are dropped by the membership test.
    """
    text = _LIQUID_COMMENT.sub("", COCKTAIL_LAYOUT.read_text(encoding="utf-8"))
    assert text.count(_WORDS_BEGIN) == 1, (
        f"`_layouts/cocktail.html` no longer has exactly one {_WORDS_BEGIN}, "
        f"which is where the key-order derivation starts reading (#1213). "
        f"Point `_WORDS_BEGIN` at whatever now opens the page's words; do not "
        f"let this read the whole file, or the glass icon's lookup puts "
        f"`glass` above `title`."
    )
    order = []
    for key in _PAGE_FIELD.findall(text[text.index(_WORDS_BEGIN):]):
        if key in TOP_LEVEL_KEYS and key not in order:
            order.append(key)
    return order


def keys_out_of_page_order(keys):
    """`(have, want)` when these top-level keys are out of order, else None.

    Only declared keys are compared; an undeclared one is
    `test_no_unknown_top_level_keys`'s to report, and a key that is absent is
    simply not in either list. `scripts/tidy_drafts.py` and
    `tests/test_standalone_docs.py` both ask this, so the rule has one
    definition.
    """
    have = [k for k in keys if k in TOP_LEVEL_KEYS]
    want = [k for k in TOP_LEVEL_KEYS_IN_ORDER if k in have]
    return None if have == want else (have, want)


def test_the_declared_key_order_is_the_order_the_page_prints():
    """`TOP_LEVEL_KEYS_IN_ORDER` equals the order read off the layout. #1213.

    The layout is the authority, so neither can move alone: a key added to the
    schema is either printed by the layout or given a place and a reason in
    `KEYS_THE_LAYOUT_NEVER_NAMES`.
    """
    derived = page_order_from_the_layout()
    assert len(derived) >= 10, (
        f"Only {len(derived)} top-level keys were found in the layout: "
        f"{derived}. The scan has stopped matching -- an order derived from "
        f"almost nothing would agree with almost anything."
    )

    by_hand = set(KEYS_THE_LAYOUT_NEVER_NAMES)
    excused_but_printed = sorted(by_hand & set(derived))
    assert not excused_but_printed, (
        f"`KEYS_THE_LAYOUT_NEVER_NAMES` lists {excused_but_printed}, and the "
        f"layout names it now. Delete the entry: the page has given the key a "
        f"place, and the place is where it is first printed."
    )
    unplaced = sorted(TOP_LEVEL_KEYS - set(derived) - by_hand)
    assert not unplaced, (
        f"Declared key(s) the layout never names, with no place given: "
        f"{unplaced}. Add each to `KEYS_THE_LAYOUT_NEVER_NAMES` with the "
        f"reason it sits where it does."
    )

    declared = [k for k in TOP_LEVEL_KEYS_IN_ORDER if k not in by_hand]
    assert declared == derived, (
        "`TOP_LEVEL_KEYS_IN_ORDER` is not the order `_layouts/cocktail.html` "
        "prints the fields in (#1213):\n"
        f"  declared: {declared}\n"
        f"  the page: {derived}\n\n"
        "The page is the authority. If a section really has moved, move the "
        "key in the list at the top of this file -- and then the drafts are "
        "out of order too: `python3 scripts/tidy_drafts.py --site cocktails "
        "--only order` reports them."
    )
    assert len(TOP_LEVEL_KEYS_IN_ORDER) == len(TOP_LEVEL_KEYS), (
        "`TOP_LEVEL_KEYS_IN_ORDER` names a key twice."
    )


def test_a_draft_drinks_keys_are_in_page_order():
    """A cocktail draft's top-level keys are in page order. #1213.

    Drafts only: the rule is not applied to published drinks, which keep the
    order they were promoted in. The order is part of the drafts schema
    (`tests/drafts_schema.py`), so a clone that predates it fails
    `test_the_cocktail_drafts_clone_is_in_step` first.
    """
    bad = []
    for drink in _load_draft_files():
        problem = keys_out_of_page_order(list(drink.fm))
        if problem:
            bad.append(f"{_drink_where(drink)}\n      has:  "
                       f"{', '.join(problem[0])}\n      want: "
                       f"{', '.join(problem[1])}")
    assert not bad, (
        "Draft drink(s) whose top-level keys are not in page order:\n  "
        + "\n  ".join(bad)
        + "\n\n`python3 scripts/tidy_drafts.py --site cocktails --only order "
          "--apply` reorders them and changes nothing else. See "
          ".claude/commands/tidy-drafts.md."
    )


def test_no_unknown_ingredient_keys():
    """An ingredient entry holds only the keys the schema declares.

    An entry is a bare mapping with no layout of its own, so a stray key
    renders nowhere and fails nothing: `note` versus `notes` is the whole
    failure mode. One set for both collections.
    """
    bad = []
    for slug, fm in _load():
        for i, item in enumerate(fm.get("ingredients") or [], 1):
            if not isinstance(item, dict):
                bad.append(f"{slug} entry {i}: {type(item).__name__}, not a mapping")
                continue
            for key in sorted(set(item) - INGREDIENT_KEYS):
                bad.append(f"{slug} entry {i}: {key!r}")
    assert not bad, (
        "Undeclared ingredient key(s):\n  " + "\n  ".join(bad)
        + "\n\nDeclared: " + ", ".join(sorted(INGREDIENT_KEYS))
        + ". Nothing reads anything else -- see §9.10 for what the line renders."
        + "\n\nIf this is `item`: it was retired on 2026-09-21. The source's own "
          "words go in `generic`, after a `QQ ` where the category is not "
          "settled, because that is the field the page and the cards read. "
          "Anything they do not carry goes in a `note:`."
    )


# --- The published tense: the staging folders and `_cocktail_recipes/` ---
# A draft keeps Helen's spelling and the aliases do the reading (MANUAL
# §9.3.2). A finished drink says the bottle's real name.

def test_a_staged_drink_writes_a_bottles_canonical_name():
    """A drink ready to publish names each bottle as `bottles.yml` names it.

    An alias resolves, so `test_every_suggested_bottle_resolves` passes it; it
    is shorthand for transcribing and not what the published page says. Drafts
    elsewhere keep her spelling (MANUAL §9.3.2). A suggestion that resolves to
    nothing is that other test's to report.
    """
    data = _bottles()
    index = _bottle_index(data)
    assert index, "bottles.yml resolves no names; nothing to check."
    canonical = set((data.get("bottles") or {}))

    bad = []
    for slug, fm in _load_staged():
        for item in (fm.get("ingredients") or []):
            if not isinstance(item, dict):
                continue
            suggestion = item.get("suggestion")
            for name in (suggestion if isinstance(suggestion, list)
                         else [suggestion] if suggestion else []):
                if not isinstance(name, str) or name in canonical:
                    continue
                real = index.get(name.strip().lower())
                if real is None:
                    continue        # owned by test_every_suggested_bottle_resolves
                bad.append(f"{slug}: {name!r} -> {real!r}")

    assert not bad, (
        "Staged drink(s) writing a bottle's ALIAS rather than its name:\n  "
        + "\n  ".join(sorted(bad))
        + "\n\nRetype the `suggestion` to the name on the right -- the one "
          "_data/cocktails/bottles.yml declares. A drink in a staging folder "
          f"({STAGED_NAMES}) or in "
          "`_cocktail_recipes/` is finished writing and is read by strangers, "
          "and an alias is shorthand Helen wrote for herself while transcribing "
          "(\"'ED3' isn't a bottle\", 2026-09-04). Everywhere else the opposite "
          "rule holds and is deliberate: leave a draft as she spelled it and "
          "teach the dictionary the spelling (MANUAL §9.3.2)."
    )


def test_every_ingredient_has_a_declared_shape():
    """Every ingredient entry carries a `generic`; nothing else is required.

    `generic` is what the index browses by (MANUAL §9.3.1), so an entry without
    one is invisible to every filter and to the card. An untyped ingredient is
    a visible `QQ` generic, never an absent key.
    """
    bad = []
    for slug, fm in _load():
        for i, item in enumerate(fm.get("ingredients") or [], 1):
            if not isinstance(item, dict):
                continue
            missing = sorted(REQUIRED_INGREDIENT - set(item))
            if missing:
                bad.append(f"{slug} entry {i}: missing {missing}")
    assert not bad, (
        "Ingredient entr(ies) missing a required key:\n  " + "\n  ".join(bad)
        + "\n\nAn ingredient nobody has typed yet writes `generic: \"QQ\"`, "
          "which is what test_every_ingredient_has_a_generic_or_a_qq expects. "
          "An ABSENT key is the one shape neither check can report on."
    )


def _step_text(step):
    """The words of one method step, whichever of the two shapes it is written in.

    A step is a string or a `{step, note}` pair, and every reader of `method`
    in this file goes through here: a reader of the raw list breaks on the
    pair. Anything in neither shape reads as no words; the shape test below
    fails on it.
    """
    if isinstance(step, dict):
        step = step.get("step")
    return step if isinstance(step, str) else ""


def _steps(fm):
    """Every method step of one drink, as text.

    The scalar form (`method: "Stir."`) is accepted here the way the layout
    accepts it, so a check cannot silently skip a drink written that way.
    """
    method = fm.get("method")
    listed = method if isinstance(method, list) else [method] if method else []
    return [text for text in (_step_text(s) for s in listed) if text]


def test_a_method_step_is_a_string_or_a_step_note_pair():
    """`method` holds strings, or `{step, note}` pairs.

    The note is a non-empty string when present: `note: ""` renders as a step
    with an empty grey line under it. The pair holds nothing else: a third key
    is a typo or an unimplemented field, and both render as silence.
    """
    bad = []
    for slug, fm in _load():
        method = fm.get("method")
        listed = method if isinstance(method, list) else [method] if method else []
        for i, step in enumerate(listed, 1):
            where = f"{slug} step {i}"
            if isinstance(step, str):
                continue
            if not isinstance(step, dict):
                bad.append(f"{where}: {step!r} is neither a string nor a pair")
                continue
            extra = sorted(set(step) - {"step", "note"})
            if extra:
                bad.append(f"{where}: unknown key(s) {extra}")
            if not (isinstance(step.get("step"), str) and step["step"].strip()):
                bad.append(f"{where}: `step` is {step.get('step')!r}")
            if "note" in step and not (isinstance(step["note"], str)
                                       and step["note"].strip()):
                bad.append(f"{where}: `note` is {step['note']!r}")
    assert not bad, (
        "Method step(s) in neither shape:\n  " + "\n  ".join(bad)
        + "\n\nA step is a plain string, or:\n\n"
          '  - step: "Muddle the lime chunks hard with the sugar."\n'
          '    note: "my giant spiky muddler not the polite smooth one"\n\n'
          "Both halves are non-empty strings and there is no third key. Used "
          "sparingly -- Helen, 2026-09-04."
    )


def test_method_is_a_non_empty_list():
    """Every drink's `method` is an ordered list with at least one step in it.

    A drink with no `method` renders as a drink with nothing left to do. Where
    the source records no build the step is a visible `QQ`.
    """
    bad = []
    for slug, fm in _load():
        method = fm.get("method")
        if not isinstance(method, list) or not method:
            bad.append(f"{slug}: {method!r}")
    assert not bad, (
        "Drink(s) with no usable method:\n  " + "\n  ".join(bad)
        + "\n\n`method: []` is not the answer and neither is omitting the key: "
          "both render as a drink with no steps, which is indistinguishable "
          "from a drink that needs none. If the source has no method, write one "
          "step saying so -- `QQ - no method in the source; Helen to supply.` "
          "-- and never reconstruct a build from general bartending knowledge."
    )


def test_every_ingredient_has_an_amount():
    """Every ingredient entry says how much, with no exceptions.

    An ingredient the method adds rather than measures has a verb-phrase
    amount ("to top", "to rinse"); without one, "numberless by nature" and
    "nobody wrote it down" are the same `None`.
    """
    bad = []
    for slug, fm in _load():
        for i, item in enumerate(fm.get("ingredients") or [], 1):
            if not isinstance(item, dict):
                continue
            if item.get("amount") is None:
                bad.append(f"{slug} entry {i}: "
                           f"{item.get('generic')!r}")
    assert not bad, (
        "Ingredient entr(ies) with no `amount`:\n  " + "\n  ".join(bad)
        + "\n\nThere is no amount-less case. A top-up is `amount: \"to top\"` "
          "with a `Top with ...` method step; a rinse is `amount: \"to rinse\"` "
          "with a `Rinse ...` step. Both units are declared in `measures:` in "
          "_data/cocktails/ingredients.yml, so "
          "test_every_amount_is_readable_as_a_quantity reads them by the same "
          "path it reads `dash`."
    )


def test_meta_keys_are_exactly_the_schema_in_order():
    """A drink's `meta:` block holds exactly META_KEYS_IN_ORDER, in that order.

    Reordering a block changes no value, so the order is free to obey and the
    blocks read alike at a glance.
    """
    bad = []
    for slug, fm in _load():
        meta = fm.get("meta")
        if not isinstance(meta, dict):
            bad.append(f"{slug}: no `meta:` mapping")
            continue
        if list(meta) != META_KEYS_IN_ORDER:
            bad.append(f"{slug}: {list(meta)}")
    assert not bad, (
        f"`meta:` blocks that are not exactly {META_KEYS_IN_ORDER}:\n  "
        + "\n  ".join(bad)
        + "\n\nSame keys, same order, every drink. A key that belongs here and "
          "is not listed goes in META_KEYS_IN_ORDER at the top of this file; a "
          "key that does not belong is dead weight, not data."
    )


def test_tagline_is_a_non_empty_string():
    """Every drink has a `tagline`, and it is a string with something in it.

    An unwritten tagline says `QQ`; that keeps the backlog visible rather than
    letting the key quietly disappear.
    """
    bad = []
    for slug, fm in _load():
        tagline = fm.get("tagline")
        if not isinstance(tagline, str) or not tagline.strip():
            bad.append(f"{slug}: {tagline!r}")
    assert not bad, (
        "Drink(s) with no usable tagline:\n  " + "\n  ".join(bad)
        + "\n\nOne line of prose, or the placeholder `\"QQ\"` until it is "
          "written. Never an empty string and never an absent key: both erase "
          "the fact that the line is owed."
    )


_QQ_ANYWHERE = re.compile(r"\bQQ\b")


def test_no_published_drink_carries_a_qq():
    """`QQ` never reaches the live site, in any field, in any shape.

    `QQ` means "Helen, look at this", and the gate flags say only that she has
    read the file, not that nothing in it is owed. A word-boundary search over
    the raw text, so a QQ in a method step, a note, a comment or the body is
    caught, and an unwritten tagline (`QQ`) cannot publish.
    """
    bad = []
    for drink in _load_published_files():
        for n, line in enumerate(drink.raw.splitlines(), 1):
            if _QQ_ANYWHERE.search(line):
                bad.append(f"{drink.slug}:{n}: {line.strip()[:90]}")
    assert not bad, (
        f"{len(bad)} line(s) in `_cocktail_recipes/` still carry a `QQ`:\n  "
        + "\n  ".join(bad)
        + "\n\n`QQ` means \"Helen, look at this\" and the live site is the one "
          "place it must never appear. Answer it, or move the drink back to "
          "`_cocktail_drafts/` until it is answered. Never delete a QQ to make "
          "this green -- a QQ that has been ANSWERED becomes a plain note "
          "recording the answer; only a QQ that was wrong to ask gets deleted."
    )


# --- The publication gate, drink side (#667, #668) ---
# `_plugins/publish_gate.rb` publishes a drink only on an explicit pass of each
# gate flag (DECISIONS §4.0). The boolean and hyphen checks run over both
# collections; the git-history check runs over `_cocktail_recipes/` alone,
# because it is a claim about published files.

def test_the_gate_flags_are_real_booleans():
    """`awaiting_fix: "false"` is a string and the gate does not match it.

    The plugin compares against Ruby's `false` and `true`, not truthiness, and
    fails closed, so a quoted flag holds the drink back with no explanation.
    """
    bad = []
    for slug, fm in _load():
        meta = fm.get("meta")
        if not isinstance(meta, dict):
            bad.append(f"{slug}: no `meta:` mapping")
            continue
        for flag in GATE_FLAGS:
            if flag not in meta:
                bad.append(f"{slug}: no `meta.{flag}`")
            elif not isinstance(meta[flag], bool):
                bad.append(f"{slug}: {flag} is {meta[flag]!r} "
                           f"({type(meta[flag]).__name__})")
    assert not bad, (
        f"Drink(s) whose gate flags are not unquoted true/false:\n  "
        + "\n  ".join(bad)
        + "\n\nAll three of "
        + ", ".join(GATE_FLAGS)
        + " are booleans on every drink (D2, 2026-09-02). Absent is not the "
          "same as false: absent means nobody has considered the file, and it "
          "reads as 'not cleared' to a gate that fails closed. Never quote the "
          "value -- a string never equals Ruby's `false`."
    )


def test_no_drink_uses_the_old_hyphenated_awaiting_fix_key():
    """`awaiting-fix` must never appear, on a drink or anywhere else.

    Ruby reads `meta["awaiting-fix"]` happily, but Liquid parses
    `page.meta.awaiting-fix` as subtraction, so a template asking whether a
    drink is flagged gets arithmetic instead of the flag.
    """
    bad = []
    for slug, fm in _load():
        meta = fm.get("meta")
        holders = [fm] + ([meta] if isinstance(meta, dict) else [])
        for holder in holders:
            if "awaiting-fix" in holder:
                bad.append(slug)
    assert not bad, (
        "Drink(s) using the old hyphenated `awaiting-fix` key:\n  "
        + "\n  ".join(sorted(set(bad)))
        + "\n\nRename to `awaiting_fix`. Liquid reads the hyphenated form as a "
          "subtraction, so a template asking whether the drink is flagged gets "
          "arithmetic instead of the flag."
    )


# The newest commit whose agent edits Helen has read herself. A published drink
# last touched at or before it is exempt from the proofread flip (#367). The
# test sees this repo's history only, so a promotion of drinks she has already
# read looks like an agent edit and needs a move too (#624).
# Moving it is Helen's grant, never a way to turn a red test green: run the
# test with the old value, which must name only the granted files, then move
# it in a commit of its own quoting her grant (DECISIONS §4.0). A grant covers
# that commit and nothing after; parallel grants need the merge behind both.
COCKTAIL_BASELINE_COMMIT = "8ef2be8e"   # the ten promoted after #1413; has `22d6c4c1` (its IOU marks) behind it


def _newest_commit_per_published_drink():
    """{relative path: newest commit sha} across `_cocktail_recipes/`.

    A module-level helper so the test function never names the corpus roots:
    test_every_drink_reading_test_goes_through_the_loader keeps `_load()` the
    only door.
    """
    from test_front_matter import _git

    last: dict[str, str] = {}
    sha = None
    pathspec = f"{RECIPES.name}/"
    for line in _git("log", "--format=%H", "--name-only", "--", pathspec).splitlines():
        line = line.strip()
        if not line:
            continue
        if len(line) == 40 and all(c in "0123456789abcdef" for c in line):
            sha = line
        elif line.endswith(".md"):
            last.setdefault(line, sha)
    return last


def test_agent_edited_drinks_are_not_marked_proofread():
    """A promoted drink whose newest commit is an agent's must say
    `proofread: false` (#367).

    `_git`, `AGENT_TRAILER` and `_only_invisible_keys_changed` are imported
    from tests/test_front_matter.py so the two sites cannot drift. It reads
    this repo's history only (#624), and skips while nothing is promoted.
    """
    from test_front_matter import AGENT_TRAILER, _git, _only_invisible_keys_changed

    published = {slug for slug, _ in _load_published()}   # skips if none
    assert (ROOT / ".git").exists(), "Not a git checkout -- this test cannot run."
    assert "true" not in _git("rev-parse", "--is-shallow-repository").lower(), (
        "This is a SHALLOW clone, so `git log` cannot see who last touched each "
        "drink and this test would silently check almost nothing. Fetch full "
        "history (actions/checkout needs `fetch-depth: 0`)."
    )

    last = _newest_commit_per_published_drink()
    assert last, (
        f"{len(published)} drink(s) are on disk but git knows of no commit "
        f"touching any of them. Either they are uncommitted, or the pathspec "
        f"this test uses has stopped matching -- both would let it pass while "
        f"checking nothing."
    )

    import subprocess

    agent_commit: dict[str, bool] = {}
    offenders = []
    for relpath, commit in sorted(last.items()):
        path = ROOT / relpath
        if not path.exists():
            continue                                  # renamed, or demoted since
        if subprocess.run(["git", "merge-base", "--is-ancestor",
                           commit, COCKTAIL_BASELINE_COMMIT],
                          cwd=ROOT, capture_output=True).returncode == 0:
            continue                                  # grandfathered; see above
        if _only_invisible_keys_changed(commit, relpath):
            continue                                  # renders nothing
        if commit not in agent_commit:
            agent_commit[commit] = AGENT_TRAILER in _git(
                "show", "-s", "--format=%B", commit).lower()
        if not agent_commit[commit]:
            continue                                  # Helen's own commit
        match = FRONT_MATTER.match(path.read_text(encoding="utf-8"))
        meta = (yaml.safe_load(match.group(1)) or {}).get("meta", {}) or {}
        if meta.get("proofread") is not False:
            offenders.append(f"{relpath} (last touched by {commit[:8]})")

    assert not offenders, (
        "Promoted drink(s) last edited by an agent but still marked "
        "proofread:\n  " + "\n  ".join(offenders)
        + "\n\nAn agent editing a drink invalidates Helen's proofread of it, so "
          "the SAME commit must set `meta.proofread: false` (issue #367). Since "
          "2026-09-02 that also takes the drink off the live site until she "
          "reads it, which is the point rather than a side-effect."
    )


def _vocab():
    if not VOCAB.exists():
        pytest.fail("_data/cocktails/ingredients.yml is gone. Every test that reads it would skip, not fail, without this line.")
    return _parsed(VOCAB) or {}


def _retired(vocab):
    """Every retired generic -> its reason, from every `retired_*` mapping.

    Derived from the prefix, not a list of block names, so a new `retired_*`
    block is covered at once; one left out fails as a bare "undeclared
    generic" with no reason attached.
    """
    out = {}
    for key, value in vocab.items():
        if key.startswith("retired_") and isinstance(value, dict):
            out.update(value)
    return out


def _declared_generics(vocab):
    """Every declared generic value, from every list group in the file.

    Derived from the file's shape, not a list of group names, so a group added
    tomorrow is covered tomorrow.
    """
    out = set()
    for key, value in vocab.items():
        if (key in NOT_GENERIC_LISTS or _is_character_list(key)
                or not isinstance(value, list)):
            continue
        out |= set(value)
    return out


def _ingredients():
    """(drink, generic) for every ingredient entry, one row per generic.

    `generic` may be a list, meaning either would do (#441). It is flattened
    here so each check sees one generic at a time and none has to know about
    the list form.
    """
    out = []
    for slug, fm in _load():
        for entry in (fm.get("ingredients") or []):
            if not isinstance(entry, dict):
                continue
            generic = entry.get("generic")
            if isinstance(generic, list):
                out += [(slug, g) for g in generic]
            else:
                out.append((slug, generic))
    return out


# --- 1 and 2: the vocabulary is closed, and retirements bite ---

def test_qq_followed_by_the_sources_words_is_still_a_qq():
    """`generic: "QQ aged Jamaican rum"` is an unanswered question with a hint.

    CI has no drafts clone, so nothing else there notices `_is_qq` breaking.
    Pinned both ways: the source's words are accepted, and a real generic that
    merely starts with those two letters is not.
    """
    assert _is_qq("QQ")
    assert _is_qq("QQ aged Jamaican rum")
    assert _is_qq("  QQ  Coco mix (3:1 Coco Lopez to coconut milk)")
    assert _unanswered(["QQ", "QQ simple syrup"])

    assert not _is_qq("QQuince liqueur")
    assert not _is_qq("aged Jamaican rum")
    assert not _is_qq("")
    assert not _is_qq(None)
    assert not _unanswered(["QQ simple syrup", "lime juice"])


def test_every_generic_is_declared():
    """A `generic` is a declared value or `QQ`. A third thing is how a typo
    mints a category silently.

    Retired values are left to test_no_drink_uses_a_retired_generic, which
    reports them with their reason.
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
        f"{slug}: {generic!r}"
        for slug, generic in _ingredients()
        if generic and not _is_qq(generic) and generic not in declared
        and generic not in retired
    })
    assert not bad, (
        "Undeclared generic(s):\n  " + "\n  ".join(bad)
        + "\n\nEither it is a typo, or the value is real and belongs in "
          "_data/cocktails/ingredients.yml. Issue #322 is the spec."
    )


def _shelf_problems(vocab) -> list[str]:
    """Every way `shelf_of` and the declared generics disagree, one per line."""
    declared = _declared_generics(vocab)
    shelf_of = vocab.get("shelf_of") or {}
    shelves = set(vocab.get("shopping_shelves") or [])
    out = [f"{g!r} is a declared generic with no row in `shelf_of`"
           for g in sorted(declared - set(shelf_of))]
    out += [f"`shelf_of` has a row for {g!r}, which is not a declared generic"
            for g in sorted(set(shelf_of) - declared)]
    out += [f"{g!r} is filed under {shelf!r}, which `shopping_shelves` does not list"
            for g, shelf in sorted(shelf_of.items()) if shelf not in shelves]
    return out


def test_every_declared_generic_is_on_a_shopping_shelf():
    """`shelf_of` has exactly one row per declared generic, on a real shelf (#1175).

    Nothing else errors on a missing row: the shopping list sorts an unknown
    shelf last and carries on. Declared, not poured, so it runs in CI without
    the drafts. A row for an undeclared generic, or under an undeclared shelf,
    fails too.
    """
    vocab = _vocab()
    assert _declared_generics(vocab) and vocab.get("shelf_of"), (
        "_data/cocktails/ingredients.yml has no declared generics or no "
        "`shelf_of` map, so this check compared nothing with nothing."
    )
    problems = _shelf_problems(vocab)
    assert not problems, (
        "The shopping shelves and the vocabulary disagree:\n  "
        + "\n  ".join(problems)
        + "\n\nWhich shelf a generic belongs on is Helen's call. Add or remove "
          "the row in `shelf_of`, in the commit that declares or retires the "
          "generic."
    )


def test_the_shelf_check_sees_each_way_the_map_can_be_wrong():
    """The check above passes on today's data, so prove each half can fail."""
    def vocab(shelf_of):
        return {"sugars": ["molasses sugar"], "other": ["milk"],
                "shopping_shelves": ["larder", "sugar syrup"],
                "shelf_of": shelf_of}

    assert not _shelf_problems(vocab({"molasses sugar": "sugar syrup", "milk": "larder"}))
    assert _shelf_problems(vocab({"molasses sugar": "sugar syrup"}))
    assert _shelf_problems(vocab({"molasses sugar": "sugar syrup", "milk": "larder",
                                  "cream": "larder"}))
    assert _shelf_problems(vocab({"molasses sugar": "sugar syrup", "milk": "dairy"}))
    # the aisle names are a list in the same file and must not count as generics
    assert not any("larder" in line for line in
                   _shelf_problems(vocab({"molasses sugar": "sugar syrup"})))


def test_a_claude_proposal_only_sits_beside_an_open_question():
    """A `_claude` key is legal only while its entry still carries a `QQ`.

    The `QQ` may be in `generic` or in the `note`: a source naming a bottle
    resolves the generic outright and leaves only the character open. A
    published drink carries no `QQ` (test_no_published_drink_carries_a_qq), so
    this one rule keeps proposals out of both collections.
    """
    bad = []
    for slug, fm in _load():
        for i, entry in enumerate(fm.get("ingredients") or [], 1):
            if not isinstance(entry, dict):
                continue
            proposals = sorted(set(entry) & set(CLAUDE_PROPOSALS))
            if not proposals:
                continue
            open_question = (_unanswered(_listed(entry.get("generic")))
                             or _is_qq(entry.get("note")))
            if not open_question:
                bad.append(f"{slug} entry {i}: {', '.join(proposals)} on a pour "
                           f"with nothing left open "
                           f"(generic {entry.get('generic')!r}, "
                           f"note {entry.get('note')!r})")
    assert not bad, (
        f"{len(bad)} proposal(s) outliving the question they answer:\n  "
        + "\n  ".join(sorted(bad))
        + "\n\nA `_claude` key is a PROPOSAL and is legal only while the pour "
          "still asks something -- a `QQ` in `generic`, or a `QQ -` note saying "
          "what is open. Once Helen has ruled, the proposal either becomes the "
          "field's value or is wrong; either way it stops being a proposal and "
          "the key goes. Do not delete a QQ to make this green."
    )


def _listed(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def test_a_claude_proposal_names_a_real_value():
    """A proposed generic, character or bottle is one the repo declares.

    A proposal exists to be promoted into its field with one edit, so a value
    the field would refuse can never be accepted. `suggestion_claude` resolves
    through the alias map, like any suggestion.
    """
    vocab = _vocab()
    declared = _declared_generics(vocab)
    retired = _retired(vocab)
    characters = {c for key, value in vocab.items()
                  if _is_character_list(key) for c in value}
    bottles = _bottle_index(_bottles())

    bad = []
    for slug, fm in _load():
        for entry in (fm.get("ingredients") or []):
            if not isinstance(entry, dict):
                continue
            for g in _listed(entry.get("generic_claude")):
                if g in retired:
                    bad.append(f"{slug}: generic_claude {g!r} is RETIRED "
                               f"({retired[g]})")
                elif g not in declared:
                    bad.append(f"{slug}: generic_claude {g!r} is not declared")
            for c in _listed(entry.get("character_claude")):
                if characters and c not in characters:
                    bad.append(f"{slug}: character_claude {c!r} is not a "
                               f"declared character")
            for s in _listed(entry.get("suggestion_claude")):
                if str(s).strip().lower() not in bottles:
                    bad.append(f"{slug}: suggestion_claude {s!r} names no "
                               f"known bottle")
    assert not bad, (
        "Proposal(s) naming something the field would refuse:\n  "
        + "\n  ".join(sorted(bad))
        + "\n\nA proposal exists to be promoted into its field with one edit, "
          "so it is held to the same vocabulary the field is. If the right "
          "answer is not in the vocabulary, there is no proposal to make -- "
          "leave the `QQ` and the source's words alone."
    )


def test_no_drink_uses_a_retired_generic():
    """Retired values fail with their retirement reason attached.

    Checked apart from "not declared", so a value that used to mean something
    does not blend into the undeclared pile, where nobody learns why it went.
    """
    retired = _retired(_vocab())
    assert retired, (
        "No retired values declared, so this enforces nothing. If the "
        "retirements were reversed, delete this test deliberately."
    )
    bad = [
        f"{slug}: {generic!r} ({retired[generic]})"
        for slug, generic in _ingredients()
        if generic in retired
    ]
    assert not bad, (
        "Retired generic(s) still in use:\n  " + "\n  ".join(bad)
        + "\n\nRe-type against the vocabulary. Which rum a drink wants is "
          "Helen's own knowledge and is not recoverable from the spreadsheet -- "
          "use QQ, do not guess."
    )


SERVE = ROOT / "_data" / "cocktails" / "serve.yml"


def _serve_vocab():
    if not SERVE.exists():
        pytest.fail("_data/cocktails/serve.yml is gone. Every test that reads it would skip, not fail, without this line.")
    return _parsed(SERVE) or {}


SOURCES = ROOT / "_data" / "cocktails" / "sources.yml"


def _sources_data():
    if not SOURCES.exists():
        pytest.fail("_data/cocktails/sources.yml is gone. Every test that reads it would skip, not fail, without this line.")
    return _parsed(SOURCES) or {}


def test_every_source_spelling_is_canonical():
    """A drink that cites a declared publication spells it the declared way.

    A spelling rule, never a coverage one (DECISIONS §9.2): a `source` matching
    nothing in the table is free text and passes. The match is on the whole
    field, so a compound attribution that contains a publication's name is
    untouched.
    """
    declared = _sources_data().get("publications") or {}
    canonical = {name.strip().lower(): name for name in declared}
    alias_of = {}
    for name, entry in declared.items():
        for alias in ((entry or {}).get("aliases") or []):
            alias_of[alias.strip().lower()] = name

    overlap = sorted(set(alias_of) & set(canonical))
    assert not overlap, (
        f"spelling(s) declared as both a name and an alias: {overlap}. "
        f"One of the two entries is wrong, and while both exist the rule "
        f"below cannot say which spelling it wants."
    )

    bad = []
    for slug, fm in _load():
        source = str(fm.get("source") or "").strip()
        if not source:
            continue
        got = alias_of.get(source.lower())
        if got:
            bad.append(f"{slug}: source {source!r} -> {got!r}")
    assert not bad, (
        "Drink(s) spelling a declared publication a second way:\n  "
        + "\n  ".join(sorted(bad))
        + "\n\n`_data/cocktails/sources.yml` names the form this collection "
          "uses and lists the variants seen in the wild. Write the name, or -- "
          "if this really is a different publication -- give it its own entry."
    )


def test_no_source_alias_is_stale():
    """Every declared publication lists at least one alias.

    The spelling test acts on aliases only, so an entry with none filters
    nothing.
    """
    declared = _sources_data().get("publications") or {}
    assert declared, "sources.yml declares no publications, so this checks nothing."
    for name, entry in declared.items():
        assert isinstance(entry, dict), f"{name}: expected a mapping"
        aliases = entry.get("aliases") or []
        assert aliases, (
            f"{name!r} declares no aliases, so it filters nothing. Either name "
            f"the spellings it is meant to catch, or take the entry out."
        )


def test_serve_block_uses_only_declared_keys_and_values():
    """`serve` is a closed vocabulary, declared in _data/cocktails/serve.yml.

    A free-text `ice` puts the ice back into prose, where "strain" gets written
    many ways. Absent is always legal and means nobody has decided yet; an
    empty mapping is not.
    """
    vocab = _serve_vocab()
    ices = set(vocab["ice"])
    assert ices, "serve.yml declares no ice values, so this enforces nothing."
    bad = []
    for slug, fm in _load():
        serve = fm.get("serve")
        if serve is None:
            continue
        if not isinstance(serve, dict):
            bad.append(f"{slug}: `serve` is a {type(serve).__name__}, not a mapping")
            continue
        if not serve:
            bad.append(f"{slug}: `serve` is empty -- omit the key instead")
        for key in sorted(set(serve) - SERVE_KEYS):
            bad.append(f"{slug}: unknown serve key {key!r}")
        if "ice" in serve and serve["ice"] not in ices:
            bad.append(f"{slug}: ice {serve['ice']!r} is not declared in serve.yml")
    assert not bad, (
        "serve block problem(s):\n  " + "\n  ".join(bad)
        + "\n\nThe values live in _data/cocktails/serve.yml. Adding one is a "
          "YAML edit and writing that line is the moment somebody decides the "
          "value is real."
    )


def test_every_fill_is_a_declared_one():
    """`serve.fill` says how full, and serve.yml declares the words.

    An undeclared value renders the ice clause unchanged ("filled with crushed
    ice" where the drink said half): a silent wrong answer, not a loud one.
    """
    vocab = _serve_vocab()
    declared = set(vocab.get("fill") or {})
    assert declared, (
        "serve.yml declares no `fill:` values, so the field enforces nothing. "
        "If it was retired, delete it from SERVE_KEYS and these tests with it."
    )
    bad = []
    for slug, fm in _load():
        serve = fm.get("serve")
        if not isinstance(serve, dict) or "fill" not in serve:
            continue
        if serve["fill"] not in declared:
            bad.append(f"{slug}: fill {serve['fill']!r} is not declared")
    assert not bad, (
        "serve `fill` value(s) that are not declared:\n  " + "\n  ".join(bad)
        + f"\n\nDeclared: {', '.join(sorted(declared))}. The values live in "
          "_data/cocktails/serve.yml."
    )


def test_a_fill_has_something_to_fill():
    """A drink saying how full must have ice whose clause says `filled`.

    `fill` swaps the word `filled` in the composed ice clause. Where the clause
    has none (ice the drink is strained onto, `none`, or no `serve.ice`) the
    substitution silently does nothing, and the page never says how full.
    """
    vocab = _serve_vocab()
    clauses = vocab.get("in_the_glass") or {}
    bad = []
    for slug, fm in _load():
        serve = fm.get("serve")
        if not isinstance(serve, dict) or "fill" not in serve:
            continue
        clause = clauses.get(serve.get("ice"), "")
        if "filled" not in clause:
            bad.append(
                f"{slug}: fill {serve['fill']!r} with ice "
                f"{serve.get('ice')!r}, whose clause is {clause!r}")
    assert not bad, (
        "serve `fill` on a drink with nothing to fill:\n  " + "\n  ".join(bad)
        + "\n\n`fill` replaces the word `filled` in the ice clause, so it "
          "means something only where the clause has one -- `cubed` and "
          "`crushed`. Either give the drink one of those, or drop `fill`."
    )

def test_serve_ice_is_not_restated_in_the_method():
    """The ice is recorded once, in `serve`, and not again in a strain step.

    "Strain over crushed ice" beside `ice: "crushed"` is one fact twice, and
    the copies can disagree. Swizzles are the exception: "Fill with crushed
    ice" is technique, and those steps start with Fill or Top, never a strain
    verb, which is the line this test draws.
    """
    bad = []
    for slug, fm in _load():
        for step in (fm.get("method") or []):
            if not isinstance(step, str):
                continue
            if not re.match(r"^(fine[- ]?strain|double strain|strain|dump)\b",
                            step, re.I):
                continue
            if re.search(r"\bice\b|crushed|cube|block|chilled|frozen", step, re.I):
                bad.append(f"{slug}: {step!r}")
    assert not bad, (
        "A strain step still describes the serve:\n  " + "\n  ".join(sorted(bad))
        + "\n\nThe technique belongs in `method` -- Strain, Fine strain, Double "
          "strain, Dump -- and where it lands belongs in `serve` and `glass`. "
          "Say it once."
    )


# A step ending on one of these has lost its tail. `chilled` and `cold` are
# NOT here: "shake until chilled" is a whole sentence.
_DANGLING = re.compile(
    r"\b(the|a|an|into|with|over|to|of|and|or|in|on|for|from|"
    r"pre-chilled|remaining|other|all)\s*\.\s*$", re.I)


def test_no_method_step_ends_on_a_dangling_word():
    """A step whose last word cannot end a sentence has been truncated, as in
    "Fine strain into a chilled." or "Add to the.".

    Whole sentences that look similar pass: "... shake until chilled." and
    "... drop it in.". A step starting `QQ` is skipped.
    """
    bad = []
    for slug, fm in _load():
        for step in (fm.get("method") or []):
            text = step if isinstance(step, str) else (step or {}).get("step")
            if not isinstance(text, str):
                continue
            if text.lower().startswith("qq"):
                continue
            if _DANGLING.search(text) and not re.search(r"\bdrop it in\.$", text, re.I):
                bad.append(f"{slug}: {text!r}")
    assert not bad, (
        "Method step(s) ending on a dangling word:\n  " + "\n  ".join(sorted(bad))
        + "\n\nThe tail of the sentence is missing. Finish it -- do not delete "
          "the step, which is how the instruction disappears instead of the "
          "typo."
    )


def test_to_serve_is_serveware_and_not_the_ice():
    """`to_serve` is what the drink is served with, never how it is iced.

    Ice belongs in `serve.ice`, a closed vocabulary the page renders itself; a
    sentence about ice here is a second, free-text copy that can disagree.
    """
    bad = []
    for slug, fm in _load():
        text = fm.get("to_serve")
        if not isinstance(text, str):
            continue
        if re.search(r"\bice\b|crushed|cube|frozen|chilled", text, re.I):
            bad.append(f"{slug}: to_serve {text!r}")
    assert not bad, (
        "`to_serve` describing the ice:\n  " + "\n  ".join(sorted(bad))
        + "\n\nUse `serve.ice`, which is declared in _data/cocktails/serve.yml "
          "and renders its own line. `to_serve` is straws, ladles and paper "
          "umbrellas."
    )


def test_a_rim_says_rim():
    """`serve.rim` is a noun phrase containing the word "rim".

    The layout writes it after "with a" on the strain step, so a bare
    ingredient reads "...glass with a salt". DECISIONS §9.10a.
    """
    bad = []
    for slug, fm in _load():
        rim = (fm.get("serve") or {}).get("rim")
        if rim is None:
            continue
        if not isinstance(rim, str) or not re.search(r"\brim\b", rim):
            bad.append(f"{slug}: {rim!r}")
    assert not bad, (
        "`serve.rim` value(s) the strain step cannot read as \"with a ...\":\n  "
        + "\n  ".join(bad)
        + "\n\nName the rim: \"salt rim\", \"sugar half-rim\", \"half-rim of "
          "salt\"."
    )


def test_a_garnish_is_not_an_ingredient_or_a_rim():
    """`garnish` holds garnishes, not ingredients, rims or serveware.

    Two shapes a machine can be sure of: a quantity or the word dash/drop,
    which is an ingredient and belongs where #297 can count it, and a rim
    being made ("half-rim of sugar"), which is `serve.rim`. A rim used as an
    address passes: "lime wedge on rim", "orange peel over the rim".
    """
    quantity = re.compile(r"^\s*\d|\b(dash|dashes|drop|drops)\b", re.I)
    rimming = re.compile(r"\brim\b(?!\s*$)|rim of\b|-rim\b", re.I)
    bad = []
    for slug, fm in _load():
        for g in (fm.get("garnish") or []):
            if not isinstance(g, str):
                continue
            if quantity.search(g):
                bad.append(f"{slug}: {g!r} -- a quantity, so it is a pour")
            elif rimming.search(g) and not re.search(
                    r"\b(on|over) (the )?rim\b", g, re.I):
                bad.append(f"{slug}: {g!r} -- a rim, so it is `serve.rim`")
    assert not bad, (
        "Not a garnish:\n  " + "\n  ".join(sorted(bad))
        + "\n\nA pour belongs in `ingredients` (and #297 needs it there to count "
          "the alcohol); a rim belongs in `serve.rim`; serveware belongs in "
          "`to_serve`. A placement like 'lime wedge on rim' is a real garnish "
          "and passes."
    )


def test_every_glass_in_use_has_a_serving_phrase():
    """Every glass a drink names has a `serving` phrase in glasses.yml.

    The page composes its strain step from the technique, this phrase and the
    ice clause from serve.yml. A glass with no phrase falls back to a bare
    "Strain." and the glass silently leaves the method. The article and the
    word "glass" are part of the phrase: "an old fashioned glass", "a coupe".
    """
    glasses = _glasses()
    serving = glasses.get("serving") or {}
    canon = glasses.get("canonical_glasses") or {}
    assert serving, "glasses.yml declares no `serving` phrases."
    missing = {}
    for slug, fm in _load():
        for g in (fm.get("glass") or []):
            key = str(g).lower()
            key = canon.get(key, key)
            if key not in serving:
                missing.setdefault(key, []).append(slug)
    bad = [f"{k!r} -- {', '.join(sorted(v)[:3])}" for k, v in sorted(missing.items())]
    assert not bad, (
        "Glass(es) with no serving phrase:\n  " + "\n  ".join(bad)
        + "\n\nAdd one to `serving:` in _data/cocktails/glasses.yml, keyed on "
          "the CANONICAL name and including its article -- \"a coupe\", "
          "\"an old fashioned glass\"."
    )


def test_suggestion_is_always_a_list():
    """`suggestion` is always a list, so no consumer has to handle two shapes.

    Liquid treats a bare string as a one-item sequence, so the template
    tolerates both and nothing complains. `generic` is not held to this: there
    a string and a list mean different things (#441).
    """
    bad = []
    for slug, fm in _load():
        for entry in (fm.get("ingredients") or []):
            if not isinstance(entry, dict):
                continue
            sugg = entry.get("suggestion")
            if sugg is not None and not isinstance(sugg, list):
                bad.append(f"{slug}: suggestion: {sugg!r} is a {type(sugg).__name__}")
    assert not bad, (
        "`suggestion` must always be a list:\n  " + "\n  ".join(sorted(bad))
        + '\n\nWrite one bottle as `suggestion: ["Beefeater"]`, not as a bare '
          "string. Flow style keeps it to one line."
    )


# --- 3: the family roll-up, which serves search and exclusion, not browsing ---

def test_every_family_is_declared_and_bases_have_one():
    """`family_of` maps base generics to a declared family, and every base
    either has a family or a reason in `family_less`.

    Only bases roll up: "every generic has a family" would fail on
    `lime juice`, and nobody excludes "all juices".
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


# --- 4: spelling collisions ---

def _fold(text):
    stripped = "".join(c for c in unicodedata.normalize("NFD", text)
                       if not unicodedata.combining(c))
    return stripped.lower()


def test_no_two_generics_differ_only_by_case_or_accent():
    """No two declared generics differ only by case or accent.

    Two spellings of one thing are two filter buttons each holding half the
    drinks, and search folds accents, so the collision is invisible until
    someone browses the buttons. Checked on the declared vocabulary, not the
    drinks.
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


# --- 5: coverage -- an untyped ingredient must be visible, not absent ---

def test_every_ingredient_has_a_generic_or_a_qq():
    """No ingredient may be silently untyped: a declared generic, or `QQ`.

    An absent key reads as "nothing to see" and is invisible to both the
    declared-value check and the retirement check. Not gated on any other key
    of the entry, so it cannot pass over an empty set (#540).
    """
    missing = sorted({f"{slug}: entry with no `generic` key"
                      for slug, generic in _ingredients() if not generic})
    assert not missing, (
        f"{len(missing)} ingredient(s) carry no `generic` key at all:\n  "
        + "\n  ".join(missing[:15])
        + "\n\nEvery ingredient needs a declared generic or the literal QQ. "
          "Absent is not the same as unfinished."
    )


# --- 5a: the one generic that cannot stand on its own ---

# `speciality` always carries a `character`. A tuple, so a second such generic
# is one line.
GENERICS_REQUIRING_A_CHARACTER = ("speciality",)


def test_speciality_gin_declares_a_character():
    """A `speciality` gin carries a non-empty `character`.

    The generic says only what the gin is not (juniper-led); `character` says
    what went in the still. Free text on purpose: gin declares no character
    list, so the value is not checked, only its presence.
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
            # A bare string is as good as a list: Liquid iterates either.
            if isinstance(character, str):
                character = [character] if character.strip() else []
            if not character:
                bad.append(f"{slug}: {item.get('generic') or '?'!r}")
    assert not bad, (
        f"{len(bad)} ingredient(s) typed as a generic that requires a "
        f"`character`, without one:\n  " + "\n  ".join(bad)
        + "\n\nA `speciality` gin is defined by the botanical it pushes -- "
          "cucumber, rose, rhubarb, lemon. Without that the generic says only "
          "'not a London dry', which is what got `flavoured` retired. Free "
          "text: name the thing, no vocabulary to match."
    )


# --- 6 and 7: shape guards on the drinks themselves ---

def test_a_declared_character_vocabulary_is_enforced():
    """A `character` must be declared, for every family that closes its list.

    Only families that declare a `<family>_characters` list are checked, so
    adding a list is what switches enforcement on. Gin declares none on
    purpose. The family comes through `family_of`, never from a name.
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

    One scan for both tests above, so they agree about what "checked" means.
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
                        f"{slug}: {item.get('generic') or '?'!r} -> {value!r} "
                        f"(family {'/'.join(sorted(families))})"
                    )
    return checked, bad, declared


def test_every_rum_generic_has_a_card_name_and_nothing_else_does():
    """Every rum generic has a `card_names` entry, and every entry names a
    declared generic -- #501.

    The card shows a rum's card name when its generic has one, so a rum missing
    from the map silently falls back to the bare generic. An entry for a
    renamed generic is dead weight that reads as live coverage.
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
    # The map may hold non-rum generics; only an entry that is not a declared
    # generic at all fails.
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
    """No two generics share a card name unless the collapse is declared -- #501.

    Two drinks reading the same words for rums that are not interchangeable
    looks fine on the page. A deliberate collapse is listed with its reason in
    `card_names_may_collide`, and an entry there that no longer collides fails.
    There is no length rule on purpose.
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
    """Across the collection, card names cost less room than the generics they
    replace -- #501.

    Aggregate, not per card: a disjunctive rum spends a whole second name, and
    those are the cards where the category does the most work. The card body
    clamps at two lines, so length is how many ingredients a reader can see.
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
            # The baseline is the generic, which is what the card prints for an
            # ingredient with no card name.
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
    """No card shows two different generics under one name -- #501.

    Two entries of the same generic print the name twice and that is correct.
    The failure is two different rums arriving at the same words, which a
    declared collapse in `card_names_may_collide` makes possible.
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
            # Gated on `generic`: an entry without one has no card name.
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

    The key duplicates a string the template builds from two card names. If a
    card name changes, the replacement silently stops applying; if no drink
    asks for the pair any more, the entry reads as live and does nothing.
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
            # Gated on `generic`: an entry without one has no card name.
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


# --- The bottle dictionary -- #529, and the check it unblocks, #534 ---

def _bottles():
    if not BOTTLES.exists():
        pytest.fail("_data/cocktails/bottles.yml is gone. Every test that reads it would skip, not fail, without this line.")
    return _parsed(BOTTLES) or {}


def _bottle_index(data):
    """Every name a bottle answers to, lowercased -> its canonical name.

    Case-insensitive because a suggestion is typed by hand. Aliases and
    canonical names share one namespace: an alias that collides with another
    bottle's real name is the same bug either way.
    """
    out = {}
    for name, entry in (data.get("bottles") or {}).items():
        out[name.strip().lower()] = name
        for alias in (entry or {}).get("aliases") or []:
            out[alias.strip().lower()] = name
    return out


def test_every_bottle_names_a_declared_generic():
    """A bottle's `generic` is a declared generic -- #529.

    A generic that was renamed and not followed here makes the dictionary
    quietly wrong: nothing on any page looks different. Any declared generic
    will do; a bottle need not be a rum.
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

    A name claimed twice makes resolution order-dependent, and #534's
    cross-category check would then turn on dictionary order. Canonical names
    and aliases share one namespace.
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

    `bottles` is what Helen would reach for; `not_reached_for` is what
    qualifies and is deliberately out. A bottle in both is a half-finished
    decision.
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
    """Every `suggestion` names a bottle `bottles.yml` knows -- #529, #534.

    A bottle need not be used by any drink, but a suggestion that resolves to
    nothing is skipped by the cross-category check, which then reports a clean
    run. Known failures are declared in `unresolved_suggestions` with a
    reason, so this fails on the next one; deleting a line there retires it.
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


def test_unresolved_suggestions_has_no_stale_entries():
    """Every `unresolved_suggestions` entry is a string a drink still says -- #585.

    A stale entry reads as outstanding work and silently exempts whatever is
    later written with the same string. Whole collection only. Not the
    reverse: a bottle in `bottles` need not be used by any drink.
    """
    _require_whole_collection("unresolved_suggestions")
    data = _bottles()
    declared = data.get("unresolved_suggestions")
    assert declared is not None, (
        "bottles.yml has no `unresolved_suggestions` key at all. An EMPTY "
        "mapping is a fine state and says 'nothing outstanding'; a MISSING "
        "one silently stops this check and the resolver's exemption from "
        "being kept honest."
    )

    said = set()
    for _, fm in _load():
        for item in (fm.get("ingredients") or []):
            if not isinstance(item, dict):
                continue
            suggestion = item.get("suggestion")
            for name in (suggestion if isinstance(suggestion, list)
                         else [suggestion] if suggestion else []):
                if isinstance(name, str):
                    said.add(name.strip().lower())
    assert said, "no drink carries a suggestion -- the loader has gone stale."

    stale = sorted(k for k in declared if k.strip().lower() not in said)
    assert not stale, (
        f"{len(stale)} entr(ies) in `unresolved_suggestions` name a "
        f"suggestion no drink uses any more:\n  "
        + "\n  ".join(repr(s) for s in stale)
        + "\n\nThe work is done -- delete the line. This block records LIVE "
          "problems, and a spent entry reads as outstanding while also "
          "exempting the string for whoever writes it next."
    )


def test_every_suggestion_is_the_declared_bottle_name():
    """A `suggestion` is the bottle's declared name, not an alias of it -- #701.

    A suggestion renders verbatim on the drink page, so an alias there is
    shorthand the reader shops by, and an alias that repairs stored data can
    never be removed. `test_every_suggested_bottle_resolves` passes on an
    alias, so it cannot catch this; a string that resolves to nothing is that
    test's business and is skipped here.
    """
    data = _bottles()
    index = _bottle_index(data)
    declared = set(data.get("bottles") or {})
    exempt = {k.strip().lower() for k in (data.get("unresolved_suggestions") or {})}
    exempt |= {k.strip().lower() for k in (data.get("not_reached_for") or {})}

    drifted = []
    for slug, fm in _load():
        for item in (fm.get("ingredients") or []):
            if not isinstance(item, dict):
                continue
            suggestion = item.get("suggestion")
            for name in (suggestion if isinstance(suggestion, list)
                         else [suggestion] if suggestion else []):
                key = str(name).strip().lower()
                if name in declared or key in exempt:
                    continue
                canonical = index.get(key)
                if canonical and canonical != name:
                    drifted.append((slug, str(name), canonical))

    assert not drifted, (
        f"{len(drifted)} suggestion(s) name a bottle by an alias rather than by "
        f"its declared name:\n  "
        + "\n  ".join(f"{slug}: {written!r} -> {canonical!r}"
                      for slug, written, canonical in sorted(drifted))
        + "\n\nA suggestion renders verbatim on the drink page, so this is what "
          "the reader shops by. Write the declared name; the alias stays in "
          "bottles.yml for the SEARCH to use."
    )


def test_the_bottle_index_is_exercised():
    """Some ingredient in the collection carries a suggestion.

    Zero means the loader went stale and
    `test_every_suggested_bottle_resolves` is green over nothing. Whole
    collection only: see `_exercised`.
    """
    checked, _ = _suggested_bottle_scan()
    _exercised(
        checked, "the suggested-bottle check",
        "Around forty rum pours name a bottle across the whole collection, so "
        "zero means `family_of` stopped mapping the rum styles or the loader is "
        "stale.")


def _suggested_bottle_scan():
    """(how many suggestions were checked, the ones naming no known bottle).

    One scan for two tests, as `_character_scan`. Every ingredient is scanned,
    not only the rums: every bottle a drink names is declared
    (DECISIONS §9.3.2).
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
                # A `QQ` is the drink saying nobody has chosen a bottle yet: not
                # resolved, and not counted as checked, or it would inflate the
                # figure test_the_bottle_index_is_exercised reads.
                if _unanswered([name]):
                    continue
                checked += 1
                key = name.strip().lower()
                if key in index or key in known or key in excluded:
                    continue
                unresolved.append(f"{slug}: {name!r}")
    return checked, unresolved


def test_a_cross_category_suggestion_carries_a_note():
    """A suggested bottle outside the ingredient's `generic` needs a `note` -- #534.

    The note must exist and `QQ` counts, so a substitution never ships
    unmarked while nothing demands prose Helen has not written. A list generic
    means either would do (#441): it crosses only if the bottle matches none
    of its options. An unresolvable suggestion is skipped here;
    `test_every_suggested_bottle_resolves` owns it.
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
    """Some suggestion in the collection resolves to a known bottle.

    The rule only sees suggestions that resolve, so a bottles.yml that stopped
    matching the collection's spellings would leave it green over nothing.
    Whole collection only: see `_exercised`.
    """
    checked, _ = _cross_category_scan()
    _exercised(
        checked, "the cross-category substitution check",
        "Either bottles.yml stopped matching the collection's spellings, or the "
        "loader is stale.")


_RATIO = re.compile(r"^\d+:\d+$")


def _same_category(bottle_generic, ingredient_generic):
    """Does a bottle's own category cover the one an ingredient asks for?

    The same string, or the same string plus a ratio: a honey is declared
    under flat `honey water`, because the ratio is what is done with it, so a
    drink asking for `honey water 2:1` and suggesting it is not a substitution
    and needs no note. One way only: a bottle typed with a ratio does not
    cover an ingredient asking for the flat generic.
    """
    if bottle_generic == ingredient_generic:
        return True
    if not (isinstance(bottle_generic, str)
            and isinstance(ingredient_generic, str)):
        return False
    head, _, tail = ingredient_generic.rpartition(" ")
    return bool(head == bottle_generic and _RATIO.match(tail))


def _cross_category_scan():
    """(how many resolved suggestions were checked, the unexplained ones).

    One scan for two tests, as `_character_scan`. Every ingredient is scanned,
    not only the rums. A bottle's category is its own entry in bottles.yml,
    never the generic beside the suggestion, or every pair would match (#534).
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
                if any(_same_category(bottle_generic, g) for g in generics):
                    continue
                if item.get("note"):
                    continue
                bad.append(
                    f"{slug}: {item.get('generic') or '?'!r} asks for "
                    f"{generics} and suggests {canonical!r} "
                    f"({bottle_generic!r}) — no note"
                )
    return checked, bad


# AMOUNTS -- one field, and a table that turns it into a number (#571)

_AMOUNT_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(?:/\s*(\d+))?\s*(.*?)\s*$")


def _millilitres(amount, measures):
    """(millilitres, unit) for one `amount` string; (None, unit) if not a volume.

    Raises ValueError when the string cannot be read at all. A bare number is
    an error, never an assumed millilitre figure: the unitless amounts are not
    all one unit, and a wrong guess is out by a factor of thirty. An amount
    with no number, such as `(top)` or `(rinse)`, reads by lookup in
    `non_volumetric`, so the vocabulary stays in `measures:`.
    """
    text = str(amount)
    match = _AMOUNT_RE.match(text)
    if not match:
        unit = " ".join(w for w in text.lower().split()
                        if w not in (measures.get("ignored_words") or []))
        if unit and unit in (measures.get("non_volumetric") or []):
            return None, unit
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

    One scan for two tests, as `_character_scan`.
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
                # The exemption is the drink's own QQ note, not a list of slugs
                # here: a list cannot tell a filled gap from a deleted one, and
                # a note works on a partial corpus.
                if "no unit in the source" in notes or "carries no ml figure" in notes:
                    continue
                bad.append(
                    f"{slug}: amount {item['amount']!r} on "
                    f"{item.get('generic')!r} -- {why}"
                )
            else:
                read += 1
    return read, bad


def test_every_amount_is_readable_as_a_quantity():
    """Every `amount` yields millilitres, or names a declared non-volume -- #571.

    The figure is derived from `measures:` in ingredients.yml, and this is the
    promise the scaler, the alcohol units and the cost are built on. An
    undeclared unit fails here instead of vanishing: add it to `per_ml` if it
    is a volume, to `non_volumetric` if it counts or weighs.
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
    """Amounts are actually being read, not all exempted.

    The QQ escape in `_amount_scan` is per-drink and generous, so a parser
    change that raised on everything would look identical to a clean run.
    """
    read, _ = _amount_scan()
    _exercised(
        read, "the amount table",
        "Every amount in the collection failed to parse, or none was found at "
        "all -- `measures:` or the `amount` key has moved.")


# Only a unit with both forms declared in `non_volumetric` is in scope:
# `pinch`, `strip` and `each` have no declared plural, and demanding one
# would invent vocabulary. `half` and `whole` take no number, so there is no
# count to agree with.
PLURAL_UNITS = {"dash": "dashes", "drop": "drops", "cube": "cubes",
                "leaf": "leaves", "sprig": "sprigs", "wedge": "wedges"}

_COUNTED_AMOUNT = re.compile(r"^\s*(\d+(?:\.\d+)?)\s+(.+?)\s*$")


def _plural_unit_scan():
    """(how many counted amounts were checked, the ones whose form is wrong).

    One scan for two tests, as `_character_scan`.
    """
    declared = set((_vocab().get("measures") or {}).get("non_volumetric") or [])
    pairs = {s: p for s, p in PLURAL_UNITS.items()
             if s in declared and p in declared}
    singulars, plurals = set(pairs), set(pairs.values())

    checked = 0
    bad = []
    for slug, fm in _load():
        for item in (fm.get("ingredients") or []):
            if not isinstance(item, dict):
                continue
            match = _COUNTED_AMOUNT.match(str(item.get("amount", "")))
            if not match:
                continue
            count, unit = float(match.group(1)), match.group(2)
            if unit not in singulars | plurals:
                continue
            checked += 1
            wants_plural = count != 1
            if wants_plural == (unit in plurals):
                continue
            want = pairs[unit] if wants_plural else \
                next(s for s, p in pairs.items() if p == unit)
            bad.append(f"{slug}: {item['amount']!r} should be "
                       f"'{match.group(1)} {want}'")
    return checked, bad


def test_a_counted_unit_agrees_with_its_count():
    """`1 dash`, `2 dashes`: a counted unit agrees with its number.

    `amount` prints on the recipe page and the shopping list as written, and
    `_millilitres` accepts either form, so nothing else sees a `2 dash`. The
    fix is the amount, never `measures:`: both forms stay declared.
    """
    _, bad = _plural_unit_scan()
    assert not bad, (
        "Counted amounts whose unit disagrees with their number:\n  "
        + "\n  ".join(sorted(bad))
        + "\n\nHelen, 2026-09-26: \"'dashes' throughout please, but 'dash' "
          "when it's one.\" Fix the `amount`, not `measures:` -- both forms "
          "are declared on purpose, because both are correct at the right "
          "count. A unit with no declared plural (pinch, sprig, strip, each) "
          "is not checked here at all."
    )


def test_the_plural_unit_rule_is_exercised():
    """Counted amounts are actually being read.

    The scan skips an amount whose unit is outside `PLURAL_UNITS`, so a rename
    in `measures:`, or a change to how `amount` is spelled, would empty this
    check and leave it green.
    """
    checked, _ = _plural_unit_scan()
    _exercised(
        checked, "the counted-unit rule",
        "No counted amount was checked at all -- either `PLURAL_UNITS` no "
        "longer matches what `measures:` declares, or the `amount` shape has "
        "moved.")


US_UNITS = {"oz", "ounce", "ounces", "tsp", "teaspoon", "teaspoons",
            "tbsp", "tablespoon", "tablespoons", "cup", "cups"}

# A barspoon is not a US unit and is still not wanted: it is written as
# millilitres, the same remedy, so the same test checks it.
NOT_UNITS = {"barspoon", "barspoons", "bar-spoon", "bar-spoons"}


def test_no_amount_uses_a_us_unit():
    """Volumes are millilitres: no oz, tsp, tbsp, cup or barspoon in an `amount`.

    A test and not only an ingest instruction, because a transcription copies
    the units its source prints. `oz` and `tsp` stay declared in `measures:`
    on purpose: that table is the conversion record
    test_the_declared_measures_produce_the_figures_the_data_used_to_store
    reads. A dash, a pinch, a cube and a sprig are not US units.
    """
    measures = _vocab().get("measures") or {}
    ignored = {w.lower() for w in (measures.get("ignored_words") or [])}

    checked = 0
    bad = []
    for slug, fm in _load():
        for item in (fm.get("ingredients") or []):
            if not isinstance(item, dict) or item.get("amount") is None:
                continue
            checked += 1
            words = {w.strip(".,").lower() for w in str(item["amount"]).split()}
            hit = (words - ignored) & (US_UNITS | NOT_UNITS)
            if hit:
                bad.append(
                    f"{slug}: {item['amount']!r} on "
                    f"{item.get('generic')!r} -- {sorted(hit)}"
                )

    assert not bad, (
        f"{len(bad)} amount(s) in a US unit or a barspoon:\n  " + "\n  ".join(bad)
        + "\n\nConvert to millilitres using the factors in `measures:` "
          "(1 oz = 30 ml, 1 tsp = 5 ml, 1 barspoon = 5 ml). Transcribe the "
          "DRINK, not the page's "
          "units. If a source qualifies the measure -- a scant or a heaping "
          "one -- print the single figure and put the qualifier in the "
          "ingredient's `note`, per MANUAL 9.4.1: the site states one figure "
          "and does not hedge it."
    )
    assert checked, (
        "No amounts were examined at all, so this compared nothing -- the "
        "collection carried 568 when this was written."
    )


def test_the_declared_measures_produce_the_figures_the_data_used_to_store():
    """The conversions still give the figures the retired `ml:` key held -- #571.

    Anchors, not a round trip: a real pair per declared unit, plus the
    fraction and the ignored word, the two shapes a parser most easily
    misreads (`2/3 oz` read as 2 triples the figure).
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
    """No ingredient carries `ml:`; `amount` is the only quantity -- #571.

    A returning key is read by nothing and can only drift from the string
    beside it. Copying an older drink as a template is how it comes back.
    """
    bad = [f"{slug}: {item.get('generic')!r} has ml: {item['ml']!r}"
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
    """Stored moods equal what taxonomy.yml's rules produce -- #452.

    Moods are stored so that Helen can override one, and a stored value goes
    stale against the rules while looking fine; a drink with no mood cannot be
    reached by browsing. Her corrections, `mood_include` and `mood_exclude`,
    are part of the expected value. Never hand-edit a `mood:` block:
    `python3 scripts/derive_cocktail_moods.py --write` reverts it.
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
        # The script's own function, not a second copy of its steps: a copy
        # drifts when the derivation gains an input.
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
    """A mood correction names a real drink and still changes something -- #452.

    One naming a drink that is gone is inert; one whose mood the rules now
    derive anyway reads as a live reason while doing nothing. Whole collection
    only: on a partial corpus an absent drink looks the same as a deleted one.
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
                bad.append(
                    f"{kind}.{slug}: names no drink in the collection "
                    "(if you have just renamed a drink, the drafts repo may "
                    "simply not be merged yet -- the drafts side merges "
                    "first, DECISIONS.md §11; #855)")
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
    """Every member of `mood_ingredients` is a declared generic or character -- #452.

    A renamed generic does not fail at derivation: the set intersection comes
    back empty and the mood silently stops firing. Characters count as well as
    generics, because a `<family>_characters` value may sit in a set.
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


def test_every_icy_serve_value_is_a_real_one():
    """`mood_serve_ice` names declared `serve.ice` values -- #1147.

    The rule is a set membership, so a value renamed in serve.yml and not in
    taxonomy.yml raises nothing: every drink served that way silently loses
    `ice ice baby`.
    """
    taxonomy = _taxonomy()
    declared = (_serve_vocab() or {}).get("ice") or {}
    assert declared, (
        "serve.yml declares no `ice:` values, so this check compares nothing. "
        "It is the vocabulary `serve.ice` is validated against."
    )

    icy = taxonomy.get("mood_serve_ice") or []
    assert icy, (
        "`mood_serve_ice` is missing from taxonomy.yml. `ice ice baby` reads "
        "it for the serve half of its rule, so without it the mood fires only "
        "on a swizzle, churn or blend -- quietly, on every drink served over "
        "crushed ice or a block."
    )

    unknown = sorted(str(v) for v in icy if str(v) not in declared)
    assert not unknown, (
        "`mood_serve_ice` names serve.ice value(s) that serve.yml does not "
        "declare:\n  " + "\n  ".join(unknown)
        + f"\n\nDeclared values: {sorted(declared)}. A name here that no drink "
          "can carry matches nothing, and the mood goes quiet for every drink "
          "served that way rather than failing. If a value was renamed in "
          "serve.yml, follow it here in the same commit."
    )


def test_every_mood_step_word_list_is_actually_read():
    """Every `mood_step_words` list is read by the derivation -- #1147.

    A declared list nothing reads looks live, and editing it changes no drink.
    This asks the running code, not the source: the real derivation runs over
    the collection through a dict that records which keys were fetched. Every
    rule fetches its list unconditionally; if one ever fetches inside a
    branch, hoist the fetch instead of weakening this.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import derive_cocktail_moods as deriver
    except ImportError:  # pragma: no cover
        pytest.skip("scripts/derive_cocktail_moods.py not importable")

    taxonomy = _taxonomy()
    declared = taxonomy.get("mood_step_words") or {}
    assert declared, (
        "taxonomy.yml has no `mood_step_words`, so this check has nothing to "
        "do. `I want to faff`, `on fire` and `ice ice baby` all read it."
    )

    class Recording(dict):
        """A `mood_step_words` that remembers which lists were asked for."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fetched = set()

        def get(self, key, default=None):
            self.fetched.add(key)
            return super().get(key, default)

    recorded = Recording(declared)
    vocab = _vocab()
    sets = deriver.load_sets(taxonomy, vocab)
    families = set(vocab.get("family_of") or {})

    drinks = list(_load())
    assert drinks, (
        "no drinks loaded, so the derivation never ran and every list would "
        "read as dead."
    )
    for slug, fm in drinks:
        stored = [str(m) for m in (fm.get("mood") or [])]
        deriver.expected_moods(slug, fm, stored, taxonomy, sets,
                               recorded, families)

    dead = sorted(set(declared) - recorded.fetched)
    assert not dead, (
        "`mood_step_words` list(s) that the derivation never reads:\n  "
        + "\n  ".join(dead)
        + "\n\nA declared vocabulary nothing reads is worse than no "
          "vocabulary: it invites an edit that cannot take effect. Either "
          "wire the list into its rule in scripts/derive_cocktail_moods.py, "
          "or delete the block. `ice` sat here dead from 2026-09-05 to "
          "2026-09-20 (#1147) because the rule held a hardcoded copy."
    )


def test_source_names_a_source_and_source_url_holds_the_url():
    """`source` is who, `source_url` is where -- #454. A shape rule only.

    Nothing here asks for coverage: an empty `source` is fine, because a drink
    is a formula and not adapted prose. A URL in `source` prints on the drink
    page where a name belongs and leaves `source_url` unused.
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

    A wrong-but-declared generic is invisible to every other guard: the value
    is valid and nothing contradicts it. The list is the enforcement and
    removing a line is the grant: Helen deletes an entry in the same commit as
    the drink that earns the style, and nobody else does, never to make this
    go green.
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
    """An entry with neither `amount` nor `generic` prints as a raw Hash.

    `_layouts/cocktail.html` renders the structured line when the entry
    carries one of those and otherwise falls to the bare-string branch, where
    Liquid stringifies a dict on a clean build with nothing in the log.
    """
    checked = 0
    bad = []
    for slug, fm in _load():
        for entry in (fm.get("ingredients") or []):
            if not isinstance(entry, dict):
                continue
            checked += 1
            if not (entry.get("amount") or entry.get("generic")):
                bad.append(f"{slug}: {entry!r}")
    assert not bad, (
        "Ingredient entries with nothing the line can render:\n  "
        + "\n  ".join(bad)
        + "\n\nEach needs an `amount` or a `generic`. Without one the drink "
          "page prints the YAML dict itself, on a green build."
    )
    assert checked, "No ingredient entries were scanned, so this compared nothing."


def test_no_drink_writes_plantation():
    """No drink writes `plantation`; Planteray is the brand's name -- #582.

    The rule governs what is written; the aliases in `bottles.yml` govern what
    can be read, and stay so that a suggestion keeps resolving. So this checks
    the drinks (filename, title, generic, suggestion, note) and not the data
    files.
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
            for key in ("generic", "suggestion", "note"):
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
    """A note whose text begins `QQ` is labelled `QQ` -- #572.

    An unresolved note under the default "note" tab reads as a remark about
    the drink. The text keeps its own `QQ` prefix as well: every QQ scanner
    matches the prefix. The converse is not asserted: a `QQ` label over other
    text means Helen has not read it yet (#1258), and
    `test_no_published_drink_carries_a_qq` is the gate.
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
    assert not bad, (
        "QQ notes and their labels disagree:\n  " + "\n  ".join(bad)
        + "\n\nA note whose text begins `QQ` is written as:\n"
          '  - label: "QQ"\n    text: "QQ - ..."\n\n'
          "Both halves, on purpose: the label is what the page shows, the "
          "prefix is what every QQ scanner in this repo matches on."
    )
    assert checked, (
        "No drink notes were scanned at all, so this compared nothing -- the "
        "collection had 170 when this was written."
    )


def test_a_draft_drink_has_a_notes_slot_and_no_unlabelled_note():
    """#1258, the drinks half: somewhere to type, and no imported text unlabelled.

    `tests/test_drafts.py::test_a_draft_has_a_notes_slot_and_no_unlabelled_note`
    is the food half and carries the argument. Drafts only: a published drink
    with nothing to say may write `notes: []`, and its notes are held to
    `test_a_published_drink_note_is_a_filled_pair`.
    """
    bad = []
    for drink in _load_draft_files():
        notes = drink.fm.get("notes")
        if not notes:
            bad.append(f"{drink.slug}: `notes` is {notes!r}, with no slot to "
                       f"type into")
            continue
        for i, note in enumerate(notes, 1):
            if isinstance(note, dict) and note.get("text") \
                    and not note.get("label"):
                bad.append(f"{drink.slug}: note {i} has text and no label")
    assert not bad, (
        "Draft drink(s) Helen would have to retype YAML for:\n  "
        + "\n  ".join(bad)
        + "\n\n`python3 scripts/tidy_drafts.py --only notes --apply` writes "
          'the empty `{label: "", text: ""}` pair into an empty `notes:` and '
          'labels an unlabelled note `"QQ"`. See .claude/commands/'
          "tidy-drafts.md."
    )


def _published_note_problem(note) -> str | None:
    """Why this note is neither a filled pair nor the empty one, or None."""
    if not isinstance(note, dict):
        return f"is a bare {type(note).__name__}, not a `{{label, text}}` mapping"
    missing = sorted({"label", "text"} - set(note))
    if missing:
        return ("is missing " + " and ".join(f"`{k}`" for k in missing)
                + " (check for a key typo, e.g. `note:` for `text:`)")
    extra = sorted(set(note) - {"label", "text"})
    if extra:
        return ("carries " + " and ".join(f"`{k}`" for k in extra)
                + ", which nothing renders")
    if note == {"label": "", "text": ""}:
        return None
    for key in ("label", "text"):
        if not (isinstance(note[key], str) and note[key].strip()):
            return f"has an empty `{key}`"
    return None


def test_a_published_drink_note_is_a_filled_pair():
    """A published drink's note is `{label, text}`, both written or both "".

    The layout skips a note with no text and heads one with no label "note",
    so a half-written note either vanishes or prints under a word nobody
    chose; `note:` typed for `text:` is the usual cause. The pair with both
    halves "" is the slot every draft carries: it prints nothing, and it
    stays through promotion so Helen has somewhere to type. DECISIONS §4.
    """
    bad = []
    checked = 0
    for slug, fm in _load_published():
        for i, note in enumerate(fm.get("notes") or [], 1):
            checked += 1
            problem = _published_note_problem(note)
            if problem is not None:
                bad.append(f"{slug} note {i} {problem} -- {note!r}")
    assert checked, (
        "No published drink carries a note, so this compared nothing -- there "
        "were 39 on 78 drinks when it was written."
    )
    assert not bad, (
        "Published drink note(s) that are not a filled `{label, text}` pair:\n  "
        + "\n  ".join(bad)
        + "\n\nThe label is the word on the note's tab and is Helen's to write. "
          'A drink with nothing to say keeps the empty pair, `label: ""` and '
          '`text: ""`, or writes `notes: []`.'
    )


def test_the_published_note_check_sees_each_broken_shape():
    """The check above passes on today's drinks, so prove each shape fails it."""
    assert _published_note_problem({"label": "Rum", "text": "Any aged rum works."}) is None
    assert _published_note_problem({"label": "", "text": ""}) is None
    for broken in (
        {"label": " ", "text": ""},
        "Any aged rum works.",
        {"label": "Rum", "note": "Any aged rum works."},
        {"label": "Rum", "text": "Any aged rum works.", "note": "x"},
        {"label": "", "text": "Any aged rum works."},
        {"label": "Rum", "text": ""},
        {"label": "Rum", "text": None},
    ):
        assert _published_note_problem(broken), broken


def test_no_method_step_restates_to_serve_or_garnish():
    """A step that opens "Serve" or "Garnish" is another field's fact -- #573.

    Presentation is `to_serve`, and "Garnish with X" restates `garnish:`,
    which then renders twice. The verb is the test: a step that does something
    to a garnish ("Float the lime wheel"), or muddles an ingredient that is
    also the garnish, does not fire, on purpose. MANUAL §9.4.
    """
    checked = 0
    bad = []
    for slug, fm in _load():
        for step in _steps(fm):
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


# THE GLASS GENERATOR -- #1214
# `methods.yml in_the_glass` maps a built-in-the-glass step to a sentence
# with a `<glass>` slot, and `_layouts/cocktail.html` fills it. These
# guard a key that is not a real step, a value that cannot be filled, and
# a template that stops reading the table.

GLASS_SLOT = "<glass>"


def _in_the_glass():
    return _methods().get("in_the_glass") or {}


def test_every_glass_step_key_is_a_canonical_step():
    """Every `in_the_glass` key is a step a drink may actually write.

    A key that matches no canonical step is a rule that never fires, silently:
    the page keeps its step with no glass named (#1214).
    """
    spec = _methods()
    table = _in_the_glass()
    assert table, (
        "methods.yml declares no `in_the_glass:`, so the glass generator has "
        "no table and _layouts/cocktail.html composes nothing. If it was "
        "retired, delete these tests with it."
    )
    unknown = sorted(k for k in table if not _is_canonical_step(k, spec))
    assert not unknown, (
        "`in_the_glass` key(s) that are not canonical steps:\n  "
        + "\n  ".join(repr(k) for k in unknown)
        + "\n\nDeclare the step under `canonical:` first. A key matching no "
          "real step is a rule that never fires, and nothing else would say so."
    )


def test_every_glass_step_value_has_exactly_one_slot():
    """Every `in_the_glass` value is a sentence with one `<glass>` and a full stop.

    Zero slots is a rewrite that loses the glass and looks done. `<glass>` and
    not the `<X>` of `shapes:`: that slot is filled by the drink with an
    ingredient, this one by the page from a field.
    """
    table = _in_the_glass()
    bad = []
    for key, value in sorted(table.items()):
        if value.count(GLASS_SLOT) != 1:
            bad.append(f"{key!r} -> {value!r}: {value.count(GLASS_SLOT)} slots")
        elif not value.endswith("."):
            bad.append(f"{key!r} -> {value!r}: no full stop")
        elif GLASS_SLOT in key:
            bad.append(f"{key!r}: the KEY carries a slot; only the value may")
    assert not bad, (
        "`in_the_glass` value(s) that cannot be filled:\n  " + "\n  ".join(bad)
    )


def test_the_layout_takes_the_glass_sentences_from_methods_yml():
    """The composed glass sentences are the data's, not literals in the template.

    A sentence held in both places drifts when one is reworded, so the
    template must read `in_the_glass`. Matches the assignment, not the
    sentence: a scan for the quoted string fires on the template's own
    comments (MANUAL §12).
    """
    layout = (ROOT / "_layouts" / "cocktail.html").read_text(encoding="utf-8")

    assert "in_the_glass" in layout, (
        "_layouts/cocktail.html never reads `methods.in_the_glass`, so the "
        "table in methods.yml is dead data and every built-in-the-glass drink "
        "is back to naming no glass at all -- silently."
    )

    spelled_out = sorted(
        v for v in _in_the_glass().values()
        if re.search(r'assign\s+shown\s*=\s*"' + re.escape(v[:12]), layout)
    )
    assert not spelled_out, (
        "_layouts/cocktail.html assigns a composed glass sentence as a "
        "literal instead of reading methods.yml:\n  "
        + "\n  ".join(repr(v) for v in spelled_out)
    )

    assert GLASS_SLOT in layout, (
        f"the template never substitutes {GLASS_SLOT!r}, so the slot is "
        "rendered to the reader verbatim."
    )

def test_the_layout_takes_the_twist_step_from_methods_yml():
    """The page's twist sentence is methods.yml's, not a string in the template.

    No literal is assigned to `twist_step`, and the layout reads
    `canonical.express` by index. The order of that list is load-bearing: [0]
    is the drop-in form and [1] the discard form, chosen by whether the
    garnish says "discard". Swapped, every twist-garnished drink gives the
    wrong instruction with every other test green.
    """
    layout = (ROOT / "_layouts" / "cocktail.html").read_text(encoding="utf-8")

    # Match the assignment, not the sentence: a scan for the quoted string
    # fires on the template's own comments, which quote it (MANUAL §12).
    spelled_out = re.findall(
        r'assign\s+twist_step\s*=\s*"[^"]+"', layout
    )
    assert not spelled_out, (
        "_layouts/cocktail.html assigns the twist step as a literal instead of "
        "reading _data/cocktails/methods.yml's `canonical.express`. That is one "
        "fact in two places and it has drifted once already:\n  "
        + "\n  ".join(spelled_out)
    )
    assert "canonical.express" in layout, (
        "_layouts/cocktail.html no longer reads `canonical.express` from "
        "methods.yml. If the twist step has moved somewhere else, move this "
        "test with it -- do not delete it, because the string used to live in "
        "the template and drifted from the declaration."
    )

    express = (_methods().get("canonical") or {}).get("express") or []
    assert len(express) == 2, (
        "methods.yml `canonical.express` must hold exactly two steps -- the "
        "layout indexes it as [0] drop-in and [1] discard. It holds "
        f"{len(express)}."
    )
    assert "drop it in" in express[0], (
        "methods.yml `canonical.express`[0] must be the DROP-IN form; the "
        f"layout takes it for a garnish that does not say 'discard'. It is "
        f"{express[0]!r}."
    )
    assert "discard" in express[1], (
        "methods.yml `canonical.express`[1] must be the DISCARD form; the "
        f"layout takes it for a garnish that says 'discard'. It is "
        f"{express[1]!r}."
    )


def test_the_express_step_names_the_twist():
    """The page says WHICH twist: "Express the lemon twist over the drink...".

    The declared sentences keep "the twist" and the layout swaps the garnish
    in, so both halves are needed: the phrase to replace must be in each
    sentence, and the layout must do the replacing. DECISIONS §9.3.
    """
    express = (_methods().get("canonical") or {}).get("express") or []
    lacking = [s for s in express if "the twist" not in s]
    assert not lacking, (
        "methods.yml `canonical.express` sentence(s) without \"the twist\", "
        "which _layouts/cocktail.html replaces with the garnish's own name:\n  "
        + "\n  ".join(lacking)
    )
    layout = (ROOT / "_layouts" / "cocktail.html").read_text(encoding="utf-8")
    assert layout.count('replace: "the twist", named_twist') == 2, (
        "_layouts/cocktail.html no longer names the twist in both express "
        "forms (drop-in and discard)."
    )


def test_a_bracketed_amount_does_not_repeat_its_use():
    """`amount: "(rinse)"` with `as: "rinse"` prints "(rinse)" once.

    Both fields are required of an unmeasured rinse --
    test_every_ingredient_has_an_amount and
    test_a_method_that_floats_or_rinses_says_so_in_a_field -- so the data
    cannot drop one; the layout skips the use line where the amount is it.
    """
    layout = (ROOT / "_layouts" / "cocktail.html").read_text(encoding="utf-8")
    assert "item.as and amount_shown != use_mark" in layout, (
        "_layouts/cocktail.html prints `as` without checking whether the "
        "amount already says it, so an unmeasured rinse reads \"(rinse)(rinse)\"."
    )


EXPRESS_INTO_BUILD = re.compile(r"\b(stirring glass|mixing glass|shaker|tin)\b", re.I)


def test_no_method_step_opens_with_express():
    """No drink writes the twist step: the layout derives it from `garnish:`.

    A hand-written copy is the same fact in two fields, and the two can
    disagree: a step saying "discard" beside a garnish that does not. The
    emitted wording is `canonical.express` in methods.yml. Fires only on a
    step that opens with "Express"; one that expresses something in passing
    stays, and so does one that expresses INTO the build -- the stirring
    glass, the mixing glass, the shaker or the tin -- which is part of
    making the drink, not its garnish (Helen, DECISIONS §9.3).
    """
    checked = 0
    bad = []
    for slug, fm in _load():
        for step in _steps(fm):
            checked += 1
            if re.match(r"\s*express\b", step, re.I) and not EXPRESS_INTO_BUILD.search(step):
                bad.append(f"{slug}: {step!r}")
    assert not bad, (
        "Method step(s) writing the twist step by hand:\n  " + "\n  ".join(bad)
        + "\n\nDELETE THEM. _layouts/cocktail.html adds \"Express the twist "
          "over the drink then drop it in.\" as the last step of any drink whose "
          "`garnish` names a citrus twist, and \"...then discard it.\" where the "
          "garnish says `(discarded)`, both from `canonical.express` in "
          "methods.yml. Helen's ruling is that no drink writes it. If the drink really does express something, say what it "
          "is doing to the drink and lead with that verb."
    )
    assert checked, (
        "No method steps were scanned at all, so this compared nothing -- the "
        "loader or the key name has moved."
    )


def test_optional_is_a_real_boolean():
    """`optional` is a real boolean, never a quoted string -- #570.

    `optional: "false"` is a non-empty string, so it is true to Liquid and to
    Python while reading as false to a person. No spelling of the field fails
    loudly on its own. `false` is permitted and means the same as absent.
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
                    f"{slug}: {item.get('generic')!r} has "
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

    The word written into `generic` or `suggestion` becomes part of the
    ingredient's name: it reaches the card, the search pool and the recipe
    line, and never reaches `optional`'s own rendering. A method step or a
    note may still discuss what is optional.
    """
    checked = 0
    bad = []
    for slug, fm in _load():
        for item in (fm.get("ingredients") or []):
            if not isinstance(item, dict):
                continue
            for key in ("generic", "suggestion"):
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
          "the text. A word inside `generic`/`suggestion` becomes part "
          "of the ingredient's name -- it reaches the card, the search pool "
          "and the recipe line as though it were the category."
    )
    assert checked, (
        "No ingredient text was scanned at all, so this check compared "
        "nothing. It reads `generic` and `suggestion` across every "
        "drink; an empty scan means the loader or the key names have moved."
    )


def test_to_serve_is_a_string():
    """`to_serve` is one line of presentation, never a list.

    `_layouts/cocktail.html` pipes it through `markdownify`, and Liquid
    stringifies a list into that chain without raising.
    """
    bad = [f"{slug}: to_serve is a {type(fm['to_serve']).__name__}"
           for slug, fm in _load()
           if "to_serve" in fm and not isinstance(fm["to_serve"], str)]
    assert not bad, (
        "to_serve must be a string:\n  " + "\n  ".join(bad)
        + "\n\nIt is ONE line of presentation -- \"over crushed ice, with a "
          "straw\" -- not an ordered list of steps. Steps are `method`."
    )


def test_notes_is_a_list():
    """`notes:` with nothing after it parses as null, not `[]` -- #706.

    `REQUIRED_TOP_LEVEL` only asks that the key is present. A null renders as
    nothing only because the layout tests `page.notes.size > 0` and Liquid's
    `nil.size` is nil.
    """
    bad = [f"{slug}: notes is {fm['notes']!r} ({type(fm['notes']).__name__})"
           for slug, fm in _load()
           if "notes" in fm and not isinstance(fm["notes"], list)]
    assert not bad, (
        "`notes:` must be a list:\n  " + "\n  ".join(bad)
        + "\n\nA drink with no notes writes `notes: []`. A bare `notes:` is "
          "YAML null, which is not an empty list -- it renders as nothing "
          "today only because Liquid's `nil.size` happens to be falsy."
    )


def test_glass_is_a_list():
    """`glass` is an ordered list, first entry preferred.

    A leftover scalar still renders: Liquid iterates a string and produces
    nothing visible, so nothing else would catch one.
    """
    bad = [f"{slug}: glass is a {type(fm['glass']).__name__}"
           for slug, fm in _load()
           if "glass" in fm and not isinstance(fm["glass"], list)]
    assert not bad, (
        "glass must be a list, first entry preferred:\n  " + "\n  ".join(bad)
    )


def test_every_glass_value_is_in_the_vocabulary():
    """Every glass a drink names is a key in glasses.yml `icons:` -- #500.

    An unknown glass renders no icon and no complaint: "absent means no icon"
    is the right default, and it cannot tell a typo from a decision. There is
    no exempt value.
    """
    g = _glasses()
    icons = g.get("icons") or {}
    assert icons, "glasses.yml has no `icons:` -- see the sibling tests."

    # No exemptions. A new one is argued for in an issue first: the value
    # of this check is that an unrecognised glass is a typo, not a decision.
    deliberately_unmapped = set()

    unknown = {}
    for slug, fm in _load():
        for value in fm.get("glass") or []:
            key = str(value).strip().lower()
            if key in icons or key in deliberately_unmapped:
                continue
            unknown.setdefault(key, []).append(slug)

    # Some icons are drawn but no spelling reaches them (the `UNUSED ICONS`
    # note in glasses.yml). For those the generic advice below is wrong:
    # the artwork exists and only a key in `icons:` is missing, so say so
    # per value.
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


# The drinks that named no glass when #491 settled that every recipe has one.
# A closed backlog: empty, and `test_the_glassless_list_has_no_stale_entries`
# fails if a name is added back. `set()`, not `{}`: an empty brace literal is a
# dict, and the set arithmetic below raises TypeError on one.
GLASSLESS_ON_2026_08_27 = set()


def test_every_drink_names_a_glass():
    """Every drink names a glass (#491).

    On a drink page the glass is the hero image, so an empty `glass` is a hole
    where the page's main picture goes. Which glass a drink wants is Helen's
    call and is not derivable from the ingredients: ask, never guess.
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
    """GLASSLESS_ON_2026_08_27 is empty and stays empty (#491, #540).

    Whole collection only: with the drafts absent every listed name would read
    as fixed. A new glassless drink is given a glass, never added to the set.
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
    """Every mood in `taxonomy.yml` sits in exactly one of `mood_groups`.

    cocktails/index.html renders each group by iterating its list, so an
    ungrouped mood gets no button and its drinks cannot be filtered for; a
    grouped name that is not a mood renders a button matching nothing; and a
    mood in two groups renders twice and one click toggles both copies.
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
    """`garnish` is a list, never a bare string.

    `_layouts/cocktail.html` takes its `.size` and joins it; a string answers
    both without raising, so a scalar renders wrongly and nothing fails.
    """
    bad = [f"{slug}: garnish is a {type(fm['garnish']).__name__}"
           for slug, fm in _load()
           if "garnish" in fm and not isinstance(fm["garnish"], list)]
    assert not bad, "garnish must be a list:\n  " + "\n  ".join(bad)


GARNISH = ROOT / "_data" / "cocktails" / "garnish.yml"


def _garnish_vocab():
    return _parsed(GARNISH)


def _declared_garnishes(vocab):
    """Every string under `canonical`, plus the no-garnish marker.

    Derived from the mapping's shape, so a group added to garnish.yml is
    covered without touching this file.
    """
    declared = set()
    for group in (vocab.get("canonical") or {}).values():
        if isinstance(group, list):
            declared |= {g for g in group if isinstance(g, str)}
    marker = vocab.get("no_garnish")
    if isinstance(marker, str):
        declared.add(marker)
    return declared


NO_GARNISH = "no garnish"


def test_every_garnish_is_declared():
    """Every garnish on every drink is declared in `_data/cocktails/garnish.yml`.

    A second spelling of an existing garnish fails here; a new garnish gets a
    line under `canonical`. Nothing requires a `proposals` row to be applied:
    that judgement is Helen's (MANUAL §9.12.1).
    """
    declared = _declared_garnishes(_garnish_vocab())
    assert declared, "garnish.yml declares nothing -- has `canonical` been renamed?"

    checked = 0
    bad = []
    for slug, fm in _load():
        garnish = fm.get("garnish")
        if not isinstance(garnish, list):
            continue          # test_garnish_is_a_list owns that failure
        for g in garnish:
            if not isinstance(g, str):
                continue
            checked += 1
            if g not in declared:
                bad.append(f"{slug}: {g!r}")

    assert not bad, (
        f"{len(bad)} garnish(es) not declared in _data/cocktails/garnish.yml:\n  "
        + "\n  ".join(bad)
        + "\n\nEither it is a new garnish -- add it to the right group under "
          "`canonical` -- or it is a second spelling of one already there, in "
          "which case use the existing string. Case and plurals both count: "
          "`mint sprigs` and `mint sprig` are two entries a reader has to "
          "re-read, which is the whole reason that file exists."
    )
    assert checked, (
        "No drink declares a garnish at all, so this compared nothing -- 124 "
        "carried the key when this was written."
    )


def test_every_garnish_proposal_still_matches_a_real_string():
    """Every key of garnish.yml's `proposals` is a string some drink still says.

    A row whose string is gone reads as outstanding work that is already done.
    Whole collection only.
    """
    _require_whole_collection("a garnish proposal's staleness")

    vocab = _garnish_vocab()
    # The key must exist; empty is the settled state. A missing key would
    # switch this guard off for whatever is proposed next.
    assert "proposals" in vocab, (
        "garnish.yml has no `proposals` key at all. An empty mapping says "
        "'nothing outstanding'; a missing one says nothing, and silently "
        "switches this guard off for whatever is added next."
    )
    proposals = vocab.get("proposals") or {}

    live = set()
    for _slug, fm in _load():
        garnish = fm.get("garnish")
        if isinstance(garnish, list):
            live |= {g for g in garnish if isinstance(g, str)}

    stale = sorted(set(proposals) - live)
    assert not stale, (
        "garnish.yml proposes changes to strings no drink says any more:\n  "
        + "\n  ".join(repr(s) for s in stale)
        + "\n\nDelete the row. It has either been applied already or the drink "
          "that said it has changed, and either way it now describes the "
          "collection as it was rather than as it is."
    )


def test_no_garnish_is_stated_as_no_garnish_and_nothing_else():
    """`["no garnish"]` means decided: this drink takes none. `[]` means nobody
    has filled it in (MANUAL §9.12.1).

    `_layouts/cocktail.html` prints the list, so the stored word is what a
    reader sees. It stands alone and lowercase, and the retired spelling
    `none` fails by name.
    """
    bad = []
    for slug, fm in _load():
        garnish = fm.get("garnish")
        if not isinstance(garnish, list):
            continue          # test_garnish_is_a_list owns that failure
        lowered = [str(g).strip().lower() for g in garnish]
        # `none` is the retired spelling, named as such rather than left to
        # fail as merely undeclared.
        if "none" in lowered:
            bad.append(
                f"{slug}: {garnish!r} -- `none` was renamed to "
                f"{NO_GARNISH!r} on 2026-08-31"
            )
            continue
        if NO_GARNISH not in lowered:
            continue
        if len(garnish) > 1:
            bad.append(
                f"{slug}: {garnish!r} -- {NO_GARNISH!r} alongside a real garnish"
            )
        elif garnish[0] != NO_GARNISH:
            bad.append(
                f"{slug}: {garnish[0]!r} -- must be exactly {NO_GARNISH!r}"
            )
    assert not bad, (
        "Garnish problems:\n  " + "\n  ".join(bad)
        + f"\n\n{NO_GARNISH!r} states a DECISION and must stand alone, "
          "lowercase. Use `[]` for a garnish nobody has chosen yet -- absent is "
          "not the same as deliberately nothing."
    )


def _glasses():
    return _parsed(ROOT / "_data" / "cocktails" / "glasses.yml")


GLASS_ICON_DIR = ROOT / "_includes" / "icons" / "glasses"


def test_drinks_use_the_canonical_glass_spelling():
    """A drink writes the canonical glass name, not one of its aliases (#347).

    `canonical_glasses` in glasses.yml is the whole vocabulary: adding a pair
    there is what enforces it, and an alias absent from it is undecided, not
    blessed. The `icons:` alias map stays, so a slipped alias still draws and
    ingest can read a source's spelling. MANUAL §9.11.1.
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


GLASS_SURVEY = ROOT / "_data" / "cocktails" / "glass_survey.yml"


def _glass_survey():
    return _parsed(GLASS_SURVEY)["survey"]


def test_glass_survey_statistics_are_current():
    """`typical_ml` / `typical_height_mm` in glasses.yml are the survey's sums.

    Runs the same `check` as the script's `--check` (#1238). The figures
    between the markers are generated from glass_survey.yml; a hand edit there
    is a number with no product behind it.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    from glass_survey_stats import check  # noqa: E402

    diff, problems = check()
    assert not (diff or problems), (
        "glasses.yml's surveyed statistics no longer match glass_survey.yml:\n\n"
        + "\n".join(problems) + ("\n" if problems else "") + diff
        + "\nRun: python3 scripts/glass_survey_stats.py --write\n"
          "Fix a figure in the SURVEY, never between the markers."
    )


def test_glass_base_centres_are_current():
    """`base_centre` in glasses.yml is what the published drawings measure.

    Runs the same `check` as the script's `--check`. The glasses page centres
    each label under a drawing's base, not its box, from offsets rasterised
    off the icons; a redraw that moves a handle or a base goes stale here.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    from glass_base_centres import check  # noqa: E402

    diff, _ = check()
    assert not diff, (
        "a glass drawing's base no longer sits where glasses.yml says:\n\n" + diff
        + "\nRun: python3 scripts/glass_base_centres.py --write"
    )


def test_every_glass_type_has_a_sourced_capacity_and_height():
    """Every icon, and every survey-only type, has a capacity and a height.

    An icon no drink uses yet still gets its numbers: the glasses page states
    them for everything it declares.
    """
    g = _glasses()
    want = set(g["all_icons"]) | set(g.get("survey_only_types") or {})
    for block in ("typical_ml", "typical_height_mm"):
        have = g.get(block) or {}
        missing = sorted(k for k in want if not have.get(k))
        extra = sorted(set(have) - want)
        assert not missing and not extra, (
            f"`{block}` in glasses.yml: missing {missing}, unexpected {extra}. "
            "Add survey rows for a missing type; do not type a figure in."
        )


def test_every_survey_row_is_a_sourced_figure():
    """Each row says what product, whose, what the page said, and where."""
    bad = []
    for i, row in enumerate(_glass_survey()):
        where = f"row {i} ({row.get('product')!r})"
        for field in ("glass", "product", "maker", "stated", "source"):
            if not str(row.get(field) or "").strip():
                bad.append(f"{where}: no `{field}`")
        for field in ("capacity_ml", "height_mm"):
            v = row.get(field)
            if v is not None and not (isinstance(v, int) and v > 0):
                bad.append(f"{where}: `{field}` is {v!r}, not a positive whole number or null")
        # A search that came back empty is a finding, and is kept -- but it
        # must say what was looked for, or it is just an empty row.
        if row.get("capacity_ml") is None and row.get("height_mm") is None \
                and not str(row.get("note") or "").strip():
            bad.append(f"{where}: carries neither a capacity nor a height, and no note why")
        if "exclude" in row and not str(row["exclude"]).strip():
            bad.append(f"{where}: `exclude` must say why")
    assert not bad, "glass_survey.yml:\n  " + "\n  ".join(bad)


def test_a_survey_only_type_is_a_spelling_that_draws_another_icon():
    """A `survey_only_types` entry is not itself an icon, and each of its
    spellings draws the icon it says it `draws_as`. The map may be empty."""
    g = _glasses()
    bad = []
    for key, spec in (g.get("survey_only_types") or {}).items():
        if key in g["all_icons"]:
            bad.append(f"{key}: is an icon now, so it needs no survey-only entry")
        for spelling in spec.get("spellings") or []:
            if g["icons"].get(spelling) != spec.get("draws_as"):
                bad.append(f"{key}: {spelling!r} draws {g['icons'].get(spelling)!r}, "
                           f"not {spec.get('draws_as')!r}")
    assert not bad, "survey_only_types:\n  " + "\n  ".join(bad)


def test_every_fit_rule_range_runs_low_to_high():
    """The report flags on the LOW end of each range (the forgiving one); a
    reversed pair would quietly make it the harsh one."""
    rules = _glasses()["fit_rules"]
    ranges = {f"dilution.{k}": v for k, v in rules["dilution"].items()}
    ranges |= {f"ice_space.{k}": v for k, v in rules["ice_space"].items()}
    for k in ("blended_multiplier", "large_cube_ml", "punch_cup_ml"):
        ranges[k] = rules[k]
    bad = [f"{k}: {v}" for k, v in ranges.items()
           if not (isinstance(v, dict) and 0 <= v["low"] <= v["high"])]
    assert not bad, "fit_rules ranges out of order:\n  " + "\n  ".join(bad)


def test_every_mapped_glass_names_an_icon_that_exists():
    """Every value in glasses.yml's `icons:` map names an SVG that exists.

    A missing key only costs an icon. A key naming a missing file sets a
    non-empty `glass_icon`, the layout hands `icons/glasses/<name>.svg` to
    {% include %}, and the build fails. Checked against the directory, not
    `all_icons`, which is itself a written-down list.
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
    """`all_icons` equals the icon directory, in both directions.

    Liquid cannot list `_includes/`, so the inventory is written down. An icon
    with no entry is invisible to `_dev/glasses.html`; an entry with no file
    makes that page {% include %} a missing file, which fails the build.
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
    """`heights_mm` covers every icon and names no icon that is not there.

    The templates scale each glass by these millimetres. A missing key is nil
    in Liquid and `nil | times: 1.0` is 0, so that glass draws at zero height
    with no error; a phantom entry can inflate the tallest-glass figure every
    icon is scaled against. Coverage only: scripts/glass_survey_stats.py
    writes the values.
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
          "-- an invisible gap, not an error. Give the icon's glass type rows "
          "in glass_survey.yml, or a `height_overrides` entry with its reason, "
          "then run `python3 scripts/glass_survey_stats.py --write`."
    )
    bad = sorted(f"{k}={v!r}" for k, v in heights.items()
                 if not isinstance(v, (int, float)) or v <= 0)
    assert not bad, (
        "heights_mm values must be positive numbers, not strings:\n  "
        + "\n  ".join(bad)
        + "\n\nA quoted number is a string, and Liquid's `times` turns a "
          "non-numeric string into 0 -- the same invisible-gap failure."
    )


# `heights_mm` sizes an icon by its viewBox, not its ink, so a drawing that
# does not fill its canvas renders small. Values are the percentage of the
# canvas height the ink spans. Empty, and an entry appearing means a drawing
# reached _includes/ without scripts/normalise_glass_icons.py.
KNOWN_LOOSE_VIEWBOXES = {}
VIEWBOX_FILL_FLOOR = 92.0
VIEWBOX_FILL_TOLERANCE = 3.0


def test_no_glass_artwork_has_a_slack_viewbox():
    """#503. An icon must fill its own canvas, or it renders smaller than declared.

    `heights_mm` scales the viewBox, so empty canvas is lost height, and it
    cannot be seen by reading the file: this rasterises. The tolerance on a
    KNOWN_LOOSE_VIEWBOXES entry is two-sided, so one that is fixed fails until
    it is removed.
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
    """A <g> inside a <g> composes; reading only the outer one misplaces the
    artwork (#599).

    Synthetic on purpose, so the rule holds even if no real icon nests. The
    inner matrix doubles x and shifts y by 10, the outer group translates by
    (100, 1000), so (1, 2) lands at (102, 1012).
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


def test_the_normaliser_keeps_a_circle_and_refuses_a_shape_it_cannot_read():
    """A <circle> in a source drawing is artwork and survives normalising.

    Synthetic on purpose. A filled circle comes out as a path carrying
    `glass-icon-dot` beside the line class; an unfilled one as a plain line;
    and a shape the script does not read stops it by name, never dropped.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    import normalise_glass_icons as N  # inert on import: see its __main__ guard

    def drawing(shape):
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">'
                '<g transform="translate(1,1)">'
                '<path d="M 2,2 L 18,18" style="fill:none" />'
                f'{shape}</g></svg>')

    dot = N.normalise(drawing(
        '<circle style="fill:#4c4c4d;stroke:#4c4c4d" cx="10" cy="5" r="1" />'), "t")
    assert dot.count("<path") == 2, f"the circle did not survive:\n{dot}"
    assert 'class="glass-icon-line glass-icon-dot" d="M 9.00000,5.00000 a 1,1' in dot, (
        f"a FILLED circle should be a two-arc path marked as a dot:\n{dot}")

    ring = N.normalise(drawing(
        '<circle style="fill:none;stroke:#4c4c4d" cx="10" cy="5" r="3" />'), "t")
    assert ring.count("<path") == 2 and "glass-icon-dot" not in ring, (
        f"an UNFILLED circle is a line, not a dot:\n{ring}")

    with pytest.raises(SystemExit, match="<rect>"):
        N.normalise(drawing('<rect x="1" y="1" width="3" height="3" />'), "t")


# The margin scripts/normalise_glass_icons.py pads a fitted canvas with, in
# user units. Ink is allowed to sit this far inside the frame and no distance
# at all outside it.
VIEWBOX_MARGIN = 1.4


def test_no_glass_artwork_is_drawn_outside_its_viewbox():
    """#599. A drawing must fit inside its own canvas, not merely fill it.

    The slack-viewBox test rasterises inside the frame and cannot see ink
    outside it. `heights_mm` scales the viewBox and the cards do not clip the
    svg, so that ink paints, taller than declared. Fix by re-running the fit
    (`fit_viewbox` rewrites only the viewBox), never by editing the path data.
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
    """Fitting a viewBox is a reframe, never a redraw, and is idempotent.

    Path data and the <g transform> come out identical; only the viewBox may
    differ. The normaliser's source folder is gitignored and empty in a fresh
    worktree, so nothing else exercises `fit_viewbox`. Fitting twice must equal
    fitting once, or the canvas creeps on every import.
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
    """Every `display_scale` key is a real icon, and every value is in (0, 1].

    It multiplies a glass's drawn height on a card. A key naming no icon does
    nothing, so the glass it was meant to shrink stays wrong while the data
    file looks like it handles it. Absent means 1, so coverage is not asserted.
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


def test_the_cocktail_drafts_clone_is_in_step():
    """This checkout's rules and `_cocktail_drafts/`'s data agree (#624).

    The first test to read when a cocktails run goes red with drinks in it: a
    rule lives here and its data in a separate repo, so tightening a rule is
    two merges, and between them real drinks fail rules whose migration has
    not arrived. Skips when the clone is absent. See `tests/drafts_schema.py`.
    """
    if not drafts_schema.present("_cocktail_drafts"):
        pytest.skip(
            "`_cocktail_drafts/` is not on this machine, so there is no clone "
            "to be in step with. Clone it to check this -- MANUAL 9.1."
        )
    problem = drafts_schema.mismatch("_cocktail_drafts")
    assert problem is None, problem


def test_meta_ship_is_a_rung_or_off_scale():
    """`meta.ship` is a rung on `ship_scale` or a key of `ship_off_scale`
    ("who knows", "IOU"), on every drink, drafts included. `QQ` is not a ship
    value (#722).

    An unmade drink may publish (#722), so there is no promotion-only version.
    """
    taxonomy = _taxonomy()
    scale = set(taxonomy.get("ship_scale") or [])
    assert scale, "taxonomy.yml has no `ship_scale:` to check against."
    allowed = scale | set(taxonomy.get("ship_off_scale") or {})

    offenders = []
    for slug, fm in _load():
        meta = fm.get("meta")
        if not isinstance(meta, dict):
            offenders.append(f"{slug}: no `meta:` mapping")
            continue
        if meta.get("ship") not in allowed:
            offenders.append(f"{slug}: meta.ship is {meta.get('ship')!r}")

    assert not offenders, (
        "Drink(s) whose `meta.ship` is not a rung or an off-scale value:\n  "
        + "\n  ".join(sorted(offenders))
        + f"\n\nAllowed: {sorted(allowed)}. `QQ` is not one of them -- a drink "
          "Helen has never made says \"who knows\", and one she made and liked "
          "but never rated says \"IOU\"."
    )


def test_ship_agrees_with_made_before():
    """`who knows` is exactly the unmade drinks; every other ship says made (#1413).

    The YOLO filters read `ship` alone, so `chaos only` lists an unmade drink
    only because it says `who knows`. A drink made and not rated is `IOU`;
    leaving it `who knows` would offer it as a gamble.
    """
    bad = []
    for slug, fm in _load():
        meta = fm.get("meta")
        if not isinstance(meta, dict) or not isinstance(meta.get("made_before"), bool):
            continue  # test_made_before_is_a_real_boolean names these
        unmade_word = meta.get("ship") == "who knows"
        if unmade_word == meta["made_before"]:
            bad.append(f"{slug}: made_before {meta['made_before']}, "
                       f"ship {meta.get('ship')!r}")
    assert not bad, (
        "Drink(s) whose `meta.ship` and `meta.made_before` disagree:\n  "
        + "\n  ".join(sorted(bad))
        + "\n\nNever made is `made_before: false` with `ship: \"who knows\"`. "
          "Made but not rated is `made_before: true` with `ship: \"IOU\"`. A "
          "rung means she has made it."
    )


def test_made_before_is_a_real_boolean():
    """`meta.made_before` is unquoted true or false on every drink (#722).

    A quoted "false" is truthy and looks correct in the file; absent means
    nobody has asked. The value gates nothing: `false` is publishable. Not in
    GATE_FLAGS, which names only what `_plugins/publish_gate.rb` reads.
    """
    bad = []
    for slug, fm in _load():
        meta = fm.get("meta")
        if not isinstance(meta, dict):
            bad.append(f"{slug}: no `meta:` mapping")
            continue
        if "made_before" not in meta:
            bad.append(f"{slug}: no `meta.made_before`")
        elif not isinstance(meta["made_before"], bool):
            bad.append(f"{slug}: {meta['made_before']!r} "
                       f"({type(meta['made_before']).__name__})")
    assert not bad, (
        "Drink(s) whose `meta.made_before` is not unquoted true/false:\n  "
        + "\n  ".join(bad)
        + "\n\nHas Helen made this drink? Never quote the value, and never "
          "leave it out -- absent is not false, it means nobody has asked."
    )


def test_every_off_scale_ship_has_a_word():
    """Each `ship_off_scale` value and its word are non-empty and not rungs
    (#722, #1413).

    `_includes/cocktails/ship.html` prints the word for any ship not on
    `ship_scale`. A missing word is nil in Liquid and prints as nothing: the
    ship mark with no word beside it and no error. The words are Helen's to
    change; they must never read as a rating (MANUAL §9.9).
    """
    taxonomy = _taxonomy()
    off = taxonomy.get("ship_off_scale")
    assert isinstance(off, dict) and {"who knows", "IOU"} <= set(off), (
        f"taxonomy.yml's `ship_off_scale` must map at least \"who knows\" and "
        f"\"IOU\" to a word (got {off!r})."
    )

    scale = taxonomy.get("ship_scale") or []
    for value, word in off.items():
        assert isinstance(word, str) and word.strip(), (
            f"`ship_off_scale` gives {value!r} no usable word (got {word!r}), "
            "so its drinks draw the ship mark with nothing beside it, on the "
            "cards AND on the drink page."
        )
        assert value not in scale and word not in scale, (
            f"`ship_off_scale` entry {value!r}: {word!r} is also a rung on "
            "`ship_scale`. An off-scale value must not read as a rating."
        )


def test_the_chaos_lists_name_only_real_ship_values():
    """taxonomy.yml's `chaos` lists name rungs or off-scale values, and share none.

    A misspelt value fails no comparison loudly: its drinks just fall into
    `middle`, the bucket only `I'm open to chaos` shows (#1413).
    """
    taxonomy = _taxonomy()
    known = set(taxonomy.get("ship_scale") or []) | set(taxonomy.get("ship_off_scale") or {})
    chaos = taxonomy.get("chaos") or {}
    assert set(chaos) == {"good", "chaos"}, (
        f"taxonomy.yml `chaos` should have exactly `good` and `chaos` lists, the "
        f"two YOLO buttons that narrow (got {sorted(chaos)})."
    )
    for name, values in chaos.items():
        unknown = sorted(set(values) - known)
        assert not unknown, f"`chaos.{name}` names no real ship value: {unknown}"
    assert not set(chaos["good"]) & set(chaos["chaos"]), (
        "A ship value is in both `chaos.good` and `chaos.chaos`."
    )


def test_suggestion_is_a_string_or_a_list_of_strings():
    """`suggestion` is a string or a list of strings (#499).

    Both shapes are correct: Liquid's `for` treats a bare string as a one-item
    sequence, so one loop renders both (MANUAL §9.10). A mapping or a list of
    lists from an ingest renders as `{"a"=>"b"}` or as nothing.
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


# Suggestions that read as prose and are Helen's to reword (#457). A ratchet:
# a new one fails `test_no_new_prose_suggestions`, and a fixed one fails
# `test_the_known_prose_suggestion_list_has_no_stale_entries` until its line
# goes. `set()`, not `{}`: an empty brace literal is a dict.
KNOWN_PROSE_SUGGESTIONS = set()


def _prose_suggestions():
    """Every (slug, suggestion) that reads as prose rather than a bottle name.

    One definition for the ratchet and the staleness check, so "new offender"
    and "fixed entry" stay complements of each other.
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
    """A `suggestion` names a bottle, it does not explain one (#457, #499).

    The page renders a suggestion as the ingredient headline, so prose there is
    what a reader sees first. The check is a heuristic on connective words and
    length, so it runs as a ratchet against KNOWN_PROSE_SUGGESTIONS: a genuine
    bottle name that trips it is added there with a word about why.
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
    """A reworded suggestion comes off KNOWN_PROSE_SUGGESTIONS (#540).

    Whole collection only: an absent drink has no suggestions, so every pinned
    entry would read as fixed.
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
    """Flag only: a syrup-to-citrus ratio no recipe would use.

    The bounds are wide on purpose. Helen adjusts sugar deliberately (MANUAL
    §9.4.1), so this looks for a transcription error, a figure off by a factor,
    and never for taste.
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

    Zero would mean the `cane sugar syrup` generic prefix or the citrus pattern
    gone stale, leaving the ratio check green over nothing. Whole collection
    only: see `_exercised`.
    """
    checked, _ = _syrup_ratio_scan()
    _exercised(
        checked, "the syrup-to-citrus ratio check",
        "That is implausible for the whole collection -- the `cane sugar syrup` "
        "generic prefix or the citrus pattern has probably gone stale.")


def _syrup_ratio_scan():
    """(how many drinks had both figures, the implausible ratios).

    One scan for both tests: see `_character_scan`.
    """
    citrus = re.compile(r"lime juice|lemon juice|grapefruit juice", re.I)
    measures = _vocab().get("measures") or {}

    def ml(entry):
        """Millilitres derived from `amount` (#571), or 0 for a non-volume.

        If this returned 0 for everything the scan would skip every drink and
        pass; test_the_syrup_ratio_check_is_exercised is what catches that.
        """
        try:
            return _millilitres(entry.get("amount", ""), measures)[0] or 0
        except ValueError:
            return 0

    problems = []
    checked = 0
    for slug, fm in _load():
        items = [i for i in (fm.get("ingredients") or []) if isinstance(i, dict)]
        # `generic` may be a list: see _ingredients().
        def generics(entry):
            g = entry.get("generic")
            return g if isinstance(g, list) else [g] if g else []

        # The prefix picks out the cane syrups only; the demerara generic is
        # outside it on purpose.
        syrup = sum(ml(i) for i in items
                    if any(str(g).startswith("cane sugar syrup")
                           for g in generics(i)))
        # Matches the generic, not `item` (#544): most juice entries carry no
        # `item`, and a sour side read from it would vanish under the
        # `if not (syrup and sour)` skip below.
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


# ---- METHOD STEPS: the dictionary, not an enforcement layer (#290) ----
# Nothing here checks a drink's method: a change to a canonical step is
# proposed in methods.yml and Helen prunes (MANUAL §9.12). These check only
# that the map proposes real canonical forms and that every string it claims
# to have found is still in the collection.

METHODS = ROOT / "_data" / "cocktails" / "methods.yml"


def _methods():
    if not METHODS.exists():
        pytest.fail("_data/cocktails/methods.yml is gone. Every test that reads it would skip, not fail, without this line.")
    return _parsed(METHODS) or {}


def _canonical_steps(spec):
    """Every canonical step, flattened from the verb groups.

    Derived from the mapping's shape, not a hardcoded group list.
    """
    out = set()
    for value in (spec.get("canonical") or {}).values():
        if isinstance(value, list):
            out |= set(value)
    return out


SHAPE_SLOT = "<X>"


def _shape_patterns(spec):
    """Every `shapes:` string as a compiled regex, `<X>` matching one non-empty
    run of text.

    A shape is a canonical sentence with one slot for the ingredient the drink
    names; everything else matches literally, and a filled shape counts as
    canonical wherever a literal would.
    """
    out = []
    for value in (spec.get("shapes") or {}).values():
        if not isinstance(value, list):
            continue
        for shape in value:
            head, _, tail = shape.partition(SHAPE_SLOT)
            out.append((shape, re.compile(
                "^" + re.escape(head) + r"(.+)" + re.escape(tail) + "$")))
    return out


def _is_canonical_step(step, spec):
    """A literal under `canonical:`, or a filled `shapes:` sentence."""
    if step in _canonical_steps(spec):
        return True
    return any(rx.match(step) for _, rx in _shape_patterns(spec))


def test_every_shape_has_exactly_one_slot():
    """A shape carries one `<X>` and ends on a full stop.

    Two slots would be a grammar, and the file's own header says one is the
    limit that keeps it a dictionary. Zero slots is a literal that belongs
    under `canonical:` instead. A missing full stop would let a filled shape
    pass while every literal is a sentence.
    """
    spec = _methods()
    shapes = [s for v in (spec.get("shapes") or {}).values()
              if isinstance(v, list) for s in v]
    assert shapes, (
        "methods.yml declares no `shapes:`, so the slot rule guards nothing. "
        "If shapes were abandoned, delete this test with them."
    )
    bad = [s for s in shapes
           if s.count(SHAPE_SLOT) != 1 or not s.endswith(".")]
    assert not bad, (
        "Shape(s) with other than one `<X>`, or no full stop:\n  "
        + "\n  ".join(repr(s) for s in bad)
    )
    literal = sorted(set(shapes) & _canonical_steps(spec))
    assert not literal, f"declared as BOTH a shape and a literal: {literal}"


def _all_method_steps():
    """Every step in the collection, as (slug, text).

    Through `_steps`, so a `{step, note}` pair arrives as hashable text.
    """
    return [(slug, s) for slug, fm in _load() for s in _steps(fm)]


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
    # A filled `shapes:` sentence is as canonical as a literal.
    bad = sorted(f"{k!r} -> {v!r}" for k, v in (spec.get("proposals") or {}).items()
                 if v != "QQ" and not _is_canonical_step(v, spec))
    assert not bad, (
        "Proposal(s) pointing at a step that is not declared under "
        "`canonical` and fills no `shapes:` sentence:\n  " + "\n  ".join(bad)
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
    overlap = sorted(s for s in (spec.get("proposals") or {})
                     if _is_canonical_step(s, spec))
    assert not overlap, (
        "Step(s) listed as BOTH canonical and as a proposal to be replaced:\n  "
        + "\n  ".join(repr(s) for s in overlap)
        + "\n\nPick one. A canonical step is the destination, never the source."
    )


def test_every_proposal_still_matches_a_real_step():
    """Every key of methods.yml's `proposals` is a step some drink still says.

    A spent row reads as outstanding work. Not the reverse: a step with no
    proposal is the normal case. `proposals` is a worklist, so empty is the
    settled state; what is asserted is that the key exists, since losing it
    would switch this check off. Whole collection only.
    """
    _require_whole_collection("methods.yml's proposal list")
    spec = _methods()
    assert "proposals" in spec, (
        "methods.yml has no `proposals` key at all. An EMPTY map is the "
        "settled state and is fine; a MISSING one silently switches this "
        "check off for whatever gets proposed next. Restore `proposals: {}`."
    )
    proposals = spec.get("proposals") or {}
    live = {s for _, s in _all_method_steps()}
    assert live, "no drink has a method -- the loader has gone stale."
    spent = sorted(set(proposals) - live)
    assert not spent, (
        f"{len(spent)} proposal(s) name a step no drink uses any more:\n  "
        + "\n  ".join(repr(s) for s in spent)
        + "\n\nThe work is done -- delete the row. A spent proposal reads as "
          "outstanding, which is the one thing this file must not get wrong."
    )


# ---- MOOD: the browsing vocabulary (taxonomy.yml, #292) ----

def _taxonomy():
    if not TAXONOMY.exists():
        pytest.fail("_data/cocktails/taxonomy.yml is gone. Every test that reads it would skip, not fail, without this line.")
    return _parsed(TAXONOMY) or {}


def test_every_mood_is_declared():
    """A drink's moods come from taxonomy.yml and nowhere else.

    Moods are derived at ingest and stored on the drink so Helen can override
    one; a hand-edited mood is free text, and a typo is a mood no filter
    button matches.
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
    """`mood` is a list, never a bare string: the templates sort and loop it
    as a list, and a scalar renders wrongly without raising.
    """
    bad = [f"{slug}: mood is a {type(fm['mood']).__name__}"
           for slug, fm in _load()
           if "mood" in fm and not isinstance(fm["mood"], list)]
    assert not bad, "mood must be a list:\n  " + "\n  ".join(bad)


def test_every_drink_carries_a_mood_key():
    """Present even when empty, so "no mood yet" is visible rather than absent.

    An absent key reads as "nothing to see"; `mood: []` reads as "nothing
    matched".
    """
    missing = [slug for slug, fm in _load() if "mood" not in fm]
    assert not missing, (
        f"{len(missing)} drink(s) carry no `mood` key at all: {missing[:10]}.\n"
        f"Use `mood: []` for none. Absent is not the same as empty."
    )


def test_no_mood_covers_more_than_half_the_collection():
    """A mood matching most drinks is not a filter, it is noise.

    A guard rather than a note, because the failure is gradual: a mood stays
    useful until the collection grows past it, and nobody re-measures. Whole
    collection only.
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


# ---- THINGS A CARD NEVER MENTIONS (#580) ----


def test_nothing_on_the_not_on_cards_list_reaches_a_card_or_the_search():
    """Bare `water` is never on a card and never in the search (#580).

    `_plugins/cocktail_card_ingredients.rb` applies `not_on_cards` once per
    drink, and the card line and the search pool both read its
    `card_ingredients`. A template that went back to looping
    `drink.ingredients` would bring back everything the list hides.
    """
    vocab = _vocab()
    hidden = vocab.get("not_on_cards")
    assert hidden, (
        "_data/cocktails/ingredients.yml has no `not_on_cards` list. It is what "
        "keeps bare `water` off the index (#580); without it the plugin passes "
        "everything through."
    )

    template = (ROOT / "cocktails" / "index.html").read_text(encoding="utf-8")
    assert template.count("drink.card_ingredients") == 2, (
        "cocktails/index.html no longer reads `card_ingredients` in BOTH places. "
        "It is needed for the `searchable` capture (what the filter matches) and "
        "for the card's ingredient line (what a reader sees); one without the "
        "other means a word is either invisible but filterable, or printed but "
        "unsearchable -- and looping `drink.ingredients` directly skips the "
        "suppression and the ordering together."
    )
    assert "not_on_cards contains g" not in template, (
        "cocktails/index.html has gone back to applying `not_on_cards` in "
        "Liquid. That is the duplication _plugins/cocktail_card_ingredients.rb "
        "exists to remove; two implementations of one rule is what this test "
        "used to be counting."
    )


def test_nothing_that_decides_a_drink_is_ever_kept_off_a_card():
    """`not_on_cards` never hides a spirit, a lower-proof spirit, a juice or
    bitters (#640).

    Those are tiers 1, 2, 3 and 6 of `_plugins/cocktail_card_ingredients.rb`,
    and hiding one takes it off every card that uses it and out of the search.
    Tiers 4 and 5 are not policed: which syrup, sugar or herb is a staple is
    Helen's judgement, and no rule separates them.
    """
    vocab = _vocab()
    protected = {}
    for tier, sections in sorted(_tier_sections().items()):
        if tier not in (1, 2, 3, 6):
            continue
        for section in sections:
            for generic in vocab.get(section) or []:
                protected[str(generic)] = (tier, section)

    for value in vocab.get("not_on_cards") or []:
        hit = protected.get(str(value))
        assert hit is None, (
            f"`not_on_cards` names {value!r}, which _data/cocktails/"
            f"ingredients.yml declares in `{hit[1]}` -- tier {hit[0]} of the "
            f"card ordering, i.e. a spirit, a lower-proof spirit, a juice or "
            f"bitters. Those are what a card is FOR. Hiding this would take it "
            f"off every card that pours it and out of the search pool with it."
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


# ---- THE CARD'S INGREDIENT LINE (#567, #640, #691) ----
# _plugins/cocktail_card_ingredients.rb ranks a generic by which section of
# ingredients.yml declares it. A section renamed there and not in the plugin's
# TIERS drops its generics into the unclassified tier with only a build
# warning; these tests are what fails.

CARD_PLUGIN = ROOT / "_plugins" / "cocktail_card_ingredients.rb"


def _plugin_source():
    if not CARD_PLUGIN.exists():
        pytest.fail("_plugins/cocktail_card_ingredients.rb is gone. Every test that reads it would skip, not fail, without this line.")
    return CARD_PLUGIN.read_text(encoding="utf-8")


def _tier_sections():
    """The section names the plugin's TIERS constant claims, tier by tier.

    Parsed out of the Ruby, not restated here, so the two cannot disagree.
    """
    src = _plugin_source()
    block = re.search(r"TIERS\s*=\s*\{(.*?)\}\.freeze", src, re.S)
    assert block, "Cannot find the TIERS constant in the card plugin."
    out = {}
    for tier, body in re.findall(r"(\d+)\s*=>\s*%w\[([^\]]*)\]", block.group(1)):
        out[int(tier)] = body.split()
    assert out, "TIERS parsed as empty; the constant's shape has changed."
    return out


def test_every_section_the_card_plugin_sorts_by_still_exists():
    """TIERS names sections of ingredients.yml, and all of them are real.

    A section renamed in ingredients.yml and not in the plugin raises nothing:
    every generic in it moves to the unclassified tier and the cards reorder
    slightly (#653, #654).
    """
    vocab = _vocab()
    missing = []
    for tier, sections in sorted(_tier_sections().items()):
        for section in sections:
            if not isinstance(vocab.get(section), list):
                missing.append(f"tier {tier}: {section}")
    assert not missing, (
        "The card plugin sorts by these sections of "
        "_data/cocktails/ingredients.yml and they are not there (renamed? "
        "removed?). Every generic in them is now sorted as 'unclassified':\n  "
        + "\n  ".join(missing)
    )


def test_no_generic_is_declared_in_two_sections_the_plugin_ranks():
    """A generic in two ranked sections has two tiers.

    The card order would resolve it by whichever section the plugin read last.
    """
    vocab = _vocab()
    seen = {}
    duplicated = []
    for tier, sections in sorted(_tier_sections().items()):
        for section in sections:
            for generic in vocab.get(section) or []:
                key = str(generic)
                if key in seen and seen[key] != tier:
                    duplicated.append(f"{key}: tier {seen[key]} and tier {tier}")
                seen[key] = tier
    assert not duplicated, (
        "These generics are declared in two sections that the card plugin ranks "
        "differently, so their position on a card is decided by read order:\n  "
        + "\n  ".join(sorted(set(duplicated)))
    )


def test_every_poured_generic_has_a_tier(drink_file):
    """Every generic a drink's card lists is declared in a section TIERS ranks.

    The plugin only warns at build time and puts an unplaceable ingredient in
    the unclassified tier, so this is what makes somebody fix it.
    """
    _require_drink(drink_file)
    vocab = _vocab()
    hidden = set(vocab.get("not_on_cards") or [])

    placed = set()
    for sections in _tier_sections().values():
        for section in sections:
            placed.update(str(g) for g in (vocab.get(section) or []))

    unplaced = []
    for ing in drink_file.fm.get("ingredients") or []:
        if not isinstance(ing, dict) or ing.get("card_order") is not None:
            continue
        generics = ing.get("generic")
        generics = [generics] if isinstance(generics, str) else (generics or [])
        generics = [str(g) for g in generics]
        if generics and all(g in hidden for g in generics):
            continue
        if _unanswered(generics):
            continue        # nobody has typed it yet -- see `_unanswered`
        for g in generics:
            if g not in placed:
                unplaced.append(g)

    assert not unplaced, (
        f"{drink_file.slug} pours these, and no section of ingredients.yml that "
        f"the card plugin ranks declares them -- so they sort into the "
        f"unclassified tier:\n  " + "\n  ".join(sorted(set(unplaced)))
    )


def test_things_kept_off_cards_are_real_generics():
    """`not_on_cards` names things that exist, and exactly.

    Matching is exact (#580): bare `water`, never `honey water` or `soda
    water`. A typo matches nothing, so the ingredient goes on being printed
    while the list looks as if it works.
    """
    vocab = _vocab()
    declared = set()
    for key, value in vocab.items():
        if isinstance(value, list) and not key.startswith("retired_"):
            declared.update(str(v) for v in value if isinstance(v, str))

    unknown = sorted(set(vocab.get("not_on_cards") or []) - declared)
    assert not unknown, (
        "`not_on_cards` in _data/cocktails/ingredients.yml names these, and no "
        "section declares them, so each one hides nothing:\n  "
        + "\n  ".join(unknown)
    )


def test_always_fresh_juices_are_declared_generics_the_layout_reads():
    """`always_fresh` (#707) names declared generics, and the layout reads it.

    A typo prefixes "fresh " onto a generic no drink uses; a key renamed in
    `_layouts/cocktail.html` alone leaves the list declared and never read.
    Neither fails anywhere else.
    """
    vocab = _vocab()
    always_fresh = vocab.get("always_fresh") or []
    assert always_fresh, (
        "_data/cocktails/ingredients.yml declares no `always_fresh` juices -- "
        "either the key was renamed or #707's list was emptied by mistake."
    )
    declared = _declared_generics(vocab)
    unknown = sorted(set(always_fresh) - declared)
    assert not unknown, (
        "`always_fresh` names these, and no vocabulary section declares them, "
        "so each one is a typo or a retired spelling:\n  "
        + "\n  ".join(unknown)
    )

    layout = (ROOT / "_layouts" / "cocktail.html").read_text(encoding="utf-8")
    assert "always_fresh" in layout, (
        "_layouts/cocktail.html no longer reads `always_fresh`, so #707's "
        "juices are declared but nothing prefixes them with \"fresh \" on the "
        "drink page."
    )


def test_standing_notes_key_declared_generics_the_layout_reads():
    """`standing_notes` (#707) keys declared generics, and the layout reads it.

    `test_every_generic_is_declared` walks from a drink to the vocabulary, so a
    typo'd key here attaches its note to nothing on a green suite.
    """
    vocab = _vocab()
    standing_notes = vocab.get("standing_notes") or {}
    assert standing_notes, (
        "_data/cocktails/ingredients.yml declares no `standing_notes` -- "
        "either the key was renamed or #707's pineapple note was deleted by "
        "mistake."
    )
    declared = _declared_generics(vocab)
    unknown = sorted(set(standing_notes) - declared)
    assert not unknown, (
        "`standing_notes` keys these, and no vocabulary section declares "
        "them, so each note is attached to a generic no drink can pour:\n  "
        + "\n  ".join(unknown)
    )

    layout = (ROOT / "_layouts" / "cocktail.html").read_text(encoding="utf-8")
    assert "standing_notes" in layout, (
        "_layouts/cocktail.html no longer reads `standing_notes`, so #707's "
        "pineapple warning is declared but nothing renders it on the drink "
        "page."
    )


def test_the_citrus_that_sorts_first_is_juice_that_exists():
    """Every name in the card plugin's CITRUS list is a declared juice -- #567.

    CITRUS is the one place the plugin overrides volume within a tier, so a name
    that matches nothing silently returns the juices to plain volume order.
    """
    src = _plugin_source()
    block = re.search(r"CITRUS\s*=\s*\[(.*?)\]\.freeze", src, re.S)
    assert block, "Cannot find the CITRUS constant in the card plugin."
    citrus = re.findall(r'"([^"]+)"', block.group(1))
    assert citrus, "CITRUS parsed as empty; the constant's shape has changed."

    juices = {str(j) for j in (_vocab().get("juices") or [])}
    assert juices, "ingredients.yml declares no `juices:`."
    unknown = sorted(set(citrus) - juices)
    assert not unknown, (
        "The card plugin's CITRUS list names these and `juices:` in "
        "ingredients.yml does not declare them, so they sort as ordinary "
        "juice:\n  " + "\n  ".join(unknown)
    )


# ==== House style: INGEST_ONE_COCKTAIL.md §7 (#670) ==========================
# tests/test_style.py is parametrised over the food recipes only, so these
# apply the same predicates (conftest's) to a drink. The field lists are this
# file's: where to look for a fault is drink-specific.

# Lines no house-style rule may touch, beside the `QQ` lines
# `conftest.checkable_text` blanks: a `suggestion` is a bottle, spelled as its
# label spells it, and `source` / `source_url` are a citation reproduced as
# published.
VERBATIM_KEYS = ("suggestion", "source", "source_url")
_VERBATIM_LINE = re.compile(
    rf"^(?:-\s*)?(?:{'|'.join(VERBATIM_KEYS)}):(?P<value>.*)$"
)


def _checkable(drink):
    """`drink.raw` with QQ lines and verbatim-field lines blanked.

    Blanked, not dropped, so line numbers survive into failure messages. A
    verbatim key with an empty value opens a block (`suggestion:` then an
    indented list), so the lines under it are blanked too.
    """
    out, block_indent = [], None
    for line in checkable_text(drink.raw).split("\n"):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if block_indent is not None:
            if not stripped or indent > block_indent:
                out.append("")
                continue
            block_indent = None
        match = _VERBATIM_LINE.match(stripped)
        if match:
            out.append("")
            if not match.group("value").strip():
                block_indent = indent
            continue
        out.append(line)
    return "\n".join(out)


def _prose_fields(drink):
    """Every stretch of Helen's own prose on a drink, tagged with where it is.

    Free prose only. The closed vocabularies (`glass`, `garnish`, `mood`,
    `generic`, the characters) are spelled by their declarations in
    `_data/cocktails/`, and VERBATIM_KEYS are somebody else's words. `QQ`
    values are dropped.
    """
    fields = []
    for key in ("title", "tagline", "to_serve"):
        value = drink.fm.get(key)
        if isinstance(value, str) and value.strip():
            fields.append((key, value))
    for i, step in enumerate(drink.fm.get("method") or [], 1):
        # Both halves of a `{step, note}` pair are prose. Reading only a string
        # step would exempt every step written in the mapping shape.
        if isinstance(step, str):
            fields.append((f"method step {i}", step))
        elif isinstance(step, dict):
            if isinstance(step.get("step"), str):
                fields.append((f"method step {i}", step["step"]))
            if isinstance(step.get("note"), str):
                fields.append((f"method step {i} note", step["note"]))
    for i, note in enumerate(drink.fm.get("notes") or [], 1):
        if isinstance(note, dict):
            for part in ("label", "text"):
                if isinstance(note.get(part), str):
                    fields.append((f"note {i} {part}", note[part]))
        elif isinstance(note, str):
            fields.append((f"note {i}", note))
    for i, ingredient in enumerate(drink.fm.get("ingredients") or [], 1):
        if isinstance(ingredient, dict) and isinstance(ingredient.get("note"), str):
            fields.append((f"ingredient {i} note", ingredient["note"]))
    return [(location, text) for location, text in fields if not is_qq(text)]


# The string-valued top-level keys only. The `meta:` booleans must never be
# quoted: a quoted one is the string "true", which the publish gate reads as
# neither true nor false (test_the_gate_flags_are_real_booleans). `meta.ship`
# is checked by test_meta_ship_is_a_rung_or_off_scale.
DRINK_SCALAR_FIELDS = ["title", "tagline", "snippet", "source", "source_url",
                       "to_serve"]


def test_the_quoted_scalar_list_names_real_drink_fields():
    """Every name in DRINK_SCALAR_FIELDS is a key TOP_LEVEL_KEYS declares.

    `unquoted_scalars` passes an absent field, correctly, since `to_serve` is
    optional -- so a typo or a rename here stops checking instead of failing.
    """
    unknown = sorted(set(DRINK_SCALAR_FIELDS) - TOP_LEVEL_KEYS)
    assert not unknown, (
        f"DRINK_SCALAR_FIELDS names {unknown}, which the schema does not "
        f"declare. A name that matches no field checks nothing and fails "
        f"nothing -- add it to TOP_LEVEL_KEYS_IN_ORDER if it is real, or fix the "
        f"spelling here."
    )


def test_drink_scalar_fields_are_quoted(drink_file):
    """Every string value is quoted -- INGEST_ONE_COCKTAIL §7.

    Read from the raw front matter: a quoted and an unquoted scalar parse
    identically, so the parsed value cannot show how it was written.
    """
    _require_drink(drink_file)
    match = re.match(r"\A---\n(.*?\n)---", drink_file.raw, re.S)
    assert match, f"{_drink_where(drink_file)} has no front matter to read."
    bad = unquoted_scalars(match.group(1), DRINK_SCALAR_FIELDS)
    assert not bad, (
        f"{_drink_where(drink_file)} has unquoted scalar front-matter "
        f"value(s): {bad!r}. Wrap each in double quotes, e.g. "
        f'title: "Fish House Punch". Never the `meta:` booleans.'
    )


def test_drink_front_matter_has_no_duplicate_keys(drink_file):
    """A repeated YAML key is discarded silently; the last one wins -- #1077.

    `yaml.safe_load` accepts duplicates, and every other test reads the parsed
    front matter, where the lost line is already gone. `_StrictLoader` is
    imported from test_front_matter.py so both collections share one loader.
    """
    from test_front_matter import _StrictLoader

    _require_drink(drink_file)
    match = re.match(r"\A---\n(.*?\n)---", drink_file.raw, re.S)
    assert match, f"{_drink_where(drink_file)} has no front matter to read."
    try:
        yaml.load(match.group(1), Loader=_StrictLoader)
    except yaml.constructor.ConstructorError as exc:
        raise AssertionError(
            f"{_drink_where(drink_file)} has a duplicate key in its front "
            f"matter: {exc}.\nYAML keeps only the LAST one, so whatever the "
            f"earlier line said has already been thrown away. Check what is "
            f"missing from the rendered drink page, not just what looks wrong "
            f"in the file -- every other test here reads the parsed front "
            f"matter and cannot see the discarded line at all."
        ) from None


def test_drink_number_ranges_use_en_dashes(drink_file):
    """`3–4 dashes`, not `3-4 dashes` -- INGEST_ONE_COCKTAIL §7, #670.

    Over the whole file, not only the prose fields: an amount, a method step
    and a note all reach the page (DECISIONS §5).
    """
    _require_drink(drink_file)
    hits = number_range_hits(_checkable(drink_file))
    assert not hits, (
        f"{_drink_where(drink_file)} writes {len(hits)} number range(s) with a "
        f"hyphen: {sorted(set(hits))[:5]}. Ranges take an en dash -- 3–4 "
        f"dashes, 1–4 years old."
    )


# Note text -> reason, for a note exempt from `test_drink_notes_are_sentences`.
# `test_no_drink_note_exception_is_stale` fails an entry whose note has gone.
# A draft's note lives in another repository, so removing a note and its entry
# leaves one suite red until both merge.
DRINK_NOTE_EXCEPTIONS: dict[str, str] = {}


def test_no_drink_note_exception_is_stale():
    """Every DRINK_NOTE_EXCEPTIONS entry still names a note some drink has.

    An exemption that outlives its note exempts that string for whoever writes
    it next. Needs the whole collection: with the drafts absent, an entry for a
    draft's note is indistinguishable from a stale one.
    """
    _require_whole_collection("a stale note exception")

    live = set()
    for slug, fm in _load():
        live.update((text or "").strip() for _, text in notes_of(fm))
    stale = [note for note in DRINK_NOTE_EXCEPTIONS if note not in live]
    assert not stale, (
        f"{len(stale)} DRINK_NOTE_EXCEPTIONS entr(ies) name a note no drink has "
        f"any more:\n  " + "\n  ".join(repr(s) for s in stale)
        + "\n\nThe work is done -- delete the line."
    )


def test_ingredient_as_is_declared(drink_file):
    """`as:` carries a value `ingredient_as` declares -- #754.

    A closed vocabulary nothing checks is an open one: a typo'd `as:` stops
    sorting on the card, and the card still looks plausible. Adding a member is
    Helen's decision.
    """
    _require_drink(drink_file)
    declared = set(_vocab().get("ingredient_as") or [])
    assert declared, "ingredients.yml declares no `ingredient_as` vocabulary."

    bad = []
    for item in (drink_file.fm.get("ingredients") or []):
        if not isinstance(item, dict) or not item.get("as"):
            continue
        if str(item["as"]) not in declared:
            bad.append(f"{item.get('generic')}: {item['as']!r}")

    assert not bad, (
        f"{_drink_where(drink_file)} uses an undeclared `as` value:\n  "
        + "\n  ".join(bad)
        + "\n\nDeclared: " + ", ".join(sorted(declared))
        + ". Adding one is a vocabulary decision -- ingredients.yml."
    )


# The method verbs that imply an `as:` value. Narrow on purpose: the words the
# collection writes, not every synonym English offers.
_AS_VERBS = {"float": ("float",), "rinse": ("rinse",), "muddle": ("muddle",)}

# (slug, `as` value) -> reason, for a drink whose method says the verb and
# whose ingredients do not. An entry claims the drink is wrong, not the rule;
# `test_no_as_exception_is_stale` fails it once the gap closes.
_AS_EXCEPTIONS: dict[tuple[str, str], str] = {}


def test_no_as_exception_is_stale():
    """Every `_AS_EXCEPTIONS` entry still describes a live gap.

    An exemption that outlives its defect reads as outstanding work while
    excusing that drink for whoever edits it next. Needs the whole collection:
    with the drafts absent, an entry for a draft is indistinguishable from a
    stale one.
    """
    _require_whole_collection("a stale `as` exception")

    live = []
    for slug, fm in _load():
        steps = " ".join(
            str(s.get("step") if isinstance(s, dict) else s)
            for s in (fm.get("method") or [])
        ).lower()
        declared = {
            str(i["as"]) for i in (fm.get("ingredients") or [])
            if isinstance(i, dict) and i.get("as")
        }
        for value, verbs in _AS_VERBS.items():
            if any(v in steps for v in verbs) and value not in declared:
                live.append((slug, value))

    stale = [k for k in _AS_EXCEPTIONS if k not in live]
    assert not stale, (
        f"{len(stale)} _AS_EXCEPTIONS entr(ies) no longer describe a real gap:\n  "
        + "\n  ".join(f"{s}: {v}" for s, v in stale)
        + "\n\nThe work is done -- delete the line."
    )


def test_a_method_that_floats_or_rinses_says_so_in_a_field(drink_file):
    """If the method floats, rinses or muddles, an ingredient says `as:` (#754).

    A float recorded only in prose is a fact the card ordering cannot read. A
    garnish float (a lime wheel, coffee beans) is not an ingredient: a float
    whose method names a word of the drink's `garnish` is skipped.
    """
    _require_drink(drink_file)
    steps = " ".join(
        str(s.get("step") if isinstance(s, dict) else s)
        for s in (drink_file.fm.get("method") or [])
    ).lower()

    declared = {
        str(i["as"]) for i in (drink_file.fm.get("ingredients") or [])
        if isinstance(i, dict) and i.get("as")
    }
    garnishes = " ".join(str(g) for g in (drink_file.fm.get("garnish") or [])).lower()

    missing = []
    for value, verbs in _AS_VERBS.items():
        if value in declared:
            continue
        if not any(v in steps for v in verbs):
            continue
        # The method says the word but no ingredient claims it. If the object of
        # the verb is plainly a garnish, that is not this test's business.
        if value == "float" and garnishes:
            words = [w for w in garnishes.replace(",", " ").split() if len(w) > 3]
            if any(w in steps for w in words):
                continue
        if (drink_file.slug, value) in _AS_EXCEPTIONS:
            continue
        missing.append(value)

    assert not missing, (
        f"{_drink_where(drink_file)}'s method says "
        + ", ".join(sorted(missing))
        + " but no ingredient carries the matching `as:` value.\n\n"
        "A float, a rinse or a muddle recorded only in prose is a fact the card "
        "ordering cannot read -- which is how #754 came to undercount the "
        "floats. Add `as:` to the pour it describes, or if the method is "
        "talking about a GARNISH, that is what `garnish:` is for."
    )


def _shell_patterns():
    """The `shapes.shell` sentences as regexes, `<X>` capturing the rum."""
    return [rx for shape, rx in _shape_patterns(_methods())
            if shape in ((_methods().get("shapes") or {}).get("shell") or [])]


def test_a_shell_pour_is_written_one_way(drink_file):
    """A fruit shell of flaming rum is one ingredient and three steps -- #1256.

    One ingredient with `as: "shell"` and a millilitre amount, last but for a
    `(sprinkle)`; the method ends on a `shapes.shell` sentence naming that rum,
    then `canonical.fire`; `garnish` names the shell once, the fruit the method
    fills. Conversely, a method that fills a shell has such an ingredient.
    """
    _require_drink(drink_file)
    fm = drink_file.fm
    items = [i for i in (fm.get("ingredients") or []) if isinstance(i, dict)]
    shells = [i for i in items if str(i.get("as") or "") == "shell"]
    steps = _steps(fm)
    patterns = _shell_patterns()
    assert patterns, "methods.yml declares no `shapes.shell`, so this guards nothing."
    filled = [m for s in steps for rx in patterns for m in [rx.match(s)] if m]

    assert shells or not filled, (
        f"{_drink_where(drink_file)}'s method fills a shell but no "
        "ingredient carries `as: \"shell\"`. The rum is a pour: give it "
        "its own line, a millilitre amount (25 ml unless Helen says "
        "otherwise) and the role."
    )

    problems = []
    if len(shells) > 1:
        problems.append(f"{len(shells)} ingredients say `as: \"shell\"`; one shell, one line")
    for shell in shells[:1]:
        amount = str(shell.get("amount") or "")
        if not re.fullmatch(r"\d+(\.\d+)? ml", amount):
            problems.append(f"the shell pour's amount is {amount!r}, not millilitres")
        after = items[items.index(shell) + 1:]
        if any(str(i.get("amount")) != "(sprinkle)" for i in after):
            problems.append("the shell pour is not the last measured ingredient")

        fire = (_methods().get("canonical") or {}).get("fire") or []
        tail = steps[-(len(fire) + 1):]
        last = next((rx.match(tail[0]) for rx in patterns if rx.match(tail[0])), None) \
            if len(tail) == len(fire) + 1 else None
        if last is None or tail[1:] != fire:
            problems.append(
                "the method does not END on the three shell steps: "
                + " / ".join(["Fill the <fruit> shell with the <rum> and set on "
                              "top of the drink."] + fire))
        else:
            generic = shell.get("generic")
            generic = str(generic[0] if isinstance(generic, list) else generic)
            if not generic.lower().startswith(last.group(1).lower()):
                problems.append(
                    f"the shell step pours {last.group(1)!r} but the "
                    f"`as: \"shell\"` ingredient is {generic!r}")

        shell_garnishes = [str(g) for g in (fm.get("garnish") or [])
                           if "shell" in str(g).lower()]
        if len(shell_garnishes) != 1:
            problems.append(
                f"`garnish` names {len(shell_garnishes)} shells; it must name "
                "the one the rum goes in, so the page mentions the shell "
                "before the ingredients say \"(shell)\"")
        elif last is not None and \
                shell_garnishes[0].replace("half an empty ", "") not in tail[0]:
            problems.append(
                f"`garnish` says {shell_garnishes[0]!r} but the method fills "
                "a different shell")

    assert not problems, (
        f"{_drink_where(drink_file)} writes its flaming shell its own way:\n  "
        + "\n  ".join(problems)
        + "\n\nSee `ingredient_as` in ingredients.yml and `shapes.shell` / "
          "`canonical.fire` in methods.yml."
    )


def _to_serve_items(text):
    """A `to_serve` string as its lowercased items, split on `.` and `,`."""
    return [p.strip().lower() for p in re.split(r"[.,]", text) if p.strip()]


def test_every_to_serve_item_is_declared(drink_file):
    """Each thing a drink is served with is a declared item -- #1256, #1249.

    The field stays one string; the items, split on `.` and `,`, are what is
    closed (`to_serve` in serve.yml). Rum in a shell written here as prose is
    not an item: it belongs in the ingredients, where the units are counted.
    """
    _require_drink(drink_file)
    text = drink_file.fm.get("to_serve")
    text = text if isinstance(text, str) else ""
    groups = _serve_vocab().get("to_serve") or {}
    declared = {i for members in groups.values() for i in members}
    assert declared, "serve.yml declares no `to_serve` vocabulary."

    # An empty `to_serve` has no items and nothing to punctuate.
    bad = [i for i in _to_serve_items(text) if i not in declared]
    assert not bad and (not text.strip() or text.strip().endswith(".")), (
        f"{_drink_where(drink_file)} has `to_serve: {text!r}`"
        + (", with undeclared item(s): " + ", ".join(repr(b) for b in bad)
           if bad else ", which does not end on a full stop")
        + "\n\nDeclared: " + ", ".join(sorted(declared))
        + ".\n\nA POUR is not serveware: rum in a shell is an ingredient with "
          "`as: \"shell\"`. Adding an item is a vocabulary decision -- "
          "_data/cocktails/serve.yml."
    )


def test_drink_notes_are_sentences(drink_file):
    """A note starts with a capital and ends with a full stop -- #711.

    Covers the drink-level `notes:` list and each ingredient's `note:`. A QQ
    note is never checked: `notes_of` drops it. DRINK_NOTE_EXCEPTIONS exempts a
    note by its text.
    """
    _require_drink(drink_file)
    problems = [
        f"{where_note}: {text!r} ({', '.join(note_problems(text))})"
        for where_note, text in notes_of(drink_file.fm)
        if (text or "").strip() not in DRINK_NOTE_EXCEPTIONS
        and not note_is_a_sentence(text)
    ]
    assert not problems, (
        f"{_drink_where(drink_file)} has note(s) not styled as a sentence "
        f"(capital letter, trailing full stop):\n  " + "\n  ".join(problems)
    )


@pytest.mark.parametrize("name,pattern,fix", SHARED_TYPOGRAPHY,
                         ids=[name for name, _, _ in SHARED_TYPOGRAPHY])
def test_drink_typography(drink_file, name, pattern, fix):
    """The typography rules that are about English, not about food.

    SHARED_TYPOGRAPHY is conftest's, and test_style.py splices it into its
    larger table for recipes; the rest of that table is food's own.
    """
    _require_drink(drink_file)
    hits = re.findall(pattern, _checkable(drink_file))
    assert not hits, (
        f"{_drink_where(drink_file)} contains {len(hits)} instance(s) of "
        f"{name}: "
        f"{sorted(set(h if isinstance(h, str) else h[0] for h in hits))[:5]}. "
        f"Fix: {fix}."
    )


# Title Case (#1089). The rule only ever raises a letter: a word outside
# brackets that opens in lowercase is capitalised unless it is a small word
# below, and nothing is lowered. Inside brackets nothing is touched, because
# whether a qualifier is a proper noun is a judgement. Only a spaced word's
# first letter is read, so a hyphenated word is left alone, as is a word
# opening with a digit, a quote or `#`.
TITLE_SMALL_WORDS = frozenset(
    "a an and as at au aux by de del des di du el en for from in la le les "
    "of on or the to with y".split()
)
_TITLE_BRACKETS = re.compile(r"(\([^)]*\))")


def title_cased(title):
    """`title` in the house's Title Case; the same string when it already is.

    `scripts/tidy_drafts.py` imports this, so the fixer and the test cannot
    disagree about a title.
    """
    out, first = [], True
    for chunk in _TITLE_BRACKETS.split(title):
        if chunk.startswith("("):
            out.append(chunk)
            continue
        words = re.split(r"(\s+)", chunk)
        for i, word in enumerate(words):
            if not word or word.isspace():
                continue
            if word[0].islower() and (first or word.lower() not in TITLE_SMALL_WORDS):
                words[i] = word[0].upper() + word[1:]
            first = False
        out.append("".join(words))
    return "".join(out)


@pytest.mark.parametrize("title,want", [
    ("Apple and ginger mulled wine", "Apple and Ginger Mulled Wine"),
    ("Pear, apricot and rosemary Bellini", "Pear, Apricot and Rosemary Bellini"),
    ("Frozen fruit Daiquiri", "Frozen Fruit Daiquiri"),
    ("the last wall highball", "The Last Wall Highball"),
    # Already right, and each one a way to get it wrong.
    ("Margarita (classic)", "Margarita (classic)"),
    ("Fog Cutter (Bramble style)", "Fog Cutter (Bramble style)"),
    ("Del Famoso (The Famous)", "Del Famoso (The Famous)"),
    ("Dark 'n' Stormy (Difford's recipe)", "Dark 'n' Stormy (Difford's recipe)"),
    ("Naked and Famous", "Naked and Famous"),
    ("Between the Sheets", "Between the Sheets"),
    ("Voodoo That You Do", "Voodoo That You Do"),
    ("Daisy de Santiago", "Daisy de Santiago"),
    ("Port au Prince", "Port au Prince"),
    ("Pic-a-de-Crop Punch", "Pic-a-de-Crop Punch"),
    ("Corpse Reviver #2", "Corpse Reviver #2"),
    ("6th Street Swizzle", "6th Street Swizzle"),
    ("Man O' War", "Man O' War"),
    ("L'Isle Martinique", "L'Isle Martinique"),
])
def test_title_case_raises_a_letter_and_never_lowers_one(title, want):
    assert title_cased(title) == want


def test_drink_titles_are_title_case(drink_file):
    """Every drink's title, published or draft, is in Title Case. #1089.

    A `QQ` title is the source's and is left alone, as everywhere else.
    """
    _require_drink(drink_file)
    title = drink_file.fm.get("title")
    checked = isinstance(title, str) and not is_qq(title)
    assert not checked or title == title_cased(title), (
        f"{_drink_where(drink_file)} is titled {title!r}; in Title Case that "
        f"is {title_cased(title)!r}. A qualifier in brackets keeps its own "
        f"case. `python3 scripts/tidy_drafts.py --site cocktails --only "
        f"titles` fixes a draft; a published drink is edited by hand, with "
        f"`proofread: false`."
    )


def test_drink_spellings(drink_file):
    """The declared non-house spellings, shared with the recipes."""
    _require_drink(drink_file)
    problems = spelling_problems(_checkable(drink_file))
    assert not problems, (
        f"{_drink_where(drink_file)} uses non-house spellings: "
        + "; ".join(problems)
    )


def test_drink_temperatures_use_degree_c(drink_file):
    """`°C`, never a bare `C` -- INGEST_ONE_COCKTAIL §7.

    A drink names a temperature rarely enough that the first one to arrive
    unmarked would arrive unnoticed.
    """
    _require_drink(drink_file)
    bad = degreeless_temperatures(_checkable(drink_file))
    assert not bad, (
        f"{_drink_where(drink_file)} writes temperature(s) {bad} without the "
        f"degree sign. Always °C, e.g. 70°C."
    )


def test_drink_accents(drink_file):
    """Words that take an accent have one, per `_data/accented_words.yml`.

    The list is shared with the food site. Scope is `_prose_fields`: Helen's
    own writing, never a bottle name or a citation (see VERBATIM_KEYS).
    """
    _require_drink(drink_file)
    words = accented_words()
    # Asserted, not returned early: an empty list would silence the accent
    # rule across the whole collection while reporting green.
    assert words, (
        "_data/accented_words.yml has no `words:` map, so there is nothing to "
        "check any drink against. That file IS this test's specification -- an "
        "empty one means the accent rule is unenforced, not satisfied."
    )
    problems = accent_problems(_prose_fields(drink_file), words)
    assert not problems, (
        f"{_drink_where(drink_file)} uses unaccented spelling(s):\n  "
        + "\n  ".join(problems)
        + "\n\nIf the word genuinely takes no accent in British usage, add it "
          "to the `no_accent` list in _data/accented_words.yml so nobody "
          "'fixes' it back."
    )


# ==== Costings: _data/cocktails/costs.yml, _plugins/cocktail_costs.rb ========
# A bottle has its own price; a generic has a fallback for an ingredient that
# names no bottle. A generic with no price does not raise: the plugin skips it
# and the drink's total is quietly too low. So the checks that matter run from
# the drinks, not from the price table (MANUAL §12).

COSTS = ROOT / "_data" / "cocktails" / "costs.yml"

# Kept in step with `confidence:` in costs.yml's own header. `low` is not a
# defect -- it is the file admitting which rows Helen should overwrite first.
COST_CONFIDENCE = {"high", "medium", "low"}


def _costs():
    if not COSTS.exists():
        pytest.fail("_data/cocktails/costs.yml is gone. Every test that reads it would skip, not fail, without this line.")
    return _parsed(COSTS) or {}


def _declared_bottles():
    if not BOTTLES.exists():
        pytest.fail("_data/cocktails/bottles.yml is gone. Every test that reads it would skip, not fail, without this line.")
    return (_parsed(BOTTLES) or {}).get(
        "bottles"
    ) or {}


def test_every_declared_bottle_carries_a_price():
    """bottles.yml and costs.yml name exactly the same bottles.

    A bottle with no price drops out of every total that uses it. A price with
    no bottle is usually a bottle renamed in bottles.yml and not followed here,
    so the new name resolves to nothing.
    """
    bottles = _declared_bottles()
    priced = _costs().get("bottles") or {}
    assert bottles, "bottles.yml declares no bottles; nothing to price."

    unpriced = sorted(set(bottles) - set(priced))
    orphaned = sorted(set(priced) - set(bottles))
    assert not unpriced, (
        "These bottles are declared in _data/cocktails/bottles.yml but carry "
        "no price in _data/cocktails/costs.yml, so every pour that names one "
        "is costed as free:\n  " + "\n  ".join(unpriced)
    )
    assert not orphaned, (
        "These rows in _data/cocktails/costs.yml name no bottle in "
        "bottles.yml. A renamed bottle needs its price row renamed too -- the "
        "alias list does not cover this file:\n  " + "\n  ".join(orphaned)
    )


def test_the_price_check_date_is_less_than_two_years_old():
    """costs.yml's `checked:` date is within the last 730 days -- #749.

    The build's `Costs:` log line reports the age; this fails once it passes
    two years. Parsed as a date, so a `checked:` that is not one fails here
    instead of never ageing.
    """
    import datetime

    raw = _costs().get("checked")
    try:
        checked = datetime.date.fromisoformat(str(raw))
    except ValueError:
        pytest.fail(
            f"_data/cocktails/costs.yml `checked:` is {raw!r}, which is not a "
            f"YYYY-MM-DD date, so the prices cannot be said to be any age."
        )
    age = (datetime.date.today() - checked).days
    assert age <= 730, (
        f"_data/cocktails/costs.yml says its prices were checked on "
        f"{checked.isoformat()}, which is {age} days ago -- more than two "
        f"years. Re-read the `high` rows (Master of Malt, by hand -- see the "
        f"file's header) and move `checked:` forward."
    )


def test_every_bottle_price_has_a_size_and_a_confidence():
    """Every priced bottle has a positive `size_ml` and `gbp`, and a confidence.

    Bottles are not all one size, so a price means nothing without one, and
    the plugin skips a bottle that lacks it without raising.
    """
    priced = _costs().get("bottles") or {}
    problems = []
    for name, entry in sorted(priced.items()):
        if not isinstance(entry, dict):
            problems.append(f"{name}: not a mapping")
            continue
        size, gbp = entry.get("size_ml"), entry.get("gbp")
        conf = entry.get("confidence")
        if not isinstance(size, (int, float)) or size <= 0:
            problems.append(f"{name}: size_ml is {size!r}, must be a positive number")
        if not isinstance(gbp, (int, float)) or gbp <= 0:
            problems.append(f"{name}: gbp is {gbp!r}, must be a positive number")
        if conf not in COST_CONFIDENCE:
            problems.append(
                f"{name}: confidence is {conf!r}, must be one of "
                f"{sorted(COST_CONFIDENCE)}"
            )
    assert not problems, (
        "Bad rows in _data/cocktails/costs.yml `bottles:`\n  "
        + "\n  ".join(problems)
    )


def test_a_generic_priced_both_ways_is_deliberate_and_declared():
    """A generic may be both bought and made, but it must say so.

    A generic with priced bottles under it and a row in `generics:` is a
    make-or-buy (the sugar syrups), and the plugin spans both. The row must
    carry a `basis`: an overlap without one is an accident that silently
    widens every total using that generic.
    """
    costs = _costs()
    bottles = _declared_bottles()
    priced_bottles = costs.get("bottles") or {}
    generics = costs.get("generics") or {}

    backed = {
        (b or {}).get("generic")
        for name, b in bottles.items()
        if name in priced_bottles
    }
    undocumented = sorted(
        g
        for g in backed & set(generics)
        if not str((generics[g] or {}).get("basis") or "").strip()
    )
    assert not undocumented, (
        "These generics are priced BOTH by a bottle in bottles.yml and by a "
        "figure in costs.yml `generics:`, with no `basis` explaining the "
        "second one. The two are unioned into one range, so an accidental "
        "overlap silently widens every drink that pours it. Either delete the "
        "fallback, or give it a `basis` saying what it is (a make-or-buy, like "
        "the sugar syrups):\n  " + "\n  ".join(undocumented)
    )


def test_from_fruit_costs_resolve_to_a_yield_and_a_price():
    """`from_fruit` is a join across three blocks; check it lands.

    A squeezed juice is priced from `juice_yields:` in ingredients.yml and
    `fruit_prices:` here (#546), so a typo in either key costs the juice its
    price without a murmur.
    """
    costs = _costs()
    vocab = _vocab()
    yields = vocab.get("juice_yields") or {}
    prices = costs.get("fruit_prices") or {}
    problems = []
    for generic, entry in sorted((costs.get("generics") or {}).items()):
        if not isinstance(entry, dict) or "from_fruit" not in entry:
            continue
        key = entry["from_fruit"]
        y = yields.get(key)
        if not y:
            problems.append(
                f"{generic}: from_fruit {key!r} is not in ingredients.yml "
                f"`juice_yields:`"
            )
            continue
        fruit = y.get("fruit")
        if fruit not in prices:
            problems.append(
                f"{generic}: yields name fruit {fruit!r}, which has no row in "
                f"costs.yml `fruit_prices:`"
            )
            continue
        if not (y.get("ml_min") and y.get("ml_max")):
            problems.append(f"{generic}: {key!r} has no ml_min/ml_max to divide by")
    assert not problems, (
        "Broken `from_fruit` joins in _data/cocktails/costs.yml:\n  "
        + "\n  ".join(problems)
    )


COUNTED_AMOUNT = re.compile(r"^\s*([\d.]+)\s+(whole|each|cubes?)\s*$")
WEIGHED_AMOUNT = re.compile(r"^\s*([\d.]+)\s+g\s*$")


def test_fruit_and_weight_price_rows_are_well_formed():
    """A per-piece or per-kilo row is an ordered pair on a real generic -- #748.

    `fruit_prices` prices a squeezed juice (through `juice_yields`) and a
    counted fruit; `weight_prices` prices a weighed solid. The plugin skips a
    row it cannot read, so a typo'd key or an inverted range fails nothing.
    """
    costs = _costs()
    vocab = _vocab()
    # A `fruit_prices` key is either a generic a drink counts (pear) or the
    # fruit a `juice_yields` entry names (lemon, orange, grapefruit -- which are
    # squeezed, never counted, and are not generics in their own right).
    declared = _declared_generics(vocab) | {
        str((y or {}).get("fruit"))
        for y in (vocab.get("juice_yields") or {}).values()
    }
    problems = []
    for name, row in sorted((costs.get("fruit_prices") or {}).items()):
        if not isinstance(row, dict):
            problems.append(f"fruit_prices {name}: not a mapping")
            continue
        lo, hi = row.get("gbp_min"), row.get("gbp_max")
        if not (isinstance(lo, (int, float)) and isinstance(hi, (int, float)) and 0 < lo <= hi):
            problems.append(f"fruit_prices {name}: gbp_min/gbp_max are {lo!r}/{hi!r}")
        if row.get("confidence") not in COST_CONFIDENCE:
            problems.append(f"fruit_prices {name}: confidence {row.get('confidence')!r}")
        if name not in declared:
            problems.append(f"fruit_prices {name}: not a generic ingredients.yml declares")
    for name, row in sorted((costs.get("weight_prices") or {}).items()):
        if not isinstance(row, dict):
            problems.append(f"weight_prices {name}: not a mapping")
            continue
        lo, hi = row.get("gbp_per_kg_min"), row.get("gbp_per_kg_max")
        # Zero is a price: sugar by weight is free on Helen's word (#1371).
        if not (isinstance(lo, (int, float)) and isinstance(hi, (int, float)) and 0 <= lo <= hi):
            problems.append(f"weight_prices {name}: gbp_per_kg_min/max are {lo!r}/{hi!r}")
        if row.get("confidence") not in COST_CONFIDENCE:
            problems.append(f"weight_prices {name}: confidence {row.get('confidence')!r}")
        if not str(row.get("basis") or "").strip():
            problems.append(f"weight_prices {name}: no basis -- say what shop price the figure came from")
        if name not in declared:
            problems.append(f"weight_prices {name}: not a generic ingredients.yml declares")
    assert not problems, (
        "Bad rows in _data/cocktails/costs.yml:\n  " + "\n  ".join(problems)
    )


def test_every_counted_fruit_and_weighed_solid_has_a_price(drink_file):
    """A counted fruit or a weighed solid finds a price row -- #748.

    A counted ingredient in `fruit_and_herbs` and any `N g` amount must have a
    row, or the plugin treats it as free and the drink's figure is short by it.
    Counted things outside `fruit_and_herbs` (a sugar cube) are free and are
    not asked for.
    """
    _require_drink(drink_file)
    costs = _costs()
    vocab = _vocab()
    fruit = set(vocab.get("fruit_and_herbs") or [])
    fruit_priced = set(costs.get("fruit_prices") or {})
    weight_priced = set(costs.get("weight_prices") or {})

    missing = []
    for ing in drink_file.fm.get("ingredients") or []:
        if not isinstance(ing, dict):
            continue
        amount = str(ing.get("amount", "")).strip()
        generics = ing.get("generic")
        generics = generics if isinstance(generics, list) else [generics]
        generics = [str(g) for g in generics if g]
        if amount == "half" or COUNTED_AMOUNT.match(amount):
            for g in generics:
                if g in fruit and g not in fruit_priced:
                    missing.append(f"{amount} {g}: no `fruit_prices` row")
        elif WEIGHED_AMOUNT.match(amount):
            for g in generics:
                if g not in weight_priced:
                    missing.append(f"{amount} {g}: no `weight_prices` row")
    assert not missing, (
        f"{_drink_where(drink_file)} pours a counted fruit or a weighed solid "
        f"that _data/cocktails/costs.yml cannot price, so it is costed as free "
        f"and the drink's figure is short by it (#748: whole fruit and weighed "
        f"solids are priced):\n  " + "\n  ".join(missing)
    )


def test_excluded_cost_units_are_real_declared_units():
    """Each `excluded_units` entry in costs.yml is a `non_volumetric` unit.

    A typo in that list excludes nothing, and quietly prices something Helen
    ruled out (#547). One direction only: `(top)` is non-volumetric and
    deliberately not excluded, because `top_up_ml` prices it.
    """
    costs = _costs()
    vocab = _vocab()
    declared = set((vocab.get("measures") or {}).get("non_volumetric") or [])
    assert declared, (
        "ingredients.yml declares no `non_volumetric` units, so this test can "
        "check nothing. That file IS this test's specification."
    )
    unknown = sorted(set(costs.get("excluded_units") or []) - declared)
    assert not unknown, (
        "costs.yml `excluded_units` names units that ingredients.yml does not "
        "declare as non-volumetric. A unit that does not exist excludes "
        "nothing:\n  " + "\n  ".join(unknown)
    )


def test_top_up_volumes_cover_every_to_top_pour(drink_file):
    """Every `(top)` ingredient's generic has a volume in costs.yml `top_up_ml`.

    Read by the costing and by assets/js/shopping-list.js. An undeclared top
    costs nothing and falls back to a count on the shopping list, so this runs
    from the drinks.
    """
    _require_drink(drink_file)
    declared = _costs().get("top_up_ml") or {}
    missing = []
    for ing in drink_file.fm.get("ingredients") or []:
        # `(top)` is how a top's amount is spelled (#1217).
        if not isinstance(ing, dict) or str(ing.get("amount", "")).strip() != "(top)":
            continue
        generics = ing.get("generic")
        generics = generics if isinstance(generics, list) else [generics]
        for g in generics:
            if g and str(g) not in declared:
                missing.append(str(g))
    assert not missing, (
        f"{_drink_where(drink_file)} is topped with "
        f"{', '.join(sorted(set(missing)))}, which has no entry in "
        f"_data/cocktails/costs.yml `top_up_ml:`. Add one (a range -- topping "
        f"is not measuring) so the drink costs correctly and the shopping list "
        f"can give a volume instead of a count."
    )


def test_every_priceable_pour_has_a_price(drink_file):
    """A volume-measured ingredient has a price, by bottle or by generic.

    Runs from the drinks: the failure is a drink using a vocabulary the price
    table has not caught up with. Excluded amounts (a dash, a leaf, a sugar
    cube) are free by ruling (#547) and are not asked for.
    """
    _require_drink(drink_file)
    costs = _costs()
    vocab = _vocab()
    bottles = _declared_bottles()

    per_ml = (vocab.get("measures") or {}).get("per_ml") or {}
    excluded = set(costs.get("excluded_units") or [])
    ignored = (vocab.get("measures") or {}).get("ignored_words") or []
    priced_bottles = costs.get("bottles") or {}
    generic_costs = costs.get("generics") or {}

    # A generic is priceable if a priced bottle sits under it, or it has a row.
    backed = {
        (b or {}).get("generic")
        for name, b in bottles.items()
        if name in priced_bottles
    }
    aliases = set()
    for name, b in bottles.items():
        if name not in priced_bottles:
            continue
        aliases.add(name.lower())
        for a in (b or {}).get("aliases") or []:
            aliases.add(str(a).lower())

    unpriced = []
    for ing in drink_file.fm.get("ingredients") or []:
        if not isinstance(ing, dict):
            continue
        amount = str(ing.get("amount", "")).strip()
        if amount in excluded or amount == "(top)":
            continue
        match = re.match(r"^([\d.]+)\s+(.*)$", amount)
        if not match:
            continue
        unit = match.group(2).strip()
        for word in ignored:
            unit = re.sub(rf"^{re.escape(word)}\s+", "", unit)
        if unit in excluded or unit not in per_ml:
            continue  # not a volume: free, by Helen's ruling

        suggestions = ing.get("suggestion")
        suggestions = (
            [suggestions] if isinstance(suggestions, str) else (suggestions or [])
        )
        if any(str(s).lower() in aliases for s in suggestions):
            continue

        generics = ing.get("generic")
        generics = generics if isinstance(generics, list) else [generics]
        if any(g and (str(g) in backed or str(g) in generic_costs) for g in generics):
            continue
        if _unanswered(generics):
            continue        # nobody has typed it yet -- see `_unanswered`
        unpriced.append(f"{amount} {' or '.join(str(g) for g in generics if g)}")

    assert not unpriced, (
        f"{_drink_where(drink_file)} pours these in a VOLUME, so they count "
        f"toward the estimate, but nothing in _data/cocktails/costs.yml prices "
        f"them:\n  " + "\n  ".join(unpriced)
        + "\n\nEither add the bottle to bottles.yml and a price beside it, or "
          "add a `gbp_per_litre_min`/`_max` row under `generics:`. A pour with "
          "no price is not free -- it is missing, and the drink's total is "
          "quietly too low."
    )


def test_default_bottles_are_declared_priced_and_in_the_right_category():
    """`default_bottles` names only real, priced bottles of that generic.

    The block overrides the bottles declared under a generic when pricing it,
    and each mistake is silent: a typo'd or unpriced name contributes no rate,
    and a bottle of the wrong generic prices the category from another spirit
    and still computes cleanly.
    """
    costs = _costs()
    bottles = _declared_bottles()
    priced = costs.get("bottles") or {}
    defaults = costs.get("default_bottles") or {}
    assert defaults, (
        "costs.yml has no `default_bottles`. An EMPTY mapping is a fine state "
        "and means 'no category has been narrowed'; a MISSING one means this "
        "check silently stopped covering Helen's shelf rules."
    )

    problems = []
    for generic, names in sorted(defaults.items()):
        if not isinstance(names, list) or not names:
            problems.append(f"{generic}: must be a non-empty list of bottle names")
            continue
        for name in names:
            if name not in bottles:
                problems.append(
                    f"{generic}: {name!r} is not a bottle in bottles.yml"
                )
            elif name not in priced:
                problems.append(
                    f"{generic}: {name!r} is declared but carries no price, so "
                    f"defaulting to it prices the category from nothing"
                )
            elif (bottles[name] or {}).get("generic") != generic:
                problems.append(
                    f"{generic}: {name!r} is a "
                    f"{(bottles[name] or {}).get('generic')!r}, not a "
                    f"{generic!r} -- this would price the category off the "
                    f"wrong bottle and still compute cleanly"
                )
    assert not problems, (
        "Bad rows in _data/cocktails/costs.yml `default_bottles:`\n  "
        + "\n  ".join(problems)
    )


# ==== Units of alcohol (#297): abv.yml, _plugins/cocktail_units.rb ===========
# As with the costs, the checks that matter run from the drinks. A spirit with
# no strength drops out and the drink reads believably weak, so a zero is
# declared in abv.yml and absence never means zero.

ABV = ROOT / "_data" / "cocktails" / "abv.yml"

# Kept in step with abv.yml's own header, and with COST_CONFIDENCE above.
ABV_CONFIDENCE = {"high", "medium", "low"}

# 96 is roughly the azeotrope: nothing bottled is stronger, so a figure above it
# is a typo. The floor is 0, which is a real value (the syrups).
ABV_MAX = 96

# A UK unit is 10 ml of pure ethanol, so `ml * abv / 1000` units. Pinned here
# as well as in the plugin, because the two must agree.
ML_PER_UNIT = 1000.0


def _abv():
    if not ABV.exists():
        pytest.fail("_data/cocktails/abv.yml is gone. Every test that reads it would skip, not fail, without this line.")
    return _parsed(ABV) or {}


def _generics_with_bottles():
    """Every generic with at least one bottle declared under it."""
    return {(b or {}).get("generic") for b in _declared_bottles().values()} - {None}


def test_every_declared_bottle_has_an_abv():
    """bottles.yml and abv.yml name exactly the same bottles.

    A bottle with no strength counts as water. A row naming no bottle is never
    looked up by the plugin, so it sits there looking authoritative.
    """
    bottles = _declared_bottles()
    strengths = _abv().get("bottles") or {}
    assert bottles, "bottles.yml declares no bottles; nothing to measure."

    unmeasured = sorted(set(bottles) - set(strengths))
    orphaned = sorted(set(strengths) - set(bottles))
    assert not unmeasured, (
        "These bottles are declared in _data/cocktails/bottles.yml but carry no "
        "`abv` in _data/cocktails/abv.yml, so every pour that names one counts "
        "as water:\n  " + "\n  ".join(unmeasured)
    )
    assert not orphaned, (
        "These rows in _data/cocktails/abv.yml name no bottle in bottles.yml. A "
        "renamed or retired bottle needs its row followed here -- the alias list "
        "does not cover this file:\n  " + "\n  ".join(orphaned)
    )


def test_every_strength_is_plausible_and_says_how_sure_it_is():
    """An `abv` is a number from 0 to 96, and every row declares a confidence.

    The lower bound is zero on purpose: a syrup is declared at 0, so a missing
    key is a failure and a zero is a statement.
    """
    data = _abv()
    problems = []
    for block in ("bottles", "generics"):
        for name, row in sorted((data.get(block) or {}).items()):
            if not isinstance(row, dict):
                problems.append(f"{block}/{name}: not a mapping")
                continue
            abv = row.get("abv")
            if isinstance(abv, bool) or not isinstance(abv, (int, float)):
                problems.append(f"{block}/{name}: abv is {abv!r}, not a number")
            elif not 0 <= abv <= ABV_MAX:
                problems.append(f"{block}/{name}: abv {abv} is outside 0-{ABV_MAX}")
            if row.get("confidence") not in ABV_CONFIDENCE:
                problems.append(
                    f"{block}/{name}: confidence {row.get('confidence')!r} is not "
                    f"one of {sorted(ABV_CONFIDENCE)}"
                )
    assert not problems, (
        "Bad rows in _data/cocktails/abv.yml:\n  " + "\n  ".join(problems)
    )


def test_a_low_confidence_strength_says_what_helen_has_to_check():
    """A `confidence: low` row carries a `qq:` saying what Helen has to check.

    The `qq:` rows are her worklist, so a low row without one never reaches
    it. Bitters are exempt (#1012): their strength never reaches a unit figure,
    and scripts/abv_worklist.py skips them the same way.
    """
    data = _abv()
    bitters = set(_vocab().get("bitters") or [])
    bottle_generic = {
        name: (entry or {}).get("generic")
        for name, entry in _declared_bottles().items()
    }
    silent = []
    for block in ("bottles", "generics"):
        for name, row in sorted((data.get(block) or {}).items()):
            if isinstance(row, dict) and row.get("confidence") == "low":
                generic = bottle_generic.get(name) if block == "bottles" else name
                if generic in bitters:
                    continue
                if not str(row.get("qq") or "").strip():
                    silent.append(f"{block}/{name}")
    assert not silent, (
        "These rows in _data/cocktails/abv.yml are `confidence: low` but carry no "
        "`qq:` saying what Helen has to check, so they will never reach her "
        "worklist:\n  " + "\n  ".join(silent)
    )


def test_no_generic_gets_its_strength_from_two_places():
    """A generic takes its strength from its bottles or a figure, never both.

    The plugin takes the bottles, so a declared figure beside them is consulted
    by nobody and drifts. A `non_alcoholic` generic has no strength anywhere.
    """
    data = _abv()
    declared = set(data.get("generics") or {})
    zero = set(data.get("non_alcoholic") or [])
    derived = _generics_with_bottles()

    both = sorted(declared & derived)
    assert not both, (
        "These generics have bottles under them in bottles.yml AND a figure in "
        "abv.yml `generics:`. The bottles win and the figure rots -- delete "
        "it:\n  " + "\n  ".join(both)
    )
    contradicted = sorted(zero & (declared | derived))
    assert not contradicted, (
        "These generics are in `non_alcoholic:` and also given a strength "
        "somewhere. One of the two is wrong:\n  " + "\n  ".join(contradicted)
    )


def _unique_mode(values):
    """The single most common value, or None -- the plugin's `unique_mode`."""
    counts = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    top = max(counts.values())
    winners = [v for v, c in counts.items() if c == top]
    return winners[0] if len(winners) == 1 else None


def test_every_bottled_generic_resolves_to_one_strength():
    """A bottled category has a mode strength, or a default Helen has named.

    An ingredient naming no bottle takes the mode of its category's bottles
    (#1016). Where no single mode exists the plugin falls back to the mean,
    which she ruled against, so this fails and names the category that needs a
    `default_bottles` entry. Bitters are not asked (#1012).
    """
    abv_bottles = _abv().get("bottles") or {}
    defaults = _costs().get("default_bottles") or {}
    bitters = set(_vocab().get("bitters") or [])

    by_generic = {}
    for name, entry in _declared_bottles().items():
        generic = (entry or {}).get("generic")
        row = abv_bottles.get(name)
        if generic and isinstance(row, dict) and row.get("abv") is not None:
            by_generic.setdefault(generic, []).append((name, float(row["abv"])))

    no_answer = []
    for generic, rows in sorted(by_generic.items()):
        if generic in defaults or generic in bitters:
            continue
        if _unique_mode([abv for _, abv in rows]) is None:
            no_answer.append(
                f"{generic}: " + ", ".join(f"{n} {abv:g}%" for n, abv in sorted(rows))
            )

    assert not no_answer, (
        "These categories have no single most common strength and no default "
        "bottle, so an unbottled pour of them has no answer under Helen's mode "
        "rule (#1016) and the units plugin is falling back to the mean she "
        "ruled against:\n  " + "\n  ".join(no_answer)
        + "\n\nAsk Helen which bottle is the default, and add it to "
          "`default_bottles` in _data/cocktails/costs.yml. That also sets the "
          "category's price for an unbottled pour -- tell her so."
    )


def test_every_counted_pour_can_reach_a_strength(drink_file):
    """Every measured ingredient that counts toward units reaches a strength.

    Dashes, leaves and cubes are free, as for cost, and bitters never count
    (#1012). A measured ingredient with no route to a strength contributes
    zero and the drink reads weaker than it is. Runs from the drinks: abv.yml
    cannot answer for a generic it has never heard of.
    """
    _require_drink(drink_file)
    data = _abv()
    costs = _costs()
    vocab = _vocab()
    bottles = _declared_bottles()

    per_ml = (vocab.get("measures") or {}).get("per_ml") or {}
    ignored = (vocab.get("measures") or {}).get("ignored_words") or []
    excluded = set(costs.get("excluded_units") or [])
    top_up = costs.get("top_up_ml") or {}

    measured_bottles = data.get("bottles") or {}
    aliases = set()
    for name, b in bottles.items():
        if name not in measured_bottles:
            continue
        aliases.add(name.lower())
        for a in (b or {}).get("aliases") or []:
            aliases.add(str(a).lower())

    # A generic reaches a strength three ways, matching the plugin exactly.
    reachable = (
        {(b or {}).get("generic") for n, b in bottles.items() if n in measured_bottles}
        | set(data.get("generics") or {})
        | set(data.get("non_alcoholic") or [])
    )

    bitters = set(vocab.get("bitters") or [])

    unmeasured = []
    for ing in drink_file.fm.get("ingredients") or []:
        if not isinstance(ing, dict):
            continue
        amount = str(ing.get("amount", "")).strip()
        generics = ing.get("generic")
        generics = [generics] if isinstance(generics, str) else (generics or [])

        # Bitters never count, whatever the amount (#1012), as in the plugin.
        if generics and all(str(g) in bitters for g in generics):
            continue

        # `(top)` is how a top's amount is spelled (#1217). A top is asked for
        # a strength only when `top_up_ml` gives its generic a volume.
        if amount == "(top)":
            if not any(str(g) in top_up for g in generics):
                continue  # not a topped-up volume we model; contributes nothing
        else:
            if amount in excluded:
                continue
            match = re.match(r"^([\d.]+)\s+(.*)$", amount)
            if not match:
                continue
            unit = match.group(2).strip()
            for word in ignored:
                unit = re.sub(rf"^{re.escape(word)}\s+", "", unit)
            if unit in excluded or unit not in per_ml:
                continue  # not a volume: free, by Helen's ruling

        suggestions = ing.get("suggestion")
        suggestions = (
            [suggestions] if isinstance(suggestions, str) else (suggestions or [])
        )
        if any(str(s).lower() in aliases for s in suggestions):
            continue
        if any(str(g) in reachable for g in generics):
            continue
        if _unanswered(generics):
            continue        # nobody has typed it yet -- see `_unanswered`
        unmeasured.append(f"{amount} {generics or '(no generic)'}")

    assert not unmeasured, (
        f"{drink_file.slug} pours these by volume, and nothing in "
        f"_data/cocktails/abv.yml gives them a strength -- so each counts as 0% "
        f"and the drink reads weaker than it is:\n  " + "\n  ".join(unmeasured)
    )


def test_serves_is_a_count_and_only_where_a_recipe_makes_more_than_one():
    """`serves:`, where present, is a whole number of two or more.

    Absent means one, so `serves: 1` says nothing and `serves: 0` would divide
    the unit count by zero. Which drinks carry it is Helen's judgement and is
    not checked.
    """
    problems = []
    for slug, fm in _load():
        if "serves" not in fm:
            continue
        serves = fm["serves"]
        if isinstance(serves, bool) or not isinstance(serves, int):
            problems.append(f"{slug}: serves is {serves!r}, not a whole number")
        elif serves < 2:
            problems.append(
                f"{slug}: serves is {serves} -- absent already means one, so this "
                f"either says nothing or is a typo"
            )
    assert not problems, (
        "Bad `serves:` values:\n  " + "\n  ".join(problems)
    )


def test_the_unit_formula_and_its_worked_example_still_agree():
    """60 ml of Tanqueray is 2.6 units, and this pins every part of that.

    A worked example ties the constant, the arithmetic and one row of abv.yml
    together, so any of the three moving alone goes red. Tanqueray because
    43.1% is not round: a slip shows in the first decimal place, and it is the
    default bottle behind an unqualified `London dry gin`.
    """
    tanqueray = (_abv().get("bottles") or {}).get("Tanqueray")
    assert tanqueray, "Tanqueray has no row in abv.yml; the example needs one."
    assert tanqueray["abv"] == 43.1, (
        f"Tanqueray is 43.1% and abv.yml now says {tanqueray['abv']}. If the "
        f"bottle really has changed, update the expected figure below with it."
    )
    assert round(60 * tanqueray["abv"] / ML_PER_UNIT, 1) == 2.6, (
        "A 60 ml pour of Tanqueray is 2.586 units, which prints as 2.6. This "
        "failing means the formula, the constant or the data has moved."
    )


# ==== The reference page's reading of the data (#529) ========================

def test_retired_rum_style_keys_split_by_case():
    """A capitalised `retired_rum_styles` key is a bottle; a lowercase, a word.

    cocktails/reference/rum-categories.html shows only the lowercase keys, and
    tells them apart by the first character's case because the data declares no
    kind. "Names a bottle" is a prefix match either way: a retired generic's
    spelling need not equal the bottle's name in bottles.yml.
    """
    vocab = _vocab()
    retired = vocab.get("retired_rum_styles") or {}
    assert retired, "retired_rum_styles is empty; this check has nothing to hold."

    index = _bottle_index(_bottles())

    def names_a_bottle(key):
        k = key.strip().lower()
        return any(k == n or k.startswith(n + " ") or n.startswith(k + " ")
                   for n in index)

    wrong = []
    for key in retired:
        is_capitalised = key[:1] != key[:1].lower()
        is_bottle = names_a_bottle(key)
        if is_capitalised and not is_bottle:
            wrong.append(f"{key!r} is capitalised but names no bottle")
        if not is_capitalised and is_bottle:
            wrong.append(f"{key!r} is lowercase but names a bottle")

    assert not wrong, (
        "retired_rum_styles keys break the case convention:\n  "
        + "\n  ".join(wrong)
        + "\n\ncocktails/reference/rum-categories.html shows the lowercase keys "
          "and hides the capitalised ones, because the first are words a recipe "
          "asks for and the second are bottles whose generic was retired. Either "
          "fix the spelling, or -- if the two kinds genuinely need telling apart "
          "some other way -- declare it in the data and change the page to read "
          "the declaration instead of the case."
    )


def test_rum_groups_partition_the_styles():
    """`rum_groups` places every `rum_styles` member exactly once.

    cocktails/reference/rum-categories.html walks `rum_groups`, so a style in
    no group silently leaves the page, a style in two is listed twice, and a
    group naming an undeclared style is a typo. Each group has a name to print.
    """
    vocab = _vocab()
    styles = vocab.get("rum_styles") or []
    groups = vocab.get("rum_groups") or []
    assert styles and groups, (
        "rum_styles or rum_groups is empty; this check has nothing to hold."
    )

    placed = [s for g in groups for s in (g.get("styles") or [])]

    unknown = sorted(set(placed) - set(styles))
    assert not unknown, (
        "rum_groups names style(s) that rum_styles does not declare:\n  "
        + "\n  ".join(unknown)
        + "\n\nA group is a reading of the vocabulary, never an addition to it."
    )

    unplaced = [s for s in styles if s not in placed]
    assert not unplaced, (
        "rum_style(s) in no group:\n  " + "\n  ".join(unplaced)
        + "\n\ncocktails/reference/rum-categories.html walks rum_groups, so an "
          "unplaced style is invisible on the page with nothing else failing. "
          "Put it on the shelf it belongs on -- that is Helen's call, not an "
          "inference from its name."
    )

    twice = sorted({s for s in placed if placed.count(s) > 1})
    assert not twice, (
        "rum_style(s) in more than one group:\n  " + "\n  ".join(twice)
        + "\n\nThe page would list the category twice under two headings."
    )

    unnamed = [i for i, g in enumerate(groups) if not (g.get("name") or "").strip()]
    assert not unnamed, (
        f"rum_groups entr(ies) with no name: index {unnamed}. The fourth group's "
        f"name is a placeholder in Helen's gift, but it must be a string the "
        f"page can print -- an empty heading renders as a gap."
    )


def test_rum_adjacent_before_names_a_real_group():
    """`rum_adjacent_before` names a shelf in `rum_groups` -- #919.

    The rum page renders the Rum-adjacent block when the current shelf's name
    matches this key, and a Liquid `if` that never matches fails silently: a
    renamed shelf would drop the whole block with every other check green.
    """
    vocab = _vocab()
    groups = vocab.get("rum_groups") or []
    target = vocab.get("rum_adjacent_before")

    assert target, (
        "rum_adjacent_before is missing or empty in "
        "_data/cocktails/ingredients.yml.\n\n"
        "cocktails/reference/rum-categories.html renders the Rum-adjacent block "
        "only when a shelf's name matches it, so without a value the block -- "
        "cachaca, Batavia arrack and coconut-flower arrack -- renders nowhere."
    )

    names = [(g.get("name") or "").strip() for g in groups]
    assert target in names, (
        f"rum_adjacent_before is {target!r}, which names no shelf in "
        f"rum_groups.\n\nThe shelves are:\n  " + "\n  ".join(names)
        + "\n\nIf a shelf was renamed, this key needs the new name -- otherwise "
          "the Rum-adjacent block silently stops rendering (#919)."
    )


def test_no_bottle_under_a_combined_rum_row():
    """A `combined` rum row lists its own styles, never their bottles -- #1379.

    The rum page prints a combined row's styles in its bottles column and
    skips them as rows of their own, so a bottle declared under one of them
    would appear nowhere. Each combined style must also be on its group's
    shelf, or the row names a style the partition never placed.
    """
    groups = _vocab().get("rum_groups") or []
    bottles = _bottles().get("bottles") or {}
    wrong = []
    for g in groups:
        on_shelf = set(g.get("styles") or [])
        for row in g.get("combined") or []:
            for style in row.get("styles") or []:
                if style not in on_shelf:
                    wrong.append(f"{g.get('name')}: {style!r} is combined but not on the shelf")
                for name, entry in bottles.items():
                    if isinstance(entry, dict) and entry.get("generic") == style:
                        wrong.append(f"{name!r} is a bottle under combined style {style!r}")
    assert not wrong, (
        "combined rum row(s) the page cannot print whole:\n  " + "\n  ".join(wrong)
        + "\n\nA combined row lists generics, not bottles. A style with a bottle "
          "needs its own row: take it out of `combined`."
    )


def test_rum_liqueur_shelf_names_declared_liqueurs():
    """Every row of `rum_liqueur_shelf` names a generic in `liqueurs` -- #1379.

    The page looks each row's bottles up by that generic, so a renamed or
    misspelt one renders an empty row with nothing else failing.
    """
    vocab = _vocab()
    shelf = vocab.get("rum_liqueur_shelf") or {}
    rows = shelf.get("rows") or []
    assert shelf.get("name") and rows, (
        "`rum_liqueur_shelf` has no name or no rows, so the rum page prints an "
        "empty section."
    )
    liqueurs = set(vocab.get("liqueurs") or [])
    stray = [r.get("generic") for r in rows if r.get("generic") not in liqueurs]
    assert not stray, (
        "rum_liqueur_shelf row(s) naming no declared liqueur:\n  "
        + "\n  ".join(repr(s) for s in stray)
    )


def test_search_umbrellas_name_declared_generics():
    """Every generic a search umbrella covers or offers is declared -- #1376.

    assets/js/cocktail-search.js matches an umbrella's members by exact name,
    so a renamed generic leaves the `(all)` button selecting nothing, with
    every other check green. A label that is also a family would give two
    buttons one name.
    """
    vocab = _vocab()
    declared = _declared_generics(vocab)
    families = set(vocab.get("families") or [])
    wrong = []
    for u in (vocab.get("search") or {}).get("umbrellas") or []:
        label = u.get("label")
        if not label or not u.get("covers"):
            wrong.append(f"{u!r}: an umbrella needs a label and covers")
        if label in families:
            wrong.append(f"{label!r} is already a family")
        for key in ("covers", "then_offer"):
            wrong += [f"{label!r} {key}: {g!r} is not a declared generic"
                      for g in u.get(key) or [] if g not in declared]
    assert not wrong, "search umbrella problem(s):\n  " + "\n  ".join(wrong)


def test_family_reach_names_real_things():
    """`family_reach` maps declared generics to declared families -- #1379.

    The search matches by exact name, so a renamed generic silently drops out
    of `rum (all)`. A generic already in `family_of` needs no reach, and one
    there for a different family would be found by two families' chips.
    """
    vocab = _vocab()
    declared = _declared_generics(vocab)
    families = set(vocab.get("families") or [])
    family_of = vocab.get("family_of") or {}
    wrong = []
    for generic, family in (vocab.get("family_reach") or {}).items():
        if generic not in declared:
            wrong.append(f"{generic!r} is not a declared generic")
        if family not in families:
            wrong.append(f"{generic!r} -> {family!r}, which is not a family")
        if generic in family_of:
            wrong.append(f"{generic!r} is already in family_of ({family_of[generic]})")
    assert not wrong, "family_reach problem(s):\n  " + "\n  ".join(wrong)


def test_every_rum_based_liqueur_is_reached_by_rum():
    """A rum or rhum liqueur is on the rum page's liqueur shelf and answers to
    `rum (all)` -- #1379.

    So a new one is found by `rum (all)` without anyone having to remember
    to say so. What a liqueur is made from is not in its name
    (Créole Shrubb), so the shelf is the declaration and this test makes the
    reach follow from it. A liqueur whose NAME says rum or rhum must be on
    the shelf, which catches the next one typed in without being placed.
    """
    vocab = _vocab()
    reach = vocab.get("family_reach") or {}
    shelf = [r.get("generic") for r in
             (vocab.get("rum_liqueur_shelf") or {}).get("rows") or []]
    assert shelf, "`rum_liqueur_shelf` has no rows, so this check has nothing to hold."
    unreached = [g for g in shelf if reach.get(g) != "rum"]
    named = [g for key in ("liqueurs", "herbal_liqueurs")
             for g in vocab.get(key) or []
             if re.search(r"\brh?um\b", g, re.I) and g not in shelf]
    assert not (unreached or named), (
        "rum-based liqueur(s) that `rum (all)` would not find:\n  "
        + "\n  ".join([f"{g!r}: on rum_liqueur_shelf, missing from family_reach"
                       for g in unreached]
                      + [f"{g!r}: a rum or rhum liqueur not on rum_liqueur_shelf"
                         for g in named])
        + "\n\nA rum or rhum liqueur goes on `rum_liqueur_shelf` (the rum page "
          "lists it) and in `family_reach` as rum (search finds it). Both are "
          "in _data/cocktails/ingredients.yml."
    )


def test_rum_page_notes_name_real_things():
    """`rum_page_bottle_notes` keys are bottles; `rum_character_notes` keys are
    characters -- #1379. A note on a renamed key silently stops printing.
    """
    vocab = _vocab()
    bottles = set(_bottles().get("bottles") or {})
    characters = set(vocab.get("rum_characters") or [])
    stale = ([f"bottle {k!r}" for k in (vocab.get("rum_page_bottle_notes") or {})
              if k not in bottles]
             + [f"character {k!r}" for k in (vocab.get("rum_character_notes") or {})
                if k not in characters])
    assert not stale, (
        "rum page note(s) keyed by a name that does not exist:\n  "
        + "\n  ".join(stale)
    )


def test_bottle_origin_is_declared():
    """A bottle's `origin:` is a value `bottle_origins` declares -- #591.

    A closed vocabulary nothing checks is an open one, and a typo mints a new
    member in silence. Adding a value is Helen's decision.
    """
    declared = set(_vocab().get("bottle_origins") or [])
    assert declared, (
        "ingredients.yml declares no `bottle_origins` vocabulary, so nothing "
        "constrains the `origin:` field (#591)."
    )

    undeclared = sorted(
        {(name, entry["origin"])
         for name, entry in (_bottles().get("bottles") or {}).items()
         if isinstance(entry, dict) and entry.get("origin") not in (None, "")
         and entry["origin"] not in declared}
    )
    assert not undeclared, (
        "bottle(s) whose `origin` is not in `bottle_origins`:\n  "
        + "\n  ".join(f"{n}: {o!r}" for n, o in undeclared)
        + "\n\nEither it is a typo, or the vocabulary needs the new value -- "
          "and adding one is a decision about what the collection is willing to "
          "say, which is Helen's."
    )


def test_cane_juice_bottles_declare_an_origin():
    """Every bottle on the Cane juice shelf declares an `origin` -- #591.

    Agricole is the cane family whose origin is not in its generic, so a bottle
    without one loses it. The shelf's styles are read from `rum_groups`, and
    the shelf is asserted to exist: renamed, this would find no styles and
    check nothing.
    """
    SHELF = "Cane juice"
    groups = _vocab().get("rum_groups") or []
    shelf = [g for g in groups if (g.get("name") or "").strip() == SHELF]
    assert shelf, (
        f"`rum_groups` has no {SHELF!r} shelf, so this test just checked "
        f"nothing.\n\nThe shelves are:\n  "
        + "\n  ".join((g.get("name") or "?") for g in groups)
        + f"\n\nIf it was renamed, rename it here too -- otherwise the guard "
          f"that stops an agricole bottle arriving without an origin (#591) is "
          f"silently switched off."
    )

    styles = set(shelf[0].get("styles") or [])
    assert styles, f"the {SHELF!r} shelf declares no styles."

    missing = sorted(
        name for name, entry in (_bottles().get("bottles") or {}).items()
        if isinstance(entry, dict)
        and entry.get("generic") in styles
        and not (entry.get("origin") or "").strip()
    )
    assert not missing, (
        f"cane-juice bottle(s) with no `origin`:\n  " + "\n  ".join(missing)
        + "\n\nAgricole is the one cane family whose origin is not in its "
          "generic -- `rhum agricole blanc` is Martinique, Guadeloupe AND Haiti "
          "-- so a bottle without one loses the distinction Helen asked for "
          "(#591). The permitted values are `bottle_origins` in ingredients.yml."
    )
