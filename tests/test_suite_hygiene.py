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
PER_ITEM_FIXTURES = {"recipe", "draft"}


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
