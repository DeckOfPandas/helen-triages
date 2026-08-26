"""Tests about the tests.

One failure mode has now bitten this codebase five times, and it is the only
one whose symptom is GREEN: a test that cannot fail, because the thing it
scans came back empty and it treated "found nothing" as "nothing wrong".
HANDOVER_v26.md §12 lists the first four -- a stale JS_DIR, a non-recursive
SCSS glob, a method_groups key typo that made every prose test see zero steps,
and a link shape no regex considered. The fifth was written on 2026-08-14 by
someone who had just read that section, in a commit fixing a bug caused by not
checking, and was only caught because breaking a new guard on purpose is house
practice here.

The house answer to it already exists and is used in several places:
`assert js_files`, `assert found_any`, `assert svgs`,
test_sass_files_are_actually_found. Assert the corpus is non-empty BEFORE
asserting the property of it.

What was missing is the sharper form of the same rule, which is what this file
enforces:

    NEVER `return` EARLY BECAUSE A SCAN CAME BACK EMPTY.
    Assert it is non-empty instead, with a message saying what to do if the
    emptiness turns out to be legitimate.

An early return LOOKS reasonable -- "nothing to check, so nothing to fail" --
and it is exactly how a test stops testing without anyone noticing. An assert
in the same place costs nothing when the corpus is healthy and is loud on the
day it is not.
"""
from __future__ import annotations

import ast
import pathlib
import re

import pytest

# Suite marker, so `pytest -m shared` can run this half alone.
# tests/test_suite_hygiene.py asserts every module declares one --
# an unmarked file is silently missed by every filtered run.
pytestmark = pytest.mark.shared

TESTS_DIR = pathlib.Path(__file__).resolve().parent

# A test parametrised per recipe/draft (see conftest.pytest_generate_tests) may
# legitimately return early: "this recipe has no internal_temp_ref, nothing to
# check HERE" is fine, because the other ~80 parametrisations still exercise
# the predicate. The dangerous case is a whole-corpus scan, where one early
# return silences the entire check.
PER_ITEM_FIXTURES = {"recipe", "draft", "magic_bag"}


