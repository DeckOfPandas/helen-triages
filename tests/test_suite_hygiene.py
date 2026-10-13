"""Tests about the tests.

The failure this file guards has a green symptom: a test that cannot fail,
because the thing it scans came back empty and it read "found nothing" as
"nothing wrong" (MANUAL §12). The rule, which has no other enforcement:

    NEVER `return` EARLY BECAUSE A SCAN CAME BACK EMPTY.
    Assert it is non-empty instead, with a message saying what to do if the
    emptiness turns out to be legitimate.

Assert the corpus is non-empty before asserting the property of it. An early
return looks reasonable -- "nothing to check, so nothing to fail" -- and is how
a test stops testing unnoticed. An assert in the same place costs nothing when
the corpus is healthy and is loud on the day it is not.
"""
from __future__ import annotations

import ast
import pathlib
import re

import pytest

pytestmark = pytest.mark.shared

TESTS_DIR = pathlib.Path(__file__).resolve().parent

# A test parametrised per item (conftest.pytest_generate_tests) may return
# early: "this recipe has no internal_temp_ref" is fine, because the other
# parametrisations still exercise the predicate. The dangerous case is a
# whole-corpus scan, where one early return silences the entire check.
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

    An unmarked module is deselected by every `pytest -m food` or
    `pytest -m cocktails` run: it reports nothing and looks like a module
    with no problems. Checked by reading the source, because pytest only
    knows the markers of tests it has already collected.
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

    Not exhaustive: this sees a bare `return` in a test that is not
    parametrised per item. It cannot see a per-item test returning early
    because a shared reference set is empty (`if not words: return`), which
    silences the rule across every recipe at once. Before writing any early
    return in a test, ask: empty because this item has nothing, or empty
    because the check itself has nothing?
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


# --- the private drafts are not in CI (#378) ----------------------------------
# `_food_drafts/` is a separate private repository, gitignored here, so a CI
# checkout has the published recipes and none of the drafts. A test that reads
# drafts finds fewer offenders there and reports green.
# Every draft-reading test must be in one of the two registries below, so that
# what happens to it in CI is a decision somebody made.

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
    # _food_drafts/'s own. In CI it checks the recipes and none of the drafts,
    # which is where tidy-up passes happen. See its docstring.
    "test_no_agent_commit_claims_helens_rewrite",
    # Sweeps recipes, drafts and the magic bag for the notes NOTE_EXCEPTIONS
    # exempts (#711). In CI an exemption naming a draft's note would look stale
    # and fail; it keeps running because the declared exemption names a
    # published recipe.
    "test_no_note_exception_is_stale",
}


def _function_source(path, node):
    lines = path.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[node.lineno - 1:node.end_lineno])


