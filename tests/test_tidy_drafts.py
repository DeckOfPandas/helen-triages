"""What `/tidy-drafts` does to a DRINK, proved on a fixture and not on Helen's.

`scripts/tidy_drafts.py` grew a cocktails half on 2026-09-05, at Helen's
request: *"Widen please -- cocktail drafts passing will save me a lot of time."*
The food half has been run for real three times and its evidence is the diff it
left behind; the drinks half had no such history, and the first thing anyone
would want to do to get one is point it at `_cocktail_drafts/`. That is exactly
what must not happen while she is proofreading the staged drinks, so this module
is the evidence instead.

NOTHING HERE READS OR WRITES A REAL DRAFTS REPO. Every case builds one drink
under this repo's own `tmp/` and removes it again -- the same construction
`tests/test_ingest_inbox.py` uses and for the same two reasons: `/tmp` is
forbidden by CLAUDE.md, and both private repos are absent in a worktree and in
CI, so a test that needed one would be a test that mostly skips.

THE ASSERTION IS BYTE-FOR-BYTE, and that is the design. "It fixed the six
faults" is easy to satisfy, and easy to satisfy while also doing something else
to the other thirty lines; a script whose whole safety story is "read the diff
afterwards" has to be provable by comparing whole files. So `AFTER` below is the
entire expected output, and every line of it that is not one of the four changed
lines is a line the pass must have left exactly alone.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# Suite marker, so `pytest -m shared` runs this. test_suite_hygiene.py asserts
# every module declares one -- an unmarked file is silently missed by every
# filtered run. `shared` because the script serves both collections, which is
# also why test_ingest_inbox.py chose it.
pytestmark = pytest.mark.shared

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "tidy_drafts.py"


# =============================================================================
# ONE DRINK, CARRYING EVERY CLASS THE PASS TOUCHES AND EVERY CLASS IT MUST NOT
# =============================================================================
# The faults it MUST fix -- six of them across four lines, all in Helen's own
# prose and every one named by tests/test_cocktails.py:
#
#   1. `tagline:` is an unquoted scalar   test_drink_scalar_fields_are_quoted
#   2. `--` in the tagline                test_drink_typography[double hyphen]
#   3. `--` in an ingredient's note       test_drink_typography[double hyphen]
#   4. `2-3` in the tagline               test_drink_number_ranges_use_en_dashes
#   5. `2-3` in an ingredient's note      test_drink_number_ranges_use_en_dashes
#   6. `2-3` in a note's text             test_drink_number_ranges_use_en_dashes
#
# THE SAME FAULT APPEARS IN MORE THAN ONE PLACE ON PURPOSE. A tagline is the
# obvious prose field and the one anybody would remember to allow; an
# ingredient's `note:` sits two lines below an `amount:` and a `generic:` that
# are both off limits, and a `notes:` entry's `text:` sits directly above a `QQ`
# one. Those are the boundaries worth having a fixture for.
#
# Everything else in the file is a fault of the same MECHANICAL SHAPE sitting
# somewhere the pass does not go, and each is here because leaving it out would
# make the byte-for-byte assertion below prove less than it looks like it does.
BEFORE = '''---
title: "Test Drink"
tagline: Sharp -- and bright, 2-3 dashes of it
glass:
  - "old fashioned"
garnish:
  - "lemon twist"
ingredients:
  - amount: "30-45 ml"
    item: "Somebody Else's Rum -- as printed on the label"
    generic: "aged rum"
  - amount: "10 ml"
    generic: "cane sugar syrup 2:1"
    note: "A 2-3 ml difference is not worth measuring -- use the 10."
  - amount: "1 dash"
    generic: "aromatic bitters"
    suggestion:
      - "Angostura"
      - "Peychaud's -- if you have it"
method:
  - "Stir all ingredients with ice."
  - "Strain."
mood:
  - "clear"
notes:
  - label: "Balance"
    text: "Give it 2-3 stirs more than you think."
  - label: "QQ"
    text: "QQ - the source said 2-3 dashes -- reproduce, do not correct"
source: ""
source_url: ""
meta:
  ship: "meh"
  date_last_edited: "2026-09-05"
  rewritten: false
  awaiting_fix: false
  proofread: false
---
'''

# FOUR LINES DIFFER FROM `BEFORE` AND NO OTHERS: the tagline (quoted, em dash,
# en dash), the ingredient note (em dash, en dash), and note 1 (en dash). Every
# other line here is copied from BEFORE character for character, including the
# four that carry the identical faults in places the pass does not go.
AFTER = '''---
title: "Test Drink"
tagline: "Sharp — and bright, 2–3 dashes of it"
glass:
  - "old fashioned"
garnish:
  - "lemon twist"
ingredients:
  - amount: "30-45 ml"
    item: "Somebody Else's Rum -- as printed on the label"
    generic: "aged rum"
  - amount: "10 ml"
    generic: "cane sugar syrup 2:1"
    note: "A 2–3 ml difference is not worth measuring — use the 10."
  - amount: "1 dash"
    generic: "aromatic bitters"
    suggestion:
      - "Angostura"
      - "Peychaud's -- if you have it"
method:
  - "Stir all ingredients with ice."
  - "Strain."
mood:
  - "clear"
notes:
  - label: "Balance"
    text: "Give it 2–3 stirs more than you think."
  - label: "QQ"
    text: "QQ - the source said 2-3 dashes -- reproduce, do not correct"
source: ""
source_url: ""
meta:
  ship: "meh"
  date_last_edited: "2026-09-05"
  rewritten: false
  awaiting_fix: false
  proofread: false
---
'''


@pytest.fixture
def drinks():
    """A drafts root under this repo's own `tmp/`, removed afterwards.

    NOT `tmp_path`, and CLAUDE.md is why: nothing in this project writes under
    the system `/tmp`, for any reason. `tmp/` is gitignored here.
    """
    root = ROOT / "tmp" / "test_tidy_drafts_drinks"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    yield root
    shutil.rmtree(root)


def run(root, *extra):
    """The script as Helen runs it, on a copy, with the drinks rules."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--site", "cocktails",
         "--drafts-dir", str(root), "--allow-dirty", *extra],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, (
        f"the script exited {result.returncode}:\n{result.stdout}\n"
        f"{result.stderr}"
    )
    return result.stdout