def _test_functions():
    for path in sorted(TESTS_DIR.glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                yield path, node


SUITE_MARKERS = {"food", "cocktails", "shared"}


def test_every_test_module_declares_a_suite_marker():
    """Every tests/test_*.py sets `pytestmark = pytest.mark.<suite>`.

    THE FAILURE MODE IS A SILENT OMISSION, which is this file's whole subject.
    `pytest -m food` and `pytest -m cocktails` exist so that Helen's in-progress
    food QA and the cocktails work do not mask each other -- a red half hides a
    real regression in the other half. But an UNMARKED module is deselected by
    every filtered run: it reports nothing, fails nothing, and looks exactly
    like a module with no problems.

    So the marker is not optional bookkeeping. A new test file without one is
    invisible to the only commands anyone actually runs day to day.

    Checked by reading the source rather than by asking pytest, because pytest
    can only tell us about markers on tests it has already collected -- which is
    the same circularity as asking a deselected test whether it ran.
    """
    missing = []
    checked = 0
    for path in sorted(TESTS_DIR.glob("test_*.py")):
        checked += 1
        src = path.read_text(encoding="utf-8")
        found = re.findall(r"^pytestmark = pytest\.mark\.(\w+)\s*$", src, re.M)
        if not found:
            missing.append(f"{path.name}: no pytestmark")
        elif len(found) > 1:
            missing.append(f"{path.name}: {len(found)} markers ({found})")
        elif found[0] not in SUITE_MARKERS:
            missing.append(f"{path.name}: unknown suite {found[0]!r}")

    assert checked, (
        "No test modules found at all -- this check would pass while checking "
        "nothing, which is the exact thing this file exists to prevent."
    )
    assert not missing, (
        "Test module(s) with a missing or wrong suite marker:\n  "
        + "\n  ".join(missing)
        + f"\n\nAdd `pytestmark = pytest.mark.<suite>` at module level, one of "
          f"{sorted(SUITE_MARKERS)}, and register it in pytest.ini. Without one "
          f"the module is deselected by every `pytest -m ...` run and its "
          f"silence is indistinguishable from success."
    )


def test_no_whole_corpus_test_can_return_early():
    """A corpus-scanning test must assert its corpus is non-empty, not return.

    NOT EXHAUSTIVE, and worth knowing where the edge is: this sees a bare
    `return` in a test that is not parametrised per recipe/draft. It cannot
    see the subtler variant, where a PER-ITEM test returns early because a
    shared REFERENCE set is empty -- test_accents_in_prose did exactly that
    until 2026-08-14 (`if not words: return`, which would have silenced the
    accent rule across every recipe at once if accented_words.yml ever lost
    its `words:` key). Both were fixed to assert; only one shape is guarded
    automatically. If you are writing an early return of any kind in a test,
    the question to ask is "empty because THIS item has nothing, or empty
    because the check itself has nothing?"
    """
    offenders = []
    checked = 0
    for path, fn in _test_functions():
        checked += 1
        if {a.arg for a in fn.args.args} & PER_ITEM_FIXTURES:
            continue
        for node in ast.walk(fn):
            if isinstance(node, ast.Return) and node.value is None:
                offenders.append(f"{path.name}::{fn.name} line {node.lineno}")

    assert checked, (
        "No test functions found at all -- this check would pass while "
        "checking nothing, which is the exact thing it exists to prevent."
    )
    assert not offenders, (
        "Whole-corpus test(s) with a bare early return:\n  "
        + "\n  ".join(offenders)
        + "\n\nA test that is not parametrised per recipe/draft scans "
          "something once. Returning early because that scan came back empty "
          "turns 'I found nothing' into 'nothing is wrong' and the test stops "
          "being able to fail -- green, silent, and indistinguishable from "
          "working. Assert the scan found something instead, with a message "
          "saying what to do if the emptiness is legitimate."
    )


# =============================================================================
# THE PRIVATE DRAFTS ARE NOT IN CI — GitHub issue #378
# =============================================================================
# `_food_drafts/` is a separate private repository, gitignored here, so a CI
# checkout has the ~82 published recipes and none of the ~290 drafts. Every test
# that reads drafts therefore examines a fraction of the collection in CI, and
# because they are all offender-list shaped they find fewer offenders and report
# GREEN rather than failing. Same failure mode as the rest of this file, arriving
# by a different route: not a scan that matched nothing, but a corpus that was
# never delivered.
#
# The two registries below are the point. Every draft-reading test must be in
# one, so that "what happens to this check in CI" is a decision somebody made
# rather than something nobody noticed.

# Reads drafts ONLY. With none present there is nothing to examine, so it skips
# with a reason -- which shows in the run as "did not run" rather than "checked
# and clean".
SKIPS_WITHOUT_DRAFTS = {
    "test_accents_in_drafts",
    "test_pan_and_ingredient_sizes_use_digits_in_drafts",
    "test_pantry_entries_are_actually_used",
}

# Reads recipes AND drafts. Deliberately does NOT skip: the published half is
# real coverage and is the half that ships, so losing it to be honest about the
# other half would be a bad trade. Each says so in its own docstring.
PARTIAL_IN_CI = {
    "test_no_main_ingredient_spelling_collisions",
    "test_no_recipe_uses_the_retired_instructions_field",
    # Reads the published half from this repo's history and the draft half from
    # _food_drafts/'s own. In CI the second half is absent, so it checks the 82
    # recipes and none of the 314 drafts -- and the drafts are where the risk
    # actually lives, since tidy-up passes happen there. Kept running anyway:
    # the published half is the half that ships. See its docstring.
    "test_no_agent_commit_claims_helens_rewrite",
}


def _function_source(path, node):
    lines = path.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[node.lineno - 1:node.end_lineno])


def _calls_pytest_skip(node):
    """Does this function actually call pytest.skip()?

    ASKED OF THE SYNTAX TREE, NOT OF THE TEXT, and that is the whole point. The
    first version asked whether the word "skip" appeared in the source, and
    every test whose DOCSTRING explains that it deliberately does not skip
    answered yes. Two of the five classified themselves wrong on their own prose.

    Fourth instance in one session of a source-scanning check being defeated by
    the writing around the code (see the note in the test below). An AST cannot
    be fooled by a comment, which is the reason to reach for it here rather than
    add another exclusion to a regex.
    """
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        func = child.func
        if isinstance(func, ast.Attribute) and func.attr == "skip":
            if isinstance(func.value, ast.Name) and func.value.id == "pytest":
                return True
    return False