def _calls_pytest_skip(node):
    """Does this function call pytest.skip()?

    Asked of the syntax tree, not the text: a test whose docstring explains
    that it deliberately does not skip contains the word too.
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
    """A test that reads `_food_drafts/` must declare what it does in CI (#378).

    The list is generated from the code -- every test function whose source
    names ALL_DRAFTS -- and each must be in SKIPS_WITHOUT_DRAFTS or
    PARTIAL_IN_CI. A test taking the `draft` fixture is exempt: pytest reports
    an empty parametrisation as a skip already.

    Not seen: a test that reaches drafts through a module-level name derived
    from ALL_DRAFTS (test_drafts.py's `_ALL_SLUGS`) rather than naming it. That
    one is per-draft and so exempt, but a non-parametrised consumer of such a
    name would slip past.
    """
    unclassified = []
    miscategorised = []
    found = set()

    for path, node in _test_functions():
        # This file is excluded: a test about draft-reading tests names the
        # corpus in its own docstring and code, and would detect itself. It
        # reads no drafts, and the assertions on `found` and `stale` below
        # stop the exclusion from hollowing the check out.
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

    # The scan itself is asserted, not trusted: excluding a module above is
    # the kind of edit that can turn a real check into a vacuous one.
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


# --- the aggregate caveat: conftest's end-of-run report ------------------------
# The registries work test by test; none can show how much of the corpus a run
# never opened. conftest reports it rather than failing (DECISIONS §11). Pinned
# here: the report says so when the drafts are missing and is silent when they
# are not, because a caveat printed on every run is ignored like a failure.

def test_the_drafts_caveat_is_silent_when_both_clones_are_present(tmp_path):
    import conftest

    present = tmp_path / "here"
    present.mkdir()
    original = (conftest.DRAFTS_DIR, conftest.COCKTAIL_DRAFTS_DIR)
    try:
        conftest.DRAFTS_DIR = present
        conftest.COCKTAIL_DRAFTS_DIR = present
        assert conftest._absent_drafts() == []
        assert conftest.pytest_report_header(None) is None
    finally:
        conftest.DRAFTS_DIR, conftest.COCKTAIL_DRAFTS_DIR = original


def test_the_drafts_caveat_names_each_absent_clone_and_how_to_get_it(tmp_path):
    import conftest

    original = (conftest.DRAFTS_DIR, conftest.COCKTAIL_DRAFTS_DIR)
    try:
        conftest.DRAFTS_DIR = tmp_path / "_food_drafts"
        conftest.COCKTAIL_DRAFTS_DIR = tmp_path / "_cocktail_drafts"
        absent = conftest._absent_drafts()
        assert absent == ["_food_drafts", "_cocktail_drafts"]
        header = conftest.pytest_report_header(None)
        for name in absent:
            assert name in header
            # A caveat that does not say what to do about it is a complaint.
            assert name in conftest._CLONE, (
                f"{name} can be reported absent but has no clone command"
            )
            assert conftest._CLONE[name].startswith("sh scripts/git-clone-agent.sh")
    finally:
        conftest.DRAFTS_DIR, conftest.COCKTAIL_DRAFTS_DIR = original


def test_the_drafts_caveat_can_never_turn_a_run_red(tmp_path):
    """It reports; it does not judge. A summary hook that raised would take the
    whole run down, which is a far worse trade than the silence it replaced."""
    import conftest

    class _Exploding:
        def write_line(self, *args, **kwargs):
            raise RuntimeError("terminal gone")

    original = (conftest.DRAFTS_DIR, conftest.COCKTAIL_DRAFTS_DIR)
    try:
        conftest.DRAFTS_DIR = tmp_path / "_food_drafts"
        conftest.COCKTAIL_DRAFTS_DIR = tmp_path / "_cocktail_drafts"
        conftest.pytest_terminal_summary(_Exploding(), 0, None)
    finally:
        conftest.DRAFTS_DIR, conftest.COCKTAIL_DRAFTS_DIR = original


# --- the browser smoke test's skip (#1200) --------------------------------------
# test_browser_smoke.py skips whenever Chromium cannot launch. Two things keep
# that honest: the skip is decided in one place, and the run says it happened.

class _Lines:
    def __init__(self):
        self.lines = []

    def __call__(self, text, **kwargs):
        self.lines.append(text)


class _Report:
    def __init__(self, nodeid, reason):
        self.nodeid = nodeid
        self.longrepr = ("file", 1, f"Skipped: {reason}")


def test_the_browser_caveat_names_the_skip_and_its_reason():
    import conftest

    write = _Lines()
    conftest._report_browser_skips(write, [
        _Report(f"tests/{conftest.BROWSER_SMOKE}::test_a[x]", "no launchable Chromium: gone"),
        _Report(f"tests/{conftest.BROWSER_SMOKE}::test_b[y]", "no launchable Chromium: gone"),
    ])
    said = "\n".join(write.lines)
    assert "2 browser smoke tests skipped" in said
    assert "no launchable Chromium: gone" in said
    assert "sh scripts/browser/install.sh" in said, "a caveat with no remedy is a complaint"


def test_the_browser_caveat_is_silent_when_the_smoke_test_ran():
    """Another module's skips are not the browser's, and no skip is silence."""
    import conftest

    write = _Lines()
    conftest._report_browser_skips(write, [_Report("tests/test_drafts.py::test_x", "no drafts")])
    conftest._report_browser_skips(write, [])
    assert write.lines == []


def test_every_browser_test_goes_through_the_launch_probe():
    """Skip on whether Chromium launches, never on whether playwright imports.

    Where the binding is installed and no browser is, an import skip does not
    skip: the test runs, fails to launch and gates the deploy, and no test is
    expected to fail (DECISIONS §10). The `chromium` fixture is the one probe;
    every test in the module asks for it, and nothing in the suite may
    importorskip playwright.
    """
    smoke = TESTS_DIR / "test_browser_smoke.py"
    tests = [n for p, n in _test_functions() if p == smoke]
    assert tests, f"no tests found in {smoke.name} -- an empty scan passes"
    unprobed = [n.name for n in tests if "chromium" not in {a.arg for a in n.args.args}]
    assert not unprobed, (
        f"{smoke.name}: {unprobed} do not take the `chromium` fixture, so they "
        f"do not skip when no browser can launch")

    importskips = []
    for path in sorted(TESTS_DIR.glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "importorskip" and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and str(node.args[0].value).startswith("playwright")):
                importskips.append(f"{path.name}:{node.lineno}")
    assert not importskips, (
        f"importorskip('playwright...') at {importskips}: CI has the binding "
        f"and no browser, so this would run and fail there. Take the "
        f"`chromium` fixture from test_browser_smoke.py instead.")