def write_drink(root, name="test-drink.md", text=BEFORE):
    path = root / name
    path.write_text(text, encoding="utf-8")
    return path


# =============================================================================

def test_the_report_names_every_fault_and_writes_nothing(drinks):
    """Report mode is the default and it is the half that must never write."""
    path = write_drink(drinks)
    out = run(drinks)

    assert "would apply 6 mechanical change(s) across 1 file(s)" in out, out
    assert "[quoting] tagline:" in out, out
    assert out.count("[typography] double hyphen -> em dash") == 2, out
    assert out.count("[dashes]") == 3, out
    assert path.read_text(encoding="utf-8") == BEFORE, (
        "report mode wrote to the file. Nothing else in this module matters if "
        "the default run is not read-only."
    )


def test_apply_fixes_exactly_those_and_touches_nothing_else(drinks):
    """Byte-for-byte, because "it fixed six things" is the weaker claim.

    A LINE-BY-LINE DIFF IN THE FAILURE MESSAGE, not a 34-line repr against
    another 34-line repr. The one bug this script has ever had produced output
    that looked entirely plausible in a diff -- it was caught by parsing the
    result, not by reading it -- so when this does fail, the thing to see first
    is which lines moved.
    """
    path = write_drink(drinks)
    run(drinks, "--apply")
    got = path.read_text(encoding="utf-8")
    if got != AFTER:
        moved = [f"    line {i}\n      want: {w!r}\n      got:  {g!r}"
                 for i, (w, g) in enumerate(zip(AFTER.split("\n"),
                                                got.split("\n")), 1)
                 if w != g]
        pytest.fail("--apply did not produce the expected drink:\n"
                    + "\n".join(moved or ["(line counts differ)"]))