def test_every_draft_reading_test_says_what_it_does_without_drafts():
    """A test that reads `_food_drafts/` must declare what it does in CI.

    Issue #378 found four checks quietly scanning a third of the collection in
    CI and passing. Fixing those four is the small half; the large half is that
    a FIFTH could be written tomorrow and join them silently, because nothing
    about writing `for draft in ALL_DRAFTS` tells you the list is empty on the
    machine that gates the deploy.

    So this generates the list from the code -- every test function referencing
    ALL_DRAFTS -- and requires each to be classified. HANDOVER §12's lesson from
    the filter-state sweep, applied: when a generated test keeps missing the same
    bug, generate the next one from the other end. The other end here is the
    source, not a list somebody maintains.

    Adding a draft-reading test means adding its name to one of the two sets
    above, which is thirty seconds and forces the question.

    PER-DRAFT TESTS ARE EXEMPT and need no entry: a test taking the `draft`
    fixture is parametrised over ALL_DRAFTS by conftest.pytest_generate_tests,
    and an empty parametrisation is reported by pytest as a skip already. They
    are the 51 skips a CI-shaped run shows. Visible without help.

    WHAT THIS CANNOT SEE, said plainly rather than left to be discovered: a test
    that reaches drafts through a module-level name derived from ALL_DRAFTS
    (test_drafts.py's `_ALL_SLUGS` is the live example) rather than naming it
    directly. That one happens to be per-draft and so exempt anyway, but a
    future non-parametrised consumer of such a name would slip past. Widening
    this to follow module-level derivations is possible and was not done for a
    single hypothetical.
    """
    unclassified = []
    miscategorised = []
    found = set()

    for path, node in _test_functions():
        # THIS FILE IS EXCLUDED, and the reason is funny enough to be worth
        # recording: the first version of this test failed on ITSELF. A test
        # about draft-reading tests necessarily writes the corpus name in its own
        # docstring and in the line that looks for it, so it detected itself as
        # an unclassified draft-reading test.
        #
        # Third time in one session that prose defeated a source-scanning check
        # -- the destructive-git hook refused its own introducing commit, the
        # picker guard counted a flag named in a comment, and now this. The
        # pattern is not a coincidence: a guard's own text is where its subject's
        # vocabulary is densest. Excluding this module is the honest fix (it
        # reads no drafts), and the two assertions at the bottom stop that
        # exclusion from quietly hollowing the check out.
        if path.name == "test_suite_hygiene.py":
            continue
        source = _function_source(path, node)
        if "ALL_DRAFTS" not in source:
            continue
        found.add(node.name)
        if PER_ITEM_FIXTURES & {a.arg for a in node.args.args}:
            continue                     # parametrised; an empty set already skips

        name = node.name
        skips = _calls_pytest_skip(node)
        where = f"{path.name}::{name}"

        if name in SKIPS_WITHOUT_DRAFTS:
            if not skips:
                miscategorised.append(
                    f"{where} is listed in SKIPS_WITHOUT_DRAFTS but has no "
                    f"`if not DRAFTS_PRESENT: pytest.skip(...)` guard, so it "
                    f"does not do what the list says it does"
                )
        elif name in PARTIAL_IN_CI:
            if skips:
                miscategorised.append(
                    f"{where} is listed in PARTIAL_IN_CI but skips when the "
                    f"drafts are absent -- move it to SKIPS_WITHOUT_DRAFTS"
                )
        else:
            unclassified.append(where)

    assert not unclassified, (
        "Test(s) read _food_drafts/ without declaring what they do when it is "
        "absent:\n  " + "\n  ".join(sorted(unclassified))
        + "\n\nIn CI that directory does not exist, so these scan an empty list "
          "and pass. Decide which it is and add the name to the matching set in "
          "tests/test_suite_hygiene.py:\n"
          "  SKIPS_WITHOUT_DRAFTS — reads drafts only; skip with "
          "conftest.NO_DRAFTS_REASON so the run says it did not run.\n"
          "  PARTIAL_IN_CI — reads recipes too; keep running for their sake, and "
          "say in the docstring what the CI green does and does not mean."
    )
    assert not miscategorised, (
        "Draft-reading test(s) do not match the set they are listed in:\n  "
        + "\n  ".join(sorted(miscategorised))
        + "\n\nThe registries are only worth having if they are true."
    )

    # THE SCAN ITSELF, asserted rather than trusted -- this file's whole subject.
    # Excluding a module above is exactly the sort of edit that can turn a real
    # check into a vacuous one, and "found nothing, so nothing was wrong" is the
    # failure this file exists to prevent.
    assert found, (
        "No draft-reading tests were found anywhere. Either they were all "
        "removed, or the scan has stopped matching -- and an empty scan passes "
        "while checking nothing."
    )
    stale = (SKIPS_WITHOUT_DRAFTS | PARTIAL_IN_CI) - found
    assert not stale, (
        f"These names are registered as draft-reading tests but no such test "
        f"was found reading drafts: {sorted(stale)}.\n"
        f"Either the test was renamed or deleted and its entry left behind, or "
        f"it no longer reads _food_drafts/ and the entry is now noise. A "
        f"registry with dead entries stops being read."
    )