@pytest.mark.parametrize("line", [
    'text: "QQ - the source said 2-3 dashes -- reproduce, do not correct"',
    'amount: "30-45 ml"',
    'item: "Somebody Else\'s Rum -- as printed on the label"',
    '- "Peychaud\'s -- if you have it"',
])
def test_the_lines_the_pass_must_not_touch_survive_apply(drinks, line):
    """Each of these carries a fault the pass fixes elsewhere in the same file.

    That is the whole point of the parametrisation: `2-3` and `--` are fixed
    three lines up, so a rule that had leaked out of Helen's prose would show
    here rather than in a general "nothing changed" assertion that a
    do-nothing script would also pass.

    A `QQ` NOTE IS THE FIRST CASE AND THE LOAD-BEARING ONE. On a drink the
    marker sits behind a key -- `text: "QQ - ..."` -- and the food QQ pattern in
    tidy_drafts.py, which allows only a list dash and a quote in front of it,
    matches that line not at all. The drinks half asks
    `conftest.checkable_text` instead; this is the test that fails if anybody
    ever "simplifies" it back to the food one.
    """
    path = write_drink(drinks)
    assert line in path.read_text(encoding="utf-8"), (
        f"the fixture no longer contains {line!r}, so this case is checking "
        f"nothing. Fix the fixture, never this assertion."
    )
    run(drinks, "--apply")
    assert line in path.read_text(encoding="utf-8"), (
        f"the tidy pass edited a line it must leave alone:\n  {line}"
    )


def test_a_range_in_an_amount_is_reported_rather_than_silently_declined(drinks):
    """The drinks suite fails on it, so the report has to say why it did not.

    `test_drink_number_ranges_use_en_dashes` checks amounts -- Helen, of
    `cook_time: "20-25 mins"`: "These still render to the user, so correct to en
    dash please." This script declines them on a recorded harm
    (anitas-attitude-adjuster, see the module docstring), and a decline that
    prints nothing is indistinguishable from a rule that is not running.
    """
    write_drink(drinks)
    out = run(drinks)
    assert "reported, never changed: 1 file(s)" in out, out
    assert "hyphenated number range, not this pass's to fix" in out, out
    assert '30-45 ml' in out, out


def test_a_file_with_no_front_matter_is_named_and_left_alone(drinks):
    """`_cocktail_drafts/README.md` is the live case and it is prose.

    The three line-wise fixers do not parse front matter, so before 2026-09-05
    a README containing `--` was a file this pass would have em-dashed. Absent
    this test the only symptom would be an em dash in a README nobody diffs.
    """
    write_drink(drinks)
    readme = drinks / "README.md"
    readme.write_text("# Drafts\n\nRun -- carefully -- with 2-3 checks.\n",
                      encoding="utf-8")
    out = run(drinks, "--apply")
    assert "no front matter" in out and "README.md" in out, out
    assert readme.read_text(encoding="utf-8") == (
        "# Drafts\n\nRun -- carefully -- with 2-3 checks.\n"
    )


def test_a_drink_in_a_staging_subfolder_is_reached(drinks):
    """`to-promote/` is half the collection and a flat glob would miss it.

    22 of the 124 drinks live there. The food side went recursive on 2026-08-20
    for the same reason and the failure was invisible: a flat glob reports the
    files it found, all of them clean, and says nothing about the ones it did
    not look for.
    """
    (drinks / "to-promote").mkdir()
    path = write_drink(drinks, "to-promote/staged.md")
    out = run(drinks)
    assert "to-promote/staged.md" in out, out
    assert "would apply 6 mechanical change(s)" in out, out
    assert path.read_text(encoding="utf-8") == BEFORE


def test_food_only_rules_do_not_run_on_a_drink(drinks):
    """`--only meta` on the drinks site changes nothing, and says so.

    The #429 `meta:` migration drops two retired keys and reorders three flags.
    A drink's `meta:` is five keys in its own order (test_cocktails.
    META_KEYS_IN_ORDER), two of which food RETIRED -- so the food migration
    pointed at a drink would strip them and reorder what is left, quietly, on
    all 124 files. The rules are in two tables precisely so this cannot happen;
    this is the test that says the tables are still two.
    """
    path = write_drink(drinks)
    out = run(drinks, "--only", "meta", "--apply")
    assert "would apply" not in out
    assert "applied 0 mechanical change(s)" in out, out
    assert path.read_text(encoding="utf-8") == BEFORE, (
        "food's `meta:` migration ran over a drink. Check that DRINK_FIXERS "
        "still omits fix_meta_block."
    )
